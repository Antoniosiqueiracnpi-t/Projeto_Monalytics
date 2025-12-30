"""
CAPTURADOR DE DIVIDENDOS FUTUROS - Projeto Monalytics

Captura dividendos futuros (provisionados) de múltiplas fontes:
1. Notícias B3 categoria "Dividendos" (já capturadas)
2. API B3 Eventos Corporativos (backup)

SAÍDA:
- balancos/{TICKER}/dividendos_futuros.json

USO:
python src/capturar_dividendos_futuros.py --modo quantidade --quantidade 10
python src/capturar_dividendos_futuros.py --modo ticker --ticker VALE3
python src/capturar_dividendos_futuros.py --modo completo
"""

import json
import re
import requests
import base64
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import sys
from typing import List, Dict


class ParserNoticiasB3:
    """
    Parser inteligente para extrair dividendos de notícias B3.
    """
    
    @staticmethod
    def extrair_tipo(texto: str) -> str:
        """Detecta tipo de provento."""
        texto_upper = texto.upper()
        
        if 'JCP' in texto_upper or 'JUROS SOBRE CAPITAL' in texto_upper:
            return 'JCP'
        elif 'DIVIDENDO' in texto_upper:
            return 'Dividendos'
        else:
            return 'Outros'
    
    @staticmethod
    def extrair_valor(texto: str) -> float:
        """Extrai valor monetário."""
        # Padrões: R$ 2,09 ou R$2.09 ou 2,09 por ação
        patterns = [
            r'R\$\s*(\d+[.,]\d+)',
            r'valor\s+de\s+R\$\s*(\d+[.,]\d+)',
            r'(\d+[.,]\d+)\s*por\s+ação',
            r'montante\s+de\s+R\$\s*(\d+[.,]\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                valor_str = match.group(1).replace(',', '.')
                try:
                    return float(valor_str)
                except:
                    continue
        
        return None
    
    @staticmethod
    def extrair_data(texto: str, tipo_data: str) -> str:
        """
        Extrai data específica (com, pagamento).
        """
        patterns = {
            'com': [
                r'data[- ]com:?\s*(\d{2}/\d{2}/\d{4})',
                r'data[- ]base:?\s*(\d{2}/\d{2}/\d{4})',
                r'posição\s+acionária\s+(?:em|de)\s+(\d{2}/\d{2}/\d{4})'
            ],
            'pagamento': [
                r'pagamento:?\s*(\d{2}/\d{2}/\d{4})',
                r'(?:será\s+)?pago\s+em\s+(\d{2}/\d{2}/\d{4})',
                r'creditado\s+em\s+(\d{2}/\d{2}/\d{4})',
                r'data\s+de\s+pagamento:?\s*(\d{2}/\d{2}/\d{4})'
            ]
        }
        
        for pattern in patterns.get(tipo_data, []):
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                data_str = match.group(1)
                # Converter para YYYY-MM-DD
                try:
                    dia, mes, ano = data_str.split('/')
                    return f"{ano}-{mes}-{dia}"
                except:
                    continue
        
        return None
    
    @staticmethod
    def extrair_todas_datas(texto: str) -> List[str]:
        """Extrai todas as datas encontradas."""
        datas = re.findall(r'(\d{2}/\d{2}/\d{4})', texto)
        datas_convertidas = []
        
        for data_str in datas:
            try:
                dia, mes, ano = data_str.split('/')
                datas_convertidas.append(f"{ano}-{mes}-{dia}")
            except:
                continue
        
        return datas_convertidas
    
    def parse_noticia(self, noticia: Dict) -> Dict:
        """
        Parse completo de uma notícia.
        """
        texto_completo = f"{noticia.get('titulo', '')} {noticia.get('headline', '')}"
        
        tipo = self.extrair_tipo(texto_completo)
        valor = self.extrair_valor(texto_completo)
        data_com = self.extrair_data(texto_completo, 'com')
        data_pagamento = self.extrair_data(texto_completo, 'pagamento')
        todas_datas = self.extrair_todas_datas(texto_completo)
        
        # Se não encontrou data de pagamento mas tem datas, usar a mais futura
        if not data_pagamento and todas_datas:
            datas_futuras = [d for d in todas_datas if d >= datetime.now().strftime('%Y-%m-%d')]
            if datas_futuras:
                data_pagamento = max(datas_futuras)
        
        return {
            'tipo': tipo,
            'valor': valor,
            'data_com': data_com,
            'data_pagamento': data_pagamento,
            'todas_datas': todas_datas,
            'texto_original': texto_completo[:200]  # Primeiros 200 chars para debug
        }


class ScraperB3API:
    """
    Scraper da API não oficial da B3 de eventos corporativos.
    """
    
    def __init__(self):
        self.base_url = "https://sistemasweb.b3.com.br/ProventosEventosEndPoint/ProventosEventos/ListarEventosProventos"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
    
    def ticker_para_b3(self, ticker: str) -> str:
        """Remove número do ticker (VALE3 → VALE)."""
        return ticker.rstrip('0123456789')
    
    def buscar_proventos(self, ticker: str) -> List[Dict]:
        """
        Busca proventos futuros na API da B3.
        Retorna lista vazia se API não disponível (não interrompe execução).
        """
        try:
            ticker_b3 = self.ticker_para_b3(ticker)
            
            # Parâmetros
            params = {
                "language": "pt-br",
                "pageNumber": 1,
                "pageSize": 100,
                "tradingName": ticker_b3
            }
            
            # Codificar em base64
            params_json = json.dumps(params)
            params_b64 = base64.b64encode(params_json.encode()).decode()
            
            # URL completa
            url = f"{self.base_url}/{params_b64}"
            
            # Fazer requisição
            response = requests.get(url, headers=self.headers, timeout=15)
            
            # Se não for 200, retornar vazio (API pode estar indisponível)
            if response.status_code != 200:
                return []
            
            data = response.json()
            
            # Processar resultados
            proventos = []
            for item in data.get('results', []):
                # Filtrar apenas futuros
                data_pagamento = item.get('paymentDate', '')
                if data_pagamento and data_pagamento >= datetime.now().strftime('%Y-%m-%d'):
                    provento = {
                        'ticker': ticker,
                        'tipo': self._normalizar_tipo(item.get('type', '')),
                        'data_aprovacao': item.get('approvalDate'),
                        'data_com': item.get('lastDatePriorEx'),
                        'data_pagamento': data_pagamento,
                        'valor': item.get('rate'),
                        'moeda': item.get('currency', 'BRL'),
                        'fonte': 'b3_api'
                    }
                    proventos.append(provento)
            
            return proventos
            
        except Exception:
            # API B3 opcional - se não funcionar, apenas retorna vazio
            return []
    
    @staticmethod
    def _normalizar_tipo(tipo_b3: str) -> str:
        """Normaliza tipo de provento da B3."""
        tipo_upper = tipo_b3.upper()
        
        if 'JUROS' in tipo_upper or 'JCP' in tipo_upper:
            return 'JCP'
        elif 'DIVIDENDO' in tipo_upper:
            return 'Dividendos'
        else:
            return tipo_b3


class CapturadorDividendosFuturos:
    """
    Captura dividendos futuros de múltiplas fontes.
    """
    
    def __init__(self, pasta_output: str = "balancos"):
        self.pasta_output = Path(pasta_output)
        self.parser = ParserNoticiasB3()
        self.scraper = ScraperB3API()
        self.empresas_processadas = 0
        self.dividendos_totais = 0
        self.erros = []
    
    def carregar_noticias_dividendos(self, ticker: str) -> List[Dict]:
        """
        Carrega notícias de dividendos já capturadas.
        """
        try:
            # Caminho do arquivo de notícias
            arquivo_noticias = self.pasta_output / ticker / "noticias.json"
            
            if not arquivo_noticias.exists():
                return []
            
            with open(arquivo_noticias, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            # Filtrar apenas categoria Dividendos
            noticias_div = [
                n for n in dados.get('noticias', [])
                if n.get('categoria') == 'Dividendos'
            ]
            
            return noticias_div
            
        except Exception as e:
            print(f"  ⚠️  Erro ao carregar notícias de {ticker}: {e}")
            return []
    
    def processar_noticias(self, ticker: str, noticias: List[Dict]) -> List[Dict]:
        """
        Processa notícias e extrai dividendos.
        """
        dividendos = []
        
        for noticia in noticias:
            parsed = self.parser.parse_noticia(noticia)
            
            # Validar se tem dados mínimos
            if parsed['valor'] and (parsed['data_pagamento'] or parsed['data_com']):
                dividendo = {
                    'ticker': ticker,
                    'tipo': parsed['tipo'],
                    'valor': parsed['valor'],
                    'data_com': parsed['data_com'],
                    'data_pagamento': parsed['data_pagamento'],
                    'data_anuncio': noticia.get('data'),
                    'status': 'provisionado',
                    'fonte': 'noticias_b3',
                    'fonte_url': noticia.get('url'),
                    'titulo_original': noticia.get('titulo', '')[:100]
                }
                dividendos.append(dividendo)
        
        return dividendos
    
    def capturar_dividendos_futuros(self, ticker: str) -> Dict:
        """
        Captura dividendos futuros de um ticker.
        """
        print(f"  🔮 Buscando dividendos futuros de {ticker}...")
        
        dividendos = []
        
        # FONTE 1: Notícias B3
        noticias = self.carregar_noticias_dividendos(ticker)
        if noticias:
            print(f"  📰 {len(noticias)} notícias de dividendos encontradas")
            dividendos_noticias = self.processar_noticias(ticker, noticias)
            dividendos.extend(dividendos_noticias)
            print(f"  ✅ {len(dividendos_noticias)} dividendos extraídos das notícias")
        
        # FONTE 2: B3 API (backup/complemento - opcional)
        dividendos_b3 = self.scraper.buscar_proventos(ticker)
        if dividendos_b3:
            print(f"  🌐 {len(dividendos_b3)} dividendos da B3 API")
            dividendos.extend(dividendos_b3)
        
        if not dividendos:
            print(f"  ⚠️  Sem dividendos futuros para {ticker}")
            return None
        
        # Deduplicar (mesma data de pagamento + valor)
        dividendos_unicos = self._deduplicar(dividendos)
        
        # Ordenar por data de pagamento
        dividendos_unicos.sort(key=lambda x: x.get('data_pagamento', '9999-99-99'))
        
        # Calcular estatísticas
        total_provisionado = sum(d['valor'] for d in dividendos_unicos if d.get('valor'))
        
        resultado = {
            'ticker': ticker,
            'ultima_atualizacao': datetime.now().isoformat() + 'Z',
            'total_dividendos': len(dividendos_unicos),
            'dividendos': dividendos_unicos,
            'estatisticas': {
                'total_provisionado': round(total_provisionado, 2),
                'proxima_data': dividendos_unicos[0].get('data_pagamento') if dividendos_unicos else None,
                'proximo_valor': dividendos_unicos[0].get('valor') if dividendos_unicos else None
            }
        }
        
        print(f"  ✅ {ticker}: {len(dividendos_unicos)} dividendos futuros")
        print(f"     Total provisionado: R$ {total_provisionado:.2f}")
        if resultado['estatisticas']['proxima_data']:
            print(f"     Próximo: {resultado['estatisticas']['proxima_data']} - R$ {resultado['estatisticas']['proximo_valor']:.2f}")
        
        self.empresas_processadas += 1
        self.dividendos_totais += len(dividendos_unicos)
        
        return resultado
    
    def _deduplicar(self, dividendos: List[Dict]) -> List[Dict]:
        """
        Remove duplicatas baseado em data + valor.
        """
        vistos = set()
        unicos = []
        
        for div in dividendos:
            # Chave: data_pagamento + valor
            chave = (div.get('data_pagamento'), div.get('valor'))
            
            if chave not in vistos and all(chave):
                vistos.add(chave)
                unicos.append(div)
        
        return unicos
    
    def salvar_json(self, ticker: str, dados: Dict):
        """
        Salva JSON de dividendos futuros.
        """
        if dados is None:
            return
        
        # Criar pasta do ticker
        pasta_ticker = self.pasta_output / ticker
        pasta_ticker.mkdir(parents=True, exist_ok=True)
        
        # Salvar JSON
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
        
        try:
            dados = self.capturar_dividendos_futuros(ticker)
            if dados:
                self.salvar_json(ticker, dados)
        except Exception as e:
            erro = f"Erro ao processar {ticker}: {str(e)}"
            print(f"  ❌ {erro}")
            self.erros.append(erro)
    
    def processar_lista(self, tickers: List[str]):
        """
        Processa lista de tickers.
        """
        print(f"\n{'='*70}")
        print(f"🔮 CAPTURANDO DIVIDENDOS FUTUROS")
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
        
        if self.erros:
            print(f"\n❌ Erros encontrados: {len(self.erros)}")
            for erro in self.erros[:5]:
                print(f"   - {erro}")
            if len(self.erros) > 5:
                print(f"   ... e mais {len(self.erros) - 5} erros")


# ============================================================================
# MAIN
# ============================================================================

def carregar_mapeamento(arquivo: str = "mapeamento_b3_consolidado.csv") -> List[str]:
    """Carrega lista de tickers do CSV."""
    try:
        import pandas as pd
        df = pd.read_csv(arquivo, sep=';')
        return df['ticker'].unique().tolist()
    except Exception as e:
        print(f"❌ Erro ao carregar mapeamento: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description='Capturar dividendos futuros')
    parser.add_argument('--modo', choices=['quantidade', 'ticker', 'lista', 'completo'],
                       default='quantidade', help='Modo de captura')
    parser.add_argument('--quantidade', type=int, default=10,
                       help='Quantidade de empresas (modo quantidade)')
    parser.add_argument('--ticker', type=str,
                       help='Ticker específico (modo ticker)')
    parser.add_argument('--lista', type=str,
                       help='Lista de tickers separados por vírgula (modo lista)')
    
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
