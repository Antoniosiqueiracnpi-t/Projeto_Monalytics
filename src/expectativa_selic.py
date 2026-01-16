#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================
EXPECTATIVA SELIC (BCB OLINDA / ODATA) - MONALYTICS
===============================================================
Fonte:
  https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoSelic

O que faz:
- Baixa um conjunto recente (top N) ordenado por Data desc
- Identifica a data mais recente disponível
- Identifica uma data ~1 semana antes (maior Data <= (Data_recente - 7 dias))
- Monta payload com:
    - snapshot_atual (por Reuniao)
    - snapshot_semana_anterior (por Reuniao)
    - comparacao (merge por Reuniao) com deltas
- Salva JSON em site/data/expectativa_selic.json
===============================================================
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests


BCB_OADATA_URL = (
    "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoSelic"
)

# Campos mais úteis (mantém também "Indicador" por segurança)
DEFAULT_SELECT = [
    "Indicador",
    "Data",
    "Reuniao",
    "Media",
    "Mediana",
    "DesvioPadrao",
    "Minimo",
    "Maximo",
    "numeroRespondentes",
    "baseCalculo",
]


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _now_brt_iso() -> str:
    # America/Sao_Paulo (UTC-3). Sem pytz para manter dependências mínimas.
    # Em janeiro não há DST, então UTC-3 é ok.
    brt = timezone(timedelta(hours=-3))
    return datetime.now(brt).isoformat(timespec="seconds")


def _to_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        if pd.isna(x):
            return None
    except Exception:
        pass
    try:
        return float(x)
    except Exception:
        return None


def _to_int(x: Any) -> Optional[int]:
    if x is None:
        return None
    try:
        if pd.isna(x):
            return None
    except Exception:
        pass
    try:
        return int(float(x))
    except Exception:
        return None


def _safe_json(obj: Any) -> Any:
    """Converte tipos pandas/numpy para JSON."""
    if obj is None:
        return None

    # pandas Timestamp
    if isinstance(obj, pd.Timestamp):
        if pd.isna(obj):
            return None
        # manter timezone se existir; caso não, ISO padrão
        return obj.isoformat()

    # numpy scalar
    try:
        import numpy as np  # lazy

        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
    except Exception:
        pass

    # datetime
    if isinstance(obj, datetime):
        return obj.isoformat()

    return obj


@dataclass
class Config:
    saida: str
    top: int
    timeout: int
    base_calculo: int
    verbose: bool


def fetch_odata_top(url: str, select_fields: List[str], top: int, timeout: int, verbose: bool) -> List[Dict[str, Any]]:
    """
    Baixa TOP N itens do endpoint OData, ordenados por Data desc.
    """
    params = {
        "$format": "json",
        "$orderby": "Data desc",
        "$top": str(int(top)),
        "$select": ",".join(select_fields),
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Monalytics; +https://github.com)",
        "Accept": "application/json,text/plain,*/*",
    }

    if verbose:
        print("🔍 Consultando BCB Olinda (OData)...")
        print(f"   URL: {url}")
        print(f"   Params: {params}")

    r = requests.get(url, params=params, headers=headers, timeout=timeout)
    r.raise_for_status()

    data = r.json()
    if not isinstance(data, dict) or "value" not in data:
        raise ValueError("Resposta inesperada do OData: campo 'value' não encontrado")

    value = data.get("value", [])
    if not isinstance(value, list):
        raise ValueError("Resposta inesperada do OData: 'value' não é lista")

    if verbose:
        print(f"✅ Registros recebidos: {len(value)}")

    return value


def to_dataframe(rows: List[Dict[str, Any]], base_calculo: int, verbose: bool) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows).copy()

    # Normaliza colunas
    for c in DEFAULT_SELECT:
        if c not in df.columns:
            df[c] = None

    # Converte Data
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", utc=True)

    # Tipos numéricos
    for col in ["Media", "Mediana", "DesvioPadrao", "Minimo", "Maximo"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["Reuniao", "numeroRespondentes", "baseCalculo"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # Filtra baseCalculo
    df = df[df["baseCalculo"].astype("Int64") == int(base_calculo)]

    # Remove linhas sem Data
    df = df.dropna(subset=["Data"]).reset_index(drop=True)

    if verbose:
        if df.empty:
            print(f"⚠️  DataFrame vazio após filtrar baseCalculo={base_calculo}")
        else:
            dmax = df["Data"].max()
            dmin = df["Data"].min()
            print(f"📅 Janela capturada: {dmin.date()} .. {dmax.date()} (UTC) | baseCalculo={base_calculo}")

    return df


def pick_dates(df: pd.DataFrame, verbose: bool) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """
    Retorna (data_mais_recente, data_semana_anterior_aproximada)
    onde a segunda é a maior Data <= (data_recente - 7 dias).
    """
    if df.empty:
        raise ValueError("DataFrame vazio - não há datas para selecionar")

    latest = df["Data"].max()
    target = latest - pd.Timedelta(days=7)

    candidates = df.loc[df["Data"] <= target, "Data"]
    if candidates.empty:
        # fallback: pega a segunda data distinta (se existir)
        distinct = sorted(df["Data"].dropna().dt.normalize().unique())
        if len(distinct) >= 2:
            prev = pd.Timestamp(distinct[-2]).tz_localize("UTC")
        else:
            prev = latest
    else:
        prev = candidates.max()

    # Normaliza para o timestamp existente no dataset (mantém horário)
    return latest, prev


def snapshot_for_date(df: pd.DataFrame, date_ts: pd.Timestamp) -> pd.DataFrame:
    """
    Filtra linhas para a mesma 'Data' (mesmo timestamp).
    Observação: no dataset do BCB, Data costuma vir como 00:00:00Z.
    """
    return df[df["Data"] == date_ts].copy().reset_index(drop=True)


def df_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    if df is None or df.empty:
        return []
    out: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        out.append({k: _safe_json(v) for k, v in row.to_dict().items()})
    return out


def build_comparison(df_now: pd.DataFrame, df_prev: pd.DataFrame) -> pd.DataFrame:
    """
    Merge por (Indicador, Reuniao, baseCalculo) e calcula deltas.
    """
    key_cols = ["Indicador", "Reuniao", "baseCalculo"]

    cols_metrics = ["Media", "Mediana", "DesvioPadrao", "Minimo", "Maximo", "numeroRespondentes"]
    keep_now = key_cols + ["Data"] + cols_metrics
    keep_prev = key_cols + ["Data"] + cols_metrics

    a = df_now[keep_now].copy()
    b = df_prev[keep_prev].copy()

    merged = a.merge(
        b,
        on=key_cols,
        how="outer",
        suffixes=("_atual", "_semana"),
        indicator=True,
    )

    # deltas (atual - semana)
    for m in ["Media", "Mediana", "DesvioPadrao", "Minimo", "Maximo"]:
        merged[f"Delta_{m}"] = pd.to_numeric(merged[f"{m}_atual"], errors="coerce") - pd.to_numeric(
            merged[f"{m}_semana"], errors="coerce"
        )

    merged["Delta_numeroRespondentes"] = (
        pd.to_numeric(merged["numeroRespondentes_atual"], errors="coerce")
        - pd.to_numeric(merged["numeroRespondentes_semana"], errors="coerce")
    )

    # ordena por Reuniao
    merged = merged.sort_values(["Reuniao"], na_position="last").reset_index(drop=True)
    return merged


def build_payload(
    base_calculo: int,
    latest_ts: pd.Timestamp,
    prev_ts: pd.Timestamp,
    df_now: pd.DataFrame,
    df_prev: pd.DataFrame,
    df_comp: pd.DataFrame,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "fonte": "BCB Olinda - ExpectativasMercadoSelic (OData)",
        "endpoint": BCB_OADATA_URL,
        "gerado_em": _now_brt_iso(),
        "baseCalculo": int(base_calculo),
        "data_atual_utc": _safe_json(latest_ts),
        "data_semana_anterior_utc": _safe_json(prev_ts),
        "resumo": {
            "qtde_registros_atual": int(len(df_now)),
            "qtde_registros_semana_anterior": int(len(df_prev)),
            "qtde_reunioes_distintas_atual": int(df_now["Reuniao"].nunique(dropna=True)) if not df_now.empty else 0,
            "qtde_reunioes_distintas_semana_anterior": int(df_prev["Reuniao"].nunique(dropna=True)) if not df_prev.empty else 0,
        },
        "snapshot_atual": df_to_records(df_now),
        "snapshot_semana_anterior": df_to_records(df_prev),
        "comparacao": df_to_records(df_comp),
    }
    return payload


def run(cfg: Config) -> int:
    rows = fetch_odata_top(
        url=BCB_OADATA_URL,
        select_fields=DEFAULT_SELECT,
        top=cfg.top,
        timeout=cfg.timeout,
        verbose=cfg.verbose,
    )

    df = to_dataframe(rows, base_calculo=cfg.base_calculo, verbose=cfg.verbose)
    if df.empty:
        print("❌ Sem dados após filtros. Abortando.")
        return 2

    latest_ts, prev_ts = pick_dates(df, verbose=cfg.verbose)

    df_now = snapshot_for_date(df, latest_ts)
    df_prev = snapshot_for_date(df, prev_ts)

    if cfg.verbose:
        print("\n" + "=" * 70)
        print("EXPECTATIVA SELIC - DATAS SELECIONADAS")
        print("=" * 70)
        print(f"📅 Atual (UTC):   {latest_ts.isoformat()}")
        print(f"📅 Semana (UTC):  {prev_ts.isoformat()}")
        print(f"📌 Registros atual: {len(df_now)} | semana: {len(df_prev)}")
        print("=" * 70 + "\n")

    df_comp = build_comparison(df_now, df_prev)

    payload = build_payload(
        base_calculo=cfg.base_calculo,
        latest_ts=latest_ts,
        prev_ts=prev_ts,
        df_now=df_now,
        df_prev=df_prev,
        df_comp=df_comp,
    )

    _ensure_parent_dir(cfg.saida)
    with open(cfg.saida, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=_safe_json)

    print(f"💾 Salvo: {cfg.saida}")
    return 0


def parse_args() -> Config:
    p = argparse.ArgumentParser(description="Captura Expectativa Selic (BCB Olinda) e salva JSON.")
    p.add_argument(
        "--saida",
        default="site/data/expectativa_selic.json",
        help="Caminho do JSON de saída (default: site/data/expectativa_selic.json)",
    )
    p.add_argument("--top", type=int, default=5000, help="Quantidade de linhas (top) para baixar do OData (default: 5000)")
    p.add_argument("--timeout", type=int, default=30, help="Timeout da requisição HTTP em segundos (default: 30)")
    p.add_argument(
        "--base-calculo",
        type=int,
        default=0,
        choices=[0, 1],
        help="baseCalculo (0 = amostra maior; 1 = amostra curta). Default: 0",
    )
    p.add_argument("--quiet", action="store_true", help="Silencia logs detalhados")
    args = p.parse_args()

    return Config(
        saida=args.saida,
        top=args.top,
        timeout=args.timeout,
        base_calculo=args.base_calculo,
        verbose=(not args.quiet),
    )


def main() -> int:
    cfg = parse_args()
    try:
        return run(cfg)
    except requests.HTTPError as e:
        print(f"❌ HTTPError: {e}")
        return 3
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
