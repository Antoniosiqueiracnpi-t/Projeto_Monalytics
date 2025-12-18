#!/usr/bin/env python3
import sys
import os
import argparse
import subprocess
from pathlib import Path
from typing import List
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


def carregar_tickers_ordenados(csv_path: Path) -> List[str]:
    possible_paths = [
        csv_path,
        REPO_ROOT / csv_path.name,
        Path.cwd() / csv_path.name,
        Path(__file__).parent.parent / csv_path.name,
        Path(os.environ.get('GITHUB_WORKSPACE', '.')) / csv_path.name,
    ]
    
    csv_file = None
    for path in possible_paths:
        if path.exists():
            csv_file = path
            break
    
    if csv_file is None:
        return []
    
    try:
        df = pd.read_csv(csv_file, sep=';', encoding='utf-8')
        if 'ticker' not in df.columns:
            return []
        
        tickers = df['ticker'].dropna().astype(str).str.strip().str.upper()
        seen = set()
        ordered_tickers = []
        for t in tickers:
            if t not in seen and t:
                seen.add(t)
                ordered_tickers.append(t)
        
        print(f"[INFO] Usando arquivo: {csv_file}")
        return ordered_tickers
    except Exception as e:
        print(f"[ERRO] Falha ao ler CSV: {e}")
        return []


def filtrar_tickers(all_tickers: List[str], modo: str, quantidade: str, ticker: str, 
                   lista: str, faixa: str) -> List[str]:
    if modo == "quantidade":
        try:
            n = int(quantidade) if quantidade else 10
            return all_tickers[:n]
        except ValueError:
            return all_tickers[:10]
    
    elif modo == "ticker":
        if not ticker:
            return all_tickers
        ticker_upper = ticker.strip().upper()
        return [t for t in all_tickers if t == ticker_upper]
    
    elif modo == "lista":
        if not lista:
            return all_tickers
        tickers_list = [t.strip().upper() for t in lista.split(",") if t.strip()]
        return [t for t in all_tickers if t in tickers_list]
    
    elif modo == "faixa":
        if not faixa or "-" not in faixa:
            start, end = 1, 50
        else:
            try:
                parts = faixa.split("-")
                start = int(parts[0].strip())
                end = int(parts[1].strip())
            except (ValueError, IndexError):
                start, end = 1, 50
        
        start_idx = max(0, start - 1)
        end_idx = end
        return all_tickers[start_idx:end_idx]
    
    else:
        return all_tickers


def main():
    parser = argparse.ArgumentParser(description="Captura balanços da B3/CVM")
    parser.add_argument("--modo", default="quantidade", choices=["quantidade", "ticker", "lista", "faixa"])
    parser.add_argument("--quantidade", default="10")
    parser.add_argument("--ticker", default="")
    parser.add_argument("--lista", default="")
    parser.add_argument("--faixa", default="1-50")
    args = parser.parse_args()
    
    mapping_file = REPO_ROOT / "mapeamento_final_b3_completo_utf8.csv"
    all_tickers = carregar_tickers_ordenados(mapping_file)
    
    if not all_tickers:
        print("[ERRO] Nenhum ticker encontrado")
        sys.exit(1)
    
    print(f"Total de tickers disponíveis: {len(all_tickers)}")
    print(f"Primeiro ticker: {all_tickers[0]}")
    print(f"Último ticker: {all_tickers[-1]}")
    
    tickers_selecionados = filtrar_tickers(all_tickers, args.modo, args.quantidade, 
                                          args.ticker, args.lista, args.faixa)
    
    if not tickers_selecionados:
        print("[AVISO] Nenhum ticker selecionado")
        sys.exit(0)
    
    print(f"\n{'='*60}")
    print(f"Modo: {args.modo}")
    print(f"Tickers selecionados: {len(tickers_selecionados)}")
    print(f"{'='*60}\n")
    
    preview = tickers_selecionados[:10]
    print("Primeiros tickers a processar:")
    for i, t in enumerate(preview, 1):
        print(f"  {i}. {t}")
    if len(tickers_selecionados) > 10:
        print(f"  ... e mais {len(tickers_selecionados) - 10} tickers")
    print()
    
    # Procura script de captura
    for script_name in ["captura_balancos.py", "capturar_balancos.py"]:
        captura_script = REPO_ROOT / script_name
        if captura_script.exists():
            break
    else:
        print("[ERRO] Script de captura não encontrado na raiz do repositório")
        print("       Crie 'captura_balancos.py' que aceite ticker como argumento")
        print("       Exemplo: python captura_balancos.py PETR4")
        sys.exit(1)
    
    print(f"[INFO] Usando script: {captura_script.name}\n")
    
    sucesso = 0
    falhas = 0
    
    for idx, ticker in enumerate(tickers_selecionados, 1):
        print(f"[{idx}/{len(tickers_selecionados)}] Processando {ticker}...")
        try:
            result = subprocess.run(
                [sys.executable, str(captura_script), ticker],
                capture_output=False,
                check=False
            )
            if result.returncode == 0:
                sucesso += 1
            else:
                falhas += 1
        except Exception as e:
            falhas += 1
            print(f"[ERRO] {ticker}: {e}")
    
    print(f"\n{'='*60}")
    print(f"RESUMO")
    print(f"{'='*60}")
    print(f"Total: {len(tickers_selecionados)}")
    print(f"Sucesso: {sucesso}")
    print(f"Falhas: {falhas}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
