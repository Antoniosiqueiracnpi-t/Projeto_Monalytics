"""
CAPTURA DE BALANÇOS - VERSÃO GITHUB ACTIONS
- TRIMESTRAL: ITR (T1..T4 quando existir)  -> *_consolidado.csv
- ANUAL:     DFP (fechamento do exercício) -> *_anual.csv
- DFC pelo método indireto: DFC_MI
- Cache local de ZIP por ano
"""

import pandas as pd
import requests
from pathlib import Path
from datetime import datetime
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

        # Consolidado (con). Se quiser individual: False
        self.consolidado = True

        # Demos (inclui DFC_MI)
        self.demos = ["DRE", "BPA", "BPP", "DFC_MI"]

    # ------------------------- DOWNLOAD / LEITURA -------------------------

    def _download_zip(self, doc: str, ano: int) -> Path:
        """
        doc: 'ITR' ou 'DFP'
        """
        doc = doc.upper().strip()
        if doc not in ("ITR", "DFP"):
            raise ValueError("doc deve ser 'ITR' ou 'DFP'")

        prefix = "itr_cia_aberta" if doc == "ITR" else "dfp_cia_aberta"
        url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/{doc}/DADOS/{prefix}_{ano}.zip"
        dest = self.cache_dir / f"{prefix}_{ano}.zip"

        if dest.exists() and dest.stat().st_size > 0:
            return dest

        r = requests.get(url, timeout=180)
        r.raise_for_status()
        dest.write_bytes(r.content)
        return dest

    def _ler_csv_do_zip(self, zip_path: Path, alvo_csv: str) -> pd.DataFrame | None:
        try:
            with zipfile.ZipFile(zip_path) as z:
                name_map = {n.lower(): n for n in z.namelist()}
                real_name = name_map.get(alvo_csv.lower())
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
        except Exception:
            return None

    def baixar_doc(self, doc: str, ano: int, demo: str, consolidado: bool = True) -> pd.DataFrame | None:
        """
        doc: 'ITR' ou 'DFP'
        demo: 'DRE', 'BPA', 'BPP', 'DFC_MI', ...
        """
        doc = doc.upper().strip()
        demo = demo.upper().strip()

        prefix = "itr_cia_aberta" if doc == "ITR" else "dfp_cia_aberta"
        sufixo = "con" if consolidado else "ind"
        alvo = f"{prefix}_{demo}_{sufixo}_{ano}.csv"

        try:
            zip_path = self._download_zip(doc, ano)
        except Exception as e:
            print(f"[AVISO] Falha ao baixar ZIP {doc} {ano}: {e}")
            return None

        df = self._ler_csv_do_zip(zip_path, alvo)
        return df

    # ------------------------- HELPERS -------------------------

    def _cnpj_digits(self, cnpj: str) -> str:
        return re.sub(r"\D", "", str(cnpj))

    def _filtrar_empresa_ultimo(self, df: pd.DataFrame, cnpj_digits: str) -> pd.DataFrame:
        if df is None or df.empty:
            return df.iloc[0:0]

        if "CNPJ_CIA" not in df.columns:
            return df.iloc[0:0]

        cnpj_col = df["CNPJ_CIA"].astype(str).str.replace(r"\D", "", regex=True)
        df = df[cnpj_col == cnpj_digits].copy()
        if df.empty:
            return df

        if "ORDEM_EXERC" in df.columns:
            ordv = df["ORDEM_EXERC"].astype(str).str.upper()
            df = df[ordv.isin(["ÚLTIMO", "ULTIMO"])].copy()
            if df.empty:
                return df

        if "DT_FIM_EXERC" not in df.columns:
            return df.iloc[0:0]

        df["DT_FIM_EXERC"] = df["DT_FIM_EXERC"].astype(str)
        return df

    def _add_trimestre_itr(self, df: pd.DataFrame) -> pd.DataFrame:
        # ITR: trimestre pelo mês (formato esperado YYYY-MM-DD)
        mes = df["DT_FIM_EXERC"].str[5:7]
        df["TRIMESTRE"] = mes.map({"03": "T1", "06": "T2", "09": "T3", "12": "T4"})
        return df

    def _valor_em_mil(self, df: pd.DataFrame) -> pd.DataFrame:
        if "VL_CONTA" not in df.columns:
            df["VALOR_MIL"] = pd.NA
            return df

        df["VL_CONTA"] = pd.to_numeric(df["VL_CONTA"], errors="coerce")

        # respeita ESCALA_MOEDA quando existir (UNIDADE/MIL)
        if "ESCALA_MOEDA" in df.columns:
            escala = df["ESCALA_MOEDA"].astype(str).str.upper()
            fator = escala.map({"UNIDADE": 1/1000, "MIL": 1}).fillna(1)
            df["VALOR_MIL"] = df["VL_CONTA"] * fator
        else:
            df["VALOR_MIL"] = df["VL_CONTA"] / 1000

        return df

    def _padronizar(self, df: pd.DataFrame, trimestral: bool) -> pd.DataFrame:
        # garante TRIMESTRE na saída
        if trimestral:
            req = ["DT_FIM_EXERC", "TRIMESTRE", "CD_CONTA", "DS_CONTA", "VALOR_MIL"]
            if not all(c in df.columns for c in req):
                return df.iloc[0:0]
            out = df[req].copy()
            out.columns = ["data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"]
            return out

        # anual (DFP): não tem trimestre -> fixamos como T4 para padronizar seu pipeline
        req = ["DT_FIM_EXERC", "CD_CONTA", "DS_CONTA", "VALOR_MIL"]
        if not all(c in df.columns for c in req):
            return df.iloc[0:0]
        out = df[req].copy()
        out["TRIMESTRE"] = "T4"
        out = out[["DT_FIM_EXERC", "TRIMESTRE", "CD_CONTA", "DS_CONTA", "VALOR_MIL"]]
        out.columns = ["data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"]
        return out

    def _consolidar(self, frames: list[pd.DataFrame]) -> pd.DataFrame:
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

        cnpj_digits = self._cnpj_digits(cnpj)

        for demo in self.demos:
            # -------- TRIMESTRAL (ITR) --------
            dados_tri = []
            for ano in range(self.ano_inicio, self.ano_atual + 1):
                df = self.baixar_doc("ITR", ano, demo, consolidado=self.consolidado)
                if df is None or df.empty:
                    continue

                df = self._filtrar_empresa_ultimo(df, cnpj_digits)
                if df.empty:
                    continue

                df = self._add_trimestre_itr(df)
                df = self._valor_em_mil(df)
                out = self._padronizar(df, trimestral=True)
                if out.empty:
                    continue

                dados_tri.append(out)

            if dados_tri:
                tri = self._consolidar(dados_tri)
                arq_tri = pasta / f"{demo.lower()}_consolidado.csv"
                tri.to_csv(arq_tri, index=False, encoding="utf-8-sig")
                tri_info = f"✅ {len(tri)} linhas"
            else:
                tri_info = "❌"

            # -------- ANUAL (DFP) --------
            dados_anual = []
            for ano in range(self.ano_inicio, self.ano_atual + 1):
                df = self.baixar_doc("DFP", ano, demo, consolidado=self.consolidado)
                if df is None or df.empty:
                    continue

                df = self._filtrar_empresa_ultimo(df, cnpj_digits)
                if df.empty:
                    continue

                df = self._valor_em_mil(df)
                out = self._padronizar(df, trimestral=False)
                if out.empty:
                    continue

                dados_anual.append(out)

            if dados_anual:
                anual = self._consolidar(dados_anual)
                arq_anual = pasta / f"{demo.lower()}_anual.csv"
                anual.to_csv(arq_anual, index=False, encoding="utf-8-sig")
                anual_info = f"✅ {len(anual)} linhas"
            else:
                anual_info = "❌"

            print(f"  {demo}: trimestral(ITR) {tri_info} | anual(DFP) {anual_info}")


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--modo", default="quantidade", choices=["quantidade", "ticker", "lista", "faixa"])
    parser.add_argument("--quantidade", default="10")
    parser.add_argument("--ticker", default="")
    parser.add_argument("--lista", default="")
    parser.add_argument("--faixa", default="1-50")

    args = parser.parse_args()
    captura = CapturaBalancos()

    df = pd.read_csv("mapeamento_final_b3_completo_utf8.csv", sep=";", encoding="utf-8-sig")
    df = df[df["cnpj"].notna()].reset_index(drop=True)

    if args.modo == "quantidade":
        limite = int(args.quantidade)
        df_sel = df.head(limite)

    elif args.modo == "ticker":
        df_sel = df[df["ticker"].str.upper() == args.ticker.upper()]

    elif args.modo == "lista":
        tickers = [t.strip().upper() for t in args.lista.split(",") if t.strip()]
        df_sel = df[df["ticker"].str.upper().isin(tickers)]

    elif args.modo == "faixa":
        inicio, fim = map(int, args.faixa.split("-"))
        df_sel = df.iloc[inicio-1:fim]

    else:
        df_sel = df.head(10)

    print(f"\n🚀 Processando {len(df_sel)} empresas (modo: {args.modo})...\n")

    for _, row in df_sel.iterrows():
        try:
            captura.processar_empresa(row["ticker"], row["cnpj"])
        except Exception as e:
            print(f"❌ Erro: {e}")

    print(f"\n✅ Concluído! Dados em: balancos/")
