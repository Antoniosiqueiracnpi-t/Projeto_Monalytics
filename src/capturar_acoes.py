"""
CAPTURA DE HISTÓRICO DE AÇÕES - FORMULÁRIO DE REFERÊNCIA (FRE)
- Usa arquivo: fre_cia_aberta_capital_social_AAAA.csv
- Fonte: Formulário de Referência da CVM
- Formato de saída: Horizontal (2010T4, 2011T4, 2012T4...)
- Arquivo: balancos/<TICKER>/acoes_historico.csv
"""

import pandas as pd
import requests
from pathlib import Path
from datetime import datetime
import zipfile
import re
import argparse


# ============================================================================
# UTILITÁRIOS MULTI-TICKER
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
    """Retorna ordem numérica do trimestre."""
    return {"T4": 4}.get(q, 99)


# ============================================================================
# CAPTURADOR DE HISTÓRICO DE AÇÕES
# ============================================================================

class CapturadorAcoes:
    
    def __init__(self):
        self.pasta_balancos = Path("balancos")
        self.pasta_balancos.mkdir(exist_ok=True)
        
        self.cache_dir = Path(".cvm_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        self.ano_inicio = 2010
        self.ano_atual = datetime.now().year
    
    # ----------------------- DOWNLOAD / LEITURA -----------------------
    
    def _download_fre_zip(self, ano: int) -> Path:
        """Baixa ZIP do Formulário de Referência."""
        url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/fre_cia_aberta_{ano}.zip"
        dest = self.cache_dir / f"fre_cia_aberta_{ano}.zip"
        
        if dest.exists() and dest.stat().st_size > 0:
            return dest
        
        try:
            r = requests.get(url, timeout=180)
            r.raise_for_status()
            dest.write_bytes(r.content)
            return dest
        except Exception as e:
            print(f"[AVISO] Falha ao baixar FRE {ano}: {e}")
            return None
    
    def _ler_capital_social(self, zip_path: Path, ano: int) -> pd.DataFrame | None:
        """Lê arquivo fre_cia_aberta_capital_social do ZIP."""
        if zip_path is None or not zip_path.exists():
            return None
        
        alvo = f"fre_cia_aberta_capital_social_{ano}.csv"
        
        try:
            with zipfile.ZipFile(zip_path) as z:
                name_map = {n.lower(): n for n in z.namelist()}
                real_name = name_map.get(alvo.lower())
                
                if not real_name:
                    return None
                
                with z.open(real_name) as f:
                    df = pd.read_csv(
                        f,
                        sep=";",
                        encoding="ISO-8859-1",
                        dtype=str,
                        low_memory=False
                    )
                    return df
        except Exception as e:
            print(f"[AVISO] Erro ao ler {alvo}: {e}")
            return None
    
    # ----------------------- HELPERS -----------------------
    
    def _cnpj_digits(self, cnpj: str) -> str:
        """Remove formatação do CNPJ."""
        return re.sub(r"\D", "", str(cnpj))
    
    def _processar_capital_social(self, df: pd.DataFrame, cnpj_digits: str, ano: int) -> pd.DataFrame:
        """
        Processa dados de capital social do FRE.
        
        Retorna DataFrame com:
        - ano
        - trimestre (sempre T4 para FRE)
        - ON (Ordinárias)
        - PN (Preferenciais)
        - TOTAL
        """
        if df is None or df.empty:
            return pd.DataFrame(columns=["ano", "trimestre", "ON", "PN", "TOTAL"])
        
        # Filtrar pela empresa
        if "CNPJ_Companhia" not in df.columns:
            return pd.DataFrame(columns=["ano", "trimestre", "ON", "PN", "TOTAL"])
        
        cnpj_col = df["CNPJ_Companhia"].str.replace(r'\D', '', regex=True)
        df_empresa = df[cnpj_col == cnpj_digits].copy()
        
        if df_empresa.empty:
            return pd.DataFrame(columns=["ano", "trimestre", "ON", "PN", "TOTAL"])
        
        # Pegar linha com Tipo_Capital = "Capital Integralizado" ou primeiro registro
        if "Tipo_Capital" in df_empresa.columns:
            df_integralizado = df_empresa[df_empresa["Tipo_Capital"].str.contains("Integralizado", case=False, na=False)]
            if not df_integralizado.empty:
                df_empresa = df_integralizado
        
        # Pegar primeira linha (último FRE do ano)
        linha = df_empresa.iloc[0]
        
        # Extrair quantidades
        on = pd.to_numeric(linha.get("Quantidade_Acoes_Ordinarias", 0), errors="coerce")
        pn = pd.to_numeric(linha.get("Quantidade_Acoes_Preferenciais", 0), errors="coerce")
        total = pd.to_numeric(linha.get("Quantidade_Total_Acoes", 0), errors="coerce")
        
        # Se total não existir, calcular
        if pd.isna(total) or total == 0:
            total = (on if not pd.isna(on) else 0) + (pn if not pd.isna(pn) else 0)
        
        result = pd.DataFrame({
            "ano": [ano],
            "trimestre": ["T4"],
            "ON": [int(on) if not pd.isna(on) else 0],
            "PN": [int(pn) if not pd.isna(pn) else 0],
            "TOTAL": [int(total) if not pd.isna(total) else 0]
        })
        
        return result
    
    def _build_horizontal(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Constrói tabela horizontal (períodos como colunas).
        
        Formato:
        | Espécie_Acao | 2010T4 | 2011T4 | 2012T4 | ...
        | ON           | 1000   | 1000   | 1200   | ...
        | PN           | 5000   | 5000   | 5500   | ...
        | TOTAL        | 6000   | 6000   | 6700   | ...
        """
        if df.empty:
            return pd.DataFrame(columns=["Espécie_Acao"])
        
        # Criar período (ano + trimestre)
        df["periodo"] = df["ano"].astype(str) + df["trimestre"]
        
        # Reorganizar dados para formato longo
        df_long = pd.DataFrame()
        for _, row in df.iterrows():
            periodo = row["periodo"]
            for especie in ["ON", "PN", "TOTAL"]:
                df_long = pd.concat([
                    df_long,
                    pd.DataFrame({
                        "especie": [especie],
                        "periodo": [periodo],
                        "quantidade": [row[especie]]
                    })
                ], ignore_index=True)
        
        # Pivotar
        pivot = df_long.pivot_table(
            index="especie",
            columns="periodo",
            values="quantidade",
            aggfunc="first"
        )
        
        # Ordenar colunas cronologicamente
        def sort_key(p):
            try:
                ano = int(p[:4])
                trim = _quarter_order(p[4:])
                return (ano, trim)
            except:
                return (9999, 99)
        
        cols = sorted(pivot.columns, key=sort_key)
        pivot = pivot[cols]
        
        # Ordenar linhas: ON, PN, TOTAL
        especies_ordem = ["ON", "PN", "TOTAL"]
        especies_presentes = [e for e in especies_ordem if e in pivot.index]
        
        pivot = pivot.reindex(especies_presentes)
        
        # Converter para inteiros
        pivot = pivot.fillna(0).astype(int)
        
        # Resetar índice
        pivot.insert(0, "Espécie_Acao", pivot.index)
        pivot = pivot.reset_index(drop=True)
        
        return pivot
    
    # ----------------------- PROCESSAMENTO -----------------------
    
    def processar_empresa(self, ticker: str, cnpj: str):
        """
        Captura histórico de ações de uma empresa.
        Fonte: Formulário de Referência (FRE).
        """
        print(f"\n{'='*50}")
        print(f"📊 {ticker} (CNPJ: {cnpj})")
        
        pasta = get_pasta_balanco(ticker)
        pasta.mkdir(exist_ok=True)
        
        cnpj_digits = self._cnpj_digits(cnpj)
        
        # Baixar FRE de todos os anos
        dados_anos = []
        
        for ano in range(self.ano_inicio, self.ano_atual + 1):
            zip_path = self._download_fre_zip(ano)
            if zip_path is None:
                continue
            
            df = self._ler_capital_social(zip_path, ano)
            if df is None or df.empty:
                continue
            
            df_processado = self._processar_capital_social(df, cnpj_digits, ano)
            if df_processado.empty:
                continue
            
            dados_anos.append(df_processado)
        
        # Consolidar
        if dados_anos:
            consolidado = pd.concat(dados_anos, ignore_index=True)
            
            # Construir formato horizontal
            horizontal = self._build_horizontal(consolidado)
            
            # Salvar
            arq_horizontal = pasta / "acoes_historico.csv"
            horizontal.to_csv(arq_horizontal, index=False, encoding="utf-8-sig")
            
            # Estatísticas
            n_periodos = len([c for c in horizontal.columns if c != "Espécie_Acao"])
            
            print(f"  ✅ Períodos: {n_periodos} (anos)")
            print(f"  ✅ Espécies: ON, PN, TOTAL")
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
        description="Captura histórico de número de ações (Formulário de Referência)"
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
    print(f">>> JOB: CAPTURAR HISTÓRICO DE AÇÕES (FRE) <<<")
    print(f"{'='*70}")
    print(f"Modo: {args.modo}")
    print(f"Empresas: {len(df_sel)}")
    print(f"Período: 2010 - {datetime.now().year}")
    print(f"Fonte: Formulário de Referência (FRE)")
    print(f"Formato: Horizontal (AAAAT4)")
    print(f"Saída: balancos/<TICKER>/acoes_historico.csv")
    print(f"{'='*70}\n")
    
    # Processar
    capturador = CapturadorAcoes()
    capturador.processar_lote(df_sel)


if __name__ == "__main__":
    main()
