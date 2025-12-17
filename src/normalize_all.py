from pathlib import Path
import sys

# garante que a raiz do repo esteja no PYTHONPATH (para importar arquivo na raiz)
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

        try:
            df = padronizar_dre_trimestral_e_anual(
                str(tri),
                str(anu),
                itr_is_ytd=True,
                unidade="mil",
                preencher_derivadas=True
            )
            df.to_csv(out, index=False, encoding="utf-8-sig")
            print(f"[OK] {pasta.name}: gerou {out.name} ({df.shape[0]} linhas, {df.shape[1]} cols)")
            gerados += 1
        except Exception as e:
            print(f"[ERRO] {pasta.name}: {e}")

    print(f"Concluído. Arquivos gerados: {gerados}")


if __name__ == "__main__":
    main()
