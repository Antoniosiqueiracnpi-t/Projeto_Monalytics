"""
CAPTURADOR DE DIVIDENDOS FUTUROS - Projeto Monalytics

Usa finbr para capturar dividendos futuros de múltiplas fontes:
1. b3.plantao_noticias.get() - Notícias B3 sobre dividendos
2. statusinvest.acao.dividendos() - Incluem dividendos provisionados

IMPORTANTE: Roda 100% ONLINE (GitHub Actions ou ambiente sem proxy)

USO:
python src/capturar_dividendos_futuros.py --modo lista --lista "BBAS3,ITUB4,VALE3"
python src/capturar_dividendos_futuros.py --modo completo
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import sys
import re


class CapturadorDividendosFuturos:
    """
    Captura dividendos futuros usando finbr (B3 notícias + StatusInvest).
    """
    
    def __init__(self, pasta_output: str = "balancos"):
        self.pasta_output = Path(pasta_output)
        self.empresas_processadas = 0
        self.dividendos_totais = 0
        self.noticias_b3_cache = None
    
    def buscar_noticias_b3(self):
        """
        Busca notícias B3 dos últimos 90 dias (cache).
        """
        if self.noticias_b3_cache is not None:
            return self.noticias_b3_cache
        
        try:
            from finbr.b3 import plantao_noticias
            
            # Buscar últimos 90 dias
            fim = datetime.now()
            inicio = fim - timedelta(days=90)
            
            print(f"  📰 Buscando notícias B3 ({inicio.strftime('%Y-%m-%d')} a {fim.strftime('%Y-%m-%d')})...")
            noticias = plantao_noticias.get(inicio=inicio, fim=fim)
            
            self.noticias_b3_cache = noticias
            print(f"  ✅ {len(noticias) if not noticias else 0} notícias B3 carregadas")
            
            return noticias
        except:
            print(f"  ⚠️  Erro ao buscar notícias B3")
            return []
    
    def filtrar_noticias_ticker(self, ticker: str, noticias: list) -> list:
        """
        Filtra notícias relacionadas ao ticker e categoria Dividendos.
        """
        ticker_clean = ticker.upper().replace('.SA', '').replace('3', '').replace('4', '')
        
        noticias_ticker = []
        for noticia in noticias:
            # Verificar se menciona o ticker
            titulo = getattr(noticia, 'titulo', '')
            categoria = getattr(noticia, 'categoria', '')
            
            if ticker_clean in titulo.upper() and 'DIVID' in categoria.upper():
                noticias_ticker.append(noticia)
        
        return noticias_ticker
    
    def parse_noticia(self, noticia) -> dict:
        """
        Extrai informações de dividendo de uma notícia.
        """
        titulo = getattr(noticia, 'titulo', '')
        headline = getattr(noticia, 'headline', '')
        texto = f"{titulo} {headline}"
        
        # Detectar tipo
        if 'JCP' in texto.upper() or 'JUROS SOBRE CAPITAL' in texto.upper():
            tipo = 'JCP'
        else:
            tipo = 'Dividendos'
        
        # Extrair valor
        valor_match = re.search(r'R\$\s*(\d+[.,]\d+)', texto)
        valor = float(valor_match.group(1).replace(',', '.')) if valor_match else None
        
        # Extrair datas
        datas = re.findall(r'(\d{2}/\d{2}/\d{4})', texto)
        datas_convertidas = []
        for d in datas:
            try:
                dia, mes, ano = d.split('/')
                data_iso = f"{ano}-{mes}-{dia}"
                # Só adicionar se for data futura
                if data_iso >= datetime.now().strftime('%Y-%m-%d'):
                    datas_convertidas.append(data_iso)
            except:
                pass
        
        data_pagamento = datas_convertidas[0] if datas_convertidas else None
        
        return {
            'tipo': tipo,
            'valor': valor,
            'data_pagamento': data_pagamento,
            'data_anuncio': getattr(noticia, 'data', None),
            'fonte_url': getattr(noticia, 'url', None)
        }
    
    def capturar_futuros_noticias(self, ticker: str) -> list:
        """
        Captura dividendos futuros de notícias B3.
        """
        noticias = self.buscar_noticias_b3()
        
        if not noticias:
            return []
        
        # Filtrar notícias do ticker
        noticias_ticker = self.filtrar_noticias_ticker(ticker, noticias)
        
        if not noticias_ticker:
            return []
        
        print(f"    [noticias_b3] ✓ {len(noticias_ticker)} notícias de dividendos")
        
        # Parsear notícias
        dividendos = []
        for noticia in noticias_ticker:
            parsed = self.parse_noticia(noticia)
            if parsed['valor'] and parsed['data_pagamento']:
                dividendos.append({
                    'ticker': ticker,
                    'tipo': parsed['tipo'],
                    'valor': parsed['valor'],
                    'data_pagamento': parsed['data_pagamento'],
                    'data_anuncio': parsed['data_anuncio'],
                    'status': 'provisionado',
                    'fonte': 'noticias_b3',
                    'fonte_url': parsed['fonte_url']
                })
        
        return dividendos
    
    def capturar_futuros_statusinvest(self, ticker: str) -> list:
        """
        Captura dividendos futuros do StatusInvest.
        """
        try:
            from finbr.statusinvest import acao
            
            ticker_clean = ticker.upper().replace('.SA', '')
            dividendos_df = acao.dividendos(ticker_clean)
            
            if dividendos_df is None or dividendos_df.empty:
                return []
            
            # Filtrar apenas futuros
            hoje = datetime.now().strftime('%Y-%m-%d')
            dividendos = []
            
            for _, row in dividendos_df.iterrows():
                # Verificar se tem data de pagamento
                data_pag = None
                if 'datapagamento' in dividendos_df.columns:
                    data_pag = pd.to_datetime(row['datapagamento']).strftime('%Y-%m-%d')
                elif 'data_pagamento' in dividendos_df.columns:
                    data_pag = pd.to_datetime(row['data_pagamento']).strftime('%Y-%m-%d')
                
                # Se data futura, adicionar
                if data_pag and data_pag >= hoje:
                    dividendos.append({
                        'ticker': ticker,
                        'tipo': row.get('tipo', 'Dividendos'),
                        'valor': float(row.get('valor', 0)),
                        'data_pagamento': data_pag,
                        'status': 'provisionado',
                        'fonte': 'statusinvest'
                    })
            
            if dividendos:
                print(f"    [statusinvest] ✓ {len(dividendos)} futuros")
            
            return dividendos
        except:
            return []
    
    def capturar_dividendos(self, ticker: str) -> dict:
        """
        Captura dividendos futuros de um ticker.
        """
        print(f"  🔮 Buscando dividendos futuros de {ticker}...")
        
        dividendos = []
        
        # Fonte 1: Notícias B3
        div_noticias = self.capturar_futuros_noticias(ticker)
        dividendos.extend(div_noticias)
        
        # Fonte 2: StatusInvest
        div_statusinvest = self.capturar_futuros_statusinvest(ticker)
        dividendos.extend(div_statusinvest)
        
        if not dividendos:
            print(f"  ⚠️  Sem dividendos futuros para {ticker}")
            return None
        
        # Deduplicar por data_pagamento + valor
        vistos = set()
        unicos = []
        for div in dividendos:
            chave = (div.get('data_pagamento'), div.get('valor'))
            if chave not in vistos:
                vistos.add(chave)
                unicos.append(div)
        
        # Ordenar por data
        unicos.sort(key=lambda x: x.get('data_pagamento', '9999-99-99'))
        
        total_provisionado = sum(d['valor'] for d in unicos)
        
        resultado = {
            'ticker': ticker,
            'ultima_atualizacao': datetime.now().isoformat() + 'Z',
            'total_dividendos': len(unicos),
            'dividendos': unicos,
            'estatisticas': {
                'total_provisionado': round(total_provisionado, 2),
                'proxima_data': unicos[0].get('data_pagamento') if unicos else None,
                'proximo_valor': unicos[0].get('valor') if unicos else None
            }
        }
        
        print(f"  ✅ {ticker}: {len(unicos)} dividendos futuros")
        print(f"     Total provisionado: R$ {total_provisionado:.2f}")
        if resultado['estatisticas']['proxima_data']:
            print(f"     Próximo: {resultado['estatisticas']['proxima_data']} - R$ {resultado['estatisticas']['proximo_valor']:.2f}")
        
        self.empresas_processadas += 1
        self.dividendos_totais += len(unicos)
        
        return resultado
    
    def salvar_json(self, ticker: str, dados: dict):
        """
        Salva JSON de dividendos futuros.
        """
        if dados is None:
            return
        
        pasta_ticker = self.pasta_output / ticker
        pasta_ticker.mkdir(parents=True, exist_ok=True)
        
        arquivo = pasta_ticker / "dividendos_futuros.json"
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        print(f"  💾 Salvo: {arquivo}")
    
    def processar_ticker(self, ticker: str):
        """
        Processa um único ticker.
        """
        print(f"\n{'='*70}")
        print(f"🔮 {ticker}")
        print(f"{'='*70}")
        
        dados = self.capturar_dividendos(ticker)
        if dados:
            self.salvar_json(ticker, dados)
    
    def processar_lista(self, tickers: list):
        """
        Processa lista de tickers.
        """
        print(f"\n{'='*70}")
        print(f"🔮 CAPTURANDO DIVIDENDOS FUTUROS (ONLINE)")
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
        print(f"✅ Total de dividendos futuros: {self.dividendos_totais}")


def carregar_mapeamento(arquivo: str = "mapeamento_b3_consolidado.csv") -> list:
    """Carrega lista de tickers do CSV."""
    try:
        df = pd.read_csv(arquivo, sep=';')
        return df['ticker'].unique().tolist()
    except:
        return []


def main():
    parser = argparse.ArgumentParser(description='Capturar dividendos futuros (ONLINE)')
    parser.add_argument('--modo', choices=['quantidade', 'ticker', 'lista', 'completo'],
                       default='quantidade')
    parser.add_argument('--quantidade', type=int, default=10)
    parser.add_argument('--ticker', type=str)
    parser.add_argument('--lista', type=str)
    
    args = parser.parse_args()
    
    capturador = CapturadorDividendosFuturos()
    
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
