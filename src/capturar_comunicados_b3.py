"""
CAPTURADOR DE NOTÍCIAS B3 - Execução Diária com busca de pasta existente
"""

import pandas as pd
import re
from pathlib import Path
from datetime import datetime, timedelta
import json
import argparse
from finbr.b3 import plantao_noticias
from typing import Dict, List, Optional
from collections import Counter


class CapturadorNoticiasB3:

    def __init__(self, arquivo_mapeamento: str = "mapeamento_b3_consolidado.csv",
                 pasta_saida: str = "balancos"):
        self.arquivo_mapeamento = Path(arquivo_mapeamento)
        self.pasta_saida = Path(pasta_saida)
        self.pasta_saida.mkdir(exist_ok=True)

    def _split_tickers(self, tickers_raw: str) -> List[str]:
        """Quebra uma célula que pode vir como 'ITUB3;ITUB4' em uma lista de tickers."""
        if not tickers_raw:
            return []
        s = str(tickers_raw).strip().upper()
        # separadores comuns em CSVs: ; , / | e espaços
        parts = re.split(r"[;,/|\s]+", s)
        return [p.strip() for p in parts if p and p.strip()]

    def _extrair_ticker_base(self, ticker: str) -> str:
        """Remove número da classe, suportando múltiplos tickers na mesma célula.
        Exemplos:
          - ITUB3 -> ITUB
          - ITUB3;ITUB4 -> ITUB
          - SANB11;SANB3;SANB4 -> SANB
        """
        if not ticker:
            return ""
        tickers = self._split_tickers(ticker)
        # fallback caso venha um ticker único sem separador
        if not tickers:
            tickers = [str(ticker).strip().upper()]
        bases = [re.sub(r"\d+$", "", t) for t in tickers if t]
        bases = [b for b in bases if b]
        if not bases:
            return ""
        # se vierem várias classes, todas devem apontar para a mesma base; em dúvida, pega a mais comum
        return Counter(bases).most_common(1)[0][0]

    def encontrar_pasta_empresa(self, ticker_completo: str) -> Path:
        """
        Busca pasta existente para ticker completo (preserva classe: BBDC3).
        Regra: Usa pasta já aberta da empresa (qualquer classe).
               Prioriza exata > com base > cria nova com classe.
        """
        ticker_base = self.extrair_ticker_base(ticker_completo)
        pastas_candidatas = []
        
        if self.pasta_saida.exists():
            for pasta in self.pasta_saida.iterdir():
                if pasta.is_dir():
                    nome_pasta = pasta.name.upper()
                    # PRIORIDADE 1: Match EXATO (BBDC3 buscando BBDC3)
                    if nome_pasta == ticker_completo.upper():
                        return pasta
                    # PRIORIDADE 2: Mesma empresa (base coincide: BBDC4 buscando BBDC3)
                    if self.extrair_ticker_base(nome_pasta) == ticker_base:
                        pastas_candidatas.append(pasta)
        
        if pastas_candidatas:
            # Prefere nomes mais longos (com classe: BBDC11 > BBDC)
            pastas_candidatas.sort(key=lambda p: len(p.name), reverse=True)
            return pastas_candidatas[0]
        
        # CRIA NOVA com ticker completo (mantém classe)
        nova_pasta = self.pasta_saida / ticker_completo
        return nova_pasta


    def _carregar_empresas(self) -> pd.DataFrame:
        """Carrega lista de empresas do CSV."""
        df = pd.read_csv(self.arquivo_mapeamento, sep=';', encoding='utf-8-sig')
        df['ticker_base'] = df['ticker'].apply(self._extrair_ticker_base)
        return df.drop_duplicates(subset=['ticker_base'], keep='first')

    def _selecionar_empresas(self, df: pd.DataFrame, modo: str, **kwargs) -> pd.DataFrame:
        """Seleciona empresas baseado no modo especificado."""

        if modo == 'quantidade':
            qtd = int(kwargs.get('quantidade', 10))
            return df.head(qtd)

        elif modo == 'ticker':
            ticker = kwargs.get('ticker', '').strip().upper()
            ticker_base = self._extrair_ticker_base(ticker)
            return df[df['ticker_base'] == ticker_base]

        elif modo == 'lista':
            lista = kwargs.get('lista', '')
            tickers = [self._extrair_ticker_base(t.strip().upper()) for t in lista.split(',') if t.strip()]
            return df[df['ticker_base'].isin(tickers)]

        elif modo == 'faixa':
            faixa = kwargs.get('faixa', '1-50')
            inicio, fim = map(int, faixa.split('-'))
            return df.iloc[inicio-1:fim]

        else:
            print(f"⚠️ Modo '{modo}' não reconhecido. Usando primeiras 10 empresas.")
            return df.head(10)

    def _classificar_noticia(self, titulo: str, headline: str) -> str:
        """Classifica notícia por palavras-chave."""
        texto = f"{titulo} {headline}".upper()

        categorias = {
            "Fato Relevante": ["FATO RELEVANTE", "MATERIAL FACT"],
            "Resultados": ["RESULTADO", "ITR", "DFP", "BALANÇO", "LUCRO", "RECEITA"],
            "Dividendos": ["DIVIDENDO", "JCP", "PROVENTO", "DIVIDEND"],
            "Governança": ["AGO", "AGE", "ASSEMBLEIA", "CONSELHO", "ATA"],
            "Aquisição": ["AQUISIÇÃO", "ACQUISITION", "COMPRA", "FUSÃO"],
            "Emissão": ["EMISSÃO", "DEBÊNTURE", "BOND"],
            "Aviso": ["AVISO", "COMUNICADO", "NOTICE"],
        }

        for categoria, palavras in categorias.items():
            if any(palavra in texto for palavra in palavras):
                return categoria
        return "Outros"

    def _buscar_noticias_empresa(self, ticker_base: str, data_inicio: str, data_fim: str,
                                tickers_ref: Optional[List[str]] = None) -> pd.DataFrame:
        """Busca notícias filtrando por ticker base e menções no texto.

        tickers_ref (opcional): lista de tickers completos (classes) para ajudar no filtro por texto
        quando o campo ticker da notícia vier vazio/inconsistente.
        """
        print(f"  🔍 Buscando notícias para {ticker_base}.", end=" ")

        try:
            noticias_raw = plantao_noticias.get(inicio=data_inicio, fim=data_fim)
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
            return pd.DataFrame()

        if not noticias_raw:
            print("⚠️ Nenhuma notícia no período")
            return pd.DataFrame()

        df = pd.DataFrame([{
            "data_hora": getattr(n, "data_hora", None),
            "ticker": getattr(n, "ticker", None),
            "empresa": getattr(n, "empresa", None),
            "titulo": getattr(n, "titulo", None),
            "headline": getattr(n, "headline", None),
            "conteudo": getattr(n, "conteudo", None),
            "url": getattr(n, "url", None),
            "id": getattr(n, "id", None),
        } for n in noticias_raw])

        # Filtro 1: Ticker (normalizado para base; suporta ticker múltiplo no retorno)
        mask_ticker = (
            df["ticker"]
            .fillna("")
            .astype(str)
            .str.upper()
            .apply(self._extrair_ticker_base)
            .eq(ticker_base)
        )

        # Filtro 2: Menção no texto (base OU ticker(s) completo(s) caso informado)
        tokens = [ticker_base]
        if tickers_ref:
            tokens.extend([t.strip().upper() for t in tickers_ref if t])
        # dedup preservando ordem
        seen = set()
        tokens = [t for t in tokens if not (t in seen or seen.add(t))]
        pattern = "|".join([rf"\b{re.escape(t)}\b" for t in tokens if t])

        mask_texto = (
            df[["empresa", "titulo", "headline", "conteudo"]]
            .fillna("")
            .agg(" ".join, axis=1)
            .astype(str)
            .str.upper()
            .str.contains(pattern, regex=True)
        )

        df_filtrado = df[mask_ticker | mask_texto].copy()

        if df_filtrado.empty:
            print("⚠️ Nenhuma correspondência encontrada")
        else:
            print(f"✅ {len(df_filtrado)} notícia(s)")

        return df_filtrado

    def _carregar_arquivo_existente(self, caminho: Path) -> Dict:
        """Carrega JSON existente ou retorna estrutura vazia."""
        if caminho.exists():
            with open(caminho, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"noticias": []}

    def processar_empresa(self, row: pd.Series, data_inicio: str, data_fim: str) -> bool:
        """Processa notícias de uma empresa, salva na pasta correta."""
        # ticker_base para buscas amplas (sem classe)
        ticker_base = row.get('ticker_base', '').strip().upper()
        
        # ticker_completo para pasta (preserva classe de row['ticker'])
        ticker_completo = row.get('ticker', ticker_base or '').strip().upper()
        if not ticker_completo:
            ticker_completo = ticker_base
        
        # Lista com classes para filtro por texto
        tickers_ref = self.split_tickers(row.get('ticker', ''))
        
        # ENCONTRA/CRIA PASTA (nova lógica!)
        pasta_empresa = self.encontrar_pasta_empresa(ticker_completo)
        pasta_empresa.mkdir(exist_ok=True)
        print(f"📁 Pasta: {pasta_empresa.name}")
        
        df_noticias = self.buscar_noticias_empresa(ticker_base, data_inicio, data_fim, tickers_ref)
        if df_noticias.empty:
            return False
        
        arquivo_json = pasta_empresa / 'noticias.json'
        dados_existentes = self.carregar_arquivo_existente(arquivo_json)
        ids_existentes = {n.get('id') for n in dados_existentes.get('noticias', [])}
        
        noticias_novas = []
        for _, noticia in df_noticias.iterrows():
            noticia_id = noticia.get('id')
            if noticia_id and noticia_id in ids_existentes:
                continue
            
            data_hora_obj = noticia.get('datahora')
            if isinstance(data_hora_obj, str):
                data_hora_obj = pd.to_datetime(data_hora_obj)
            
            noticias_novas.append({
                'data': data_hora_obj.strftime('%Y-%m-%d') if data_hora_obj else None,
                'datahora': data_hora_obj.strftime('%Y-%m-%d %H:%M:%S') if data_hora_obj else None,
                'titulo': noticia.get('titulo'),
                'headline': noticia.get('headline'),
                'conteudo': noticia.get('conteudo'),
                'url': noticia.get('url'),
                'id': noticia_id,
                'categoria': self.classificar_noticia(noticia.get('titulo'), noticia.get('headline'))
            })
            if noticia_id:
                ids_existentes.add(noticia_id)
        
        if not noticias_novas:
            print("ℹ️ Nenhuma notícia nova (todas já existem)")
            return False
        
        todas_noticias = noticias_novas + dados_existentes.get('noticias', [])
        todas_noticias.sort(key=lambda x: x.get('datahora'), reverse=True)
        
        dados_finais = {
            'empresa': {
                'ticker': ticker_completo,
                'nome': row.get('empresa'),
                'cnpj': row.get('cnpj')
            },
            'ultima_atualizacao': datetime.now().isoformat(),
            'total_noticias': len(todas_noticias),
            'noticias': todas_noticias
        }
        
        with open(arquivo_json, 'w', encoding='utf-8') as f:
            json.dump(dados_finais, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {len(noticias_novas)} novas | Total: {len(todas_noticias)}")
        return True


    def executar(self, modo: str = 'quantidade', dias_retroativos: int = 1, **kwargs):
        """Executa captura para empresas selecionadas."""
        print("="*70)
        print("📰 CAPTURADOR DE NOTÍCIAS B3")
        print("="*70)

        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=dias_retroativos)

        print(f"\n📅 Período: {data_inicio.strftime('%Y-%m-%d')} a {data_fim.strftime('%Y-%m-%d')}")

        df_empresas = self._carregar_empresas()
        df_selecionadas = self._selecionar_empresas(df_empresas, modo, **kwargs)

        print(f"🎯 Modo: {modo}")
        print(f"✅ {len(df_selecionadas)} empresa(s) selecionada(s)\n")

        if df_selecionadas.empty:
            print("⚠️ Nenhuma empresa selecionada!")
            return

        empresas_processadas = 0
        empresas_com_noticias = 0

        for idx, (_, row) in enumerate(df_selecionadas.iterrows(), 1):
            print(f"\n[{idx}/{len(df_selecionadas)}] {row['ticker_base']} - {row.get('empresa', '')[:50]}.")

            try:
                if self._processar_empresa(row, data_inicio.strftime('%Y-%m-%d'), data_fim.strftime('%Y-%m-%d')):
                    empresas_com_noticias += 1
                empresas_processadas += 1
            except Exception as e:
                print(f"  ❌ Erro: {e}")
                import traceback
                traceback.print_exc()

        print(f"\n{'='*70}")
        print(f"✅ Processadas: {empresas_processadas}/{len(df_selecionadas)} | Com notícias novas: {empresas_com_noticias}")
        print(f"💾 Salvos em: {self.pasta_saida}/")
        print("="*70)


def main():
    parser = argparse.ArgumentParser(description='Capturador de Notícias B3')
    parser.add_argument('--modo', default='quantidade',
                        choices=['quantidade', 'ticker', 'lista', 'faixa'],
                        help='Modo de seleção de empresas')
    parser.add_argument('--quantidade', type=int, default=10,
                        help='Quantidade de empresas (modo=quantidade)')
    parser.add_argument('--ticker', default='',
                        help='Ticker para buscar (modo=ticker)')
    parser.add_argument('--lista', default='',
                        help='Lista de tickers separados por vírgula (modo=lista)')
    parser.add_argument('--faixa', default='1-50',
                        help='Faixa de linhas no formato INICIO-FIM (modo=faixa)')
    parser.add_argument('--dias', type=int, default=30,
                        help='Período de busca em dias')

    args = parser.parse_args()

    capturador = CapturadorNoticiasB3()
    capturador.executar(
        modo=args.modo,
        dias_retroativos=args.dias,
        quantidade=args.quantidade,
        ticker=args.ticker,
        lista=args.lista,
        faixa=args.faixa
    )


if __name__ == "__main__":
    main()
