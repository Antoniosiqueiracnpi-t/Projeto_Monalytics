"""
CONSOLIDADOR DE DIVIDENDOS - Projeto Monalytics

Consolida dividendos históricos + futuros em agenda única.
Gera múltiplos JSONs para diferentes visualizações.

SAÍDA:
- balancos/agenda_dividendos.json (feed único completo)
- balancos/agenda_dividendos_mes.json (organizado por mês)
- balancos/estatisticas_dividendos.json (análises)

USO:
python src/consolidar_dividendos.py
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import List, Dict


class ConsolidadorDividendos:
    """
    Consolida dividendos históricos e futuros em agenda única.
    """
    
    def __init__(self, pasta_balancos: str = "balancos"):
        self.pasta_balancos = Path(pasta_balancos)
        self.empresas_processadas = 0
        self.dividendos_historicos = 0
        self.dividendos_futuros = 0
    
    def carregar_dividendos_empresa(self, ticker: str) -> Dict:
        """
        Carrega dividendos históricos + futuros de uma empresa.
        """
        pasta_ticker = self.pasta_balancos / ticker
        
        if not pasta_ticker.exists():
            return None
        
        dividendos = []
        
        # Carregar histórico
        arquivo_historico = pasta_ticker / "dividendos_historico.json"
        if arquivo_historico.exists():
            try:
                with open(arquivo_historico, 'r', encoding='utf-8') as f:
                    historico = json.load(f)
                    for div in historico.get('dividendos', []):
                        div['ticker'] = ticker
                        div['status'] = 'pago'
                        dividendos.append(div)
                    self.dividendos_historicos += len(historico.get('dividendos', []))
            except Exception as e:
                print(f"⚠️  Erro ao carregar histórico de {ticker}: {e}")
        
        # Carregar futuros
        arquivo_futuros = pasta_ticker / "dividendos_futuros.json"
        if arquivo_futuros.exists():
            try:
                with open(arquivo_futuros, 'r', encoding='utf-8') as f:
                    futuros = json.load(f)
                    for div in futuros.get('dividendos', []):
                        div['ticker'] = ticker
                        div['status'] = 'provisionado'
                        dividendos.append(div)
                    self.dividendos_futuros += len(futuros.get('dividendos', []))
            except Exception as e:
                print(f"⚠️  Erro ao carregar futuros de {ticker}: {e}")
        
        if not dividendos:
            return None
        
        # Ordenar por data (mais recente primeiro)
        dividendos.sort(key=lambda x: self._get_data_ordenacao(x), reverse=True)
        
        return {
            'ticker': ticker,
            'dividendos': dividendos
        }
    
    @staticmethod
    def _get_data_ordenacao(dividendo: Dict) -> str:
        """
        Retorna data para ordenação (pagamento ou data).
        """
        return dividendo.get('data_pagamento') or dividendo.get('data') or '1900-01-01'
    
    def consolidar_tudo(self) -> Dict:
        """
        Consolida todas as empresas em feed único.
        """
        print("="*70)
        print("📊 CONSOLIDANDO DIVIDENDOS")
        print("="*70)
        
        todos_dividendos = []
        
        # Buscar todas as pastas de tickers
        for pasta_ticker in self.pasta_balancos.iterdir():
            if not pasta_ticker.is_dir():
                continue
            
            ticker = pasta_ticker.name
            
            # Pular arquivos JSON (não são tickers)
            if ticker.endswith('.json'):
                continue
            
            dados = self.carregar_dividendos_empresa(ticker)
            if dados:
                todos_dividendos.extend(dados['dividendos'])
                self.empresas_processadas += 1
                print(f"  ✅ {ticker}: {len(dados['dividendos'])} dividendos")
        
        # Ordenar todos por data
        todos_dividendos.sort(key=lambda x: self._get_data_ordenacao(x), reverse=True)
        
        # Calcular estatísticas
        estatisticas = self._calcular_estatisticas(todos_dividendos)
        
        # Estrutura final
        agenda = {
            'meta': {
                'ultima_atualizacao': datetime.now().isoformat() + 'Z',
                'data_atualizacao': datetime.now().strftime('%Y-%m-%d'),
                'hora_atualizacao': datetime.now().strftime('%H:%M:%S'),
                'total_empresas': self.empresas_processadas,
                'total_dividendos': len(todos_dividendos),
                'dividendos_historicos': self.dividendos_historicos,
                'dividendos_futuros': self.dividendos_futuros
            },
            'estatisticas': estatisticas,
            'dividendos': todos_dividendos
        }
        
        return agenda
    
    def _calcular_estatisticas(self, dividendos: List[Dict]) -> Dict:
        """
        Calcula estatísticas agregadas.
        """
        # Contadores
        por_status = Counter(d.get('status') for d in dividendos)
        por_tipo = Counter(d.get('tipo') for d in dividendos)
        por_ticker = Counter(d.get('ticker') for d in dividendos)
        
        # Valores
        total_pago = sum(d.get('valor', 0) for d in dividendos if d.get('status') == 'pago')
        total_provisionado = sum(d.get('valor', 0) for d in dividendos if d.get('status') == 'provisionado')
        
        # Top pagadores
        valores_por_ticker = defaultdict(float)
        for d in dividendos:
            if d.get('valor'):
                valores_por_ticker[d.get('ticker')] += d.get('valor', 0)
        
        top_pagadores = sorted(
            [{'ticker': t, 'total': round(v, 2)} for t, v in valores_por_ticker.items()],
            key=lambda x: x['total'],
            reverse=True
        )[:20]
        
        # Dividendos por mês
        por_mes = defaultdict(int)
        for d in dividendos:
            data = self._get_data_ordenacao(d)
            if data and len(data) >= 7:
                mes = data[:7]  # YYYY-MM
                por_mes[mes] += 1
        
        return {
            'por_status': dict(por_status),
            'por_tipo': dict(por_tipo),
            'por_ticker_top10': [
                {'ticker': t, 'total': c}
                for t, c in por_ticker.most_common(10)
            ],
            'valores': {
                'total_pago': round(total_pago, 2),
                'total_provisionado': round(total_provisionado, 2),
                'total_geral': round(total_pago + total_provisionado, 2)
            },
            'top_pagadores': top_pagadores,
            'por_mes': dict(sorted(por_mes.items(), reverse=True)[:12])  # Últimos 12 meses
        }
    
    def organizar_por_mes(self, dividendos: List[Dict]) -> Dict:
        """
        Organiza dividendos por mês (data de pagamento).
        """
        por_mes = defaultdict(list)
        
        for div in dividendos:
            data = self._get_data_ordenacao(div)
            if data and len(data) >= 7:
                mes = data[:7]  # YYYY-MM
                por_mes[mes].append({
                    'ticker': div.get('ticker'),
                    'tipo': div.get('tipo'),
                    'valor': div.get('valor'),
                    'data_com': div.get('data_com'),
                    'data_pagamento': div.get('data_pagamento') or div.get('data'),
                    'status': div.get('status')
                })
        
        # Ordenar meses (mais recente primeiro)
        meses_ordenados = {}
        for mes in sorted(por_mes.keys(), reverse=True):
            # Ordenar dividendos do mês por data
            dividendos_mes = por_mes[mes]
            dividendos_mes.sort(key=lambda x: x.get('data_pagamento', '1900-01-01'))
            meses_ordenados[mes] = dividendos_mes
        
        return {
            'meta': {
                'ultima_atualizacao': datetime.now().isoformat() + 'Z',
                'total_meses': len(meses_ordenados),
                'meses_disponiveis': list(meses_ordenados.keys())
            },
            'por_mes': meses_ordenados
        }
    
    def gerar_estatisticas_detalhadas(self, dividendos: List[Dict]) -> Dict:
        """
        Gera arquivo separado com estatísticas detalhadas.
        """
        # Dividendos futuros (próximos 12 meses)
        hoje = datetime.now().strftime('%Y-%m-%d')
        futuros = [d for d in dividendos if self._get_data_ordenacao(d) >= hoje]
        
        # Análise por empresa
        por_empresa = defaultdict(lambda: {
            'historicos': 0,
            'futuros': 0,
            'total_valor': 0,
            'ultimo_pagamento': None,
            'proximo_pagamento': None
        })
        
        for div in dividendos:
            ticker = div.get('ticker')
            valor = div.get('valor', 0)
            data = self._get_data_ordenacao(div)
            
            por_empresa[ticker]['total_valor'] += valor
            
            if div.get('status') == 'pago':
                por_empresa[ticker]['historicos'] += 1
                if not por_empresa[ticker]['ultimo_pagamento'] or data > por_empresa[ticker]['ultimo_pagamento']:
                    por_empresa[ticker]['ultimo_pagamento'] = data
            else:
                por_empresa[ticker]['futuros'] += 1
                if not por_empresa[ticker]['proximo_pagamento'] or data < por_empresa[ticker]['proximo_pagamento']:
                    por_empresa[ticker]['proximo_pagamento'] = data
        
        # Converter para lista
        empresas_lista = [
            {
                'ticker': ticker,
                **dados,
                'total_valor': round(dados['total_valor'], 2)
            }
            for ticker, dados in por_empresa.items()
        ]
        
        # Ordenar por valor total
        empresas_lista.sort(key=lambda x: x['total_valor'], reverse=True)
        
        return {
            'meta': {
                'ultima_atualizacao': datetime.now().isoformat() + 'Z',
                'total_empresas': len(empresas_lista)
            },
            'proximos_dividendos': futuros[:50],  # Próximos 50
            'por_empresa': empresas_lista,
            'resumo': {
                'total_empresas_com_historico': sum(1 for e in empresas_lista if e['historicos'] > 0),
                'total_empresas_com_futuros': sum(1 for e in empresas_lista if e['futuros'] > 0),
                'total_dividendos_futuros': sum(e['futuros'] for e in empresas_lista),
                'valor_total_provisionado': round(sum(d['valor'] for d in futuros if d.get('valor')), 2)
            }
        }
    
    def salvar_json(self, dados: Dict, nome_arquivo: str):
        """
        Salva JSON no diretório balancos.
        """
        arquivo = self.pasta_balancos / nome_arquivo
        
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        # Calcular tamanho
        tamanho_kb = arquivo.stat().st_size / 1024
        
        print(f"\n✅ {nome_arquivo}")
        print(f"   📁 {arquivo}")
        print(f"   📊 {tamanho_kb:.2f} KB")
    
    def consolidar_e_salvar(self):
        """
        Executa consolidação completa e salva todos os JSONs.
        """
        # 1. Consolidar tudo
        agenda = self.consolidar_tudo()
        
        # 2. Organizar por mês
        por_mes = self.organizar_por_mes(agenda['dividendos'])
        
        # 3. Estatísticas detalhadas
        estatisticas = self.gerar_estatisticas_detalhadas(agenda['dividendos'])
        
        # Imprimir resumo
        print(f"\n{'='*70}")
        print(f"📊 RESUMO CONSOLIDAÇÃO")
        print(f"{'='*70}")
        print(f"✅ Empresas processadas: {self.empresas_processadas}")
        print(f"✅ Dividendos históricos: {self.dividendos_historicos}")
        print(f"✅ Dividendos futuros: {self.dividendos_futuros}")
        print(f"✅ Total de dividendos: {len(agenda['dividendos'])}")
        print(f"✅ Valor total pago: R$ {agenda['estatisticas']['valores']['total_pago']:,.2f}")
        print(f"✅ Valor provisionado: R$ {agenda['estatisticas']['valores']['total_provisionado']:,.2f}")
        
        print(f"\n{'='*70}")
        print(f"💾 SALVANDO ARQUIVOS")
        print(f"{'='*70}")
        
        # Salvar todos os JSONs
        self.salvar_json(agenda, "agenda_dividendos.json")
        self.salvar_json(por_mes, "agenda_dividendos_mes.json")
        self.salvar_json(estatisticas, "estatisticas_dividendos.json")
        
        print(f"\n{'='*70}")
        print(f"✅ CONSOLIDAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"{'='*70}")
        print(f"\n💡 Arquivos prontos para consumo:")
        print(f"   - agenda_dividendos.json (feed completo)")
        print(f"   - agenda_dividendos_mes.json (por mês)")
        print(f"   - estatisticas_dividendos.json (análises)")
        print()


# ============================================================================
# MAIN
# ============================================================================

def main():
    consolidador = ConsolidadorDividendos()
    consolidador.consolidar_e_salvar()


if __name__ == "__main__":
    main()
