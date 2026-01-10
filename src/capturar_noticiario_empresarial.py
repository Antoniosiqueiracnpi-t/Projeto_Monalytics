"""
CAPTURA DE NOTICIÁRIO EMPRESARIAL - VERSÃO GITHUB ACTIONS
- Busca notícias via Google News RSS
- Suporta múltiplos tickers (modo lista, quantidade, ticker, faixa)
- Salva em JSON na pasta de cada ticker da empresa (balancos/<TICKER>/noticiario.json)
  ✅ FIX: empresas com múltiplas classes (ex: KLBN11, KLBN3, KLBN4) agora recebem o arquivo em TODAS as pastas
- Acumula notícias (evita duplicatas por ID)
- Limita a 100 notícias mais recentes por ticker

FIXES DEFINITIVOS (sem afetar outras funcionalidades):
1) Deduplicação determinística: NÃO usa hash() do Python (instável entre execuções).
   Agora usa SHA1 estável (título|link|data_hora) -> evita duplicatas e comportamento errático entre runs.
2) pubDate robusto: parsing via email.utils.parsedate_to_datetime.
3) Fonte robusta: prioriza <source> do RSS (quando existir), fallback por domínio.
4) Query/URL robusta: requests.get com params= (encoding correto).
5) Leitura do JSON existente resiliente: se JSON estiver corrompido, não derruba o ticker (reconstrói).
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup


# ============================================================================
# UTILITÁRIOS MULTI-TICKER
# ============================================================================

def load_mapeamento_consolidado() -> pd.DataFrame:
    """Carrega CSV de mapeamento (tenta consolidado, fallback para original)."""
    csv_consolidado = "mapeamento_b3_consolidado.csv"
    csv_original = "mapeamento_final_b3_completo_utf8.csv"

    if Path(csv_consolidado).exists():
        return pd.read_csv(csv_consolidado, sep=";", encoding="utf-8", dtype=str)
    if Path(csv_original).exists():
        return pd.read_csv(csv_original, sep=";", encoding="utf-8", dtype=str)

    raise FileNotFoundError("Nenhum CSV de mapeamento encontrado (consolidado/original).")


def normalizar_ticker(t: str) -> str:
    return str(t or "").strip().upper()


def extrair_ticker_base(ticker: str) -> str:
    """Extrai ticker base removendo sufixos numéricos (KLBN11 -> KLBN)."""
    t = normalizar_ticker(ticker)
    return re.sub(r"\d+$", "", t)


def listar_tickers_da_empresa(df_full: pd.DataFrame, ticker_base: str) -> list[str]:
    """Retorna todos os tickers (classes) que pertencem ao mesmo ticker_base."""
    tb = normalizar_ticker(ticker_base)
    tickers = df_full.loc[df_full["ticker_base"] == tb, "ticker"].dropna().astype(str).tolist()
    tickers = [normalizar_ticker(x) for x in tickers if str(x).strip()]
    # remove duplicados preservando ordem
    return list(dict.fromkeys(tickers))


def buscar_nome_empresa_ticker(row: pd.Series) -> str:
    """Retorna nome da empresa (se existir no CSV), fallback para ticker_base."""
    for col in ["empresa", "nome", "razao_social", "denominacao_social"]:
        if col in row and pd.notna(row[col]) and str(row[col]).strip():
            return str(row[col]).strip()
    # fallback
    return str(row.get("ticker_base") or row.get("ticker") or "").strip()


# ============================================================================
# PARSING RSS
# ============================================================================

def extrair_data_publicacao(item) -> tuple[str, str]:
    """
    Extrai a data de publicação do item RSS do Google News.
    Retorna (YYYY-MM-DD, YYYY-MM-DD HH:MM:SS)
    """
    try:
        pub_date = item.find("pubDate")
        if pub_date and pub_date.text:
            dt = parsedate_to_datetime(pub_date.text.strip())
            # dt pode vir timezone-aware; para padronizar exibimos sem tz no campo data_hora
            return dt.strftime("%Y-%m-%d"), dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass

    agora = datetime.now()
    return agora.strftime("%Y-%m-%d"), agora.strftime("%Y-%m-%d %H:%M:%S")


def extrair_fonte_noticia(link: Optional[str], item=None) -> str:
    """
    Extrai a fonte da notícia.
    - Prioriza <source> do RSS (mais confiável no Google News RSS)
    - Fallback: tenta extrair domínio da URL (inclui tentativa com parâmetro url=)
    """
    try:
        # 1) Prioriza <source>
        if item is not None:
            src = item.find("source")
            if src and src.text:
                return src.text.strip()

        if not link:
            return "Desconhecida"

        # 2) Fallback por domínio / url real
        dominio = ""
        try:
            if "news.google.com" in link:
                parsed = urlparse(link)
                params = parse_qs(parsed.query)
                if "url" in params and params["url"]:
                    url_real = params["url"][0]
                    dominio = urlparse(url_real).netloc
                else:
                    dominio = urlparse(link).netloc
            else:
                dominio = urlparse(link).netloc
        except Exception:
            dominio = ""

        dominio = (dominio or "").replace("www.", "").strip()

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


def limpar_descricao_html(descricao: str) -> str:
    if not descricao:
        return ""
    # remove tags HTML
    texto = re.sub(r"<[^>]+>", " ", str(descricao))
    texto = re.sub(r"\s+", " ", texto).strip()
    # limita tamanho para evitar JSON gigante (mantém estética do front)
    if len(texto) > 300:
        texto = texto[:297] + "..."
    return texto


def _gerar_id_noticia_estavel(titulo: str, link: Optional[str], data_hora: str) -> int:
    """
    Gera um ID estável entre execuções (importante para deduplicação).
    NÃO usar hash() do Python (instável entre runs).
    """
    base = f"{titulo.strip()}|{(link or '').strip()}|{data_hora.strip()}"
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def buscar_noticiario_empresarial(ticker_base: str, nome_empresa: str) -> list:
    """
    Busca notícias do mercado sobre a empresa via Google News RSS.
    """
    try:
        tb = normalizar_ticker(ticker_base)
        ne = str(nome_empresa or tb).strip()

        query = f'("{ne}") OR ({tb}) bolsa ações'
        url = "https://news.google.com/rss/search"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        params = {
            "q": query,
            "hl": "pt-BR",
            "gl": "BR",
            "ceid": "BR:pt-419",
        }

        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"⚠️ Erro ao buscar notícias: Status {response.status_code}")
            return []

        soup = BeautifulSoup(response.content, "xml")
        itens = soup.find_all("item")

        noticias = []
        for item in itens[:30]:
            try:
                titulo = item.find("title").text if item.find("title") else "Título não disponível"
                link = item.find("link").text if item.find("link") else None
                descricao = item.find("description").text if item.find("description") else ""

                descricao_limpa = limpar_descricao_html(descricao)
                data, data_hora = extrair_data_publicacao(item)
                fonte = extrair_fonte_noticia(link, item=item) if link else "Desconhecida"

                id_noticia = _gerar_id_noticia_estavel(titulo, link, data_hora)

                noticias.append(
                    {
                        "id": id_noticia,
                        "data": data,
                        "data_hora": data_hora,
                        "titulo": titulo.strip(),
                        "descricao": descricao_limpa,
                        "fonte": fonte,
                        "url": link,
                        "tipo": "noticia_mercado",
                    }
                )
            except Exception as e:
                print(f"⚠️ Erro ao processar item de notícia: {e}")
                continue

        return noticias

    except Exception as e:
        print(f"❌ Erro ao buscar noticiário empresarial: {e}")
        return []


def salvar_noticiario_json_multiplos(
    ticker_base: str,
    nome_empresa: str,
    tickers_alvo: list[str],
    noticias: list,
    pasta_saida: Path,
) -> list[Path]:
    """
    ✅ FIX: salva o MESMO noticiário em TODAS as pastas de tickers da empresa.
    Acumula com notícias existentes por ID, e limita a 100 por ticker.
    """
    salvos: list[Path] = []

    for ticker in tickers_alvo:
        try:
            pasta_ticker = pasta_saida / normalizar_ticker(ticker)
            pasta_ticker.mkdir(parents=True, exist_ok=True)
            arquivo_json = pasta_ticker / "noticiario.json"

            noticias_existentes = []
            if arquivo_json.exists():
                try:
                    with open(arquivo_json, "r", encoding="utf-8") as f:
                        dados_existentes = json.load(f)
                        noticias_existentes = dados_existentes.get("noticias", []) or []
                except Exception:
                    # JSON corrompido / inválido -> recomeça sem derrubar o processo
                    noticias_existentes = []

            noticias_dict = {}
            for n in noticias_existentes:
                if isinstance(n, dict) and n.get("id") is not None:
                    noticias_dict[n["id"]] = n

            for n in noticias:
                if isinstance(n, dict) and n.get("id") is not None:
                    noticias_dict[n["id"]] = n

            noticias_finais = list(noticias_dict.values())
            noticias_finais.sort(key=lambda x: x.get("data_hora", ""), reverse=True)
            noticias_finais = noticias_finais[:100]

            dados_finais = {
                "empresa": {
                    "ticker": normalizar_ticker(ticker),
                    "ticker_base": normalizar_ticker(ticker_base),
                    "nome": str(nome_empresa or ticker_base).strip(),
                },
                "ultima_atualizacao": datetime.now().isoformat(),
                "total_noticias": len(noticias_finais),
                "fonte": "Google News",
                "noticias": noticias_finais,
            }

            with open(arquivo_json, "w", encoding="utf-8") as f:
                json.dump(dados_finais, f, ensure_ascii=False, indent=2)

            salvos.append(arquivo_json)

        except Exception as e:
            print(f"  ❌ Erro ao salvar em {ticker}: {e}")

    return salvos


# ============================================================================
# PROCESSAMENTO EM LOTE
# ============================================================================

def processar_ticker(row: pd.Series, df_full: pd.DataFrame, pasta_saida: Path) -> bool:
    """
    Processa um ticker_base: busca 1x e salva em todas as classes (tickers) da empresa.
    """
    try:
        ticker_base = normalizar_ticker(row.get("ticker_base") or "")
        if not ticker_base:
            print("❌ ticker_base vazio. Pulando.")
            return False

        nome_empresa = buscar_nome_empresa_ticker(row)

        tickers_alvo = listar_tickers_da_empresa(df_full, ticker_base)
        if not tickers_alvo:
            # fallback: salva ao menos no ticker_base (evita perder empresa)
            tickers_alvo = [ticker_base]

        print(f"{ticker_base} → classes: {', '.join(tickers_alvo)}")

        noticias = buscar_noticiario_empresarial(ticker_base, nome_empresa)

        salvos = salvar_noticiario_json_multiplos(
            ticker_base=ticker_base,
            nome_empresa=nome_empresa,
            tickers_alvo=tickers_alvo,
            noticias=noticias,
            pasta_saida=pasta_saida,
        )

        if salvos:
            print(f"  ✅ Salvo: {len(salvos)} arquivo(s)")
        else:
            print("  ⚠️ Nada salvo")

        return True

    except Exception as e:
        print(f"❌ Erro ao processar {row.get('ticker_base')}: {e}")
        return False


def selecionar_empresas(df_base: pd.DataFrame, modo: str, **kwargs) -> pd.DataFrame:
    """
    Seleciona empresas (1 por ticker_base) conforme modo.
    Mantém a assinatura/contrato existente do seu arquivo atual.
    """
    modo = (modo or "quantidade").strip().lower()

    if modo == "ticker":
        ticker = normalizar_ticker(kwargs.get("ticker", "") or kwargs.get("positional_ticker", ""))
        if not ticker:
            return df_base.iloc[0:0]
        tb = extrair_ticker_base(ticker)
        return df_base[df_base["ticker_base"] == tb].head(1)

    if modo == "lista":
        lista = kwargs.get("lista", "") or ""
        tickers = [normalizar_ticker(x) for x in re.split(r"[,\s]+", lista) if x.strip()]
        bases = [extrair_ticker_base(t) for t in tickers]
        return df_base[df_base["ticker_base"].isin(bases)].drop_duplicates("ticker_base").reset_index(drop=True)

    if modo == "faixa":
        faixa = kwargs.get("faixa", "1-50")
        inicio, fim = map(int, faixa.split("-"))
        return df_base.iloc[inicio - 1 : fim].reset_index(drop=True)

    # quantidade (default)
    qtd = int(kwargs.get("quantidade", 10) or 10)
    return df_base.head(qtd).reset_index(drop=True)


def processar_lote(df_sel: pd.DataFrame, df_full: pd.DataFrame, pasta_saida: Path):
    print(f"\n{'='*70}")
    print(f"🚀 Processando {len(df_sel)} empresas...")
    print(f"{'='*70}")

    ok_count = 0
    err_count = 0

    for idx, (_, row) in enumerate(df_sel.iterrows(), 1):
        print(f"\n[{idx}/{len(df_sel)}]", end=" ")
        sucesso = processar_ticker(row, df_full, pasta_saida)
        if sucesso:
            ok_count += 1
        else:
            err_count += 1

    print(f"\n{'='*70}")
    print(f"✅ Finalizado: OK={ok_count} | ERRO={err_count}")
    print(f"💾 Salvos em: {pasta_saida}/")
    print(f"{'='*70}\n")


# ============================================================================
# MAIN COM ARGPARSE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Captura noticiário empresarial via Google News RSS")
    parser.add_argument(
        "--modo",
        choices=["quantidade", "ticker", "lista", "faixa"],
        default="quantidade",
        help="Modo de seleção: quantidade, ticker, lista, faixa",
    )
    parser.add_argument("--quantidade", type=int, default=10, help="Quantidade de empresas (modo quantidade)")
    parser.add_argument("--ticker", default="", help="Ticker específico (modo ticker): ex: PETR4 ou KLBN11")
    parser.add_argument("--lista", default="", help="Lista de tickers (modo lista): ex: PETR4,VALE3,KLBN11")
    parser.add_argument("--faixa", default="1-50", help="Faixa de linhas (modo faixa): ex: 1-50, 51-150")

    # ✅ aceita ticker posicional (workflow antigo: python script.py KLBN11)
    parser.add_argument("positional_ticker", nargs="?", default="", help="Ticker posicional (opcional)")

    args = parser.parse_args()

    # se veio posicional, assume modo ticker
    if args.positional_ticker and not args.ticker:
        args.modo = "ticker"
        args.ticker = args.positional_ticker

    try:
        df_full = load_mapeamento_consolidado()
        df_full = df_full[df_full["ticker"].notna()].reset_index(drop=True)

        df_full["ticker"] = df_full["ticker"].astype(str).apply(normalizar_ticker)
        df_full["ticker_base"] = df_full["ticker"].apply(extrair_ticker_base)

        df_base = df_full.drop_duplicates(subset=["ticker_base"], keep="first").reset_index(drop=True)
        df_base["ticker_base"] = df_base["ticker_base"].astype(str).apply(normalizar_ticker)

    except Exception as e:
        print(f"❌ Erro ao carregar mapeamento: {e}")
        sys.exit(1)

    pasta_saida = Path("balancos")
    pasta_saida.mkdir(exist_ok=True)

    df_sel = selecionar_empresas(
        df_base,
        args.modo,
        df_full=df_full,
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
    print(">>> JOB: CAPTURAR NOTICIÁRIO EMPRESARIAL <<<")
    print(f"{'='*70}")
    print(f"Modo: {args.modo}")
    print(f"Empresas selecionadas (ticker_base): {len(df_sel)}")
    print("Fonte: Google News RSS")
    print("Limite por empresa: 30 notícias novas (max 100 acumuladas) POR TICKER")
    print("Saída: balancos/<TICKER>/noticiario.json (todas as classes)")
    print(f"{'='*70}")

    processar_lote(df_sel, df_full, pasta_saida)


if __name__ == "__main__":
    main()
