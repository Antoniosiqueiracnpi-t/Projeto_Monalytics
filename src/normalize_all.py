from pathlib import Path
import sys
import traceback
from typing import Optional, Dict, Tuple, List

import pandas as pd


# garante import a partir da raiz do repo
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from padronizar_dre_trimestral_e_anual import padronizar_dre_trimestral_e_anual
from padronizar_bpa_bpp import padronizar_bpa_trimestral_e_anual, padronizar_bpp_trimestral_e_anual


# =========================
# PATCH CIRÚRGICO: FALLBACK
# =========================

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


def _classify_stmt(df: pd.DataFrame) -> Optional[str]:
    """
    Retorna: 'dre', 'bpa', 'bpp' ou None, pelo prefixo dominante de cd_conta.
    """
    if df is None or "cd_conta" not in df.columns:
        return None
    s = df["cd_conta"].astype(str).str.strip()
    n3 = (s.str.startswith("3")).sum()
    n1 = (s.str.startswith("1")).sum()
    n2 = (s.str.startswith("2")).sum()
    mx = max(n1, n2, n3)
    if mx == 0:
        return None
    if mx == n3:
        return "dre"
    if mx == n1:
        return "bpa"
    return "bpp"


def _score_periodicity(df: pd.DataFrame, path: Path, want: str) -> float:
    """
    Score para decidir trimestral vs anual.
    want = 'trimestral' ou 'anual'
    Usa:
      - coluna trimestre (T1/T2/T3 vs T4)
      - data_fim (meses 3/6/9 vs 12)
      - bônus por nome (itr/dfp/anual/trimestral)
    """
    if df is None:
        return 0.0

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

    # evita pegar outputs gerados
    if "padron" in name or "normaliz" in name:
        bonus -= 0.30

    tri_score = 0.0
    anu_score = 0.0

    # trimestre
    if "trimestre" in df.columns:
        t = df["trimestre"].astype(str).str.upper().str.strip()
        if len(t) > 0:
            tri_score += float(t.isin(["T1", "T2", "T3"]).mean())
            anu_score += float((t == "T4").mean())

    # data_fim (mês)
    if "data_fim" in df.columns:
        dt = pd.to_datetime(df["data_fim"], errors="coerce")
        m = dt.dt.month.dropna()
        if not m.empty:
            tri_score += float(m.isin([3, 6, 9]).mean())
            anu_score += float((m == 12).mean())

    if want == "trimestral":
        return tri_score + bonus
    return anu_score + bonus


def _discover_files_by_content(ticker_dir: Path) -> Dict[str, Dict[str, Optional[Path]]]:
    """
    Fallback automático (só é usado quando os nomes originais não existirem).
    Retorna:
      {'dre': {'trimestral': Path, 'anual': Path}, 'bpa': {...}, 'bpp': {...}}
    """
    out = {
        "dre": {"trimestral": None, "anual": None},
        "bpa": {"trimestral": None, "anual": None},
        "bpp": {"trimestral": None, "anual": None},
    }

    # varre CSVs (recursivo) — ignora os já padronizados
    files = [p for p in ticker_dir.rglob("*.csv") if p.is_file()]
    files = [p for p in files if not p.name.lower().endswith("_padronizada.csv")]

    scored: Dict[str, List[Tuple[float, Path, str]]] = {"dre": [], "bpa": [], "bpp": []}

    for f in files:
        dfh = _safe_read_head(f)
        if dfh is None:
            continue
        if not REQUIRED_COLS.issubset(set(dfh.columns)):
            continue

        stmt = _classify_stmt(dfh)
        if stmt not in ("dre", "bpa", "bpp"):
            continue

        s_tri = _score_periodicity(dfh, f, "trimestral")
        s_anu = _score_periodicity(dfh, f, "anual")

        scored[stmt].append((s_tri, f, "trimestral"))
        scored[stmt].append((s_anu, f, "anual"))

    for stmt in ("dre", "bpa", "bpp"):
        tri_list = sorted([x for x in scored[stmt] if x[2] == "trimestral"], key=lambda z: z[0], reverse=True)
        anu_list = sorted([x for x in scored[stmt] if x[2] == "anual"], key=lambda z: z[0], reverse=True)

        tri_best = tri_list[0][1] if tri_list and tri_list[0][0] > 0 else None
        anu_best = anu_list[0][1] if anu_list and anu_list[0][0] > 0 else None

        # evita mesmo arquivo nos dois, se houver alternativa
        if tri_best and anu_best and tri_best.resolve() == anu_best.resolve():
            if len(anu_list) > 1 and anu_list[1][0] > 0:
                anu_best = anu_list[1][1]

        out[stmt]["trimestral"] = tri_best
        out[stmt]["anual"] = anu_best

    return out


def _pick_original_named_files(tdir: Path) -> Dict[str, Dict[str, Optional[Path]]]:
    """
    Mantém o comportamento original: procura pelos nomes padrão.
    Se encontrar, retorna paths.
    Se não encontrar, retorna None para permitir fallback.
    """
    def p(name: str) -> Optional[Path]:
        x = tdir / name
        return x if x.exists() else None

    return {
        "dre": {"trimestral": p("dre_trimestral.csv"), "anual": p("dre_anual.csv")},
        "bpa": {"trimestral": p("bpa_trimestral.csv"), "anual": p("bpa_anual.csv")},
        "bpp": {"trimestral": p("bpp_trimestral.csv"), "anual": p("bpp_anual.csv")},
    }


def _merge_original_with_fallback(original: Dict[str, Dict[str, Optional[Path]]], fallback: Dict[str, Dict[str, Optional[Path]]]) -> Dict[str, Dict[str, Optional[Path]]]:
    """
    Regra cirúrgica:
    - se o original tiver, usa o original (100% igual antes)
    - se faltou, completa com fallback
    """
    out = {"dre": {"trimestral": None, "anual": None}, "bpa": {"trimestral": None, "anual": None}, "bpp": {"trimestral": None, "anual": None}}
    for stmt in out.keys():
        for per in ("trimestral", "anual"):
            out[stmt][per] = original[stmt][per] if original[stmt][per] is not None else fallback[stmt][per]
    return out


# =========================
# MAIN (mantido)
# =========================

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
        print("        Setor/segmento não será usado para ativar exceções (Seguros/Bancos).")

    tickers = [p for p in base.iterdir() if p.is_dir()]
    print(f"Encontradas {len(tickers)} pastas de empresas.")

    gerados = []
    erros = 0

    for tdir in tickers:
        ticker = tdir.name.upper().strip()

        try:
            # 1) tenta o modo original (nomes fixos)
            original = _pick_original_named_files(tdir)

            # 2) se algo faltar, ativa fallback por conteúdo (patch)
            need_fallback = any(
                original[s][p] is None
                for s in ("dre", "bpa", "bpp")
                for p in ("trimestral", "anual")
            )

            fallback = _discover_files_by_content(tdir) if need_fallback else {
                "dre": {"trimestral": None, "anual": None},
                "bpa": {"trimestral": None, "anual": None},
                "bpp": {"trimestral": None, "anual": None},
            }

            picked = _merge_original_with_fallback(original, fallback)

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
                print(f"[{ticker}] DRE: arquivos não encontrados (trimestral/anual). Pulando DRE.")

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
                print(f"[{ticker}] BPA: arquivos não encontrados (trimestral/anual). Pulando BPA.")

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
                print(f"[{ticker}] BPP: arquivos não encontrados (trimestral/anual). Pulando BPP.")

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
