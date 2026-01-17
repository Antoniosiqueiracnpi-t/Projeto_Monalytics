#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================
ANALISADOR CONSOLIDADO DE RENDA FIXA (ANBIMA)
===============================================================
- Lê:
  - site/data/debentures_anbima.json
  - site/data/cri_cra_anbima.json
- Monta 6 DataFrames:
  - deb_ipca_spread, deb_di_spread, deb_di_percentual
  - cri_cra_ipca_spread, cri_cra_di_spread, cri_cra_di_percentual
- Executa analisar_portfolios() (mesma lógica do usuário)
- Adiciona:
  - estatísticas gerais
  - TOP 10 spreads IPCA+
  - TOP 10 spreads DI+
- Salva:
  - site/data/portfolio_renda_fixa.json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------

def _read_json(path: str) -> Optional[dict]:
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        # fallback
        return json.loads(p.read_text(encoding="utf-8-sig"))


def _extract_tables_payload(payload: dict) -> dict:
    """
    Extrai a seção 'tabelas' do JSON.
    Espera formato (como os scripts anteriores):
      { ..., "tabelas": { "ipca_spread": [...], ... } }
    """
    if not isinstance(payload, dict):
        return {}
    if "tabelas" in payload and isinstance(payload["tabelas"], dict):
        return payload["tabelas"]
    # fallback: alguns scripts podem ter outro layout
    return payload


def _rows_to_df(rows: Any) -> pd.DataFrame:
    if rows is None:
        return pd.DataFrame()
    if isinstance(rows, list):
        try:
            return pd.DataFrame(rows)
        except Exception:
            return pd.DataFrame()
    if isinstance(rows, dict):
        # se vier dict com lista dentro
        for v in rows.values():
            if isinstance(v, list):
                return pd.DataFrame(v)
    return pd.DataFrame()


def _safe_datetime_now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------
# Sua função (mantida, só encapsulada)
# ---------------------------------------------------------------------

def analisar_portfolios(deb_ipca_spread, deb_di_spread, deb_di_percentual,
                        cri_cra_ipca_spread, cri_cra_di_spread, cri_cra_di_percentual) -> pd.DataFrame:
    """
    Analisa 6 dataframes de renda fixa e retorna resumo consolidado.
    (Mantém toda a lógica e cálculos fornecidos)
    """

    # ---------- Helpers robustos ----------
    def _normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza nomes e remove espaços duplicados."""
        if df is None or len(df) == 0:
            return pd.DataFrame()
        df = df.copy()
        df.columns = [re.sub(r'\s+', ' ', str(c)).strip() for c in df.columns]
        return df

    def _dedup_coalesce_cols(df: pd.DataFrame) -> pd.DataFrame:
        """
        Para cada nome duplicado, coalesce linha a linha usando o primeiro valor não-nulo
        e mantém apenas UMA coluna por nome. Garante colunas únicas no final.
        """
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.copy()

        # agrupar posições por nome de coluna
        name_to_idx = defaultdict(list)
        for i, col in enumerate(df.columns):
            name_to_idx[col].append(i)

        cols_out = {}
        for name, idxs in name_to_idx.items():
            if len(idxs) == 1:
                cols_out[name] = df.iloc[:, idxs[0]]
            else:
                bloco = df.iloc[:, idxs]
                # primeiro valor não nulo por linha
                coalescida = bloco.bfill(axis=1).iloc[:, 0]
                cols_out[name] = coalescida

        df_coalescido = pd.DataFrame(cols_out, index=df.index)
        return df_coalescido

    def _coalesce_series(df: pd.DataFrame, candidates) -> pd.Series:
        """
        Retorna uma Series unificada procurando pelos nomes (ou regex exata) em 'candidates'.
        """
        if df is None or df.empty:
            return pd.Series(dtype=float)
        if isinstance(candidates, str):
            candidates = [candidates]

        for name in candidates:
            # match exato (case-insensitive)
            exact = [c for c in df.columns if c.lower() == str(name).lower()]
            if exact:
                s = pd.to_numeric(df[exact[0]], errors='coerce')
                return s

            # regex exata da string inteira (já normalizada)
            pat = re.compile(rf'^{re.escape(str(name))}$', re.IGNORECASE)
            cols = [c for c in df.columns if pat.match(str(c))]
            if cols:
                s = pd.to_numeric(df[cols[0]], errors='coerce')
                return s

        return pd.Series([np.nan] * len(df), index=df.index, dtype=float)

    def _metricas(df: pd.DataFrame, cand_taxa):
        if df is None or df.empty:
            return {'taxa_media': np.nan, 'taxa_maxima': np.nan,
                    'pu_par_medio': np.nan, 'duration_media': np.nan}

        taxa_valida = _coalesce_series(df, cand_taxa)
        pu_par_val  = _coalesce_series(df, ['% PU Par', '%PU Par', 'PU Par %'])
        duration    = _coalesce_series(df, ['Duration', 'Duration (dias)'])

        return {
            'taxa_media': taxa_valida.mean(skipna=True),
            'taxa_maxima': taxa_valida.max(skipna=True),
            'pu_par_medio': pu_par_val.mean(skipna=True),
            'duration_media': duration.mean(skipna=True)
        }

    def _safe_round(x, ndigits):
        return (round(float(x), ndigits) if pd.notna(x) else np.nan)

    # ---------- Normalizar + deduplicar cada DF ----------
    def _prep(df):
        return _dedup_coalesce_cols(_normalize_cols(df))

    deb_ipca_spread       = _prep(deb_ipca_spread)
    deb_di_spread         = _prep(deb_di_spread)
    deb_di_percentual     = _prep(deb_di_percentual)
    cri_cra_ipca_spread   = _prep(cri_cra_ipca_spread)
    cri_cra_di_spread     = _prep(cri_cra_di_spread)
    cri_cra_di_percentual = _prep(cri_cra_di_percentual)

    # ---------- Concat por indexador + dedup após concat ----------
    df_ipca = _dedup_coalesce_cols(pd.concat([deb_ipca_spread, cri_cra_ipca_spread],
                                             ignore_index=True, sort=False))
    total_titulos_ipca = len(df_ipca)

    df_cdi_spread = _dedup_coalesce_cols(pd.concat([deb_di_spread, cri_cra_di_spread],
                                                   ignore_index=True, sort=False))
    total_titulos_cdi = len(df_cdi_spread)

    df_cdi_perc = _dedup_coalesce_cols(pd.concat([deb_di_percentual, cri_cra_di_percentual],
                                                 ignore_index=True, sort=False))
    total_titulos_perc = len(df_cdi_perc)

    total_geral = total_titulos_ipca + total_titulos_cdi + total_titulos_perc
    if total_geral == 0:
        return pd.DataFrame([{
            'Indexador': 'TOTAL',
            'Distribuição (%)': 100.00,
            'Quantidade Títulos': 0,
            'PU/Par Médio (%)': np.nan,
            'Duration Média (dias)': np.nan,
            'Taxa Indicativa Média (%)': np.nan,
            'Maior Taxa (%)': np.nan
        }])

    # ---------- Métricas (com aliases de colunas) ----------
    metricas_ipca = _metricas(df_ipca, ['Taxa Indicativa', 'Taxa Indicativa (%)', 'Spread IPCA', 'Spread IPCA (%)'])
    metricas_cdi  = _metricas(df_cdi_spread, ['Taxa Indicativa', 'Taxa Indicativa (%)', 'Spread DI', 'Spread CDI'])
    metricas_perc = _metricas(df_cdi_perc, ['Taxa Indicativa', 'Taxa Indicativa (%CDI)', '%CDI', '% CDI'])

    # ---------- Montagem do resultado ----------
    dados = [
        {
            'Indexador': 'IPCA+',
            'Distribuição (%)': _safe_round((total_titulos_ipca / total_geral) * 100, 2),
            'Quantidade Títulos': total_titulos_ipca,
            'PU/Par Médio (%)': _safe_round(metricas_ipca['pu_par_medio'], 2),
            'Duration Média (dias)': _safe_round(metricas_ipca['duration_media'], 0),
            'Taxa Indicativa Média (%)': _safe_round(metricas_ipca['taxa_media'], 2),
            'Maior Taxa (%)': _safe_round(metricas_ipca['taxa_maxima'], 2)
        },
        {
            'Indexador': 'CDI+',
            'Distribuição (%)': _safe_round((total_titulos_cdi / total_geral) * 100, 2),
            'Quantidade Títulos': total_titulos_cdi,
            'PU/Par Médio (%)': _safe_round(metricas_cdi['pu_par_medio'], 2),
            'Duration Média (dias)': _safe_round(metricas_cdi['duration_media'], 0),
            'Taxa Indicativa Média (%)': _safe_round(metricas_cdi['taxa_media'], 2),
            'Maior Taxa (%)': _safe_round(metricas_cdi['taxa_maxima'], 2)
        },
        {
            'Indexador': '%CDI',
            'Distribuição (%)': _safe_round((total_titulos_perc / total_geral) * 100, 2),
            'Quantidade Títulos': total_titulos_perc,
            'PU/Par Médio (%)': _safe_round(metricas_perc['pu_par_medio'], 2),
            'Duration Média (dias)': _safe_round(metricas_perc['duration_media'], 0),
            'Taxa Indicativa Média (%)': _safe_round(metricas_perc['taxa_media'], 2),
            'Maior Taxa (%)': _safe_round(metricas_perc['taxa_maxima'], 2)
        }
    ]

    df_resultado = pd.DataFrame(dados)

    total_row = {
        'Indexador': 'TOTAL',
        'Distribuição (%)': 100.00,
        'Quantidade Títulos': total_geral,
        'PU/Par Médio (%)': np.nan,
        'Duration Média (dias)': np.nan,
        'Taxa Indicativa Média (%)': np.nan,
        'Maior Taxa (%)': np.nan
    }
    df_resultado = pd.concat([df_resultado, pd.DataFrame([total_row])], ignore_index=True)

    return df_resultado


# ---------------------------------------------------------------------
# Add-ons: TOP 10 spreads + stats
# ---------------------------------------------------------------------

def _normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    df.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in df.columns]
    return df


def _dedup_coalesce_cols(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    name_to_idx = defaultdict(list)
    for i, col in enumerate(df.columns):
        name_to_idx[col].append(i)
    cols_out = {}
    for name, idxs in name_to_idx.items():
        if len(idxs) == 1:
            cols_out[name] = df.iloc[:, idxs[0]]
        else:
            bloco = df.iloc[:, idxs]
            cols_out[name] = bloco.bfill(axis=1).iloc[:, 0]
    return pd.DataFrame(cols_out, index=df.index)


def _coalesce_series(df: pd.DataFrame, candidates) -> pd.Series:
    if df is None or df.empty:
        return pd.Series(dtype=float)
    if isinstance(candidates, str):
        candidates = [candidates]
    for name in candidates:
        exact = [c for c in df.columns if c.lower() == str(name).lower()]
        if exact:
            return pd.to_numeric(df[exact[0]], errors="coerce")
        pat = re.compile(rf"^{re.escape(str(name))}$", re.IGNORECASE)
        cols = [c for c in df.columns if pat.match(str(c))]
        if cols:
            return pd.to_numeric(df[cols[0]], errors="coerce")
    return pd.Series([np.nan] * len(df), index=df.index, dtype=float)


def _pick_ident_col(df: pd.DataFrame) -> Optional[str]:
    """
    Coluna identificadora preferencial para ranking:
      - Código
      - Emissor
      - (fallback) primeira coluna
    """
    if df is None or df.empty:
        return None
    for c in ["Código", "Codigo", "Emissor", "Nome", "Ativo", "Título", "Titulo"]:
        if c in df.columns:
            return c
    return df.columns[0] if len(df.columns) else None


def _top10_spreads(df: pd.DataFrame, spread_candidates, label: str) -> list:
    """
    Retorna lista de 10 maiores spreads com campos estáveis.
    Inclui: tipo, id, spread, duration
    """
    if df is None or df.empty:
        return []

    df2 = _dedup_coalesce_cols(_normalize_cols(df))

    s_spread = _coalesce_series(df2, spread_candidates)
    s_duration = _coalesce_series(df2, ['Duration', 'Duration (dias)'])
    ident_col = _pick_ident_col(df2)

    out = df2.copy()
    out["_spread"] = s_spread
    out["_duration"] = s_duration

    if ident_col:
        out["_id"] = out[ident_col].astype(str)
    else:
        out["_id"] = out.index.astype(str)

    out = out.dropna(subset=["_spread"])
    out = out.sort_values("_spread", ascending=False).head(10)

    rows = []
    for _, r in out.iterrows():
        rows.append({
            "tipo": label,
            "id": str(r.get("_id", "")),
            "spread": float(r["_spread"]),
            "duration": float(r["_duration"]) if pd.notna(r.get("_duration")) else None,
        })
    return rows


def _basic_stats(df: pd.DataFrame, taxa_candidates) -> dict:
    """
    Estatísticas simples e robustas para uma série de taxa/spread.
    """
    if df is None or df.empty:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "p90": None,
        }

    df2 = _dedup_coalesce_cols(_normalize_cols(df))
    s = _coalesce_series(df2, taxa_candidates).dropna()
    if len(s) == 0:
        return {
            "count": int(len(df2)),
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "p90": None,
        }

    return {
        "count": int(len(df2)),
        "mean": float(s.mean()),
        "median": float(s.median()),
        "min": float(s.min()),
        "max": float(s.max()),
        "p90": float(s.quantile(0.90)),
    }


# ---------------------------------------------------------------------
# Main: montar DFs a partir dos JSONs e salvar payload final
# ---------------------------------------------------------------------

def montar_dfs(deb_json_path: str, cri_cra_json_path: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Constrói os 6 DataFrames a partir dos JSONs (tabelas).
    Espera que cada JSON tenha payload com "tabelas".
    """
    deb_payload = _read_json(deb_json_path)
    cri_payload = _read_json(cri_cra_json_path)

    deb_tabs = _extract_tables_payload(deb_payload or {})
    cri_tabs = _extract_tables_payload(cri_payload or {})

    # Debêntures
    deb_ipca_spread = _rows_to_df(deb_tabs.get("ipca_spread"))
    deb_di_spread = _rows_to_df(deb_tabs.get("di_spread"))
    deb_di_percentual = _rows_to_df(deb_tabs.get("di_percentual"))

    # CRI/CRA
    cri_ipca_spread = _rows_to_df(cri_tabs.get("ipca_spread"))
    cri_di_spread = _rows_to_df(cri_tabs.get("di_spread"))
    cri_di_percentual = _rows_to_df(cri_tabs.get("di_percentual"))

    return (
        deb_ipca_spread, deb_di_spread, deb_di_percentual,
        cri_ipca_spread, cri_di_spread, cri_di_percentual
    )


def build_payload(
    resumo_df: pd.DataFrame,
    top10_ipca: list,
    top10_di: list,
    stats: dict,
    fontes: dict,
) -> dict:
    return {
        "gerado_em": _safe_datetime_now_str(),
        "fontes": fontes,
        "resumo": resumo_df.to_dict(orient="records") if resumo_df is not None else [],
        "estatisticas": stats,
        "top10": {
            "ipca_spread": top10_ipca,
            "di_spread": top10_di,
        },
    }


def save_json(payload: dict, out_path: str) -> None:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Consolida portfolio renda fixa a partir de debentures/cri_cra ANBIMA.")
    p.add_argument("--deb", default="site/data/debentures_anbima.json", help="JSON de debêntures ANBIMA")
    p.add_argument("--cri", default="site/data/cri_cra_anbima.json", help="JSON de CRI/CRA ANBIMA")
    p.add_argument("--out", default="site/data/portfolio_renda_fixa.json", help="JSON final consolidado")
    p.add_argument("--quiet", action="store_true", help="Modo silencioso")
    return p


def main() -> int:
    args = build_parser().parse_args()
    verbose = not bool(args.quiet)

    # Monta DFs
    dfs = montar_dfs(args.deb, args.cri)
    (deb_ipca_spread, deb_di_spread, deb_di_percentual,
     cri_ipca_spread, cri_di_spread, cri_di_percentual) = dfs

    # Resumo (sua função)
    resumo_df = analisar_portfolios(
        deb_ipca_spread, deb_di_spread, deb_di_percentual,
        cri_ipca_spread, cri_di_spread, cri_di_percentual
    )

    # Top 10 spreads (maiores)
    top10_ipca = _top10_spreads(
        df=_dedup_coalesce_cols(pd.concat([deb_ipca_spread, cri_ipca_spread], ignore_index=True, sort=False)),
        spread_candidates=["Spread IPCA", "Spread IPCA (%)", "Taxa Indicativa", "Taxa Indicativa (%)"],
        label="IPCA+"
    )

    top10_di = _top10_spreads(
        df=_dedup_coalesce_cols(pd.concat([deb_di_spread, cri_di_spread], ignore_index=True, sort=False)),
        spread_candidates=["Spread DI", "Spread CDI", "Taxa Indicativa", "Taxa Indicativa (%)"],
        label="DI+"
    )

    # Estatísticas (simples e úteis)
    stats = {
        "ipca_spread": _basic_stats(
            df=_dedup_coalesce_cols(pd.concat([deb_ipca_spread, cri_ipca_spread], ignore_index=True, sort=False)),
            taxa_candidates=["Spread IPCA", "Spread IPCA (%)", "Taxa Indicativa", "Taxa Indicativa (%)"],
        ),
        "di_spread": _basic_stats(
            df=_dedup_coalesce_cols(pd.concat([deb_di_spread, cri_di_spread], ignore_index=True, sort=False)),
            taxa_candidates=["Spread DI", "Spread CDI", "Taxa Indicativa", "Taxa Indicativa (%)"],
        ),
        "di_percentual": _basic_stats(
            df=_dedup_coalesce_cols(pd.concat([deb_di_percentual, cri_di_percentual], ignore_index=True, sort=False)),
            taxa_candidates=["Taxa Indicativa", "Taxa Indicativa (%CDI)", "%CDI", "% CDI"],
        ),
    }

    # Fontes (datas se existirem nos payloads)
    deb_payload = _read_json(args.deb) or {}
    cri_payload = _read_json(args.cri) or {}

    fontes = {
        "debentures_anbima": {
            "arquivo": args.deb,
            "data_referencia": deb_payload.get("data_referencia") or deb_payload.get("data") or None,
        },
        "cri_cra_anbima": {
            "arquivo": args.cri,
            "data_referencia": cri_payload.get("data_referencia") or cri_payload.get("data") or None,
        },
    }

    payload = build_payload(
        resumo_df=resumo_df,
        top10_ipca=top10_ipca,
        top10_di=top10_di,
        stats=stats,
        fontes=fontes,
    )

    save_json(payload, args.out)

    if verbose:
        print("✅ Portfolio consolidado gerado!")
        print(f"💾 Saída: {args.out}")
        print(f"   IPCA+ top10: {len(top10_ipca)} | DI+ top10: {len(top10_di)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
