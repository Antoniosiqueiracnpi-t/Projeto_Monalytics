"""
CAPTURA DE NOTICIÁRIO EMPRESARIAL (DESACOPLADO DO NOTICIÁRIO ECONÔMICO)

- Busca notícias via Google News RSS usando modelo simples:
  https://news.google.com/rss/search?q=<TICKER>&hl=pt-BR&gl=BR&ceid=BR:pt-419

- Salva em JSON em TODAS as classes da empresa:
  balancos/<TICKER_CLASSE>/noticiario.json

- Se o mapeamento NÃO existir no runner, o script continua funcionando em modo:
  - ticker
  - lista
  - ticker posicional
  - ou via env var TICKERS="KLBN11,VALE3,..."
  E descobre as classes pela estrutura de pastas em balancos/.

Regra de criação de pasta:
- Se precisar criar, cria SEMPRE com uma classe válida (ticker com número, ex: KLBN11),
  nunca com ticker_base puro (ex: KLBN).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Optional, List, Dict
from urllib.parse import urlparse, parse_qs

import requests
import pandas as pd
from bs4 import BeautifulSoup


# =============================================================================
# Utils
# =============================================================================

def _norm(s: str) -> str:
    return str(s or "").strip().upper()


def extrair_ticker_base(ticker: str) -> str:
    """Remove números finais do ticker (PETR4 -> PETR)."""
    return re.sub(r"\d+$", "", _norm(ticker))


def _split_tickers(s: str) -> List[str]:
    if not s:
        return []
    parts = re.split(r"[,\s;]+", s.strip())
    return [_norm(p) for p in parts if p and p.strip()]


def _sha1_id(titulo: str, link: Optional[str], data_hora: str) -> int:
    base = f"{(titulo or '').strip()}|{(link or '').strip()}|{(data_hora or '').strip()}"
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def _ler_json_resiliente(path: Path) -> Dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


# =============================================================================
# Mapeamento (opcional)
# =============================================================================

def load_mapeamento_consolidado() -> Optional[pd.DataFrame]:
    """
    Tenta carregar mapeamento.
    Se não existir, retorna None (o script continua funcionando em modo ticker/lista).
    """
    csv_consolidado = Path("mapeamento_b3_consolidado.csv")
    csv_original = Path("mapeamento_final_b3_completo_utf8.csv")

    for p in [csv_consolidado, csv_original]:
        if p.exists():
            try:
                df = pd.read_csv(p, sep=";", encoding="utf-8-sig", dtype=str)
                if "ticker" in df.columns:
                    df = df[df["ticker"].notna()].copy()
                    df["ticker"] = df["ticker"].astype(str).apply(_norm)
                    df["ticker_base"] = df["ticker"].apply(extrair_ticker_base)
                    return df
            except Exception:
                continue

    return None


def listar_classes_por_mapeamento(ticker_base: str, df_map: pd.DataFrame) -> List[str]:
    tb = _norm(ticker_base)
    m = df_map[df_map["ticker_base"] == tb]
    if m.empty:
        return []
    ticks = [_norm(x) for x in m["ticker"].dropna().astype(str).tolist() if str(x).strip()]
    # remove duplicados preservando ordem
    ticks = list(dict.fromkeys(ticks))
    # classes (com número) primeiro
    ticks.sort(key=lambda t: (len(t) == len(tb), len(t)))
    return ticks


def buscar_nome_empresa_por_mapeamento(ticker_base: str, df_map: pd.DataFrame) -> str:
    tb = _norm(ticker_base)
    m = df_map[df_map["ticker_base"] == tb]
    if m.empty:
        return tb
    row = m.iloc[0]
    for col in ["empresa", "nome", "razao_social", "denominacao_social"]:
        if col in m.columns and pd.notna(row.get(col)) and str(row.get(col)).strip():
            return str(row.get(col)).strip()
    return tb


# =============================================================================
# Descobrir classes por filesystem (fallback quando não há mapeamento)
# =============================================================================

def listar_classes_por_filesystem(ticker_base: str, pasta_saida: Path) -> List[str]:
    """
    Procura pastas em balancos/ que pertençam ao ticker_base.
    Ex: ticker_base=KLBN -> encontra KLBN11, KLBN3, KLBN4.
    """
    tb = _norm(ticker_base)
    classes: List[str] = []

    if not pasta_saida.exists():
        return []

    for p in pasta_saida.iterdir():
        if p.is_dir():
            name = _norm(p.name)
            if extrair_ticker_base(name) == tb and len(name) > len(tb):
                classes.append(name)

    # remove duplicados e ordena com classes mais longas primeiro (KLBN11 antes de KLBN3)
    classes = list(dict.fromkeys(classes))
    classes.sort(key=lambda t: len(t), reverse=True)
    return classes


def garantir_pastas_classes(pasta_saida: Path, classes: List[str], ticker_fallback_classe: str) -> List[Path]:
    """
    Garante que as pastas existam.
    Regra: se precisar criar, cria sempre com classe (ticker com número),
    e se não tiver classes, usa o ticker_fallback_classe (ex: KLBN11).
    """
    pasta_saida.mkdir(parents=True, exist_ok=True)

    if not classes:
        t = _norm(ticker_fallback_classe)
        p = pasta_saida / t
        p.mkdir(parents=True, exist_ok=True)
        return [p]

    paths: List[Path] = []
    for t in classes:
        t = _norm(t)
        p = pasta_saida / t
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
        paths.append(p)

    return paths


# =============================================================================
# Google News RSS scraping (modelo simples q=ticker)
# =============================================================================

def limpar_descricao_html(descricao: str) -> str:
    try:
        soup = BeautifulSoup(descricao or "", "html.parser")
        texto = " ".join(soup.get_text().split()).strip()
        if len(texto) > 300:
            texto = texto[:297] + "..."
        return texto
    except Exception:
        return str(descricao or "").strip()


def extrair_data_publicacao(item) -> tuple[str, str]:
    try:
        pub = item.find("pubDate")
        if pub and pub.text:
            dt = parsedate_to_datetime(pub.text.strip())
            return dt.strftime("%Y-%m-%d"), dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass

    agora = datetime.now()
    return agora.strftime("%Y-%m-%d"), agora.strftime("%Y-%m-%d %H:%M:%S")


def _resolver_url_real_google_news(link: Optional[str]) -> Optional[str]:
    """
    Se o link vier do Google News com parâmetro url=, extrai a URL real.
    Caso contrário, retorna o link original.
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


def extrair_fonte_noticia(link: Optional[str], item=None) -> str:
    """
    Fonte:
    - Prioriza <source> do RSS
    - Fallback por domínio
    """
    try:
        if item is not None:
            src = item.find("source")
            if src and src.text:
                return src.text.strip()

        if not link:
            return "Desconhecida"

        url_final = _resolver_url_real_google_news(link) or link
        dominio = (urlparse(url_final).netloc or "").replace("www.", "").strip()

        if not dominio:
            return "Desconhecida"

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
        }

        for dom, nome in fontes_conhecidas.items():
            if dominio.endswith(dom):
                return nome

        if "news.google.com" in dominio:
            return "Google News"

        return dominio.split(".")[0].capitalize()
    except Exception:
        return "Desconhecida"


def buscar_noticias_scraping_google(ticker: str, max_itens: int = 30) -> List[Dict]:
    """
    MODELO SIMPLES, IGUAL AO SEU EXEMPLO:
    q=<ticker>&hl=pt-BR&gl=BR&ceid=BR:pt-419
    """
    t = _norm(ticker)
    if not t:
        return []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    params = {
        "q": t,
        "hl": "pt-BR",
        "gl": "BR",
        "ceid": "BR:pt-419",
    }

    resp = requests.get(
        "https://news.google.com/rss/search",
        params=params,
        headers=headers,
        timeout=15
    )

    if resp.status_code != 200:
        print(f"⚠️ Erro ao buscar notícias: {resp.status_code}")
        return []

    soup = BeautifulSoup(resp.content, "xml")
    itens = soup.find_all("item")

    resultados: List[Dict] = []
    for item in itens[:max_itens]:
        try:
            titulo = item.find("title").text.strip() if item.find("title") else "Título não disponível"
            link = item.find("link").text.strip() if item.find("link") else None
            descricao = item.find("description").text if item.find("description") else "Descrição não disponível"

            data, data_hora = extrair_data_publicacao(item)
            url_final = _resolver_url_real_google_news(link) or link
            fonte = extrair_fonte_noticia(url_final or link, item=item)

            resultados.append({
                "titulo": titulo,
                "descricao": limpar_descricao_html(descricao),
                "link": url_final or link,
                "data": data,
                "data_hora": data_hora,
                "fonte": fonte,
            })
        except Exception as e:
            print(f"⚠️ Erro ao processar item RSS: {e}")
            continue

    return resultados


# =============================================================================
# Salvar JSON por classe
# =============================================================================

def salvar_noticiario_em_classes(
    ticker_base: str,
    nome_empresa: str,
    classes: List[str],
    ticker_consulta: str,
    noticias_rss: List[Dict],
    pasta_saida: Path,
) -> List[Path]:
    """
    Salva em TODAS as classes:
      balancos/<CLASSE>/noticiario.json

    Deduplica por id com base no json existente de cada classe.
    """
    tb = _norm(ticker_base)
    ne = str(nome_empresa or tb).strip()

    pastas = garantir_pastas_classes(pasta_saida, classes, ticker_fallback_classe=ticker_consulta)
    salvos: List[Path] = []

    # padroniza no formato final do Monalytics
    novas: List[Dict] = []
    for n in noticias_rss:
        titulo = str(n.get("titulo", "")).strip()
        url = n.get("link")
        data_hora = str(n.get("data_hora", "")).strip()
        nid = _sha1_id(titulo, url, data_hora)

        novas.append({
            "id": nid,
            "data": str(n.get("data", "")).strip(),
            "data_hora": data_hora,
            "titulo": titulo,
            "descricao": str(n.get("descricao", "")).strip(),
            "fonte": str(n.get("fonte", "")).strip() or "Desconhecida",
            "url": url,
            "tipo": "noticia_empresarial",
        })

    for pasta in pastas:
        ticker_classe = _norm(pasta.name)
        arq = pasta / "noticiario.json"

        dados_exist = _ler_json_resiliente(arq)
        existentes = dados_exist.get("noticias", []) if isinstance(dados_exist, dict) else []
        if not isinstance(existentes, list):
            existentes = []

        d: Dict[int, Dict] = {}
        for x in existentes:
            if isinstance(x, dict) and x.get("id") is not None:
                try:
                    d[int(x["id"])] = x
                except Exception:
                    continue

        for x in novas:
            d[int(x["id"])] = x

        finais = list(d.values())
        finais.sort(key=lambda x: x.get("data_hora", ""), reverse=True)
        finais = finais[:100]

        payload = {
            "empresa": {
                "ticker": ticker_classe,
                "ticker_base": tb,
                "nome": ne,
            },
            "ultima_atualizacao": datetime.now().isoformat(),
            "total_noticias": len(finais),
            "fonte": "Google News RSS",
            "ticker_consulta": _norm(ticker_consulta),
            "noticias": finais,
        }

        with open(arq, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        salvos.append(arq)

    return salvos


# =============================================================================
# Seleção de tickers (sem depender de mapeamento)
# =============================================================================

def obter_tickers_alvo(args) -> List[str]:
    """
    Ordem de prioridade:
    1) modo ticker / ticker posicional
    2) modo lista (--lista)
    3) env TICKERS (ex: "KLBN11,VALE3")
    """
    if args.modo == "ticker":
        t = _norm(args.ticker or args.positional_ticker)
        return [t] if t else []

    if args.modo == "lista":
        ticks = _split_tickers(args.lista)
        if ticks:
            return ticks

    env_ticks = _split_tickers(os.getenv("TICKERS", ""))
    if env_ticks:
        return env_ticks

    return []


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Captura noticiário empresarial via Google News RSS (q=ticker)")
    parser.add_argument("--modo", choices=["quantidade", "ticker", "lista", "faixa"], default="ticker")
    parser.add_argument("--quantidade", type=int, default=10)
    parser.add_argument("--ticker", default="")
    parser.add_argument("--lista", default="")
    parser.add_argument("--faixa", default="1-50")
    parser.add_argument("positional_ticker", nargs="?", default="")

    args = parser.parse_args()

    # Se veio ticker posicional, força modo ticker
    if args.positional_ticker and not args.ticker:
        args.modo = "ticker"
        args.ticker = args.positional_ticker

    pasta_saida = Path("balancos")
    pasta_saida.mkdir(exist_ok=True)

    # tenta carregar mapeamento (opcional)
    df_map = load_mapeamento_consolidado()

    # Seleção dos tickers-alvo SEM depender do mapeamento
    tickers_alvo = obter_tickers_alvo(args)

    # Se o usuário pediu quantidade/faixa mas não há mapeamento, não tem como escolher “as primeiras”
    if args.modo in ("quantidade", "faixa") and df_map is None:
        print("❌ mapeamento não encontrado no runner. Use --modo ticker/--modo lista ou a env TICKERS.")
        sys.exit(1)

    # Se modo quantidade/faixa com mapeamento, converte em tickers “classe” para consulta
    if args.modo in ("quantidade", "faixa") and df_map is not None:
        df_base = df_map.drop_duplicates(subset=["ticker_base"], keep="first").reset_index(drop=True)

        if args.modo == "quantidade":
            df_sel = df_base.head(int(args.quantidade or 10))
        else:
            inicio, fim = map(int, str(args.faixa or "1-50").split("-"))
            df_sel = df_base.iloc[inicio - 1: fim].reset_index(drop=True)

        # usa o primeiro ticker (classe) de cada base como “consulta”
        tickers_alvo = []
        for _, row in df_sel.iterrows():
            tb = _norm(row.get("ticker_base", ""))
            classes = listar_classes_por_mapeamento(tb, df_map)
            if classes:
                tickers_alvo.append(classes[0])
            else:
                # fallback: tenta ticker da própria linha
                tickers_alvo.append(_norm(row.get("ticker", tb)))

    # Se ainda estiver vazio, aborta com mensagem clara
    tickers_alvo = [t for t in tickers_alvo if t]
    if not tickers_alvo:
        print("❌ Nenhuma empresa selecionada com os critérios fornecidos.")
        sys.exit(1)

    print(f"✅ {len(tickers_alvo)} ticker(s) selecionado(s)\n")

    ok = 0
    erro = 0

    for idx, t in enumerate(tickers_alvo, 1):
        t = _norm(t)
        if not t:
            erro += 1
            continue

        tb = extrair_ticker_base(t)

        # classes da empresa:
        # 1) se mapeamento existe, usa ele
        # 2) senão, tenta filesystem balancos/
        if df_map is not None:
            classes = listar_classes_por_mapeamento(tb, df_map)
            nome = buscar_nome_empresa_por_mapeamento(tb, df_map)
        else:
            classes = listar_classes_por_filesystem(tb, pasta_saida)
            nome = tb  # sem mapeamento, não temos nome confiável

        # regra: se não achou classes no fs/map, usa o ticker informado como classe (ex: KLBN11)
        if not classes:
            classes = [t]

        print(f"[{idx}/{len(tickers_alvo)}] Processando {t} (base {tb}) | classes: {', '.join(classes)}")

        noticias = buscar_noticias_scraping_google(t, max_itens=30)

        if not noticias:
            print("  ⚠️ Nenhuma notícia encontrada\n")
            erro += 1
            continue

        salvos = salvar_noticiario_em_classes(
            ticker_base=tb,
            nome_empresa=nome,
            classes=classes,
            ticker_consulta=t,
            noticias_rss=noticias,
            pasta_saida=pasta_saida,
        )

        print(f"  ✅ Salvo em {len(salvos)} pasta(s)\n")
        ok += 1

    print(f"✅ Sucesso: {ok} | ❌ Erro: {erro}")


if __name__ == "__main__":
    main()
