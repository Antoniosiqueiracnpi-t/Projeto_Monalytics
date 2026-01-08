#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAPTURADOR DE DIVIDENDOS FUTUROS B3 + CVM RAD (COMPLETO) + JANELA DESLIZANTE
============================================================================

Fluxo:
1. Carrega mapeamento_tradingname_b3.csv
2. Para cada empresa: trading_name → B3 → link CVM → tabela proventos
3. Salva por ticker: balancos/{TICKER}/dividendos_futuros.json (incremental, dedup)
4. Salva agregado diário: balancos/dividendos_anunciados.json (somente NOVOS da janela)

Deduplicação (janela deslizante):
- Lê dividendos_futuros.json existente por ticker
- Marca chaves já capturadas: data_pagamento + valor_bruto (2 casas)
- Busca notícias na janela --dias
- Só adiciona proventos não duplicados

Dependências:
pip install requests beautifulsoup4 pandas lxml
"""

import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, date, timedelta
import re
import time
import argparse
import sys
from typing import List, Dict, Optional
from urllib.parse import urljoin
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class CapturadorDividendosFuturos:

    def __init__(self, dias: int = 30):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
        })
        self.pasta_balancos = Path("balancos")
        self.hoje = date.today()
        self.total_futuros = 0
        self.dividendos_anunciados: List[Dict] = []  # agregador diário (somente novos)
        self.dias_janela = int(dias) if dias and dias > 0 else 30

    def executar(self, modo: str = 'completo', ticker: str = '', lista: str = '',
                 quantidade: int = 10, dias: int = 30):
        """Ponto de entrada principal."""
        self.dias_janela = int(dias) if dias and dias > 0 else self.dias_janela

        print("🔮 CAPTURANDO DIVIDENDOS FUTUROS (B3 + CVM RAD) — JANELA DESLIZANTE")
        print("=" * 70)
        print(f"🗓️ Janela de busca: últimos {self.dias_janela} dia(s)")
        print("=" * 70)

        empresas = self._carregar_empresas(modo, ticker, lista, quantidade)

        for empresa in empresas:
            self._processar_empresa(empresa)
            time.sleep(1.5)  # Rate limiting

        # Salvar compilado diário (somente novos)
        if self.dividendos_anunciados:
            self._salvar_dividendos_anunciados()

        print("\n" + "=" * 70)
        print(f"✅ FINALIZADO: {self.total_futuros} novos proventos encontrados na janela")
        print(f"📊 Compilado diário (novos): {len(self.dividendos_anunciados)} proventos")
        print("=" * 70)

    def _carregar_empresas(self, modo, ticker, lista, quantidade):
        """Carrega lista de empresas do mapeamento."""
        mapeamento_path = Path("mapeamento_tradingname_b3.csv")

        if not mapeamento_path.exists():
            logger.error("❌ mapeamento_tradingname_b3.csv não encontrado na raiz!")
            sys.exit(1)

        df = pd.read_csv(mapeamento_path, sep=';', encoding='utf-8')
        df = df[df['status'] == 'ok'].copy()

        empresas = []
        for _, row in df.iterrows():
            empresas.append({
                'ticker': str(row['ticker']).strip(),
                'trading_name': str(row['trading_name']).upper().strip(),
                'codigo': str(row.get('codigo', '')).strip()
            })

        if modo == 'ticker':
            empresas = [e for e in empresas if e['ticker'] == ticker]
        elif modo == 'lista':
            tickers_lista = [t.strip() for t in lista.split(',') if t.strip()]
            empresas = [e for e in empresas if e['ticker'] in tickers_lista]
        elif modo == 'quantidade':
            empresas = empresas[:quantidade]

        logger.info(f"📊 {len(empresas)} empresas para processar")
        return empresas

    def _processar_empresa(self, empresa):
        """Processa uma empresa completa (incremental + dedup)."""
        ticker = empresa['ticker']
        trading_name = empresa['trading_name']

        print(f"\n{'='*70}")
        print(f"🔮 {ticker} ({trading_name})")
        print(f"{'='*70}")

        # NOVO: dedup com existentes
        existentes = self._carregar_proventos_existentes(ticker)
        print(f"📊 {ticker}: {len(existentes)} proventos já capturados (dedup)")

        # NOVO: janela específica
        data_inicio = (self.hoje - timedelta(days=self.dias_janela)).strftime('%d/%m/%Y')

        dividendos_novos: List[Dict] = []

        # Busca com janela específica
        noticias = self._buscar_noticias_b3_janela(trading_name, ticker, data_inicio)

        for noticia in noticias:
            try:
                futuros_noticia = self._extrair_dividendos_cvm(noticia['url'])

                # NOVO: filtro de duplicatas
                novos_noticia = []
                for futuro in futuros_noticia:
                    chave = self._chave_provento(futuro)
                    if chave and chave not in existentes:
                        novos_noticia.append(futuro)
                        existentes.add(chave)  # evita duplicar na mesma execução

                dividendos_novos.extend(novos_noticia)
                logger.info(f"  📄 {noticia['titulo'][:60]}... → {len(novos_noticia)} novos")
            except Exception as e:
                logger.warning(f"  ⚠️ Erro em {noticia.get('titulo','')[:40]}: {e}")

        # Salvar só se houver novos
        if dividendos_novos:
            self._salvar_dividendos_incremental(ticker, dividendos_novos)
            self.total_futuros += len(dividendos_novos)

            # Agregar só novos no diário
            for d in dividendos_novos:
                item = d.copy()
                item['ticker'] = ticker
                item['trading_name'] = trading_name
                self.dividendos_anunciados.append(item)
        else:
            logger.info("  ✅ Sem novos dividendos nesta janela")

    def _buscar_noticias_b3(self, trading_name: str, ticker: str) -> List[Dict]:
        """Compat: busca padrão de 90 dias (mantido)."""
        data_inicio = (self.hoje - timedelta(days=90)).strftime('%d/%m/%Y')
        return self._buscar_noticias_b3_janela(trading_name, ticker, data_inicio)

    def _buscar_noticias_b3_janela(self, trading_name: str, ticker: str, data_inicio: str) -> List[Dict]:
        """Busca notícias B3 restrita à janela de dias."""
        url_base = "https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/Index"

        # Busca 1: trading_name (principal)
        params1 = {
            'agencia': '18',
            'busca': trading_name,
            'dataInicio': data_inicio,
            'dataFim': self.hoje.strftime('%d/%m/%Y')
        }
        noticias = self._scrapear_pagina_b3(url_base, params1)

        # Busca 2: ticker (fallback) — mantém seu comportamento original
        params2 = {
            'agencia': '18',
            'busca': ticker.replace('3', ''),
            'dataInicio': data_inicio,
            'dataFim': self.hoje.strftime('%d/%m/%Y')
        }
        noticias.extend(self._scrapear_pagina_b3(url_base, params2))

        # Dedup e filtro (mantém sua regra original: “fato relevante”)
        noticias_dict = {}
        for n in noticias:
            if 'fato relevante' in n['titulo'].lower() and n['url'] not in noticias_dict:
                noticias_dict[n['url']] = n

        return list(noticias_dict.values())

    def _scrapear_pagina_b3(self, url: str, params: dict) -> List[Dict]:
        """Scraping genérico de página B3."""
        try:
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            noticias = []
            for selector in ['table tr:has(a)', '.noticia-item', '.linha-resultado', 'tr td a']:
                for row in soup.select(selector):
                    link = row.select_one('a')
                    if link:
                        titulo = link.get_text().strip()
                        href = link.get('href', '')
                        if href and any(palavra in titulo.lower()
                                        for palavra in ['fato relevante', 'dividendos', 'jcp', 'proventos']):
                            noticias.append({
                                'titulo': titulo,
                                'url': urljoin(url, href)
                            })
            return noticias[:10]  # Limite por página
        except Exception as e:
            logger.warning(f"Erro scraping B3: {e}")
            return []

    def _extrair_dividendos_cvm(self, url_b3: str) -> List[Dict]:
        """B3 → link CVM → parse proventos."""
        # 1. Abrir página B3
        resp = self.session.get(url_b3, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')

        # 2. Encontrar link CVM RAD
        link_cvm = None
        for elem in soup.find_all(string=re.compile(r'documento|ver arq|uivo|cvm', re.I)):
            parent_a = elem.find_parent('a')
            if parent_a:
                href = parent_a.get('href')
                if href and ('rad.cvm.gov.br' in href or 'IPEExterno' in href):
                    link_cvm = urljoin(url_b3, href)
                    break

        if not link_cvm:
            return []

        logger.info(f"📄 Documento CVM: {link_cvm}")

        # 3. Abrir CVM RAD
        resp_cvm = self.session.get(link_cvm, timeout=15)
        soup_cvm = BeautifulSoup(resp_cvm.text, 'html.parser')

        # 4. Parsear todas as tabelas
        dividendos = []
        for table in soup_cvm.find_all('table'):
            try:
                dfs = pd.read_html(str(table))
                for df in dfs:
                    novos_proventos = self._parse_tabela_proventos(df)
                    dividendos.extend([p for p in novos_proventos if p])
            except Exception:
                continue

        return dividendos

    def _parse_tabela_proventos(self, df: pd.DataFrame) -> List[Dict]:
        """Parse inteligente de tabelas de proventos."""
        proventos = []

        # Normalizar colunas
        try:
            cols_lower = df.columns.astype(str).str.lower().str.strip()
        except Exception:
            return proventos

        # Identificar colunas relevantes
        col_data_pag = self._encontrar_coluna(cols_lower, ['pagamento', 'data pagamento', 'data_pgto'])
        col_valor = self._encontrar_coluna(cols_lower, ['valor', 'r$', 'montante'])
        col_tipo = self._encontrar_coluna(cols_lower, ['tipo', 'natureza', 'espécie'])
        col_data_com = self._encontrar_coluna(cols_lower, ['data com', 'com'])
        col_data_ex = self._encontrar_coluna(cols_lower, ['data ex', 'ex'])

        for idx, row in df.iterrows():
            try:
                data_pag = self._parse_data(row[col_data_pag] if col_data_pag is not None else '')
                if not data_pag or data_pag < self.hoje:
                    continue

                valor = self._parse_valor(row[col_valor] if col_valor is not None else 0)

                provento = {
                    'data_pagamento': data_pag.isoformat(),
                    'valor_bruto': valor,
                    'tipo': str(row[col_tipo]).strip() if col_tipo is not None else 'DIV',
                    'data_com': self._parse_data(row[col_data_com] if col_data_com is not None else ''),
                    'data_ex': self._parse_data(row[col_data_ex] if col_data_ex is not None else ''),
                    'fonte': 'CVM_RAD',
                    'linha_original': int(idx) if str(idx).isdigit() else idx
                }

                proventos.append(provento)
            except Exception:
                continue

        return proventos

    def _encontrar_coluna(self, cols: pd.Index, palavras: List[str]) -> Optional[int]:
        """Encontra coluna por palavras-chave."""
        for palavra in palavras:
            for i, col in enumerate(cols):
                if palavra in col:
                    return i
        return None

    def _parse_data(self, texto) -> Optional[date]:
        """Parse flexível de datas brasileiras."""
        if pd.isna(texto):
            return None

        s = str(texto).strip()

        # dd/mm/yyyy
        m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', s)
        if m:
            try:
                return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            except Exception:
                pass

        # yyyy-mm-dd (ISO)  ✅ (corrigido: ano = group1)
        m = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', s)
        if m:
            try:
                return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except Exception:
                pass

        # dd-mm-yyyy / dd/mm/yyyy já cobre; mantém fallback
        m = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', s)
        if m:
            try:
                return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            except Exception:
                pass

        return None

    def _parse_valor(self, texto) -> float:
        """Parse valores monetários."""
        if pd.isna(texto):
            return 0.0

        texto = re.sub(r'[^\d,.]', '', str(texto))
        texto = texto.replace('.', '').replace(',', '.')
        try:
            return float(texto)
        except Exception:
            return 0.0

    # =========================
    # NOVOS MÉTODOS (DEDUPE)
    # =========================

    def _chave_provento(self, d: Dict) -> Optional[str]:
        """Chave de dedup: data_pagamento + valor_bruto (2 casas)."""
        try:
            dp = d.get('data_pagamento', '') or ''
            vb = float(d.get('valor_bruto', 0) or 0)
            if not dp:
                return None
            return f"{dp}|{vb:.2f}"
        except Exception:
            return None

    def _carregar_proventos_existentes(self, ticker: str) -> set:
        """Carrega proventos já capturados para dedup."""
        arquivo = self.pasta_balancos / ticker / 'dividendos_futuros.json'
        if not arquivo.exists():
            return set()

        try:
            dados = json.loads(arquivo.read_text(encoding='utf-8'))
            existentes = set()
            for d in dados.get('dividendos', []):
                chave = self._chave_provento(d)
                if chave:
                    existentes.add(chave)
            return existentes
        except Exception:
            return set()

    def _salvar_dividendos_incremental(self, ticker: str, novos: List[Dict]):
        """Carrega antigos + adiciona novos (incremental)."""
        pasta = self.pasta_balancos / ticker
        pasta.mkdir(exist_ok=True)

        arquivo = pasta / 'dividendos_futuros.json'

        # Carrega antigos se existem
        dividendos = []
        if arquivo.exists():
            try:
                dados_antigos = json.loads(arquivo.read_text(encoding='utf-8'))
                dividendos = dados_antigos.get('dividendos', []) or []
            except Exception:
                dividendos = []

        # Adiciona novos
        dividendos.extend(novos)

        # Atualiza metadados de período (somente se houver data_pagamento)
        datas = [d.get('data_pagamento') for d in dividendos if d.get('data_pagamento')]
        periodo = None
        if datas:
            periodo = {'inicio': min(datas), 'fim': max(datas)}
        else:
            periodo = {'inicio': None, 'fim': None}

        dados = {
            'ticker': ticker,
            'ultima_atualizacao': datetime.now().isoformat(),
            'total_futuros': len(dividendos),
            'periodo': periodo,
            'dividendos': dividendos
        }

        arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')
        logger.info(f"💾 {ticker}: {len(novos)} novos → total {len(dividendos)}")

    def _salvar_dividendos_anunciados(self):
        """Salva compilado diário com SOMENTE os novos proventos da janela atual."""
        self.pasta_balancos.mkdir(exist_ok=True)

        # Ordena por data_pagamento + ticker
        ordenados = sorted(
            self.dividendos_anunciados,
            key=lambda x: (x.get('data_pagamento', ''), x.get('ticker', ''))
        )

        dados = {
            'data_execucao': datetime.now().strftime('%Y-%m-%d'),
            'hora_execucao': datetime.now().strftime('%H:%M:%S'),
            'dias_janela': self.dias_janela,
            'total_proventos': len(ordenados),
            'total_empresas': len({d['ticker'] for d in ordenados}),
            'proventos': ordenados,
        }

        arquivo = self.pasta_balancos / 'dividendos_anunciados.json'
        arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')
        logger.info(f"💾 Compilado diário salvo: {arquivo} ({len(ordenados)} proventos)")


def main():
    parser = argparse.ArgumentParser(description='Capturar dividendos futuros B3+CVM (janela deslizante)')
    parser.add_argument('--modo', choices=['completo', 'ticker', 'lista', 'quantidade'],
                        default='completo', help='Modo de execução')
    parser.add_argument('--ticker', help='Ticker específico')
    parser.add_argument('--lista', help='Lista de tickers (vírgula)')
    parser.add_argument('--quantidade', type=int, default=10, help='Qtd empresas (modo quantidade)')

    # NOVO: janela deslizante
    parser.add_argument('--dias', type=int, default=30,
                        help='Dias para buscar notícias (janela deslizante)')

    args = parser.parse_args()

    capturador = CapturadorDividendosFuturos(dias=args.dias)
    capturador.executar(args.modo, args.ticker or '', args.lista or '', args.quantidade, args.dias)


if __name__ == "__main__":
    main()
