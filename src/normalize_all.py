from pathlib import Path
import sys
import traceback

# garante import a partir da raiz do repo
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from padronizar_dre_trimestral_e_anual import padronizar_dre_trimestral_e_anual
from padronizar_bpa_bpp import (
    padronizar_bpa_trimestral_e_anual,
    padronizar_bpp_trimestral_e_anual,
)


def _pick_file(ticker_dir: Path, candidates: list[str], patterns: list[str]) -> Path | None:
    """
    Tenta primeiro por nomes exatos (candidates). Se não achar,
    tenta glob por patterns. Retorna o primeiro encontrado.
    """
    for name in candidates:
        p = ticker_dir / name
        if p.exists():
            return p

    for pat in patterns:
        hits = sorted(ticker_dir.glob(pat))
        if hits:
            return hits[0]

    return None


def main():
    base = REPO_ROOT / "balancos"
    if not base.exists():
        print("[ERRO] Pasta balancos/ não existe.")
        return

    # --- NOVO: mapeamento B3 (setor/segmento) ---
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
            # -------------------- DRE --------------------
            dre_tri = _pick_file(
                tdir,
                candidates=["dre_trimestral.csv", "DRE_trimestral.csv"],
                patterns=["*dre*trimestral*.csv", "*DRE*trimestral*.csv"],
            )
            dre_anu = _pick_file(
                tdir,
                candidates=["dre_anual.csv", "DRE_anual.csv"],
                patterns=["*dre*anual*.csv", "*DRE*anual*.csv", "*dre*dfp*.csv", "*DRE*dfp*.csv"],
            )

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
            bpa_tri = _pick_file(
                tdir,
                candidates=["bpa_trimestral.csv", "BPA_trimestral.csv"],
                patterns=["*bpa*trimestral*.csv", "*BPA*trimestral*.csv"],
            )
            bpa_anu = _pick_file(
                tdir,
                candidates=["bpa_anual.csv", "BPA_anual.csv"],
                patterns=["*bpa*anual*.csv", "*BPA*anual*.csv", "*bpa*dfp*.csv", "*BPA*dfp*.csv"],
            )

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
            bpp_tri = _pick_file(
                tdir,
                candidates=["bpp_trimestral.csv", "BPP_trimestral.csv"],
                patterns=["*bpp*trimestral*.csv", "*BPP*trimestral*.csv"],
            )
            bpp_anu = _pick_file(
                tdir,
                candidates=["bpp_anual.csv", "BPP_anual.csv"],
                patterns=["*bpp*anual*.csv", "*BPP*anual*.csv", "*bpp*dfp*.csv", "*BPP*dfp*.csv"],
            )

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
