from pathlib import Path
import sys
import traceback
import argparse
from typing import Optional, Dict, Tuple, List

import pandas as pd

# garante import a partir da raiz do repo
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from padronizar_dre_trimestral_e_anual import padronizar_dre_trimestral_e_anual

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


def _is_dre(df: pd.DataFrame) -> bool:
    if df is None or "cd_conta" not in df.columns:
        return False
    s = df["cd_conta"].astype(str).str.strip()
    return (s.str.startswith("3").sum()) > 0


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


def _discover_dre_files(ticker_dir: Path) -> Dict[str, Optional[Path]]:
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
        if not _is_dre(dfh):
            continue

        tri_candidates.append((_score_periodicity(dfh, f, "trimestral"), f))
        anu_candidates.append((_score_periodicity(dfh, f, "anual"), f))

    tri_candidates.sort(key=lambda x: x[0], reverse=True)
    anu_candidates.sort(key=lambda x: x[0], reverse=True)

    out["trimestral"] = tri_candidates[0][1] if tri_candidates and tri_candidates[0][0] > 0 else None
    out["anual"] = anu_candidates[0][1] if anu_candidates and anu_candidates[0][0] > 0 else None

    # evita escolher o mesmo arquivo pros dois se possível
    if out["trimestral"] and out["anual"] and out["trimestral"].resolve() == out["anual"].resolve():
        if len(anu_candidates) > 1 and anu_candidates[1][0] > 0:
            out["anual"] = anu_candidates[1][1]

    return out


def _pick_original_named_dre(tdir: Path) -> Dict[str, Optional[Path]]:
    tri = tdir / "dre_trimestral.csv"
    anu = tdir / "dre_anual.csv"
    return {
        "trimestral": tri if tri.exists() else None,
        "anual": anu if anu.exists() else None,
    }


def _filtrar_tickers(all_tickers: List[Path], modo: str, quantidade: str, ticker: str, lista: str, faixa: str) -> List[Path]:
    """
    Filtra a lista de tickers baseado no modo de seleção.
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
        return [t for t in all_tickers if t.name.upper() == ticker_upper]
    
    elif modo == "lista":
        if not lista:
            print("[AVISO] Lista vazia, processando todos")
            return all_tickers
        tickers_list = [t.strip().upper() for t in lista.split(",") if t.strip()]
        return [t for t in all_tickers if t.name.upper() in tickers_list]
    
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
    parser = argparse.ArgumentParser(description="Normalizar DRE")
    parser.add_argument("--modo", default="quantidade", choices=["quantidade", "ticker", "lista", "faixa"])
    parser.add_argument("--quantidade", default="10")
    parser.add_argument("--ticker", default="")
    parser.add_argument("--lista", default="")
    parser.add_argument("--faixa", default="1-50")
    args = parser.parse_args()

    base = REPO_ROOT / "balancos"
    if not base.exists():
        print("[ERRO] Pasta balancos/ não existe.")
        return

    b3_map_path = REPO_ROOT / "mapeamento_final_b3_completo_utf8.csv"
    b3_map = str(b3_map_path) if b3_map_path.exists() else None

    all_tickers = sorted([p for p in base.iterdir() if p.is_dir()])
    print(f"Encontradas {len(all_tickers)} pastas de empresas.")

    # Aplicar filtro
    tickers = _filtrar_tickers(all_tickers, args.modo, args.quantidade, args.ticker, args.lista, args.faixa)
    print(f"Selecionadas {len(tickers)} empresas para processar (modo: {args.modo}).")

    gerados = []
    erros = 0

    for tdir in tickers:
        ticker = tdir.name.upper().strip()
        try:
            original = _pick_original_named_dre(tdir)
            need_fallback = (original["trimestral"] is None or original["anual"] is None)
            fallback = _discover_dre_files(tdir) if need_fallback else {"trimestral": None, "anual": None}

            dre_tri = original["trimestral"] or fallback["trimestral"]
            dre_anu = original["anual"] or fallback["anual"]

            if dre_tri and dre_anu:
                out_dre = padronizar_dre_trimestral_e_anual(
                    str(dre_tri),
                    str(dre_anu),
                    ticker=ticker,
                    b3_mapping_csv=b3_map,
                )
                out_path = tdir / "dre_padronizada.csv"
                out_dre.to_csv(out_path, index=False)
                gerados.append(str(out_path))
            else:
                print(f"[{ticker}] DRE: arquivos não encontrados (trimestral/anual). Pulando.")

            print(f"[OK] {ticker} (DRE) finalizado.")
        except Exception as e:
            erros += 1
            print(f"[ERRO] Falha ao processar DRE de {ticker}: {e}")
            traceback.print_exc()

    print("\n================== RESUMO DRE ==================")
    print(f"Gerados: {len(gerados)} arquivo(s)")
    print(f"Erros: {erros}")
    for p in gerados:
        print(" -", p)


if __name__ == "__main__":
    main()
