"""
CAPTURA DE BALANÇOS - VERSÃO GITHUB ACTIONS (corrigida p/ estrutura atual da CVM)
- Baixa 1 ZIP por ano: itr_cia_aberta_{ano}.zip (T1, T2, T3)
- Baixa 1 ZIP por ano: dfp_cia_aberta_{ano}.zip (ANUAL)
- DRE/DFC: Calcula T4 = ANUAL - (T1 + T2 + T3)
- BPA/BPP: Apenas adiciona posição de 31/12 (sem cálculo)
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

        # Classificação de demonstrações
        self.demos_fluxo = ['DRE', 'DFC_MD', 'DFC_MI', 'DVA', 'DMPL']  # Precisa calcular T4
        self.demos_estoque = ['BPA', 'BPP']  # Apenas buscar posição 31/12

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

    def _download_zip_dfp_ano(self, ano: int) -> Path:
        """
        Estrutura atual CVM (DFP): 1 ZIP por ano (dados ANUAIS)
        Ex.: https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_2024.zip
        """
        url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{ano}.zip"
        dest = self.cache_dir / f"dfp_cia_aberta_{ano}.zip"

        if dest.exists() and dest.stat().st_size > 0:
            return dest

        r = requests.get(url, timeout=120)
        r.raise_for_status()
        dest.write_bytes(r.content)
        return dest

    def baixar_cvm(self, ano: int, demo: str, consolidado: bool = True, tipo: str = "ITR") -> pd.DataFrame | None:
        """
        Lê o CSV de uma demonstração (demo) dentro do ZIP anual.
        demo exemplos: 'DRE', 'BPA', 'BPP', 'DFC_MD', 'DFC_MI', 'DMPL', 'DRA', 'DVA'
        tipo: 'ITR' (trimestral) ou 'DFP' (anual)
        """
        try:
            if tipo == "ITR":
                zip_path = self._download_zip_itr_ano(ano)
                prefixo = "itr"
            else:  # DFP
                zip_path = self._download_zip_dfp_ano(ano)
                prefixo = "dfp"
        except Exception as e:
            print(f"[AVISO] Falha ao baixar ZIP {tipo} {ano}: {e}")
            return None

        sufixo = "con" if consolidado else "ind"
        alvo = f"{prefixo}_cia_aberta_{demo}_{sufixo}_{ano}.csv"

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
        demos = ['DRE', 'BPA', 'BPP', 'DFC_MI']

        cnpj_digits = re.sub(r"\D", "", str(cnpj))

        for demo in demos:
            print(f"  {demo}:", end=" ")
            dados_itr = []
            dados_t4 = []

            for ano in range(self.ano_inicio, self.ano_atual + 1):
                # ============================================
                # 1. BAIXAR ITR (T1, T2, T3)
                # ============================================
                df_itr = self.baixar_cvm(ano, demo, consolidado=True, tipo="ITR")
                if df_itr is not None and not df_itr.empty:
                    # Filtro CNPJ robusto (compara só dígitos)
                    if "CNPJ_CIA" in df_itr.columns:
                        df_cnpj_digits = df_itr["CNPJ_CIA"].astype(str).str.replace(r"\D", "", regex=True)
                        df_itr = df_itr[df_cnpj_digits == cnpj_digits].copy()

                    if not df_itr.empty:
                        # Filtrar apenas "ÚLTIMO"
                        if "ORDEM_EXERC" in df_itr.columns:
                            ordv = df_itr["ORDEM_EXERC"].astype(str).str.upper()
                            df_itr = df_itr[ordv.isin(["ÚLTIMO", "ULTIMO"])].copy()

                        if not df_itr.empty and "DT_FIM_EXERC" in df_itr.columns:
                            df_itr["DT_FIM_EXERC"] = df_itr["DT_FIM_EXERC"].astype(str)

                            # Extrair trimestre (baseado no mês)
                            df_itr["TRIMESTRE"] = df_itr["DT_FIM_EXERC"].str[5:7].map({
                                "03": "T1", "06": "T2", "09": "T3", "12": "T4"
                            })

                            # Converter valores
                            if "VL_CONTA" in df_itr.columns:
                                df_itr["VL_CONTA"] = pd.to_numeric(df_itr["VL_CONTA"], errors="coerce")

                                escala = df_itr["ESCALA_MOEDA"].astype(str).str.upper() if "ESCALA_MOEDA" in df_itr.columns else ""
                                fator_mil = escala.map({"UNIDADE": 1/1000, "MIL": 1}).fillna(1)
                                df_itr["VALOR_MIL"] = df_itr["VL_CONTA"] * fator_mil

                                # Selecionar colunas
                                keep = ["DT_FIM_EXERC", "TRIMESTRE", "CD_CONTA", "DS_CONTA", "VALOR_MIL"]
                                if all(c in df_itr.columns for c in keep):
                                    out_itr = df_itr[keep].copy()
                                    out_itr.columns = ["data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"]
                                    dados_itr.append(out_itr)

                # ============================================
                # 2. BAIXAR DFP (ANUAL)
                # ============================================
                df_dfp = self.baixar_cvm(ano, demo, consolidado=True, tipo="DFP")
                if df_dfp is not None and not df_dfp.empty:
                    # Filtro CNPJ
                    if "CNPJ_CIA" in df_dfp.columns:
                        df_cnpj_digits = df_dfp["CNPJ_CIA"].astype(str).str.replace(r"\D", "", regex=True)
                        df_dfp = df_dfp[df_cnpj_digits == cnpj_digits].copy()

                    if not df_dfp.empty:
                        # Filtrar apenas "ÚLTIMO"
                        if "ORDEM_EXERC" in df_dfp.columns:
                            ordv = df_dfp["ORDEM_EXERC"].astype(str).str.upper()
                            df_dfp = df_dfp[ordv.isin(["ÚLTIMO", "ULTIMO"])].copy()

                        if not df_dfp.empty and "DT_FIM_EXERC" in df_dfp.columns:
                            df_dfp["DT_FIM_EXERC"] = df_dfp["DT_FIM_EXERC"].astype(str)

                            # Converter valores
                            if "VL_CONTA" in df_dfp.columns and "CD_CONTA" in df_dfp.columns:
                                df_dfp["VL_CONTA"] = pd.to_numeric(df_dfp["VL_CONTA"], errors="coerce")

                                escala = df_dfp["ESCALA_MOEDA"].astype(str).str.upper() if "ESCALA_MOEDA" in df_dfp.columns else ""
                                fator_mil = escala.map({"UNIDADE": 1/1000, "MIL": 1}).fillna(1)
                                df_dfp["VALOR_MIL"] = df_dfp["VL_CONTA"] * fator_mil

                                # Pegar apenas dados de 31/12
                                df_anual = df_dfp[df_dfp["DT_FIM_EXERC"].str.endswith("-12-31")].copy()

                                if not df_anual.empty:
                                    # ==========================================
                                    # DECISÃO: FLUXO vs ESTOQUE
                                    # ==========================================
                                    
                                    if demo in self.demos_fluxo:
                                        # DEMONSTRAÇÕES DE FLUXO: calcular T4
                                        if dados_itr:
                                            df_itr_ano = pd.concat([d for d in dados_itr if d["data_fim"].str.startswith(str(ano))], ignore_index=True)
                                            
                                            if not df_itr_ano.empty:
                                                soma_t123 = df_itr_ano.groupby(["cd_conta", "ds_conta"])["valor_mil"].sum().reset_index()
                                                soma_t123.columns = ["cd_conta", "ds_conta", "soma_t123"]

                                                # Merge com anual
                                                df_anual_sel = df_anual[["DT_FIM_EXERC", "CD_CONTA", "DS_CONTA", "VALOR_MIL"]].copy()
                                                df_anual_sel.columns = ["data_fim", "cd_conta", "ds_conta", "valor_anual"]

                                                df_t4 = df_anual_sel.merge(soma_t123, on=["cd_conta", "ds_conta"], how="left")
                                                df_t4["soma_t123"] = df_t4["soma_t123"].fillna(0)
                                                df_t4["valor_mil"] = df_t4["valor_anual"] - df_t4["soma_t123"]
                                                df_t4["trimestre"] = "T4"

                                                # Selecionar colunas finais
                                                out_t4 = df_t4[["data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"]].copy()
                                                dados_t4.append(out_t4)
                                    
                                    elif demo in self.demos_estoque:
                                        # BALANÇOS PATRIMONIAIS: apenas adicionar posição 31/12
                                        df_anual_sel = df_anual[["DT_FIM_EXERC", "CD_CONTA", "DS_CONTA", "VALOR_MIL"]].copy()
                                        df_anual_sel.columns = ["data_fim", "cd_conta", "ds_conta", "valor_mil"]
                                        df_anual_sel["trimestre"] = "T4"
                                        
                                        # Selecionar colunas finais
                                        out_t4 = df_anual_sel[["data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"]].copy()
                                        dados_t4.append(out_t4)

            # ============================================
            # 3. CONSOLIDAR TUDO (ITR + T4)
            # ============================================
            if dados_itr or dados_t4:
                todos = dados_itr + dados_t4
                consolidado = pd.concat(todos, ignore_index=True)
                consolidado = consolidado.sort_values(["data_fim", "cd_conta"])
                consolidado = consolidado.drop_duplicates(
                    subset=["data_fim", "trimestre", "cd_conta"],
                    keep="last"
                )
                arquivo = pasta / f"{demo.lower()}_consolidado.csv"
                consolidado.to_csv(arquivo, index=False, encoding="utf-8-sig")
                
                tipo_processamento = "calculado" if demo in self.demos_fluxo else "posição 31/12"
                print(f"✅ {len(consolidado)} linhas (T4 {tipo_processamento})")
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
