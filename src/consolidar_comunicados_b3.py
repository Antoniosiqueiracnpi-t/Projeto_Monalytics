"""
CONSOLIDADOR DE COMUNICADOS B3 - Feed Único para Web

Gera arquivo JSON consolidado com todas as notícias de todas as empresas.
Ideal para consumo em páginas HTML/frontend.

SAÍDA:
- Arquivo: balancos/feed_noticias.json
- Formato: JSON estruturado com todas as notícias
- Ordenação: Data decrescente (mais recente primeiro)
- Atualização: Automática via GitHub Actions (diária)

ESTRUTURA DO JSON:
{
  "meta": {
    "ultima_atualizacao": "2024-12-30T09:00:00Z",
    "total_empresas": 50,
    "total_noticias": 750,
    "periodo_dias": 30
  },
  "estatisticas": {
    "por_categoria": {...},
    "por_ticker": {...}
  },
  "feed": [
    {
      "data": "2024-12-30",
      "hora": "09:00:00",
      "empresa": {...},
      "noticia": {...}
    }
  ]
}
"""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import List, Dict


class ConsolidadorNoticias:
    """
    Consolida todas as notícias individuais em um único JSON.
    """
    
    def __init__(self, pasta_balancos: str = "balancos"):
        self.pasta_balancos = Path(pasta_balancos)
        self.empresas_processadas = 0
        self.total_noticias = 0
    
    def consolidar(self) -> Dict:
        """
        Consolida todas as notícias em uma única estrutura.
        """
        print("="*70)
        print("📊 CONSOLIDANDO NOTÍCIAS PARA WEB")
        print("="*70)
        
        # Buscar todos os arquivos noticias.json
        arquivos_noticias = list(self.pasta_balancos.glob("*/noticias.json"))
        
        if not arquivos_noticias:
            print("⚠️  Nenhum arquivo de notícias encontrado")
            return self._estrutura_vazia()
        
        print(f"\n📁 Arquivos encontrados: {len(arquivos_noticias)}")
        
        # Coletar todas as notícias
        feed = []
        categorias = Counter()
        tickers = Counter()
        periodo_min = None
        periodo_max = None
        
        for arquivo in arquivos_noticias:
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                
                empresa_info = dados['empresa']
                ticker = empresa_info['ticker']
              
                # Normaliza ticker para sempre ter classe quando o JSON vier sem (ex.: 'BBAS' -> 'BBAS3')
                try:
                    t_norm = str(ticker).strip().upper()
                    if t_norm and not re.search(r'\d{1,2}$', t_norm):
                        base = t_norm[:4]
                        if base in self._mapa_base_para_ticker_classe:
                            ticker = self._mapa_base_para_ticker_classe[base]
                            empresa_info['ticker'] = ticker
                except Exception:
                    pass
              
                
                self.empresas_processadas += 1
                
                # Processar cada notícia
                for noticia in dados['noticias']:
                    # Adicionar informação da empresa à notícia
                    item_feed = {
                        'data': noticia['data'],
                        'hora': self._extrair_hora(noticia.get('titulo', '')),
                        'empresa': {
                            'ticker': ticker,
                            'nome': empresa_info['nome'],
                            'cnpj': empresa_info.get('cnpj', '')
                        },
                        'noticia': {
                            'titulo': noticia['titulo'],
                            'headline': noticia['headline'],
                            'categoria': noticia['categoria'],
                            'url': noticia['url']
                        }
                    }
                    
                    feed.append(item_feed)
                    categorias[noticia['categoria']] += 1
                    tickers[ticker] += 1
                    self.total_noticias += 1
                    
                    # Atualizar range de datas
                    data = noticia['data']
                    if periodo_min is None or data < periodo_min:
                        periodo_min = data
                    if periodo_max is None or data > periodo_max:
                        periodo_max = data
                
                print(f"  ✅ {ticker}: {len(dados['noticias'])} notícias")
                
            except Exception as e:
                print(f"  ❌ Erro ao processar {arquivo}: {e}")
                continue
        
        # Ordenar feed por data (mais recente primeiro)
        feed.sort(key=lambda x: (x['data'], x['hora']), reverse=True)
        
        # Criar estrutura consolidada
        consolidado = {
            'meta': {
                'ultima_atualizacao': datetime.now().isoformat() + 'Z',
                'data_atualizacao': datetime.now().strftime('%Y-%m-%d'),
                'hora_atualizacao': datetime.now().strftime('%H:%M:%S'),
                'total_empresas': self.empresas_processadas,
                'total_noticias': self.total_noticias,
                'periodo': {
                    'inicio': periodo_min,
                    'fim': periodo_max
                }
            },
            'estatisticas': {
                'por_categoria': dict(categorias.most_common()),
                'por_ticker': dict(tickers.most_common(20)),  # Top 20
                'top_categorias': [
                    {'categoria': cat, 'total': count}
                    for cat, count in categorias.most_common(10)
                ],
                'top_empresas': [
                    {'ticker': ticker, 'total': count}
                    for ticker, count in tickers.most_common(10)
                ]
            },
            'feed': feed
        }
        
        # Estatísticas
        print(f"\n{'='*70}")
        print(f"📊 ESTATÍSTICAS:")
        print(f"{'='*70}")
        print(f"✅ Empresas processadas: {self.empresas_processadas}")
        print(f"✅ Total de notícias: {self.total_noticias}")
        print(f"✅ Período: {periodo_min} a {periodo_max}")
        
        print(f"\n📈 TOP 5 CATEGORIAS:")
        for i, (cat, count) in enumerate(categorias.most_common(5), 1):
            print(f"  {i}. {cat}: {count} notícias")
        
        print(f"\n📈 TOP 5 EMPRESAS:")
        for i, (ticker, count) in enumerate(tickers.most_common(5), 1):
            print(f"  {i}. {ticker}: {count} notícias")
        
        return consolidado
    
    def _extrair_hora(self, titulo: str) -> str:
        """
        Extrai hora do título se disponível.
        Retorna '00:00:00' como padrão.
        """
        import re
        # Tentar extrair hora do formato DD/MM/AAAA HH:MM
        match = re.search(r'(\d{2}):(\d{2})', titulo)
        if match:
            return f"{match.group(1)}:{match.group(2)}:00"
        return "00:00:00"
    
    def _estrutura_vazia(self) -> Dict:
        """Retorna estrutura vazia quando não há notícias."""
        return {
            'meta': {
                'ultima_atualizacao': datetime.now().isoformat() + 'Z',
                'data_atualizacao': datetime.now().strftime('%Y-%m-%d'),
                'hora_atualizacao': datetime.now().strftime('%H:%M:%S'),
                'total_empresas': 0,
                'total_noticias': 0,
                'periodo': {
                    'inicio': None,
                    'fim': None
                }
            },
            'estatisticas': {
                'por_categoria': {},
                'por_ticker': {},
                'top_categorias': [],
                'top_empresas': []
            },
            'feed': []
        }
    
    def salvar(self, dados: Dict, arquivo: str = "feed_noticias.json"):
        """
        Salva JSON consolidado.
        """
        output_path = self.pasta_balancos / arquivo
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        # Calcular tamanho
        tamanho_kb = output_path.stat().st_size / 1024
        
        print(f"\n{'='*70}")
        print(f"✅ ARQUIVO GERADO COM SUCESSO!")
        print(f"{'='*70}")
        print(f"📁 Local: {output_path}")
        print(f"📊 Tamanho: {tamanho_kb:.2f} KB")
        print(f"🌐 URL: balancos/{arquivo}")
        print(f"{'='*70}\n")
        
        return output_path


# ============================================================================
# MAIN
# ============================================================================

def main():
    consolidador = ConsolidadorNoticias()
    
    # Consolidar todas as notícias
    dados = consolidador.consolidar()
    
    # Salvar JSON único
    consolidador.salvar(dados)
    
    print("✅ Consolidação concluída!")
    print("💡 Arquivo pronto para consumo em páginas HTML")
    print("💡 Atualização diária automática via GitHub Actions\n")


if __name__ == "__main__":
    main()
