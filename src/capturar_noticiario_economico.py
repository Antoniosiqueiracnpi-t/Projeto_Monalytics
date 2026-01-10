#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
capturar_noticiario_economico.py
================================
Captura noticias economicas de multiplos portais via RSS com suporte a imagens.

Baseado no financial-news-bot da Monalisa Research.
Formato de saida: JSON compativel com o site Monalytics.

Portais suportados:
- Investing.com (BR)
- Valor Economico
- InfoMoney
- Money Times
- CNN Brasil Business
- Estadao Economia

Autor: Monalisa Research
"""

from __future__ import annotations

import json
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field, asdict

# Dependencias
try:
    import feedparser
    feedparser.USER_AGENT = "Mozilla/5.0 (MonalisaResearchBot/2.0; +https://monalytics.com.br)"
except ImportError:
    print("ERRO: feedparser nao instalado. Execute: pip install feedparser")
    raise

try:
    import pytz
    BR_TZ = pytz.timezone("America/Sao_Paulo")
except ImportError:
    BR_TZ = None
    print("AVISO: pytz nao instalado. Usando UTC.")


# =============================================================================
# CONFIGURACAO
# =============================================================================

# Caminhos de saida
OUTPUT_DIR = Path("balancos/NOTICIAS")
OUTPUT_FILE = OUTPUT_DIR / "noticias_mercado.json"
ULTIMA_ATUALIZACAO_FILE = Path("site/data/ultima_atualizacao.json")

# Limite de noticias por portal
DEFAULT_LIMIT_PER_PORTAL = 5

# Maximo de noticias totais no JSON (evita arquivo muito grande)
MAX_NOTICIAS_TOTAL = 100

# Horas para manter noticias antigas
HORAS_MANTER_NOTICIAS = 48


# =============================================================================
# CONFIGURACAO DOS PORTAIS RSS
# =============================================================================

PORTAIS_CONFIG = {
    "investing": {
        "nome": "Investing.com",
        "emoji": "⚡",
        "feeds": [
            "https://br.investing.com/rss/news.rss",
            "https://br.investing.com/rss/news_285.rss",  # Mercados
            "https://br.investing.com/rss/news_95.rss",   # Economia
        ],
        "limite": 6,
        "prioridade": 1,
    },
    "valor": {
        "nome": "Valor Economico",
        "emoji": "📈",
        "feeds": [
            "https://valor.globo.com/rss/ultimas/",
            "https://pox.globo.com/rss/valor",
        ],
        "limite": 5,
        "prioridade": 2,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/rss+xml, application/xml;q=0.9,*/*;q=0.8",
        },
    },
    "infomoney": {
        "nome": "InfoMoney",
        "emoji": "💠",
        "feeds": [
            "https://www.infomoney.com.br/feed/",
        ],
        "limite": 5,
        "prioridade": 3,
    },
    "moneytimes": {
        "nome": "Money Times",
        "emoji": "💰",
        "feeds": [
            "https://www.moneytimes.com.br/feed/",
        ],
        "limite": 4,
        "prioridade": 4,
    },
    "cnn_business": {
        "nome": "CNN Brasil Business",
        "emoji": "📺",
        "feeds": [
            "https://www.cnnbrasil.com.br/economia/feed/",
        ],
        "limite": 4,
        "prioridade": 5,
    },
    "estadao": {
        "nome": "Estadao Economia",
        "emoji": "📰",
        "feeds": [
            "https://www.estadao.com.br/economia/feed/",
        ],
        "limite": 4,
        "prioridade": 6,
    },
}


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class Noticia:
    """Representa uma noticia capturada."""
    id: str
    titulo: str
    link: str
    fonte: str
    fonte_emoji: str
    horario: str
    data_publicacao: str
    imagem: str = ""
    resumo: str = ""
    categoria: str = "Mercado"  # Campo esperado pelo JS
    tags: List[str] = field(default_factory=list)  # Campo esperado pelo JS
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NoticiarioEconomico:
    """Container para o noticiario completo."""
    ultima_atualizacao: str
    total_noticias: int
    fontes: List[str]
    noticias: List[Dict[str, Any]]
    portais: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# FUNCOES AUXILIARES
# =============================================================================

def get_now() -> datetime:
    """Retorna datetime atual no fuso horario de Brasilia."""
    if BR_TZ:
        return datetime.now(BR_TZ)
    return datetime.utcnow()


def normalize_title(title: str) -> str:
    """Normaliza titulo para comparacao (evita duplicatas)."""
    t = (title or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^\w\s]", "", t)
    return t


def generate_id(title: str, link: str) -> str:
    """Gera ID unico para a noticia baseado em titulo e link."""
    content = f"{normalize_title(title)}:{link}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


def extract_image_from_entry(entry) -> str:
    """
    Extrai URL da imagem de uma entrada RSS.
    Tenta multiplas fontes: media_content, media_thumbnail, enclosures, summary.
    """
    # 1. media_content (padrao Media RSS)
    try:
        if hasattr(entry, "media_content") and entry.media_content:
            for media in entry.media_content:
                url = media.get("url", "")
                if url and is_valid_image_url(url):
                    return url
    except Exception:
        pass
    
    # 2. media_thumbnail
    try:
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            for thumb in entry.media_thumbnail:
                url = thumb.get("url", "")
                if url and is_valid_image_url(url):
                    return url
    except Exception:
        pass
    
    # 3. enclosures (RSS 2.0)
    try:
        if hasattr(entry, "enclosures") and entry.enclosures:
            for enc in entry.enclosures:
                url = enc.get("href", "") or enc.get("url", "")
                enc_type = enc.get("type", "")
                if url and ("image" in enc_type or is_valid_image_url(url)):
                    return url
    except Exception:
        pass
    
    # 4. Buscar <img> no summary/content
    try:
        html = getattr(entry, "summary", "") or ""
        if not html:
            content = getattr(entry, "content", [])
            if content and isinstance(content, list):
                html = content[0].get("value", "")
        
        if html:
            # Buscar src de imagem
            match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if match:
                url = match.group(1)
                if is_valid_image_url(url):
                    return url
    except Exception:
        pass
    
    return ""


def is_valid_image_url(url: str) -> bool:
    """Verifica se URL parece ser de uma imagem valida."""
    if not url:
        return False
    
    url_lower = url.lower()
    
    # Extensoes de imagem comuns
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg')
    if any(url_lower.endswith(ext) or f"{ext}?" in url_lower for ext in image_extensions):
        return True
    
    # Padroes de CDN de imagem
    image_patterns = [
        r'image', r'img', r'photo', r'media', r'cdn', 
        r'thumb', r'picture', r'figura', r'imagem'
    ]
    if any(p in url_lower for p in image_patterns):
        return True
    
    return False


def detectar_categoria(titulo: str, resumo: str = "") -> str:
    """
    Detecta categoria da noticia baseado no titulo e resumo.
    
    Categorias possiveis: Mercado, Economia, Empresas, Politica, Internacional, Cripto
    """
    texto = f"{titulo} {resumo}".lower()
    
    # Palavras-chave por categoria
    categorias = {
        "Cripto": ["bitcoin", "btc", "ethereum", "cripto", "blockchain", "token", "nft"],
        "Internacional": ["eua", "china", "europa", "fed", "powell", "trump", "biden", 
                         "guerra", "russia", "ucrania", "internacional", "global"],
        "Politica": ["lula", "governo", "congresso", "senado", "camara", "ministro",
                    "haddad", "planalto", "stf", "politica", "eleicao"],
        "Empresas": ["petrobras", "vale", "itau", "bradesco", "ambev", "weg", 
                    "magazine", "magalu", "nubank", "banco", "varejista", "ipo",
                    "fusao", "aquisicao", "lucro", "prejuizo", "balanco"],
        "Economia": ["inflacao", "ipca", "pib", "selic", "copom", "juros", "dolar",
                    "cambio", "fiscal", "divida", "orcamento", "economia", "recessao"],
        "Mercado": ["ibovespa", "b3", "bolsa", "acoes", "indice", "alta", "queda",
                   "investidor", "mercado", "pregao", "fechamento", "abertura"],
    }
    
    for categoria, palavras in categorias.items():
        for palavra in palavras:
            if palavra in texto:
                return categoria
    
    return "Mercado"  # Default


def extract_summary(entry, max_length: int = 200) -> str:
    """Extrai resumo limpo da noticia."""
    try:
        html = getattr(entry, "summary", "") or ""
        if not html:
            content = getattr(entry, "content", [])
            if content and isinstance(content, list):
                html = content[0].get("value", "")
        
        if html:
            # Remove tags HTML
            text = re.sub(r'<[^>]+>', '', html)
            # Remove espacos extras
            text = re.sub(r'\s+', ' ', text).strip()
            # Limita tamanho
            if len(text) > max_length:
                text = text[:max_length].rsplit(' ', 1)[0] + "..."
            return text
    except Exception:
        pass
    
    return ""


def parse_datetime_from_entry(entry) -> Optional[datetime]:
    """Extrai datetime da entrada RSS."""
    try:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            dt = datetime(*entry.published_parsed[:6])
            if BR_TZ:
                import pytz
                dt = pytz.utc.localize(dt).astimezone(BR_TZ)
            return dt
    except Exception:
        pass
    
    try:
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            dt = datetime(*entry.updated_parsed[:6])
            if BR_TZ:
                import pytz
                dt = pytz.utc.localize(dt).astimezone(BR_TZ)
            return dt
    except Exception:
        pass
    
    return None


# =============================================================================
# SCRAPERS POR PORTAL
# =============================================================================

def fetch_rss_news(
    portal_key: str,
    config: Dict[str, Any],
    used_titles: Set[str],
    used_ids: Set[str]
) -> List[Noticia]:
    """
    Captura noticias de um portal via RSS.
    
    Args:
        portal_key: Chave do portal (ex: "investing")
        config: Configuracao do portal
        used_titles: Set de titulos ja usados (evita duplicatas)
        used_ids: Set de IDs ja usados
    
    Returns:
        Lista de objetos Noticia
    """
    feeds = config.get("feeds", [])
    limite = config.get("limite", DEFAULT_LIMIT_PER_PORTAL)
    headers = config.get("headers", {})
    nome = config.get("nome", portal_key)
    emoji = config.get("emoji", "📰")
    
    all_entries = []
    
    for feed_url in feeds:
        try:
            # Parse do feed com headers customizados se necessario
            if headers:
                feed = feedparser.parse(feed_url, request_headers=headers)
            else:
                feed = feedparser.parse(feed_url)
            
            entries = getattr(feed, "entries", []) or []
            
            for entry in entries:
                # Adiciona datetime parseado
                entry._parsed_dt = parse_datetime_from_entry(entry) or get_now()
                all_entries.append(entry)
                
        except Exception as e:
            print(f"  [!] Erro ao buscar {feed_url}: {e}")
            continue
    
    if not all_entries:
        return []
    
    # Ordena por data (mais recentes primeiro)
    all_entries.sort(key=lambda x: x._parsed_dt, reverse=True)
    
    noticias = []
    local_seen = set()
    
    for entry in all_entries:
        if len(noticias) >= limite:
            break
        
        try:
            # Extrair titulo
            titulo = (getattr(entry, "title", "") or "").strip()
            titulo = titulo.replace("[", "").replace("]", "")
            
            if not titulo:
                continue
            
            # Verificar duplicatas
            norm_title = normalize_title(titulo)
            if norm_title in local_seen or norm_title in used_titles:
                continue
            
            # Extrair link
            link = getattr(entry, "link", "") or ""
            if not link:
                continue
            
            # Gerar ID
            noticia_id = generate_id(titulo, link)
            if noticia_id in used_ids:
                continue
            
            # Extrair datetime
            dt = entry._parsed_dt
            horario = dt.strftime("%H:%M")
            data_pub = dt.strftime("%Y-%m-%d %H:%M:%S")
            
            # Extrair imagem
            imagem = extract_image_from_entry(entry)
            
            # Extrair resumo
            resumo = extract_summary(entry)
            
            # Detectar categoria
            categoria = detectar_categoria(titulo, resumo)
            
            # Criar objeto Noticia
            noticia = Noticia(
                id=noticia_id,
                titulo=titulo,
                link=link,
                fonte=nome,
                fonte_emoji=emoji,
                horario=horario,
                data_publicacao=data_pub,
                imagem=imagem,
                resumo=resumo,
                categoria=categoria,
            )
            
            noticias.append(noticia)
            local_seen.add(norm_title)
            used_titles.add(norm_title)
            used_ids.add(noticia_id)
            
        except Exception as e:
            print(f"  [!] Erro ao processar entrada: {e}")
            continue
    
    return noticias


# =============================================================================
# FUNCAO PRINCIPAL DE CAPTURA
# =============================================================================

def capturar_noticias() -> NoticiarioEconomico:
    """
    Captura noticias de todos os portais configurados.
    
    Returns:
        NoticiarioEconomico com todas as noticias agregadas
    """
    print("\n" + "="*60)
    print("CAPTURANDO NOTICIARIO ECONOMICO")
    print("="*60)
    
    now = get_now()
    print(f"Data/Hora: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    todas_noticias: List[Noticia] = []
    noticias_por_portal: Dict[str, List[Dict[str, Any]]] = {}
    fontes_com_noticias: List[str] = []
    used_titles: Set[str] = set()
    used_ids: Set[str] = set()
    
    # Ordenar portais por prioridade
    portais_ordenados = sorted(
        PORTAIS_CONFIG.items(),
        key=lambda x: x[1].get("prioridade", 99)
    )
    
    for portal_key, config in portais_ordenados:
        nome = config.get("nome", portal_key)
        emoji = config.get("emoji", "📰")
        
        print(f"\n{emoji} Buscando: {nome}...")
        
        try:
            noticias = fetch_rss_news(portal_key, config, used_titles, used_ids)
            
            if noticias:
                todas_noticias.extend(noticias)
                fontes_com_noticias.append(nome)
                
                # Agrupar por portal (formato esperado pelo JS)
                noticias_por_portal[nome] = [n.to_dict() for n in noticias]
                
                # Contar com/sem imagem
                com_img = sum(1 for n in noticias if n.imagem)
                print(f"  [OK] {len(noticias)} noticias ({com_img} com imagem)")
            else:
                print(f"  [--] Nenhuma noticia nova")
                
        except Exception as e:
            print(f"  [ERRO] {e}")
            continue
    
    # Ordenar todas por data de publicacao (mais recentes primeiro)
    todas_noticias.sort(
        key=lambda x: x.data_publicacao,
        reverse=True
    )
    
    # Limitar total
    if len(todas_noticias) > MAX_NOTICIAS_TOTAL:
        todas_noticias = todas_noticias[:MAX_NOTICIAS_TOTAL]
    
    # Criar objeto de saida
    noticiario = NoticiarioEconomico(
        ultima_atualizacao=now.strftime("%Y-%m-%d %H:%M:%S"),
        total_noticias=len(todas_noticias),
        fontes=fontes_com_noticias,
        noticias=[n.to_dict() for n in todas_noticias],
        portais=noticias_por_portal,  # Formato esperado pelo JS
    )
    
    print(f"\n{'='*60}")
    print(f"TOTAL: {len(todas_noticias)} noticias de {len(fontes_com_noticias)} fontes")
    print(f"{'='*60}\n")
    
    return noticiario


def carregar_noticias_existentes() -> List[Dict[str, Any]]:
    """Carrega noticias existentes do JSON (para merge)."""
    if not OUTPUT_FILE.exists():
        return []
    
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("noticias", [])
    except Exception as e:
        print(f"[!] Erro ao carregar noticias existentes: {e}")
        return []


def merge_noticias(
    novas: List[Dict[str, Any]], 
    existentes: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Faz merge das noticias novas com existentes, removendo duplicatas
    e noticias muito antigas.
    """
    # Criar mapa por ID
    por_id: Dict[str, Dict[str, Any]] = {}
    
    # Adicionar existentes primeiro
    for noticia in existentes:
        nid = noticia.get("id", "")
        if nid:
            por_id[nid] = noticia
    
    # Sobrescrever/adicionar novas
    for noticia in novas:
        nid = noticia.get("id", "")
        if nid:
            por_id[nid] = noticia
    
    # Converter para lista
    todas = list(por_id.values())
    
    # Filtrar noticias muito antigas
    agora = get_now()
    limite_tempo = agora - timedelta(hours=HORAS_MANTER_NOTICIAS)
    
    noticias_filtradas = []
    for noticia in todas:
        try:
            data_str = noticia.get("data_publicacao", "")
            if data_str:
                data_pub = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
                if BR_TZ:
                    data_pub = BR_TZ.localize(data_pub)
                
                if data_pub >= limite_tempo:
                    noticias_filtradas.append(noticia)
            else:
                # Sem data, manter
                noticias_filtradas.append(noticia)
        except Exception:
            # Em caso de erro, manter
            noticias_filtradas.append(noticia)
    
    # Ordenar por data (mais recentes primeiro)
    noticias_filtradas.sort(
        key=lambda x: x.get("data_publicacao", ""),
        reverse=True
    )
    
    # Limitar total
    if len(noticias_filtradas) > MAX_NOTICIAS_TOTAL:
        noticias_filtradas = noticias_filtradas[:MAX_NOTICIAS_TOTAL]
    
    return noticias_filtradas


def salvar_noticiario(noticiario: NoticiarioEconomico) -> None:
    """Salva o noticiario em JSON."""
    # Garantir que diretorio existe
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Carregar existentes e fazer merge
    existentes = carregar_noticias_existentes()
    noticias_merged = merge_noticias(noticiario.noticias, existentes)
    
    # Atualizar contagem
    noticiario.noticias = noticias_merged
    noticiario.total_noticias = len(noticias_merged)
    
    # Coletar fontes unicas
    fontes_set = set()
    for n in noticias_merged:
        fonte = n.get("fonte", "")
        if fonte:
            fontes_set.add(fonte)
    noticiario.fontes = sorted(fontes_set)
    
    # Reagrupar por portal (para manter estrutura compativel com JS)
    portais_merged: Dict[str, List[Dict[str, Any]]] = {}
    for n in noticias_merged:
        fonte = n.get("fonte", "Outros")
        if fonte not in portais_merged:
            portais_merged[fonte] = []
        portais_merged[fonte].append(n)
    
    noticiario.portais = portais_merged
    
    # Salvar JSON principal
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(noticiario.to_dict(), f, ensure_ascii=False, indent=2)
    
    print(f"[OK] Salvo: {OUTPUT_FILE}")
    print(f"     Total: {noticiario.total_noticias} noticias")
    
    # Salvar ultima atualizacao (para o site)
    salvar_ultima_atualizacao(noticiario.ultima_atualizacao)


def salvar_ultima_atualizacao(timestamp: str) -> None:
    """Salva timestamp da ultima atualizacao para o site."""
    try:
        ULTIMA_ATUALIZACAO_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "noticias_mercado": timestamp,
            "gerado_em": get_now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        with open(ULTIMA_ATUALIZACAO_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] Salvo: {ULTIMA_ATUALIZACAO_FILE}")
        
    except Exception as e:
        print(f"[!] Erro ao salvar ultima_atualizacao: {e}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Funcao principal."""
    try:
        # Capturar noticias
        noticiario = capturar_noticias()
        
        if noticiario.total_noticias == 0:
            print("[!] Nenhuma noticia capturada.")
            return 1
        
        # Salvar
        salvar_noticiario(noticiario)
        
        print("\n[OK] Processo concluido com sucesso!")
        return 0
        
    except Exception as e:
        print(f"\n[ERRO FATAL] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
