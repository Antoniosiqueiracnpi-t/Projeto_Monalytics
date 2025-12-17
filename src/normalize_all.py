from pathlib import Path
import pandas as pd

# importe sua função pronta
from normalizar_dre import padronizar_dre_trimestral_e_anual  # ajuste o nome do arquivo conforme você salvar

def main():
    base = Path("balancos")
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
