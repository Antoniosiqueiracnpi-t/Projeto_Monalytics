"""
CAPTURA DE ACIONISTAS - FORMULÁRIO DE REFERÊNCIA (FRE)

FONTE DE DADOS:
- Arquivo: fre_cia_aberta_posicao_acionaria_AAAA.csv
- Origem: Portal de Dados Abertos da CVM
- URL: https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/

IMPORTANTE - DADOS ANUAIS:
- O Formulário de Referência (FRE) é enviado ANUALMENTE pelas empresas
- Contém posição acionária de final de ano (geralmente 31/12)
- Dados mais recentes: último FRE disponível

FORMATO DE SAÍDA:
- Layout: JSON estruturado
- Top 10 acionistas por empresa
- Arquivo: balancos/<TICKER>/acionistas.json

ESTRUTURA DO JSON:
{
  "empresa": {"cnpj": "...", "nome": "...", "ticker": "..."},
  "data_referencia": "2024-12-31",
  "acionistas": [
    {
      "posicao": 1,
      "nome": "...",
      "cpf_cnpj": "...",
      "tipo_pessoa": "...",
      "nacionalidade": "...",
      "acoes_total": 1000000,
      "percentual_total": 10.50,
      "acoes_ordinarias": 500000,
      "percentual_ordinarias": 8.30,
      "acoes_preferenciais": 500000,
      "percentual_preferenciais": 12.70
    }
  ]
}
"""

import pandas as pd
import requests
from pathlib import Path
from datetime import datetime
import zipfile
import re
import argparse
import json


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
    Verifica se já existe pasta com ticker base antes de criar nova.
    """
    ticker_clean = extrair_ticker_inteligente(ticker)
    base_dir = Path("balancos")
    base_dir.mkdir(exist_ok=True)
    
    # Extrair ticker base (ITUB4 → ITUB)
    ticker_base = ticker_clean.rstrip("0123456789")
    
    # Verificar se já existe alguma pasta com esse ticker base
    pastas_existentes = list(base_dir.glob(f"{ticker_base}*"))
    
    if pastas_existentes:
        return pastas_existentes[0]
    
    return base_dir / ticker_clean


# ============================================================================
# CAPTURADOR DE ACIONISTAS
# ============================================================================

class CapturadorAcionistas:
    """
    Captura composição acionária de empresas brasileiras.
    
    ESTRATÉGIA DE DADOS:
    -------------------
    ✓ Fonte: Formulário de Referência (FRE) - Item 15.1/2
    ✓ Período: Ano mais recente disponível
    ✓ Top 10 acionistas por empresa
    ✓ Formato JSON estruturado
    
    INFORMAÇÕES CAPTURADAS:
    ----------------------
    - Nome do acionista
    - CPF/CNPJ completo
    - Tipo de pessoa (PF, PJ, Fundo, Governo, etc)
    - Nacionalidade (Nacional, Estrangeiro)
    - Quantidade de ações (Total, ON, PN)
    - Percentuais (Total, ON, PN)
    
    LIMITAÇÕES:
    ----------
    - Dados ANUAIS (FRE é enviado uma vez por ano)
    - Posição de final de ano (31/12 do ano anterior)
    - Acionistas <5% podem não estar listados individualmente
    """
    
    def __init__(self):
        self.pasta_balancos = Path("balancos")
        self.pasta_balancos.mkdir(exist_ok=True)
        
        self.cache_dir = Path(".cvm_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Usar ano atual e ano anterior
        self.ano_atual = datetime.now().year
        self.anos_teste = [self.ano_atual, self.ano_atual - 1]
    
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
    
    def _ler_posicao_acionaria(self, zip_path: Path, ano: int) -> pd.DataFrame | None:
        """Lê arquivo fre_cia_aberta_posicao_acionaria do ZIP."""
        if zip_path is None or not zip_path.exists():
            return None
        
        alvo = f"fre_cia_aberta_posicao_acionaria_{ano}.csv"
        
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
    
    def _formatar_cpf_cnpj(self, doc: str) -> str:
        """
        Formata CPF ou CNPJ.
        CPF: XXX.XXX.XXX-XX
        CNPJ: XX.XXX.XXX/XXXX-XX
        """
        if pd.isna(doc) or not doc:
            return ""
        
        doc = self._cnpj_digits(doc)
        
        if len(doc) == 11:  # CPF
            return f"{doc[:3]}.{doc[3:6]}.{doc[6:9]}-{doc[9:11]}"
        elif len(doc) == 14:  # CNPJ
            return f"{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:14]}"
        else:
            return doc
    
    def _safe_float(self, value, default=0.0) -> float:
        """Converte valor para float com segurança."""
        try:
            if pd.isna(value) or value == "":
                return default
            return float(str(value).replace(",", "."))
        except:
            return default
    
    def _safe_int(self, value, default=0) -> int:
        """Converte valor para int com segurança."""
        try:
            if pd.isna(value) or value == "":
                return default
            return int(float(str(value).replace(",", ".")))
        except:
            return default
    
    def _processar_acionistas(self, df: pd.DataFrame, cnpj_digits: str) -> list:
        """
        Processa dados de posição acionária.
        
        Retorna lista de dicionários com top 10 acionistas.
        """
        if df is None or df.empty:
            return []
        
        # Filtrar pela empresa
        if "CNPJ_Companhia" not in df.columns:
            return []
        
        cnpj_col = df["CNPJ_Companhia"].str.replace(r'\D', '', regex=True)
        df_empresa = df[cnpj_col == cnpj_digits].copy()
        
        if df_empresa.empty:
            return []
        
        # Mapear colunas (baseado na estrutura REAL do arquivo FRE 2024)
        col_map = {
            # Nome do acionista
            "nome": ["Acionista", "Nome_Acionista", "Nome"],
            # CPF/CNPJ
            "cpf_cnpj": ["CPF_CNPJ_Acionista", "CPF_CNPJ", "Documento"],
            # Tipo de pessoa
            "tipo_pessoa": ["Tipo_Pessoa_Acionista", "Tipo_Pessoa", "TipoPessoa", "Tipo"],
            # Nacionalidade
            "nacionalidade": ["Nacionalidade", "Pais", "Nacional"],
            # Quantidade total (CIRCULACAO é o correto)
            "qtd_total": ["Quantidade_Total_Acoes_Circulacao", "Quantidade_Acoes", "Quantidade_Total", "QtdAcoes"],
            # Percentual total (CIRCULACAO é o correto)
            "perc_total": ["Percentual_Total_Acoes_Circulacao", "Percentual_Total", "Perc_Total", "PercTotal"],
            # Quantidade ON (CIRCULACAO é o correto)
            "qtd_on": ["Quantidade_Acao_Ordinaria_Circulacao", "Quantidade_Acoes_Ordinarias", "QtdON", "ON"],
            # Percentual ON (CIRCULACAO é o correto)
            "perc_on": ["Percentual_Acao_Ordinaria_Circulacao", "Percentual_Acoes_Ordinarias", "PercON", "Perc_Ordinarias"],
            # Quantidade PN (CIRCULACAO é o correto)
            "qtd_pn": ["Quantidade_Acao_Preferencial_Circulacao", "Quantidade_Acoes_Preferenciais", "QtdPN", "PN"],
            # Percentual PN (CIRCULACAO é o correto)
            "perc_pn": ["Percentual_Acao_Preferencial_Circulacao", "Percentual_Acoes_Preferenciais", "PercPN", "Perc_Preferenciais"],
        }
        
        # Identificar colunas disponíveis
        colunas_encontradas = {}
        for key, possiveis in col_map.items():
            for col_nome in possiveis:
                if col_nome in df_empresa.columns:
                    colunas_encontradas[key] = col_nome
                    break
        
        # Processar acionistas
        acionistas = []
        
        for _, row in df_empresa.iterrows():
            # Pular registros especiais (não são acionistas reais)
            nome_acionista = str(row.get(colunas_encontradas.get("nome", ""), "")).strip()
            
            # Filtrar categorias especiais
            if not nome_acionista:
                continue
            if nome_acionista.lower() in ["ações tesouraria", "tesouraria", "outros", "ações em tesouraria"]:
                continue
            
            # Pular se for acionista relacionado (linha secundária)
            if "Acionista_Relacionado" in row.index and pd.notna(row["Acionista_Relacionado"]):
                # Esta é uma linha de "Acionista Relacionado", pular
                continue
            
            acionista = {
                "nome": nome_acionista,
                "cpf_cnpj": self._formatar_cpf_cnpj(row.get(colunas_encontradas.get("cpf_cnpj", ""), "")),
                "tipo_pessoa": str(row.get(colunas_encontradas.get("tipo_pessoa", ""), "")).strip(),
                "nacionalidade": str(row.get(colunas_encontradas.get("nacionalidade", ""), "")).strip(),
                "acoes_total": self._safe_int(row.get(colunas_encontradas.get("qtd_total", ""), 0)),
                "percentual_total": self._safe_float(row.get(colunas_encontradas.get("perc_total", ""), 0.0)),
                "acoes_ordinarias": self._safe_int(row.get(colunas_encontradas.get("qtd_on", ""), 0)),
                "percentual_ordinarias": self._safe_float(row.get(colunas_encontradas.get("perc_on", ""), 0.0)),
                "acoes_preferenciais": self._safe_int(row.get(colunas_encontradas.get("qtd_pn", ""), 0)),
                "percentual_preferenciais": self._safe_float(row.get(colunas_encontradas.get("perc_pn", ""), 0.0)),
            }
            
            # Validar se tem dados mínimos
            if acionista["nome"] and acionista["acoes_total"] > 0:
                acionistas.append(acionista)
        
        # Ordenar por percentual total (decrescente)
        acionistas.sort(key=lambda x: x["percentual_total"], reverse=True)
        
        # Retornar top 10
        return acionistas[:10]
    
    # ----------------------- PROCESSAMENTO -----------------------
    
    def processar_empresa(self, ticker: str, cnpj: str, nome_empresa: str):
        """
        Captura composição acionária de uma empresa.
        Fonte: Formulário de Referência (FRE).
        """
        print(f"\n{'='*50}")
        print(f"📊 {ticker} - {nome_empresa}")
        
        pasta = get_pasta_balanco(ticker)
        pasta.mkdir(exist_ok=True)
        
        # Mostrar pasta que será usada
        ticker_display = extrair_ticker_inteligente(ticker)
        if pasta.name != ticker_display:
            print(f"  ℹ️  Usando pasta existente: {pasta.name}")
        
        cnpj_digits = self._cnpj_digits(cnpj)
        
        # Tentar baixar FRE do ano atual e anterior
        acionistas = []
        data_referencia = None
        ano_usado = None
        
        for ano in self.anos_teste:
            zip_path = self._download_fre_zip(ano)
            if zip_path is None:
                continue
            
            df = self._ler_posicao_acionaria(zip_path, ano)
            if df is None or df.empty:
                continue
            
            acionistas_ano = self._processar_acionistas(df, cnpj_digits)
            if acionistas_ano:
                acionistas = acionistas_ano
                ano_usado = ano
                # Data de referência geralmente é 31/12 do ano
                data_referencia = f"{ano}-12-31"
                break
        
        # Consolidar e salvar
        if acionistas:
            # Adicionar posição
            for i, acionista in enumerate(acionistas, 1):
                acionista["posicao"] = i
            
            # Estrutura final do JSON
            dados = {
                "empresa": {
                    "cnpj": cnpj,
                    "nome": nome_empresa,
                    "ticker": ticker_display
                },
                "data_referencia": data_referencia,
                "ano_fre": ano_usado,
                "top_acionistas": len(acionistas),
                "acionistas": acionistas
            }
            
            # Salvar JSON
            arq_json = pasta / "acionistas.json"
            with open(arq_json, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            
            # Estatísticas
            print(f"  ✅ Ano FRE: {ano_usado}")
            print(f"  ✅ Data ref: {data_referencia}")
            print(f"  ✅ Acionistas: {len(acionistas)}")
            print(f"  ✅ Arquivo: acionistas.json")
            
            # Mostrar top 3
            print(f"\n  📈 TOP 3 ACIONISTAS:")
            for acionista in acionistas[:3]:
                print(f"    {acionista['posicao']}. {acionista['nome']}: {acionista['percentual_total']:.2f}%")
        else:
            print(f"  ❌ Nenhum acionista encontrado")
    
    def processar_lote(self, df_sel: pd.DataFrame):
        """Processa lote de empresas."""
        print(f"\n🚀 Processando {len(df_sel)} empresas...\n")
        
        ok_count = 0
        err_count = 0
        
        for _, row in df_sel.iterrows():
            try:
                ticker_str = str(row["ticker"]).strip().upper()
                ticker_cvm = extrair_ticker_inteligente(ticker_str)
                nome_empresa = str(row.get("nome_empresa", row.get("denominacao_social", ""))).strip()
                
                self.processar_empresa(ticker_cvm, row["cnpj"], nome_empresa)
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
        description="Captura composição acionária (Top 10 acionistas - Formulário de Referência)"
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
    print(f">>> CAPTURA DE ACIONISTAS (TOP 10 - FRE) <<<")
    print(f"{'='*70}")
    print(f"Modo: {args.modo}")
    print(f"Empresas: {len(df_sel)}")
    print(f"Ano: {datetime.now().year} (mais recente disponível)")
    print(f"Fonte: Formulário de Referência (FRE)")
    print(f"Top: 10 acionistas por empresa")
    print(f"Formato: JSON")
    print(f"Saída: balancos/<TICKER>/acionistas.json")
    print(f"{'='*70}")
    print(f"ℹ️  INFORMAÇÕES CAPTURADAS:")
    print(f"   - Nome, CPF/CNPJ, Tipo de Pessoa, Nacionalidade")
    print(f"   - Quantidade e % de ações (Total, ON, PN)")
    print(f"{'='*70}\n")
    
    # Processar
    capturador = CapturadorAcionistas()
    capturador.processar_lote(df_sel)


if __name__ == "__main__":
    main()
