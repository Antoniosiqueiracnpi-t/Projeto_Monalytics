#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CAPTURADOR DE DIVIDENDOS FUTUROS (OFICIAL B3 LISTADOS) + JANELA DESLIZANTE + DEDUP
=================================================================================

✅ Fonte oficial:
- B3 Listados (sistemaswebb3-listados.b3.com.br) via endpoints proxy JSON.

✅ Por que essa versão funciona melhor do que o caminho Plantão/CVM RAD:
- Resolve o tradingName CANÔNICO via GetInitialCompanies (fluxo usado pela própria tela oficial)
- Evita GetDetail via codeCVM (que estava sendo chamado errado e gerando 403)

Fluxo:
1) Carrega mapeamento_tradingname_b3.csv
2) Para cada ticker:
   - Resolve tradingName canônico via GetInitialCompanies (B3)
   - Busca proventos em dinheiro via GetListedCashDividends (B3)
   - Janela deslizante --dias (filtra por data-com/ex/evento quando houver)
   - Dedup: lê balancos/{TICKER}/dividendos_futuros.json existente e só adiciona novos
3) Salva por ticker: balancos/{TICKER}/dividendos_futuros.json
4) Salva agregado diário (SOMENTE novos desta execução): balancos/dividendos_anunciados.json

Dependências:
pip install requests pandas

Exemplos:
  python src/capturar_dividendos_futuros.py --modo completo --dias 10
  python src/capturar_dividendos_futuros.py --modo lista --lista "ASAI3,POSI3,GRND3,BMGB4" --dias 20
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
from typing import Dict, List, Optional, Set
from urllib.parse import quote

import pandas as pd
import requests
from requests import Response


# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


# ---------------- DATA MODEL ----------------
@dataclass
class Empresa:
    ticker: str
    trading_name: str
    codigo: str  # pode ser código CVM numérico ou outro campo do seu CSV


# ---------------- HELPERS ----------------
def _parse_any_date(value) -> Optional[date]:
    """
    Parse tolerante:
      - dd/mm/yyyy
      - dd/mm/yyyy hh:mm:ss
      - yyyy-mm-dd
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() in ("nan", "none", "null"):
        return None

    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", s)
    if m:
        try:
            d, mth, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            return date(y, mth, d)
        except Exception:
            return None

    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            y, mth, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            return date(y, mth, d)
        except Exception:
            return None

    return None


def _parse_money(value) -> float:
    if value is None:
        return 0.0
    s = str(value).strip()
    if not s or s.lower() in ("nan", "none", "null"):
        return 0.0

    # mantém dígitos, . , e -
    s = re.sub(r"[^\d,.\-]", "", s)

    # pt-br: 1.234,56 -> 1234.56
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0


def _b64_str_dict(params: Dict) -> str:
    """
    A B3 Listados (proxy) usa base64 de str(dict) (com aspas simples) em vários endpoints.
    Mantemos esse formato.
    """
    raw = str(params).encode("ascii", errors="ignore")
    return base64.b64encode(raw).decode("ascii")


# ---------------- CAPTURADOR ----------------
class CapturadorDividendosFuturos:
    BASE = "https://sistemaswebb3-listados.b3.com.br"

    def __init__(self, dias: int = 30):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json,text/plain,*/*",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://sistemaswebb3-listados.b3.com.br/",
                "Origin": "https://sistemaswebb3-listados.b3.com.br",
            }
        )

        self.pasta_balancos = Path("balancos")
        self.hoje = date.today()

        self.dias_janela = int(dias) if dias and dias > 0 else 30
        self.total_novos = 0
        self.dividendos_anunciados: List[Dict] = []  # SOMENTE novos desta execução

    # -------------- PUBLIC --------------
    def executar(
        self,
        modo: str = "completo",
        ticker: str = "",
        lista: str = "",
        quantidade: int = 10,
        dias: int = 30,
    ):
        self.dias_janela = int(dias) if dias and dias > 0 else self.dias_janela

        print("🔮 CAPTURANDO DIVIDENDOS FUTUROS (B3 LISTADOS - OFICIAL) + JANELA DESLIZANTE")
        print("=" * 90)
        logger.info(f"🪟 Janela deslizante: últimos {self.dias_janela} dia(s)")
        print("=" * 90)

        empresas = self._carregar_empresas(modo, ticker, lista, quantidade)

        for i, emp in enumerate(empresas, start=1):
            self._processar_empresa(emp, i, len(empresas))
            time.sleep(1.1)  # rate-limit leve

        if self.dividendos_anunciados:
            self._salvar_dividendos_anunciados()

        print("\n" + "=" * 90)
        print(f"✅ FINALIZADO: {self.total_novos} novos proventos encontrados na janela")
        print(f"📦 Compilado diário: {len(self.dividendos_anunciados)} itens (somente novos)")
        print("=" * 90)

    # -------------- LOAD EMPRESAS --------------
    def _carregar_empresas(self, modo: str, ticker: str, lista: str, quantidade: int) -> List[Empresa]:
        mapeamento_path = Path("mapeamento_tradingname_b3.csv")
        if not mapeamento_path.exists():
            logger.error("❌ mapeamento_tradingname_b3.csv não encontrado na raiz!")
            sys.exit(1)

        df = pd.read_csv(mapeamento_path, sep=";", encoding="utf-8")
        if "status" in df.columns:
            df = df[df["status"] == "ok"].copy()

        empresas: List[Empresa] = []
        for _, row in df.iterrows():
            empresas.append(
                Empresa(
                    ticker=str(row.get("ticker", "")).strip().upper(),
                    trading_name=str(row.get("trading_name", "")).strip().upper(),
                    codigo=str(row.get("codigo", "")).strip(),
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

        logger.info(f"📊 {len(empresas)} empresas para processar")
        return empresas

    # -------------- CORE --------------
    def _processar_empresa(self, empresa: Empresa, idx: int, total: int):
        ticker = empresa.ticker
        print(f"\n{'='*90}")
        print(f"({idx}/{total}) 🔮 {ticker} | trading_name(CSV)={empresa.trading_name} | codigo={empresa.codigo}")
        print(f"{'='*90}")

        existentes = self._carregar_proventos_existentes(ticker)
        logger.info(f"📌 Já capturados: {len(existentes)} itens (dedup)")

        # ✅ Resolve tradingName canônico pelo fluxo oficial
        trading_name_b3 = self._b3_get_trading_name_por_ticker(ticker)
        if not trading_name_b3:
            logger.warning(f"⚠️  TradingName não resolvido via B3 Listados para {ticker} (root={self._ticker_root(ticker)})")
            logger.info("✅ Sem novos dividendos nesta janela")
            return

        logger.info(f"✅ tradingName(B3): {trading_name_b3}")

        # Busca proventos em dinheiro
        itens_raw = self._b3_get_listed_cash_dividends(trading_name_b3)

        # Janela
        data_inicio = self.hoje - timedelta(days=self.dias_janela)

        novos: List[Dict] = []
        for raw in itens_raw:
            norm = self._normalizar_item_b3(raw)

            # pagamento futuro
            dt_pag = _parse_any_date(norm.get("data_pagamento"))
            if not dt_pag or dt_pag < self.hoje:
                continue

            # janela: usa data_com/ex/evento se existirem
            dt_com = _parse_any_date(norm.get("data_com"))
            dt_ex = _parse_any_date(norm.get("data_ex"))
            dt_evt = _parse_any_date(norm.get("data_evento"))

            # se tiver alguma data de referência, aplica janela
            if dt_com or dt_ex or dt_evt:
                dentro = False
                for dtx in (dt_com, dt_ex, dt_evt):
                    if dtx and dtx >= data_inicio:
                        dentro = True
                        break
                if not dentro:
                    continue

            chave = self._chave_dedup(norm)
            if chave in existentes:
                continue

            novos.append(norm)
            existentes.add(chave)  # evita duplicar nesta execução

        if not novos:
            logger.info("✅ Sem novos dividendos nesta janela")
            return

        # salva incremental
        self._salvar_dividendos_incremental(ticker, novos)
        self.total_novos += len(novos)

        # agregado diário: somente novos
        for d in novos:
            item = dict(d)
            item["ticker"] = ticker
            item["trading_name"] = trading_name_b3
            self.dividendos_anunciados.append(item)

        logger.info(f"💾 {ticker}: {len(novos)} novos (janela)")

    # -------------- DEDUP --------------
    def _chave_dedup(self, item: Dict) -> str:
        dt = str(item.get("data_pagamento", "") or "").strip()
        vl = float(item.get("valor_bruto", 0.0) or 0.0)
        tp = str(item.get("tipo", "") or "").strip().upper()
        return f"{dt}|{vl:.2f}|{tp}"

    def _carregar_proventos_existentes(self, ticker: str) -> Set[str]:
        arquivo = self.pasta_balancos / ticker / "dividendos_futuros.json"
        if not arquivo.exists():
            return set()

        try:
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
            s: Set[str] = set()
            for d in dados.get("dividendos", []):
                s.add(self._chave_dedup(d))
            return s
        except Exception:
            return set()

    # -------------- B3 (OFICIAL) --------------
    def _ticker_root(self, ticker: str) -> str:
        """
        'ASAI3' -> 'ASAI', 'BMGB4' -> 'BMGB', 'BPAC11' -> 'BPAC'
        """
        t = (ticker or "").strip().upper()
        m = re.match(r"^([A-Z]{4,6})", t)
        return m.group(1) if m else t

    def _normalizar_trading_name_b3(self, trading_name: str) -> str:
        """
        Mantém somente A-Z0-9 (remove espaços, /, ., etc.)
        """
        s = (trading_name or "").upper()
        return re.sub(r"[^A-Z0-9]", "", s)

    def _safe_get(self, url: str, timeout: int = 25) -> Response:
        """
        GET robusto:
        - Primeiro com verify=True
        - Se SSL falhar, tenta verify=False
        - Se 403, tenta uma vez com headers reforçados (sem mascarar como erro de SSL)
        """
        try:
            r = self.session.get(url, timeout=timeout, verify=True)
            r.raise_for_status()
            return r
        except requests.exceptions.SSLError:
            logger.warning("⚠️  SSLError (verify=True). Tentando verify=False...")
            r = self.session.get(url, timeout=timeout, verify=False)
            r.raise_for_status()
            return r
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            if status == 403:
                # tenta uma vez com header reforçado
                logger.warning("⚠️  403 Forbidden. Reforçando headers e tentando novamente...")
                self.session.headers.update(
                    {
                        "X-Requested-With": "XMLHttpRequest",
                        "Connection": "keep-alive",
                    }
                )
                r2 = self.session.get(url, timeout=timeout, verify=True)
                if r2.status_code == 403:
                    # última tentativa sem verify (não por SSL, mas por compatibilidade ambiente)
                    r2 = self.session.get(url, timeout=timeout, verify=False)
                r2.raise_for_status()
                return r2
            raise

    def _b3_get_trading_name_por_ticker(self, ticker: str) -> Optional[str]:
        """
        ✅ Fluxo oficial: GetInitialCompanies -> achar issuingCompany == root(ticker) -> pegar tradingName
        """
        issuing = self._ticker_root(ticker)

        params = {"language": "pt-br", "pageNumber": 1, "pageSize": 50, "company": issuing}
        b64 = _b64_str_dict(params)
        url = f"{self.BASE}/listedCompaniesProxy/CompanyCall/GetInitialCompanies/{quote(b64)}"

        try:
            r = self._safe_get(url, timeout=25)
            js = r.json() or {}
            results = js.get("results") or []
            for it in results:
                if str(it.get("issuingCompany", "")).strip().upper() == issuing:
                    tn = str(it.get("tradingName", "")).strip()
                    return self._normalizar_trading_name_b3(tn) if tn else None
            return None
        except Exception as e:
            logger.warning(f"⚠️  Falha ao resolver tradingName para {ticker} (issuing={issuing}): {e}")
            return None

    def _b3_get_listed_cash_dividends(self, trading_name_b3: str) -> List[Dict]:
        """
        Endpoint oficial:
          /listedCompaniesProxy/CompanyCall/GetListedCashDividends/{base64}

        Paginação por pageNumber/pageSize.
        """
        resultados: List[Dict] = []
        page = 1
        page_size = 120

        while True:
            params = {
                "language": "pt-br",
                "pageNumber": page,
                "pageSize": page_size,
                "tradingName": trading_name_b3,
            }
            b64 = _b64_str_dict(params)
            url = f"{self.BASE}/listedCompaniesProxy/CompanyCall/GetListedCashDividends/{quote(b64)}"

            try:
                r = self._safe_get(url, timeout=30)
                js = r.json() or {}
                batch = js.get("results") or []
                if not batch:
                    break

                resultados.extend(batch)
                page += 1

                if page > 60:  # proteção
                    break

                time.sleep(0.35)
            except Exception as e:
                logger.warning(f"⚠️  Falha GetListedCashDividends (page={page}) {trading_name_b3}: {e}")
                break

        return resultados

    # -------------- NORMALIZAÇÃO --------------
    def _normalizar_item_b3(self, item: Dict) -> Dict:
        """
        Normaliza para o seu formato padrão.

        Campos mais comuns observados na B3:
        - paymentDate
        - lastDatePrior (muitas vezes o "com"/record date)
        - lastDate (muitas vezes ex-date)
        - rate (valor)
        - corporateActionType (DIV/JCP etc)
        - approvedOn / approvalDate (às vezes)
        """
        def pick(*keys):
            for k in keys:
                if k in item and item.get(k) not in (None, ""):
                    return item.get(k)
            return None

        dt_pag = _parse_any_date(pick("paymentDate", "datePayment", "dataPagamento", "data_pagamento"))
        dt_com = _parse_any_date(pick("lastDatePrior", "recordDate", "dataCom", "data_com"))
        dt_ex = _parse_any_date(pick("lastDate", "exDate", "dataEx", "data_ex"))
        dt_evt = _parse_any_date(pick("approvedOn", "approvalDate", "createdAt", "dataEvento", "data_evento"))

        valor = _parse_money(pick("rate", "value", "amount", "valor", "valorProvento", "valor_bruto"))

        tipo = str(pick("corporateActionType", "type", "proventoType", "tipo", "natureza") or "").strip().upper()
        if not tipo:
            tipo = "DIV"

        return {
            "data_pagamento": dt_pag.isoformat() if dt_pag else None,
            "valor_bruto": float(valor),
            "tipo": tipo,
            "data_com": dt_com.isoformat() if dt_com else None,
            "data_ex": dt_ex.isoformat() if dt_ex else None,
            "data_evento": dt_evt.isoformat() if dt_evt else None,
            "fonte": "B3_LISTADOS",
            "raw": item,  # auditoria (mantém)
        }

    # -------------- SAVE --------------
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

        merged = antigos + novos

        # dedup final
        seen: Set[str] = set()
        final: List[Dict] = []
        for d in merged:
            k = self._chave_dedup(d)
            if k in seen:
                continue
            seen.add(k)
            final.append(d)

        final.sort(key=lambda x: (x.get("data_pagamento") or "", str(x.get("tipo") or "")))

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
    parser.add_argument("--modo", choices=["completo", "ticker", "lista", "quantidade"], default="completo")
    parser.add_argument("--ticker", default="", help="Ticker específico")
    parser.add_argument("--lista", default="", help="Lista de tickers (vírgula)")
    parser.add_argument("--quantidade", type=int, default=10, help="Qtd empresas (modo quantidade)")
    parser.add_argument("--dias", type=int, default=30, help="Dias da janela deslizante")

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
