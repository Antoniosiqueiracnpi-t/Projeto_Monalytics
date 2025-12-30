"""
CAPTURADOR DE DIVIDENDOS HISTÓRICOS - Projeto Monalytics

Captura dividendos históricos (2020+) usando biblioteca finbr.
Gera JSON por empresa com todos os proventos pagos.

SAÍDA:
- balancos/{TICKER}/dividendos_historico.json

USO:
python src/capturar_dividendos_passados.py --modo quantidade --quantidade 10
python src/capturar_dividendos_passados.py --modo ticker --ticker VALE3
python src/capturar_dividendos_passados.py --modo lista --lista "VALE3,PETR4,ITUB4"
python src/capturar_dividendos_passados.py --modo completo
"""

import finbr
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import argparse
import sys


class CapturadorDividendosHistoricos:
    """
    Captura dividendos históricos usando finbr.
    """
    
    def __init__(self, pasta_output: str = "balancos"):
        self.pasta_output = Path(pasta_output)
        self.empresas_processadas = 0
        self.dividendos_totais = 0
        self.erros = []
    
    def capturar_dividendos(self, ticker: str) -> dict:
        """
        Captura dividendos históricos de um ticker.
        """
        try:
            print(f"  📊 Buscando dividendos históricos de {ticker}...")
            
            # Buscar com finbr
            df = finbr.dividendos(ticker)
            
            if df is None or df.empty:
                print(f"  ⚠️  Sem dividendos históricos para {ticker}")
                return None
            
            # Converter para lista de dicts
            dividendos = []
            for _, row in df.iterrows():
                dividendo = {
                    'data': row['data'].strftime('%Y-%m-%d') if isinstance(row['data'], pd.Timestamp) else str(row['data']),
                    'tipo': row['tipo'],
                    'valor': float(row['valor']),
                    'status': 'pago',
                    'fonte': 'finbr'
                }
                dividendos.append(dividendo)
            
            # Ordenar por data (mais recente primeiro)
            dividendos.sort(key=lambda x: x['data'], reverse=True)
            
            # Calcular estatísticas
            total_bruto = sum(d['valor'] for d in dividendos)
            ultimo_ano = [d for d in dividendos if d['data'] >= f"{datetime.now().year - 1}-01-01"]
            
            resultado = {
                'ticker': ticker,
                'ultima_atualizacao': datetime.now().isoformat() + 'Z',
                'total_dividendos': len(dividendos),
                'dividendos': dividendos,
                'estatisticas': {
                    'total_bruto': round(total_bruto, 2),
                    'total_ultimos_12m': round(sum(d['valor'] for d in ultimo_ano), 2),
                    'quantidade_ultimos_12m': len(ultimo_ano),
                    'data_primeiro': dividendos[-1]['data'] if dividendos else None,
                    'data_ultimo': dividendos[0]['data'] if dividendos else None
                }
            }
            
            print(f"  ✅ {ticker}: {len(dividendos)} dividendos encontrados")
            print(f"     Total histórico: R$ {total_bruto:.2f}")
            print(f"     Últimos 12M: R$ {resultado['estatisticas']['total_ultimos_12m']:.2f}")
            
            self.empresas_processadas += 1
            self.dividendos_totais += len(dividendos)
            
            return resultado
            
        except Exception as e:
            erro = f"Erro ao processar {ticker}: {str(e)}"
            print(f"  ❌ {erro}")
            self.erros.append(erro)
            return None
    
    def salvar_json(self, ticker: str, dados: dict):
        """
        Salva JSON de dividendos históricos.
        """
        if dados is None:
            return
        
        # Criar pasta do ticker
        pasta_ticker = self.pasta_output / ticker
        pasta_ticker.mkdir(parents=True, exist_ok=True)
        
        # Salvar JSON
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
        print(f"📊 CAPTURANDO DIVIDENDOS HISTÓRICOS")
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
        
        if self.erros:
            print(f"\n❌ Erros encontrados: {len(self.erros)}")
            for erro in self.erros[:5]:  # Mostrar apenas 5 primeiros
                print(f"   - {erro}")
            if len(self.erros) > 5:
                print(f"   ... e mais {len(self.erros) - 5} erros")


# ============================================================================
# MAIN
# ============================================================================

def carregar_mapeamento(arquivo: str = "mapeamento_b3_consolidado.csv") -> list:
    """
    Carrega lista de tickers do CSV.
    """
    try:
        import pandas as pd
        df = pd.read_csv(arquivo, sep=';')
        return df['ticker'].unique().tolist()
    except Exception as e:
        print(f"❌ Erro ao carregar mapeamento: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description='Capturar dividendos históricos')
    parser.add_argument('--modo', choices=['quantidade', 'ticker', 'lista', 'completo'], 
                       default='quantidade', help='Modo de captura')
    parser.add_argument('--quantidade', type=int, default=10, 
                       help='Quantidade de empresas (modo quantidade)')
    parser.add_argument('--ticker', type=str, 
                       help='Ticker específico (modo ticker)')
    parser.add_argument('--lista', type=str, 
                       help='Lista de tickers separados por vírgula (modo lista)')
    
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
        tickers_selecionados = tickers[:args.quantidade]
        capturador.processar_lista(tickers_selecionados)
    
    elif args.modo == 'completo':
        tickers = carregar_mapeamento()
        if not tickers:
            print("❌ Erro: Não foi possível carregar lista de tickers")
            sys.exit(1)
        capturador.processar_lista(tickers)


if __name__ == "__main__":
    main()
