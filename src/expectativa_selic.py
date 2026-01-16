#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================
EXPECTATIVA SELIC (BCB OLINDA / ODATA) - Projeto Monalytics
===============================================================

- Fonte: https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoSelic
- Captura a data mais recente disponível + data "uma semana antes" (ou a data útil mais próxima <= alvo)
- Gera JSON estruturado para o site: site/data/expectativa_selic.json

IMPORTANTE:
- NÃO usa $orderby=Data desc, pois esse endpoint retorna 400 com esse orderby.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests


BASE_URL = "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoSelic"


@dataclass
class RegistroComparado:
    reuniao: str
    base_calculo: int

    media_atual: Optional[float]
    mediana_atual: Optional[float]
    desvio_padrao_atual: Optional[float]
    minimo_atual: Optional[float]
    maximo_atual: Optional[float]
    numero_respondentes_atual: Optional[int]

    media_semana: Optional[float]
    mediana_semana: Optional[float]
    desvio_padrao_semana: Optional[float]
    minimo_semana: Optional[float]
    maximo_semana: Optional[float]
    numero_respondentes_semana: Optional[int]

    delta_media: Optional[float]
    delta_mediana: Optional[float]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_float(x) -> Optional[float]:
    try:
        if pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None


def _safe_int(x) -> Optional[int]:
    try:
        if pd.isna(x):
            return None
        return int(x)
    except Exception:
        return None


def _http_get_json(url: str, params: Dict[str, str], timeout: int = 30) -> Dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Monalytics; +https://github.com/)",
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
    }
    r = requests.get(url, params=params, headers=headers, timeout=timeout)
    # Se der 400, queremos a mensagem completa no log
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        msg = f"HTTPError {r.status_code} em {r.url} | body_prefix={r.text[:200]!r}"
        raise requests.HTTPError(msg) from e
    return r.json()


def carregar_dados_olinda(top: int = 5000, timeout: int = 30) -> pd.DataFrame:
    """
    Carrega os registros via OData em JSON.

    Observação:
    - Não usa $orderby (esse endpoint rejeita orderby=Data desc).
    """
    params = {
        "$format": "json",
        "$top": str(top),
        "$select": "Indicador,Data,Reuniao,Media,Mediana,DesvioPadrao,Minimo,Maximo,numeroRespondentes,baseCalculo",
    }

    data = _http_get_json(BASE_URL, params=params, timeout=timeout)
    rows = data.get("value", [])
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Tipos
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce", utc=False)  # vem YYYY-MM-DD
    for c in ["Media", "Mediana", "DesvioPadrao", "Minimo", "Maximo"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["numeroRespondentes", "baseCalculo"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")

    # Limpa linhas sem data/reunião
    df = df.dropna(subset=["Data", "Reuniao"]).reset_index(drop=True)
    return df


def escolher_datas(df: pd.DataFrame) -> Tuple[pd.Timestamp, pd.Timestamp, str]:
    """
    Retorna:
    - data_atual (máxima)
    - data_semana (data útil mais próxima <= data_atual - 7 dias)
    - observacao
    """
    data_atual = df["Data"].max()

    alvo = data_atual - timedelta(days=7)
    datas_disponiveis = sorted(df["Data"].dropna().unique())

    # pega a maior data <= alvo
    data_semana = None
    for d in reversed(datas_disponiveis):
        if d <= alvo:
            data_semana = d
            break

    if data_semana is None:
        # fallback: menor data disponível (evita quebrar)
        data_semana = min(datas_disponiveis)

    obs = (
        "Comparação usa a data disponível mais próxima <= (data_mais_recente - 7 dias). "
        f"Alvo: {alvo.date().isoformat()}."
    )
    return pd.Timestamp(data_atual), pd.Timestamp(data_semana), obs


def _agrupar_por_reuniao_base(df: pd.DataFrame) -> pd.DataFrame:
    """
    Em geral há 1 linha por (Data, Reuniao, baseCalculo), mas garantimos:
    - se houver duplicatas, pegamos o primeiro não-nulo por coluna.
    """
    cols_num = ["Media", "Mediana", "DesvioPadrao", "Minimo", "Maximo", "numeroRespondentes"]
    keep_cols = ["Reuniao", "baseCalculo"] + [c for c in cols_num if c in df.columns]

    dfx = df[keep_cols].copy()

    # coalesce por grupo
    def first_valid(s: pd.Series):
        s2 = s.dropna()
        return s2.iloc[0] if len(s2) else pd.NA

    agg = {c: first_valid for c in cols_num if c in dfx.columns}
    out = dfx.groupby(["Reuniao", "baseCalculo"], dropna=False, as_index=False).agg(agg)

    # ordenação amigável (Reuniao pode ser tipo "R1/2026", "R8/2027" etc.)
    out = out.sort_values(["Reuniao", "baseCalculo"], ascending=[True, True]).reset_index(drop=True)
    return out


def montar_payload(df: pd.DataFrame) -> Dict:
    if df is None or df.empty:
        return {
            "fonte": "BCB Olinda - ExpectativasMercadoSelic (OData)",
            "atualizacao_utc": _utc_now_iso(),
            "status": "vazio",
            "mensagem": "Nenhum dado retornado do endpoint.",
        }

    data_atual, data_semana, obs = escolher_datas(df)

    df_atual = df[df["Data"] == data_atual].copy()
    df_semana = df[df["Data"] == data_semana].copy()

    g_atual = _agrupar_por_reuniao_base(df_atual)
    g_semana = _agrupar_por_reuniao_base(df_semana)

    merged = pd.merge(
        g_atual,
        g_semana,
        on=["Reuniao", "baseCalculo"],
        how="outer",
        suffixes=("_atual", "_semana"),
    )

    registros: List[RegistroComparado] = []
    for _, r in merged.iterrows():
        media_atual = _safe_float(r.get("Media_atual"))
        media_semana = _safe_float(r.get("Media_semana"))
        mediana_atual = _safe_float(r.get("Mediana_atual"))
        mediana_semana = _safe_float(r.get("Mediana_semana"))

        registros.append(
            RegistroComparado(
                reuniao=str(r.get("Reuniao")),
                base_calculo=int(r.get("baseCalculo")) if pd.notna(r.get("baseCalculo")) else 0,
                media_atual=media_atual,
                mediana_atual=mediana_atual,
                desvio_padrao_atual=_safe_float(r.get("DesvioPadrao_atual")),
                minimo_atual=_safe_float(r.get("Minimo_atual")),
                maximo_atual=_safe_float(r.get("Maximo_atual")),
                numero_respondentes_atual=_safe_int(r.get("numeroRespondentes_atual")),
                media_semana=media_semana,
                mediana_semana=mediana_semana,
                desvio_padrao_semana=_safe_float(r.get("DesvioPadrao_semana")),
                minimo_semana=_safe_float(r.get("Minimo_semana")),
                maximo_semana=_safe_float(r.get("Maximo_semana")),
                numero_respondentes_semana=_safe_int(r.get("numeroRespondentes_semana")),
                delta_media=(media_atual - media_semana) if (media_atual is not None and media_semana is not None) else None,
                delta_mediana=(mediana_atual - mediana_semana)
                if (mediana_atual is not None and mediana_semana is not None)
                else None,
            )
        )

    payload = {
        "fonte": "BCB Olinda - ExpectativasMercadoSelic (OData)",
        "endpoint": BASE_URL,
        "atualizacao_utc": _utc_now_iso(),
        "data_mais_recente": data_atual.date().isoformat(),
        "data_semana_anterior": data_semana.date().isoformat(),
        "observacao": obs,
        "total_registros_data_atual": int(len(df_atual)),
        "total_registros_data_semana": int(len(df_semana)),
        "registros": [asdict(x) for x in registros],
    }
    return payload


def salvar_json(payload: Dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    tmp_path.replace(out_path)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Captura Expectativas Selic (BCB Olinda) e salva JSON.")
    parser.add_argument("--out-dir", default="site/data", help="Diretório de saída (default: site/data)")
    parser.add_argument("--out-name", default="expectativa_selic.json", help="Nome do arquivo JSON (default: expectativa_selic.json)")
    parser.add_argument("--top", type=int, default=5000, help="Quantidade máxima de registros (default: 5000)")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout HTTP em segundos (default: 30)")
    args = parser.parse_args(argv)

    out_path = Path(args.out_dir) / args.out_name

    print("Consultando BCB Olinda (OData)...")
    print(f"  URL: {BASE_URL}")
    print(f"  Params: $format=json, $top={args.top}, $select=campos (sem $orderby)")

    try:
        df = carregar_dados_olinda(top=args.top, timeout=args.timeout)
        if df.empty:
            print("⚠️  Resposta sem registros (value vazio).")
        else:
            print(f"✅ Registros carregados: {len(df)}")
            print(f"✅ Datas encontradas (amostra): {sorted(df['Data'].dt.date.unique())[-3:] if 'Data' in df.columns else 'N/A'}")

        payload = montar_payload(df)
        salvar_json(payload, out_path)

        print(f"💾 Salvo: {out_path.as_posix()}")
        print(f"📅 Mais recente: {payload.get('data_mais_recente')} | Semana anterior: {payload.get('data_semana_anterior')}")
        return 0

    except requests.HTTPError as e:
        print(f"❌ HTTPError: {e}")
        return 3
    except Exception as e:
        print(f"❌ Erro inesperado: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
