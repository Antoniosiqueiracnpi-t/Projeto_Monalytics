# -*- coding: utf-8 -*-
"""
CAPTURA DE NOTICIÁRIO ECONÔMICO (DESACOPLADO DO NOTICIÁRIO EMPRESARIAL)

- Lê RSS DIRETO dos portais (estilo "bot"): tende a vir com imagem.
- Extrai imagem via:
  1) media:content / media:thumbnail
  2) enclosure/links do tipo image
  3) <img src> dentro do summary/description
  4) fallback: og:image / twitter:image (requisição na URL da notícia)

- Gera JSON para o site:
  balancos/NOTICIAS/noticias_mercado.json

Formato esperado pelo seu front (script.js):
- data.portais[Portal] = lista de notícias
- cada notícia: {titulo, descricao, link, fonte, categoria, tags, horario, data_hora, imagem, id}
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import feedparser
import requests
from bs4 import BeautifulSoup


# =============================================================================
# CONFIG
# =============================================================================

BRT = timezone(timedelta(hours=-3))

OUT_JSON = Path("balancos/NOTICIAS/noticias_mercado.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

REQUEST_TIMEOUT = 15
MAX_ITENS_POR_FEED = 30
MAX_NOTICIAS_POR_PORTAL = 60
MAX_TOTAL_NOTICIAS = 240

# Evita fazer muitas requisições "og:image" por run (só quando necessário)
MAX_OG_FETCH = 25


@dataclass
class FeedSource:
    portal: str
    url: str


# RSS dos portais (você pode ajustar/expandir)
# Observação: URLs comuns e amplamente usadas:
# - InfoMoney: /feed/
# - MoneyTimes: /feed/
# - Investing BR: rss/news.rss
# - Valor Investe: /rss/ (pode variar; deixe se estiver funcionando no seu runner)
SOURCES: List[FeedSource] = [
    FeedSource("InfoMoney", "https://www.infomoney.com.br/feed/"),
    FeedSource("Money Times", "https://www.moneytimes.com.br/feed/"),
    FeedSource("Investing", "https://br.investing.com/rss/news.rss"),
    FeedSource("Valor Investe", "https://valorinveste.globo.com/rss/"),
]


# =============================================================================
# HELPERS
# =============================================================================

def _now_iso() -> str:
    return datetime.now(BRT).isoformat()

def _sha1_id(*parts: str) -> int:
    base = "|".join([p.strip() for p in parts if p is not None])
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)

def _clean_text(s: str, limit: int = 220) -> str:
    s = BeautifulSoup(s or "", "html.parser").get_text(" ", strip=True)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > limit:
        return s[: limit - 3] + "..."
    return s

def _parse_datetime(entry) -> datetime:
    # feedparser fornece published_parsed/updated_parsed (time.struct_time)
    for key in ("published_parsed", "updated_parsed"):
        st = getattr(entry, key, None)
        if st:
            try:
                # converte como UTC e depois ajusta BRT
                dt_utc = datetime(*st[:6], tzinfo=timezone.utc)
                return dt_utc.astimezone(BRT)
            except Exception:
                pass
    return datetime.now(BRT)

def _fmt_horario(dt: datetime) -> str:
    return dt.strftime("%H:%M")

def _fmt_data_hora(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def _extract_tags(entry) -> List[str]:
    tags = []
    for t in getattr(entry, "tags", []) or []:
        term = (t.get("term") if isinstance(t, dict) else None) or ""
        term = term.strip()
        if term:
            tags.append(term)
    # remove duplicados preservando ordem
    tags = list(dict.fromkeys(tags))
    # limita para não poluir UI
    return tags[:4]

def _guess_categoria(titulo: str, link: str, tags: List[str]) -> str:
    # Mantém alinhado com os botões do seu site: Internacional | Empresas | Economia | Mercados
    text = f"{titulo} {link} {' '.join(tags)}".lower()

    # Internacional
    if any(k in text for k in [
        "eua", "estados unidos", "china", "europa", "rússia", "ucrânia", "israel", "gaza",
        "fed", "federal reserve", "boj", "ecb", "opec", "international", "internacional",
    ]):
        return "Internacional"

    # Empresas (resultados, balanços, M&A, dividendos etc.)
    if any(k in text for k in [
        "lucro", "preju", "ebitda", "resultado", "balanço", "guidance",
        "dividendo", "jcp", "bonificação", "follow-on", "ipo",
        "fusão", "aquisição", "m&a", "captação", "oferta",
    ]) or re.search(r"\b[A-Z]{4}\d{1,2}\b", titulo.upper()):  # padrão ticker B3
        return "Empresas"

    # Mercados (bolsa, dólar, cripto, commodities)
    if any(k in text for k in [
        "ibovespa", "b3", "bolsa", "ações", "dólar", "câmbio", "juros futuros",
        "commodities", "petróleo", "minério", "bitcoin", "ethereum", "cripto",
        "nasdaq", "s&p", "dow jones",
    ]):
        return "Mercados"

    # Economia (macro, inflação, selic, fiscal)
    if any(k in text for k in [
        "inflação", "ipca", "igp", "pib", "selic", "copom", "bc", "banco central",
        "fiscal", "dívida", "arrecadação", "emprego", "payroll", "atividade",
    ]):
        return "Economia"

    return "Economia"


# =============================================================================
# IMAGE EXTRACTION (estilo bot)
# =============================================================================

def _extract_image_from_entry(entry) -> Optional[str]:
    # 1) media_content
    mc = getattr(entry, "media_content", None)
    if mc and isinstance(mc, list):
        for item in mc:
            url = (item.get("url") if isinstance(item, dict) else None) or ""
            if url.startswith("http"):
                return url

    # 2) media_thumbnail
    mt = getattr(entry, "media_thumbnail", None)
    if mt and isinstance(mt, list):
        for item in mt:
            url = (item.get("url") if isinstance(item, dict) else None) or ""
            if url.startswith("http"):
                return url

    # 3) enclosures / links rel=enclosure
    for lk in getattr(entry, "links", []) or []:
        if not isinstance(lk, dict):
            continue
        href = lk.get("href", "") or ""
        ltype = (lk.get("type", "") or "").lower()
        rel = (lk.get("rel", "") or "").lower()
        if href.startswith("http") and (rel == "enclosure") and ("image" in ltype):
            return href

    # 4) <img src> no summary/description
    html = (getattr(entry, "summary", "") or getattr(entry, "description", "") or "")
    m = re.search(r'<img[^>]+src="([^"]+)"', html, flags=re.I)
    if m:
        url = m.group(1).strip()
        if url.startswith("http"):
            return url

    return None


def _fetch_og_image(url: str) -> Optional[str]:
    if not url or not url.startswith("http"):
        return None
    try:
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if r.status_code != 200 or not r.text:
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        # og:image
        og = soup.find("meta", attrs={"property": "og:image"})
        if og and og.get("content"):
            img = og.get("content").strip()
            if img.startswith("http"):
                return img

        # twitter:image
        tw = soup.find("meta", attrs={"name": "twitter:image"})
        if tw and tw.get("content"):
            img = tw.get("content").strip()
            if img.startswith("http"):
                return img

        return None
    except Exception:
        return None


# =============================================================================
# CORE
# =============================================================================

def coletar_portal(feed: FeedSource, og_budget: List[int]) -> List[Dict]:
    parsed = feedparser.parse(feed.url)
    if getattr(parsed, "bozo", False):
        # bozo_exception existe em parsed.bozo_exception, mas não derrubamos o job
        pass

    out: List[Dict] = []

    for entry in (parsed.entries or [])[:MAX_ITENS_POR_FEED]:
        try:
            titulo = (getattr(entry, "title", "") or "").strip() or "Título não disponível"
            link = (getattr(entry, "link", "") or "").strip()
            desc = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
            desc = _clean_text(desc, limit=240)

            dt = _parse_datetime(entry)
            horario = _fmt_horario(dt)
            data_hora = _fmt_data_hora(dt)

            tags = _extract_tags(entry)
            categoria = _guess_categoria(titulo, link, tags)

            imagem = _extract_image_from_entry(entry)

            # fallback og:image (limitado)
            if (not imagem) and link and og_budget[0] < MAX_OG_FETCH:
                og_budget[0] += 1
                ogimg = _fetch_og_image(link)
                if ogimg:
                    imagem = ogimg

            nid = _sha1_id(feed.portal, titulo, link, data_hora)

            out.append({
                "id": nid,
                "titulo": titulo,
                "descricao": desc,
                "link": link,
                "url": link,  # compat
                "fonte": feed.portal,
                "categoria": categoria,
                "tags": tags,
                "horario": horario,
                "data_hora": data_hora,
                "imagem": imagem,  # <--- chave que seu front usa
            })
        except Exception:
            continue

    # Dedup local e ordena
    uniq: Dict[int, Dict] = {}
    for n in out:
        uniq[int(n["id"])] = n
    out = list(uniq.values())
    out.sort(key=lambda x: x.get("data_hora", ""), reverse=True)
    return out[:MAX_NOTICIAS_POR_PORTAL]


def salvar_json(portais: Dict[str, List[Dict]]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    # achata para corte global
    flat = []
    for lst in portais.values():
        flat.extend(lst)
    flat.sort(key=lambda x: x.get("data_hora", ""), reverse=True)
    flat = flat[:MAX_TOTAL_NOTICIAS]

    # re-separa respeitando o corte global
    allowed_ids = set(int(x["id"]) for x in flat)
    portais_cortado: Dict[str, List[Dict]] = {}
    for p, lst in portais.items():
        portais_cortado[p] = [x for x in lst if int(x["id"]) in allowed_ids]

    payload = {
        "ultima_atualizacao": _now_iso(),
        "total_noticias": len(flat),
        "portais": portais_cortado,
    }

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main():
    og_budget = [0]  # mutável

    portais: Dict[str, List[Dict]] = {}
    for feed in SOURCES:
        print(f"📰 Coletando: {feed.portal} | {feed.url}")
        noticias = coletar_portal(feed, og_budget)
        print(f"   ✅ {len(noticias)} itens (og_fetch={og_budget[0]}/{MAX_OG_FETCH})")
        portais[feed.portal] = noticias

    salvar_json(portais)
    print(f"\n✅ JSON salvo em: {OUT_JSON}")


if __name__ == "__main__":
    main()
