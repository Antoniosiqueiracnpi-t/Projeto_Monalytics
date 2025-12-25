"""
Utilitários para sistema de múltiplos tickers.
Consolida empresas B3 com vários códigos de negociação.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict


# Caminhos padrão
PASTA_BALANCOS = Path("balancos")
CSV_CONSOLIDADO = "mapeamento_b3_consolidado.csv"
CSV_ORIGINAL = "mapeamento_final_b3_completo_utf8.csv"


def load_mapeamento_consolidado() -> pd.DataFrame:
    """
    Carrega CSV de mapeamento (tenta consolidado, fallback para original).
    
    Returns:
        DataFrame com colunas: ticker, empresa, cnpj, setor
    """
    # Tentar CSV consolidado primeiro
    if Path(CSV_CONSOLIDADO).exists():
        try:
            df = pd.read_csv(CSV_CONSOLIDADO, sep=";", encoding="utf-8-sig")
            return df
        except Exception:
            pass
    
    # Fallback para CSV original
    if Path(CSV_ORIGINAL).exists():
        try:
            df = pd.read_csv(CSV_ORIGINAL, sep=";", encoding="utf-8-sig")
            return df
        except Exception:
            pass
    
    # Último fallback: tentar sem especificar encoding
    try:
        df = pd.read_csv(CSV_ORIGINAL, sep=";")
        return df
    except Exception as e:
        raise FileNotFoundError(
            f"Nenhum arquivo de mapeamento encontrado. "
            f"Procurei: {CSV_CONSOLIDADO}, {CSV_ORIGINAL}"
        ) from e


def get_ticker_principal(ticker: str) -> Optional[str]:
    """
    Resolve qualquer ticker para o ticker principal do grupo.
    
    Exemplos:
        ITUB4 → ITUB3
        PETR4 → PETR3
        KLBN11 → KLBN11
    
    Args:
        ticker: Código do ticker (ex: ITUB4, PETR3, KLBN11)
    
    Returns:
        Ticker principal ou None se não encontrado
    """
    try:
        df = load_mapeamento_consolidado()
    except FileNotFoundError:
        return None
    
    ticker_upper = ticker.upper().strip()
    
    # Buscar linha que contém o ticker
    mask = df['ticker'].str.upper().str.contains(
        ticker_upper, 
        case=False, 
        na=False, 
        regex=False
    )
    
    result = df[mask]
    
    if result.empty:
        return None
    
    # Pegar primeiro ticker do grupo (principal)
    ticker_str = str(result.iloc[0]['ticker']).strip()
    principal = ticker_str.split(';')[0] if ';' in ticker_str else ticker_str
    
    return principal.upper()


def get_all_tickers(ticker: str) -> List[str]:
    """
    Retorna lista completa de tickers do grupo.
    
    Exemplos:
        ITUB3 → [ITUB3, ITUB4]
        PETR4 → [PETR3, PETR4]
        KLBN3 → [KLBN11, KLBN3, KLBN4]
    
    Args:
        ticker: Qualquer ticker do grupo
    
    Returns:
        Lista de tickers do grupo (ordenados)
    """
    try:
        df = load_mapeamento_consolidado()
    except FileNotFoundError:
        return [ticker.upper().strip()]
    
    ticker_upper = ticker.upper().strip()
    
    # Buscar linha que contém o ticker
    mask = df['ticker'].str.upper().str.contains(
        ticker_upper, 
        case=False, 
        na=False, 
        regex=False
    )
    
    result = df[mask]
    
    if result.empty:
        return [ticker_upper]
    
    # Pegar string de tickers e separar
    ticker_str = str(result.iloc[0]['ticker']).strip()
    
    if ';' in ticker_str:
        tickers = [t.strip().upper() for t in ticker_str.split(';')]
    else:
        tickers = [ticker_str.upper()]
    
    return sorted(tickers)


def get_pasta_balanco(ticker: str) -> Path:
    """
    Retorna Path da pasta de balanços usando SEMPRE o ticker principal.
    
    Exemplos:
        get_pasta_balanco("ITUB4") → balancos/ITUB3
        get_pasta_balanco("PETR3") → balancos/PETR3
        get_pasta_balanco("KLBN3") → balancos/KLBN11
    
    Args:
        ticker: Qualquer ticker do grupo
    
    Returns:
        Path para pasta de balanços (usa ticker principal)
    """
    principal = get_ticker_principal(ticker)
    
    if principal is None:
        # Fallback: usar o ticker fornecido
        principal = ticker.upper().strip()
    
    return PASTA_BALANCOS / principal


def resolve_ticker(ticker: str) -> Optional[Dict[str, any]]:
    """
    Retorna dados completos da empresa.
    
    Args:
        ticker: Qualquer ticker do grupo
    
    Returns:
        Dict com: ticker_principal, all_tickers, empresa, cnpj, setor
        None se não encontrado
    """
    try:
        df = load_mapeamento_consolidado()
    except FileNotFoundError:
        return None
    
    ticker_upper = ticker.upper().strip()
    
    # Buscar linha que contém o ticker
    mask = df['ticker'].str.upper().str.contains(
        ticker_upper, 
        case=False, 
        na=False, 
        regex=False
    )
    
    result = df[mask]
    
    if result.empty:
        return None
    
    row = result.iloc[0]
    
    # Extrair tickers
    ticker_str = str(row['ticker']).strip()
    if ';' in ticker_str:
        all_tickers = [t.strip().upper() for t in ticker_str.split(';')]
        principal = all_tickers[0]
    else:
        all_tickers = [ticker_str.upper()]
        principal = ticker_str.upper()
    
    return {
        'ticker_principal': principal,
        'all_tickers': sorted(all_tickers),
        'empresa': str(row.get('empresa', '')),
        'cnpj': str(row.get('cnpj', '')),
        'setor': str(row.get('setor', ''))
    }


def is_valid_ticker(ticker: str) -> bool:
    """
    Verifica se ticker existe no mapeamento.
    
    Args:
        ticker: Código do ticker
    
    Returns:
        True se ticker existe
    """
    return get_ticker_principal(ticker) is not None
