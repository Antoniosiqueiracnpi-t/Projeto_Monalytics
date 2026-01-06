"""
CAPTURA DE HISTÓRICO DE AÇÕES - FORMULÁRIO DE REFERÊNCIA (FRE)

FONTE DE DADOS:
- Arquivo: fre_cia_aberta_capital_social_AAAA.csv
- Origem: Portal de Dados Abertos da CVM
- URL: https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/

IMPORTANTE - DADOS ANUAIS (T4):
- O Formulário de Referência (FRE) é enviado ANUALMENTE pelas empresas
- Portanto, contém apenas dados de final de ano (T4)
- Não há dados trimestrais oficiais (T1, T2, T3) em anos anteriores a 2024
- A partir de 2024, a CVM começou a exigir composição de capital no ITR
- Mantemos apenas T4 para garantir DADOS OFICIAIS sem interpolações artificiais

FORMATO DE SAÍDA:
- Layout: Horizontal (períodos como colunas)
- Exemplo: 2010T4, 2011T4, 2012T4, ..., 2024T4
- Arquivo: balancos/<TICKER>/acoes_historico.csv
- Espécies: ON (Ordinárias), PN (Preferenciais), TOTAL

ESTRUTURA DO ARQUIVO DE SAÍDA:
┌──────────────┬────────┬────────┬────────┬─────┐
│ Espécie_Acao │ 2010T4 │ 2011T4 │ 2012T4 │ ... │
├──────────────┼────────┼────────┼────────┼─────┤
│ ON           │ 1000   │ 1000   │ 1200   │ ... │
│ PN           │ 5000   │ 5000   │ 5500   │ ... │
│ TOTAL        │ 6000   │ 6000   │ 6700   │ ... │
└──────────────┴────────┴────────┴────────┴─────┘
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
    """
    Retorna Path da pasta de balanços.
    
    Lógica:
    1. Se já existe uma pasta com o ticker base (sem dígito final), usa ela
    2. Senão, cria nova pasta usando priorização (ON > PN)
    
    Exemplo:
    - get_pasta_balanco("ITUB4") com pasta ITUB4 existente → balancos/ITUB4
    - get_pasta_balanco("ITUB4") com pasta ITUB3 existente → balancos/ITUB3
    - get_pasta_balanco("ITUB4") sem pasta ITUB* → balancos/ITUB3 (prioriza ON)
    """
    ticker_clean = extrair_ticker_inteligente(ticker)
    base_dir = Path("balancos")
    base_dir.mkdir(exist_ok=True)
    
    # Extrair ticker base (sem dígito final)
    # ITUB3 -> ITUB, BBAS3 -> BBAS, VALE3 -> VALE
    ticker_base = ticker_clean.rstrip("0123456789")
    
    # Verificar se já existe alguma pasta com esse ticker base
    pastas_existentes = list(base_dir.glob(f"{ticker_base}*"))
    
    if pastas_existentes:
        # Usar a primeira pasta encontrada (geralmente só tem uma)
        return pastas_existentes[0]
    
    # Se não existe, criar nova pasta com ticker priorizado
    return base_dir / ticker_clean


def _quarter_order(q: str) -> int:
    """Retorna ordem numérica do trimestre."""
    return {"T4": 4}.get(q, 99)

def _remover_especies_zeradas(self, df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove linhas de espécies que têm TODOS os valores = 0.
    
    Exemplo: Se PN sempre zero, remove linha PN.
    
    Args:
        df: DataFrame horizontal com Espécie_Acao + períodos
    
    Returns:
        DataFrame sem linhas zeradas
    """
    if df.empty or "Espécie_Acao" not in df.columns:
        return df
    
    # Colunas numéricas (períodos)
    colunas_periodos = [c for c in df.columns if c != "Espécie_Acao"]
    
    if not colunas_periodos:
        return df
    
    # Filtrar linhas onde ALGUM período tem valor > 0
    mask = (df[colunas_periodos] > 0).any(axis=1)
    
    df_filtrado = df[mask].reset_index(drop=True)
    
    # Log de espécies removidas
    especies_removidas = set(df["Espécie_Acao"]) - set(df_filtrado["Espécie_Acao"])
    if especies_removidas:
        print(f"  ℹ️  Removidas espécies zeradas: {', '.join(especies_removidas)}")
    
    return df_filtrado


# ============================================================================
# CAPTURADOR DE HISTÓRICO DE AÇÕES
# ============================================================================

class CapturadorAcoes:
    """
    Captura histórico de número de ações de empresas brasileiras.
    
    ESTRATÉGIA DE DADOS:
    -------------------
    ✓ Fonte: Formulário de Referência (FRE) - Dados anuais oficiais
    ✓ Período: 2010 até ano atual
    ✓ Frequência: ANUAL (apenas T4 - final de ano)
    ✗ NÃO cria dados trimestrais artificiais (T1, T2, T3)
    
    JUSTIFICATIVA:
    -------------
    O FRE é enviado ANUALMENTE (geralmente em abril do ano seguinte).
    Interpolar ou repetir valores para T1/T2/T3 criaria falsa impressão
    de precisão trimestral. Mantemos apenas dados oficiais (T4).
    
    CASOS ESPECIAIS:
    ---------------
    - A partir de 2024: CVM passou a exigir composição de capital no ITR
    - Futuro: Podemos adicionar captura de dados trimestrais ITR 2024+
    - Atual: Mantemos apenas dados anuais confiáveis
    
    FORMATO DE SAÍDA:
    ----------------
    CSV horizontal com espécies de ações como linhas:
    - ON: Ações Ordinárias
    - PN: Ações Preferenciais  
    - TOTAL: Soma de todas as ações
    
    Períodos como colunas: 2010T4, 2011T4, ..., 2024T4
    """
    
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

        if "Data_Referencia" in linha.index or "DT_Refer" in linha.index:
            data_ref_col = "Data_Referencia" if "Data_Referencia" in linha.index else "DT_Refer"
            try:
                data_ref = pd.to_datetime(linha[data_ref_col], errors="coerce")
                if pd.notna(data_ref):
                    ano_ref = data_ref.year
                    # Verificar se ano de referência bate com ano esperado
                    if ano_ref != ano:
                        print(f"    ⚠️ Ajustando ano: FRE {ano} tem data_ref {ano_ref}")
                        ano = ano_ref
            except Exception:
                pass        
        
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
        Constrói tabela horizontal com dados ANUAIS OFICIAIS (apenas T4).
        
        IMPORTANTE: Mantém apenas dados T4 (Formulário de Referência).
        Não cria períodos trimestrais artificiais para evitar falsa precisão.
        
        Formato de saída:
        ┌──────────────┬────────┬────────┬────────┬─────┐
        │ Espécie_Acao │ 2010T4 │ 2011T4 │ 2012T4 │ ... │
        ├──────────────┼────────┼────────┼────────┼─────┤
        │ ON           │ 1000   │ 1000   │ 1200   │ ... │
        │ PN           │ 5000   │ 5000   │ 5500   │ ... │
        │ TOTAL        │ 6000   │ 6000   │ 6700   │ ... │
        └──────────────┴────────┴────────┴────────┴─────┘
        
        Args:
            df: DataFrame com colunas [ano, trimestre, ON, PN, TOTAL]
        
        Returns:
            DataFrame no formato horizontal (períodos como colunas)
        """
        if df.empty:
            return pd.DataFrame(columns=["Espécie_Acao"])
        
        # ====================================================================
        # ETAPA 1: Criar identificador de período (AAAATX)
        # ====================================================================
        df = df.copy()
        df["periodo"] = df["ano"].astype(str) + df["trimestre"].astype(str)
        
        # ====================================================================
        # ETAPA 2: Transformar para formato longo (unpivot)
        # ====================================================================
        # De:   ano | trimestre | ON | PN | TOTAL
        # Para: especie | periodo | quantidade
        
        registros = []
        for _, row in df.iterrows():
            periodo = row["periodo"]
            for especie in ["ON", "PN", "TOTAL"]:
                registros.append({
                    "especie": especie,
                    "periodo": periodo,
                    "quantidade": row[especie]
                })
        
        df_long = pd.DataFrame(registros)
        
        # ====================================================================
        # ETAPA 3: Pivotar para formato horizontal
        # ====================================================================
        # De:   especie | periodo | quantidade
        # Para: especie como índice, períodos como colunas
        
        pivot = df_long.pivot_table(
            index="especie",
            columns="periodo",
            values="quantidade",
            aggfunc="first"  # Apenas um valor por espécie/período
        )
        
        # ====================================================================
        # ETAPA 4: Ordenar colunas cronologicamente
        # ====================================================================
        def extrair_ano_trimestre(periodo_str):
            """Extrai (ano, trimestre_num) de string AAAATX"""
            try:
                ano = int(periodo_str[:4])
                trimestre_str = periodo_str[4:]  # "T4"
                trimestre_num = _quarter_order(trimestre_str)
                return (ano, trimestre_num)
            except:
                return (9999, 99)  # Erro → colocar no final
        
        colunas_ordenadas = sorted(pivot.columns, key=extrair_ano_trimestre)
        pivot = pivot[colunas_ordenadas]
        
        # ====================================================================
        # ETAPA 5: Ordenar linhas na sequência: ON → PN → TOTAL
        # ====================================================================
        especies_ordem = ["ON", "PN", "TOTAL"]
        especies_presentes = [e for e in especies_ordem if e in pivot.index]
        pivot = pivot.reindex(especies_presentes)
        
        # ====================================================================
        # ETAPA 6: Tratamento de valores e formatação final
        # ====================================================================
        # Substituir NaN por 0 e converter para inteiros
        pivot = pivot.fillna(0).astype(int)
        
        # Adicionar coluna Espécie_Acao como primeira coluna
        pivot.insert(0, "especie", pivot.index)
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
        
        # Mostrar pasta que será usada
        ticker_display = extrair_ticker_inteligente(ticker)
        if pasta.name != ticker_display:
            print(f"  ℹ️  Usando pasta existente: {pasta.name}")
        
        cnpj_digits = self._cnpj_digits(cnpj)
        
        # ✅ ADICIONAR: Definir ano máximo válido
        # FRE de YYYY reporta dados até 31/12/(YYYY-1)
        # Exemplo: FRE 2025 (reportado em 2026) = dados de 2024T4
        ano_atual_real = datetime.now().year
        mes_atual = datetime.now().month
        
        # Se estamos em Jan-Abr, último ano fiscal completo é (ano_atual - 2)
        # Se estamos em Mai-Dez, último ano fiscal completo é (ano_atual - 1)
        if mes_atual <= 4:
            ano_max_valido = ano_atual_real - 2
        else:
            ano_max_valido = ano_atual_real - 1
        
        # Baixar FRE de todos os anos VÁLIDOS
        dados_anos = []
        
        for ano in range(self.ano_inicio, ano_max_valido + 1):  # ← CORRIGIDO
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

            # ✅ ADICIONAR: Remover espécies zeradas
            horizontal = self._remover_especies_zeradas(horizontal)
            
            # Salvar
            arq_horizontal = pasta / "acoes_historico.csv"
            horizontal.to_csv(arq_horizontal, index=False, encoding="utf-8-sig")
            
            # Estatísticas
            n_periodos = len([c for c in horizontal.columns if c != "Espécie_Acao"])
            anos_inicio = consolidado["ano"].min()
            anos_fim = consolidado["ano"].max()
            
            print(f"  ✅ Dados anuais (T4): {anos_inicio} a {anos_fim}")
            print(f"  ✅ Total de anos: {n_periodos}")
            print(f"  ✅ Espécies: ON, PN, TOTAL")
            print(f"  ✅ Arquivo: acoes_historico.csv")
            print(f"  ℹ️  Apenas dados oficiais (FRE não contém dados trimestrais)")
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
    print(f">>> CAPTURA DE HISTÓRICO DE AÇÕES (DADOS ANUAIS - FRE) <<<")
    print(f"{'='*70}")
    print(f"Modo: {args.modo}")
    print(f"Empresas: {len(df_sel)}")
    print(f"Período: 2010 - {datetime.now().year}")
    print(f"Fonte: Formulário de Referência (FRE)")
    print(f"Frequência: ANUAL (apenas T4 - final de ano)")
    print(f"Formato: Horizontal (AAAAT4)")
    print(f"Saída: balancos/<TICKER>/acoes_historico.csv")
    print(f"{'='*70}")
    print(f"ℹ️  IMPORTANTE: FRE contém apenas dados anuais oficiais (T4).")
    print(f"             Não há interpolação ou criação de dados trimestrais.")
    print(f"{'='*70}\n")
    
    # Processar
    capturador = CapturadorAcoes()
    capturador.processar_lote(df_sel)


if __name__ == "__main__":
    main()
