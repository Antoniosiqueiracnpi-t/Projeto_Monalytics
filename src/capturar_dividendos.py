# src/capturar_dividendos.py
from __future__ import annotations

import argparse
import base64
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Dict
import warnings

import pandas as pd
import numpy as np
import requests


import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from multi_ticker_utils import get_ticker_principal, get_pasta_balanco, load_mapeamento_consolidado

# Suprimir warnings
warnings.filterwarnings('ignore')

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

# Suprimir warnings SSL para API B3
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass


def _quarter_order(q: str) -> int:
    """Retorna ordem numérica do trimestre para ordenação."""
    return {"T1": 1, "T2": 2, "T3": 3, "T4": 4}.get(q, 99)


def _date_to_quarter(date: pd.Timestamp) -> str:
    """Converte data para trimestre (T1, T2, T3, T4)."""
    if pd.isna(date):
        return None
    month = date.month
    if month <= 3:
        return "T1"
    elif month <= 6:
        return "T2"
    elif month <= 9:
        return "T3"
    else:
        return "T4"


def _extract_trading_name(nome_empresa: str) -> str:
    """
    Extrai trading name do nome completo da empresa.
    
    Exemplos:
    - "MUNDIAL S.A. – PRODUTOS DE CONSUMO" → "MUNDIAL"
    - "TECHNOS S.A." → "TECHNOS"
    - "SÃO MARTINHO S.A." → "SAO MARTINHO"
    - "VIVARA PARTICIPAÇÕES S.A." → "VIVARA"
    """
    if not nome_empresa:
        return ""
    
    # Remover sufixos comuns
    nome = nome_empresa.upper()
    
    # Padrões a remover
    patterns = [
        r'\s+S\.?A\.?.*$',  # S.A. e tudo após
        r'\s+SA\b.*$',       # SA e tudo após
        r'\s+LTDA.*$',       # LTDA e tudo após
        r'\s+–.*$',          # Hífen longo e tudo após
        r'\s+-\s+.*$',       # Hífen e tudo após
        r'\s+PARTICIPACOES.*$',
        r'\s+PARTICIPAÇÕES.*$',
    ]
    
    for pattern in patterns:
        nome = re.sub(pattern, '', nome, flags=re.IGNORECASE)
    
    return nome.strip()


def _parse_b3_value(value_str: str) -> float:
    """
    Converte valor da API B3 de formato brasileiro para float.
    
    Exemplos:
    - "0,20092175" → 0.20092175
    - "1,028980" → 1.028980
    """
    if not value_str:
        return 0.0
    
    try:
        # Substituir vírgula por ponto
        value_str = str(value_str).replace(',', '.')
        return float(value_str)
    except:
        return 0.0


@dataclass
class CapturadorDividendos:
    """
    Captura histórico de dividendos usando múltiplas fontes.
    
    Prioridade:
    1. API B3 Oficial (gratuita, dados primários B3)
    2. OkaneBox API (gratuita, simples, dados B3)
    3. yfinance (fallback, dados Yahoo Finance)
    4. CSV Local (último fallback)
    
    Agrupa dividendos por trimestre baseado na data COM
    e gera formato horizontal padronizado.
    
    Salva 2 arquivos:
    - dividendos_trimestrais.csv (formato horizontal)
    - dividendos_detalhado.json (datas exatas para mapa de calor)
    """
    pasta_balancos: Path = Path("balancos")
    timeout: int = 30
    csv_mapeamento: str = "mapeamento_final_b3_completo_utf8.csv"
    _df_mapeamento: Optional[pd.DataFrame] = None
    
    def __post_init__(self):
        """Carregar CSV de mapeamento na inicialização."""
        self._load_mapeamento()
    
    def _load_mapeamento(self):
        """Carrega CSV de mapeamento de empresas."""
        try:
            self._df_mapeamento = pd.read_csv(
                self.csv_mapeamento, 
                sep=";", 
                encoding="utf-8-sig"
            )
        except Exception as e:
            print(f"    ⚠️ Erro ao carregar mapeamento: {e}")
            self._df_mapeamento = pd.DataFrame()
    
    def _get_empresa_info(self, ticker: str) -> Dict[str, str]:
        """
        Busca informações da empresa no CSV de mapeamento.
        Agora usa ticker principal para garantir encontrar os dados.
        
        Returns:
            dict com 'empresa', 'cnpj', 'trading_name'
        """
        if self._df_mapeamento is None or self._df_mapeamento.empty:
            return {}
        
        # Resolver para ticker principal
        ticker_principal = get_ticker_principal(ticker)
        if not ticker_principal:
            ticker_principal = ticker.upper().strip()
        
        mask = self._df_mapeamento['ticker'].str.upper().str.contains(
            ticker_principal, 
            case=False, 
            na=False, 
            regex=False
        )
        rows = self._df_mapeamento[mask]
        
        if rows.empty:
            return {}
        
        row = rows.iloc[0]
        
        empresa = str(row.get('empresa', ''))
        cnpj = str(row.get('cnpj', ''))
        trading_name = _extract_trading_name(empresa)
        
        return {
            'empresa': empresa,
            'cnpj': cnpj,
            'trading_name': trading_name
        }
    
    def _fetch_b3_api(self, ticker: str) -> pd.DataFrame:
        """
        Busca dividendos da API B3 Oficial.
        
        Endpoint: sistemaswebb3-listados.b3.com.br
        Usa trading name da empresa obtido do CSV de mapeamento.
        Pagina automaticamente (120 registros por página).
        """
        # Buscar trading name no CSV
        info = self._get_empresa_info(ticker)
        trading_name = info.get('trading_name', '')
        
        if not trading_name:
            print(f"    [B3 API] Trading name não encontrado no CSV")
            return pd.DataFrame()
        
        print(f"    [B3 API] Trading name: {trading_name}")
        
        all_dividends = []
        page = 1
        max_pages = 50  # Limite de segurança
        
        while page <= max_pages:
            try:
                # Parâmetros da API
                params = {
                    "language": "pt-br",
                    "pageNumber": page,
                    "pageSize": 120,
                    "tradingName": trading_name
                }
                
                # Codificar em base64
                params_json = json.dumps(params)
                params_b64 = base64.b64encode(params_json.encode()).decode()
                
                # URL da API B3
                url = f"https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetListedCashDividends/{params_b64}"
                
                # Requisição (SSL verify=False necessário)
                response = requests.get(url, verify=False, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                
                # Extrair resultados
                results = data.get('results', [])
                
                if not results:
                    break
                
                all_dividends.extend(results)
                
                # Verificar paginação
                page_info = data.get('page', {})
                current_page = page_info.get('pageNumber', 0)
                total_pages = page_info.get('totalPages', 0)
                
                if current_page >= total_pages:
                    break
                
                page += 1
                
            except Exception as e:
                if page == 1:
                    print(f"    [B3 API] Erro: {e}")
                break
        
        if not all_dividends:
            return pd.DataFrame()
        
        # Converter para DataFrame
        df = pd.DataFrame(all_dividends)
        
        # Padronizar colunas
        column_mapping = {
            'lastDatePriorEx': 'data_com',
            'corporateActionPrice': 'valor',
            'corporateAction': 'tipo',
            'dateApproval': 'data_aprovacao',
            'lastDateTimePriorEx': 'data_com_full'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Converter valores de formato brasileiro
        if 'valor' in df.columns:
            df['valor'] = df['valor'].apply(
                lambda x: _parse_b3_value(x) if pd.notna(x) else 0.0
            )
        
        return df
    
    def _fetch_okanebox(self, ticker: str) -> pd.DataFrame:
        """
        Busca dividendos da OkaneBox API.
        
        Endpoint: https://okanebox.com.br/api/acoes/proventos/{ticker}/
        Retorna: JSON com histórico completo de proventos
        """
        ticker_clean = ticker.upper().replace('.SA', '')
        url = f"https://okanebox.com.br/api/acoes/proventos/{ticker_clean}/"
        
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return pd.DataFrame()
            
            # Converter para DataFrame
            df = pd.DataFrame(data)
            
            # Padronizar colunas
            # OkaneBox retorna: ticker, tipo, datacom, datapagamento, valor
            if 'datacom' in df.columns:
                df = df.rename(columns={
                    'datacom': 'data_com',
                    'datapagamento': 'data_pagamento'
                })
            
            return df
            
        except Exception as e:
            print(f"    [OkaneBox] Erro: {e}")
            return pd.DataFrame()
    
    def _fetch_yfinance(self, ticker: str) -> pd.DataFrame:
        """
        Busca dividendos via yfinance (Yahoo Finance).
        
        Fallback quando OkaneBox não funciona.
        """
        if not HAS_YFINANCE:
            return pd.DataFrame()
        
        try:
            # Garantir que ticker tenha .SA
            ticker_yf = ticker.upper()
            if not ticker_yf.endswith('.SA'):
                ticker_yf = f"{ticker_yf}.SA"
            
            stock = yf.Ticker(ticker_yf)
            divs = stock.dividends
            
            if divs.empty:
                return pd.DataFrame()
            
            # Converter Series para DataFrame
            df = divs.reset_index()
            df.columns = ['data_pagamento', 'valor']
            
            # yfinance não diferencia tipo, considerar tudo como "Dividendo"
            df['tipo'] = 'Dividendo'
            df['data_com'] = df['data_pagamento']  # Aproximação
            
            return df
            
        except Exception as e:
            print(f"    [yfinance] Erro: {e}")
            return pd.DataFrame()
    
    def _fetch_local_csv(self, ticker: str) -> pd.DataFrame:
        """
        Busca dividendos de arquivo CSV local (se disponível).
        
        Formato esperado: balancos/{ticker}/dividendos_raw.csv
        Colunas: data_com, data_pagamento, valor, tipo
        
        Terceiro fallback para ambientes sem acesso a APIs externas.
        """
        csv_path = self.pasta_balancos / ticker / "dividendos_raw.csv"
        
        if not csv_path.exists():
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(csv_path)
            return df
        except Exception as e:
            print(f"    [CSV Local] Erro: {e}")
            return pd.DataFrame()
    
    def _fetch_all_dividends(self, ticker: str) -> pd.DataFrame:
        """
        Busca dividendos tentando múltiplas fontes em ordem de prioridade.
        
        1. B3 API Oficial (dados primários B3 via trading name)
        2. OkaneBox API (gratuita, dados B3 oficiais)
        3. yfinance (Yahoo Finance, dados internacionais)
        4. CSV local (se arquivo dividendos_raw.csv existe)
        """
        # 1. Tentar B3 API Oficial (PRIORIDADE)
        df = self._fetch_b3_api(ticker)
        
        if not df.empty:
            print(f"    ✓ Fonte: B3 API Oficial ({len(df)} registros)")
            return df
        
        # 2. Tentar OkaneBox (fallback 1)
        df = self._fetch_okanebox(ticker)
        
        if not df.empty:
            print(f"    ✓ Fonte: OkaneBox ({len(df)} registros)")
            return df
        
        # 3. Tentar yfinance (fallback 2)
        df = self._fetch_yfinance(ticker)
        
        if not df.empty:
            print(f"    ✓ Fonte: yfinance ({len(df)} registros)")
            return df
        
        # 4. Tentar CSV local (último fallback)
        df = self._fetch_local_csv(ticker)
        
        if not df.empty:
            print(f"    ✓ Fonte: CSV Local ({len(df)} registros)")
            return df
        
        return pd.DataFrame()
    
    def _process_dividends(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """
        Processa dividendos brutos.
        
        1. Padroniza colunas
        2. Converte datas
        3. Padroniza valores
        4. Remove dados inválidos
        """
        if df.empty:
            return df
        
        # Garantir colunas essenciais
        if 'ticker' not in df.columns:
            df['ticker'] = ticker.upper()
        
        # Usar data_com se disponível, senão data_pagamento
        if 'data_com' in df.columns:
            date_ref = 'data_com'
        elif 'data_pagamento' in df.columns:
            date_ref = 'data_pagamento'
            df['data_com'] = df['data_pagamento']
        else:
            return pd.DataFrame()
        
        # Converter datas
        for date_col in ['data_com', 'data_pagamento']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Converter valores
        if 'valor' in df.columns:
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        
        # Remover linhas sem data ou valor
        df = df.dropna(subset=['data_com', 'valor'])
        
        # Remover valores zero ou negativos
        df = df[df['valor'] > 0]
        
        return df
    
    def _group_by_quarter(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrupa dividendos por trimestre.
        
        Usa data_com (ex-dividendo) como referência.
        Soma todos os proventos do mesmo trimestre.
        """
        if df.empty:
            return df
        
        # Extrair ano e trimestre
        df['ano'] = df['data_com'].dt.year
        df['trimestre'] = df['data_com'].apply(_date_to_quarter)
        
        # Remover registros sem trimestre
        df = df.dropna(subset=['trimestre'])
        
        # Agrupar e somar por ano/trimestre
        grouped = df.groupby(['ano', 'trimestre'], as_index=False).agg({
            'valor': 'sum'
        })
        
        # Arredondar valores
        grouped['valor'] = grouped['valor'].round(4)
        
        return grouped
    
    def _build_horizontal(self, df_grouped: pd.DataFrame) -> pd.DataFrame:
        """
        Constrói tabela horizontal (períodos como colunas).
        
        Formato: Dividendos_Pagos | 2022T1 | 2022T2 | ...
        """
        if df_grouped.empty:
            return pd.DataFrame(columns=["Dividendos_Pagos"])
        
        # Criar período (ex: 2022T1)
        df_grouped['periodo'] = (
            df_grouped['ano'].astype(str) + df_grouped['trimestre']
        )
        
        # Ordenar períodos cronologicamente
        def sort_key(p):
            try:
                return (int(p[:4]), _quarter_order(p[4:]))
            except:
                return (9999, 99)
        
        df_grouped = df_grouped.sort_values(
            by='periodo',
            key=lambda x: x.map(sort_key)
        )
        
        # Criar dict com período: valor
        value_dict = dict(zip(
            df_grouped['periodo'],
            df_grouped['valor']
        ))
        
        # Construir linha horizontal
        result = {"Dividendos_Pagos": "Dividendos + JCP Pagos no Trimestre"}
        result.update(value_dict)
        
        return pd.DataFrame([result])
    
    def _build_detalhado_json(self, df_processed: pd.DataFrame, ticker: str) -> dict:
        """
        Constrói JSON detalhado com datas exatas para mapeamento de calor.
        
        Formato:
        {
            "ticker": "PETR4",
            "total_dividendos": 56.09,
            "periodo": "2020-2024",
            "dividendos": [
                {
                    "data_com": "2022-02-23",
                    "valor": 2.2336,
                    "tipo": "Dividendo",
                    "ano": 2022,
                    "mes": 2,
                    "trimestre": "T1"
                },
                ...
            ]
        }
        """
        if df_processed.empty:
            return {}
        
        # Preparar lista de dividendos
        dividendos_list = []
        
        for _, row in df_processed.iterrows():
            data_com = row.get('data_com')
            
            if pd.isna(data_com):
                continue
            
            dividendo = {
                "data_com": data_com.strftime('%Y-%m-%d'),
                "valor": float(row.get('valor', 0)),
                "tipo": str(row.get('tipo', 'Dividendo')),
                "ano": int(data_com.year),
                "mes": int(data_com.month),
                "dia": int(data_com.day),
                "trimestre": _date_to_quarter(data_com)
            }
            
            # Adicionar data de pagamento se disponível
            if 'data_pagamento' in row and pd.notna(row['data_pagamento']):
                dividendo['data_pagamento'] = row['data_pagamento'].strftime('%Y-%m-%d')
            
            dividendos_list.append(dividendo)
        
        # Ordenar por data
        dividendos_list.sort(key=lambda x: x['data_com'])
        
        # Calcular estatísticas
        total = sum(d['valor'] for d in dividendos_list)
        periodo_inicio = dividendos_list[0]['ano'] if dividendos_list else None
        periodo_fim = dividendos_list[-1]['ano'] if dividendos_list else None
        
        resultado = {
            "ticker": ticker,
            "total_dividendos": round(total, 4),
            "periodo": f"{periodo_inicio}-{periodo_fim}" if periodo_inicio else "",
            "quantidade_pagamentos": len(dividendos_list),
            "dividendos": dividendos_list
        }
        
        return resultado
    
    def capturar_e_salvar_ticker(self, ticker: str) -> Tuple[bool, str]:
        """
        Pipeline completo de captura de dividendos.
        Agora usa get_pasta_balanco() para garantir pasta correta.
        """
        ticker = ticker.upper().strip()
        pasta = get_pasta_balanco(ticker)
        
        # Garantir que pasta existe
        pasta.mkdir(parents=True, exist_ok=True)
        
        # 1. Buscar dividendos brutos (multi-fonte)
        df_raw = self._fetch_all_dividends(ticker)
        
        if df_raw.empty:
            return False, "nenhum dividendo encontrado (todas as fontes falharam)"
        
        # 2. Processar dados
        df_processed = self._process_dividends(df_raw, ticker)
        
        if df_processed.empty:
            return False, "nenhum dividendo válido após processamento"
        
        # 3. Agrupar por trimestre
        df_grouped = self._group_by_quarter(df_processed)
        
        if df_grouped.empty:
            return False, "nenhum dividendo após agrupamento trimestral"
        
        # 4. Construir formato horizontal
        df_out = self._build_horizontal(df_grouped)
        
        # 5. Construir JSON detalhado
        json_data = self._build_detalhado_json(df_processed, ticker)
        
        # 6. Salvar arquivo CSV (formato horizontal)
        try:
            csv_path = pasta / "dividendos_trimestrais.csv"
            df_out.to_csv(csv_path, index=False, encoding="utf-8")
        except Exception as e:
            return False, f"erro ao salvar CSV: {e}"
        
        # 7. Salvar arquivo JSON (datas detalhadas)
        try:
            json_path = pasta / "dividendos_detalhado.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            return False, f"erro ao salvar JSON: {e}"
        
        # 8. Estatísticas
        n_periodos = len([c for c in df_out.columns if c != "Dividendos_Pagos"])
        total_dividendos = df_grouped['valor'].sum()
        n_pagamentos = len(df_processed)
        
        if not df_processed.empty and 'data_com' in df_processed.columns:
            periodo_inicio = df_processed['data_com'].min().year
            periodo_fim = df_processed['data_com'].max().year
        else:
            periodo_inicio = periodo_fim = "?"
        
        msg_parts = [
            f"periodos={n_periodos}",
            f"pagamentos={n_pagamentos}",
            f"total=R${total_dividendos:.2f}",
            f"range={periodo_inicio}-{periodo_fim}"
        ]
        
        msg = f"CSV+JSON | {' | '.join(msg_parts)}"
        
        return True, msg


def main():
    parser = argparse.ArgumentParser(
        description="Captura dividendos históricos agrupados por trimestre"
    )
    parser.add_argument(
        "--modo",
        choices=["quantidade", "ticker", "lista", "faixa"],
        default="quantidade",
        help="Modo de seleção: quantidade, ticker, lista, faixa",
    )
    parser.add_argument("--quantidade", default="10", help="Quantidade de empresas")
    parser.add_argument("--ticker", default="", help="Ticker específico")
    parser.add_argument("--lista", default="", help="Lista de tickers separados por vírgula")
    parser.add_argument("--faixa", default="", help="Faixa de linhas: inicio-fim (ex: 1-50)")
    args = parser.parse_args()

    # Tentar carregar mapeamento consolidado, fallback para original
    df = load_mapeamento_consolidado()
    df = df[df["cnpj"].notna()].reset_index(drop=True)

    if args.modo == "quantidade":
        limite = int(args.quantidade)
        df_sel = df.head(limite)

    elif args.modo == "ticker":
        ticker_upper = args.ticker.upper()
        # Buscar ticker em qualquer posição da string de tickers
        df_sel = df[df["ticker"].str.upper().str.contains(ticker_upper, case=False, na=False, regex=False)]

    elif args.modo == "lista":
        tickers = [t.strip().upper() for t in args.lista.split(",") if t.strip()]
        # Buscar cada ticker em qualquer posição
        mask = df["ticker"].str.upper().apply(
            lambda x: any(t in x for t in tickers) if pd.notna(x) else False
        )
        df_sel = df[mask]

    elif args.modo == "faixa":
        inicio, fim = map(int, args.faixa.split("-"))
        df_sel = df.iloc[inicio - 1: fim]

    else:
        df_sel = df.head(10)

    print(f"\n>>> JOB: CAPTURAR DIVIDENDOS TRIMESTRAIS <<<")
    print(f"Modo: {args.modo} | Selecionadas: {len(df_sel)}")
    print("Fontes: B3 API (primária) → OkaneBox → yfinance → CSV local")
    print("Saída: balancos/<TICKER>/dividendos_trimestrais.csv + dividendos_detalhado.json\n")

    capturador = CapturadorDividendos()

    ok_count = 0
    err_count = 0

    for _, row in df_sel.iterrows():
        # Pegar primeiro ticker do grupo (principal)
        ticker_str = str(row["ticker"]).upper().strip()
        ticker = ticker_str.split(';')[0] if ';' in ticker_str else ticker_str

        pasta = get_pasta_balanco(ticker)
        if not pasta.exists():
            err_count += 1
            print(f"❌ {ticker}: pasta {pasta} não existe")
            continue

        try:
            ok, msg = capturador.capturar_e_salvar_ticker(ticker)

            if ok:
                ok_count += 1
                print(f"✅ {ticker}: {msg}")
            else:
                err_count += 1
                print(f"⚠️ {ticker}: {msg}")

        except Exception as e:
            err_count += 1
            print(f"❌ {ticker}: erro ({type(e).__name__}: {e})")

    print("\n" + "=" * 70)
    print(f"Finalizado: OK={ok_count} | ERRO={err_count}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
