"""
CAPTURA DE NOTICIÁRIO EMPRESARIAL - (DESACOPLADO DO NOTICIÁRIO ECONÔMICO)

Objetivo:
- Capturar notícias "exclusivas da empresa" via Google News RSS usando busca simples por ticker:
  https://news.google.com/rss/search?q=<TICKER>&hl=pt-BR&gl=BR&ceid=BR:pt-419

Regras importantes:
- Suporta múltiplos tickers (modo quantidade, ticker, lista, faixa)
- ✅ Para empresas com múltiplas classes (KLBN11/KLBN3/KLBN4), salva em TODAS as classes
- ✅ Se precisar criar pasta, cria SEMPRE com uma classe existente (nunca ticker_base puro)
- Acumula notícias e deduplica por ID determinístico (SHA1 estável)
- Limita 100 notícias mais recentes por classe

DESACOPLAMENTO:
- NÃO gera/atualiza nenhum arquivo do noticiário econômico
- NÃO escreve em balancos/NOTICIAS/noticias_mercado.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs

import pandas as pd
import requests
from bs4 import BeautifulSoup


# =============================================================================
# Helpers básicos
# =============================================================================

def _norm(s: str) -> str:
    return str(s or "").strip().upper()


def extrair_ticker_base(ticker: str) -> str:
    """Remove números finais do ticker (PETR4 -> PETR)."""
    return re.sub(r"\d+$", "", _norm(ticker))


def _safe_int(x, default=None):
    try:
        return int(x)
    except Exception:
        return default


# =============================================================================
# Mapeamento / multi-classe
# =============================================================================

def load_mapeamento_consolidado() -> pd.DataFrame:
    """Carrega CSV de mapeamento (tenta consolidado, fallback para original)."""
    csv_consolidado = "mapeamento_b3_consolidado.csv"
    csv_original = "mapeamento_final_b3_completo_utf8.csv"

    if Path(csv_consolidado).exists():
        try:
            return pd.read_csv(csv_consolidado, sep=";", encoding="utf-8-sig", dtype=str)
        except Exception:
            pass

    if Path(csv_original).exists():
        try:
            return pd.read_csv(csv_original, sep=";", encoding="utf-8-sig", dtype=str)
        except Exception:
            pass

    try:
        return pd.read_csv(csv_original, sep=";", dtype=str)
    except Exception as e:
        raise FileNotFoundError("Nenhum arquivo de mapeamento encontrado") from e


def _col_first_non_empty(row: pd.Series, cols: list[str]) -> str:
    for c in cols:
        if c in row and pd.notna(row[c]) and str(row[c]).strip():
            return str(row[c]).strip()
    return ""


def buscar_nome_empresa_ticker_base(ticker_base: str, df_full: pd.DataFrame) -> str:
    tb = _norm(ticker_base)
    try:
        m = df_full[df_full["ticker_base"] == tb]
        if m.empty:
            return tb
        row = m.iloc[0]
        nome = _col_first_non_empty(row, ["empresa", "nome", "razao_social", "denominacao_social"])
        return nome if nome else tb
    except Exception:
        return tb


def listar_classes_da_empresa(ticker_base: str, df_full: pd.DataFrame) -> list[str]:
    """Retorna todas as classes (tickers) que pertencem ao ticker_base."""
    tb = _norm(ticker_base)

    if "ticker_base" not in df_full.columns:
        df_full = df_full.copy()
        df_full["ticker_base"] = df_full["ticker"].apply(extrair_ticker_base)

    try:
        m = df_full[df_full["ticker_base"] == tb]
        if m.empty:
            return []
        tickers = [_norm(x) for x in m["ticker"].dropna().astype(str).tolist() if str(x).strip()]
        # remove duplicados preservando ordem
        tickers = list(dict.fromkeys(tickers))
        # garante que classes (com número) venham primeiro
        tickers.sort(key=lambda t: (len(t) == len(tb), len(t)))
        return tickers
    except Exception:
        return []


def garantir_pastas_classes(pasta_saida: Path, tickers_classes: list[str], ticker_base: str) -> list[Path]:
    """
    ✅ Regra de criação: se precisar criar pasta, cria SEMPRE com classe existente.
    - Se tickers_classes estiver vazio (mapeamento falho), faz fallback para ticker_base (último recurso).
    """
    pasta_saida.mkdir(parents=True, exist_ok=True)

    if not tickers_classes:
        p = pasta_saida / _norm(ticker_base)
        p.mkdir(parents=True, exist_ok=True)
        return [p]

    paths: list[Path] = []
    for t in tickers_classes:
        p = pasta_saida / _norm(t)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
        paths.append(p)
    return paths


# =============================================================================
# Scraping Google News RSS (modelo simples q=ticker)
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
    """
    Retorna (YYYY-MM-DD, YYYY-MM-DD HH:MM:SS)
    """
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
    Se o link for do Google News e trouxer parâmetro url=, retorna a URL real.
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

        if dominio:
            return dominio.split(".")[0].capitalize()

        return "Desconhecida"
    except Exception:
        return "Desconhecida"


def _gerar_id_noticia_estavel(titulo: str, link: Optional[str], data_hora: str) -> int:
    base = f"{(titulo or '').strip()}|{(link or '').strip()}|{(data_hora or '').strip()}"
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def buscar_noticias_scraping_google_rss(ticker: str, max_itens: int = 30) -> list[dict]:
    """
    MODELO SIMPLES (como o seu exemplo):
    - q = ticker (classe)
    - hl=pt-BR gl=BR ceid=BR:pt-419

    Retorna lista de notícias padronizadas.
    """
    t = _norm(ticker)
    if not t:
        return []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    params = {
        "q": t,                 # ✅ modelo simples: ticker puro
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

    resultados: list[dict] = []

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
            print(f"⚠️ Erro ao processar item: {e}")
            continue

    return resultados


# =============================================================================
# Persistência: noticiario.json em todas as classes
# =============================================================================

def _ler_json_resiliente(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def salvar_noticiario_multiclasse(
    ticker_base: str,
    nome_empresa: str,
    tickers_classes: list[str],
    noticias_rss: list[dict],
    pasta_saida: Path,
) -> list[Path]:
    """
    Salva o noticiário empresarial em TODAS as classes:
      balancos/<TICKER_CLASSE>/noticiario.json
    """
    tb = _norm(ticker_base)
    ne = str(nome_empresa or tb).strip()

    pastas = garantir_pastas_classes(pasta_saida, tickers_classes, tb)
    salvos: list[Path] = []

    # Padroniza notícias RSS -> formato final
    novas_padronizadas: list[dict] = []
    for n in noticias_rss:
        titulo = str(n.get("titulo", "")).strip()
        url = n.get("link")
        data_hora = str(n.get("data_hora", "")).strip()
        nid = _gerar_id_noticia_estavel(titulo, url, data_hora)

        novas_padronizadas.append({
            "id": nid,
            "data": str(n.get("data", "")).strip(),
            "data_hora": data_hora,
            "titulo": titulo,
            "descricao": str(n.get("descricao", "")).strip(),
            "fonte": str(n.get("fonte", "")).strip() or "Desconhecida",
            "url": url,
            "tipo": "noticia_empresarial",  # ✅ não confunde com econômico
        })

    for pasta_ticker in pastas:
        ticker_classe = _norm(pasta_ticker.name)
        arquivo = pasta_ticker / "noticiario.json"

        dados_exist = _ler_json_resiliente(arquivo)
        existentes = dados_exist.get("noticias", []) if isinstance(dados_exist, dict) else []
        if not isinstance(existentes, list):
            existentes = []

        # Dedupe por id
        d: dict[int, dict] = {}
        for x in existentes:
            if isinstance(x, dict) and x.get("id") is not None:
                d[_safe_int(x["id"], x["id"])] = x

        for x in novas_padronizadas:
            if isinstance(x, dict) and x.get("id") is not None:
                d[_safe_int(x["id"], x["id"])] = x

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
            "noticias": finais,
        }

        try:
            with open(arquivo, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            salvos.append(arquivo)
        except Exception as e:
            print(f"  ❌ Erro ao salvar {ticker_classe}: {e}")

    return salvos


# =============================================================================
# Seleção de empresas (CLI)
# =============================================================================

def selecionar_empresas(df_base: pd.DataFrame, modo: str, **kwargs) -> pd.DataFrame:
    modo = (modo or "quantidade").strip().lower()

    if modo == "ticker":
        ticker = _norm(kwargs.get("ticker", "") or kwargs.get("positional_ticker", ""))
        if not ticker:
            return df_base.iloc[0:0]
        tb = extrair_ticker_base(ticker)
        return df_base[df_base["ticker_base"] == tb].head(1)

    if modo == "lista":
        lista = kwargs.get("lista", "") or ""
        ticks = [_norm(x) for x in re.split(r"[,\s]+", lista) if x.strip()]
        bases = [extrair_ticker_base(t) for t in ticks]
        return df_base[df_base["ticker_base"].isin(bases)].drop_duplicates("ticker_base").reset_index(drop=True)

    if modo == "faixa":
        faixa = kwargs.get("faixa", "1-50")
        inicio, fim = map(int, faixa.split("-"))
        return df_base.iloc[inicio - 1: fim].reset_index(drop=True)

    qtd = int(kwargs.get("quantidade", 10) or 10)
    return df_base.head(qtd).reset_index(drop=True)


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Captura noticiário empresarial via Google News RSS (q=ticker)")
    parser.add_argument("--modo", choices=["quantidade", "ticker", "lista", "faixa"], default="quantidade")
    parser.add_argument("--quantidade", type=int, default=10)
    parser.add_argument("--ticker", default="")
    parser.add_argument("--lista", default="")
    parser.add_argument("--faixa", default="1-50")

    # compatibilidade: python script.py KLBN11
    parser.add_argument("positional_ticker", nargs="?", default="")

    args = parser.parse_args()

    if args.positional_ticker and not args.ticker:
        args.modo = "ticker"
        args.ticker = args.positional_ticker

    try:
        df_full = load_mapeamento_consolidado()
        if "ticker" not in df_full.columns:
            raise ValueError("CSV de mapeamento não possui coluna 'ticker'.")

        df_full = df_full[df_full["ticker"].notna()].copy()
        df_full["ticker"] = df_full["ticker"].astype(str).apply(_norm)
        df_full["ticker_base"] = df_full["ticker"].apply(extrair_ticker_base)

        df_base = df_full.drop_duplicates(subset=["ticker_base"], keep="first").reset_index(drop=True)

    except Exception as e:
        print(f"❌ Erro ao carregar mapeamento: {e}")
        sys.exit(1)

    pasta_saida = Path("balancos")
    pasta_saida.mkdir(exist_ok=True)

    df_sel = selecionar_empresas(
        df_base,
        args.modo,
        quantidade=args.quantidade,
        ticker=args.ticker,
        lista=args.lista,
        faixa=args.faixa,
        positional_ticker=args.positional_ticker,
    )

    if df_sel.empty:
        print("❌ Nenhuma empresa selecionada com os critérios fornecidos.")
        sys.exit(1)

    print(f"\n{'='*70}")
    print(">>> JOB: CAPTURAR NOTICIÁRIO EMPRESARIAL (RSS q=ticker) <<<")
    print(f"{'='*70}")
    print(f"Modo: {args.modo}")
    print(f"Empresas selecionadas (ticker_base): {len(df_sel)}")
    print("Fonte: Google News RSS")
    print("Saída: balancos/<TICKER_CLASSE>/noticiario.json (todas as classes)")
    print(f"{'='*70}")

    ok = 0
    erro = 0

    for idx, (_, row) in enumerate(df_sel.iterrows(), 1):
        tb = _norm(row.get("ticker_base", ""))
        if not tb:
            erro += 1
            continue

        classes = listar_classes_da_empresa(tb, df_full)
        nome = buscar_nome_empresa_ticker_base(tb, df_full)

        # Se rodar em modo ticker, prioriza a classe informada como "ticker consulta" (se ela pertencer ao base)
        ticker_consulta = None
        if args.modo == "ticker":
            t_in = _norm(args.ticker)
            if t_in and extrair_ticker_base(t_in) == tb:
                ticker_consulta = t_in

        # Caso contrário, escolhe uma classe com número (preferência) ou a primeira
        if not ticker_consulta:
            ticker_consulta = None
            for t in classes:
                if len(t) > len(tb):  # tem número (classe)
                    ticker_consulta = t
                    break
            if not ticker_consulta:
                ticker_consulta = classes[0] if classes else tb

        print(f"\n[{idx}/{len(df_sel)}] 📰 {tb} ({nome})")
        if classes:
            print(f"  Classes: {', '.join(classes)}")
        print(f"  Consulta RSS (q=): {ticker_consulta}")

        noticias_rss = buscar_noticias_scraping_google_rss(ticker_consulta, max_itens=30)

        if not noticias_rss:
            print("  ⚠️ Nenhuma notícia encontrada")
            erro += 1
            continue

        salvos = salvar_noticiario_multiclasse(
            ticker_base=tb,
            nome_empresa=nome,
            tickers_classes=classes if classes else [ticker_consulta],
            noticias_rss=noticias_rss,
            pasta_saida=pasta_saida,
        )

        if salvos:
            print(f"  ✅ Salvo em {len(salvos)} pasta(s)")
            ok += 1
        else:
            print("  ❌ Falha ao salvar")
            erro += 1

    print(f"\n{'='*70}")
    print(f"✅ Finalizado: OK={ok} | ERRO={erro}")
    print(f"💾 Saída: {pasta_saida}/")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
