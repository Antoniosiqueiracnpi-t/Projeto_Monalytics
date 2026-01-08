#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CAPTURADOR DE DIVIDENDOS FUTUROS - FONTE OFICIAL (B3 LISTADOS)
=============================================================

Fonte oficial:
- B3 Listados (sistemaswebb3-listados.b3.com.br) via endpoints proxy em JSON.

Fluxo:
1) Carrega mapeamento_tradingname_b3.csv (ticker, trading_name, codigo)
2) Para cada ticker:
   - Dedup: lê balancos/{TICKER}/dividendos_futuros.json existente
   - Busca proventos (cash dividends) no B3 Listados
   - Aplica janela --dias (cliente) e só adiciona NÃO-duplicados
3) Salva por ticker: balancos/{TICKER}/dividendos_futuros.json
4) Salva agregado do dia (somente novos desta execução): balancos/dividendos_anunciados.json

Dependências:
pip install requests pandas
(opcional) pip install certifi

Exemplos:
  # Busca últimos 10 dias (janela deslizante)
  python src/capturar_dividendos_futuros.py --modo completo --dias 10

  # Busca últimos 5 dias (20 empresas)
  python src/capturar_dividendos_futuros.py --modo quantidade --quantidade 20 --dias 5
"""

import argparse
import base64
import json
import logging
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import quote

import pandas as pd
import requests


# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


# ---------------- HELPERS ----------------
def _b64_params(params: Dict) -> str:
    """
    Importante: a B3 Listados (proxy) costuma usar base64 de str(dict) (com aspas simples),
    não JSON. Mantemos exatamente esse formato por compatibilidade.
    """
    raw = str(params).encode("ascii", errors="ignore")
    return base64.b64encode(raw).decode("ascii")


def _safe_get(session: requests.Session, url: str, timeout: int = 20) -> requests.Response:
    """
    GET com fallback (alguns ambientes antigos reclamam de SSL chain).
    Preferimos verify=True, e só caímos para verify=False se necessário.
    """
    try:
        resp = session.get(url, timeout=timeout, verify=True)
        resp.raise_for_status()
        return resp
    except Exception as e1:
        # fallback
        logger.warning(f"⚠️  SSL/GET falhou (verify=True). Tentando verify=False... ({type(e1).__name__})")
        resp = session.get(url, timeout=timeout, verify=False)
        resp.raise_for_status()
        return resp


def _parse_any_date(value) -> Optional[date]:
    """
    Tenta parsear datas em formatos comuns que aparecem nos JSONs da B3:
    - '07/01/2026'
    - '07/01/2026 23:12:12'
    - '2026-01-07'
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() in ("nan", "none"):
        return None

    # dd/mm/yyyy (com ou sem hora)
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", s)
    if m:
        d, mth, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(y, mth, d)
        except Exception:
            return None

    # yyyy-mm-dd
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        y, mth, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(y, mth, d)
        except Exception:
            return None

    return None


def _parse_money(value) -> float:
    if value is None:
        return 0.0
    s = str(value).strip()
    if not s or s.lower() in ("nan", "none"):
        return 0.0
    # remove moeda/labels
    s = re.sub(r"[^\d,.\-]", "", s)
    # pt-br: 1.234,56
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0


@dataclass
class Empresa:
    ticker: str
    trading_name: str
    codigo_cvm: str


class CapturadorDividendosFuturos:
    """
    Captura dividendos/proventos em dinheiro (cash dividends) via B3 Listados.
    """

    BASE_LISTADOS = "https://sistemaswebb3-listados.b3.com.br"

    def __init__(self, dias: int = 30):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json,text/plain,*/*",
            }
        )

        self.pasta_balancos = Path("balancos")
        self.hoje = date.today()

        self.dias_janela = int(dias)
        self.total_novos = 0

        # agregado diário: SOMENTE novos desta execução
        self.dividendos_anunciados: List[Dict] = []

    # ---------------- PUBLIC ----------------
    def executar(
        self,
        modo: str = "completo",
        ticker: str = "",
        lista: str = "",
        quantidade: int = 10,
        dias: int = 30,
    ):
        print("🔮 CAPTURANDO DIVIDENDOS FUTUROS (FONTE OFICIAL: B3 LISTADOS)")
        print("=" * 78)

        self.dias_janela = int(dias)
        logger.info(f"🪟 Janela deslizante: últimos {self.dias_janela} dias")

        empresas = self._carregar_empresas(modo, ticker, lista, quantidade)

        for i, emp in enumerate(empresas, start=1):
            self._processar_empresa(emp, idx=i, total=len(empresas))
            time.sleep(1.1)  # rate limit leve (B3)

        if self.dividendos_anunciados:
            self._salvar_dividendos_anunciados()

        print("\n" + "=" * 78)
        print(f"✅ FINALIZADO: {self.total_novos} novos proventos encontrados na janela")
        print(f"📦 Compilado diário: {len(self.dividendos_anunciados)} itens (somente novos)")
        print("=" * 78)

    # ---------------- LOAD EMPRESAS ----------------
    def _carregar_empresas(self, modo: str, ticker: str, lista: str, quantidade: int) -> List[Empresa]:
        mapeamento_path = Path("mapeamento_tradingname_b3.csv")
        if not mapeamento_path.exists():
            logger.error("❌ mapeamento_tradingname_b3.csv não encontrado na raiz!")
            sys.exit(1)

        df = pd.read_csv(mapeamento_path, sep=";", encoding="utf-8")
        # mantém compatibilidade com seu arquivo
        if "status" in df.columns:
            df = df[df["status"] == "ok"].copy()

        empresas: List[Empresa] = []
        for _, row in df.iterrows():
            empresas.append(
                Empresa(
                    ticker=str(row.get("ticker", "")).strip().upper(),
                    trading_name=str(row.get("trading_name", "")).strip().upper(),
                    codigo_cvm=str(row.get("codigo", "")).strip(),
                )
            )

        if modo == "ticker":
            t = str(ticker).strip().upper()
            empresas = [e for e in empresas if e.ticker == t]

        elif modo == "lista":
            tickers_lista = [t.strip().upper() for t in str(lista).split(",") if t.strip()]
            empresas = [e for e in empresas if e.ticker in tickers_lista]

        elif modo == "quantidade":
            empresas = empresas[: int(quantidade)]

        # modo completo: mantém tudo
        logger.info(f"📊 {len(empresas)} empresas para processar")
        return empresas

    # ---------------- CORE ----------------
    def _processar_empresa(self, empresa: Empresa, idx: int, total: int):
        ticker = empresa.ticker
        trading_name = empresa.trading_name
        codigo_cvm = empresa.codigo_cvm

        print(f"\n{'='*78}")
        print(f"({idx}/{total}) 🔮 {ticker} | trading_name={trading_name} | CVM={codigo_cvm}")
        print(f"{'='*78}")

        existentes = self._carregar_proventos_existentes(ticker)
        logger.info(f"📌 Já capturados: {len(existentes)} itens (dedup)")

        # Janela deslizante
        data_inicio = self.hoje - timedelta(days=self.dias_janela)

        # Fonte oficial: B3 Listados
        # 1) Se trading_name vier vazio/errado, tenta obter via GetDetail (CVM) e usa o tradingName oficial
        trading_name_final = self._obter_trading_name_oficial(empresa) or trading_name
        if trading_name_final != trading_name:
            logger.info(f"🔁 trading_name ajustado via B3: {trading_name} → {trading_name_final}")
            trading_name = trading_name_final

        # 2) Busca proventos em dinheiro (cash dividends)
        itens_raw = self._b3_get_listed_cash_dividends(trading_name)

        # 3) Normaliza + filtra: futuro + janela --dias (por data ex/com/última atualização quando existir)
        novos: List[Dict] = []
        for item in itens_raw:
            norm = self._normalizar_item_b3(item)

            # Exigimos pagamento futuro
            dt_pag = _parse_any_date(norm.get("data_pagamento"))
            if not dt_pag or dt_pag < self.hoje:
                continue

            # Janela deslizante:
            # Considera "data_com" ou "data_ex" se existirem; senão usa "data_evento" (quando houver)
            dt_com = _parse_any_date(norm.get("data_com"))
            dt_ex = _parse_any_date(norm.get("data_ex"))
            dt_evt = _parse_any_date(norm.get("data_evento"))

            dentro_janela = False
            for dtx in (dt_com, dt_ex, dt_evt):
                if dtx and dtx >= data_inicio:
                    dentro_janela = True
                    break

            # Se não tiver nenhuma dessas datas no JSON, não bloqueia (mantém),
            # mas isso tende a ser raro nos payloads da B3.
            if (dt_com or dt_ex or dt_evt) and not dentro_janela:
                continue

            chave = self._chave_dedup(norm)
            if chave in existentes:
                continue

            novos.append(norm)

        if not novos:
            logger.info("✅ Sem novos dividendos nesta janela")
            return

        # 4) Salva incremental (antigos + novos)
        self._salvar_dividendos_incremental(ticker, novos)
        self.total_novos += len(novos)

        # 5) Agregado diário: só os novos desta execução
        for d in novos:
            item = dict(d)
            item["ticker"] = ticker
            item["trading_name"] = trading_name
            self.dividendos_anunciados.append(item)

        logger.info(f"💾 {ticker}: {len(novos)} novos (janela)")

    # ---------------- DEDUP ----------------
    def _carregar_proventos_existentes(self, ticker: str) -> Set[str]:
        arquivo = self.pasta_balancos / ticker / "dividendos_futuros.json"
        if not arquivo.exists():
            return set()

        try:
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
            existentes: Set[str] = set()
            for d in dados.get("dividendos", []):
                existentes.add(self._chave_dedup(d))
            return existentes
        except Exception:
            return set()

    def _chave_dedup(self, item: Dict) -> str:
        """
        Dedup forte: data_pagamento + valor_bruto(2 casas) + tipo
        """
        dt = str(item.get("data_pagamento", "")).strip()
        vl = float(item.get("valor_bruto", 0.0) or 0.0)
        tp = str(item.get("tipo", "")).strip().upper()
        return f"{dt}|{vl:.2f}|{tp}"

    # ---------------- B3 (OFICIAL) ----------------
    def _obter_trading_name_oficial(self, empresa: Empresa) -> Optional[str]:
        """
        Usa endpoint oficial GetDetail (B3 Listados) via codeCVM.
        Exemplo do próprio endpoint retornando tradingName e lastDate.
        """
        cvm = str(empresa.codigo_cvm).strip()
        if not cvm:
            return None

        params = {"codeCVM": cvm, "language": "pt-br"}
        b64 = _b64_params(params)
        url = f"{self.BASE_LISTADOS}/listedCompaniesProxy/CompanyCall/GetDetail/{quote(b64)}"

        try:
            resp = _safe_get(self.session, url, timeout=20)
            data = resp.json()
            tn = str(data.get("tradingName", "")).strip().upper()
            return tn or None
        except Exception as e:
            logger.warning(f"⚠️  GetDetail falhou para CVM={cvm}: {e}")
            return None

    def _b3_get_listed_cash_dividends(self, trading_name: str) -> List[Dict]:
        """
        Endpoint oficial (B3 Listados):
          /listedCompaniesProxy/CompanyCall/GetListedCashDividends/{base64}

        Paginação: pageNumber incremental até results vazio.
        """
        results: List[Dict] = []
        page = 1
        page_size = 120  # limite citado em mudanças de API

        while True:
            params = {
                "language": "pt-br",
                "pageNumber": page,
                "pageSize": page_size,
                "tradingName": str(trading_name).strip().upper(),
            }
            b64 = _b64_params(params)
            url = f"{self.BASE_LISTADOS}/listedCompaniesProxy/CompanyCall/GetListedCashDividends/{quote(b64)}"

            try:
                resp = _safe_get(self.session, url, timeout=25)
                payload = resp.json()
                batch = payload.get("results") if isinstance(payload, dict) else None
                if not batch:
                    break

                results.extend(batch)
                page += 1

                # proteção
                if page > 40:
                    break

                time.sleep(0.35)
            except Exception as e:
                logger.warning(f"⚠️  CashDividends falhou (page={page}) {trading_name}: {e}")
                break

        return results

    # ---------------- NORMALIZAÇÃO ----------------
    def _normalizar_item_b3(self, item: Dict) -> Dict:
        """
        Converte um item do JSON da B3 para o seu formato padrão:
          - data_pagamento (ISO string)
          - valor_bruto (float)
          - tipo (DIV/JCP etc)
          - data_com (ISO string opcional)
          - data_ex (ISO string opcional)
          - data_evento (melhor esforço, p/ janela)
          - fonte = B3_LISTADOS
          - raw = item original (para auditoria)
        """
        # Campos variam; tentamos múltiplos aliases comuns.
        # OBS: Sem quebrar caso a B3 altere o nome de campos.
        def pick(*keys):
            for k in keys:
                if k in item and item.get(k) not in (None, ""):
                    return item.get(k)
            return None

        # pagamento
        dt_pag = _parse_any_date(
            pick("paymentDate", "paymentdate", "payDate", "datePayment", "dataPagamento", "data_pagamento")
        )

        # com / ex
        dt_com = _parse_any_date(pick("lastDatePrior", "recordDate", "dataCom", "data_com"))
        dt_ex = _parse_any_date(pick("exDate", "lastDate", "dataEx", "data_ex"))

        # data_evento (para janela): tenta capturar uma data “de referência” do evento/anúncio
        dt_evt = _parse_any_date(
            pick("approvedOn", "approvalDate", "dateApproved", "createdAt", "lastDate", "dataEvento", "data_evento")
        )

        # valor
        valor = _parse_money(pick("rate", "value", "valor", "amount", "valorProvento", "valor_bruto"))

        # tipo
        tipo = str(pick("corporateActionType", "type", "proventoType", "tipo", "nature", "natureza") or "").strip().upper()
        if not tipo:
            tipo = "DIV"

        out = {
            "data_pagamento": dt_pag.isoformat() if dt_pag else None,
            "valor_bruto": float(valor),
            "tipo": tipo,
            "data_com": dt_com.isoformat() if dt_com else None,
            "data_ex": dt_ex.isoformat() if dt_ex else None,
            "data_evento": dt_evt.isoformat() if dt_evt else None,
            "fonte": "B3_LISTADOS",
            "raw": item,
        }
        return out

    # ---------------- SAVE ----------------
    def _salvar_dividendos_incremental(self, ticker: str, novos: List[Dict]):
        pasta = self.pasta_balancos / ticker
        pasta.mkdir(parents=True, exist_ok=True)

        arquivo = pasta / "dividendos_futuros.json"

        antigos: List[Dict] = []
        if arquivo.exists():
            try:
                dados_antigos = json.loads(arquivo.read_text(encoding="utf-8"))
                antigos = dados_antigos.get("dividendos", []) or []
            except Exception:
                antigos = []

        # merge + dedup final (safety)
        merged = antigos + novos
        seen: Set[str] = set()
        final: List[Dict] = []
        for d in merged:
            k = self._chave_dedup(d)
            if k in seen:
                continue
            seen.add(k)
            final.append(d)

        # ordena por data_pagamento
        final.sort(key=lambda x: (x.get("data_pagamento") or "", str(x.get("tipo") or "")))

        # período
        datas_pag = [d.get("data_pagamento") for d in final if d.get("data_pagamento")]
        periodo = {"inicio": None, "fim": None}
        if datas_pag:
            periodo["inicio"] = min(datas_pag)
            periodo["fim"] = max(datas_pag)

        dados = {
            "ticker": ticker,
            "ultima_atualizacao": datetime.now().isoformat(),
            "total_futuros": len(final),
            "janela_dias": int(self.dias_janela),
            "periodo": periodo,
            "dividendos": final,
        }

        arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    def _salvar_dividendos_anunciados(self):
        self.pasta_balancos.mkdir(parents=True, exist_ok=True)

        # ordena por data_pagamento + ticker
        ordenados = sorted(
            self.dividendos_anunciados,
            key=lambda x: (x.get("data_pagamento") or "", x.get("ticker") or ""),
        )

        dados = {
            "data_execucao": datetime.now().strftime("%Y-%m-%d"),
            "hora_execucao": datetime.now().strftime("%H:%M:%S"),
            "janela_dias": int(self.dias_janela),
            "total_proventos": len(ordenados),
            "total_empresas": len({d.get("ticker") for d in ordenados if d.get("ticker")}),
            "proventos": ordenados,
        }

        arquivo = self.pasta_balancos / "dividendos_anunciados.json"
        arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"📦 Compilado diário salvo: {arquivo} ({len(ordenados)} novos)")

# ---------------- CLI ----------------
def main():
    parser = argparse.ArgumentParser(description="Capturar dividendos futuros (B3 Listados - oficial)")
    parser.add_argument(
        "--modo",
        choices=["completo", "ticker", "lista", "quantidade"],
        default="completo",
        help="Modo de execução",
    )
    parser.add_argument("--ticker", default="", help="Ticker específico")
    parser.add_argument("--lista", default="", help="Lista de tickers (vírgula)")
    parser.add_argument("--quantidade", type=int, default=10, help="Qtd empresas (modo quantidade)")
    parser.add_argument("--dias", type=int, default=30, help="Dias para buscar (janela deslizante)")

    args = parser.parse_args()

    capturador = CapturadorDividendosFuturos(dias=args.dias)
    capturador.executar(
        modo=args.modo,
        ticker=args.ticker,
        lista=args.lista,
        quantidade=args.quantidade,
        dias=args.dias,
    )

if __name__ == "__main__":
    main()
