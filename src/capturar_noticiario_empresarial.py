"""
CAPTURA DE NOTICIÁRIO EMPRESARIAL - VERSÃO GITHUB ACTIONS
- Busca notícias via Google News RSS
- Suporta múltiplos tickers (modo lista, quantidade, ticker, faixa)
- Salva em JSON na pasta de cada ticker da empresa (balancos/<TICKER>/noticiario.json)
  ✅ FIX: empresas com múltiplas classes (ex: KLBN11, KLBN3, KLBN4) agora recebem o arquivo em TODAS as pastas
- Acumula notícias (evita duplicatas por ID)
- Limita a 100 notícias mais recentes por ticker
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
from urllib.parse import urlparse, parse_qs
import argparse
import sys
import pandas as pd
from pathlib import Path


# ============================================================================
# UTILITÁRIOS MULTI-TICKER
# ============================================================================

def load_mapeamento_consolidado() -> pd.DataFrame:
    """Carrega CSV de mapeamento (tenta consolidado, fallback para original)."""
    csv_consolidado = "mapeamento_b3_consolidado.csv"
    csv_original = "mapeamento_final_b3_completo_utf8.csv"

    if Path(csv_consolidado).exists():
        try:
            return pd.read_csv(csv_consolidado, sep=";", encoding="utf-8-sig")
        except Exception:
            pass

    if Path(csv_original).exists():
        try:
            return pd.read_csv(csv_original, sep=";", encoding="utf-8-sig")
        except Exception:
            pass

    try:
        return pd.read_csv(csv_original, sep=";")
    except Exception as e:
        raise FileNotFoundError("Nenhum arquivo de mapeamento encontrado") from e


def normalizar_ticker(ticker: str) -> str:
    return str(ticker or "").strip().upper()


def extrair_ticker_base(ticker: str) -> str:
    """
    Remove números finais do ticker (PETR4 -> PETR).
    """
    return re.sub(r"\d+$", "", normalizar_ticker(ticker))


def listar_tickers_da_empresa(ticker_base: str, df: pd.DataFrame) -> list[str]:
    """
    Retorna TODOS os tickers (classes) associados ao ticker_base, ex:
    KLBN -> ["KLBN11","KLBN4","KLBN3"] (ordem preservada por prioridade simples)
    """
    tb = normalizar_ticker(ticker_base)
    if "ticker" not in df.columns:
        return [tb]

    candidatos = []
    for t in df.loc[df["ticker_base"] == tb, "ticker"].dropna().astype(str).tolist():
        tt = normalizar_ticker(t)
        if extrair_ticker_base(tt) == tb:
            candidatos.append(tt)

    # remove duplicados preservando ordem
    vistos = set()
    uniq = []
    for x in candidatos:
        if x not in vistos:
            uniq.append(x)
            vistos.add(x)

    if not uniq:
        return [tb]

    # Prioridade típica B3: units 11, depois PN (4/5/6), depois ON (3/1/2)
    # (não é regra absoluta, mas ajuda a manter uma ordem estável)
    prioridade = {"11": 0, "6": 1, "5": 2, "4": 3, "3": 4, "2": 5, "1": 6}

    def key(tk: str):
        suf = re.findall(r"\d+$", tk)
        suf = suf[0] if suf else ""
        return (prioridade.get(suf, 99), len(tk), tk)

    uniq.sort(key=key)
    return uniq


def buscar_nome_empresa_ticker(ticker_base: str, df: pd.DataFrame) -> str:
    """
    Busca o nome da empresa associada ao ticker_base no DataFrame.
    """
    try:
        match = df[df["ticker_base"] == normalizar_ticker(ticker_base)]
        if not match.empty and "empresa" in match.columns:
            return str(match.iloc[0]["empresa"]).strip()
        return normalizar_ticker(ticker_base)
    except Exception as e:
        print(f"⚠️ Erro ao buscar nome da empresa: {e}")
        return normalizar_ticker(ticker_base)


# ============================================================================
# FUNÇÕES DE EXTRAÇÃO DE NOTÍCIAS
# ============================================================================

def extrair_data_publicacao(item):
    """
    Extrai a data de publicação do item RSS do Google News.
    """
    try:
        pub_date = item.find("pubDate")
        if pub_date:
            data_str = pub_date.text  # Wed, 08 Jan 2026 14:30:00 GMT
            data_obj = datetime.strptime(data_str, "%a, %d %b %Y %H:%M:%S %Z")
            return data_obj.strftime("%Y-%m-%d"), data_obj.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass

    agora = datetime.now()
    return agora.strftime("%Y-%m-%d"), agora.strftime("%Y-%m-%d %H:%M:%S")


def extrair_fonte_noticia(link: str) -> str:
    """
    Extrai a fonte da notícia a partir da URL.
    """
    try:
        if not link:
            return "Desconhecida"

        if "news.google.com" in link:
            parsed = urlparse(link)
            params = parse_qs(parsed.query)
            if "url" in params:
                url_real = params["url"][0]
                dominio = urlparse(url_real).netloc
            else:
                return "Google News"
        else:
            dominio = urlparse(link).netloc

        dominio = dominio.replace("www.", "")

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

        for dominio_chave, nome_fonte in fontes_conhecidas.items():
            if dominio_chave in dominio:
                return nome_fonte

        return dominio.split(".")[0].capitalize() if dominio else "Desconhecida"

    except Exception:
        return "Desconhecida"


def limpar_descricao_html(descricao: str) -> str:
    """
    Remove tags HTML da descrição e limpa o texto.
    """
    try:
        soup = BeautifulSoup(descricao or "", "html.parser")
        texto = soup.get_text()
        texto = " ".join(texto.split())
        if len(texto) > 300:
            texto = texto[:297] + "..."
        return texto
    except Exception:
        return descricao or ""


def buscar_noticiario_empresarial(ticker_base: str, nome_empresa: str) -> list:
    """
    Busca notícias do mercado sobre a empresa via Google News RSS.
    """
    try:
        tb = normalizar_ticker(ticker_base)
        ne = str(nome_empresa or tb).strip()

        # Query mais específica (mantida)
        query = f"{ne} OR {tb} bolsa ações"
        url = f"https://news.google.com/rss/search?q={query}&hl=pt-BR&gl=BR&ceid=BR:pt-419"

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        response = requests.get(url, headers=headers, timeout=15)

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
                descricao = item.find("description").text if item.find("description") else "Descrição não disponível"

                descricao_limpa = limpar_descricao_html(descricao)
                data, data_hora = extrair_data_publicacao(item)
                fonte = extrair_fonte_noticia(link) if link else "Desconhecida"

                # ID consistente por título+data_hora
                id_noticia = hash(f"{titulo}{data_hora}") & 0x7FFFFFFF

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

    Ex: ticker_base=KLBN, tickers_alvo=["KLBN11","KLBN4","KLBN3"]
        salva:
          balancos/KLBN11/noticiario.json
          balancos/KLBN4/noticiario.json
          balancos/KLBN3/noticiario.json
    """
    salvos: list[Path] = []

    for ticker in tickers_alvo:
        try:
            pasta_ticker = pasta_saida / normalizar_ticker(ticker)
            pasta_ticker.mkdir(parents=True, exist_ok=True)
            arquivo_json = pasta_ticker / "noticiario.json"

            noticias_existentes = []
            if arquivo_json.exists():
                with open(arquivo_json, "r", encoding="utf-8") as f:
                    dados_existentes = json.load(f)
                    noticias_existentes = dados_existentes.get("noticias", [])

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

    Returns:
        True se salvou ao menos 1 arquivo, False caso contrário
    """
    try:
        ticker_base = normalizar_ticker(row["ticker_base"])
        nome_empresa = row.get("empresa", ticker_base)

        tickers_alvo = listar_tickers_da_empresa(ticker_base, df_full)

        print(f"\n📰 {ticker_base} - {str(nome_empresa)[:60]}")
        print(f"  🎯 Tickers alvo: {', '.join(tickers_alvo)}")

        noticias = buscar_noticiario_empresarial(ticker_base, nome_empresa)

        if not noticias:
            print("  ⚠️ Nenhuma notícia encontrada")
            return False

        salvos = salvar_noticiario_json_multiplos(
            ticker_base=ticker_base,
            nome_empresa=nome_empresa,
            tickers_alvo=tickers_alvo,
            noticias=noticias,
            pasta_saida=pasta_saida,
        )

        if salvos:
            for p in salvos:
                print(f"  ✅ {p}")
            return True

        return False

    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False


def selecionar_empresas(df_base: pd.DataFrame, modo: str, **kwargs) -> pd.DataFrame:
    """
    Seleciona empresas baseado no modo especificado.
    df_base deve conter 1 linha por ticker_base.
    """
    if modo == "quantidade":
        qtd = int(kwargs.get("quantidade", 10))
        return df_base.head(qtd)

    elif modo == "ticker":
        ticker = normalizar_ticker(kwargs.get("ticker", ""))
        ticker_base = extrair_ticker_base(ticker)
        return df_base[df_base["ticker_base"] == ticker_base]

    elif modo == "lista":
        lista = kwargs.get("lista", "")
        bases = []
        for t in lista.split(","):
            tt = normalizar_ticker(t)
            if tt:
                bases.append(extrair_ticker_base(tt))
        bases = list(dict.fromkeys(bases))  # unique mantendo ordem
        return df_base[df_base["ticker_base"].isin(bases)]

    elif modo == "faixa":
        faixa = kwargs.get("faixa", "1-50")
        inicio, fim = map(int, faixa.split("-"))
        return df_base.iloc[inicio - 1 : fim]

    else:
        print(f"⚠️ Modo '{modo}' não reconhecido. Usando primeiras 10 empresas.")
        return df_base.head(10)


def processar_lote(df_sel: pd.DataFrame, df_full: pd.DataFrame, pasta_saida: Path):
    """
    Processa um lote de empresas selecionadas (1 por ticker_base).
    """
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
    """
    Função principal com suporte a argumentos CLI.
    ✅ FIX: aceita ticker posicional (ex: python script.py KLBN11)
    """
    parser = argparse.ArgumentParser(
        description="Captura noticiário empresarial via Google News RSS"
    )
    parser.add_argument(
        "--modo",
        choices=["quantidade", "ticker", "lista", "faixa"],
        default="quantidade",
        help="Modo de seleção: quantidade, ticker, lista, faixa",
    )
    parser.add_argument(
        "--quantidade",
        type=int,
        default=10,
        help="Quantidade de empresas (modo quantidade)"
    )
    parser.add_argument(
        "--ticker",
        default="",
        help="Ticker específico (modo ticker): ex: PETR4 ou KLBN11"
    )
    parser.add_argument(
        "--lista",
        default="",
        help="Lista de tickers (modo lista): ex: PETR4,VALE3,KLBN11"
    )
    parser.add_argument(
        "--faixa",
        default="1-50",
        help="Faixa de linhas (modo faixa): ex: 1-50, 51-150"
    )

    # ✅ NOVO: captura argumento posicional opcional (compatível com workflow antigo)
    parser.add_argument(
        "positional_ticker",
        nargs="?",
        default="",
        help="(Opcional) Ticker posicional. Ex: python script.py KLBN11"
    )

    args = parser.parse_args()

    # ✅ Se veio ticker posicional, assume modo ticker automaticamente
    if args.positional_ticker and not args.ticker:
        args.modo = "ticker"
        args.ticker = args.positional_ticker

    # Carregar mapeamento
    try:
        df_full = load_mapeamento_consolidado()
        df_full = df_full[df_full["ticker"].notna()].reset_index(drop=True)

        df_full["ticker"] = df_full["ticker"].astype(str).apply(normalizar_ticker)
        df_full["ticker_base"] = df_full["ticker"].apply(extrair_ticker_base)

        # df_base: 1 linha por ticker_base (para não processar duplicado)
        df_base = df_full.drop_duplicates(subset=["ticker_base"], keep="first").reset_index(drop=True)

    except Exception as e:
        print(f"❌ Erro ao carregar mapeamento: {e}")
        sys.exit(1)

    # Pasta de saída
    pasta_saida = Path("balancos")
    pasta_saida.mkdir(exist_ok=True)

    # Seleção baseada no modo
    df_sel = selecionar_empresas(
        df_base,
        args.modo,
        quantidade=args.quantidade,
        ticker=args.ticker,
        lista=args.lista,
        faixa=args.faixa
    )

    if df_sel.empty:
        print("❌ Nenhuma empresa selecionada com os critérios fornecidos.")
        sys.exit(1)

    # Exibir informações do job
    print(f"\n{'='*70}")
    print(f">>> JOB: CAPTURAR NOTICIÁRIO EMPRESARIAL <<<")
    print(f"{'='*70}")
    print(f"Modo: {args.modo}")
    print(f"Empresas selecionadas (ticker_base): {len(df_sel)}")
    print(f"Fonte: Google News RSS")
    print(f"Limite por empresa: 30 notícias novas (max 100 acumuladas) POR TICKER")
    print(f"Saída: balancos/<TICKER>/noticiario.json (todas as classes)")
    print(f"{'='*70}")

    # Processar
    processar_lote(df_sel, df_full, pasta_saida)



if __name__ == "__main__":
    main()
