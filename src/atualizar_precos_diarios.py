# src/atualizar_precos_diarios.py
"""
Atualização Diária de Preços e Múltiplos de Valuation
=====================================================
VERSÃO CORRIGIDA - Janeiro 2025

Este script:
1. Baixa preços de fechamento do dia anterior para todas as empresas
2. Atualiza os arquivos precos_trimestrais.csv
3. Recalcula APENAS os múltiplos de valuation (que dependem de preço):
   - P/L, P/VPA, EV/EBITDA, EV/EBIT, EV/Receita, DY
4. Mantém intactos os múltiplos fundamentalistas (ROE, ROA, etc)

Fonte de dados: yfinance (Yahoo Finance)
Periodicidade: Execução diária (após fechamento do mercado)

CORREÇÕES APLICADAS:
1. Atualização correta do CSV de preços
2. Recálculo usando preço mais recente
3. Atualização do período de ações se necessário
4. Processamento de TODAS as classes de ações (ON, PN, UNIT)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Importar utilitários do projeto
sys.path.insert(0, str(Path(__file__).parent))
from multi_ticker_utils import get_ticker_principal, get_pasta_balanco, load_mapeamento_consolidado

# Tentar importar yfinance
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    print("⚠️  yfinance não instalado. Execute: pip install yfinance")


# ======================================================================================
# CONFIGURAÇÕES
# ======================================================================================

# Mapeamento de códigos B3 para Yahoo Finance
SUFIXO_YAHOO = ".SA"


# ======================================================================================
# FUNÇÕES DE DOWNLOAD DE PREÇOS
# ======================================================================================

def _ticker_para_yahoo(ticker: str) -> str:
    """Converte ticker B3 para formato Yahoo Finance."""
    ticker_clean = ticker.upper().strip()
    if not ticker_clean.endswith(SUFIXO_YAHOO):
        return f"{ticker_clean}{SUFIXO_YAHOO}"
    return ticker_clean


def baixar_preco_ultimo_dia(ticker: str, max_dias_atras: int = 10) -> Optional[Dict[str, float]]:
    """
    Baixa o preço de fechamento ajustado do último dia disponível.
    
    Args:
        ticker: Ticker B3 (ex: PETR4, VALE3)
        max_dias_atras: Máximo de dias para buscar retroativamente
    
    Returns:
        {
            'data': 'YYYY-MM-DD',
            'preco_fechamento': float,
            'preco_ajustado': float,
            'volume': float
        }
    """
    if not HAS_YFINANCE:
        return None
    
    ticker_yahoo = _ticker_para_yahoo(ticker)
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=max_dias_atras)
        
        stock = yf.Ticker(ticker_yahoo)
        hist = stock.history(start=start_date, end=end_date)
        
        if hist.empty:
            return None
        
        last_row = hist.iloc[-1]
        last_date = hist.index[-1]
        
        return {
            'data': last_date.strftime('%Y-%m-%d'),
            'preco_fechamento': float(last_row['Close']),
            'preco_ajustado': float(last_row['Close']),
            'volume': float(last_row['Volume']) if 'Volume' in last_row else 0.0
        }
        
    except Exception as e:
        print(f"⚠️  Erro ao baixar {ticker}: {e}")
        return None


def baixar_precos_lote(tickers: List[str], max_workers: int = 10) -> Dict[str, Optional[Dict]]:
    """
    Baixa preços para múltiplos tickers em paralelo.
    
    Returns:
        {ticker: dados_preco}
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    resultados = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(baixar_preco_ultimo_dia, ticker): ticker 
            for ticker in tickers
        }
        
        for future in as_completed(futures):
            ticker = futures[future]
            try:
                dados = future.result()
                resultados[ticker] = dados
            except Exception as e:
                print(f"❌ Erro em {ticker}: {e}")
                resultados[ticker] = None
    
    return resultados


# ======================================================================================
# ATUALIZAÇÃO DE ARQUIVOS PRECOS_TRIMESTRAIS.CSV - CORRIGIDA
# ======================================================================================

def _determinar_trimestre(data: datetime) -> str:
    """Determina o trimestre de uma data."""
    ano = data.year
    mes = data.month
    trimestre = (mes - 1) // 3 + 1
    return f"{ano}T{trimestre}"


def atualizar_arquivo_precos(ticker: str, preco_novo: Dict[str, float]) -> Tuple[bool, str]:
    """
    Atualiza o arquivo precos_trimestrais.csv com novo preço.
    
    FORMATO DO CSV:
    Preço_Fechamento,2015T1,2015T2,...,2025T3
    Preço de Fechamento Ajustado,2.11,2.12,...,15.56
    
    Returns:
        (sucesso, mensagem)
    """
    pasta = get_pasta_balanco(ticker)
    arquivo_precos = pasta / "precos_trimestrais.csv"
    
    if not arquivo_precos.exists():
        return False, "arquivo precos_trimestrais.csv não existe"
    
    try:
        df = pd.read_csv(arquivo_precos)
        
        # Determinar trimestre atual
        data_preco = datetime.strptime(preco_novo['data'], '%Y-%m-%d')
        periodo = _determinar_trimestre(data_preco)
        
        preco_valor = round(preco_novo['preco_ajustado'], 2)
        
        # Verificar se coluna já existe
        if periodo in df.columns:
            # Atualizar valor existente na primeira linha de dados
            df.iloc[0, df.columns.get_loc(periodo)] = preco_valor
            acao = "atualizado"
        else:
            # Adicionar nova coluna
            df[periodo] = [preco_valor]
            acao = "adicionado"
        
        # Salvar
        df.to_csv(arquivo_precos, index=False)
        return True, f"{acao} {periodo}=R${preco_valor}"
        
    except Exception as e:
        return False, f"erro: {e}"


def atualizar_arquivo_acoes(ticker: str, periodo: str) -> Tuple[bool, str]:
    """
    Atualiza o arquivo acoes_historico.csv para incluir novo período.
    
    Se o período não existe, copia os valores do último período disponível.
    Isso é necessário porque o número de ações só muda em eventos corporativos.
    
    Returns:
        (sucesso, mensagem)
    """
    pasta = get_pasta_balanco(ticker)
    arquivo_acoes = pasta / "acoes_historico.csv"
    
    if not arquivo_acoes.exists():
        return False, "arquivo acoes_historico.csv não existe"
    
    try:
        df = pd.read_csv(arquivo_acoes)
        
        if periodo in df.columns:
            return True, f"período {periodo} já existe"
        
        # Encontrar último período disponível
        colunas_periodos = [c for c in df.columns if c not in ['Espécie_Acao']]
        if not colunas_periodos:
            return False, "nenhum período encontrado"
        
        # Ordenar para pegar o mais recente
        ultimo_periodo = sorted(colunas_periodos)[-1]
        
        # Copiar valores do último período
        df[periodo] = df[ultimo_periodo]
        
        # Salvar
        df.to_csv(arquivo_acoes, index=False)
        return True, f"copiado de {ultimo_periodo}"
        
    except Exception as e:
        return False, f"erro: {e}"


# ======================================================================================
# RECÁLCULO DE MÚLTIPLOS DE VALUATION - CORRIGIDO
# ======================================================================================

def recalcular_multiplos_completo(ticker: str) -> Tuple[bool, str]:
    """
    Recalcula todos os múltiplos usando o script principal.
    
    Esta é a forma mais robusta pois garante consistência total.
    
    Returns:
        (sucesso, mensagem)
    """
    try:
        from calcular_multiplos import processar_ticker
        
        sucesso, msg, resultado = processar_ticker(ticker, salvar=True)
        
        if sucesso and resultado:
            ltm = resultado.get("ltm", {})
            preco = ltm.get("preco_utilizado", "?")
            multiplos = ltm.get("multiplos", {})
            p_l = multiplos.get("P_L", "?")
            
            # Para empresas não-financeiras, mostrar EV/EBITDA
            # Para bancos/seguradoras, mostrar ROE
            if "EV_EBITDA" in multiplos:
                ev_ebitda = multiplos.get("EV_EBITDA", "?")
                return True, f"P/L={p_l} | EV/EBITDA={ev_ebitda} | Preço=R${preco}"
            elif "ROE" in multiplos:
                roe = multiplos.get("ROE", "?")
                return True, f"P/L={p_l} | ROE={roe}% | Preço=R${preco}"
            else:
                return True, f"P/L={p_l} | Preço=R${preco}"
        
        return False, msg
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"erro: {e}"


# ======================================================================================
# PROCESSADOR PRINCIPAL
# ======================================================================================

def processar_atualizacao_diaria(
    modo: str = "quantidade",
    quantidade: int = 10,
    ticker: str = "",
    lista: str = "",
    faixa: str = "1-50"
) -> Tuple[int, int, int]:
    """
    Processa atualização diária de preços e múltiplos.
    
    Returns:
        (sucesso, sem_preco, erro)
    """
    if not HAS_YFINANCE:
        print("❌ yfinance não está instalado!")
        print("Execute: pip install yfinance")
        return 0, 0, 0
    
    # Carregar mapeamento
    df = load_mapeamento_consolidado()
    df = df[df["cnpj"].notna()].reset_index(drop=True)
    
    # Selecionar empresas
    if modo == "quantidade":
        df_sel = df.head(quantidade)
    elif modo == "ticker":
        ticker_upper = ticker.upper()
        df_sel = df[df["ticker"].str.upper().str.contains(ticker_upper, case=False, na=False)]
    elif modo == "lista":
        tickers = [t.strip().upper() for t in lista.split(",") if t.strip()]
        mask = df["ticker"].str.upper().apply(
            lambda x: any(t in x for t in tickers) if pd.notna(x) else False
        )
        df_sel = df[mask]
    elif modo == "faixa":
        inicio, fim = map(int, faixa.split("-"))
        df_sel = df.iloc[inicio - 1 : fim]
    else:
        df_sel = df.head(10)
    
    print(f"\n{'='*70}")
    print(f">>> ATUALIZAÇÃO DIÁRIA DE PREÇOS E MÚLTIPLOS DE VALUATION <<<")
    print(f"{'='*70}")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Modo: {modo} | Selecionadas: {len(df_sel)}")
    print(f"ATENÇÃO: Processa TODAS as classes de ações (ON, PN, UNIT)")
    print(f"{'='*70}\n")
    
    # CORREÇÃO: Extrair TODOS os tickers individuais (processar cada classe)
    tickers_processar = []
    for _, row in df_sel.iterrows():
        ticker_str = str(row["ticker"]).upper().strip()
        # Exemplo: "ITUB3;ITUB4" → ['ITUB3', 'ITUB4']
        tickers = [t.strip() for t in ticker_str.split(';') if t.strip()]
        tickers_processar.extend(tickers)
    
    print(f"Total de tickers (incluindo todas as classes): {len(tickers_processar)}")
    print(f"Baixando preços...\n")
    
    # Baixar preços em lote
    precos = baixar_precos_lote(tickers_processar, max_workers=10)
    
    # Processar cada ticker
    ok_count = 0
    sem_preco_count = 0
    err_count = 0
    
    for ticker_clean in tickers_processar:
        preco_dados = precos.get(ticker_clean)
        
        if preco_dados is None:
            sem_preco_count += 1
            print(f"⏭️  {ticker_clean}: sem dados de preço")
            continue
        
        try:
            # 1. Determinar período do preço
            data_preco = datetime.strptime(preco_dados['data'], '%Y-%m-%d')
            periodo = _determinar_trimestre(data_preco)
            
            # 2. Atualizar arquivo de preços
            ok_preco, msg_preco = atualizar_arquivo_precos(ticker_clean, preco_dados)
            if not ok_preco:
                print(f"⚠️  {ticker_clean}: preços - {msg_preco}")
            
            # 3. Atualizar arquivo de ações (se necessário)
            ok_acoes, msg_acoes = atualizar_arquivo_acoes(ticker_clean, periodo)
            if not ok_acoes:
                print(f"⚠️  {ticker_clean}: ações - {msg_acoes}")
            
            # 4. Recalcular múltiplos
            ok_mult, msg_mult = recalcular_multiplos_completo(ticker_clean)
            
            if ok_mult:
                ok_count += 1
                print(f"✅ {ticker_clean}: {msg_mult}")
            else:
                err_count += 1
                print(f"❌ {ticker_clean}: {msg_mult}")
                
        except Exception as e:
            err_count += 1
            print(f"❌ {ticker_clean}: ERRO - {type(e).__name__}: {e}")
    
    print(f"\n{'='*70}")
    print(f"RESUMO: OK={ok_count} | SEM_PREÇO={sem_preco_count} | ERRO={err_count}")
    print(f"{'='*70}\n")
    
    return ok_count, sem_preco_count, err_count


# ======================================================================================
# CLI
# ======================================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Atualização Diária de Preços e Múltiplos de Valuation"
    )
    parser.add_argument("--modo", default="quantidade", 
                       choices=["quantidade", "ticker", "lista", "faixa"])
    parser.add_argument("--quantidade", default="10", type=int)
    parser.add_argument("--ticker", default="")
    parser.add_argument("--lista", default="")
    parser.add_argument("--faixa", default="1-50")
    args = parser.parse_args()
    
    processar_atualizacao_diaria(
        modo=args.modo,
        quantidade=args.quantidade,
        ticker=args.ticker,
        lista=args.lista,
        faixa=args.faixa
    )


if __name__ == "__main__":
    main()
