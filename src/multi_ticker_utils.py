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
    Carrega o CSV de mapeamento (consolidado/original), de forma robusta
    (cwd variável no GitHub Actions, repo aninhado, etc), SEM depender de constantes.

    Você pode opcionalmente setar:
        MONALYTICS_MAP_PATH=/caminho/para/seu_mapeamento.csv
    """
    import os
    from pathlib import Path
    import pandas as pd

    def _try_read(p: Path) -> pd.DataFrame | None:
        if not p.exists() or not p.is_file():
            return None

        # tenta separadores/encodings comuns do projeto
        for sep in (";", ","):
            for enc in ("utf-8-sig", "utf-8", "latin1"):
                try:
                    return pd.read_csv(p, sep=sep, encoding=enc)
                except Exception:
                    pass
            try:
                return pd.read_csv(p, sep=sep)
            except Exception:
                pass
        return None

    def _looks_like_mapping(df: pd.DataFrame) -> bool:
        cols = {str(c).strip().lower() for c in df.columns}
        has_ticker = any(k in cols for k in [
            "ticker", "codneg", "codigo_negociacao", "codigo de negociacao", "codnegociacao"
        ])
        has_cnpj = any(k in cols for k in ["cnpj", "cnpj_cia", "cnpj cia", "cnpj_companhia"])
        # em alguns mapas pode não ter CNPJ, mas ao menos ticker precisa existir
        return has_ticker and (has_cnpj or True)

    # 0) Caminho explícito via env (mais seguro no Actions)
    env_path = os.getenv("MONALYTICS_MAP_PATH", "").strip()
    if env_path:
        p = Path(env_path).expanduser().resolve()
        df = _try_read(p)
        if df is not None and _looks_like_mapping(df):
            return df

    # 1) Onde procurar (cwd, src, raiz do repo, etc.)
    src_dir = Path(__file__).resolve().parent
    repo_root = src_dir.parent

    base_dirs = []
    for d in [Path.cwd(), src_dir, repo_root, repo_root.parent]:
        try:
            d = d.resolve()
            if d not in base_dirs:
                base_dirs.append(d)
        except Exception:
            pass

    # 2) Nomes padrão (os mais prováveis no seu projeto)
    preferred_names = [
        "mapeamento_b3_consolidado.csv",
        "mapeamento_final_b3_completo_utf8.csv",
        "mapeamento_final_b3_completo.csv",
        "mapeamento_b3.csv",
        "mapeamento.csv",
        "mapeamento_cnpj_consolidado.csv",
        "mapeamento_cnpj_ticker.csv",
    ]

    tried = []

    # 3) Tentativas diretas (raiz e src)
    for d in base_dirs:
        for name in preferred_names:
            for p in [d / name, d / "src" / name]:
                rp = str(p)
                tried.append(rp)
                df = _try_read(p)
                if df is not None and _looks_like_mapping(df):
                    return df

    # 4) Fallback: procurar qualquer "*mapeamento*.csv" até 2 níveis
    def _walk_depth2(root: Path):
        # root
        yield root
        # depth 1
        try:
            for a in root.iterdir():
                if a.is_dir():
                    yield a
        except Exception:
            return
        # depth 2
        try:
            for a in root.iterdir():
                if a.is_dir():
                    for b in a.iterdir():
                        if b.is_dir():
                            yield b
        except Exception:
            return

    for d in base_dirs:
        for folder in _walk_depth2(d):
            try:
                for p in folder.glob("*mapeamento*.csv"):
                    rp = str(p)
                    tried.append(rp)
                    df = _try_read(p)
                    if df is not None and _looks_like_mapping(df):
                        return df
            except Exception:
                pass

    raise FileNotFoundError(
        "Nenhum arquivo de mapeamento encontrado.\n"
        "Tente colocar o CSV na raiz do repo ou em /src, ou setar MONALYTICS_MAP_PATH.\n"
        "Caminhos tentados (amostra):\n- " + "\n- ".join(tried[:80]) +
        ("\n... (truncado)" if len(tried) > 80 else "")
    )

