"""
CAPTURA DE BALANÇOS - VERSÃO GITHUB ACTIONS
- ITR trimestral (T1..T4) + ANUAL (apenas T4) no mesmo run
- Usa DFC pelo MÉTODO INDIRETO: DFC_MI
- Baixa 1 ZIP por ano: itr_cia_aberta_{ano}.zip
"""

import pandas as pd
import requests
from pathlib import Path
from datetime import datetime
from io import BytesIO
import zipfile
import re

class CapturaBalancos:

    def __init__(self):
        self.pasta_balancos = Path("balancos")
        self.pasta_balancos.mkdir(exist_ok=True)

        self.cache_dir = Path(".cvm_cache")
        self.cache_dir.mkdir(exist_ok=True)

        self.ano_inicio = 2015
        self.ano_atual = datetime.now().year

        # Consolidado (con). Se quiser individual, troque para False
        self.consolidado = True

    # ------------------------- DOWNLOAD / LEITURA CVM -------------------------

    def _download_zip_itr_ano(self, ano: int) -> Path:
        url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_{ano}.zip"
        dest = self.cache_dir / f"itr_cia_aberta_{ano}.zip"

        if dest.exists() and dest.stat().st_size > 0:
            return dest

        r = requests.get(url, timeout=180)
        r.raise_for_status()
        dest.write_bytes(r.content)
        return dest

    def baixar_cvm(self, ano: int, demo: str, consolidado: bool = True) -> pd.DataFrame | None:
        """
        demo exemplos: DRE, BPA, BPP, DFC_MI, DFC_MD, DRA, DMPL, DVA...
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
                    return None

                with z.open(real_name) as f:
                    return pd.read_csv(
                        f,
                        sep=";",
                        encoding="ISO-8859-1",
                        decimal=",",
                        dtype=str,
                        low_memory=False
                    )
        except Exception as e:
            print(f"[AVISO] Falha ao ler {alvo} dentro do ZIP {ano}: {e}")
            return None

    # ------------------------- HELPERS -------------------------

    def _normalizar_cnpj(self, cnpj: str) -> str:
        return re.sub(r"\D", "", str(cnpj))

    def _filtrar_empresa_e_exercicio(self, df: pd.DataFrame, cnpj_digits: str) -> pd.DataFrame:
        # CNPJ
        if "CNPJ_CIA" not in df.columns:
            return df.iloc[0:0]
        df_cnpj_digits = df["CNPJ_CIA"].astype(str).str.replace(r"\D", "", regex=True)
        df = df[df_cnpj_digits == cnpj_digits].copy()
        if df.empty:
            return df

        # ÚLTIMO exercício
        if "ORDEM_EXERC" in df.columns:
            ordv = df["ORDEM_EXERC"].astype(str).str.upper()
            df = df[ordv.isin(["ÚLTIMO", "ULTIMO"])].copy()
            if df.empty:
                return df

        # Datas
        if "DT_FIM_EXERC" not in df.columns:
            return df.iloc[0:0]
        df["DT_FIM_EXERC"] = df["DT_FIM_EXERC"].astype(str)

        # Trimestre pelo mês
        mes = df["DT_FIM_EXERC"].str[5:7]
        df["TRIMESTRE"] = mes.map({"03": "T1", "06": "T2", "09": "T3", "12": "T4"})

        return df

    def _calcular_valor_mil(self, df: pd.DataFrame) -> pd.DataFrame:
        if "VL_CONTA" not in df.columns:
            df["VALOR_MIL"] = pd.NA
            return df

        df["VL_CONTA"] = pd.to_numeric(df["VL_CONTA"], errors="coerce")

        # Respeita ESCALA_MOEDA (muito comum ser MIL)
        if "ESCALA_MOEDA" in df.columns:
            escala = df["ESCALA_MOEDA"].astype(str).str.upper()
            fator = escala.map({"UNIDADE": 1/1000, "MIL": 1}).fillna(1)
            df["VALOR_MIL"] = df["VL_CONTA"] * fator
        else:
            # fallback: assume UNIDADE e converte para mil
            df["VALOR_MIL"] = df["VL_CONTA"] / 1000

        return df

    def _padronizar_saida(self, df: pd.DataFrame) -> pd.DataFrame:
        required = ["DT_FIM_EXERC", "TRIMESTRE", "CD_CONTA", "DS_CONTA", "VALOR_MIL"]
        if not all(c in df.columns for c in required):
            return df.iloc[0:0]

        out = df[required].copy()
        out.columns = ["data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"]
        return out

    def _consolidar_e_limpar(self, frames: list[pd.DataFrame]) -> pd.DataFrame:
        consolidado = pd.concat(frames, ignore_index=True)
        consolidado = consolidado.sort_values(["data_fim", "cd_conta"])
        consolidado = consolidado.drop_duplicates(
            subset=["data_fim", "trimestre", "cd_conta"],
            keep="last"
        )
        return consolidado

    # ------------------------- PROCESSAMENTO -------------------------

    def processar_empresa(self, ticker: str, cnpj: str):
        print(f"\n{'='*50}")
        print(f"📊 {ticker} (CNPJ: {cnpj})")

        pasta = self.pasta_balancos / ticker
        pasta.mkdir(exist_ok=True)

        # Trimestral (mantém como estava) + DFC método indireto
        demos = ["DRE", "BPA", "BPP", "DFC_MI"]

        cnpj_digits = self._normalizar_cnpj(cnpj)

        for demo in demos:
            print(f"  {demo}:", end=" ")
            dados_trimestral = []

            for ano in range(self.ano_inicio, self.ano_atual + 1):
                df = self.baixar_cvm(ano, demo, consolidado=self.consolidado)
                if df is None or df.empty:
                    continue

                df = self._filtrar_empresa_e_exercicio(df, cnpj_digits)
                if df.empty:
                    continue

                df = self._calcular_valor_mil(df)
                out = self._padronizar_saida(df)
                if out.empty:
                    continue

                dados_trimestral.append(out)

            if not dados_trimestral:
                print("❌")
                continue

            # 1) Salvar TRIMESTRAL (T1..T4 juntos) - como estava
            tri = self._consolidar_e_limpar(dados_trimestral)
            arq_tri = pasta / f"{demo.lower()}_consolidado.csv"
            tri.to_csv(arq_tri, index=False, encoding="utf-8-sig")

            # 2) Salvar ANUAL (apenas T4) - adicional
            anual = tri[tri["trimestre"] == "T4"].copy()
            arq_anual = pasta / f"{demo.lower()}_anual.csv"
            anual.to_csv(arq_anual, index=False, encoding="utf-8-sig")

            print(f"✅ {len(tri)} linhas | anual(T4): {len(anual)}")

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
