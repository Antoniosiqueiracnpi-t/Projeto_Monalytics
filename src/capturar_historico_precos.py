"""
CAPTURADOR DE HISTÓRICO DE PREÇOS - 5 ANOS + MÉDIAS MÓVEIS
==========================================================
Janeiro 2025

Captura histórico de preços ajustados dos últimos 5 anos e calcula:
- Médias móveis: 20, 50, 200 períodos
- Estatísticas: máxima, mínima, variação

CLASSES SUPORTADAS: 3, 4, 11 + IBOVESPA (^BVSP)
SAÍDA: balancos/{TICKER}/historico_precos.json

EXECUÇÃO:
python src/capturar_historico_precos.py --modo lista --lista "PETR4,VALE3,BBDC4"
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

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    print("❌ yfinance não instalado: pip install yfinance")


# ======================================================================================
# UTILITÁRIOS DE MAPEAMENTO
# ======================================================================================

def load_mapeamento_b3() -> pd.DataFrame:
    """Carrega mapeamento de tickers B3 do CSV."""
    csv_path = Path("mapeamento_b3_consolidado.csv")
    
    if not csv_path.exists():
        print(f"❌ Arquivo não encontrado: {csv_path}")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(csv_path, encoding='utf-8', sep=',')
        return df
    except Exception as e:
        print(f"❌ Erro ao ler CSV: {e}")
        return pd.DataFrame()


def get_pasta_balanco(ticker: str) -> Path:
    """
    Retorna pasta balancos/{TICKER_BASE}/ para salvar dados.
    Remove sufixos numéricos (3, 4, 11) do ticker.
    """
    # Remover sufixos de classe
    ticker_base = ticker.rstrip('0123456789')
    
    # Se ficou vazio, usar o ticker original
    if not ticker_base:
        ticker_base = ticker
    
    return Path("balancos") / ticker_base.upper()


# ======================================================================================
# CONFIGURAÇÕES
# ======================================================================================

ANOS_HISTORICO = 5
PERIODOS_MM = [20, 50, 200]  # Médias móveis


# ======================================================================================
# CAPTURA DE DADOS
# ======================================================================================

def capturar_historico_ticker(ticker: str, anos: int = ANOS_HISTORICO) -> Optional[pd.DataFrame]:
    """
    Captura histórico de preços ajustados via yfinance.
    
    Args:
        ticker: Código B3 (ex: PETR4) ou ^BVSP para Ibovespa
        anos: Anos de histórico (padrão: 5)
    
    Returns:
        DataFrame com OHLCV ou None
    """
    if not HAS_YFINANCE:
        return None
    
    # Converter para formato Yahoo
    if ticker == "IBOV":
        ticker_yahoo = "^BVSP"
    else:
        ticker_yahoo = f"{ticker}.SA" if not ticker.endswith(".SA") else ticker
    
    # Período
    end_date = datetime.now()
    start_date = end_date - timedelta(days=anos * 365 + 30)  # +30 dias de margem
    
    try:
        hist = yf.download(
            ticker_yahoo,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            progress=False,
            auto_adjust=True  # Preços ajustados
        )
        
        if hist.empty:
            return None
        
        # Renomear colunas para padrão
        hist = hist.rename(columns={
            'Open': 'abertura',
            'High': 'maxima',
            'Low': 'minima',
            'Close': 'fechamento',
            'Volume': 'volume'
        })
        
        # Garantir que índice é datetime
        hist.index = pd.to_datetime(hist.index)
        
        return hist[['abertura', 'maxima', 'minima', 'fechamento', 'volume']]
        
    except Exception as e:
        print(f"  ⚠️  Erro ao baixar {ticker}: {e}")
        return None


# ======================================================================================
# CÁLCULO DE MÉDIAS MÓVEIS
# ======================================================================================

def calcular_medias_moveis(df: pd.DataFrame, periodos: List[int] = PERIODOS_MM) -> pd.DataFrame:
    """
    Calcula médias móveis do fechamento.
    
    Args:
        df: DataFrame com coluna 'fechamento'
        periodos: Lista de períodos (ex: [20, 50, 200])
    
    Returns:
        DataFrame com colunas mm20, mm50, mm200 adicionadas
    """
    df = df.copy()
    
    for periodo in periodos:
        col_name = f"mm{periodo}"
        df[col_name] = df['fechamento'].rolling(window=periodo, min_periods=periodo).mean()
    
    return df


# ======================================================================================
# ESTATÍSTICAS
# ======================================================================================

def calcular_estatisticas(df: pd.DataFrame) -> Dict:
    """Calcula estatísticas do período."""
    if df.empty:
        return {}
    
    primeiro_preco = df['fechamento'].iloc[0]
    ultimo_preco = df['fechamento'].iloc[-1]
    variacao_pct = ((ultimo_preco - primeiro_preco) / primeiro_preco * 100) if primeiro_preco > 0 else 0
    
    return {
        "total_dias": len(df),
        "preco_inicial": round(float(primeiro_preco), 2),
        "preco_atual": round(float(ultimo_preco), 2),
        "variacao_periodo": round(variacao_pct, 2),
        "maxima_periodo": round(float(df['fechamento'].max()), 2),
        "minima_periodo": round(float(df['fechamento'].min()), 2),
        "volume_medio": int(df['volume'].mean()) if 'volume' in df.columns else 0
    }


# ======================================================================================
# CONVERSÃO PARA JSON
# ======================================================================================

def df_para_json(df: pd.DataFrame, ticker: str) -> Dict:
    """
    Converte DataFrame em estrutura JSON otimizada para gráficos.
    
    Returns:
        {
            "ticker": "PETR4",
            "ultima_atualizacao": "2025-01-02T10:00:00",
            "periodo": {"inicio": "2020-01-02", "fim": "2025-01-02"},
            "dados": [...],
            "estatisticas": {...}
        }
    """
    if df.empty:
        return {}
    
    # Resetar índice para ter 'data' como coluna
    df = df.reset_index()
    df['data'] = df['Date'].dt.strftime('%Y-%m-%d')
    
    # Converter para lista de dicts
    dados = []
    for _, row in df.iterrows():
        ponto = {
            "data": row['data'],
            "abertura": round(float(row['abertura']), 2) if pd.notna(row['abertura']) else None,
            "maxima": round(float(row['maxima']), 2) if pd.notna(row['maxima']) else None,
            "minima": round(float(row['minima']), 2) if pd.notna(row['minima']) else None,
            "fechamento": round(float(row['fechamento']), 2) if pd.notna(row['fechamento']) else None,
            "volume": int(row['volume']) if pd.notna(row['volume']) else 0,
            "mm20": round(float(row['mm20']), 2) if pd.notna(row['mm20']) else None,
            "mm50": round(float(row['mm50']), 2) if pd.notna(row['mm50']) else None,
            "mm200": round(float(row['mm200']), 2) if pd.notna(row['mm200']) else None
        }
        dados.append(ponto)
    
    # Estrutura final
    return {
        "ticker": ticker,
        "ultima_atualizacao": datetime.now().isoformat(),
        "periodo": {
            "inicio": dados[0]['data'] if dados else None,
            "fim": dados[-1]['data'] if dados else None
        },
        "dados": dados,
        "estatisticas": calcular_estatisticas(df)
    }


# ======================================================================================
# PROCESSADOR PRINCIPAL
# ======================================================================================

def processar_ticker(ticker: str, anos: int = ANOS_HISTORICO) -> Tuple[bool, str]:
    """
    Processa um ticker: baixa histórico, calcula médias, salva JSON.
    
    Returns:
        (sucesso, mensagem)
    """
    # Determinar pasta
    if ticker == "IBOV":
        pasta = Path("balancos") / "IBOV"
    else:
        pasta = get_pasta_balanco(ticker)
    
    pasta.mkdir(parents=True, exist_ok=True)
    
    # Baixar histórico
    df = capturar_historico_ticker(ticker, anos)
    
    if df is None or df.empty:
        return False, "sem dados disponíveis"
    
    # Calcular médias móveis
    df = calcular_medias_moveis(df, PERIODOS_MM)
    
    # Converter para JSON
    dados_json = df_para_json(df, ticker)
    
    # Salvar
    arquivo = pasta / "historico_precos_diarios.json"
    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados_json, f, ensure_ascii=False, indent=2)
    
    # Estatísticas para log
    stats = dados_json.get('estatisticas', {})
    total_dias = stats.get('total_dias', 0)
    preco_atual = stats.get('preco_atual', 0)
    variacao = stats.get('variacao_periodo', 0)
    
    msg = f"{total_dias} dias | R$ {preco_atual} | Δ {variacao:+.1f}%"
    
    return True, msg


# ======================================================================================
# PROCESSADOR EM LOTE
# ======================================================================================

def processar_lote(tickers: List[str], anos: int = ANOS_HISTORICO) -> Tuple[int, int]:
    """
    Processa múltiplos tickers em sequência.
    
    Returns:
        (sucessos, erros)
    """
    print(f"\n{'='*70}")
    print(f"📈 CAPTURANDO HISTÓRICO DE PREÇOS ({anos} ANOS)")
    print(f"{'='*70}")
    print(f"Total de tickers: {len(tickers)}")
    print(f"Médias móveis: {', '.join(f'MM{p}' for p in PERIODOS_MM)}")
    print(f"{'='*70}\n")
    
    ok_count = 0
    err_count = 0
    
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] {ticker}...", end=" ")
        
        try:
            ok, msg = processar_ticker(ticker, anos)
            
            if ok:
                ok_count += 1
                print(f"✅ {msg}")
            else:
                err_count += 1
                print(f"⚠️  {msg}")
                
        except Exception as e:
            err_count += 1
            print(f"❌ {type(e).__name__}: {e}")
    
    print(f"\n{'='*70}")
    print(f"RESUMO: ✅ {ok_count} | ❌ {err_count}")
    print(f"{'='*70}\n")
    
    return ok_count, err_count


# ======================================================================================
# CLI
# ======================================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Captura histórico de preços (5 anos) + médias móveis"
    )
    parser.add_argument("--modo", default="quantidade", 
                       choices=["quantidade", "ticker", "lista", "faixa", "todos"])
    parser.add_argument("--quantidade", default="10", type=int)
    parser.add_argument("--ticker", default="")
    parser.add_argument("--lista", default="")
    parser.add_argument("--faixa", default="1-50")
    parser.add_argument("--anos", default=ANOS_HISTORICO, type=int,
                       help="Anos de histórico (padrão: 5)")
    parser.add_argument("--incluir-ibov", action="store_true",
                       help="Incluir IBOVESPA no processamento")
    args = parser.parse_args()
    
    if not HAS_YFINANCE:
        print("❌ Instale yfinance: pip install yfinance")
        return
    
    # Carregar mapeamento
    df = load_mapeamento_b3()
    
    if df.empty:
        print("❌ Não foi possível carregar mapeamento")
        return
    
    # Filtrar linhas válidas
    if 'cnpj' in df.columns:
        df = df[df["cnpj"].notna()].reset_index(drop=True)
    elif 'CNPJ' in df.columns:
        df = df[df["CNPJ"].notna()].reset_index(drop=True)
    else:
        print("⚠️  Coluna CNPJ não encontrada, usando todos os registros")
    
    # Selecionar tickers
    if args.modo == "quantidade":
        df_sel = df.head(args.quantidade)
    elif args.modo == "ticker":
        ticker_upper = args.ticker.upper()
        df_sel = df[df["ticker"].str.upper().str.contains(ticker_upper, case=False, na=False)]
    elif args.modo == "lista":
        tickers_lista = [t.strip().upper() for t in args.lista.split(",") if t.strip()]
        mask = df["ticker"].str.upper().apply(
            lambda x: any(t in x for t in tickers_lista) if pd.notna(x) else False
        )
        df_sel = df[mask]
    elif args.modo == "faixa":
        inicio, fim = map(int, args.faixa.split("-"))
        df_sel = df.iloc[inicio - 1 : fim]
    elif args.modo == "todos":
        df_sel = df
    else:
        df_sel = df.head(10)
    
    # Extrair TODOS os tickers (incluindo classes separadas)
    tickers = []
    for _, row in df_sel.iterrows():
        ticker_str = str(row["ticker"]).upper().strip()
        tickers.extend([t.strip() for t in ticker_str.split(';') if t.strip()])
    
    # Remover duplicatas preservando ordem
    tickers = list(dict.fromkeys(tickers))
    
    # Adicionar IBOVESPA se solicitado
    if args.incluir_ibov and "IBOV" not in tickers:
        tickers.insert(0, "IBOV")
    
    # Processar
    processar_lote(tickers, args.anos)


if __name__ == "__main__":
    main()
