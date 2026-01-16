#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================
SCRAPER DE DEBÊNTURES ANBIMA - MERCADO SECUNDÁRIO (GitHub-ready)
===============================================================
Captura taxas de debêntures DI+Spread, IPCA+Spread, IGP-M e DI Percentual
URL base: https://www.anbima.com.br/informacoes/merc-sec-debentures/arqs/
Formato do arquivo: d{AA}{mes}{dia}.xls (ex.: d26jan16.xls)

- Busca a data (padrão: ontem) e tenta até N dias anteriores
- Lê planilhas: DI_SPREAD, IPCA_SPREAD, IGP-M, DI_PERCENTUAL (quando existirem)
- Processa a partir da linha 10 (índice 9), conforme sua lógica
- Converte números BR, converte Data Vencimento, classifica Indexador
- Salva JSON único e estável em site/data/debentures_anbima.json

Execução:
  python src/capturar_debentures_anbima.py
  python src/capturar_debentures_anbima.py --output site/data/debentures_anbima.json --days-back 10
  python src/capturar_debentures_anbima.py --data 16/01/2026
  python src/capturar_debentures_anbima.py --quiet
"""

from __future__ import annotations

import argparse
import json
import warnings
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import requests

warnings.filterwarnings("ignore")


# -----------------------------
# Helpers
# -----------------------------

def _to_num_br(x):
    """Converte strings BR para float."""
    import numpy as np

    if x is None:
        return np.nan

    try:
        if pd.isna(x):
            return np.nan
    except Exception:
        pass

    if isinstance(x, (int, float)):
        return float(x)

    s = str(x).strip()
    if s == "" or s.lower() in {"nan", "none", "-", "n.a.", "n.d.", "--"}:
        return np.nan

    s = s.replace("\u00a0", "").replace(" ", "")

    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")

    try:
        return float(s)
    except Exception:
        return np.nan


def _mes_para_sigla(mes: int) -> str:
    """Converte número do mês para sigla em português (padrão ANBIMA)."""
    meses = {
        1: "jan", 2: "fev", 3: "mar", 4: "abr",
        5: "mai", 6: "jun", 7: "jul", 8: "ago",
        9: "set", 10: "out", 11: "nov", 12: "dez",
    }
    return meses.get(mes, "")


# -----------------------------
# Download + Parse
# -----------------------------

def buscar_debentures_anbima(
    data: Optional[str] = None,
    tentar_dias_anteriores: bool = True,
    days_back: int = 10,
    verbose: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Busca dados de debêntures do mercado secundário ANBIMA.

    Retorna:
      dict com:
        data_referencia (str)
        di_spread / ipca_spread / igpm_spread / di_percentual (DataFrames ou None)
        fonte_url (str)
        nome_arquivo (str)
    """
    BASE_URL = "https://www.anbima.com.br/informacoes/merc-sec-debentures/arqs/"

    if data is None:
        data_obj = datetime.now() - timedelta(days=1)
    else:
        data_obj = datetime.strptime(data, "%d/%m/%Y")

    max_tentativas = max(1, days_back) if tentar_dias_anteriores else 1
    xls_result: Optional[pd.ExcelFile] = None
    data_str_br: Optional[str] = None
    fonte_url: Optional[str] = None
    nome_arquivo: Optional[str] = None

    if verbose:
        print("🔍 Buscando debêntures ANBIMA...\n")

    for tentativa in range(max_tentativas):
        data_str_br = data_obj.strftime("%d/%m/%Y")
        ano_curto = data_obj.strftime("%y")
        mes_sigla = _mes_para_sigla(data_obj.month)
        dia = data_obj.strftime("%d")

        nome_arquivo = f"d{ano_curto}{mes_sigla}{dia}.xls"
        url_completa = f"{BASE_URL}{nome_arquivo}"

        if verbose:
            print(f"📅 {data_str_br} - {nome_arquivo}", end=" ")

        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(url_completa, headers=headers, timeout=30)

            if response.status_code == 200 and len(response.content) > 1000:
                # ExcelFile detecta engine automaticamente (xls -> xlrd)
                xls_result = pd.ExcelFile(BytesIO(response.content))
                fonte_url = url_completa

                if verbose:
                    print("✅ ENCONTRADO!\n")
                    print(f"   URL: {url_completa}")
                    print(f"   Planilhas: {', '.join(xls_result.sheet_names)}\n")
                break
            else:
                if verbose:
                    print("❌")

        except Exception as e:
            if verbose:
                print(f"❌ {str(e)[:80]}")

        data_obj = data_obj - timedelta(days=1)

    if xls_result is None:
        if verbose:
            print(f"\n❌ Dados não encontrados nos últimos {max_tentativas} dias")
        return None

    dados = processar_debentures(xls_result, data_str_br, verbose=verbose)

    # anexa metadata
    dados["fonte_url"] = fonte_url
    dados["nome_arquivo"] = nome_arquivo

    return dados


def processar_debentures(xls: pd.ExcelFile, data_referencia: str, verbose: bool = True) -> Dict[str, Any]:
    """Processa o arquivo Excel de debêntures (mantém sua lógica)."""

    if verbose:
        print("📊 Processando planilhas...\n")

    resultado: Dict[str, Any] = {
        "data_referencia": data_referencia,
        "di_spread": None,
        "ipca_spread": None,
        "igpm_spread": None,
        "di_percentual": None,
    }

    mapeamento = {
        "DI_SPREAD": "di_spread",
        "IPCA_SPREAD": "ipca_spread",
        "IGP-M": "igpm_spread",
        "DI_PERCENTUAL": "di_percentual",
    }

    for sheet_name in xls.sheet_names:
        tipo = mapeamento.get(sheet_name)
        if not tipo:
            continue

        if verbose:
            print(f"   📄 {sheet_name:20}", end=" ")

        try:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
            df_processado = processar_planilha(df, tipo)

            if df_processado is not None and len(df_processado) > 0:
                resultado[tipo] = df_processado
                if verbose:
                    print(f"✅ {len(df_processado):3d} debêntures")
            else:
                if verbose:
                    print("⚠️  Vazio")

        except Exception as e:
            if verbose:
                print(f"❌ Erro: {str(e)[:80]}")

    if verbose:
        print()

    return resultado


def processar_planilha(df: pd.DataFrame, tipo: str) -> Optional[pd.DataFrame]:
    """Processa uma planilha específica (mantendo sua regra de linhas/colunas)."""

    if len(df) < 10:
        return None

    # Linha 9+ (índice 9+) = Dados
    df_dados = df.iloc[9:].copy()
    df_dados.columns = range(len(df_dados.columns))
    df_dados = df_dados.dropna(how="all").reset_index(drop=True)

    dados_limpos = []

    for _, row in df_dados.iterrows():
        codigo = row[0]

        if pd.isna(codigo):
            continue

        codigo_str = str(codigo).strip()
        if not codigo_str or len(codigo_str) < 4 or codigo_str.isdigit():
            continue

        registro = {
            "Código": codigo_str,
            "Emissor": str(row[1]).strip() if pd.notna(row[1]) else "",
            "Data Vencimento": row[2],
            "Índice/Correção": str(row[3]) if pd.notna(row[3]) else "",
            "Taxa Compra": _to_num_br(row[4]),
            "Taxa Venda": _to_num_br(row[5]),
            "Taxa Indicativa": _to_num_br(row[6]),
            "Desvio Padrão": _to_num_br(row[7]),
            "Intervalo Mín": _to_num_br(row[8]),
            "Intervalo Máx": _to_num_br(row[9]),
            "PU": _to_num_br(row[10]),
            "% PU Par": _to_num_br(row[11]),
            "Duration": _to_num_br(row[12]),
        }

        dados_limpos.append(registro)

    if not dados_limpos:
        return None

    df_result = pd.DataFrame(dados_limpos)

    # Converte datas
    df_result["Data Vencimento"] = pd.to_datetime(
        df_result["Data Vencimento"],
        errors="coerce",
        dayfirst=True,
    )
    df_result = df_result.dropna(subset=["Data Vencimento"])

    # Renomeia coluna e adiciona Indexador (mantém sua regra)
    if "di" in tipo and "percentual" not in tipo:
        df_result = df_result.rename(columns={"Taxa Indicativa": "Spread DI"})
        df_result["Indexador"] = "DI+SPREAD"
    elif "ipca" in tipo:
        df_result = df_result.rename(columns={"Taxa Indicativa": "Spread IPCA"})
        df_result["Indexador"] = "IPCA+SPREAD"
    elif "igpm" in tipo:
        df_result = df_result.rename(columns={"Taxa Indicativa": "Taxa IGPM"})
        df_result["Indexador"] = "IGP-M"
    else:
        df_result["Indexador"] = tipo.upper()

    df_result = df_result.sort_values("Data Vencimento").reset_index(drop=True)
    return df_result


# -----------------------------
# JSON (estável em site/data)
# -----------------------------

def _df_to_rows(df: pd.DataFrame) -> list:
    rows = []
    for _, r in df.iterrows():
        item = {}
        for c in df.columns:
            v = r[c]
            if pd.isna(v):
                item[c] = None
            elif isinstance(v, (int, float)):
                item[c] = float(v)
            elif isinstance(v, pd.Timestamp):
                item[c] = v.strftime("%Y-%m-%d")
            else:
                item[c] = str(v)
        rows.append(item)
    return rows


def dados_to_payload(dados: Dict[str, Any]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_referencia": dados.get("data_referencia"),
        "fonte_url": dados.get("fonte_url"),
        "nome_arquivo": dados.get("nome_arquivo"),
        "tabelas": {},
    }

    for tipo in ["di_spread", "ipca_spread", "igpm_spread", "di_percentual"]:
        df = dados.get(tipo)
        if df is None or df.empty:
            payload["tabelas"][tipo] = None
        else:
            # padroniza data vencimento em ISO no payload
            df2 = df.copy()
            if "Data Vencimento" in df2.columns:
                df2["Data Vencimento"] = pd.to_datetime(df2["Data Vencimento"], errors="coerce")
            payload["tabelas"][tipo] = _df_to_rows(df2)

    return payload


def salvar_json(payload: Dict[str, Any], output_path: str) -> None:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# -----------------------------
# CLI
# -----------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Captura debêntures ANBIMA (secundário) e salva JSON em site/data.")
    p.add_argument("--output", default="site/data/debentures_anbima.json", help="Caminho do JSON de saída")
    p.add_argument("--days-back", type=int, default=10, help="Quantos dias tentar para trás")
    p.add_argument("--data", default="", help="Data fixa DD/MM/YYYY (opcional)")
    p.add_argument("--quiet", action="store_true", help="Modo silencioso")
    return p


def main() -> int:
    args = build_parser().parse_args()
    data = args.data.strip() or None
    verbose = not bool(args.quiet)

    dados = buscar_debentures_anbima(
        data=data,
        tentar_dias_anteriores=True,
        days_back=args.days_back,
        verbose=verbose,
    )

    if dados is None:
        print("❌ Falha ao capturar debêntures ANBIMA.")
        return 1

    payload = dados_to_payload(dados)
    salvar_json(payload, args.output)

    if verbose:
        print(f"💾 JSON salvo em: {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
