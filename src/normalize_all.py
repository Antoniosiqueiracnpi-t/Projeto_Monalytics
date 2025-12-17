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


def _print_file_sizes(pasta: Path, pairs: list[tuple[str, Path, Path]]):
    for label, tri, anu in pairs:
        tri_sz = tri.stat().st_size if tri.exists() else 0
        anu_sz = anu.stat().st_size if anu.exists() else 0
        print(f"  - {label}: tri={tri_sz} bytes | anu={anu_sz} bytes")


def main():
    base = REPO_ROOT / "balancos"
    if not base.exists():
        print("[ERRO] Pasta balancos/ não existe.")
        return

    tickers = [p for p in base.iterdir() if p.is_dir()]
    print(f"Encontradas {len(tickers)} pastas de empresas.")

    gerados = 0

    for pasta in tickers:
        print(f"\n==================== {pasta.name} ====================")

        dre_tri = pasta / "dre_consolidado.csv"
        dre_anu = pasta / "dre_anual.csv"
        dre_out = pasta / "dre_padronizado.csv"

        bpa_tri = pasta / "bpa_consolidado.csv"
        bpa_anu = pasta / "bpa_anual.csv"
        bpa_out = pasta / "bpa_padronizado.csv"

        bpp_tri = pasta / "bpp_consolidado.csv"
        bpp_anu = pasta / "bpp_anual.csv"
        bpp_out = pasta / "bpp_padronizado.csv"

        _print_file_sizes(
            pasta,
            [
                ("DRE", dre_tri, dre_anu),
                ("BPA", bpa_tri, bpa_anu),
                ("BPP", bpp_tri, bpp_anu),
            ],
        )

        # ---------------- DRE ----------------
        if dre_tri.exists() and dre_anu.exists():
            try:
                df = padronizar_dre_trimestral_e_anual(
                    str(dre_tri),
                    str(dre_anu),
                    unidade="mil",
                    preencher_derivadas=True,
                )
                df.to_csv(dre_out, index=False, encoding="utf-8-sig")
                print(f"[OK] {pasta.name}: gerou {dre_out.name} ({df.shape[0]} linhas, {df.shape[1]} cols)")
                gerados += 1
            except Exception as e:
                print(f"[ERRO] {pasta.name} DRE: {repr(e)}")
                traceback.print_exc()
        else:
            print(f"[SKIP] {pasta.name} DRE: faltam dre_consolidado.csv ou dre_anual.csv")

        # ---------------- BPA ----------------
        if bpa_tri.exists() and bpa_anu.exists():
            try:
                df = padronizar_bpa_trimestral_e_anual(
                    str(bpa_tri),
                    str(bpa_anu),
                    unidade="mil",
                    permitir_rollup_descendentes=True,
                )
                df.to_csv(bpa_out, index=False, encoding="utf-8-sig")
                print(f"[OK] {pasta.name}: gerou {bpa_out.name} ({df.shape[0]} linhas, {df.shape[1]} cols)")
                gerados += 1
            except Exception as e:
                print(f"[ERRO] {pasta.name} BPA: {repr(e)}")
                traceback.print_exc()
        else:
            print(f"[SKIP] {pasta.name} BPA: faltam bpa_consolidado.csv ou bpa_anual.csv")

        # ---------------- BPP ----------------
        if bpp_tri.exists() and bpp_anu.exists():
            try:
                df = padronizar_bpp_trimestral_e_anual(
                    str(bpp_tri),
                    str(bpp_anu),
                    unidade="mil",
                    permitir_rollup_descendentes=True,
                )
                df.to_csv(bpp_out, index=False, encoding="utf-8-sig")
                print(f"[OK] {pasta.name}: gerou {bpp_out.name} ({df.shape[0]} linhas, {df.shape[1]} cols)")
                gerados += 1
            except Exception as e:
                print(f"[ERRO] {pasta.name} BPP: {repr(e)}")
                traceback.print_exc()
        else:
            print(f"[SKIP] {pasta.name} BPP: faltam bpp_consolidado.csv ou bpp_anual.csv")

    print(f"\nConcluído. Arquivos gerados: {gerados}")


if __name__ == "__main__":
    main()
