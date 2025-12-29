# src/multi_ticker_utils.py
"""
Utilitários para gerenciamento de múltiplos tickers
"""

import re
from pathlib import Path
from typing import Optional
import pandas as pd

# Diretório base do projeto (relativo ao script)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent


def _find_balancos_dir() -> Path:
    """Encontra o diretório 'balancos' em múltiplos locais possíveis."""
    search_paths = [
        Path("balancos"),              # Diretório atual
        SCRIPT_DIR / "balancos",       # src/balancos
        PROJECT_ROOT / "balancos",     # raiz/balancos
    ]
    
    for path in search_paths:
        if path.exists() and path.is_dir():
            return path
    
    # Fallback para o caminho padrão
    return PROJECT_ROOT / "balancos"


def get_ticker_principal(ticker: str) -> str:
    """Retorna o ticker principal (primeiro se houver múltiplos)."""
    ticker_upper = ticker.upper().strip()
    if ';' in ticker_upper:
        return ticker_upper.split(';')[0]
    return ticker_upper


def get_pasta_balanco(ticker: str, pasta_base: Optional[Path] = None) -> Path:
    """
    Retorna o caminho da pasta de balanços do ticker.
    
    Busca variantes do ticker (3, 4, 5, 6, 11) se pasta exata não existir.
    Exemplo: Se buscar BBDC3 e não existir, procura BBDC4, BBDC5, etc.
    """
    if pasta_base is None:
        pasta_base = _find_balancos_dir()
    
    ticker_clean = get_ticker_principal(ticker).upper().strip()
    
    # Tentar pasta exata primeiro
    pasta_exata = pasta_base / ticker_clean
    if pasta_exata.exists():
        return pasta_exata
    
    # Extrair base do ticker (sem número final)
    match = re.match(r'^([A-Z]{4})(\d+)?$', ticker_clean)
    if not match:
        return pasta_exata
    
    base = match.group(1)  # Ex: "BBDC" de "BBDC3"
    
    # Variantes comuns na B3: 3 (ON), 4 (PN), 5 (PNA), 6 (PNB), 11 (Units)
    variantes = ['3', '4', '5', '6', '11', '33', '34']
    
    for var in variantes:
        pasta_variante = pasta_base / f"{base}{var}"
        if pasta_variante.exists():
            return pasta_variante
    
    return pasta_exata


def load_mapeamento_consolidado() -> pd.DataFrame:
    """
    Carrega mapeamento consolidado de empresas.
    
    Busca em múltiplos locais:
    1. Diretório atual
    2. Diretório do script (src/)
    3. Diretório pai do script (raiz do projeto)
    """
    search_paths = [
        Path("."),           # Diretório atual
        SCRIPT_DIR,          # src/
        PROJECT_ROOT,        # raiz do projeto
    ]
    
    filenames = ["mapeamento_cnpj_consolidado.csv", "mapeamento_cnpj_ticker.csv", "mapeamento_consolidado.csv"]
    
    for base_path in search_paths:
        for filename in filenames:
            path = base_path / filename
            if path.exists():
                return pd.read_csv(path)
    
    raise FileNotFoundError(
        f"Nenhum arquivo de mapeamento encontrado. "
        f"Procurado em: {[str(p) for p in search_paths]}"
    )
