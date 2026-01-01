"""
CAPTURADOR DE NOTÍCIAS B3 - Execução Diária

Captura notícias diárias de todas as empresas listadas no mapeamento B3.
Acumula notícias em arquivos JSON individuais por empresa.

ESTRUTURA DO JSON:
{
  "empresa": {
    "ticker": "ITUB",
    "nome": "ITAU UNIBANCO HOLDING S.A.",
    "cnpj": "60.872.504/0001-23"
  },
  "ultima_atualizacao": "2025-01-01T10:00:00",
  "total_noticias": 150,
  "noticias": [...]
}
"""

import pandas as pd
import re
from pathlib import Path
from datetime import datetime, timedelta
import json
from finbr.b3 import plantao_noticias
from typing import Dict


class CapturadorNoticiasB3:
    
    def __init__(self, arquivo_mapeamento: str = "mapeamento_b3_consolidado.csv", 
                 pasta_saida: str = "balancos"):
        self.arquivo_mapeamento = Path(arquivo_mapeamento)
        self.pasta_saida = Path(pasta_saida)
        self.pasta_saida.mkdir(exist_ok=True)
        
    def _extrair_ticker_base(self, ticker: str) -> str:
        """Remove número da classe: ITUB3 -> ITUB"""
        if not ticker:
            return ""
        return re.sub(r'\d+$', '', ticker.strip())
    
    def _carregar_empresas(self) -> pd.DataFrame:
        """Carrega lista de empresas do CSV."""
        df = pd.read_csv(self.arquivo_mapeamento, sep=';', encoding='utf-8-sig')
        df['ticker_base'] = df['ticker'].apply(self._extrair_ticker_base)
        return df.drop_duplicates(subset=['ticker_base'], keep='first')
    
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
    
    def _buscar_noticias_empresa(self, ticker_base: str, data_inicio: str, data_fim: str) -> pd.DataFrame:
        """Busca notícias filtrando por ticker base e menções no texto."""
        print(f"  🔍 Buscando notícias para {ticker_base}...")
        
        noticias_raw = plantao_noticias.get(inicio=data_inicio, fim=data_fim)
        
        if not noticias_raw:
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
        
        # Filtro 1: Ticker exato (sem classe)
        mask_ticker = df["ticker"].fillna("").str.upper().apply(self._extrair_ticker_base).eq(ticker_base)
        
        # Filtro 2: Menção no texto
        mask_texto = (
            df[["empresa", "titulo", "headline", "conteudo"]]
            .fillna("")
            .agg(" ".join, axis=1)
            .str.upper()
            .str.contains(rf"\b{re.escape(ticker_base)}\b|\({re.escape(ticker_base)}\)", regex=True)
        )
        
        df_filtrado = df[mask_ticker | mask_texto].copy()
        
        if not df_filtrado.empty:
            print(f"  ✅ {len(df_filtrado)} notícia(s) encontrada(s)")
        
        return df_filtrado
    
    def _carregar_arquivo_existente(self, caminho: Path) -> Dict:
        """Carrega JSON existente ou retorna estrutura vazia."""
        if caminho.exists():
            with open(caminho, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"noticias": []}
    
    def _processar_empresa(self, row: pd.Series, data_inicio: str, data_fim: str) -> bool:
        """Processa e acumula notícias de uma empresa."""
        ticker_base = row['ticker_base']
        
        pasta_empresa = self.pasta_saida / ticker_base
        pasta_empresa.mkdir(exist_ok=True)
        
        df_noticias = self._buscar_noticias_empresa(ticker_base, data_inicio, data_fim)
        
        if df_noticias.empty:
            return False
        
        arquivo_json = pasta_empresa / "noticias.json"
        dados_existentes = self._carregar_arquivo_existente(arquivo_json)
        
        ids_existentes = {n.get('id') for n in dados_existentes.get('noticias', [])}
        
        noticias_novas = []
        for _, noticia in df_noticias.iterrows():
            noticia_id = noticia.get('id')
            
            if noticia_id and noticia_id in ids_existentes:
                continue
            
            data_hora_obj = noticia.get('data_hora')
            if isinstance(data_hora_obj, str):
                data_hora_obj = pd.to_datetime(data_hora_obj)
            
            noticias_novas.append({
                "data": data_hora_obj.strftime('%Y-%m-%d') if data_hora_obj else None,
                "data_hora": data_hora_obj.strftime('%Y-%m-%d %H:%M:%S') if data_hora_obj else None,
                "titulo": noticia.get('titulo', ''),
                "headline": noticia.get('headline', ''),
                "conteudo": noticia.get('conteudo'),
                "url": noticia.get('url', ''),
                "id": noticia_id,
                "categoria": self._classificar_noticia(noticia.get('titulo', ''), noticia.get('headline', ''))
            })
            
            if noticia_id:
                ids_existentes.add(noticia_id)
        
        if not noticias_novas:
            return False
        
        todas_noticias = noticias_novas + dados_existentes.get('noticias', [])
        todas_noticias.sort(key=lambda x: x.get('data_hora', ''), reverse=True)
        
        dados_finais = {
            "empresa": {
                "ticker": ticker_base,
                "nome": row.get('empresa', ''),
                "cnpj": row.get('cnpj', '')
            },
            "ultima_atualizacao": datetime.now().isoformat(),
            "total_noticias": len(todas_noticias),
            "noticias": todas_noticias
        }
        
        with open(arquivo_json, 'w', encoding='utf-8') as f:
            json.dump(dados_finais, f, ensure_ascii=False, indent=2)
        
        print(f"  💾 {len(noticias_novas)} nova(s) | Total: {len(todas_noticias)}")
        return True
    
    def executar(self, dias_retroativos: int = 1):
        """Executa captura para todas as empresas."""
        print("="*70)
        print("📰 CAPTURADOR DE NOTÍCIAS B3")
        print("="*70)
        
        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=dias_retroativos)
        
        print(f"\n📅 Período: {data_inicio.strftime('%Y-%m-%d')} a {data_fim.strftime('%Y-%m-%d')}")
        
        df_empresas = self._carregar_empresas()
        print(f"✅ {len(df_empresas)} empresas únicas\n")
        
        empresas_com_noticias = 0
        
        for idx, (_, row) in enumerate(df_empresas.iterrows(), 1):
            print(f"[{idx}/{len(df_empresas)}] {row['ticker_base']} - {row.get('empresa', '')[:50]}...")
            
            try:
                if self._processar_empresa(row, data_inicio.strftime('%Y-%m-%d'), data_fim.strftime('%Y-%m-%d')):
                    empresas_com_noticias += 1
            except Exception as e:
                print(f"  ❌ Erro: {e}")
        
        print(f"\n{'='*70}")
        print(f"✅ Processadas: {len(df_empresas)} | Com notícias: {empresas_com_noticias}")
        print(f"💾 Salvos em: {self.pasta_saida}/")
        print("="*70)


def main():
    capturador = CapturadorNoticiasB3()
    capturador.executar(dias_retroativos=1)


if __name__ == "__main__":
    main()
