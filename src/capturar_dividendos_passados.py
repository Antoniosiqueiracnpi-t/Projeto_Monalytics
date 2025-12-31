"""
CAPTURADOR DE DIVIDENDOS HISTÓRICOS - Projeto Monalytics

Fontes de dados (em ordem de prioridade):
1. API B3 Oficial (com retry para erros 5xx)
2. finbr/fundamentus (fallback - funciona no Colab)
3. finbr/statusinvest (fallback - funciona no Colab)

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

# Suprimir warnings SSL
warnings.filterwarnings('ignore')
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass


def extrair_ticker_principal(ticker_raw: str) -> str:
    """
    Extrai o ticker principal de uma string que pode conter múltiplos tickers.
    """
    if not ticker_raw:
        return ""
    
    ticker = str(ticker_raw)
    ticker = ticker.strip().strip('"').strip("'")
    ticker = ticker.replace('.SA', '').replace('.sa', '')
    
    if ';' in ticker:
        ticker = ticker.split(';')[0]
    
    ticker = ticker.strip().upper()
    return ticker


def extrair_codigo_negociacao(ticker: str) -> str:
    """
    Extrai código de negociação (sem número) do ticker.
    PETR4 → PETR, VALE3 → VALE, TAEE11 → TAEE
    """
    ticker_clean = extrair_ticker_principal(ticker)
    codigo = ''.join([c for c in ticker_clean if not c.isdigit()])
    return codigo


def request_with_retry(url: str, timeout: int = 15, max_retries: int = 3) -> requests.Response:
    """
    Faz request HTTP com retry automático para erros 5xx.
    Usa backoff exponencial: 1s, 2s, 4s
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout, verify=False)
            
            # Se for erro 5xx, fazer retry
            if response.status_code >= 500:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 1, 2, 4 segundos
                    print(f"      ⏳ Erro {response.status_code}, aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
            
            return response
            
        except requests.exceptions.Timeout as e:
            last_exception = e
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"      ⏳ Timeout, aguardando {wait_time}s...")
                time.sleep(wait_time)
                continue
        except requests.exceptions.RequestException as e:
            last_exception = e
            break
    
    # Se chegou aqui, todas as tentativas falharam
    if last_exception:
        raise last_exception
    return response


class CapturadorDividendosHistoricos:
    """
    Captura dividendos históricos usando múltiplas fontes.
    Prioridade: API B3 (com retry) → finbr/fundamentus → finbr/statusinvest
    """
    
    def __init__(self, pasta_output: str = "balancos"):
        self.pasta_output = Path(pasta_output)
        self.empresas_processadas = 0
        self.dividendos_totais = 0
        self.timeout = 15
        self.max_retries = 3
    
    def _fetch_b3_api(self, ticker: str) -> pd.DataFrame:
        """
        Busca dividendos da API B3 Oficial com retry automático.
        """
        try:
            ticker_clean = extrair_ticker_principal(ticker)
            codigo = extrair_codigo_negociacao(ticker)
            
            if not codigo:
                print(f"    [B3 API] ⚠️ Código de negociação vazio")
                return pd.DataFrame()
            
            # ETAPA 1: Buscar tradingName
            params = {
                "language": "pt-br",
                "pageNumber": 1,
                "pageSize": 20,
                "company": codigo
            }
            
            params_b64 = base64.b64encode(json.dumps(params).encode()).decode()
            url = f"https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetInitialCompanies/{params_b64}"
            
            response = request_with_retry(url, self.timeout, self.max_retries)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                print(f"    [B3 API] ⚠️ Empresa não encontrada para {codigo}")
                return pd.DataFrame()
            
            # Encontrar a empresa correta
            trading_name = None
            for company in results:
                if company.get('issuingCompany', '').upper() == codigo.upper():
                    trading_name = company.get('tradingName', '')
                    trading_name = trading_name.replace('/', '').replace('.', '')
                    break
            
            if not trading_name:
                trading_name = results[0].get('tradingName', '').replace('/', '').replace('.', '')
            
            if not trading_name:
                print(f"    [B3 API] ⚠️ Trading name não encontrado para {codigo}")
                return pd.DataFrame()
            
            # ETAPA 2: Buscar dividendos (com paginação)
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
                
                response = request_with_retry(url, self.timeout, self.max_retries)
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
                print(f"    [B3 API] ⚠️ Nenhum dividendo encontrado para {trading_name}")
                return pd.DataFrame()
            
            # Converter para DataFrame
            df = pd.DataFrame(all_dividends)
            df['Data_Com'] = pd.to_datetime(df['lastDatePrior'], errors='coerce')
            df['Data_Pagamento'] = pd.to_datetime(df['paymentDate'], errors='coerce')
            df['Valor'] = pd.to_numeric(df['rate'], errors='coerce')
            df['Tipo'] = df['corporateActionLabel']
            
            df = df[['Data_Com', 'Data_Pagamento', 'Valor', 'Tipo']].dropna(subset=['Data_Com'])
            df = df.sort_values('Data_Com', ascending=False).reset_index(drop=True)
            
            print(f"    [B3 API] ✓ {len(df)} proventos")
            return df
            
        except requests.exceptions.HTTPError as e:
            print(f"    [B3 API] ✗ HTTP Error: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"    [B3 API] ✗ Erro: {type(e).__name__}: {e}")
            return pd.DataFrame()
    
    def _fetch_fundamentus(self, ticker: str) -> pd.DataFrame:
        """
        Busca dividendos usando finbr fundamentus.
        FALLBACK: Funciona no Colab, bloqueado no GitHub Actions (403).
        """
        try:
            from finbr import fundamentus
            
            ticker_clean = extrair_ticker_principal(ticker)
            
            if not ticker_clean:
                return pd.DataFrame()
            
            proventos = fundamentus.proventos(ticker_clean)
            
            if not proventos:
                print(f"    [fundamentus] ⚠️ Nenhum provento retornado")
                return pd.DataFrame()
            
            df = pd.DataFrame(proventos)
            df['Data_Com'] = pd.to_datetime(df['data'])
            df['Data_Pagamento'] = pd.to_datetime(df['data_pagamento'])
            df['Valor'] = df['valor']
            df['Tipo'] = df['tipo']
            
            df = df[['Data_Com', 'Data_Pagamento', 'Valor', 'Tipo']].dropna(subset=['Data_Com'])
            df = df.sort_values('Data_Com', ascending=False).reset_index(drop=True)
            
            print(f"    [fundamentus] ✓ {len(df)} proventos")
            return df
            
        except Exception as e:
            print(f"    [fundamentus] ✗ Erro: {type(e).__name__}: {e}")
            return pd.DataFrame()
    
    def _fetch_statusinvest(self, ticker: str) -> pd.DataFrame:
        """
        Busca dividendos usando Status Invest (backup).
        FALLBACK: Funciona no Colab, bloqueado no GitHub Actions (403).
        """
        try:
            from finbr.statusinvest import acao
            
            ticker_clean = extrair_ticker_principal(ticker)
            
            if not ticker_clean:
                return pd.DataFrame()
            
            dividendos = acao.dividendos(ticker_clean)
            
            if dividendos is None or dividendos.empty:
                print(f"    [statusinvest] ⚠️ Nenhum dividendo retornado")
                return pd.DataFrame()
            
            df = dividendos.copy()
            
            if 'data' in df.columns:
                df['Data_Com'] = pd.to_datetime(df['data'])
            if 'datapagamento' in df.columns or 'data_pagamento' in df.columns:
                col_pag = 'datapagamento' if 'datapagamento' in df.columns else 'data_pagamento'
                df['Data_Pagamento'] = pd.to_datetime(df[col_pag])
            if 'valor' in df.columns:
                df['Valor'] = df['valor']
            if 'tipo' in df.columns:
                df['Tipo'] = df['tipo']
            
            df = df[['Data_Com', 'Data_Pagamento', 'Valor', 'Tipo']].dropna(subset=['Data_Com'])
            df = df.sort_values('Data_Com', ascending=False).reset_index(drop=True)
            
            print(f"    [statusinvest] ✓ {len(df)} proventos")
            return df
            
        except Exception as e:
            print(f"    [statusinvest] ✗ Erro: {type(e).__name__}: {e}")
            return pd.DataFrame()
    
    def capturar_dividendos(self, ticker: str) -> dict:
        """
        Captura dividendos de um ticker usando múltiplas fontes.
        Ordem: API B3 → fundamentus → statusinvest
        """
        ticker_clean = extrair_ticker_principal(ticker)
        print(f"  📊 Buscando dividendos históricos de {ticker_clean}...")
        
        # 1. Tentar API B3 primeiro (funciona no GitHub Actions)
        df = self._fetch_b3_api(ticker)
        
        # 2. Se falhou, tentar fundamentus
        if df.empty:
            print(f"    Tentando fonte alternativa (fundamentus)...")
            df = self._fetch_fundamentus(ticker)
        
        # 3. Se ainda falhou, tentar statusinvest
        if df.empty:
            print(f"    Tentando fonte alternativa (statusinvest)...")
            df = self._fetch_statusinvest(ticker)
        
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
                'valor': float(row['Valor']),
                'status': 'pago',
                'fonte': 'b3_api'
            }
            dividendos.append(dividendo)
        
        # Calcular estatísticas
        total_bruto = sum(d['valor'] for d in dividendos)
        ultimo_ano = [d for d in dividendos if d.get('data', '') >= f"{datetime.now().year - 1}-01-01"]
        
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
        """
        Salva JSON de dividendos históricos.
        """
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
        """
        Processa um único ticker.
        """
        ticker_clean = extrair_ticker_principal(ticker)
        print(f"\n{'='*70}")
        print(f"📈 {ticker_clean}")
        print(f"{'='*70}")
        
        dados = self.capturar_dividendos(ticker)
        if dados:
            self.salvar_json(ticker, dados)
    
    def processar_lista(self, tickers: list):
        """
        Processa lista de tickers.
        """
        print(f"\n{'='*70}")
        print(f"📊 CAPTURANDO DIVIDENDOS HISTÓRICOS")
        print(f"{'='*70}")
        print(f"Fontes: API B3 (primária, com retry) → fundamentus → statusinvest")
        print(f"Total de tickers: {len(tickers)}")
        
        for ticker in tickers:
            self.processar_ticker(ticker)
        
        self.imprimir_resumo()
    
    def imprimir_resumo(self):
        """
        Imprime resumo final.
        """
        print(f"\n{'='*70}")
        print(f"📊 RESUMO FINAL")
        print(f"{'='*70}")
        print(f"✅ Empresas processadas: {self.empresas_processadas}")
        print(f"✅ Total de dividendos: {self.dividendos_totais}")


def carregar_mapeamento(arquivo: str = "mapeamento_b3_consolidado.csv") -> list:
    """
    Carrega lista de tickers do CSV.
    """
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
        tickers = carregar_mapeamento()
        if not tickers:
            print("❌ Erro: Não foi possível carregar lista de tickers")
            sys.exit(1)
        capturador.processar_lista(tickers[:args.quantidade])
    
    elif args.modo == 'completo':
        tickers = carregar_mapeamento()
        if not tickers:
            print("❌ Erro: Não foi possível carregar lista de tickers")
            sys.exit(1)
        capturador.processar_lista(tickers)


if __name__ == "__main__":
    main()
