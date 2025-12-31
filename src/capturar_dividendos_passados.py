"""
CAPTURADOR DE DIVIDENDOS HISTÓRICOS - Projeto Monalytics

Usa o mapeamento pré-gerado (mapeamento_tradingname_b3.csv) para buscar
dividendos diretamente na API B3 sem erros de nome.

IMPORTANTE: Rode primeiro o gerar_mapeamento_b3_tradingname.py para criar o mapeamento.

USO:
python src/capturar_dividendos_passados.py --modo lista --lista "BBAS3,ITUB4,VALE3"
python src/capturar_dividendos_passados.py --modo completo
"""

import json
import base64
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime
import argparse
import sys
import warnings
import time

warnings.filterwarnings('ignore')
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass


def extrair_ticker_principal(ticker_raw: str) -> str:
    """Extrai ticker limpo."""
    if not ticker_raw:
        return ""
    ticker = str(ticker_raw).strip().strip('"').strip("'")
    ticker = ticker.replace('.SA', '').replace('.sa', '')
    if ';' in ticker:
        ticker = ticker.split(';')[0]
    return ticker.strip().upper()


def carregar_mapeamento_tradingname(arquivo: str = "mapeamento_tradingname_b3.csv") -> dict:
    """
    Carrega mapeamento código → trading_name.
    
    Usa o CÓDIGO (sem número) como chave para funcionar com qualquer classe:
    PETR3, PETR4 → código PETR → trading_name PETROBRAS
    
    Returns:
        dict: {codigo: trading_name}
    """
    try:
        df = pd.read_csv(arquivo, sep=';', encoding='utf-8-sig')
        # Filtrar apenas os que têm status 'ok'
        df_ok = df[df['status'] == 'ok']
        # Usar código (sem número) como chave
        mapeamento = dict(zip(df_ok['codigo'].str.upper(), df_ok['trading_name']))
        return mapeamento
    except Exception as e:
        print(f"⚠️ Erro ao carregar mapeamento: {e}")
        return {}


def extrair_codigo(ticker: str) -> str:
    """
    Extrai código de negociação (sem número).
    PETR4 → PETR, VALE3 → VALE, TAEE11 → TAEE, KLBN11 → KLBN
    """
    ticker_clean = extrair_ticker_principal(ticker)
    return ''.join([c for c in ticker_clean if not c.isdigit()])


class CapturadorDividendosHistoricos:
    """
    Captura dividendos históricos usando API B3 com mapeamento pré-gerado.
    """
    
    def __init__(self, pasta_output: str = "balancos"):
        self.pasta_output = Path(pasta_output)
        self.empresas_processadas = 0
        self.dividendos_totais = 0
        self.timeout = 15
        self.max_retries = 3
        
        # Carregar mapeamento
        self.mapeamento = carregar_mapeamento_tradingname()
        if self.mapeamento:
            print(f"✓ Mapeamento carregado: {len(self.mapeamento)} códigos de negociação")
        else:
            print("⚠️ Mapeamento não encontrado")
    
    def _request_with_retry(self, url: str) -> requests.Response:
        """Faz request com retry para erros 5xx."""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, timeout=self.timeout, verify=False)
                
                if response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        print(f"      ⏳ Erro {response.status_code}, aguardando {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                
                return response
                
            except requests.exceptions.Timeout as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"      ⏳ Timeout, aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
            except Exception as e:
                last_error = e
                break
        
        raise last_error if last_error else Exception("Request failed")
    
    def _fetch_b3_api(self, ticker: str) -> pd.DataFrame:
        """
        Busca dividendos da API B3 usando trading_name do mapeamento.
        Usa o código (sem número) para funcionar com qualquer classe de ação.
        """
        try:
            ticker_clean = extrair_ticker_principal(ticker)
            codigo = extrair_codigo(ticker)
            
            # Buscar trading_name pelo código (não pelo ticker completo)
            trading_name = self.mapeamento.get(codigo)
            
            if not trading_name:
                print(f"    [B3 API] ⚠️ Código {codigo} (de {ticker_clean}) não está no mapeamento")
                return pd.DataFrame()
            
            # Buscar dividendos (paginado)
            all_dividends = []
            page = 1
            
            while page <= 50:
                params = {
                    "language": "pt-br",
                    "pageNumber": page,
                    "pageSize": 120,
                    "tradingName": trading_name
                }
                
                params_b64 = base64.b64encode(json.dumps(params).encode()).decode()
                url = f"https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetListedCashDividends/{params_b64}"
                
                response = self._request_with_retry(url)
                response.raise_for_status()
                
                data = response.json()
                dividends = data.get('results', [])
                
                if not dividends:
                    break
                
                all_dividends.extend(dividends)
                
                if len(dividends) < 120:
                    break
                
                page += 1
            
            if not all_dividends:
                print(f"    [B3 API] ⚠️ Nenhum dividendo para {trading_name}")
                return pd.DataFrame()
            
            # Converter para DataFrame
            # Campos da API B3:
            # - lastDatePriorEx: data ex-dividendo
            # - valueCash: valor por ação (formato brasileiro: "0,123")
            # - corporateAction: tipo (DIVIDENDO, JRS CAP PROPRIO, etc)
            # - dateApproval: data de aprovação
            
            df = pd.DataFrame(all_dividends)
            
            # Data ex-dividendo
            if 'lastDatePriorEx' in df.columns:
                df['Data_Com'] = pd.to_datetime(df['lastDatePriorEx'], format='%d/%m/%Y', errors='coerce')
            elif 'lastDateTimePriorEx' in df.columns:
                df['Data_Com'] = pd.to_datetime(df['lastDateTimePriorEx'], errors='coerce')
            else:
                print(f"    [B3 API] ⚠️ Coluna de data não encontrada")
                return pd.DataFrame()
            
            # Data de aprovação como data de pagamento (aproximação)
            if 'dateApproval' in df.columns:
                df['Data_Pagamento'] = pd.to_datetime(df['dateApproval'], format='%d/%m/%Y', errors='coerce')
            else:
                df['Data_Pagamento'] = df['Data_Com']
            
            # Valor - converter de formato brasileiro
            if 'valueCash' in df.columns:
                df['Valor'] = df['valueCash'].apply(
                    lambda x: float(str(x).replace(',', '.')) if pd.notna(x) else 0
                )
            else:
                print(f"    [B3 API] ⚠️ Coluna de valor não encontrada")
                return pd.DataFrame()
            
            # Tipo
            df['Tipo'] = df.get('corporateAction', 'DIVIDENDO')
            
            df = df[['Data_Com', 'Data_Pagamento', 'Valor', 'Tipo']].dropna(subset=['Data_Com'])
            df = df[df['Valor'] > 0]  # Remover valores zero
            df = df.sort_values('Data_Com', ascending=False).reset_index(drop=True)
            
            print(f"    [B3 API] ✓ {len(df)} proventos ({trading_name})")
            return df
            
        except requests.exceptions.HTTPError as e:
            print(f"    [B3 API] ✗ HTTP Error: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"    [B3 API] ✗ Erro: {type(e).__name__}: {e}")
            return pd.DataFrame()
    
    def capturar_dividendos(self, ticker: str) -> dict:
        """
        Captura dividendos de um ticker.
        """
        ticker_clean = extrair_ticker_principal(ticker)
        print(f"  📊 Buscando dividendos históricos de {ticker_clean}...")
        
        df = self._fetch_b3_api(ticker)
        
        if df.empty:
            print(f"  ⚠️  Sem dividendos históricos para {ticker_clean}")
            return None
        
        # Converter para lista de dicts
        dividendos = []
        for _, row in df.iterrows():
            dividendo = {
                'data': row['Data_Com'].strftime('%Y-%m-%d') if pd.notna(row['Data_Com']) else None,
                'data_pagamento': row['Data_Pagamento'].strftime('%Y-%m-%d') if pd.notna(row['Data_Pagamento']) else None,
                'tipo': str(row['Tipo']),
                'valor': round(float(row['Valor']), 6),
                'status': 'pago',
                'fonte': 'b3_api'
            }
            dividendos.append(dividendo)
        
        # Calcular estatísticas
        total_bruto = sum(d['valor'] for d in dividendos)
        data_limite = f"{datetime.now().year - 1}-01-01"
        ultimo_ano = [d for d in dividendos if d.get('data', '') >= data_limite]
        
        resultado = {
            'ticker': ticker_clean,
            'ultima_atualizacao': datetime.now().isoformat() + 'Z',
            'total_dividendos': len(dividendos),
            'dividendos': dividendos,
            'estatisticas': {
                'total_bruto': round(total_bruto, 2),
                'total_ultimos_12m': round(sum(d['valor'] for d in ultimo_ano), 2),
                'quantidade_ultimos_12m': len(ultimo_ano),
                'data_primeiro': dividendos[-1].get('data') if dividendos else None,
                'data_ultimo': dividendos[0].get('data') if dividendos else None
            }
        }
        
        print(f"  ✅ {ticker_clean}: {len(dividendos)} dividendos encontrados")
        print(f"     Total histórico: R$ {total_bruto:.2f}")
        print(f"     Últimos 12M: R$ {resultado['estatisticas']['total_ultimos_12m']:.2f}")
        
        self.empresas_processadas += 1
        self.dividendos_totais += len(dividendos)
        
        return resultado
    
    def salvar_json(self, ticker: str, dados: dict):
        """Salva JSON de dividendos históricos."""
        if dados is None:
            return
        
        ticker_clean = extrair_ticker_principal(ticker)
        pasta_ticker = self.pasta_output / ticker_clean
        pasta_ticker.mkdir(parents=True, exist_ok=True)
        
        arquivo = pasta_ticker / "dividendos_historico.json"
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        print(f"  💾 Salvo: {arquivo}")
    
    def processar_ticker(self, ticker: str):
        """Processa um único ticker."""
        ticker_clean = extrair_ticker_principal(ticker)
        print(f"\n{'='*70}")
        print(f"📈 {ticker_clean}")
        print(f"{'='*70}")
        
        dados = self.capturar_dividendos(ticker)
        if dados:
            self.salvar_json(ticker, dados)
    
    def processar_lista(self, tickers: list):
        """Processa lista de tickers."""
        print(f"\n{'='*70}")
        print(f"📊 CAPTURANDO DIVIDENDOS HISTÓRICOS (API B3)")
        print(f"{'='*70}")
        print(f"Total de tickers: {len(tickers)}")
        
        for ticker in tickers:
            self.processar_ticker(ticker)
        
        self.imprimir_resumo()
    
    def imprimir_resumo(self):
        """Imprime resumo final."""
        print(f"\n{'='*70}")
        print(f"📊 RESUMO FINAL")
        print(f"{'='*70}")
        print(f"✅ Empresas processadas: {self.empresas_processadas}")
        print(f"✅ Total de dividendos: {self.dividendos_totais}")


def carregar_mapeamento_empresas(arquivo: str = "mapeamento_b3_consolidado.csv") -> list:
    """Carrega lista de tickers do CSV de empresas."""
    try:
        df = pd.read_csv(arquivo, sep=';', encoding='utf-8-sig')
        tickers = []
        for ticker_raw in df['ticker'].unique():
            ticker_clean = extrair_ticker_principal(ticker_raw)
            if ticker_clean:
                tickers.append(ticker_clean)
        return tickers
    except Exception as e:
        print(f"⚠️ Erro ao carregar mapeamento: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description='Capturar dividendos históricos')
    parser.add_argument('--modo', choices=['quantidade', 'ticker', 'lista', 'completo'],
                       default='quantidade')
    parser.add_argument('--quantidade', type=int, default=10)
    parser.add_argument('--ticker', type=str)
    parser.add_argument('--lista', type=str)
    
    args = parser.parse_args()
    
    capturador = CapturadorDividendosHistoricos()
    
    if args.modo == 'ticker':
        if not args.ticker:
            print("❌ Erro: --ticker é obrigatório no modo 'ticker'")
            sys.exit(1)
        capturador.processar_ticker(args.ticker)
    
    elif args.modo == 'lista':
        if not args.lista:
            print("❌ Erro: --lista é obrigatório no modo 'lista'")
            sys.exit(1)
        tickers = [extrair_ticker_principal(t) for t in args.lista.split(',')]
        tickers = [t for t in tickers if t]
        capturador.processar_lista(tickers)
    
    elif args.modo == 'quantidade':
        tickers = carregar_mapeamento_empresas()
        if not tickers:
            print("❌ Erro: Não foi possível carregar lista de tickers")
            sys.exit(1)
        capturador.processar_lista(tickers[:args.quantidade])
    
    elif args.modo == 'completo':
        tickers = carregar_mapeamento_empresas()
        if not tickers:
            print("❌ Erro: Não foi possível carregar lista de tickers")
            sys.exit(1)
        capturador.processar_lista(tickers)


if __name__ == "__main__":
    main()
