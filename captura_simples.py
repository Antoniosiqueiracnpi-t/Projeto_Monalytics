"""
CAPTURA DE BALANÇOS - VERSÃO GITHUB ACTIONS (corrigida p/ estrutura atual da CVM)
- Baixa 1 ZIP por ano: itr_cia_aberta_{ano}.zip
- Lê o CSV dentro do ZIP: itr_cia_aberta_{DEMO}_{con/ind}_{ano}.csv
- Cache local para não baixar o mesmo ZIP várias vezes
"""

import pandas as pd
import requests
from io import BytesIO
import zipfile
from pathlib import Path
from datetime import datetime
import re

class CapturaBalancos:

    def __init__(self):
        self.pasta_balancos = Path("balancos")
        self.pasta_balancos.mkdir(exist_ok=True)

        self.cache_dir = Path(".cvm_cache")
        self.cache_dir.mkdir(exist_ok=True)

        self.ano_inicio = 2015
        self.ano_atual = datetime.now().year

    def _download_zip_itr_ano(self, ano: int) -> Path:
        """
        Estrutura atual CVM (ITR): 1 ZIP por ano
        Ex.: https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_2025.zip
        """
        url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_{ano}.zip"
        dest = self.cache_dir / f"itr_cia_aberta_{ano}.zip"

        if dest.exists() and dest.stat().st_size > 0:
            return dest

        r = requests.get(url, timeout=120)
        r.raise_for_status()
        dest.write_bytes(r.content)
        return dest

    def baixar_cvm(self, ano: int, demo: str, consolidado: bool = True) -> pd.DataFrame | None:
        """
        Lê o CSV de uma demonstração (demo) dentro do ZIP anual.
        demo exemplos: 'DRE', 'BPA', 'BPP', 'DFC_MD', 'DFC_MI', 'DMPL', 'DRA', 'DVA'
        """
        try:
            zip_path = self._download_zip_itr_ano(ano)
        except Exception as e:
            print(f"[AVISO] Falha ao baixar ZIP ITR {ano}: {e}")
            return None

        sufixo = "con" if consolidado else "ind"
        alvo = f"itr_cia_aberta_{demo}_{sufixo}_{ano}.csv"

        try:
            with zipfile.ZipFile(zip_path) as z:
                # match case-insensitive
                name_map = {n.lower(): n for n in z.namelist()}
                real_name = name_map.get(alvo.lower())
                if not real_name:
                    # se não existir essa demo no ano, retorna None
                    return None

                with z.open(real_name) as f:
                    # dtype=str evita problemas com CNPJ/zeros e mantém tudo consistente
                    df = pd.read_csv(
                        f,
                        sep=";",
                        encoding="ISO-8859-1",
                        decimal=",",
                        dtype=str,
                        low_memory=False
                    )
                    return df
        except Exception as e:
            print(f"[AVISO] Falha ao ler {alvo} dentro do ZIP {ano}: {e}")
            return None

    def processar_empresa(self, ticker, cnpj):
        print(f"\n{'='*50}")
        print(f"📊 {ticker} (CNPJ: {cnpj})")

        pasta = self.pasta_balancos / ticker
        pasta.mkdir(exist_ok=True)

        # Suas 4 demonstrações (você pode adicionar outras depois)
        demos = ["DRE", "BPA", "BPP", "DFC_MD"]

        cnpj_digits = re.sub(r"\D", "", str(cnpj))

        for demo in demos:
            print(f"  {demo}:", end=" ")
            dados = []

            for ano in range(self.ano_inicio, self.ano_atual + 1):
                df = self.baixar_cvm(ano, demo, consolidado=True)
                if df is None or df.empty:
                    continue

                # Filtro CNPJ robusto (compara só dígitos)
                if "CNPJ_CIA" not in df.columns:
                    continue
                df_cnpj_digits = df["CNPJ_CIA"].astype(str).str.replace(r"\D", "", regex=True)
                df = df[df_cnpj_digits == cnpj_digits].copy()
                if df.empty:
                    continue

                # Filtrar apenas "ÚLTIMO" (aceita também sem acento, por segurança)
                if "ORDEM_EXERC" in df.columns:
                    ordv = df["ORDEM_EXERC"].astype(str).str.upper()
                    df = df[ordv.isin(["ÚLTIMO", "ULTIMO"])].copy()
                    if df.empty:
                        continue

                # Garantir que DT_FIM_EXERC existe
                if "DT_FIM_EXERC" not in df.columns:
                    continue
                df["DT_FIM_EXERC"] = df["DT_FIM_EXERC"].astype(str)

                # Extrair trimestre (baseado no mês)
                df["TRIMESTRE"] = df["DT_FIM_EXERC"].str[5:7].map({
                    "03": "T1", "06": "T2", "09": "T3", "12": "T4"
                })

                # Converter valores
                if "VL_CONTA" not in df.columns:
                    continue
                df["VL_CONTA"] = pd.to_numeric(df["VL_CONTA"], errors="coerce")

                # OBS: muitos arquivos já vêm com ESCALA_MOEDA = MIL.
                # Se você quer "valor em milhares", não divida por 1000 quando for MIL.
                escala = df["ESCALA_MOEDA"].astype(str).str.upper() if "ESCALA_MOEDA" in df.columns else ""
                fator_mil = escala.map({"UNIDADE": 1/1000, "MIL": 1}).fillna(1)
                df["VALOR_MIL"] = df["VL_CONTA"] * fator_mil

                # Selecionar colunas
                keep = ["DT_FIM_EXERC", "TRIMESTRE", "CD_CONTA", "DS_CONTA", "VALOR_MIL"]
                if not all(c in df.columns for c in keep):
                    continue

                out = df[keep].copy()
                out.columns = ["data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"]

                dados.append(out)

            if dados:
                consolidado = pd.concat(dados, ignore_index=True)
                consolidado = consolidado.sort_values(["data_fim", "cd_conta"])
                consolidado = consolidado.drop_duplicates(
                    subset=["data_fim", "trimestre", "cd_conta"],
                    keep="last"
                )
                arquivo = pasta / f"{demo.lower()}_consolidado.csv"
                consolidado.to_csv(arquivo, index=False, encoding="utf-8-sig")
                print(f"✅ {len(consolidado)} linhas")
            else:
                print("❌")

    def processar_lote(self, limite=10):
        try:
            df = pd.read_csv("mapeamento_final_b3_completo.csv", encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv("mapeamento_final_b3_completo.csv", sep=";", encoding="ISO-8859-1")

        df = df[df["cnpj"].notna()].head(limite)

        print(f"\n🚀 Processando {len(df)} empresas...\n")

        for _, row in df.iterrows():
            try:
                self.processar_empresa(row["ticker"], row["cnpj"])
            except Exception as e:
                print(f"❌ Erro: {e}")

        print(f"\n✅ Concluído! Dados em: balancos/")


if __name__ == "__main__":
    import sys
    captura = CapturaBalancos()
    limite = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    captura.processar_lote(limite=limite)
