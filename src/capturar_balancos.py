#!/usr/bin/env python3
"""
Captura balanços (DRE, BPA, BPP, DFC_MI) da CVM OpenData para 1 ticker por execução.

Saídas (em balancos/<TICKER>/):
- dre_trimestral.csv / dre_anual.csv
- bpa_trimestral.csv / bpa_anual.csv
- bpp_trimestral.csv / bpp_anual.csv
- dfc_trimestral.csv / dfc_anual.csv

Formato de saída compatível com seus normalizadores:
data_fim, trimestre, cd_conta, ds_conta, valor_mil
"""

from __future__ import annotations

import re
import sys
import zipfile
from io import BytesIO
from pathlib import Path
from datetime import date
from typing import Optional, Tuple, Dict, List

import pandas as pd
import requests


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
BALANCOS_DIR = REPO_ROOT / "balancos"
CACHE_DIR = REPO_ROOT / ".cache" / "cvm"

MAPPING_NAME = "mapeamento_final_b3_completo_utf8.csv"


def _norm_cnpj(cnpj: str) -> str:
    return re.sub(r"\D+", "", str(cnpj or "")).zfill(14)


def _find_mapping_csv() -> Optional[Path]:
    candidates = [
        REPO_ROOT / MAPPING_NAME,
        SRC_DIR / MAPPING_NAME,
        Path.cwd() / MAPPING_NAME,
        Path.cwd() / "src" / MAPPING_NAME,
        Path(str(Path.cwd())).parent / MAPPING_NAME,
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _quarter_from_date(dt: pd.Timestamp) -> Optional[str]:
    if pd.isna(dt):
        return None
    m = int(dt.month)
    if m == 3:
        return "T1"
    if m == 6:
        return "T2"
    if m == 9:
        return "T3"
    if m == 12:
        return "T4"
    return None


def _scale_to_mil_factor(scale: str) -> float:
    s = str(scale or "").strip().upper()
    # CVM costuma vir como "UNIDADE" ou "MIL"
    if "UNIDADE" in s:
        return 1.0 / 1000.0
    if "MILH" in s:  # MILHAO / MILHÕES
        return 1000.0
    if "MIL" in s:
        return 1.0
    # fallback conservador
    return 1.0


def _download_zip(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    dest.write_bytes(r.content)


def _read_csv_from_zip(zip_path: Path, inner_name: str) -> Optional[pd.DataFrame]:
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            if inner_name not in z.namelist():
                return None
            raw = z.read(inner_name)
        # CVM costuma ser latin1/iso e separador ';'
        return pd.read_csv(BytesIO(raw), sep=";", encoding="latin1", dtype=str)
    except Exception:
        return None


def _load_mapping_row(ticker: str) -> Tuple[Optional[str], Optional[str]]:
    mp = _find_mapping_csv()
    if mp is None:
        return (None, None)

    df = pd.read_csv(mp, sep=";", encoding="utf-8", dtype=str)
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()

    hit = df[df["ticker"] == ticker.upper().strip()]
    if hit.empty:
        return (None, None)

    cnpj = hit.iloc[0].get("cnpj")
    codigo_cvm = hit.iloc[0].get("codigo_cvm")
    cnpj_norm = _norm_cnpj(cnpj) if cnpj is not None else None
    codigo_cvm_norm = str(codigo_cvm).strip() if codigo_cvm is not None else None
    if codigo_cvm_norm in ("", "nan", "None"):
        codigo_cvm_norm = None
    return (cnpj_norm, codigo_cvm_norm)


def _get_cd_cvm_by_cnpj(cnpj_norm: str) -> Optional[str]:
    """
    Resolve CD_CVM usando o cadastro oficial (cad_cia_aberta.csv) pelo CNPJ.
    Cache simples em .cache/cvm/cad_cia_aberta.csv
    """
    url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cad_path = CACHE_DIR / "cad_cia_aberta.csv"

    if not cad_path.exists() or cad_path.stat().st_size == 0:
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        cad_path.write_bytes(r.content)

    cad = pd.read_csv(cad_path, sep=";", encoding="latin1", dtype=str)
    # colunas típicas: CNPJ_CIA, CD_CVM
    if "CNPJ_CIA" not in cad.columns or "CD_CVM" not in cad.columns:
        return None

    cad["CNPJ_CIA"] = cad["CNPJ_CIA"].astype(str).apply(_norm_cnpj)
    hit = cad[cad["CNPJ_CIA"] == cnpj_norm]
    if hit.empty:
        return None
    cd = str(hit.iloc[0]["CD_CVM"]).strip()
    return cd if cd and cd.lower() != "nan" else None


def _ensure_numeric(v: str) -> float:
    # CVM pode vir com vírgula
    s = str(v or "").strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return float("nan")


def _extract_statement(
    *,
    doc: str,         # "ITR" ou "DFP"
    year: int,
    demo: str,        # "DRE", "BPA", "BPP", "DFC_MI"
    cd_cvm: str,
) -> pd.DataFrame:
    """
    Lê o CSV de dentro do zip e retorna DataFrame já filtrado por CD_CVM.
    Tenta con_ antes de ind_.
    """
    doc_low = doc.lower()
    zip_url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/{doc}/DADOS/{doc_low}_cia_aberta_{year}.zip"
    zip_path = CACHE_DIR / doc / f"{doc_low}_cia_aberta_{year}.zip"
    _download_zip(zip_url, zip_path)

    # nomes internos no zip
    inner_con = f"{doc_low}_cia_aberta_{demo}_con_{year}.csv"
    inner_ind = f"{doc_low}_cia_aberta_{demo}_ind_{year}.csv"

    df = _read_csv_from_zip(zip_path, inner_con)
    if df is None:
        df = _read_csv_from_zip(zip_path, inner_ind)
    if df is None:
        return pd.DataFrame()

    if "CD_CVM" not in df.columns:
        return pd.DataFrame()

    df = df[df["CD_CVM"].astype(str).str.strip() == str(cd_cvm).strip()].copy()
    return df


def _to_output_format(df_raw: pd.DataFrame, *, force_trimestre_t4: bool = False) -> pd.DataFrame:
    """
    Converte formato CVM -> formato do projeto:
    data_fim, trimestre, cd_conta, ds_conta, valor_mil
    """
    if df_raw.empty:
        return pd.DataFrame(columns=["data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"])

    # colunas CVM típicas
    # DT_REFER, CD_CONTA, DS_CONTA, VL_CONTA, ESCALA_MOEDA
    for col in ["DT_REFER", "CD_CONTA", "DS_CONTA", "VL_CONTA"]:
        if col not in df_raw.columns:
            return pd.DataFrame(columns=["data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"])

    dt = pd.to_datetime(df_raw["DT_REFER"], errors="coerce")
    trimestre = dt.apply(_quarter_from_date)

    if force_trimestre_t4:
        trimestre = "T4"

    escala = df_raw["ESCALA_MOEDA"] if "ESCALA_MOEDA" in df_raw.columns else ""
    fator = escala.apply(_scale_to_mil_factor) if hasattr(escala, "apply") else 1.0

    vl = df_raw["VL_CONTA"].apply(_ensure_numeric)
    valor_mil = vl * fator

    out = pd.DataFrame(
        {
            "data_fim": dt.dt.strftime("%Y-%m-%d"),
            "trimestre": trimestre,
            "cd_conta": df_raw["CD_CONTA"].astype(str).str.strip(),
            "ds_conta": df_raw["DS_CONTA"].astype(str),
            "valor_mil": valor_mil,
        }
    )

    out = out.dropna(subset=["data_fim", "trimestre", "cd_conta"])
    out = out[out["trimestre"].isin(["T1", "T2", "T3", "T4"])].copy()
    return out


def _concat_years(parts: List[pd.DataFrame]) -> pd.DataFrame:
    if not parts:
        return pd.DataFrame(columns=["data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"])
    df = pd.concat(parts, ignore_index=True)
    # ordena por data e conta (ajuda consistência)
    df["data_fim_dt"] = pd.to_datetime(df["data_fim"], errors="coerce")
    df = df.sort_values(["data_fim_dt", "cd_conta"]).drop(columns=["data_fim_dt"])
    return df.reset_index(drop=True)


def capturar_ticker(ticker: str, anos: int = 12) -> int:
    ticker = ticker.upper().strip()
    if not ticker:
        print("[ERRO] Ticker vazio.")
        return 1

    if not BALANCOS_DIR.exists():
        BALANCOS_DIR.mkdir(parents=True, exist_ok=True)

    out_dir = BALANCOS_DIR / ticker
    out_dir.mkdir(parents=True, exist_ok=True)

    cnpj_norm, codigo_cvm = _load_mapping_row(ticker)
    if cnpj_norm is None:
        print(f"[ERRO] Ticker {ticker} não encontrado no {MAPPING_NAME}.")
        return 1

    cd_cvm = codigo_cvm or _get_cd_cvm_by_cnpj(cnpj_norm)
    if not cd_cvm:
        print(f"[ERRO] Não foi possível resolver CD_CVM para {ticker} (CNPJ {cnpj_norm}).")
        return 1

    current_year = date.today().year
    years = list(range(current_year - (anos - 1), current_year + 1))

    # --- ITR (trimestral) ---
    dre_tri_parts: List[pd.DataFrame] = []
    bpa_tri_parts: List[pd.DataFrame] = []
    bpp_tri_parts: List[pd.DataFrame] = []
    dfc_tri_parts: List[pd.DataFrame] = []

    for y in years:
        dre_raw = _extract_statement(doc="ITR", year=y, demo="DRE", cd_cvm=cd_cvm)
        bpa_raw = _extract_statement(doc="ITR", year=y, demo="BPA", cd_cvm=cd_cvm)
        bpp_raw = _extract_statement(doc="ITR", year=y, demo="BPP", cd_cvm=cd_cvm)

        # DFC preferencialmente MI; fallback MD
        dfc_raw = _extract_statement(doc="ITR", year=y, demo="DFC_MI", cd_cvm=cd_cvm)
        if dfc_raw.empty:
            dfc_raw = _extract_statement(doc="ITR", year=y, demo="DFC_MD", cd_cvm=cd_cvm)

        if not dre_raw.empty:
            dre_tri_parts.append(_to_output_format(dre_raw, force_trimestre_t4=False))
        if not bpa_raw.empty:
            bpa_tri_parts.append(_to_output_format(bpa_raw, force_trimestre_t4=False))
        if not bpp_raw.empty:
            bpp_tri_parts.append(_to_output_format(bpp_raw, force_trimestre_t4=False))
        if not dfc_raw.empty:
            dfc_tri_parts.append(_to_output_format(dfc_raw, force_trimestre_t4=False))

    dre_tri = _concat_years(dre_tri_parts)
    bpa_tri = _concat_years(bpa_tri_parts)
    bpp_tri = _concat_years(bpp_tri_parts)
    dfc_tri = _concat_years(dfc_tri_parts)

    # --- DFP (anual / T4) ---
    dre_anu_parts: List[pd.DataFrame] = []
    bpa_anu_parts: List[pd.DataFrame] = []
    bpp_anu_parts: List[pd.DataFrame] = []
    dfc_anu_parts: List[pd.DataFrame] = []

    for y in years:
        dre_raw = _extract_statement(doc="DFP", year=y, demo="DRE", cd_cvm=cd_cvm)
        bpa_raw = _extract_statement(doc="DFP", year=y, demo="BPA", cd_cvm=cd_cvm)
        bpp_raw = _extract_statement(doc="DFP", year=y, demo="BPP", cd_cvm=cd_cvm)

        dfc_raw = _extract_statement(doc="DFP", year=y, demo="DFC_MI", cd_cvm=cd_cvm)
        if dfc_raw.empty:
            dfc_raw = _extract_statement(doc="DFP", year=y, demo="DFC_MD", cd_cvm=cd_cvm)

        if not dre_raw.empty:
            dre_anu_parts.append(_to_output_format(dre_raw, force_trimestre_t4=True))
        if not bpa_raw.empty:
            bpa_anu_parts.append(_to_output_format(bpa_raw, force_trimestre_t4=True))
        if not bpp_raw.empty:
            bpp_anu_parts.append(_to_output_format(bpp_raw, force_trimestre_t4=True))
        if not dfc_raw.empty:
            dfc_anu_parts.append(_to_output_format(dfc_raw, force_trimestre_t4=True))

    dre_anu = _concat_years(dre_anu_parts)
    bpa_anu = _concat_years(bpa_anu_parts)
    bpp_anu = _concat_years(bpp_anu_parts)
    dfc_anu = _concat_years(dfc_anu_parts)

    # grava (mesmo vazio, grava cabeçalho para não quebrar pipeline)
    dre_tri.to_csv(out_dir / "dre_trimestral.csv", index=False)
    dre_anu.to_csv(out_dir / "dre_anual.csv", index=False)

    bpa_tri.to_csv(out_dir / "bpa_trimestral.csv", index=False)
    bpa_anu.to_csv(out_dir / "bpa_anual.csv", index=False)

    bpp_tri.to_csv(out_dir / "bpp_trimestral.csv", index=False)
    bpp_anu.to_csv(out_dir / "bpp_anual.csv", index=False)

    dfc_tri.to_csv(out_dir / "dfc_trimestral.csv", index=False)
    dfc_anu.to_csv(out_dir / "dfc_anual.csv", index=False)

    print(f"[OK] Captura finalizada: {ticker} (CD_CVM={cd_cvm}) -> {out_dir}")
    return 0


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Uso: python src/capturar_balancos.py <TICKER> [--anos N]")
        return 1

    ticker = argv[1].strip().upper()
    anos = 12
    if "--anos" in argv:
        try:
            i = argv.index("--anos")
            anos = int(argv[i + 1])
        except Exception:
            anos = 12

    return capturar_ticker(ticker, anos=anos)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
