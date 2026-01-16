#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================
SCRAPER DE CURVAS DE CRÉDITO ANBIMA - VERSÃO REAL (GitHub-ready)
===============================================================
Captura dados reais do site público da ANBIMA via formulário
Site: https://www.anbima.com.br/pt_br/informar/sistema-curvas-de-credito.htm

- Faz POST em:
  https://www.anbima.com.br/informacoes/curvas-debentures/CD-down.asp

- Tenta encontrar a data com dados (padrão: ontem, voltando até 10 dias)
- Processa e padroniza colunas:
  Vértice (anos), Spread AAA (%), Spread AA (%), Spread A (%)
- Calcula Vértice (dias úteis) = anos * 252
- Gera JSON único e estável em site/data/anbima_credito.json

Execução:
  python src/capturar_curvas_credito_anbima.py
  python src/capturar_curvas_credito_anbima.py --output site/data/anbima_credito.json --days-back 10
  python src/capturar_curvas_credito_anbima.py --quiet
"""

from __future__ import annotations

import argparse
import json
import warnings
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import requests

warnings.filterwarnings("ignore")


# -----------------------------
# Util
# -----------------------------

def _to_num_br(x):
    """
    Converte strings em formato BR ('1.234,56') ou variantes para float.
    Retorna NaN quando não for parseável.
    """
    import numpy as np

    if x is None:
        return np.nan
    if isinstance(x, (int, float)):
        return float(x)

    s = str(x).strip()
    if s == "" or s.lower() in {"nan", "none", "-"}:
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


# -----------------------------
# Core scraping
# -----------------------------

def buscar_curvas_credito_anbima(
    data: Optional[str] = None,
    tentar_dias_anteriores: bool = True,
    days_back: int = 10,
    quiet: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Busca curvas de crédito ANBIMA via POST para o formulário de download.

    Parâmetros:
    -----------
    data : str, opcional
        Data no formato 'DD/MM/YYYY'. Se None, usa dia anterior.
    tentar_dias_anteriores : bool
        Se True, tenta voltar dias até encontrar dados.
    days_back : int
        Máximo de dias para tentar (se tentar_dias_anteriores=True).
    quiet : bool
        Se True, reduz prints.

    Retorna:
    --------
    dict com:
      - data_referencia
      - dados_completos (DataFrame)
      - aaa / aa / a (DataFrame por rating) ou None
    """
    BASE_URL = "https://www.anbima.com.br/informacoes/curvas-debentures/CD-down.asp"

    if data is None:
        data_obj = datetime.now() - timedelta(days=1)
    else:
        data_obj = datetime.strptime(data, "%d/%m/%Y")

    max_tentativas = max(1, days_back) if tentar_dias_anteriores else 1
    df_result = None
    data_str_br = None

    if not quiet:
        print("🔍 Capturando dados reais da ANBIMA...\n")

    for tentativa in range(max_tentativas):
        data_str_br = data_obj.strftime("%d/%m/%Y")
        dia_semana = data_obj.strftime("%A")

        if not quiet:
            print(f"🔍 Tentativa {tentativa + 1}/{max_tentativas}: {data_str_br} ({dia_semana})...")

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://www.anbima.com.br",
                "Referer": "https://www.anbima.com.br/pt_br/informar/sistema-curvas-de-credito.htm",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            form_data = {
                "Idioma": "PT",
                "Dt_Ref": data_str_br,  # DD/MM/YYYY
                "saida": "csv",
            }

            if not quiet:
                print(f"   POST: {BASE_URL}")
                print(f"   Data: {form_data}")

            response = requests.post(
                BASE_URL,
                data=form_data,
                headers=headers,
                timeout=30,
                allow_redirects=True,
            )

            if not quiet:
                print(f"   Status: {response.status_code} | Tamanho: {len(response.text)} bytes")

            if response.status_code != 200:
                data_obj = data_obj - timedelta(days=1)
                continue

            content = response.text
            if len(content) < 50:
                if not quiet:
                    print(f"   ⚠️ Resposta vazia ({len(content)} bytes)")
                data_obj = data_obj - timedelta(days=1)
                continue

            # Se vier HTML, normalmente é erro / sem dados
            low = content.lower()
            if "<html" in low or "<!doctype" in low:
                if not quiet:
                    print("   ⚠️ Resposta HTML (provável sem dados)")
                data_obj = data_obj - timedelta(days=1)
                continue

            # Parse principal (padrão ANBIMA: ; e primeira linha é título)
            parsed_ok = False
            try:
                df = pd.read_csv(
                    StringIO(content),
                    sep=";",
                    encoding="latin1",
                    decimal=",",
                    thousands=".",
                    skiprows=1,
                )
                if df is not None and len(df) > 0:
                    df_result = df
                    parsed_ok = True
            except Exception:
                parsed_ok = False

            # Fallbacks robustos de parse (mantém sua lógica)
            if not parsed_ok:
                for skiprows in [0, 2]:
                    for sep in [";", ",", "\t", "|"]:
                        try:
                            df = pd.read_csv(
                                StringIO(content),
                                sep=sep,
                                encoding="latin1",
                                decimal=",",
                                thousands=".",
                                skiprows=skiprows,
                            )
                            if len(df) > 0 and len(df.columns) >= 3:
                                df_result = df
                                parsed_ok = True
                                break
                        except Exception:
                            continue
                    if parsed_ok:
                        break

            if parsed_ok and df_result is not None and len(df_result) > 0:
                if not quiet:
                    print(f"✅ Dados capturados com sucesso para {data_str_br}!")
                    print(f"   Total de registros: {len(df_result)}")
                    print(f"   Colunas: {list(df_result.columns)}")
                break

        except Exception as e:
            if not quiet:
                print(f"   ⚠️ Erro na requisição: {str(e)[:140]}")

        data_obj = data_obj - timedelta(days=1)

    if df_result is None:
        if not quiet:
            print(f"\n❌ Não foi possível capturar dados nos últimos {max_tentativas} dias")
            print("💡 Possíveis causas:")
            print("   - Site em manutenção")
            print("   - Dados indisponíveis para a janela consultada")
            print("   - Mudança no endpoint / necessidade de acesso")
        return None

    return processar_curvas(df_result, data_str_br, quiet=quiet)


def processar_curvas(df: pd.DataFrame, data_str_br: str, quiet: bool = False) -> Optional[Dict[str, Any]]:
    """Processa o DataFrame de curvas de crédito (mantém a lógica e cálculos)."""

    if not quiet:
        print("\n📊 Processando curvas de crédito...")

    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    if not quiet:
        print(f"   Colunas encontradas: {list(df.columns)}")

    col_vertice = None
    col_aaa = None
    col_aa = None
    col_a = None

    for col in df.columns:
        col_clean = (
            col.lower()
            .replace(" ", "")
            .replace("_", "")
            .replace("í", "i")
            .replace("é", "e")
        )

        if any(x in col_clean for x in ["vertice", "vertices", "prazo", "anos", "year", "maturity"]):
            col_vertice = col
        elif "aaa" in col_clean:
            col_aaa = col
        elif col_clean == "aa" or (col_clean.startswith("aa") and "aaa" not in col_clean):
            col_aa = col
        elif col_clean == "a":
            col_a = col

    # Fallback por posição (mantém sua lógica)
    if not col_vertice and len(df.columns) >= 4:
        col_vertice = df.columns[0]
    if not col_aaa and len(df.columns) >= 4:
        col_aaa = df.columns[1]
    if not col_aa and len(df.columns) >= 4:
        col_aa = df.columns[2]
    if not col_a and len(df.columns) >= 4:
        col_a = df.columns[3]

    if not quiet:
        print("   Mapeamento:")
        print(f"   - Vértice: {col_vertice}")
        print(f"   - AAA: {col_aaa}")
        print(f"   - AA: {col_aa}")
        print(f"   - A: {col_a}")

    rename_map = {}
    if col_vertice:
        rename_map[col_vertice] = "Vértice (anos)"
    if col_aaa:
        rename_map[col_aaa] = "Spread AAA (%)"
    if col_aa:
        rename_map[col_aa] = "Spread AA (%)"
    if col_a:
        rename_map[col_a] = "Spread A (%)"

    df = df.rename(columns=rename_map)

    if "Vértice (anos)" in df.columns:
        df["Vértice (anos)"] = df["Vértice (anos)"].apply(_to_num_br)
    else:
        if not quiet:
            print("   ⚠️ Coluna 'Vértice (anos)' não encontrada após mapeamento")
            print(f"   Colunas disponíveis: {list(df.columns)}")
        return None

    for col in ["Spread AAA (%)", "Spread AA (%)", "Spread A (%)"]:
        if col in df.columns:
            df[col] = df[col].apply(_to_num_br)

    df = df.dropna(subset=["Vértice (anos)"])
    df["Vértice (dias úteis)"] = (df["Vértice (anos)"] * 252).round(0).astype(int)
    df = df.sort_values("Vértice (anos)").reset_index(drop=True)

    curvas: Dict[str, Any] = {
        "data_referencia": data_str_br,
        "dados_completos": df,
    }

    for rating, col_spread, chave in [
        ("AAA", "Spread AAA (%)", "aaa"),
        ("AA", "Spread AA (%)", "aa"),
        ("A", "Spread A (%)", "a"),
    ]:
        if col_spread in df.columns:
            df_rating = df[["Vértice (dias úteis)", "Vértice (anos)", col_spread]].dropna()
            df_rating = df_rating.rename(columns={col_spread: "Spread (%)"})
            df_rating["Rating"] = rating
            curvas[chave] = df_rating
        else:
            curvas[chave] = None

    if not quiet:
        print("✅ Processamento concluído!\n")
        disponivel = []
        for rating, chave in [("AAA", "aaa"), ("AA", "aa"), ("A", "a")]:
            if curvas.get(chave) is not None and not curvas[chave].empty:
                disponivel.append(f"{rating} ({len(curvas[chave])} vértices)")
        print(f"   Curvas disponíveis: {', '.join(disponivel) if disponivel else 'nenhuma'}")

    return curvas


# -----------------------------
# JSON output (estável p/ site)
# -----------------------------

def curvas_to_payload(curvas: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte o retorno em payload JSON estável (sem CSV timestamp).
    Mantém dados completos e curvas por rating.
    """
    df_full: pd.DataFrame = curvas["dados_completos"]

    def df_to_rows(df: pd.DataFrame) -> list:
        rows = []
        for _, r in df.iterrows():
            item = {}
            for c in df.columns:
                v = r[c]
                if pd.isna(v):
                    item[c] = None
                elif isinstance(v, (int, float)):
                    item[c] = float(v)
                else:
                    # strings/objetos
                    item[c] = str(v)
            rows.append(item)
        return rows

    payload: Dict[str, Any] = {
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_referencia": curvas.get("data_referencia"),
        "dados_completos": df_to_rows(df_full),
        "curvas": {},
    }

    for chave in ["aaa", "aa", "a"]:
        dfk = curvas.get(chave)
        if dfk is None or dfk.empty:
            payload["curvas"][chave] = None
        else:
            payload["curvas"][chave] = df_to_rows(dfk)

    return payload


def salvar_json(payload: Dict[str, Any], output_path: str) -> None:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# -----------------------------
# CLI
# -----------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Captura curvas de crédito ANBIMA e salva JSON em site/data.")
    p.add_argument("--output", default="site/data/anbima_credito.json", help="Caminho do JSON de saída")
    p.add_argument("--days-back", type=int, default=10, help="Quantos dias tentar para trás")
    p.add_argument("--data", default="", help="Data fixa DD/MM/YYYY (opcional)")
    p.add_argument("--quiet", action="store_true", help="Modo silencioso")
    return p


def main() -> int:
    args = build_parser().parse_args()
    data = args.data.strip() or None

    curvas = buscar_curvas_credito_anbima(
        data=data,
        tentar_dias_anteriores=True,
        days_back=args.days_back,
        quiet=bool(args.quiet),
    )

    if curvas is None:
        print("❌ Falha ao capturar curvas ANBIMA.")
        return 1

    payload = curvas_to_payload(curvas)
    salvar_json(payload, args.output)

    if not args.quiet:
        print(f"💾 JSON salvo em: {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
