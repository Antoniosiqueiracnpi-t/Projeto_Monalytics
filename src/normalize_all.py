from pathlib import Path
import sys
import traceback

# garante import a partir da raiz do repo
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from padronizar_dre_trimestral_e_anual import padronizar_dre_trimestral_e_anual


def main():
    base = REPO_ROOT / "balancos"
    if not base.exists():
        print("[ERRO] Pasta balancos/ não existe.")
        return

    tickers = [p for p in base.iterdir() if p.is_dir()]
    print(f"Encontradas {len(tickers)} pastas de empresas.")

    gerados = 0
    for pasta in tickers:
        tri = pasta / "dre_consolidado.csv"
        anu = pasta / "dre_anual.csv"
        out = pasta / "dre_padronizado.csv"

        if not tri.exists() or not anu.exists():
            print(f"[SKIP] {pasta.name}: faltam dre_consolidado.csv ou dre_anual.csv")
            continue

        # debug rápido do tamanho (pega caso arquivo vazio/0 bytes)
        print(f"\n[{pasta.name}] tri={tri.stat().st_size} bytes | anu={anu.stat().st_size} bytes")

        try:
            df = padronizar_dre_trimestral_e_anual(
                str(tri),
                str(anu),
                unidade="mil",
                preencher_derivadas=True
            )
            df.to_csv(out, index=False, encoding="utf-8-sig")
            print(f"[OK] {pasta.name}: gerou {out.name} ({df.shape[0]} linhas, {df.shape[1]} cols)")
            gerados += 1
        except Exception as e:
            print(f"[ERRO] {pasta.name}: {repr(e)}")
            traceback.print_exc()

    print(f"\nConcluído. Arquivos gerados: {gerados}")


if __name__ == "__main__":
    main()
