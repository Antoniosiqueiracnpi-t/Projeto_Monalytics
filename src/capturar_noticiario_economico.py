"""
CAPTURADOR DE NOTÍCIAS DO MERCADO FINANCEIRO - VERSÃO MELHORADA
==================================================================
Janeiro 2025

Melhorias:
- Logs detalhados para debug
- Tratamento robusto de erros
- Validação de dados
- Retry automático em falhas temporárias
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

import feedparser
import pytz
import re
import hashlib

# Timezone Brasil
BR_TZ = pytz.timezone('America/Sao_Paulo')

# User-Agent para evitar bloqueios
feedparser.USER_AGENT = "Mozilla/5.0 (MonalisaResearch; +https://monalisaresearch.com)"

# Configuração
OUTPUT_DIR = Path("balancos") / "NOTICIAS"
OUTPUT_FILE = "noticias_mercado.json"

# Controle de erros
MAX_RETRIES = 3
RETRY_DELAY = 2  # segundos


# ======================================================================================
# UTILITÁRIOS
# ======================================================================================

def log(mensagem: str, nivel: str = "INFO"):
    """Log com timestamp."""
    agora = datetime.now(BR_TZ).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{agora}] [{nivel}] {mensagem}")


def normalizar_titulo(titulo: str) -> str:
    """Normaliza título para comparação."""
    titulo = (titulo or "").strip().lower()
    titulo = re.sub(r"\s+", " ", titulo)
    return titulo


def gerar_id(titulo: str, link: str) -> str:
    """Gera ID único."""
    chave = f"{titulo}{link}".encode('utf-8')
    return hashlib.md5(chave).hexdigest()[:12]


def categorizar_noticia(titulo: str) -> str:
    """Categoriza notícia."""
    titulo_lower = titulo.lower()
    
    if any(palavra in titulo_lower for palavra in ['governo', 'lula', 'congresso', 'senado', 'câmara']):
        return 'Política'
    if any(palavra in titulo_lower for palavra in ['eua', 'china', 'europa', 'venezuela', 'mundial']):
        return 'Internacional'
    if any(palavra in titulo_lower for palavra in ['petróleo', 'ouro', 'commodity', 'minério']):
        return 'Commodities'
    if any(palavra in titulo_lower for palavra in ['bitcoin', 'cripto', 'blockchain']):
        return 'Criptomoedas'
    if any(palavra in titulo_lower for palavra in ['empresa', 'ação', 'ações', 'lucro', 'balanço']):
        return 'Empresas'
    if any(palavra in titulo_lower for palavra in ['inflação', 'juros', 'selic', 'pib', 'ipca']):
        return 'Economia'
    if any(palavra in titulo_lower for palavra in ['bolsa', 'ibovespa', 'mercado', 'índice', 'dólar']):
        return 'Mercados'
    
    return 'Geral'


def extrair_tags(titulo: str) -> List[str]:
    """Extrai tags do título."""
    tags = []
    titulo_lower = titulo.lower()
    
    mapa_tags = {
        'venezuela': ['Venezuela'],
        'eua': ['EUA'],
        'lula': ['Lula'],
        'petróleo': ['Petróleo'],
        'bitcoin': ['Bitcoin', 'Cripto'],
        'dólar': ['Dólar'],
        'ibovespa': ['Ibovespa'],
        'inflação': ['Inflação'],
        'juros': ['Juros'],
    }
    
    for palavra, tag_list in mapa_tags.items():
        if palavra in titulo_lower:
            tags.extend(tag_list)
    
    return list(set(tags))[:5]


def gerar_resumo(titulo: str) -> str:
    """Gera resumo curto."""
    palavras = titulo.split()
    if len(palavras) <= 12:
        return titulo
    return ' '.join(palavras[:12]) + '...'


def extrair_imagem(entry) -> str:
    """Extrai URL da imagem."""
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
# COLETOR GENÉRICO COM RETRY
# ======================================================================================

def coletar_feed_com_retry(
    nome_portal: str,
    feed_urls: List[str],
    limite: int,
    titulos_usados: Set[str],
    logo_fallback: str = ""
) -> List[Dict]:
    """
    Coleta notícias de um portal com retry automático.
    """
    todas_entradas = []
    
    for feed_url in feed_urls:
        for tentativa in range(MAX_RETRIES):
            try:
                log(f"Tentando {nome_portal} ({feed_url})... tentativa {tentativa + 1}/{MAX_RETRIES}")
                
                feed = feedparser.parse(
                    feed_url,
                    request_headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "application/rss+xml, application/xml;q=0.9,*/*;q=0.8",
                    }
                )
                
                # Verifica se feed tem dados
                if not hasattr(feed, "entries") or not feed.entries:
                    log(f"Feed vazio: {feed_url}", "WARN")
                    break
                
                log(f"✅ Feed carregado: {len(feed.entries)} entradas brutas")
                
                # Processa entradas
                for entry in feed.entries:
                    try:
                        if hasattr(entry, "published_parsed") and entry.published_parsed:
                            dt_utc = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc)
                            entry.dt_local = dt_utc.astimezone(BR_TZ)
                        else:
                            entry.dt_local = datetime.now(BR_TZ)
                    except Exception as e:
                        log(f"Erro ao parsear data: {e}", "WARN")
                        entry.dt_local = datetime.now(BR_TZ)
                    
                    todas_entradas.append(entry)
                
                # Sucesso - não precisa de retry
                break
                
            except Exception as e:
                log(f"❌ Erro no feed {feed_url}: {e}", "ERROR")
                
                if tentativa < MAX_RETRIES - 1:
                    log(f"⏳ Aguardando {RETRY_DELAY}s antes de tentar novamente...", "WARN")
                    time.sleep(RETRY_DELAY)
                else:
                    log(f"❌ Falha após {MAX_RETRIES} tentativas", "ERROR")
    
    if not todas_entradas:
        log(f"❌ Nenhuma entrada coletada de {nome_portal}", "ERROR")
        return []
    
    # Ordenar por data
    todas_entradas.sort(key=lambda x: x.dt_local, reverse=True)
    log(f"📊 Total de entradas após ordenação: {len(todas_entradas)}")
    
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
            imagem = extrair_imagem(entry) or logo_fallback
            
            titulos_locais.add(titulo_norm)
            titulos_usados.add(titulo_norm)
            
            noticias.append({
                "id": gerar_id(titulo, link),
                "titulo": titulo,
                "link": link,
                "horario": horario,
                "imagem": imagem,
                "categoria": categorizar_noticia(titulo),
                "tags": extrair_tags(titulo),
                "resumo": gerar_resumo(titulo),
                "fonte": nome_portal
            })
        except Exception as e:
            log(f"Erro ao processar entrada: {e}", "WARN")
            continue
    
    log(f"✅ {nome_portal}: {len(noticias)} notícias extraídas")
    return noticias


# ======================================================================================
# AGREGADOR PRINCIPAL
# ======================================================================================

def agregar_noticias() -> Dict:
    """Agrega notícias de todos os portais."""
    log("="*70)
    log("📰 INICIANDO CAPTURA DE NOTÍCIAS DO MERCADO")
    log("="*70)
    
    titulos_usados = set()
    portais_noticias = {}
    total = 0
    
    # Configuração de portais
    configuracao = [
        {
            "nome": "Investing.com",
            "feeds": [
                "https://br.investing.com/rss/news.rss",
                "https://br.investing.com/rss/news_285.rss",
                "https://br.investing.com/rss/news_95.rss",
            ],
            "limite": 5,
            "logo": ""
        },
        {
            "nome": "Valor Econômico",
            "feeds": [
                "https://valor.globo.com/rss/ultimas/",
                "https://pox.globo.com/rss/valor",
            ],
            "limite": 4,
            "logo": ""
        },
        {
            "nome": "InfoMoney",
            "feeds": ["https://www.infomoney.com.br/feed/"],
            "limite": 4,
            "logo": ""
        },
        {
            "nome": "Money Times",
            "feeds": ["https://www.moneytimes.com.br/feed/"],
            "limite": 4,
            "logo": "https://www.moneytimes.com.br/wp-content/themes/moneytimes/assets/img/logo-mt.png"
        },
    ]
    
    # Coleta de cada portal
    for config in configuracao:
        log(f"\n🔄 Processando {config['nome']}...")
        
        try:
            noticias = coletar_feed_com_retry(
                nome_portal=config['nome'],
                feed_urls=config['feeds'],
                limite=config['limite'],
                titulos_usados=titulos_usados,
                logo_fallback=config['logo']
            )
            
            if noticias:
                portais_noticias[config['nome']] = noticias
                total += len(noticias)
                log(f"✅ {config['nome']}: {len(noticias)} notícias adicionadas")
            else:
                log(f"⚠️  {config['nome']}: Nenhuma notícia coletada", "WARN")
                
        except Exception as e:
            log(f"❌ Erro crítico em {config['nome']}: {e}", "ERROR")
            continue
    
    log("\n" + "="*70)
    log(f"📊 TOTAL CAPTURADO: {total} notícias de {len(portais_noticias)} portais")
    log("="*70)
    
    if total == 0:
        log("❌ ALERTA: Nenhuma notícia foi capturada!", "ERROR")
        raise Exception("Falha total na captura de notícias")
    
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
        log(f"💾 Salvando dados em {OUTPUT_DIR / OUTPUT_FILE}...")
        
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        arquivo = OUTPUT_DIR / OUTPUT_FILE
        
        # Salva com indentação bonita
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        # Verifica se arquivo foi criado
        if not arquivo.exists():
            raise Exception("Arquivo não foi criado!")
        
        tamanho = arquivo.stat().st_size
        log(f"✅ Arquivo salvo com sucesso! Tamanho: {tamanho} bytes")
        
        return True
        
    except Exception as e:
        log(f"❌ Erro ao salvar arquivo: {e}", "ERROR")
        return False


# ======================================================================================
# EXIBIÇÃO
# ======================================================================================

def exibir_resumo(dados: Dict):
    """Exibe resumo das notícias."""
    log("\n" + "="*70)
    log("📋 RESUMO DAS NOTÍCIAS CAPTURADAS")
    log("="*70)
    
    total = dados.get('total_noticias', 0)
    log(f"Total: {total} notícias")
    
    portais = dados.get('portais', {})
    
    for nome_portal, noticias in portais.items():
        log(f"\n{nome_portal}: {len(noticias)} notícias")
        for i, noticia in enumerate(noticias[:3], 1):
            log(f"  {i}. [{noticia['horario']}] {noticia['titulo'][:70]}...")
        if len(noticias) > 3:
            log(f"  ... e mais {len(noticias) - 3}")
    
    log("\n" + "="*70)


# ======================================================================================
# MAIN
# ======================================================================================

def main():
    """Função principal com tratamento de erros."""
    codigo_saida = 0
    
    try:
        log("🚀 INICIANDO SCRIPT DE CAPTURA DE NOTÍCIAS")
        log(f"Horário: {datetime.now(BR_TZ).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Verifica dependências
        try:
            import feedparser
            log(f"✅ feedparser versão: {feedparser.__version__}")
        except ImportError:
            log("❌ feedparser não instalado!", "ERROR")
            log("Execute: pip install feedparser", "ERROR")
            sys.exit(1)
        
        # Agregar notícias
        dados = agregar_noticias()
        
        # Exibir resumo
        exibir_resumo(dados)
        
        # Salvar
        if not salvar_noticias(dados):
            raise Exception("Falha ao salvar arquivo")
        
        log("\n✅ SCRIPT FINALIZADO COM SUCESSO!")
        
    except Exception as e:
        log(f"\n❌ ERRO FATAL: {e}", "ERROR")
        log("Script abortado devido a erro crítico", "ERROR")
        codigo_saida = 1
    
    finally:
        log(f"Código de saída: {codigo_saida}")
        sys.exit(codigo_saida)


if __name__ == "__main__":
    main()
