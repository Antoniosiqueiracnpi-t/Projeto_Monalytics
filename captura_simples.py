#!/usr/bin/env python3
"""
Captura balanços da B3/CVM com sistema de seleção de tickers.
Segue a ordem do arquivo mapeamento_final_b3_completo_utf8.csv
"""

import sys
import os
import argparse
from pathlib import Path
from typing import List
import pandas as pd

# Adiciona o diretório src ao path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# Importa a função de captura
try:
    from captura_balancos_b3 import capturar_balancos_empresa
except ImportError:
    print("[ERRO] Não foi possível importar captura_balancos_b3")
    print("       Verifique se o arquivo existe em src/")
    sys.exit(1)


def carregar_tickers_ordenados(csv_path: Path) -> List[str]:
    """
    Carrega os tickers na ordem exata em que aparecem no CSV de mapeamento.
    """
    if not csv_path.exists():
        print(f"[AVISO] Arquivo de mapeamento não encontrado: {csv_path}")
        return []
    
    try:
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
        if 'ticker' not in df.columns:
            print("[AVISO] Coluna 'ticker' não encontrada no CSV de mapeamento")
            return []
        
        # Retorna tickers na ordem do arquivo, removendo duplicatas mas mantendo primeira ocorrência
        tickers = df['ticker'].dropna().astype(str).str.strip().str.upper()
        # Remove duplicatas mantendo a ordem (primeira ocorrência)
        seen = set()
        ordered_tickers = []
        for t in tickers:
            if t not in seen and t:
                seen.add(t)
                ordered_tickers.append(t)
        
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
        # Retorna lista com único ticker se encontrado
        return [t for t in all_tickers if t == ticker_upper]
    
    elif modo == "lista":
        if not lista:
            print("[AVISO] Lista vazia, processando todos")
            return all_tickers
        tickers_list = [t.strip().upper() for t in lista.split(",") if t.strip()]
        # Mantém a ordem original do all_tickers, mas filtra pelos da lista
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
        
        # Ajusta índices (base 1 para base 0)
        start_idx = max(0, start - 1)
        end_idx = end
        return all_tickers[start_idx:end_idx]
    
    else:
        return all_tickers


def main():
    parser = argparse.ArgumentParser(
        description="Captura balanços da B3/CVM com seleção de tickers"
    )
    parser.add_argument(
        "--modo",
        default="quantidade",
        choices=["quantidade", "ticker", "lista", "faixa"],
        help="Modo de seleção de tickers"
    )
    parser.add_argument(
        "--quantidade",
        default="10",
        help="Número de tickers (modo quantidade)"
    )
    parser.add_argument(
        "--ticker",
        default="",
        help="Ticker único (modo ticker)"
    )
    parser.add_argument(
        "--lista",
        default="",
        help="Lista de tickers separados por vírgula (modo lista)"
    )
    parser.add_argument(
        "--faixa",
        default="1-50",
        help="Faixa de tickers no formato inicio-fim (modo faixa)"
    )
    
    args = parser.parse_args()
    
    # Localiza o arquivo de mapeamento
    mapping_file = REPO_ROOT / "mapeamento_final_b3_completo_utf8.csv"
    
    # Carrega tickers na ordem do arquivo
    all_tickers = carregar_tickers_ordenados(mapping_file)
    
    if not all_tickers:
        print("[ERRO] Nenhum ticker encontrado no arquivo de mapeamento")
        print(f"       Verifique se existe: {mapping_file}")
        sys.exit(1)
    
    print(f"Total de tickers disponíveis: {len(all_tickers)}")
    print(f"Primeiro ticker: {all_tickers[0]}")
    print(f"Último ticker: {all_tickers[-1]}")
    
    # Aplica filtro
    tickers_selecionados = filtrar_tickers(
        all_tickers,
        args.modo,
        args.quantidade,
        args.ticker,
        args.lista,
        args.faixa
    )
    
    if not tickers_selecionados:
        print("[AVISO] Nenhum ticker selecionado com os critérios fornecidos")
        sys.exit(0)
    
    print(f"\n{'='*60}")
    print(f"Modo: {args.modo}")
    print(f"Tickers selecionados: {len(tickers_selecionados)}")
    print(f"{'='*60}\n")
    
    # Mostra primeiros tickers que serão processados
    preview = tickers_selecionados[:10]
    print("Primeiros tickers a processar:")
    for i, t in enumerate(preview, 1):
        print(f"  {i}. {t}")
    if len(tickers_selecionados) > 10:
        print(f"  ... e mais {len(tickers_selecionados) - 10} tickers")
    print()
    
    # Processa cada ticker
    sucesso = 0
    falhas = 0
    
    for idx, ticker in enumerate(tickers_selecionados, 1):
        print(f"\n[{idx}/{len(tickers_selecionados)}] Processando {ticker}...")
        try:
            capturar_balancos_empresa(ticker)
            sucesso += 1
        except Exception as e:
            falhas += 1
            print(f"[ERRO] Falha ao capturar {ticker}: {e}")
    
    # Resumo final
    print(f"\n{'='*60}")
    print(f"RESUMO DA CAPTURA")
    print(f"{'='*60}")
    print(f"Total processados: {len(tickers_selecionados)}")
    print(f"Sucesso: {sucesso}")
    print(f"Falhas: {falhas}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
