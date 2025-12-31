"""
CAPTURADOR DE DIVIDENDOS HISTÓRICOS - Projeto Monalytics

Usa finbr para capturar dividendos históricos de múltiplas fontes:
1. fundamentus.proventos() - Primeira opção
2. statusinvest.acao.dividendos() - Backup

IMPORTANTE: Roda 100% ONLINE (GitHub Actions ou ambiente sem proxy)

USO:
python src/capturar_dividendos_passados.py --modo lista --lista "BBAS3,ITUB4,VALE3"
python src/capturar_dividendos_passados.py --modo completo
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import argparse
import sys


def extrair_ticker_principal(ticker_raw: str) -> str:
    """
    Extrai o ticker principal de uma string que pode conter múltiplos tickers.
    
    Formatos suportados:
    - Simples: "PETR4" → "PETR4"
    - Com sufixo: "PETR4.SA" → "PETR4"
    - Compostos: "TAEE11;TAEE3;TAEE4" → "TAEE11"
    - Com aspas: '"SAPR11;SAPR3;SAPR4"' → "SAPR11"
    - Espaços: " VALE3 " → "VALE3"
    
    Returns:
        str: Ticker limpo e normalizado (primeiro da lista se houver múltiplos)
    """
    if not ticker_raw:
        return ""
    
    # Converter para string se necessário
    ticker = str(ticker_raw)
    
    # Remover aspas duplas (início e fim)
    ticker = ticker.strip().strip('"').strip("'")
    
    # Remover sufixo .SA
    ticker = ticker.replace('.SA', '').replace('.sa', '')
    
    # Se tiver múltiplos tickers separados por ;, pegar o primeiro
    if ';' in ticker:
        ticker = ticker.split(';')[0]
    
    # Limpar espaços finais
    ticker = ticker.strip().upper()
    
    return ticker


class CapturadorDividendosHistoricos:
    """
    Captura dividendos históricos usando finbr (fundamentus + statusinvest).
    """
    
    def __init__(self, pasta_output: str = "balancos"):
        self.pasta_output = Path(pasta_output)
        self.empresas_processadas = 0
        self.dividendos_totais = 0
    
    def _fetch_fundamentus(self, ticker: str) -> pd.DataFrame:
        """
        Busca dividendos usando finbr fundamentus.
        """
        try:
            from finbr import fundamentus
            
            # Extrair ticker principal (limpo)
            ticker_clean = extrair_ticker_principal(ticker)
            
            if not ticker_clean:
                print(f"    [fundamentus] ⚠️ Ticker vazio após limpeza")
                return pd.DataFrame()
            
            proventos = fundamentus.proventos(ticker_clean)
            
            if not proventos:
                print(f"    [fundamentus] ⚠️ Nenhum provento retornado para {ticker_clean}")
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
        """
        try:
            from finbr.statusinvest import acao
            
            # Extrair ticker principal (limpo)
            ticker_clean = extrair_ticker_principal(ticker)
            
            if not ticker_clean:
                print(f"    [statusinvest] ⚠️ Ticker vazio após limpeza")
                return pd.DataFrame()
            
            dividendos = acao.dividendos(ticker_clean)
            
            if dividendos is None or dividendos.empty:
                print(f"    [statusinvest] ⚠️ Nenhum dividendo retornado para {ticker_clean}")
                return pd.DataFrame()
            
            # Padronizar colunas
            df = dividendos.copy()
            
            # Mapear colunas do StatusInvest
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
        """
        # Extrair ticker limpo para exibição
        ticker_clean = extrair_ticker_principal(ticker)
        print(f"  📊 Buscando dividendos históricos de {ticker_clean}...")
        
        # Tentar fundamentus primeiro
        df = self._fetch_fundamentus(ticker)
        
        # Se não encontrou, tentar statusinvest
        if df.empty:
            print(f"    Tentando fonte alternativa...")
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
                'fonte': 'finbr'
            }
            dividendos.append(dividendo)
        
        # Calcular estatísticas
        total_bruto = sum(d['valor'] for d in dividendos)
        ultimo_ano = [d for d in dividendos if d.get('data', '') >= f"{datetime.now().year - 1}-01-01"]
        
        resultado = {
            'ticker': ticker_clean,  # Usar ticker limpo
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
        Usa ticker limpo para nome da pasta.
        """
        if dados is None:
            return
        
        # Usar ticker limpo para a pasta
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
        print(f"📊 CAPTURANDO DIVIDENDOS HISTÓRICOS (ONLINE)")
        print(f"{'='*70}")
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
    Extrai apenas o ticker principal de cada linha.
    """
    try:
        df = pd.read_csv(arquivo, sep=';', encoding='utf-8-sig')
        
        # Extrair ticker principal de cada linha
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
    parser = argparse.ArgumentParser(description='Capturar dividendos históricos (ONLINE)')
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
        # Extrair ticker principal de cada item da lista
        tickers = [extrair_ticker_principal(t) for t in args.lista.split(',')]
        tickers = [t for t in tickers if t]  # Remover vazios
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
