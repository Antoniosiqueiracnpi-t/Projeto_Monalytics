"""
CAPTURA DE NOTICIÁRIO ECONÔMICO (NOTÍCIAS DO MERCADO) - DESACOPLADO DO EMPRESARIAL

- Atualiza o bloco do site "Notícias do Mercado"
- Fonte: Google News RSS (busca por consultas amplas de mercado / macro / bolsa / câmbio / cripto)
- Saída: balancos/NOTICIAS/noticias_mercado.json

Requisitos de compatibilidade com o site (script.js):
- JSON deve conter:
  - ultima_atualizacao (iso)
  - total_noticias (int)
  - portais (dict): { "NomePortal": [itens...] }

Cada item (notícia) contém:
- id (int) estável (sha1 truncado)
- data (YYYY-MM-DD)
- data_hora (YYYY-MM-DD HH:MM:SS)
- horario (HH:MM)  -> usado para ordenação no front
- titulo (str)
- descricao (str)
- link (str)
- fonte (str)      -> nome do portal (para exibição)
- imagem (str)     -> URL ou placeholder data-uri (para não quebrar layout)
- categoria (str)  -> ex: "Bolsa", "Economia", "Exterior", "Cripto", "Geral"
- tags (list[str]) -> tags curtas

Opcional:
- Respeita janela de execução 08:00-22:00 (America/Sao_Paulo)
  - Para forçar execução: export FORCE_RUN=1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs, quote

import requests
from bs4 import BeautifulSoup


# =============================================================================
# Config
# =============================================================================

OUTPUT_PATH = Path("balancos/NOTICIAS/noticias_mercado.json")

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

HEADERS = {"User-Agent": USER_AGENT}

TIMEOUT = 20
MAX_ITENS_POR_QUERY = 25
MAX_TOTAL_ITENS = 160          # limite global antes de agrupar
MAX_ITENS_POR_PORTAL = 18      # limite por portal no JSON final
MAX_DIAS_LOOKBACK = 1          # preferir hoje; se pouco conteúdo, aceitar ontem

# Janela desejada (horário SP)
HORA_INICIO = 8
HORA_FIM = 22  # inclusive


# Consultas amplas (ajuste fino aqui se quiser)
QUERIES = [
    # Bolsa / B3
    'ibovespa OR "B3" OR "bolsa brasileira" OR ações',
    # Câmbio / juros
    'dólar OR câmbio OR "real" OR "Banco Central" OR "Copom" OR Selic OR juros',
    # Inflação / macro
    'IPCA OR inflação OR PIB OR "atividade econômica" OR "economia brasileira"',
    # Exterior / Fed / risco
    'Fed OR "Treasuries" OR "mercados globais" OR China OR EUA OR "Europa" OR commodities',
    # Cripto (mantém a categoria viva no bloco)
    'Bitcoin OR criptomoedas OR "cripto" OR Ethereum',
]


# =============================================================================
# TZ helpers
# =============================================================================

def _get_sp_tz():
    """
    Tenta usar IANA (zoneinfo). Se não estiver disponível, usa offset fixo -03:00.
    """
    try:
        from zoneinfo import ZoneInfo  # py3.9+
        return ZoneInfo("America/Sao_Paulo")
    except Exception:
        return timezone(timedelta(hours=-3))


TZ_SP = _get_sp_tz()


# =============================================================================
# Utils
# =============================================================================

def _norm(s: str) -> str:
    return str(s or "").strip()


def _sha1_id(titulo: str, link: str, data_hora: str) -> int:
    base = f"{_norm(titulo)}|{_norm(link)}|{_norm(data_hora)}"
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def _now_sp() -> datetime:
    return datetime.now(TZ_SP)


def _within_window(now_sp: datetime) -> bool:
    return HORA_INICIO <= now_sp.hour <= HORA_FIM


def _clean_text(s: str) -> str:
    s = _norm(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def limpar_descricao_html(descricao: str, limit: int = 260) -> str:
    try:
        soup = BeautifulSoup(descricao or "", "html.parser")
        texto = " ".join(soup.get_text().split()).strip()
        if limit and len(texto) > limit:
            texto = texto[: max(0, limit - 3)] + "..."
        return texto
    except Exception:
        return _clean_text(descricao)


def _placeholder_image_data_uri() -> str:
    """
    Placeholder leve (SVG) para não quebrar o layout quando não houver imagem.
    """
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='800' height='450'>"
        "<rect width='100%' height='100%' fill='#0b1220'/>"
        "<text x='50%' y='50%' fill='#ffffff' font-size='42' font-family='Arial' "
        "text-anchor='middle' dominant-baseline='middle'>Notícias</text>"
        "</svg>"
    )
    return "data:image/svg+xml;charset=utf-8," + quote(svg, safe="")


PLACEHOLDER_IMG = _placeholder_image_data_uri()


def _resolver_url_real_google_news(link: Optional[str]) -> Optional[str]:
    """
    Se vier no formato news.google.com com ?url=, tenta extrair a URL real.
    """
    if not link:
        return link
    try:
        if "news.google.com" not in link:
            return link
        parsed = urlparse(link)
        params = parse_qs(parsed.query)
        if "url" in params and params["url"]:
            return params["url"][0]
        return link
    except Exception:
        return link


def extrair_data_publicacao(item) -> Tuple[str, str, str]:
    """
    Retorna:
    - data (YYYY-MM-DD)
    - data_hora (YYYY-MM-DD HH:MM:SS)
    - horario (HH:MM) em TZ_SP
    """
    try:
        pub = item.find("pubDate")
        if pub and pub.text:
            dt = parsedate_to_datetime(pub.text.strip())
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt_sp = dt.astimezone(TZ_SP)
            return (
                dt_sp.strftime("%Y-%m-%d"),
                dt_sp.strftime("%Y-%m-%d %H:%M:%S"),
                dt_sp.strftime("%H:%M"),
            )
    except Exception:
        pass

    agora = _now_sp()
    return (
        agora.strftime("%Y-%m-%d"),
        agora.strftime("%Y-%m-%d %H:%M:%S"),
        agora.strftime("%H:%M"),
    )


def extrair_fonte_noticia(link: Optional[str], item=None) -> str:
    """
    - Prioriza <source> do RSS
    - Fallback: domínio
    """
    try:
        if item is not None:
            src = item.find("source")
            if src and src.text:
                return _clean_text(src.text)

        if not link:
            return "Google News"

        url_final = _resolver_url_real_google_news(link) or link
        dom = (urlparse(url_final).netloc or "").replace("www.", "").strip().lower()

        fontes_conhecidas = {
            "infomoney.com.br": "InfoMoney",
            "valorinveste.globo.com": "Valor Investe",
            "valor.globo.com": "Valor Econômico",
            "economia.uol.com.br": "UOL Economia",
            "moneytimes.com.br": "Money Times",
            "exame.com": "Exame",
            "estadao.com.br": "Estadão",
            "folha.uol.com.br": "Folha de S.Paulo",
            "g1.globo.com": "G1",
            "cnnbrasil.com.br": "CNN Brasil",
            "seudinheiro.com": "Seu Dinheiro",
            "investnews.com.br": "InvestNews",
            "bloomberg.com": "Bloomberg",
            "reuters.com": "Reuters",
            "wsj.com": "WSJ",
            "ft.com": "Financial Times",
        }

        for d, nome in fontes_conhecidas.items():
            if dom.endswith(d):
                return nome

        if dom:
            return dom.split(".")[0].capitalize()

        return "Google News"
    except Exception:
        return "Google News"


def extrair_imagem(item, descricao_html: str) -> str:
    """
    Tenta achar imagem:
    - media:content url=
    - enclosure url=
    - <img src="..."> na descrição
    - fallback placeholder
    """
    # 1) media:content
    try:
        mc = item.find("media:content")
        if mc and mc.get("url"):
            return str(mc.get("url")).strip()
    except Exception:
        pass

    # 2) enclosure
    try:
        enc = item.find("enclosure")
        if enc and enc.get("url"):
            return str(enc.get("url")).strip()
    except Exception:
        pass

    # 3) img na descrição
    try:
        soup = BeautifulSoup(descricao_html or "", "html.parser")
        img = soup.find("img")
        if img and img.get("src"):
            return str(img.get("src")).strip()
    except Exception:
        pass

    return PLACEHOLDER_IMG


def classificar_categoria_e_tags(titulo: str, descricao: str) -> Tuple[str, List[str]]:
    """
    Mantém categorias simples (para não depender do HTML do front):
      Bolsa / Economia / Exterior / Cripto / Geral
    """
    txt = f"{titulo} {descricao}".lower()

    tags: List[str] = []

    def has(*words):
        return any(w in txt for w in words)

    # Cripto
    if has("bitcoin", "cripto", "criptomo", "ethereum", "btc", "eth"):
        cat = "Cripto"
        if "bitcoin" in txt or "btc" in txt:
            tags.append("Bitcoin")
        if "ethereum" in txt or "eth" in txt:
            tags.append("Ethereum")
        return cat, tags[:3]

    # Bolsa
    if has("ibovespa", "b3", "bolsa", "ações", "acoes", "small caps", "blue chips", "índice"):
        cat = "Bolsa"
        if "ibovespa" in txt:
            tags.append("Ibovespa")
        if "b3" in txt:
            tags.append("B3")
        if "ações" in txt or "acoes" in txt:
            tags.append("Ações")
        return cat, tags[:3]

    # Exterior
    if has("eua", "fed", "powell", "treasur", "dow", "nasdaq", "s&p", "china", "europa", "bce", "boe", "japão", "japao"):
        cat = "Exterior"
        if "fed" in txt:
            tags.append("Fed")
        if "eua" in txt:
            tags.append("EUA")
        if "china" in txt:
            tags.append("China")
        return cat, tags[:3]

    # Economia (macro, juros, câmbio, inflação, commodities)
    if has("dólar", "dolar", "câmbio", "cambio", "selic", "copom", "juros", "ipca", "infla", "pib",
           "banco central", "commod", "petróleo", "petroleo", "minério", "minerio"):
        cat = "Economia"
        if "dólar" in txt or "dolar" in txt:
            tags.append("Dólar")
        if "selic" in txt or "copom" in txt:
            tags.append("Selic")
        if "ipca" in txt or "infla" in txt:
            tags.append("Inflação")
        return cat, tags[:3]

    return "Geral", []


# =============================================================================
# Scraping Google News RSS (econômico)
# =============================================================================

@dataclass
class Noticia:
    id: int
    data: str
    data_hora: str
    horario: str
    titulo: str
    descricao: str
    link: str
    fonte: str
    imagem: str
    categoria: str
    tags: List[str]


def fetch_rss_google_news(query: str) -> bytes:
    params = {
        "q": query,
        "hl": "pt-BR",
        "gl": "BR",
        "ceid": "BR:pt-419",
    }
    r = requests.get(GOOGLE_NEWS_RSS, params=params, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}")
    return r.content


def coletar_noticias() -> List[Noticia]:
    coletadas: Dict[int, Noticia] = {}

    for q in QUERIES:
        try:
            xml = fetch_rss_google_news(q)
        except Exception as e:
            print(f"⚠️ Falha ao buscar RSS para query: {q} | {e}")
            continue

        soup = BeautifulSoup(xml, "xml")
        itens = soup.find_all("item")

        for item in itens[:MAX_ITENS_POR_QUERY]:
            try:
                titulo = item.find("title").text.strip() if item.find("title") else "Título não disponível"
                link_raw = item.find("link").text.strip() if item.find("link") else ""
                descricao_html = item.find("description").text if item.find("description") else ""

                link = _resolver_url_real_google_news(link_raw) or link_raw
                descricao = limpar_descricao_html(descricao_html)

                data, data_hora, horario = extrair_data_publicacao(item)
                fonte = extrair_fonte_noticia(link, item=item)
                imagem = extrair_imagem(item, descricao_html)

                categoria, tags = classificar_categoria_e_tags(titulo, descricao)

                nid = _sha1_id(titulo, link, data_hora)

                coletadas[nid] = Noticia(
                    id=nid,
                    data=data,
                    data_hora=data_hora,
                    horario=horario,
                    titulo=_clean_text(titulo),
                    descricao=_clean_text(descricao),
                    link=link,
                    fonte=_clean_text(fonte) or "Google News",
                    imagem=imagem or PLACEHOLDER_IMG,
                    categoria=categoria,
                    tags=tags,
                )
            except Exception:
                continue

            if len(coletadas) >= MAX_TOTAL_ITENS:
                break

        if len(coletadas) >= MAX_TOTAL_ITENS:
            break

    return list(coletadas.values())


def filtrar_por_recencia(noticias: List[Noticia]) -> List[Noticia]:
    """
    Preferência: notícias de hoje (TZ_SP). Se ficar muito vazio, aceita ontem também.
    """
    if not noticias:
        return []

    hoje = _now_sp().strftime("%Y-%m-%d")
    ontem = (_now_sp() - timedelta(days=1)).strftime("%Y-%m-%d")

    hoje_list = [n for n in noticias if n.data == hoje]
    if len(hoje_list) >= 12:
        return hoje_list

    # fallback: hoje + ontem
    return [n for n in noticias if n.data in (hoje, ontem)]


def agrupar_por_portal(noticias: List[Noticia]) -> Dict[str, List[dict]]:
    portais: Dict[str, List[Noticia]] = {}
    for n in noticias:
        portal = n.fonte or "Google News"
        portais.setdefault(portal, []).append(n)

    # ordenar por data_hora desc e aplicar limite por portal
    out: Dict[str, List[dict]] = {}
    for portal, arr in portais.items():
        arr.sort(key=lambda x: x.data_hora, reverse=True)
        arr = arr[:MAX_ITENS_POR_PORTAL]
        out[portal] = [n.__dict__ for n in arr]

    return out


def salvar_json(portais: Dict[str, List[dict]]):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    total = sum(len(v) for v in portais.values())

    payload = {
        "ultima_atualizacao": _now_sp().isoformat(),
        "total_noticias": total,
        "fonte": "Google News RSS",
        "portais": portais,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Captura noticiário econômico (Notícias do Mercado) via Google News RSS")
    parser.add_argument("--force", action="store_true", help="Força execução mesmo fora da janela 08-22 (SP)")
    args = parser.parse_args()

    force_env = os.getenv("FORCE_RUN", "").strip() == "1"
    now_sp = _now_sp()

    if not (args.force or force_env) and not _within_window(now_sp):
        print(f"⏸️ Fora da janela de execução (SP). Agora: {now_sp.strftime('%Y-%m-%d %H:%M:%S')} | "
              f"Janela: {HORA_INICIO:02d}:00-{HORA_FIM:02d}:59. Saindo sem erro.")
        return

    print(f"🕒 Agora (SP): {now_sp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📰 Coletando notícias do mercado... (queries={len(QUERIES)})")

    noticias = coletar_noticias()
    noticias = filtrar_por_recencia(noticias)

    if not noticias:
        print("⚠️ Nenhuma notícia coletada (após filtros).")
        # ainda assim salva um JSON válido (mantém o front estável)
        salvar_json({})
        print(f"✅ JSON salvo (vazio): {OUTPUT_PATH}")
        return

    portais = agrupar_por_portal(noticias)
    salvar_json(portais)

    total = sum(len(v) for v in portais.values())
    print(f"✅ Salvo: {OUTPUT_PATH} | portais={len(portais)} | noticias={total}")


if __name__ == "__main__":
    main()
