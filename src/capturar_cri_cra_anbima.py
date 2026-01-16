#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================
SCRAPER DE CRI E CRA ANBIMA - MERCADO SECUNDÁRIO (GitHub-ready)
===============================================================
Scraping direto da tabela HTML da página ANBIMA
URL:
https://www.anbima.com.br/pt_br/informar/precos-e-indices/precos/taxas-de-cri-e-cra/taxas-de-cri-e-cra.htm

- Faz GET na página
- Extrai Data de Referência (quando disponível)
- Localiza tabela principal (classe custom-anbi-ui-table, fallback para primeira table)
- Extrai cabeçalho + linhas
- Processa:
  - identifica coluna de indexador (índice/correção)
  - separa em DI_PERCENTUAL, DI_SPREAD, IPCA_SPREAD, IGPM
  - mantém classificação CRI/CRA via código (CRA* => CRA, senão CRI)
  - converte números BR e datas
- Salva JSON único e estável em site/data/cri_cra_anbima.json

Execução:
  python src/capturar_cri_cra_anbima.py
  python src/capturar_cri_cra_anbima.py --output site/data/cri_cra_anbima.json
  python src/capturar_cri_cra_anbima.py --quiet
"""

from __future__ import annotations

import argparse
import json
import re
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

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

    s = s.replace("\u00a0", "").replace(" ", "").replace("%", "")

    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")

    try:
        return float(s)
    except Exception:
        return np.nan


# -----------------------------
# Scraping
# -----------------------------

def buscar_cri_cra_anbima(verbose: bool = True) -> Optional[Dict[str, Any]]:
    """
    Busca dados de CRI e CRA fazendo scraping da página ANBIMA.
    Retorna dict com DataFrames separados por indexador.
    """
    URL = (
        "https://www.anbima.com.br/pt_br/informar/precos-e-indices/precos/"
        "taxas-de-cri-e-cra/taxas-de-cri-e-cra.htm"
    )

    if verbose:
        print("🔍 Buscando CRI e CRA da ANBIMA...\n")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        resp = requests.get(URL, headers=headers, timeout=30)

        if resp.status_code != 200:
            if verbose:
                print(f"❌ Erro ao acessar página: Status {resp.status_code}")
            return None

        if verbose:
            print("✅ Página acessada com sucesso!")

        soup = BeautifulSoup(resp.content, "html.parser")

        data_ref = extrair_data_referencia(soup)
        if verbose and data_ref:
            print(f"📅 Data de Referência: {data_ref}\n")

        tabela = soup.find("table", {"class": "custom-anbi-ui-table"})
        if not tabela:
            tabela = soup.find("table")

        if not tabela:
            if verbose:
                print("⚠️  Tabela não encontrada na página")
                print("💡 A estrutura da página pode ter mudado")
            return None

        df_raw = extrair_tabela_html(tabela, verbose=verbose)
        if df_raw is None or len(df_raw) == 0:
            if verbose:
                print("⚠️  Nenhum dado extraído da tabela")
            return None

        if verbose:
            print(f"\n✅ {len(df_raw)} CRI/CRA capturados\n")

        return processar_cri_cra(df_raw, data_ref, verbose=verbose)

    except Exception as e:
        if verbose:
            print(f"❌ Erro: {str(e)[:150]}")
        return None


def extrair_data_referencia(soup: BeautifulSoup) -> Optional[str]:
    """Extrai data de referência da página."""
    try:
        for tag in soup.find_all(["th", "td", "div", "span"]):
            texto = tag.get_text(strip=True)
            if "Data de Referência" in texto or "DATA DE REFERÊNCIA" in texto:
                m = re.search(r"\d{2}/\d{2}/\d{4}", texto)
                if m:
                    return m.group()
                prox = tag.find_next(["td", "span", "div"])
                if prox:
                    m = re.search(r"\d{2}/\d{2}/\d{4}", prox.get_text())
                    if m:
                        return m.group()
        return None
    except Exception:
        return None


def extrair_tabela_html(tabela, verbose: bool = True) -> Optional[pd.DataFrame]:
    """Extrai dados de uma tabela HTML mantendo sua lógica de header/tbody."""

    thead = tabela.find("thead")
    headers = []

    if thead:
        for row in thead.find_all("tr"):
            cells = row.find_all(["th", "td"])
            for cell in cells:
                txt = cell.get_text(strip=True)
                if txt and txt not in headers:
                    headers.append(txt)

    if not headers:
        tbody = tabela.find("tbody")
        if tbody:
            first_row = tbody.find("tr")
            if first_row:
                cells = first_row.find_all(["th", "td"])
                headers = [c.get_text(strip=True) for c in cells]

    if verbose:
        print(f"   📋 Cabeçalhos: {headers[:8]}...")

    tbody = tabela.find("tbody")
    if not tbody:
        tbody = tabela

    rows_data = []
    for row in tbody.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if len(cells) > 0:
            row_data = [c.get_text(strip=True) for c in cells]
            if row_data and (not headers or row_data[0] not in headers):
                rows_data.append(row_data)

    if len(rows_data) == 0:
        return None

    max_cols = max(len(r) for r in rows_data)

    if len(headers) < max_cols:
        headers.extend([f"Col_{i}" for i in range(len(headers), max_cols)])
    elif len(headers) > max_cols:
        headers = headers[:max_cols]

    for i, r in enumerate(rows_data):
        if len(r) < max_cols:
            rows_data[i] = r + [""] * (max_cols - len(r))
        elif len(r) > max_cols:
            rows_data[i] = r[:max_cols]

    return pd.DataFrame(rows_data, columns=headers)


# -----------------------------
# Processing (mantém lógica)
# -----------------------------

def processar_cri_cra(df: pd.DataFrame, data_ref: Optional[str], verbose: bool = True) -> Optional[Dict[str, Any]]:
    """Processa DataFrame de CRI/CRA mantendo a lógica original."""

    if verbose:
        print("📊 Processando dados...\n")

    df = df.copy()
    df = df.dropna(how="all").reset_index(drop=True)

    resultado: Dict[str, Any] = {
        "data_referencia": data_ref,
        "di_percentual": None,
        "di_spread": None,
        "ipca_spread": None,
        "igpm_spread": None,
    }

    # coluna indexador
    col_indice = None
    for col in df.columns:
        col_lower = str(col).lower()
        if ("índice" in col_lower) or ("indice" in col_lower) or ("correção" in col_lower) or ("correcao" in col_lower):
            col_indice = col
            break

    if not col_indice:
        if verbose:
            print("   ⚠️  Coluna de indexador não encontrada")
            print(f"   Colunas: {list(df.columns)[:10]}")
        return None

    if verbose:
        print(f"   📌 Coluna indexador: {col_indice}\n")

    # classifica CRI/CRA antes de separar (mantém)
    df["_tipo_temp"] = "N/A"
    if "Código" in df.columns:
        mask_cra = df["Código"].astype(str).str.contains(r"^CRA", case=False, na=False, regex=True)
        df.loc[mask_cra, "_tipo_temp"] = "CRA"
        df.loc[df["_tipo_temp"] == "N/A", "_tipo_temp"] = "CRI"

    df["_indice_str"] = df[col_indice].astype(str).str.upper()

    df_di_perc = df[df["_indice_str"].str.contains(r"%\s*DO\s*DI|%DO\s*DI|PERCENTUAL\s*DO\s*DI", case=False, na=False, regex=True)].copy()
    df_di_spread = df[df["_indice_str"].str.contains(r"DI\s*\+|DI\+", case=False, na=False, regex=True)].copy()
    df_ipca = df[df["_indice_str"].str.contains(r"IPCA\s*\+|IPCA\+", case=False, na=False, regex=True)].copy()
    df_igpm = df[df["_indice_str"].str.contains(r"IGP-M|IGPM|IGP\s*M", case=False, na=False, regex=True)].copy()

    if len(df_di_perc) > 0:
        resultado["di_percentual"] = limpar_e_formatar(df_di_perc, "DI_PERCENTUAL")
        if verbose:
            print(f"   ✅ DI Percentual: {len(df_di_perc)} ativos")

    if len(df_di_spread) > 0:
        resultado["di_spread"] = limpar_e_formatar(df_di_spread, "DI_SPREAD")
        if verbose:
            print(f"   ✅ DI + Spread: {len(df_di_spread)} ativos")

    if len(df_ipca) > 0:
        resultado["ipca_spread"] = limpar_e_formatar(df_ipca, "IPCA_SPREAD")
        if verbose:
            print(f"   ✅ IPCA + Spread: {len(df_ipca)} ativos")

    if len(df_igpm) > 0:
        resultado["igpm_spread"] = limpar_e_formatar(df_igpm, "IGPM")
        if verbose:
            print(f"   ✅ IGP-M: {len(df_igpm)} ativos")

    if verbose:
        print()

    return resultado


def limpar_e_formatar(df: pd.DataFrame, tipo: str) -> pd.DataFrame:
    """Limpa e formata DataFrame de CRI/CRA mantendo sua regra de mapeamento."""

    df = df.copy()

    colunas_map = {}
    for col in df.columns:
        col_clean = str(col).strip().upper()

        if "CÓDIGO" in col_clean or "CODIGO" in col_clean:
            colunas_map[col] = "Código"
        elif "EMISSOR" in col_clean or "NOME" in col_clean:
            colunas_map[col] = "Emissor"
        elif "RISCO" in col_clean and ("CRÉDITO" in col_clean or "CREDITO" in col_clean):
            colunas_map[col] = "Risco de Crédito"
        elif "SÉRIE" in col_clean or "SERIE" in col_clean:
            colunas_map[col] = "Série"
        elif "EMISSÃO" in col_clean or "EMISSAO" in col_clean:
            colunas_map[col] = "Emissão"
        elif "VENCIMENTO" in col_clean:
            colunas_map[col] = "Data Vencimento"
        elif (("ÍNDICE" in col_clean or "INDICE" in col_clean) and "TAXA" not in col_clean):
            colunas_map[col] = "Índice/Correção"
        elif "TAXA" in col_clean and "COMPRA" in col_clean:
            colunas_map[col] = "Taxa Compra"
        elif "TAXA" in col_clean and "VENDA" in col_clean:
            colunas_map[col] = "Taxa Venda"
        elif "TAXA" in col_clean and "INDICATIVA" in col_clean:
            colunas_map[col] = "Taxa Indicativa"
        elif "DESVIO" in col_clean and ("PADRÃO" in col_clean or "PADRAO" in col_clean):
            colunas_map[col] = "Desvio Padrão"
        elif col_clean == "PU":
            colunas_map[col] = "PU"
        elif "DURATION" in col_clean:
            colunas_map[col] = "Duration"
        elif "%" in col_clean and ("PU" in col_clean or "PAR" in col_clean):
            colunas_map[col] = "% PU Par"

    df = df.rename(columns=colunas_map)

    for col in df.columns:
        if any(t in col for t in ["Taxa", "PU", "Duration", "Desvio", "%"]):
            df[col] = df[col].apply(_to_num_br)

    for col in df.columns:
        if "Data" in col or "Vencimento" in col:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

    # mantém classificação anterior
    if "_tipo_temp" in df.columns:
        df["Tipo"] = df["_tipo_temp"]
        df = df.drop(columns=["_tipo_temp"])
    else:
        if "Código" in df.columns:
            mask_cra = df["Código"].astype(str).str.contains(r"^CRA", case=False, na=False, regex=True)
            df["Tipo"] = "CRI"
            df.loc[mask_cra, "Tipo"] = "CRA"
        else:
            df["Tipo"] = "N/A"

    df["Indexador"] = tipo.replace("_", "+")

    if "Código" in df.columns:
        df = df[df["Código"].notna()]
        df = df[df["Código"].astype(str).str.strip() != ""]

    if "_indice_str" in df.columns:
        df = df.drop(columns=["_indice_str"])

    # seu “debug”/reclassificação final (mantém)
    if "Tipo" in df.columns:
        tipo_counts = df["Tipo"].value_counts()
        if ("CRI" not in tipo_counts) or (tipo_counts.get("CRI", 0) == 0):
            if "Código" in df.columns:
                mask_cra = df["Código"].astype(str).str.match(r"^CRA\d+", case=False, na=False)
                df["Tipo"] = "CRI"
                df.loc[mask_cra, "Tipo"] = "CRA"

    return df.reset_index(drop=True)


# -----------------------------
# JSON output (estável em site/data)
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
        "tabelas": {},
    }

    for tipo in ["di_percentual", "di_spread", "ipca_spread", "igpm_spread"]:
        df = dados.get(tipo)
        if df is None or df.empty:
            payload["tabelas"][tipo] = None
        else:
            payload["tabelas"][tipo] = _df_to_rows(df)

    return payload


def salvar_json(payload: Dict[str, Any], output_path: str) -> None:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# -----------------------------
# CLI
# -----------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Captura CRI/CRA ANBIMA e salva JSON em site/data.")
    p.add_argument("--output", default="site/data/cri_cra_anbima.json", help="Caminho do JSON de saída")
    p.add_argument("--quiet", action="store_true", help="Modo silencioso")
    return p


def main() -> int:
    args = build_parser().parse_args()
    verbose = not bool(args.quiet)

    dados = buscar_cri_cra_anbima(verbose=verbose)
    if not dados:
        print("❌ Falha ao capturar CRI/CRA ANBIMA.")
        return 1

    payload = dados_to_payload(dados)
    salvar_json(payload, args.output)

    if verbose:
        print(f"💾 JSON salvo em: {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
