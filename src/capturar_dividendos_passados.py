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
        EXATAMENTE como a função do usuário que funcionou.
        """
        try:
            from finbr import fundamentus
            
            ticker_clean = ticker.upper().replace('.SA', '')
            proventos = fundamentus.proventos(ticker_clean)
            
            if not proventos:
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
        except:
            return pd.DataFrame()
    
    def _fetch_statusinvest(self, ticker: str) -> pd.DataFrame:
        """
        Busca dividendos usando Status Invest (backup).
        """
        try:
            from finbr.statusinvest import acao
            
            ticker_clean = ticker.upper().replace('.SA', '')
            dividendos = acao.dividendos(ticker_clean)
            
            if dividendos is None or dividendos.empty:
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
        except:
            return pd.DataFrame()
    
    def capturar_dividendos(self, ticker: str) -> dict:
        """
        Captura dividendos de um ticker usando múltiplas fontes.
        """
        print(f"  📊 Buscando dividendos históricos de {ticker}...")
        
        # Tentar fundamentus primeiro
        df = self._fetch_fundamentus(ticker)
        
        # Se não encontrou, tentar statusinvest
        if df.empty:
            print(f"    Tentando fonte alternativa...")
            df = self._fetch_statusinvest(ticker)
        
        if df.empty:
            print(f"  ⚠️  Sem dividendos históricos para {ticker}")
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
            'ticker': ticker,
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
        
        print(f"  ✅ {ticker}: {len(dividendos)} dividendos encontrados")
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
        
        pasta_ticker = self.pasta_output / ticker
        pasta_ticker.mkdir(parents=True, exist_ok=True)
        
        arquivo = pasta_ticker / "dividendos_historico.json"
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        print(f"  💾 Salvo: {arquivo}")
    
    def processar_ticker(self, ticker: str):
        """
        Processa um único ticker.
        """
        print(f"\n{'='*70}")
        print(f"📈 {ticker}")
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
    """Carrega lista de tickers do CSV."""
    try:
        df = pd.read_csv(arquivo, sep=';')
        return df['ticker'].unique().tolist()
    except:
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
        tickers = [t.strip() for t in args.lista.split(',')]
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
