#!/usr/bin/env python3
"""
Captura balanços da B3/CVM com sistema de seleção de tickers.
Segue a ordem do arquivo mapeamento_final_b3_completo_utf8.csv

PATCH CIRÚRGICO:
- Mantém a lógica original de seleção/ordem
- Em vez de tentar importar captura_balancos_b3, chama diretamente:
    python src/capturar_balancos.py <TICKER>
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"


def carregar_tickers_ordenados(csv_name: str) -> List[str]:
    possible_paths = [
        REPO_ROOT / csv_name,
        SRC_DIR / csv_name,
        Path.cwd() / csv_name,
        Path(os.environ.get("GITHUB_WORKSPACE", ".")) / csv_name,
        Path(os.environ.get("GITHUB_WORKSPACE", ".")) / "src" / csv_name,
    ]

    csv_file: Optional[Path] = None
    for p in possible_paths:
        if p.exists():
            csv_file = p
            break

    if csv_file is None:
        print("[ERRO] Arquivo de mapeamento não encontrado.")
        print("       Procurado em:")
        for p in possible_paths:
            print(f"       - {p}")
        return []

    df = pd.read_csv(csv_file, sep=";", encoding="utf-8")
    if "ticker" not in df.columns:
        print("[ERRO] Coluna 'ticker' não encontrada no mapeamento.")
        return []

    tickers = df["ticker"].dropna().astype(str).str.strip().str.upper()
    seen = set()
    ordered = []
    for t in tickers:
        if t and t not in seen:
            seen.add(t)
            ordered.append(t)

    print(f"[INFO] Usando arquivo: {csv_file}")
    return ordered


def filtrar_tickers(all_tickers: List[str], modo: str, quantidade: str, ticker: str,
                   lista: str, faixa: str) -> List[str]:
    if modo == "quantidade":
        try:
            n = int(quantidade) if quantidade else 10
            return all_tickers[:n]
        except ValueError:
            print(f"[AVISO] Quantidade inválida '{quantidade}', usando 10")
            return all_tickers[:10]

    if modo == "ticker":
        if not ticker:
            print("[AVISO] Ticker não especificado, processando todos")
            return all_tickers
        t = ticker.strip().upper()
        return [x for x in all_tickers if x == t]

    if modo == "lista":
        if not lista:
            print("[AVISO] Lista vazia, processando todos")
            return all_tickers
        lst = [t.strip().upper() for t in lista.split(",") if t.strip()]
        return [x for x in all_tickers if x in lst]

    if modo == "faixa":
        if not faixa or "-" not in faixa:
            print(f"[AVISO] Faixa inválida '{faixa}', usando 1-50")
            start, end = 1, 50
        else:
            try:
                a, b = faixa.split("-", 1)
                start = int(a.strip())
                end = int(b.strip())
            except Exception:
                print(f"[AVISO] Faixa inválida '{faixa}', usando 1-50")
                start, end = 1, 50

        start_idx = max(0, start - 1)
        end_idx = max(start_idx, end)
        return all_tickers[start_idx:end_idx]

    return all_tickers


def main():
    parser = argparse.ArgumentParser(description="Captura balanços da B3/CVM com seleção de tickers")
    parser.add_argument("--modo", default="quantidade", choices=["quantidade", "ticker", "lista", "faixa"])
    parser.add_argument("--quantidade", default="10")
    parser.add_argument("--ticker", default="")
    parser.add_argument("--lista", default="")
    parser.add_argument("--faixa", default="1-50")
    parser.add_argument("--anos", default="12", help="Quantos anos voltar na captura (default 12)")

    args = parser.parse_args()

    all_tickers = carregar_tickers_ordenados("mapeamento_final_b3_completo_utf8.csv")
    if not all_tickers:
        sys.exit(1)

    tickers_sel = filtrar_tickers(all_tickers, args.modo, args.quantidade, args.ticker, args.lista, args.faixa)
    if not tickers_sel:
        print("[AVISO] Nenhum ticker selecionado.")
        sys.exit(0)

    print(f"\n{'='*60}")
    print(f"Modo: {args.modo}")
    print(f"Tickers selecionados: {len(tickers_sel)}")
    print(f"{'='*60}\n")

    preview = tickers_sel[:10]
    print("Primeiros tickers a processar:")
    for i, t in enumerate(preview, 1):
        print(f"  {i}. {t}")
    if len(tickers_sel) > 10:
        print(f"  ... e mais {len(tickers_sel) - 10} tickers")
    print()

    motor = SRC_DIR / "capturar_balancos.py"
    if not motor.exists():
        print("[ERRO] Motor de captura não encontrado: src/capturar_balancos.py")
        sys.exit(1)

    sucesso = 0
    falhas = 0

    for idx, t in enumerate(tickers_sel, 1):
        print(f"\n[{idx}/{len(tickers_sel)}] Processando {t}...")
        rc = subprocess.run(
            [sys.executable, str(motor), t, "--anos", str(args.anos)],
            check=False,
            env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
        ).returncode

        if rc == 0:
            sucesso += 1
        else:
            falhas += 1
            print(f"[ERRO] Falha ao capturar {t} (returncode={rc})")

    print(f"\n{'='*60}")
    print("RESUMO DA CAPTURA")
    print(f"{'='*60}")
    print(f"Total processados: {len(tickers_sel)}")
    print(f"Sucesso: {sucesso}")
    print(f"Falhas: {falhas}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
