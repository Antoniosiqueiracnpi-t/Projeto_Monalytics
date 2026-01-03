"""
CAPTURADOR DE NOTÍCIAS DO MERCADO FINANCEIRO
============================================
Janeiro 2025

Agrega notícias de portais financeiros brasileiros:
- Investing.com
- Valor Econômico
- InfoMoney
- Money Times

SAÍDA: balancos/NOTICIAS/noticias_mercado.json

EXECUÇÃO:
python src/capturar_noticias.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

import feedparser
import pytz
import re

# Timezone Brasil
BR_TZ = pytz.timezone('America/Sao_Paulo')

# User-Agent para evitar bloqueios em RSS
feedparser.USER_AGENT = "Mozilla/5.0 (MonalisaResearch; +https://monalisaresearch.com)"


# ======================================================================================
# CONFIGURAÇÃO
# ======================================================================================

OUTPUT_DIR = Path("balancos") / "NOTICIAS"
OUTPUT_FILE = "noticias_mercado.json"


# ======================================================================================
# UTILITÁRIOS DE EXTRAÇÃO
# ======================================================================================

def normalizar_titulo(titulo: str) -> str:
    """Normaliza título para comparação (evita duplicatas)."""
    titulo = (titulo or "").strip().lower()
    titulo = re.sub(r"\s+", " ", titulo)
    return titulo


def extrair_imagem(entry) -> str:
    """Extrai URL da imagem do RSS feed."""
    # Tenta múltiplas fontes de imagem no RSS
    try:
        if hasattr(entry, "media_content") and entry.media_content:
            return entry.media_content[0].get("url", "")
    except:
        pass
    
    try:
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            return entry.media_thumbnail[0].get("url", "")
    except:
        pass
    
    try:
        if hasattr(entry, "enclosures") and entry.enclosures:
            return entry.enclosures[0].get("href", "")
    except:
        pass
    
    try:
        html = getattr(entry, "summary", "") or ""
        match = re.search(r'<img[^>]+src="([^"]+)"', html)
        if match:
            return match.group(1)
    except:
        pass
    
    return ""


# ======================================================================================
# SCRAPERS POR PORTAL
# ======================================================================================

def coletar_investing(limite: int, titulos_usados: Set[str]) -> List[Dict]:
    """Coleta notícias do Investing.com."""
    feeds = [
        "https://br.investing.com/rss/news.rss",
        "https://br.investing.com/rss/news_285.rss",  # Mercados
        "https://br.investing.com/rss/news_95.rss",   # Análises
    ]
    
    todas_entradas = []
    
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in getattr(feed, "entries", []) or []:
                try:
                    # Parsear timestamp
                    if hasattr(entry, "published_parsed"):
                        dt_utc = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc)
                        entry.dt_local = dt_utc.astimezone(BR_TZ)
                    else:
                        entry.dt_local = datetime.now(BR_TZ)
                except:
                    entry.dt_local = datetime.now(BR_TZ)
                
                todas_entradas.append(entry)
        except Exception as e:
            print(f"⚠️  Erro no feed Investing {feed_url}: {e}")
            continue
    
    if not todas_entradas:
        return []
    
    # Ordenar por data (mais recentes primeiro)
    todas_entradas.sort(key=lambda x: x.dt_local, reverse=True)
    
    # Extrair notícias únicas
    noticias = []
    titulos_locais = set()
    
    for entry in todas_entradas:
        if len(noticias) >= limite:
            break
        
        try:
            titulo = (entry.title or "").strip().replace("[", "").replace("]", "")
            titulo_norm = normalizar_titulo(titulo)
            
            if not titulo_norm or titulo_norm in titulos_locais or titulo_norm in titulos_usados:
                continue
            
            link = entry.link
            horario = entry.dt_local.strftime("%H:%M")
            imagem = extrair_imagem(entry)
            
            titulos_locais.add(titulo_norm)
            titulos_usados.add(titulo_norm)
            
            noticias.append({
                "titulo": titulo,
                "link": link,
                "horario": horario,
                "imagem": imagem
            })
        except:
            continue
    
    return noticias


def coletar_valor(limite: int, titulos_usados: Set[str]) -> List[Dict]:
    """Coleta notícias do Valor Econômico."""
    feeds = [
        "https://valor.globo.com/rss/ultimas/",
        "https://pox.globo.com/rss/valor",
    ]
    
    todas_entradas = []
    
    for feed_url in feeds:
        try:
            feed = feedparser.parse(
                feed_url,
                request_headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/rss+xml, application/xml;q=0.9,*/*;q=0.8",
                }
            )
            
            for entry in getattr(feed, "entries", []) or []:
                try:
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        dt_utc = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc)
                        entry.dt_local = dt_utc.astimezone(BR_TZ)
                    else:
                        entry.dt_local = datetime.now(BR_TZ)
                except:
                    entry.dt_local = datetime.now(BR_TZ)
                
                todas_entradas.append(entry)
        except Exception as e:
            print(f"⚠️  Erro no feed Valor {feed_url}: {e}")
            continue
    
    if not todas_entradas:
        return []
    
    todas_entradas.sort(key=lambda x: x.dt_local, reverse=True)
    
    noticias = []
    titulos_locais = set()
    
    for entry in todas_entradas:
        if len(noticias) >= limite:
            break
        
        try:
            titulo = (entry.title or "").strip().replace("[", "").replace("]", "")
            titulo_norm = normalizar_titulo(titulo)
            
            if not titulo_norm or titulo_norm in titulos_locais or titulo_norm in titulos_usados:
                continue
            
            link = entry.link
            horario = entry.dt_local.strftime("%H:%M")
            imagem = extrair_imagem(entry)
            
            titulos_locais.add(titulo_norm)
            titulos_usados.add(titulo_norm)
            
            noticias.append({
                "titulo": titulo,
                "link": link,
                "horario": horario,
                "imagem": imagem
            })
        except:
            continue
    
    return noticias


def coletar_infomoney(limite: int, titulos_usados: Set[str]) -> List[Dict]:
    """Coleta notícias do InfoMoney."""
    feeds = ["https://www.infomoney.com.br/feed/"]
    
    todas_entradas = []
    
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in getattr(feed, "entries", []) or []:
                try:
                    if hasattr(entry, "published_parsed"):
                        dt_utc = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc)
                        entry.dt_local = dt_utc.astimezone(BR_TZ)
                    else:
                        entry.dt_local = datetime.now(BR_TZ)
                except:
                    entry.dt_local = datetime.now(BR_TZ)
                
                todas_entradas.append(entry)
        except Exception as e:
            print(f"⚠️  Erro no feed InfoMoney: {e}")
            continue
    
    if not todas_entradas:
        return []
    
    todas_entradas.sort(key=lambda x: x.dt_local, reverse=True)
    
    noticias = []
    titulos_locais = set()
    
    for entry in todas_entradas:
        if len(noticias) >= limite:
            break
        
        try:
            titulo = (entry.title or "").strip().replace("[", "").replace("]", "")
            titulo_norm = normalizar_titulo(titulo)
            
            if not titulo_norm or titulo_norm in titulos_locais or titulo_norm in titulos_usados:
                continue
            
            link = entry.link
            horario = entry.dt_local.strftime("%H:%M")
            imagem = extrair_imagem(entry)
            
            titulos_locais.add(titulo_norm)
            titulos_usados.add(titulo_norm)
            
            noticias.append({
                "titulo": titulo,
                "link": link,
                "horario": horario,
                "imagem": imagem
            })
        except:
            continue
    
    return noticias


def coletar_moneytimes(limite: int, titulos_usados: Set[str]) -> List[Dict]:
    """Coleta notícias do Money Times."""
    feeds = ["https://www.moneytimes.com.br/feed/"]
    
    todas_entradas = []
    
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in getattr(feed, "entries", []) or []:
                try:
                    if hasattr(entry, "published_parsed"):
                        dt_utc = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc)
                        entry.dt_local = dt_utc.astimezone(BR_TZ)
                    else:
                        entry.dt_local = datetime.now(BR_TZ)
                except:
                    entry.dt_local = datetime.now(BR_TZ)
                
                todas_entradas.append(entry)
        except Exception as e:
            print(f"⚠️  Erro no feed Money Times: {e}")
            continue
    
    if not todas_entradas:
        return []
    
    todas_entradas.sort(key=lambda x: x.dt_local, reverse=True)
    
    noticias = []
    titulos_locais = set()
    
    for entry in todas_entradas:
        if len(noticias) >= limite:
            break
        
        try:
            titulo = (entry.title or "").strip().replace("[", "").replace("]", "")
            titulo_norm = normalizar_titulo(titulo)
            
            if not titulo_norm or titulo_norm in titulos_locais or titulo_norm in titulos_usados:
                continue
            
            link = entry.link
            horario = entry.dt_local.strftime("%H:%M")
            imagem = extrair_imagem(entry)
            
            titulos_locais.add(titulo_norm)
            titulos_usados.add(titulo_norm)
            
            noticias.append({
                "titulo": titulo,
                "link": link,
                "horario": horario,
                "imagem": imagem
            })
        except:
            continue
    
    return noticias


# ======================================================================================
# AGREGADOR PRINCIPAL
# ======================================================================================

def agregar_noticias() -> Dict:
    """
    Agrega notícias de todos os portais.
    
    Returns:
        {
            'ultima_atualizacao': str,
            'total_noticias': int,
            'portais': {
                'Investing.com': [...],
                'Valor Econômico': [...],
                ...
            }
        }
    """
    print(f"\n{'='*70}")
    print(f"📰 CAPTURANDO NOTÍCIAS DO MERCADO")
    print(f"{'='*70}\n")
    
    titulos_usados = set()
    portais_noticias = {}
    total = 0
    
    # Configuração: (Nome Portal, Função Coleta, Limite)
    configuracao = [
        ("Investing.com", coletar_investing, 5),
        ("Valor Econômico", coletar_valor, 4),
        ("InfoMoney", coletar_infomoney, 4),
        ("Money Times", coletar_moneytimes, 4),
    ]
    
    for nome_portal, funcao_coleta, limite in configuracao:
        print(f"Coletando {nome_portal}...", end=" ")
        
        try:
            noticias = funcao_coleta(limite, titulos_usados)
            
            if noticias:
                portais_noticias[nome_portal] = noticias
                total += len(noticias)
                print(f"✅ {len(noticias)} notícias")
            else:
                print("⚠️  sem dados")
        except Exception as e:
            print(f"❌ erro: {e}")
            continue
    
    print(f"\n{'='*70}")
    print(f"Total de notícias: {total}")
    print(f"{'='*70}\n")
    
    return {
        'ultima_atualizacao': datetime.now(BR_TZ).isoformat(),
        'total_noticias': total,
        'portais': portais_noticias
    }


# ======================================================================================
# SALVAMENTO
# ======================================================================================

def salvar_noticias(dados: Dict) -> bool:
    """Salva notícias em JSON."""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        arquivo = OUTPUT_DIR / OUTPUT_FILE
        
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Arquivo salvo: {arquivo}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")
        return False


# ======================================================================================
# EXIBIÇÃO
# ======================================================================================

def exibir_resumo(dados: Dict):
    """Exibe resumo das notícias capturadas."""
    print(f"\n{'='*70}")
    print(f"📋 RESUMO DAS NOTÍCIAS")
    print(f"{'='*70}")
    
    total = dados.get('total_noticias', 0)
    print(f"Total capturado: {total} notícias")
    print()
    
    portais = dados.get('portais', {})
    
    for nome_portal, noticias in portais.items():
        print(f"{nome_portal}: {len(noticias)} notícias")
        for i, noticia in enumerate(noticias[:2], 1):  # Mostra só as 2 primeiras
            print(f"  {i}. [{noticia['horario']}] {noticia['titulo'][:60]}...")
        if len(noticias) > 2:
            print(f"  ... e mais {len(noticias) - 2}")
        print()
    
    print(f"{'='*70}\n")


# ======================================================================================
# MAIN
# ======================================================================================

def main():
    try:
        # Importar feedparser aqui para verificar se está instalado
        import feedparser
    except ImportError:
        print("❌ feedparser não instalado: pip install feedparser")
        return
    
    # Agregar notícias
    dados = agregar_noticias()
    
    # Exibir resumo
    exibir_resumo(dados)
    
    # Salvar
    salvar_noticias(dados)


if __name__ == "__main__":
    main()
