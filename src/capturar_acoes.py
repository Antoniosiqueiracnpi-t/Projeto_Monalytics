"""
CAPTURA DE HISTÓRICO DE AÇÕES
- Número de ações ON, PN, e Total por trimestre
- Baseado nos arquivos de Composição do Capital Social (ITR e DFP)
- Detecta splits, bonificações e aumentos de capital
- Salva APENAS em formato horizontal: 2022T1, 2022T2, 2022T3...
"""

import pandas as pd
import requests
from pathlib import Path
from datetime import datetime
import zipfile
import re
import argparse
import sys


# ============================================================================
# UTILITÁRIOS MULTI-TICKER (INLINE)
# ============================================================================

def load_mapeamento_consolidado() -> pd.DataFrame:
    """Carrega CSV de mapeamento."""
    csv_consolidado = "mapeamento_b3_consolidado.csv"
    csv_original = "mapeamento_final_b3_completo_utf8.csv"
    
    if Path(csv_consolidado).exists():
        try:
            return pd.read_csv(csv_consolidado, sep=";", encoding="utf-8-sig")
        except Exception:
            pass
    
    if Path(csv_original).exists():
        try:
            return pd.read_csv(csv_original, sep=";", encoding="utf-8-sig")
        except Exception:
            pass
    
    try:
        return pd.read_csv(csv_original, sep=";")
    except Exception as e:
        raise FileNotFoundError("Nenhum arquivo de mapeamento encontrado") from e


def extrair_ticker_inteligente(ticker_str: str) -> str:
    """Prioriza ON (3) > PN (4) > outros."""
    ticker_str = ticker_str.strip().upper()
    
    if ';' not in ticker_str:
        return ticker_str
    
    tickers = [t.strip() for t in ticker_str.split(';') if t.strip()]
    
    if not tickers:
        return ticker_str
    
    # Prioridade: 3 > 4 > outros
    tickers_3 = [t for t in tickers if t.endswith('3')]
    if tickers_3:
        return tickers_3[0]
    
    tickers_4 = [t for t in tickers if t.endswith('4')]
    if tickers_4:
        return tickers_4[0]
    
    return tickers[0]


def get_pasta_balanco(ticker: str) -> Path:
    """Retorna Path da pasta de balanços."""
    ticker_clean = extrair_ticker_inteligente(ticker)
    return Path("balancos") / ticker_clean


def _quarter_order(q: str) -> int:
    """Retorna ordem numérica do trimestre para ordenação."""
    return {"T1": 1, "T2": 2, "T3": 3, "T4": 4}.get(q, 99)


# ============================================================================
# CAPTURADOR DE HISTÓRICO DE AÇÕES
# ============================================================================

class CapturadorAcoes:
    
    def __init__(self):
        self.pasta_balancos = Path("balancos")
        self.pasta_balancos.mkdir(exist_ok=True)
        
        self.cache_dir = Path(".cvm_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        self.ano_inicio = 2015
        self.ano_atual = datetime.now().year
    
    # ----------------------- DOWNLOAD / LEITURA -----------------------
    
    def _download_zip(self, doc: str, ano: int) -> Path:
        """Baixa ZIP de composição do capital social."""
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
        """Lê CSV específico do ZIP."""
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
    
    def baixar_capital_social(self, doc: str, ano: int) -> pd.DataFrame | None:
        """
        Baixa arquivo de Composição do Capital Social.
        
        Arquivo: itr_cia_aberta_cap_social_con_YYYY.csv (ou dfp_...)
        
        Colunas importantes:
        - CNPJ_CIA
        - DT_FIM_EXERC
        - ORDEM_EXERC
        - ESPECIE_ACAO (ON, PN, PNA, PNB, etc)
        - QTD_ACAO
        """
        doc = doc.upper().strip()
        
        prefix = "itr_cia_aberta" if doc == "ITR" else "dfp_cia_aberta"
        alvo = f"{prefix}_cap_social_con_{ano}.csv"
        
        try:
            zip_path = self._download_zip(doc, ano)
        except Exception as e:
            print(f"[AVISO] Falha ao baixar ZIP {doc} {ano}: {e}")
            return None
        
        df = self._ler_csv_do_zip(zip_path, alvo)
        return df
    
    # ----------------------- HELPERS -----------------------
    
    def _cnpj_digits(self, cnpj: str) -> str:
        """Remove formatação do CNPJ."""
        return re.sub(r"\D", "", str(cnpj))
    
    def _filtrar_empresa_ultimo(self, df: pd.DataFrame, cnpj_digits: str) -> pd.DataFrame:
        """Filtra dados da empresa e ORDEM_EXERC = ÚLTIMO."""
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
        
        return df
    
    def _add_trimestre_itr(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adiciona coluna TRIMESTRE baseado no mês."""
        if "DT_FIM_EXERC" not in df.columns:
            return df
        
        df["DT_FIM_EXERC"] = df["DT_FIM_EXERC"].astype(str)
        mes = df["DT_FIM_EXERC"].str[5:7]
        df["TRIMESTRE"] = mes.map({"03": "T1", "06": "T2", "09": "T3", "12": "T4"})
        return df
    
    def _processar_acoes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processa dados de ações para formato padronizado.
        
        Agrupa por:
        - Data
        - Trimestre
        - Espécie de ação (ON, PN, PNA, etc)
        
        Retorna:
        - data_fim
        - trimestre
        - especie (ON, PN, TOTAL)
        - quantidade
        """
        if df.empty:
            return df
        
        # Garantir colunas necessárias
        req = ["DT_FIM_EXERC", "TRIMESTRE", "ESPECIE_ACAO", "QTD_ACAO"]
        if not all(c in df.columns for c in req):
            return pd.DataFrame(columns=["data_fim", "trimestre", "especie", "quantidade"])
        
        # Converter quantidade para numérico
        df["QTD_ACAO"] = pd.to_numeric(df["QTD_ACAO"], errors="coerce")
        
        # Agrupar por data, trimestre e espécie
        grouped = df.groupby(
            ["DT_FIM_EXERC", "TRIMESTRE", "ESPECIE_ACAO"], 
            as_index=False
        )["QTD_ACAO"].sum()
        
        grouped.columns = ["data_fim", "trimestre", "especie", "quantidade"]
        
        return grouped
    
    def _calcular_total(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adiciona linha de TOTAL para cada período.
        """
        if df.empty:
            return df
        
        # Calcular total por período
        totals = df.groupby(["data_fim", "trimestre"], as_index=False)["quantidade"].sum()
        totals["especie"] = "TOTAL"
        
        # Concatenar com dados originais
        result = pd.concat([df, totals], ignore_index=True)
        
        # Ordenar
        result = result.sort_values(["data_fim", "especie"])
        
        return result
    
    def _build_horizontal(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Constrói tabela horizontal (períodos como colunas).
        
        Formato:
        | Espécie_Acao | 2022T1 | 2022T2 | 2022T3 | 2022T4 | 2023T1 | ...
        | ON           | 1000   | 1000   | 1200   | 1200   | 1300   | ...
        | PN           | 5000   | 5000   | 5500   | 5500   | 6000   | ...
        | TOTAL        | 6000   | 6000   | 6700   | 6700   | 7300   | ...
        """
        if df.empty:
            return pd.DataFrame(columns=["Espécie_Acao"])
        
        # Criar coluna de período (ano + trimestre) no formato 2022T1
        df["ano"] = pd.to_datetime(df["data_fim"], errors="coerce").dt.year
        df["periodo"] = df["ano"].astype(str) + df["trimestre"]
        
        # Pivotar
        pivot = df.pivot_table(
            index="especie",
            columns="periodo",
            values="quantidade",
            aggfunc="first"
        )
        
        # Ordenar colunas cronologicamente (2022T1, 2022T2, 2022T3, 2022T4, 2023T1...)
        def sort_key(p):
            try:
                ano = int(p[:4])
                trim = _quarter_order(p[4:])
                return (ano, trim)
            except:
                return (9999, 99)
        
        cols = sorted(pivot.columns, key=sort_key)
        pivot = pivot[cols]
        
        # Ordenar linhas: ON, PN, PNA, ..., TOTAL
        especies_ordem = ["ON", "PN", "PNA", "PNB", "PNC", "PND", "TOTAL"]
        especies_presentes = [e for e in especies_ordem if e in pivot.index]
        outras = [e for e in pivot.index if e not in especies_ordem]
        
        ordem_final = especies_presentes + sorted(outras)
        pivot = pivot.reindex(ordem_final)
        
        # Converter para inteiros (sem casas decimais)
        pivot = pivot.fillna(0).astype(int)
        
        # Resetar índice e renomear primeira coluna
        pivot.insert(0, "Espécie_Acao", pivot.index)
        pivot = pivot.reset_index(drop=True)
        
        return pivot
    
    # ----------------------- PROCESSAMENTO -----------------------
    
    def processar_empresa(self, ticker: str, cnpj: str):
        """
        Captura histórico de ações de uma empresa.
        Salva APENAS em formato horizontal.
        """
        print(f"\n{'='*50}")
        print(f"📊 {ticker} (CNPJ: {cnpj})")
        
        pasta = get_pasta_balanco(ticker)
        pasta.mkdir(exist_ok=True)
        
        cnpj_digits = self._cnpj_digits(cnpj)
        
        # -------- TRIMESTRAL (ITR) --------
        dados_tri = []
        for ano in range(self.ano_inicio, self.ano_atual + 1):
            df = self.baixar_capital_social("ITR", ano)
            if df is None or df.empty:
                continue
            
            df = self._filtrar_empresa_ultimo(df, cnpj_digits)
            if df.empty:
                continue
            
            df = self._add_trimestre_itr(df)
            out = self._processar_acoes(df)
            if out.empty:
                continue
            
            dados_tri.append(out)
        
        # -------- ANUAL (DFP) --------
        dados_anual = []
        for ano in range(self.ano_inicio, self.ano_atual + 1):
            df = self.baixar_capital_social("DFP", ano)
            if df is None or df.empty:
                continue
            
            df = self._filtrar_empresa_ultimo(df, cnpj_digits)
            if df.empty:
                continue
            
            df["TRIMESTRE"] = "T4"
            df["DT_FIM_EXERC"] = df.get("DT_FIM_EXERC", "").astype(str)
            out = self._processar_acoes(df)
            if out.empty:
                continue
            
            dados_anual.append(out)
        
        # Consolidar
        if dados_tri or dados_anual:
            all_data = dados_tri + dados_anual
            consolidado = pd.concat(all_data, ignore_index=True)
            
            # Remover duplicatas (priorizar DFP sobre ITR para T4)
            consolidado = consolidado.sort_values(["data_fim", "trimestre", "especie"])
            consolidado = consolidado.drop_duplicates(
                subset=["data_fim", "trimestre", "especie"],
                keep="last"
            )
            
            # Adicionar total
            consolidado = self._calcular_total(consolidado)
            
            # Construir formato horizontal
            horizontal = self._build_horizontal(consolidado)
            
            # Salvar APENAS formato horizontal
            arq_horizontal = pasta / "acoes_historico.csv"
            horizontal.to_csv(arq_horizontal, index=False, encoding="utf-8-sig")
            
            # Estatísticas
            n_periodos = len([c for c in horizontal.columns if c != "Espécie_Acao"])
            especies = [e for e in horizontal["Espécie_Acao"].values if e != "TOTAL"]
            
            print(f"  ✅ Períodos: {n_periodos}")
            print(f"  ✅ Espécies: {', '.join(especies)}")
            print(f"  ✅ Arquivo: acoes_historico.csv")
        else:
            print(f"  ❌ Nenhum dado de ações encontrado")
    
    def processar_lote(self, df_sel: pd.DataFrame):
        """Processa lote de empresas."""
        print(f"\n🚀 Processando {len(df_sel)} empresas...\n")
        
        ok_count = 0
        err_count = 0
        
        for _, row in df_sel.iterrows():
            try:
                ticker_str = str(row["ticker"]).strip().upper()
                ticker_cvm = extrair_ticker_inteligente(ticker_str)
                
                self.processar_empresa(ticker_cvm, row["cnpj"])
                ok_count += 1
            except Exception as e:
                err_count += 1
                ticker_str = str(row.get("ticker", "UNKNOWN")).strip().upper()
                ticker_display = extrair_ticker_inteligente(ticker_str)
                print(f"❌ {ticker_display}: erro ({type(e).__name__}: {e})")
        
        print(f"\n{'='*70}")
        print(f"Finalizado: OK={ok_count} | ERRO={err_count}")
        print(f"{'='*70}\n")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Captura histórico de número de ações (composição do capital social)"
    )
    parser.add_argument(
        "--modo",
        choices=["quantidade", "ticker", "lista", "faixa"],
        default="quantidade",
        help="Modo de seleção",
    )
    parser.add_argument("--quantidade", default="10", help="Quantidade de empresas")
    parser.add_argument("--ticker", default="", help="Ticker específico")
    parser.add_argument("--lista", default="", help="Lista de tickers")
    parser.add_argument("--faixa", default="1-50", help="Faixa de linhas")
    args = parser.parse_args()
    
    # Carregar mapeamento
    df = load_mapeamento_consolidado()
    df = df[df["cnpj"].notna()].reset_index(drop=True)
    
    # Seleção
    if args.modo == "quantidade":
        df_sel = df.head(int(args.quantidade))
    elif args.modo == "ticker":
        df_sel = df[df["ticker"].str.upper().str.contains(
            args.ticker.upper(), case=False, na=False, regex=False
        )]
    elif args.modo == "lista":
        tickers = [t.strip().upper() for t in args.lista.split(",") if t.strip()]
        mask = df["ticker"].str.upper().apply(
            lambda x: any(t in x for t in tickers) if pd.notna(x) else False
        )
        df_sel = df[mask]
    elif args.modo == "faixa":
        inicio, fim = map(int, args.faixa.split("-"))
        df_sel = df.iloc[inicio - 1: fim]
    else:
        df_sel = df.head(10)
    
    # Exibir info
    print(f"\n{'='*70}")
    print(f">>> JOB: CAPTURAR HISTÓRICO DE AÇÕES <<<")
    print(f"{'='*70}")
    print(f"Modo: {args.modo}")
    print(f"Empresas: {len(df_sel)}")
    print(f"Período: 2015 - {datetime.now().year}")
    print(f"Formato: Horizontal (2022T1, 2022T2, 2022T3, ...)")
    print(f"Saída: balancos/<TICKER>/acoes_historico.csv")
    print(f"{'='*70}\n")
    
    # Processar
    capturador = CapturadorAcoes()
    capturador.processar_lote(df_sel)


if __name__ == "__main__":
    main()
