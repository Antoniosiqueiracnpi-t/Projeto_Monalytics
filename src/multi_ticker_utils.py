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
    Carrega CSV de mapeamento (tenta consolidado, fallback para original),
    com busca robusta para GitHub Actions / cwd variável / repo aninhado.

    Returns:
        DataFrame com colunas: ticker, empresa, cnpj, setor (dependendo do CSV)
    """
    import os

    def _try_read_csv(p: Path) -> pd.DataFrame | None:
        if not p.exists() or not p.is_file():
            return None
        # tenta encodings mais comuns do projeto
        for enc in ("utf-8-sig", "utf-8", "latin1"):
            try:
                return pd.read_csv(p, sep=";", encoding=enc)
            except Exception:
                pass
        # fallback final
        try:
            return pd.read_csv(p, sep=";")
        except Exception:
            try:
                return pd.read_csv(p)
            except Exception:
                return None

    # 0) Se o usuário setar um caminho explícito (Actions/ENV), use.
    env_path = os.getenv("MONALYTICS_MAP_PATH", "").strip()
    if env_path:
        p = Path(env_path).expanduser().resolve()
        df = _try_read_csv(p)
        if df is not None:
            return df

    # 1) Diretórios base prováveis (cwd, src, raiz do repo, etc.)
    src_dir = Path(__file__).resolve().parent
    repo_root = src_dir.parent

    base_dirs = []
    for d in [Path.cwd(), src_dir, repo_root, repo_root.parent]:
        try:
            if d not in base_dirs:
                base_dirs.append(d)
        except Exception:
            pass

    # 2) Nomes possíveis (do projeto + legados)
    # (mantém seus nomes reais do repo)
    filenames = [CSV_CONSOLIDADO, CSV_ORIGINAL]

    tried: list[str] = []
    candidates: list[Path] = []

    # 3) Tentativas diretas (raiz e /src)
    for d in base_dirs:
        for fn in filenames:
            candidates.append((d / fn))
            candidates.append((d / "src" / fn))

    # 4) Busca em até 2 níveis (repo aninhado / zip extraído / etc.)
    def _shallow_walk(d: Path, depth: int = 2):
        if depth <= 0:
            return
        try:
            for child in d.iterdir():
                if child.is_dir():
                    name = child.name.lower()
                    if name in {".git", "__pycache__", ".venv", "venv", ".tox", ".mypy_cache"}:
                        continue
                    yield child
                    yield from _shallow_walk(child, depth - 1)
        except Exception:
            return

    for d in base_dirs:
        for sub in _shallow_walk(d, depth=2):
            for fn in filenames:
                candidates.append(sub / fn)

    # 5) (opcional) rastro final: rglob só dentro do repo_root (mais pesado, mas ainda ok)
    # garante achar mesmo se estiver escondido em algum lugar.
    try:
        for fn in filenames:
            for p in repo_root.rglob(fn):
                candidates.append(p)
    except Exception:
        pass

    # 6) Executa: consolidado primeiro, depois original
    # (prioridade por ordem em filenames)
    seen = set()
    for p in candidates:
        rp = str(p.resolve())
        if rp in seen:
            continue
        seen.add(rp)
        tried.append(rp)

        if p.name == CSV_CONSOLIDADO:
            df = _try_read_csv(p)
            if df is not None:
                return df

    for p in candidates:
        rp = str(p.resolve())
        if rp not in seen:
            tried.append(rp)
        if p.name == CSV_ORIGINAL:
            df = _try_read_csv(p)
            if df is not None:
                return df

    raise FileNotFoundError(
        "Nenhum arquivo de mapeamento encontrado.\n"
        f"Arquivos esperados: {CSV_CONSOLIDADO} ou {CSV_ORIGINAL}\n"
        "Caminhos tentados (amostra):\n- " + "\n- ".join(tried[:80]) +
        ("\n... (truncado)" if len(tried) > 80 else "")
    )

