from pathlib import Path
import sys
import traceback
from typing import Optional, Dict, Tuple, List

import pandas as pd

# garante import a partir da raiz do repo
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"

# PATCH: inclui também src/ no sys.path (aditivo; não interfere no original)
sys.path.insert(0, str(REPO_ROOT))
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

# tenta importar a padronização DFC (se existir)
try:
    from padronizar_dfc_mi import padronizar_dfc_mi
except Exception:
    padronizar_dfc_mi = None  # type: ignore


REQUIRED_COLS = {"data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"}


def _sniff_sep(path: Path) -> str:
    try:
        sample = path.read_text(encoding="utf-8", errors="replace")[:4096]
    except Exception:
        return ","
    return ";" if sample.count(";") > sample.count(",") else ","


def _safe_read_head(path: Path, nrows: int = 200) -> Optional[pd.DataFrame]:
    sep = _sniff_sep(path)
    try:
        return pd.read_csv(path, sep=sep, nrows=nrows, encoding="utf-8", engine="python")
    except Exception:
        return None


def _is_dfc(df: pd.DataFrame) -> bool:
    if df is None or "cd_conta" not in df.columns:
        return False
    s = df["cd_conta"].astype(str).str.strip()
    return (s.str.startswith("6").sum()) > 0


def _score_periodicity(df: pd.DataFrame, path: Path, want: str) -> float:
    name = path.name.lower()
    bonus = 0.0

    if want == "trimestral":
        if "itr" in name:
            bonus += 0.35
        if "trimes" in name:
            bonus += 0.25
    else:
        if "dfp" in name:
            bonus += 0.35
        if "anual" in name:
            bonus += 0.25

    if "dfc" in name:
        bonus += 0.20

    if "padron" in name or "normaliz" in name:
        bonus -= 0.30

    tri_score = 0.0
    anu_score = 0.0

    if "trimestre" in df.columns:
        t = df["trimestre"].astype(str).str.upper().str.strip()
        if len(t) > 0:
            tri_score += float(t.isin(["T1", "T2", "T3"]).mean())
            anu_score += float((t == "T4").mean())

    if "data_fim" in df.columns:
        dt = pd.to_datetime(df["data_fim"], errors="coerce")
        m = dt.dt.month.dropna()
        if not m.empty:
            tri_score += float(m.isin([3, 6, 9]).mean())
            anu_score += float((m == 12).mean())

    return (tri_score + bonus) if want == "trimestral" else (anu_score + bonus)


def _discover_dfc_files(ticker_dir: Path) -> Dict[str, Optional[Path]]:
    out = {"trimestral": None, "anual": None}

    files = [p for p in ticker_dir.rglob("*.csv") if p.is_file()]
    files = [p for p in files if not p.name.lower().endswith("_padronizada.csv")]

    tri_candidates: List[Tuple[float, Path]] = []
    anu_candidates: List[Tuple[float, Path]] = []

    for f in files:
        dfh = _safe_read_head(f)
        if dfh is None:
            continue
        if not REQUIRED_COLS.issubset(set(dfh.columns)):
            continue
        if not _is_dfc(dfh):
            continue

        tri_candidates.append((_score_periodicity(dfh, f, "trimestral"), f))
        anu_candidates.append((_score_periodicity(dfh, f, "anual"), f))

    tri_candidates.sort(key=lambda x: x[0], reverse=True)
    anu_candidates.sort(key=lambda x: x[0], reverse=True)

    out["trime]()
