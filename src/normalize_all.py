from pathlib import Path
import sys
import traceback
from typing import Optional, Tuple, List, Dict

import pandas as pd


# garante import a partir da raiz do repo
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from padronizar_dre_trimestral_e_anual import padronizar_dre_trimestral_e_anual
from padronizar_bpa_bpp import (
    padronizar_bpa_trimestral_e_anual,
    padronizar_bpp_trimestral_e_anual,
)


REQUIRED_COLS = {"data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"}


def _sniff_sep(path: Path) -> str:
    try:
        sample = path.read_text(encoding="utf-8", errors="replace")[:4096]
    except Exception:
        return ","
    # Heurística simples
    return ";" if sample.count(";") > sample.count(",") else ","


def _safe_read_head(path: Path, nrows: int = 120) -> Optional[pd.DataFrame]:
    sep = _sniff_sep(path)
    try:
        df = pd.read_csv(path, sep=sep, nrows=nrows, encoding="utf-8", engine="python")
        return df
    except Exception:
        return None


def _classify_statement(df: pd.DataFrame) -> Optional[str]:
    """
    Retorna: 'dre', 'bpa', 'bpp' ou None
    """
    if df is None or "cd_conta" not in df.columns:
        return None

    s = df["cd_conta"].astype(str).str.strip()
    # pega prefixo principal
    # Ex.: '3.01', '1.01.02', '2.03'
    n3 = (s.str.startswith("3")).sum()
    n1 = (s.str.startswith("1")).sum()
    n2 = (s.str.startswith("2")).sum()

    # exige alguma evidência mínima
    mx = max(n1, n2, n3)
    if mx == 0:
        return None

    if mx == n3:
        return "dre"
    if mx == n1:
        return "bpa"
    return "bpp"


def _periodicity_score(df: pd.DataFrame) -> Tuple[float, float]:
    """
    Retorna (score_trimestral, score_anual) baseado em data_fim (mês)
    - trimestral: meses 3/6/9
    - anual: mês 12
    """
    if df is None or "data_fim" not in df.columns:
        return (0.0, 0.0)

    dt = pd.to_datetime(df["data_fim"], errors="coerce")
    m = dt.dt.month.dropna()
    if m.empty:
        return (0.0, 0.0)

    tri = (m.isin([3, 6, 9]).sum()) / len(m)
    anu = ((m == 12).sum()) / len(m)
    return (float(tri), float(anu))


def _name_bonus(path: Path, want: str) -> float:
    """
    Bônus por nome, sem depender dele.
    want: 'trimestral' ou 'anual'
    """
    name = path.name.lower()
    bonus = 0.0

    # tipo de arquivo
    if want == "trimestral":
        if "itr" in name:
            bonus += 0.35
        if "trimes" in name:
            bonus += 0.25
        if "3t" in name or "2t" in name or "1t" in name:
            bonus += 0.10
    else:
        if "dfp" in name:
            bonus += 0.35
        if "anual" in name:
            bonus += 0.25
        if "4t" in name:
            bonus += 0.10

    # evita pegar outputs gerados ou arquivos “processados”
    if "padron" in name or "normaliz" in name:
        bonus -= 0.30

    return bonus


def _pick_best_files(ticker_dir: Path) -> Dict[str, Dict[str, Optional[Path]]]:
    """
    Retorna:
      {
        'dre': {'trimestral': Path|None, 'anual': Path|None},
        'bpa': {'trimestral': ..., 'anual': ...},
        'bpp': {'trimestral': ..., 'anual': ...},
      }
    Faz varredura por conteúdo (cd_conta) e por data_fim para anual/trimestral.
    """
    result = {
        "dre": {"trimestral": None, "anual": None},
        "bpa": {"trimestral": None, "anual": None},
        "bpp": {"trimestral": None, "anual": None},
    }

    # busca CSVs (recursivo), ignorando outputs já gerados
    files = [p for p in ticker_dir.rglob("*.csv") if p.is_file()]
    files = [p for p in files if not p.name.lower().endswith("_padronizada.csv")]

    # candidatos com score
    candidates: Dict[str, List[Tuple[float, Path, str]]] = {"dre": [], "bpa": [], "bpp": []}

    for f in files:
        dfh = _safe_read_head(f)
        if dfh is None:
            continue
        if not REQUIRED_COLS.issubset(set(dfh.columns)):
            continue

        st = _classify_statement(dfh)
        if st not in ("dre", "bpa", "bpp"):
            continue

        tri_score, anu_score = _periodicity_score(dfh)

        # Score final: conteúdo + periodicidade + bônus por nome
        score_tri = (1.0 * tri_score) + _name_bonus(f, "trimestral")
        score_anu = (1.0 * anu_score) + _name_bonus(f, "anual")

        candidates[st].append((score_tri, f, "trimestral"))
        candidates[st].append((score_anu, f, "anual"))

    for st in ("dre", "bpa", "bpp"):
        # pega melhor trimestral e melhor anual, evitando escolher o mesmo arquivo pros dois se possível
        tri_list = sorted([c for c in candidates[st] if c[2] == "trimestral"], key=lambda x: x[0], reverse=True)
        anu_list = sorted([c for c in candidates[st] if c[2] == "anual"], key=lambda x: x[0], reverse=True)

        tri_best = tri_list[0][1] if tri_list and tri_list[0][0] > 0 else None
        anu_best = anu_list[0][1] if anu_list and anu_list[0][0] > 0 else None

        # se por acaso escolheu o mesmo arquivo para ambos, tenta o 2º melhor do anual
        if tri_best is not None and anu_best is not None and tri_best.resolve() == anu_best.resolve():
            if len(anu_list) > 1 and anu_list[1][0] > 0:
                anu_best = anu_list[1][1]

        result[st]["trimestral"] = tri_best
        result[st]["anual"] = anu_best

    return result


def main():
    base = REPO_ROOT / "balancos"
    if not base.exists():
        print("[ERRO] Pasta balancos/ não existe.")
        return

    # mapeamento B3 na raiz do repo (opcional)
    b3_map_path = REPO_ROOT / "mapeamento_final_b3_completo_utf8.csv"
    b3_map = str(b3_map_path) if b3_map_path.exists() else None
    if b3_map is None:
        print("[AVISO] mapeamento_final_b3_completo_utf8.csv não encontrado na raiz do repo.")
        print("        Setor/segmento não será usado para ativar exceções (Seguros).")

    tickers = [p for p in base.iterdir() if p.is_dir()]
    print(f"Encontradas {len(tickers)} pastas de empresas.")

    gerados = []
    erros = 0

    for tdir in tickers:
        ticker = tdir.name.upper().strip()

        try:
            picked = _pick_best_files(tdir)

            # -------------------- DRE --------------------
            dre_tri = picked["dre"]["trimestral"]
            dre_anu = picked["dre"]["anual"]
            if dre_tri and dre_anu:
                out_dre = padronizar_dre_trimestral_e_anual(
                    str(dre_tri),
                    str(dre_anu),
                    ticker=ticker,
                    b3_mapping_csv=b3_map,
                )
                dre_out_path = tdir / "dre_padronizada.csv"
                out_dre.to_csv(dre_out_path, index=False)
                gerados.append(str(dre_out_path))
            else:
                print(f"[{ticker}] DRE: não consegui identificar trimestral/anual automaticamente. Pulando DRE.")

            # -------------------- BPA --------------------
            bpa_tri = picked["bpa"]["trimestral"]
            bpa_anu = picked["bpa"]["anual"]
            if bpa_tri and bpa_anu:
                out_bpa = padronizar_bpa_trimestral_e_anual(
                    str(bpa_tri),
                    str(bpa_anu),
                    ticker=ticker,
                    b3_mapping_csv=b3_map,
                )
                bpa_out_path = tdir / "bpa_padronizada.csv"
                out_bpa.to_csv(bpa_out_path, index=False)
                gerados.append(str(bpa_out_path))
            else:
                print(f"[{ticker}] BPA: não consegui identificar trimestral/anual automaticamente. Pulando BPA.")

            # -------------------- BPP --------------------
            bpp_tri = picked["bpp"]["trimestral"]
            bpp_anu = picked["bpp"]["anual"]
            if bpp_tri and bpp_anu:
                out_bpp = padronizar_bpp_trimestral_e_anual(
                    str(bpp_tri),
                    str(bpp_anu),
                    ticker=ticker,
                    b3_mapping_csv=b3_map,
                )
                bpp_out_path = tdir / "bpp_padronizada.csv"
                out_bpp.to_csv(bpp_out_path, index=False)
                gerados.append(str(bpp_out_path))
            else:
                print(f"[{ticker}] BPP: não consegui identificar trimestral/anual automaticamente. Pulando BPP.")

            print(f"[OK] {ticker} finalizado.")

        except Exception as e:
            erros += 1
            print(f"[ERRO] Falha ao processar {ticker}: {e}")
            traceback.print_exc()

    print("\n================== RESUMO ==================")
    print(f"Gerados: {len(gerados)} arquivo(s)")
    print(f"Erros: {erros}")
    if gerados:
        print("Arquivos gerados:")
        for p in gerados:
            print(" -", p)


if __name__ == "__main__":
    main()
