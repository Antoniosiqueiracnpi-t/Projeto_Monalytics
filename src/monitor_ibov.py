"""
MONITOR IBOVESPA - VARIAÇÕES DIÁRIAS
====================================
Janeiro 2025

Monitora variações intraday das ações do IBOVESPA.
Atualiza a cada 30min (seg-sex, 10h30-18h30).

SAÍDA:
- balancos/IBOV/monitor_diario.json

TOP 5:
- Maiores altas
- Maiores baixas
- Maiores volumes
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    print("❌ yfinance não instalado: pip install yfinance")


# ======================================================================================
# CONFIGURAÇÃO
# ======================================================================================

IBOV_TICKERS_CSV = Path("ibov_tickers.csv")
OUTPUT_DIR = Path("balancos") / "IBOV"
OUTPUT_FILE = "monitor_diario.json"


# ======================================================================================
# CAPTURA DE COTAÇÕES
# ======================================================================================

def carregar_tickers() -> List[str]:
    """Carrega lista de tickers do IBOVESPA."""
    if not IBOV_TICKERS_CSV.exists():
        print(f"❌ Arquivo não encontrado: {IBOV_TICKERS_CSV}")
        return []
    
    try:
        df = pd.read_csv(IBOV_TICKERS_CSV, encoding='utf-8')
        if 'ticker' not in df.columns:
            return []
        
        tickers = df['ticker'].dropna().astype(str).str.strip().tolist()
        return [t for t in tickers if t]
    except Exception as e:
        print(f"❌ Erro ao ler CSV: {e}")
        return []


def buscar_cotacao_ticker(ticker: str) -> Optional[Dict]:
    """
    Busca cotação atual e calcula variação do dia.
    
    Returns:
        {
            'ticker': str,
            'preco_atual': float,
            'preco_anterior': float,
            'variacao_pct': float,
            'volume': int
        }
    """
    if not HAS_YFINANCE:
        return None
    
    ticker_yahoo = f"{ticker}.SA"
    
    try:
        stock = yf.Ticker(ticker_yahoo)
        
        # Buscar dados do dia com PREÇOS AJUSTADOS
        hist = stock.history(period='2d', auto_adjust=True)  # ← CORREÇÃO
        
        if hist is None or len(hist) < 2:
            return None
        
        # Preço anterior (último fechamento)
        preco_anterior = float(hist['Close'].iloc[-2])
        
        # Preço atual (último disponível)
        preco_atual = float(hist['Close'].iloc[-1])
        
        # Volume do dia atual
        volume = int(hist['Volume'].iloc[-1])
        
        # Variação percentual
        if preco_anterior > 0:
            variacao_pct = ((preco_atual - preco_anterior) / preco_anterior) * 100
        else:
            variacao_pct = 0.0
        
        return {
            'ticker': ticker,
            'preco_atual': round(preco_atual, 2),
            'preco_anterior': round(preco_anterior, 2),
            'variacao_pct': round(variacao_pct, 2),
            'volume': volume
        }
        
    except Exception as e:
        # Silencioso - muitos tickers podem falhar
        return None


# ======================================================================================
# ANÁLISE E RANKINGS
# ======================================================================================

def processar_ibovespa() -> Dict:
    """
    Processa todos os tickers do IBOVESPA e gera rankings.
    
    Returns:
        {
            'ultima_atualizacao': str,
            'total_acoes': int,
            'top_5_altas': [...],
            'top_5_baixas': [...],
            'top_5_volumes': [...]
        }
    """
    print(f"\n{'='*70}")
    print(f"📊 MONITOR IBOVESPA - VARIAÇÕES DIÁRIAS")
    print(f"{'='*70}\n")
    
    tickers = carregar_tickers()
    
    if not tickers:
        print("❌ Nenhum ticker carregado")
        return {"erro": "Nenhum ticker carregado"}
    
    print(f"Total de tickers: {len(tickers)}")
    print(f"Buscando cotações...\n")
    
    # Buscar todas as cotações
    cotacoes = []
    
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] {ticker}...", end=" ")
        
        cot = buscar_cotacao_ticker(ticker)
        
        if cot:
            cotacoes.append(cot)
            var = cot['variacao_pct']
            sinal = "📈" if var > 0 else "📉" if var < 0 else "➡️"
            print(f"{sinal} {var:+.2f}%")
        else:
            print("⚠️  sem dados")
    
    print(f"\n{'='*70}")
    print(f"Cotações obtidas: {len(cotacoes)}/{len(tickers)}")
    print(f"{'='*70}\n")
    
    if len(cotacoes) == 0:
        return {"erro": "Nenhuma cotação obtida"}
    
    # Criar DataFrame para facilitar análise
    df = pd.DataFrame(cotacoes)
    
    # TOP 5 MAIORES ALTAS
    top_altas = df.nlargest(5, 'variacao_pct')[
        ['ticker', 'variacao_pct', 'preco_atual', 'volume']
    ].to_dict('records')
    
    # TOP 5 MAIORES BAIXAS (variação mais negativa)
    top_baixas = df.nsmallest(5, 'variacao_pct')[
        ['ticker', 'variacao_pct', 'preco_atual', 'volume']
    ].to_dict('records')
    
    # TOP 5 MAIORES VOLUMES
    top_volumes = df.nlargest(5, 'volume')[
        ['ticker', 'volume', 'variacao_pct', 'preco_atual']
    ].to_dict('records')
    
    # Estatísticas gerais
    media_variacao = df['variacao_pct'].mean()
    acoes_alta = len(df[df['variacao_pct'] > 0])
    acoes_baixa = len(df[df['variacao_pct'] < 0])
    acoes_estavel = len(df[df['variacao_pct'] == 0])
    
    return {
        'ultima_atualizacao': datetime.now().isoformat(),
        'total_acoes': len(cotacoes),
        'estatisticas': {
            'variacao_media': round(media_variacao, 2),
            'acoes_em_alta': acoes_alta,
            'acoes_em_baixa': acoes_baixa,
            'acoes_estaveis': acoes_estavel
        },
        'top_5_altas': top_altas,
        'top_5_baixas': top_baixas,
        'top_5_volumes': top_volumes
    }


# ======================================================================================
# SALVAMENTO
# ======================================================================================

def salvar_resultado(dados: Dict) -> bool:
    """Salva resultado em JSON."""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        arquivo = OUTPUT_DIR / OUTPUT_FILE
        
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Arquivo salvo: {arquivo}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")
        return False


# ======================================================================================
# EXIBIÇÃO DE RESULTADOS
# ======================================================================================

def exibir_resumo(dados: Dict):
    """Exibe resumo dos resultados."""
    if 'erro' in dados:
        print(f"\n❌ {dados['erro']}")
        return
    
    stats = dados.get('estatisticas', {})
    
    print(f"\n{'='*70}")
    print(f"📊 RESUMO DO PREGÃO")
    print(f"{'='*70}")
    print(f"Variação média: {stats.get('variacao_media', 0):+.2f}%")
    print(f"Em alta: {stats.get('acoes_em_alta', 0)} | Em baixa: {stats.get('acoes_em_baixa', 0)} | Estáveis: {stats.get('acoes_estaveis', 0)}")
    print(f"{'='*70}\n")
    
    # TOP 5 ALTAS
    print("🚀 TOP 5 MAIORES ALTAS:")
    print(f"{'Ticker':<10} {'Variação':<12} {'Preço':<12} {'Volume'}")
    print("-" * 70)
    for acao in dados.get('top_5_altas', []):
        print(f"{acao['ticker']:<10} {acao['variacao_pct']:>+6.2f}%     R$ {acao['preco_atual']:>8.2f}   {acao['volume']:>15,}")
    
    # TOP 5 BAIXAS
    print(f"\n📉 TOP 5 MAIORES BAIXAS:")
    print(f"{'Ticker':<10} {'Variação':<12} {'Preço':<12} {'Volume'}")
    print("-" * 70)
    for acao in dados.get('top_5_baixas', []):
        print(f"{acao['ticker']:<10} {acao['variacao_pct']:>+6.2f}%     R$ {acao['preco_atual']:>8.2f}   {acao['volume']:>15,}")
    
    # TOP 5 VOLUMES
    print(f"\n💰 TOP 5 MAIORES VOLUMES:")
    print(f"{'Ticker':<10} {'Volume':<20} {'Variação':<12} {'Preço'}")
    print("-" * 70)
    for acao in dados.get('top_5_volumes', []):
        print(f"{acao['ticker']:<10} {acao['volume']:>15,}     {acao['variacao_pct']:>+6.2f}%     R$ {acao['preco_atual']:>8.2f}")
    
    print(f"\n{'='*70}\n")


# ======================================================================================
# MAIN
# ======================================================================================

def main():
    if not HAS_YFINANCE:
        print("❌ Instale yfinance: pip install yfinance")
        return
    
    # Processar
    resultado = processar_ibovespa()
    
    # Exibir
    exibir_resumo(resultado)
    
    # Salvar
    salvar_resultado(resultado)


if __name__ == "__main__":
    main()
