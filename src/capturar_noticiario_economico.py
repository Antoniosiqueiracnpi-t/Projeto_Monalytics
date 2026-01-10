"""
CAPTURA DE NOTICIÁRIO ECONÔMICO (TOTALMENTE DESACOPLADO DO NOTICIÁRIO EMPRESARIAL)

- Objetivo: gerar o feed "Notícias do Mercado" consumido pelo site (SLIDE 4).
- Fonte: Google News RSS (busca por palavras-chave, NÃO por ticker de empresa).
- Saída:
    balancos/NOTICIAS/noticias_mercado.json

IMPORTANTE (imagens):
- Muitos feeds RSS (incluindo o Google News RSS) NÃO entregam imagem no XML.
- Para resolver, este script tenta (na ordem):
    1) <media:content> / <media:thumbnail> / <enclosure>
    2) <img src="..."> dentro do <description>
    3) fallback: baixar a página do link e extrair meta og:image / twitter:image

O script foi escrito para ser determinístico e reduzir conflitos de merge:
- Ordenação consistente
- Deduplicação por id SHA1
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

try:
    from zoneinfo import ZoneInfo  # py3.9+
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


# =============================================================================
# Config
# =============================================================================

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

SAO_PAULO_TZ = "America/Sao_Paulo"

# Quantidade por categoria (antes de deduplicar)
MAX_ITENS_POR_CATEGORIA = int(os.getenv("NEWS_MAX_PER_CATEGORY", "12"))

# Limite final no JSON
MAX_TOTAL_FINAL = int(os.getenv("NEWS_MAX_TOTAL", "60"))

# Delay curto para não estressar o Google News / sites
DELAY_BETWEEN_REQUESTS_SEC = float(os.getenv("NEWS_DELAY_SEC", "0.4"))

# Timeout de rede
TIMEOUT_SEC = int(os.getenv("NEWS_TIMEOUT_SEC", "15"))

# Categorias do front (o JS usa data-categoria para filtros)
CATEGORIAS_QUERY: Dict[str, str] = {
    "bolsa":   "B3 bolsa ibovespa ações resultados trimestrais",
    "economia":"Brasil economia inflação selic juros PIB fiscal",
    "exterior":"exterior EUA China Europa guerra sanções FED",
    "cripto":  "bitcoin ethereum cripto blockchain",
    "geral":   "mercados dólar petróleo minério de ferro commodities",
}

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"


# =============================================================================
# Helpers
# =============================================================================

def _now_sp() -> datetime:
    if ZoneInfo is None:
        return datetime.now()
    return datetime.now(ZoneInfo(SAO_PAULO_TZ))


def _to_sp(dt: datetime) -> datetime:
    if ZoneInfo is None:
        return dt
    if dt.tzinfo is None:
        return dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(SAO_PAULO_TZ))
    return dt.astimezone(ZoneInfo(SAO_PAULO_TZ))


def _sha1_id(titulo: str, link: str, data_hora: str) -> int:
    base = f"{(titulo or '').strip()}|{(link or '').strip()}|{(data_hora or '').strip()}"
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def _limpar_html(texto_html: str, max_len: int = 240) -> str:
    try:
        soup = BeautifulSoup(texto_html or "", "html.parser")
        texto = " ".join(soup.get_text(" ").split()).strip()
        if len(texto) > max_len:
            return texto[: max_len - 3] + "..."
        return texto
    except Exception:
        s = str(texto_html or "").strip()
        return s[: max_len - 3] + "..." if len(s) > max_len else s


def _parse_pubdate(item) -> Tuple[str, str, str]:
    """Retorna (data_yyyy_mm_dd, data_hora_iso, horario_hh_mm) em fuso SP."""
    dt = None
    try:
        pub = item.find("pubDate")
        if pub and pub.text:
            dt = parsedate_to_datetime(pub.text.strip())
    except Exception:
        dt = None

    if dt is None:
        dt = _now_sp()
    else:
        dt = _to_sp(dt)

    data = dt.strftime("%Y-%m-%d")
    data_hora_iso = dt.strftime("%Y-%m-%d %H:%M:%S")
    horario = dt.strftime("%H:%M")
    return data, data_hora_iso, horario


def _first_text(tag) -> str:
    try:
        return (tag.text or "").strip()
    except Exception:
        return ""


def _find_image_in_rss_item(item) -> Optional[str]:
    """Tenta achar imagem no próprio XML (media/enclosure/description img)."""
    for name in ("media:content", "media:thumbnail"):
        t = item.find(name)
        if t and t.get("url"):
            return str(t.get("url")).strip() or None

    enc = item.find("enclosure")
    if enc and enc.get("url"):
        return str(enc.get("url")).strip() or None

    desc = item.find("description")
    if desc and desc.text:
        try:
            soup = BeautifulSoup(desc.text, "html.parser")
            img = soup.find("img")
            if img and img.get("src"):
                return str(img.get("src")).strip() or None
        except Exception:
            pass

    return None


def _extract_og_image_from_html(html: str) -> Optional[str]:
    """Extrai og:image / twitter:image do HTML."""
    try:
        soup = BeautifulSoup(html or "", "html.parser")
        for prop in ("og:image", "twitter:image", "twitter:image:src"):
            meta = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
            if meta and meta.get("content"):
                url = str(meta.get("content")).strip()
                if url:
                    return url
    except Exception:
        return None
    return None


class _ImageCache:
    def __init__(self):
        self._cache: Dict[str, Optional[str]] = {}

    def get(self, url: str) -> Optional[str]:
        return self._cache.get(url)

    def set(self, url: str, img: Optional[str]) -> None:
        self._cache[url] = img


_IMG_CACHE = _ImageCache()


def _buscar_imagem_por_og(link: str) -> Optional[str]:
    if not link:
        return None

    cached = _IMG_CACHE.get(link)
    if cached is not None:
        return cached

    try:
        r = requests.get(link, headers=HEADERS, timeout=TIMEOUT_SEC)
        if r.status_code != 200:
            _IMG_CACHE.set(link, None)
            return None
        img = _extract_og_image_from_html(r.text)
        _IMG_CACHE.set(link, img)
        return img
    except Exception:
        _IMG_CACHE.set(link, None)
        return None


def _normalizar_dominio(url: str) -> str:
    try:
        netloc = (urlparse(url).netloc or "").lower().replace("www.", "").strip()
        return netloc
    except Exception:
        return ""


def _fonte_por_dominio(url: str, fallback: str = "") -> str:
    dom = _normalizar_dominio(url)
    if not dom:
        return fallback or "Desconhecida"

    fontes = {
        "infomoney.com.br": "InfoMoney",
        "valor.globo.com": "Valor Econômico",
        "valorinveste.globo.com": "Valor Investe",
        "moneytimes.com.br": "Money Times",
        "estadao.com.br": "Estadão",
        "folha.uol.com.br": "Folha",
        "g1.globo.com": "G1",
        "uol.com.br": "UOL",
        "terra.com.br": "Terra",
        "cnnbrasil.com.br": "CNN Brasil",
        "investnews.com.br": "InvestNews",
        "seudinheiro.com": "Seu Dinheiro",
        "bloomberg.com": "Bloomberg",
        "reuters.com": "Reuters",
    }
    for k, v in fontes.items():
        if dom.endswith(k):
            return v

    return (dom.split(".")[0] or "Desconhecida").capitalize()


# =============================================================================
# Google News RSS
# =============================================================================

def _rss_google_news(query: str, max_itens: int) -> List[Dict]:
    params = {"q": query, "hl": "pt-BR", "gl": "BR", "ceid": "BR:pt-419"}
    r = requests.get(GOOGLE_NEWS_RSS, params=params, headers=HEADERS, timeout=TIMEOUT_SEC)
    if r.status_code != 200:
        return []

    soup = BeautifulSoup(r.content, "xml")
    items = soup.find_all("item") or []

    saida: List[Dict] = []
    for it in items[:max_itens]:
        titulo = _first_text(it.find("title")) or "Título não disponível"
        link = _first_text(it.find("link"))
        desc = _first_text(it.find("description"))

        data, data_hora, horario = _parse_pubdate(it)

        fonte_rss = ""
        src = it.find("source")
        if src and src.text:
            fonte_rss = src.text.strip()

        fonte = fonte_rss or _fonte_por_dominio(link)

        imagem = _find_image_in_rss_item(it)
        if not imagem and link:
            imagem = _buscar_imagem_por_og(link)
            time.sleep(DELAY_BETWEEN_REQUESTS_SEC)

        saida.append(
            {
                "titulo": titulo,
                "link": link,
                "descricao": _limpar_html(desc),
                "data": data,
                "data_hora": data_hora,
                "horario": horario,
                "fonte": fonte,
                "imagem": imagem or "",
            }
        )

    return saida


# =============================================================================
# Geração do JSON final
# =============================================================================

def _tags_por_categoria(categoria: str, titulo: str) -> List[str]:
    cat = (categoria or "").lower().strip()
    title = (titulo or "").lower()

    tags: List[str] = []
    if cat == "cripto":
        if "bitcoin" in title:
            tags.append("Bitcoin")
        if "ethereum" in title:
            tags.append("Ethereum")
    elif cat == "bolsa":
        if "ibov" in title or "ibovespa" in title:
            tags.append("IBOV")
        if "ações" in title or "acao" in title:
            tags.append("Ações")
    elif cat == "economia":
        for k, tag in [("selic", "Selic"), ("infla", "Inflação"), ("pib", "PIB"), ("dólar", "Dólar"), ("dolar", "Dólar")]:
            if k in title:
                tags.append(tag)
    elif cat == "exterior":
        for k, tag in [("eua", "EUA"), ("fed", "FED"), ("china", "China"), ("europa", "Europa")]:
            if k in title:
                tags.append(tag)

    if cat and cat != "geral":
        tags.append(cat.capitalize())

    tags = list(dict.fromkeys([t for t in tags if t]))
    return tags[:3]


def gerar_noticias_mercado() -> Dict:
    por_portal: Dict[str, List[Dict]] = {}
    bruto: List[Tuple[str, Dict]] = []

    for categoria, query in CATEGORIAS_QUERY.items():
        itens = _rss_google_news(query=query, max_itens=MAX_ITENS_POR_CATEGORIA)
        for it in itens:
            bruto.append((categoria, it))

    vistos: Dict[int, Dict] = {}
    for categoria, it in bruto:
        titulo = it.get("titulo", "")
        link = it.get("link", "")
        data_hora = it.get("data_hora", "")
        nid = _sha1_id(titulo, link, data_hora)

        vistos[nid] = {
            "id": nid,
            "categoria": (categoria or "geral").lower(),
            "titulo": str(titulo).strip(),
            "link": str(link).strip(),
            "fonte": str(it.get("fonte", "")).strip() or "Desconhecida",
            "horario": str(it.get("horario", "")).strip(),
            "data": str(it.get("data", "")).strip(),
            "data_hora": str(data_hora).strip(),
            "descricao": str(it.get("descricao", "")).strip(),
            "tags": _tags_por_categoria(categoria, titulo),
            "imagem": str(it.get("imagem", "")).strip(),
        }

    finais = list(vistos.values())
    finais.sort(key=lambda x: (x.get("data_hora", ""), x.get("id", 0)), reverse=True)
    finais = finais[:MAX_TOTAL_FINAL]

    for n in finais:
        portal = n.get("fonte", "Desconhecida") or "Desconhecida"
        por_portal.setdefault(portal, []).append(n)

    for portal, arr in por_portal.items():
        arr.sort(key=lambda x: (x.get("data_hora", ""), x.get("id", 0)), reverse=True)

    return {
        "ultima_atualizacao": _now_sp().isoformat(),
        "meta": {
            "total_portais": len(por_portal),
            "total_noticias": sum(len(v) for v in por_portal.values()),
            "fonte": "Google News RSS",
        },
        "portais": por_portal,
    }


def salvar_json(payload: Dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)


def atualizar_timestamp_telemetria(path: Path, fonte: str) -> None:
    """Atualiza site/data/ultima_atualizacao.json sem destruir chaves extras (reduz conflito)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    dados: Dict = {}
    if path.exists():
        try:
            dados = json.loads(path.read_text(encoding="utf-8")) or {}
            if not isinstance(dados, dict):
                dados = {}
        except Exception:
            dados = {}

    now = _now_sp()
    dados.update(
        {
            "timestamp": int(time.time()) * 1000,
            "data": now.strftime("%Y-%m-%d"),
            "hora": now.strftime("%H:%M BRT"),
            "fonte": fonte,
            "versao": "1.0.0",
        }
    )

    path.write_text(json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    out_json = Path("balancos/NOTICIAS/noticias_mercado.json")
    payload = gerar_noticias_mercado()
    salvar_json(payload, out_json)

    # mantém compatibilidade com seu fluxo atual
    atualizar_timestamp_telemetria(Path("site/data/ultima_atualizacao.json"), fonte="noticias_mercado")

    total = payload.get("meta", {}).get("total_noticias", 0)
    print(f"✅ noticias_mercado.json gerado | total={total}")


if __name__ == "__main__":
    main()
