"""
CAPTURA DE BALANÇOS - VERSÃO GITHUB ACTIONS
- TRIMESTRAL: ITR (T1..T4 quando existir)  -> *_consolidado.csv
- ANUAL:     DFP (fechamento do exercício) -> *_anual.csv
- DFC pelo método indireto: DFC_MI
- Cache local de ZIP por ano

MODOS DE SELEÇÃO:
  --modo quantidade --quantidade 50       : Primeiras N empresas
  --modo ticker --ticker PETR4            : Ticker único
  --modo lista --lista "PETR4,VALE3"      : Lista de tickers
  --modo faixa --faixa "1-50"             : Faixa de posições
"""

import pandas as pd
import requests
from pathlib import Path
from datetime import datetime
import zipfile
import re
import argparse

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

    # ------------------------- SELEÇÃO DE EMPRESAS -------------------------

    def _carregar_mapeamento(self) -> pd.DataFrame:
        """Carrega o arquivo de mapeamento de empresas"""
        try:
            df = pd.read_csv("mapeamento_final_b3_completo.csv", encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv("mapeamento_final_b3_completo.csv", sep=";", encoding="ISO-8859-1")
        
        df = df[df["cnpj"].notna()].copy()
        return df

    def selecionar_por_quantidade(self, quantidade: int) -> pd.DataFrame:
        """Seleciona as primeiras N empresas"""
        df = self._carregar_mapeamento()
        return df.head(quantidade)

    def selecionar_por_ticker(self, ticker: str) -> pd.DataFrame:
        """Seleciona uma empresa específica pelo ticker"""
        df = self._carregar_mapeamento()
        ticker = ticker.upper().strip()
        resultado = df[df["ticker"].str.upper() == ticker]
        
        if resultado.empty:
            print(f"⚠️ Ticker '{ticker}' não encontrado no mapeamento!")
            return pd.DataFrame()
        
        return resultado

    def selecionar_por_lista(self, lista_tickers: str) -> pd.DataFrame:
        """Seleciona múltiplas empresas por lista de tickers"""
        df = self._carregar_mapeamento()
        
        # Limpa e separa os tickers
        tickers = [t.upper().strip() for t in lista_tickers.split(",") if t.strip()]
        
        if not tickers:
            print("⚠️ Nenhum ticker válido na lista!")
            return pd.DataFrame()
        
        # Filtra empresas que estão na lista
        resultado = df[df["ticker"].str.upper().isin(tickers)]
        
        # Verifica quais não foram encontrados
        encontrados = set(resultado["ticker"].str.upper())
        nao_encontrados = set(tickers) - encontrados
        
        if nao_encontrados:
            print(f"⚠️ Tickers não encontrados: {', '.join(sorted(nao_encontrados))}")
        
        return resultado

    def selecionar_por_faixa(self, faixa: str) -> pd.DataFrame:
        """Seleciona empresas por faixa de posições (ex: '1-50', '51-150')"""
        df = self._carregar_mapeamento()
        
        try:
            # Parse da faixa "inicio-fim"
            partes = faixa.split("-")
            if len(partes) != 2:
                raise ValueError("Formato inválido. Use: inicio-fim (ex: 1-50)")
            
            inicio = int(partes[0].strip())
            fim = int(partes[1].strip())
            
            if inicio < 1:
                raise ValueError("Posição inicial deve ser >= 1")
            if fim < inicio:
                raise ValueError("Posição final deve ser >= posição inicial")
            
            # Converte para índices Python (começam em 0)
            idx_inicio = inicio - 1
            idx_fim = fim
            
            total = len(df)
            if idx_inicio >= total:
                print(f"⚠️ Faixa começa além do total de empresas ({total})")
                return pd.DataFrame()
            
            # Limita ao total disponível
            idx_fim = min(idx_fim, total)
            
            resultado = df.iloc[idx_inicio:idx_fim]
            print(f"📊 Selecionando empresas {inicio} a {idx_fim} (total: {len(resultado)})")
            
            return resultado
            
        except ValueError as e:
            print(f"❌ Erro ao processar faixa '{faixa}': {e}")
            return pd.DataFrame()

    def processar_lote(self, modo: str = "quantidade", **kwargs):
        """
        Processa lote de empresas conforme o modo selecionado
        
        Modos disponíveis:
        - quantidade: kwargs={'quantidade': 10}
        - ticker: kwargs={'ticker': 'PETR4'}
        - lista: kwargs={'lista': 'PETR4,VALE3,ITUB4'}
        - faixa: kwargs={'faixa': '1-50'}
        """
        print(f"\n{'='*60}")
        print(f"🔍 MODO DE SELEÇÃO: {modo.upper()}")
        print(f"{'='*60}")
        
        # Seleciona empresas conforme o modo
        if modo == "quantidade":
            quantidade = int(kwargs.get("quantidade", 10))
            df_empresas = self.selecionar_por_quantidade(quantidade)
            
        elif modo == "ticker":
            ticker = kwargs.get("ticker", "")
            if not ticker:
                print("❌ Erro: Ticker não especificado!")
                return
            df_empresas = self.selecionar_por_ticker(ticker)
            
        elif modo == "lista":
            lista = kwargs.get("lista", "")
            if not lista:
                print("❌ Erro: Lista de tickers não especificada!")
                return
            df_empresas = self.selecionar_por_lista(lista)
            
        elif modo == "faixa":
            faixa = kwargs.get("faixa", "1-50")
            df_empresas = self.selecionar_por_faixa(faixa)
            
        else:
            print(f"❌ Modo '{modo}' não reconhecido!")
            print("Modos válidos: quantidade, ticker, lista, faixa")
            return
        
        # Verifica se há empresas para processar
        if df_empresas.empty:
            print("\n❌ Nenhuma empresa selecionada para processar!")
            return
        
        print(f"\n🚀 Processando {len(df_empresas)} empresa(s)...\n")
        
        # Processa cada empresa
        sucesso = 0
        erros = 0
        
        for idx, row in df_empresas.iterrows():
            try:
                self.processar_empresa(row["ticker"], row["cnpj"])
                sucesso += 1
            except Exception as e:
                print(f"❌ Erro em {row['ticker']}: {e}")
                erros += 1
        
        print(f"\n{'='*60}")
        print(f"✅ Processamento concluído!")
        print(f"   Sucesso: {sucesso} | Erros: {erros}")
        print(f"   Dados salvos em: balancos/")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Captura de Balanços da CVM com múltiplos modos de seleção"
    )
    
    parser.add_argument(
        "--modo",
        choices=["quantidade", "ticker", "lista", "faixa"],
        default="quantidade",
        help="Modo de seleção de empresas"
    )
    
    parser.add_argument(
        "--quantidade",
        type=int,
        default=10,
        help="Quantidade de empresas (modo: quantidade)"
    )
    
    parser.add_argument(
        "--ticker",
        type=str,
        default="",
        help="Ticker único (modo: ticker)"
    )
    
    parser.add_argument(
        "--lista",
        type=str,
        default="",
        help="Lista de tickers separados por vírgula (modo: lista)"
    )
    
    parser.add_argument(
        "--faixa",
        type=str,
        default="1-50",
        help="Faixa de posições no formato 'inicio-fim' (modo: faixa)"
    )
    
    args = parser.parse_args()
    
    # Cria instância e processa
    captura = CapturaBalancos()
    
    captura.processar_lote(
        modo=args.modo,
        quantidade=args.quantidade,
        ticker=args.ticker,
        lista=args.lista,
        faixa=args.faixa
    )


if __name__ == "__main__":
    main()
