#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAPTURADOR DE DIVIDENDOS FUTUROS (B3 LISTADOS - OFICIAL) COM JANELA DESLIZANTE
============================================================================

Fluxo:
1) Carrega mapeamento_tradingname_b3.csv
2) Para cada ticker:
   - Resolve tradingName via GetInitialCompanies (por ticker)
   - Busca eventos em dinheiro via GetListedCashDividends (por tradingName)
   - Filtra pela janela --dias (aprovacao/com/pagamento) e pagamento >= hoje
   - Dedup incremental (lendo dividendos_futuros.json existente)
3) Salva por ticker: balancos/{TICKER}/dividendos_futuros.json
4) Salva agregado diário (somente novos da janela): balancos/dividendos_anunciados.json

Obs importante:
- A B3 usa base64 de JSON (btoa(JSON.stringify(obj))). NÃO use str(dict).
- Endpoints "listedCompaniesProxy" são os mesmos consumidos pelo site "Empresas Listadas".

Dependências:
pip install requests pandas
"""

import argparse
import base64
import json
import logging
import re
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
import requests
from requests.exceptions import SSLError, HTTPError, RequestException

# ---------------- LOG ----------------
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# ---------------- B3 LISTADOS (OFICIAL DO SITE) ----------------
B3_BASE = "https://sistemaswebb3-listados.b3.com.br"
END_INITIAL = f"{B3_BASE}/listedCompaniesProxy/CompanyCall/GetInitialCompanies/"
END_CASHDIV = f"{B3_BASE}/listedCompaniesProxy/CompanyCall/GetListedCashDividends/"

# Página (para Referer/Origin)
B3_REFERER = f"{B3_BASE}/listedCompaniesPage/"


def _b64_json(params: Dict) -> str:
    """
    Token correto do site: btoa(JSON.stringify(params))
    => base64 do JSON (aspas duplas), em UTF-8, sem espaços.
    """
    s = json.dumps(params, ensure_ascii=False, separators=(",", ":"))
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def _parse_date_br(txt: str) -> Optional[date]:
    if txt is None:
        return None
    s = str(txt).strip()
    if not s:
        return None

    # comuns: "07/01/2026" ou "07/01/2026 23:12:12"
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", s)
    if m:
        dd, mm, yyyy = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(yyyy, mm, dd)
        except ValueError:
            return None
    return None


def _parse_float_money(txt) -> float:
    if txt is None or (isinstance(txt, float) and pd.isna(txt)):
        return 0.0
    s = str(txt).strip()
    if not s:
        return 0.0
    # remove moeda/símbolos
    s = re.sub(r"[^\d,.\-]", "", s)
    # pt-BR: 1.234,56 => 1234.56
    if s.count(",") == 1 and s.count(".") >= 1:
        s = s.replace(".", "").replace(",", ".")
    else:
        # se vier "0.31" ok; se vier "0,31" troca
        if s.count(",") == 1 and s.count(".") == 0:
            s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


class CapturadorDividendosFuturos:
    def __init__(self, dias: int = 30):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": B3_REFERER,
            "Origin": B3_BASE,
            "Connection": "keep-alive",
        })

        self.pasta_balancos = Path("balancos")
        self.hoje = date.today()

        self.dias_janela = int(dias)
        self.total_novos = 0
        self.dividendos_anunciados: List[Dict] = []  # somente novos da execução

    # ---------------- PUBLIC ----------------
    def executar(self, modo: str = "completo", ticker: str = "", lista: str = "", quantidade: int = 10, dias: int = 30):
        self.dias_janela = int(dias)
        print("🔮 CAPTURANDO DIVIDENDOS FUTUROS (FONTE OFICIAL: B3 LISTADOS)")
        print("=" * 78)
        print(f"🪟 Janela deslizante: últimos {self.dias_janela} dias")

        empresas = self._carregar_empresas(modo, ticker, lista, quantidade)
        if not empresas:
            logger.warning("⚠️  Nenhuma empresa selecionada.")
            return

        for i, empresa in enumerate(empresas, start=1):
            print("\n" + "=" * 78)
            print(f"({i}/{len(empresas)}) 🔮 {empresa['ticker']} | trading_name={empresa.get('trading_name','')}")
            print("=" * 78)
            try:
                self._processar_empresa(empresa)
            except Exception as e:
                logger.warning(f"⚠️  Falha em {empresa['ticker']}: {e}")
            time.sleep(1.2)  # rate limiting leve

        if self.dividendos_anunciados:
            self._salvar_dividendos_anunciados()

        print("\n" + "=" * 78)
        print(f"✅ FINALIZADO: {self.total_novos} novos proventos encontrados na janela")
        print(f"📦 Compilado diário: {len(self.dividendos_anunciados)} itens (somente novos)")
        print("=" * 78)

    # ---------------- CORE ----------------
    def _carregar_empresas(self, modo, ticker, lista, quantidade):
        mapeamento_path = Path("mapeamento_tradingname_b3.csv")
        if not mapeamento_path.exists():
            logger.error("❌ mapeamento_tradingname_b3.csv não encontrado na raiz!")
            sys.exit(1)

        df = pd.read_csv(mapeamento_path, sep=";", encoding="utf-8")
        if "status" in df.columns:
            df = df[df["status"] == "ok"].copy()

        empresas = []
        for _, row in df.iterrows():
            empresas.append({
                "ticker": str(row.get("ticker", "")).strip().upper(),
                "trading_name": str(row.get("trading_name", "")).strip().upper(),
                "codigo": str(row.get("codigo", "")).strip(),  # pode existir, mas não dependemos disso
            })

        if modo == "ticker":
            empresas = [e for e in empresas if e["ticker"] == str(ticker).strip().upper()]
        elif modo == "lista":
            tickers_lista = [t.strip().upper() for t in str(lista).split(",") if t.strip()]
            empresas = [e for e in empresas if e["ticker"] in tickers_lista]
        elif modo == "quantidade":
            empresas = empresas[: int(quantidade)]
        elif modo == "completo":
            pass

        logger.info(f"📊 {len(empresas)} empresas para processar")
        return empresas

    def _processar_empresa(self, empresa: Dict):
        ticker = empresa["ticker"]

        existentes = self._carregar_proventos_existentes(ticker)
        logger.info(f"📌 Já capturados: {len(existentes)} itens (dedup)")

        # 1) resolve tradingName oficial via B3 (se falhar, tenta do CSV)
        trading_name_oficial = self._resolver_trading_name(ticker) or empresa.get("trading_name", "").strip()
        if not trading_name_oficial:
            logger.warning("⚠️  tradingName vazio (não foi possível resolver). Pulando.")
            return

        # 2) busca eventos em dinheiro
        eventos = self._buscar_cash_dividends(trading_name_oficial)

        # 3) filtra janela + pagamento futuro
        ini = self.hoje - timedelta(days=self.dias_janela)
        novos = []

        for ev in eventos:
            # campos comuns da B3 (podem variar):
            # - lastDatePrior (data com), approvedOn (aprovação), paymentDate (pagamento)
            dt_com = _parse_date_br(ev.get("lastDatePrior"))
            dt_aprov = _parse_date_br(ev.get("approvedOn"))
            dt_pag = _parse_date_br(ev.get("paymentDate"))

            # escolhe uma "data do anúncio" para janela:
            dt_ref = dt_aprov or dt_com or dt_pag
            if not dt_ref:
                continue
            if dt_ref < ini:
                continue

            # futuro = pagamento >= hoje (se não tiver pagamento, ignora)
            if not dt_pag or dt_pag < self.hoje:
                continue

            valor = _parse_float_money(ev.get("rate"))
            tipo = str(ev.get("typeName") or ev.get("label") or ev.get("type") or "DIV").strip()

            item = {
                "data_pagamento": dt_pag.isoformat(),
                "valor_bruto": float(valor),
                "tipo": tipo,
                "data_com": dt_com.isoformat() if dt_com else None,
                "data_aprovacao": dt_aprov.isoformat() if dt_aprov else None,
                "fonte": "B3_LISTADOS",
                "trading_name": trading_name_oficial,
                "ticker": ticker,
                "raw": ev,  # mantém bruto para auditoria (não atrapalha consumo)
            }

            chave = self._chave_dedup(item)
            if chave in existentes:
                continue

            novos.append(item)

        if not novos:
            logger.info("✅ Sem novos dividendos nesta janela")
            return

        # 4) salva incremental (antigos + novos)
        self._salvar_dividendos_incremental(ticker, novos)
        self.total_novos += len(novos)

        # 5) agregado diário = só novos
        for x in novos:
            self.dividendos_anunciados.append({
                k: x[k] for k in [
                    "ticker", "trading_name", "tipo", "valor_bruto",
                    "data_com", "data_aprovacao", "data_pagamento", "fonte"
                ]
            })

        logger.info(f"✅ {ticker}: {len(novos)} novos proventos")

    # ---------------- B3 REQUESTS ----------------
    def _get_json_b3(self, url: str, params: Dict, timeout: int = 15) -> Dict:
        token = _b64_json(params)
        full = url + token

        try:
            r = self.session.get(full, timeout=timeout, verify=True)
            r.raise_for_status()
            return r.json()
        except SSLError:
            # fallback em ambientes que reclamam de SSL (alguns runners)
            logger.warning("⚠️  SSL falhou (verify=True). Tentando verify=False...")
            r = self.session.get(full, timeout=timeout, verify=False)
            r.raise_for_status()
            return r.json()
        except HTTPError as e:
            # log detalhado
            status = getattr(e.response, "status_code", None)
            text = getattr(e.response, "text", "")[:300]
            raise RuntimeError(f"HTTP {status} em {full} | {text}") from e
        except RequestException as e:
            raise RuntimeError(f"Falha request em {full}: {e}") from e
        except ValueError as e:
            raise RuntimeError(f"Resposta não-JSON em {full}: {e}") from e

    def _resolver_trading_name(self, ticker: str) -> str:
        """
        Resolve tradingName via GetInitialCompanies (busca por ticker).
        Preferimos isso pois é o que o próprio site usa.
        """
        params = {"language": "pt-br", "pageNumber": 1, "pageSize": 50, "company": ticker}
        data = self._get_json_b3(END_INITIAL, params)

        results = data.get("results") or []
        if not results:
            return ""

        # tenta achar a linha exata do ticker em otherCodes/code
        ticker_u = ticker.upper()
        best = None
        for it in results:
            code = str(it.get("code", "")).upper()
            if code == ticker_u:
                best = it
                break
            other = it.get("otherCodes") or []
            if any(str(o.get("code", "")).upper() == ticker_u for o in other):
                best = it
                break

        if not best:
            best = results[0]

        trading = str(best.get("tradingName", "")).strip()
        # site remove "/" e "." no tradingName para chamadas
        trading = trading.replace("/", "").replace(".", "")
        return trading

    def _buscar_cash_dividends(self, trading_name: str) -> List[Dict]:
        """
        Busca eventos corporativos em dinheiro (cash dividends) via B3 Listados.
        Faz paginação até esgotar.
        """
        all_results: List[Dict] = []
        page = 1

        while True:
            params = {
                "language": "pt-br",
                "pageNumber": page,
                "pageSize": 120,
                "tradingName": trading_name
            }
            data = self._get_json_b3(END_CASHDIV, params)
            results = data.get("results") or []
            if not results:
                break
            all_results.extend(results)
            page += 1

            # safety: evita loop infinito se algo mudar
            if page > 50:
                break

        return all_results

    # ---------------- DEDUP / SAVE ----------------
    def _chave_dedup(self, item: Dict) -> str:
        # chave estável para não duplicar: pagamento + valor + tipo + com
        dp = item.get("data_pagamento") or ""
        vc = f"{float(item.get('valor_bruto', 0.0)):.6f}"
        tp = (item.get("tipo") or "").strip().upper()
        dc = item.get("data_com") or ""
        return f"{dp}|{vc}|{tp}|{dc}"

    def _carregar_proventos_existentes(self, ticker: str) -> Set[str]:
        arquivo = self.pasta_balancos / ticker / "dividendos_futuros.json"
        if not arquivo.exists():
            return set()

        try:
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
            existentes = set()
            for d in dados.get("dividendos", []):
                # aceita tanto formato antigo quanto novo
                dp = d.get("data_pagamento") or ""
                vc = f"{float(d.get('valor_bruto', 0.0)):.6f}"
                tp = (d.get("tipo") or "").strip().upper()
                dc = d.get("data_com") or ""
                existentes.add(f"{dp}|{vc}|{tp}|{dc}")
            return existentes
        except Exception:
            return set()

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

        dividendos = antigos + novos

        # período (min/max pagamento) só com itens válidos
        pagamentos = [d.get("data_pagamento") for d in dividendos if d.get("data_pagamento")]
        periodo = {
            "inicio": min(pagamentos) if pagamentos else None,
            "fim": max(pagamentos) if pagamentos else None
        }

        dados = {
            "ticker": ticker,
            "ultima_atualizacao": datetime.now().isoformat(),
            "janela_dias": self.dias_janela,
            "total_futuros": len(dividendos),
            "periodo": periodo,
            "dividendos": dividendos
        }

        arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"💾 {ticker}: +{len(novos)} novos → total {len(dividendos)}")

    def _salvar_dividendos_anunciados(self):
        self.pasta_balancos.mkdir(exist_ok=True)

        ordenados = sorted(
            self.dividendos_anunciados,
            key=lambda x: (x.get("data_pagamento", ""), x.get("ticker", ""))
        )

        dados = {
            "data_execucao": datetime.now().strftime("%Y-%m-%d"),
            "hora_execucao": datetime.now().strftime("%H:%M:%S"),
            "janela_dias": self.dias_janela,
            "total_proventos": len(ordenados),
            "total_empresas": len({d["ticker"] for d in ordenados}),
            "proventos": ordenados
        }

        arquivo = self.pasta_balancos / "dividendos_anunciados.json"
        arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"💾 Compilado diário salvo: {arquivo} ({len(ordenados)} proventos)")


def main():
    parser = argparse.ArgumentParser(description="Capturar dividendos futuros (B3 Listados - oficial)")
    parser.add_argument("--modo", choices=["completo", "ticker", "lista", "quantidade"],
                        default="completo", help="Modo de execução")
    parser.add_argument("--ticker", default="", help="Ticker específico")
    parser.add_argument("--lista", default="", help="Lista de tickers (vírgula)")
    parser.add_argument("--quantidade", type=int, default=10, help="Qtd empresas (modo quantidade)")
    parser.add_argument("--dias", type=int, default=30, help="Dias para janela deslizante (dedup + filtro por anúncio/com/pagamento)")

    args = parser.parse_args()

    capturador = CapturadorDividendosFuturos(dias=args.dias)
    capturador.executar(args.modo, args.ticker, args.lista, args.quantidade, args.dias)


if __name__ == "__main__":
    main()
