#!/usr/bin/env python3
"""
Captura balanços da B3/CVM com sistema de seleção de tickers.
Segue a ordem do arquivo mapeamento_final_b3_completo_utf8.csv

PATCH CIRÚRGICO:
- NÃO depende de captura_balancos_b3 nem de outro script
- Captura diretamente do OpenData CVM (ITR/DFP) e salva em balancos/<TICKER>/
- Mantém ordem do CSV e modos (quantidade/ticker/lista/faixa)
- Também permite teste rápido: python src/captura_simples.py PETR4 --anos 10
"""

import sys
import os
import argparse
import re
import zipfile
from io import BytesIO
from datetime import date
from pathlib import Path
from typing import List

import pandas as pd
import requests

# Repo root
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
BALANCOS_DIR = REPO_ROOT / "balancos"
CACHE_DIR = REPO_ROOT / ".cache" / "cvm"


def carregar_tickers_ordenados(csv_path: Path) -> List[str]:
    """
    Carrega os tickers na ordem exata em que aparecem no CSV de mapeamento.
    """
    possible_paths = [
        csv_path,  # Caminho passado como argumento
        REPO_ROOT / csv_path.name,  # Raiz do repo
        SRC_DIR / csv_path.name,  # src/
        Path.cwd() / csv_path.name,  # Diretório atual
        Path(os.environ.get("GITHUB_WORKSPACE", ".")) / csv_path.name,  # GitHub Actions workspace
        Path(os.environ.get("GITHUB_WORKSPACE", ".")) / "src" / csv_path.name,
    ]

    csv_file = None
    for path in possible_paths:
        if path.exists():
            csv_file = path
            break

    if csv_file is None:
        print(f"[AVISO] Arquivo de mapeamento não encontrado")
        print(f"        Procurado em:")
        for p in possible_paths:
            print(f"        - {p}")
        return []

    try:
        df = pd.read_csv(csv_file, sep=";", encoding="utf-8", dtype=str)
        if "ticker" not in df.columns:
            print("[AVISO] Coluna 'ticker' não encontrada no CSV de mapeamento")
            return []

        tickers = df["ticker"].dropna().astype(str).str.strip().str.upper()
        seen = set()
        ordered_tickers = []
        for t in tickers:
            if t not in seen and t:
                seen.add(t)
                ordered_tickers.append(t)

        print(f"[INFO] Usando arquivo: {csv_file}")
        return ordered_tickers
    except Exception as e:
        print(f"[ERRO] Falha ao ler CSV de mapeamento: {e}")
        return []


def filtrar_tickers(all_tickers: List[str], modo: str, quantidade: str, ticker: str,
                   lista: str, faixa: str) -> List[str]:
    """
    Filtra a lista de tickers baseado no modo de seleção.
    Mantém a ordem original dos tickers.
    """
    if modo == "quantidade":
        try:
            n = int(quantidade) if quantidade else 10
            return all_tickers[:n]
        except ValueError:
            print(f"[AVISO] Quantidade inválida '{quantidade}', usando 10")
            return all_tickers[:10]

    elif modo == "ticker":
        if not ticker:
            print("[AVISO] Ticker não especificado, processando todos")
            return all_tickers
        ticker_upper = ticker.strip().upper()
        return [t for t in all_tickers if t == ticker_upper]

    elif modo == "lista":
        if not lista:
            print("[AVISO] Lista vazia, processando todos")
            return all_tickers
        tickers_list = [t.strip().upper() for t in lista.split(",") if t.strip()]
        return [t for t in all_tickers if t in tickers_list]

    elif modo == "faixa":
        if not faixa or "-" not in faixa:
            print(f"[AVISO] Faixa inválida '{faixa}', usando 1-50")
            start, end = 1, 50
        else:
            try:
                parts = faixa.split("-")
                start = int(parts[0].strip())
                end = int(parts[1].strip())
            except (ValueError, IndexError):
                print(f"[AVISO] Faixa inválida '{faixa}', usando 1-50")
                start, end = 1, 50

        start_idx = max(0, start - 1)
        end_idx = end
        return all_tickers[start_idx:end_idx]

    else:
        return all_tickers


def main():
    parser = argparse.ArgumentParser(description="Captura balanços da B3/CVM com seleção de tickers")
    parser.add_argument("ticker_posicional", nargs="?", default="", help="(opcional) Captura somente este ticker")
    parser.add_argument("--modo", default="quantidade", choices=["quantidade", "ticker", "lista", "faixa"])
    parser.add_argument("--quantidade", default="10")
    parser.add_argument("--ticker", default="")
    parser.add_argument("--lista", default="")
    parser.add_argument("--faixa", default="1-50")
    parser.add_argument("--anos", default="12", help="Quantos anos voltar (default 12)")
    args = parser.parse_args()

    try:
        anos = int(args.anos)
        if anos < 1:
            anos = 12
    except Exception:
        anos = 12

    # Localiza o arquivo de mapeamento
    mapping_file = REPO_ROOT / "mapeamento_final_b3_completo_utf8.csv"

    # Carrega tickers na ordem do arquivo
    all_tickers = carregar_tickers_ordenados(mapping_file)
    if not all_tickers:
        print("[ERRO] Nenhum ticker encontrado no arquivo de mapeamento")
        sys.exit(1)

    # Lê o mapeamento completo (para CNPJ / codigo_cvm)
    # (procura em raiz e src, igual ao loader)
    map_candidates = [
        REPO_ROOT / "mapeamento_final_b3_completo_utf8.csv",
        SRC_DIR / "mapeamento_final_b3_completo_utf8.csv",
        Path.cwd() / "mapeamento_final_b3_completo_utf8.csv",
    ]
    map_path = None
    for p in map_candidates:
        if p.exists():
            map_path = p
            break
    if map_path is None:
        print("[ERRO] Não foi possível localizar o mapeamento para ler CNPJ/codigo_cvm.")
        sys.exit(1)

    df_map = pd.read_csv(map_path, sep=";", encoding="utf-8", dtype=str)
    df_map["ticker"] = df_map.get("ticker", "").astype(str).str.strip().str.upper()

    # Seleção final de tickers
    if args.ticker_posicional.strip():
        tickers_selecionados = [args.ticker_posicional.strip().upper()]
        args.modo = "ticker"
    else:
        tickers_selecionados = filtrar_tickers(
            all_tickers, args.modo, args.quantidade, args.ticker, args.lista, args.faixa
        )

    if not tickers_selecionados:
        print("[AVISO] Nenhum ticker selecionado com os critérios fornecidos")
        sys.exit(0)

    print(f"\n{'='*60}")
    print(f"Modo: {args.modo}")
    print(f"Tickers selecionados: {len(tickers_selecionados)}")
    print(f"{'='*60}\n")

    # garante diretórios
    BALANCOS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # cache do cadastro CVM (resolve CD_CVM por CNPJ se necessario)
    cad_path = CACHE_DIR / "cad_cia_aberta.csv"
    cad_url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"

    def _norm_cnpj(cnpj: str) -> str:
        return re.sub(r"\D+", "", str(cnpj or "")).zfill(14)

    def _quarter_from_month(m: int) -> str:
        if m == 3:
            return "T1"
        if m == 6:
            return "T2"
        if m == 9:
            return "T3"
        return "T4"

    def _scale_to_mil_factor(scale: str) -> float:
        s = str(scale or "").strip().upper()
        if "UNIDADE" in s:
            return 1.0 / 1000.0
        if "MILH" in s:
            return 1000.0
        if "MIL" in s:
            return 1.0
        return 1.0

    def _to_float(v: str) -> float:
        s = str(v or "").strip().replace(".", "").replace(",", ".")
        try:
            return float(s)
        except Exception:
            return float("nan")

    # baixa cadastro uma vez (se precisar)
    cad_df = None

    sucesso = 0
    falhas = 0
    current_year = date.today().year
    years = list(range(current_year - (anos - 1), current_year + 1))

    for idx, ticker in enumerate(tickers_selecionados, 1):
        ticker = ticker.strip().upper()
        print(f"\n[{idx}/{len(tickers_selecionados)}] Processando {ticker}...")

        try:
            hit = df_map[df_map["ticker"] == ticker]
            if hit.empty:
                print(f"[ERRO] {ticker} não encontrado no mapeamento.")
                falhas += 1
                continue

            cnpj = hit.iloc[0].get("cnpj")
            codigo_cvm = hit.iloc[0].get("codigo_cvm")

            cnpj_norm = _norm_cnpj(cnpj) if cnpj is not None else ""
            cd_cvm = str(codigo_cvm).strip() if codigo_cvm is not None else ""
            if cd_cvm.lower() in ("", "nan", "none"):
                cd_cvm = ""

            # resolve CD_CVM via cadastro se não vier no mapeamento
            if not cd_cvm:
                if cad_df is None:
                    if not cad_path.exists() or cad_path.stat().st_size == 0:
                        r = requests.get(cad_url, timeout=120)
                        r.raise_for_status()
                        cad_path.write_bytes(r.content)
                    cad_df = pd.read_csv(cad_path, sep=";", encoding="latin1", dtype=str)
                    if "CNPJ_CIA" in cad_df.columns:
                        cad_df["CNPJ_CIA"] = cad_df["CNPJ_CIA"].astype(str).apply(_norm_cnpj)

                if cad_df is None or "CD_CVM" not in cad_df.columns or "CNPJ_CIA" not in cad_df.columns:
                    print(f"[ERRO] Não foi possível carregar cadastro CVM para resolver CD_CVM de {ticker}.")
                    falhas += 1
                    continue

                hit_cad = cad_df[cad_df["CNPJ_CIA"] == cnpj_norm]
                if hit_cad.empty:
                    print(f"[ERRO] Não foi possível resolver CD_CVM para {ticker} (CNPJ {cnpj_norm}).")
                    falhas += 1
                    continue

                cd_cvm = str(hit_cad.iloc[0]["CD_CVM"]).strip()

            out_dir = BALANCOS_DIR / ticker
            out_dir.mkdir(parents=True, exist_ok=True)

            # função local: ler do zip (con e ind)
            def _read_demo_from_zip(zip_bytes: bytes, doc_low: str, demo: str, year: int) -> pd.DataFrame:
                # tenta con, depois ind
                inner_con = f"{doc_low}_cia_aberta_{demo}_con_{year}.csv"
                inner_ind = f"{doc_low}_cia_aberta_{demo}_ind_{year}.csv"

                with zipfile.ZipFile(BytesIO(zip_bytes), "r") as z:
                    name = inner_con if inner_con in z.namelist() else (inner_ind if inner_ind in z.namelist() else None)
                    if name is None:
                        return pd.DataFrame()
                    raw = z.read(name)

                df = pd.read_csv(BytesIO(raw), sep=";", encoding="latin1", dtype=str)
                if "CD_CVM" not in df.columns:
                    return pd.DataFrame()

                df = df[df["CD_CVM"].astype(str).str.strip() == str(cd_cvm).strip()].copy()
                return df

            # converter para formato do projeto
            def _format_out(df_raw: pd.DataFrame, *, force_t4: bool) -> pd.DataFrame:
                if df_raw is None or df_raw.empty:
                    return pd.DataFrame(columns=["data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"])

                need = {"DT_REFER", "CD_CONTA", "DS_CONTA", "VL_CONTA"}
                if not need.issubset(set(df_raw.columns)):
                    return pd.DataFrame(columns=["data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"])

                dt = pd.to_datetime(df_raw["DT_REFER"], errors="coerce")
                tri = dt.dt.month.fillna(12).astype(int).apply(_quarter_from_month)
                if force_t4:
                    tri = "T4"

                fator = 1.0
                if "ESCALA_MOEDA" in df_raw.columns:
                    fator = df_raw["ESCALA_MOEDA"].astype(str).apply(_scale_to_mil_factor)
                else:
                    fator = 1.0

                valor_mil = df_raw["VL_CONTA"].astype(str).apply(_to_float) * fator

                out = pd.DataFrame(
                    {
                        "data_fim": dt.dt.strftime("%Y-%m-%d"),
                        "trimestre": tri,
                        "cd_conta": df_raw["CD_CONTA"].astype(str).str.strip(),
                        "ds_conta": df_raw["DS_CONTA"].astype(str),
                        "valor_mil": valor_mil,
                    }
                )
                out = out.dropna(subset=["data_fim", "trimestre", "cd_conta"])
                out = out[out["trimestre"].isin(["T1", "T2", "T3", "T4"])].copy()
                return out

            # acumula por demonstrativo
            acc = {
                "dre_tri": [],
                "bpa_tri": [],
                "bpp_tri": [],
                "dfc_tri": [],
                "dre_anu": [],
                "bpa_anu": [],
                "bpp_anu": [],
                "dfc_anu": [],
            }

            # ITR (trimestral)
            for y in years:
                url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_{y}.zip"
                r = requests.get(url, timeout=120)
                if r.status_code != 200:
                    continue
                zip_bytes = r.content

                dre = _read_demo_from_zip(zip_bytes, "itr", "DRE", y)
                bpa = _read_demo_from_zip(zip_bytes, "itr", "BPA", y)
                bpp = _read_demo_from_zip(zip_bytes, "itr", "BPP", y)

                dfc = _read_demo_from_zip(zip_bytes, "itr", "DFC_MI", y)
                if dfc.empty:
                    dfc = _read_demo_from_zip(zip_bytes, "itr", "DFC_MD", y)

                if not dre.empty:
                    acc["dre_tri"].append(_format_out(dre, force_t4=False))
                if not bpa.empty:
                    acc["bpa_tri"].append(_format_out(bpa, force_t4=False))
                if not bpp.empty:
                    acc["bpp_tri"].append(_format_out(bpp, force_t4=False))
                if not dfc.empty:
                    acc["dfc_tri"].append(_format_out(dfc, force_t4=False))

            # DFP (anual / T4)
            for y in years:
                url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{y}.zip"
                r = requests.get(url, timeout=120)
                if r.status_code != 200:
                    continue
                zip_bytes = r.content

                dre = _read_demo_from_zip(zip_bytes, "dfp", "DRE", y)
                bpa = _read_demo_from_zip(zip_bytes, "dfp", "BPA", y)
                bpp = _read_demo_from_zip(zip_bytes, "dfp", "BPP", y)

                dfc = _read_demo_from_zip(zip_bytes, "dfp", "DFC_MI", y)
                if dfc.empty:
                    dfc = _read_demo_from_zip(zip_bytes, "dfp", "DFC_MD", y)

                if not dre.empty:
                    acc["dre_anu"].append(_format_out(dre, force_t4=True))
                if not bpa.empty:
                    acc["bpa_anu"].append(_format_out(bpa, force_t4=True))
                if not bpp.empty:
                    acc["bpp_anu"].append(_format_out(bpp, force_t4=True))
                if not dfc.empty:
                    acc["dfc_anu"].append(_format_out(dfc, force_t4=True))

            def _concat(parts):
                if not parts:
                    return pd.DataFrame(columns=["data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"])
                df = pd.concat(parts, ignore_index=True)
                df["data_fim_dt"] = pd.to_datetime(df["data_fim"], errors="coerce")
                df = df.sort_values(["data_fim_dt", "cd_conta"]).drop(columns=["data_fim_dt"])
                return df.reset_index(drop=True)

            dre_tri = _concat(acc["dre_tri"])
            dre_anu = _concat(acc["dre_anu"])
            bpa_tri = _concat(acc["bpa_tri"])
            bpa_anu = _concat(acc["bpa_anu"])
            bpp_tri = _concat(acc["bpp_tri"])
            bpp_anu = _concat(acc["bpp_anu"])
            dfc_tri = _concat(acc["dfc_tri"])
            dfc_anu = _concat(acc["dfc_anu"])

            # salva (mesmo se vazio, salva cabeçalho)
            dre_tri.to_csv(out_dir / "dre_trimestral.csv", index=False)
            dre_anu.to_csv(out_dir / "dre_anual.csv", index=False)

            bpa_tri.to_csv(out_dir / "bpa_trimestral.csv", index=False)
            bpa_anu.to_csv(out_dir / "bpa_anual.csv", index=False)

            bpp_tri.to_csv(out_dir / "bpp_trimestral.csv", index=False)
            bpp_anu.to_csv(out_dir / "bpp_anual.csv", index=False)

            dfc_tri.to_csv(out_dir / "dfc_trimestral.csv", index=False)
            dfc_anu.to_csv(out_dir / "dfc_anual.csv", index=False)

            print(f"[OK] Captura finalizada: {ticker} (CD_CVM={cd_cvm}) -> {out_dir}")
            sucesso += 1

        except Exception as e:
            falhas += 1
            print(f"[ERRO] Falha ao capturar {ticker}: {e}")

    print(f"\n{'='*60}")
    print("RESUMO DA CAPTURA")
    print(f"{'='*60}")
    print(f"Total processados: {len(tickers_selecionados)}")
    print(f"Sucesso: {sucesso}")
    print(f"Falhas: {falhas}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
