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
    from padronizar_dfc_mi import padronizar_dfc_mi_trimestral_e_anual
except Exception:
    padronizar_dfc_mi_trimestral_e_anual = None  # type: ignore


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
    """
    Score para decidir trimestral vs anual.
    want = 'trimestral' ou 'anual'
    Usa:
      - coluna trimestre (T1/T2/T3 vs T4)
      - data_fim (meses 3/6/9 vs 12)
      - bônus por nome (itr/dfp/anual/trimestral)
    """
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

    # evita pegar outputs gerados
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
    """
    Fallback automático (só é usado quando os nomes originais não existirem).
    Retorna {'trimestral': Path|None, 'anual': Path|None}
    """
    out: Dict[str, Optional[Path]] = {"trimestral": None, "anual": None}

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

    out["trimestral"] = tri_candidates[0][1] if tri_candidates and tri_candidates[0][0] > 0 else None
    out["anual"] = anu_candidates[0][1] if anu_candidates and anu_candidates[0][0] > 0 else None

    # evita usar o mesmo arquivo pros dois, se houver alternativa
    if out["trimestral"] and out["anual"] and out["trimestral"].resolve() == out["anual"].resolve():
        if len(anu_candidates) > 1 and anu_candidates[1][0] > 0:
            out["anual"] = anu_candidates[1][1]

    return out


def _pick_original_named_dfc(tdir: Path) -> Dict[str, Optional[Path]]:
    tri = tdir / "dfc_trimestral.csv"
    anu = tdir / "dfc_anual.csv"
    return {
        "trimestral": tri if tri.exists() else None,
        "anual": anu if anu.exists() else None,
    }


def main():
    if padronizar_dfc_mi_trimestral_e_anual is None:
        print("[AVISO] padronizar_dfc_mi não encontrado.")
        print("        Verifique se src/padronizar_dfc_mi.py existe e se src/ está no sys.path.")
        return

    base = REPO_ROOT / "balancos"
    if not base.exists():
        print("[ERRO] Pasta balancos/ não existe.")
        return

    tickers = [p for p in base.iterdir() if p.is_dir()]
    print(f"Encontradas {len(tickers)} pastas de empresas.")

    gerados: List[str] = []
    erros = 0

    for tdir in tickers:
        ticker = tdir.name.upper().strip()
        try:
            original = _pick_original_named_dfc(tdir)

            need_fallback = (original["trimestral"] is None) or (original["anual"] is None)
            fallback = _discover_dfc_files(tdir) if need_fallback else {"trimestral": None, "anual": None}

            dfc_tri = original["trimestral"] or fallback["trimestral"]
            dfc_anu = original["anual"] or fallback["anual"]

            if dfc_tri and dfc_anu:
                out_dfc = padronizar_dfc_mi_trimestral_e_anual(
                    str(dfc_tri),
                    str(dfc_anu),
                    unidade="mil",
                    permitir_rollup_descendentes=True,
                )
                out_path = tdir / "dfc_padronizada.csv"
                out_dfc.to_csv(out_path, index=False)
                gerados.append(str(out_path))
            else:
                print(f"[{ticker}] DFC: arquivos não encontrados (trimestral/anual). Pulando.")

            print(f"[OK] {ticker} (DFC) finalizado.")

        except Exception as e:
            erros += 1
            print(f"[ERRO] Falha ao processar DFC de {ticker}: {e}")
            traceback.print_exc()

    print("\n================== RESUMO DFC ==================")
    print(f"Gerados: {len(gerados)} arquivo(s)")
    print(f"Erros: {erros}")
    for p in gerados:
        print(" -", p)


if __name__ == "__main__":
    main()
