"""
CAPTURA DE NOTICIÁRIO EMPRESARIAL - VERSÃO GITHUB ACTIONS
- Busca notícias via Google News RSS
- Suporta múltiplos tickers (modo lista, quantidade, ticker, faixa)
- Salva em JSON na pasta de cada empresa (balancos/<TICKER>/noticiario.json)
- Acumula notícias (evita duplicatas por ID)
- Limita a 100 notícias mais recentes por empresa
"""

import requests
from bs4 import BeautifulSoup
import json
import os
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
    
    # Tentar CSV consolidado primeiro
    if Path(csv_consolidado).exists():
        try:
            return pd.read_csv(csv_consolidado, sep=";", encoding="utf-8-sig")
        except Exception:
            pass
    
    # Fallback para CSV original
    if Path(csv_original).exists():
        try:
            return pd.read_csv(csv_original, sep=";", encoding="utf-8-sig")
        except Exception:
            pass
    
    # Último fallback
    try:
        return pd.read_csv(csv_original, sep=";")
    except Exception as e:
        raise FileNotFoundError(
            f"Nenhum arquivo de mapeamento encontrado"
        ) from e


def extrair_ticker_base(ticker: str) -> str:
    """
    Remove números finais do ticker (PETR4 -> PETR).
    """
    return re.sub(r'\d+$', '', ticker.upper().strip())


def obter_pasta_ticker(ticker: str) -> Path:
    """
    Determina a pasta correta para salvar os dados do ticker.
    Busca pasta existente que começa com o ticker base.
    """
    base_path = Path("balancos")
    ticker_base = extrair_ticker_base(ticker)
    
    if base_path.exists():
        for pasta in base_path.iterdir():
            if pasta.is_dir() and pasta.name.startswith(ticker_base):
                return pasta
    
    # Se não encontrar, cria nova pasta
    pasta_ticker = base_path / ticker.upper()
    pasta_ticker.mkdir(parents=True, exist_ok=True)
    return pasta_ticker


def buscar_nome_empresa_ticker(ticker: str) -> str:
    """
    Busca o nome da empresa associada ao ticker no mapeamento_b3_consolidado.csv.
    """
    try:
        df = load_mapeamento_consolidado()
        ticker_limpo = ticker.upper().strip()
        
        # Buscar ticker em qualquer posição da string de tickers
        for _, row in df.iterrows():
            tickers_linha = str(row['ticker']).split(';')
            for t in tickers_linha:
                if t.strip().upper() == ticker_limpo:
                    return str(row['empresa']).strip()
        
        return ticker
    except Exception as e:
        print(f"⚠️ Erro ao buscar nome da empresa: {e}")
        return ticker


# ============================================================================
# FUNÇÕES DE EXTRAÇÃO DE NOTÍCIAS
# ============================================================================

def extrair_data_publicacao(item):
    """
    Extrai a data de publicação do item RSS do Google News.
    """
    try:
        pub_date = item.find('pubDate')
        if pub_date:
            # Formato: Wed, 08 Jan 2026 14:30:00 GMT
            data_str = pub_date.text
            data_obj = datetime.strptime(data_str, '%a, %d %b %Y %H:%M:%S %Z')
            return data_obj.strftime('%Y-%m-%d'), data_obj.strftime('%Y-%m-%d %H:%M:%S')
    except:
        pass
    
    # Se falhar, usa data atual
    agora = datetime.now()
    return agora.strftime('%Y-%m-%d'), agora.strftime('%Y-%m-%d %H:%M:%S')


def extrair_fonte_noticia(link: str) -> str:
    """
    Extrai a fonte da notícia a partir da URL.
    """
    try:
        # Google News usa URLs redirecionadas, tenta extrair domínio real
        if 'news.google.com' in link:
            # Tenta extrair URL real dos parâmetros
            parsed = urlparse(link)
            params = parse_qs(parsed.query)
            
            if 'url' in params:
                url_real = params['url'][0]
                dominio = urlparse(url_real).netloc
            else:
                return 'Google News'
        else:
            dominio = urlparse(link).netloc
        
        # Limpa o domínio
        dominio = dominio.replace('www.', '')
        
        # Mapeia fontes conhecidas
        fontes_conhecidas = {
            'infomoney.com.br': 'InfoMoney',
            'valorinveste.globo.com': 'Valor Investe',
            'valor.globo.com': 'Valor Econômico',
            'economia.uol.com.br': 'UOL Economia',
            'moneytimes.com.br': 'Money Times',
            'exame.com': 'Exame',
            'estadao.com.br': 'Estadão',
            'folha.uol.com.br': 'Folha de S.Paulo',
            'g1.globo.com': 'G1',
            'cnnbrasil.com.br': 'CNN Brasil',
            'seudinheiro.com': 'Seu Dinheiro',
            'investnews.com.br': 'InvestNews'
        }
        
        for dominio_chave, nome_fonte in fontes_conhecidas.items():
            if dominio_chave in dominio:
                return nome_fonte
        
        # Se não encontrar, retorna domínio capitalizado
        return dominio.split('.')[0].capitalize()
    
    except:
        return 'Desconhecida'


def limpar_descricao_html(descricao: str) -> str:
    """
    Remove tags HTML da descrição e limpa o texto.
    """
    try:
        # Remove tags HTML
        soup = BeautifulSoup(descricao, 'html.parser')
        texto = soup.get_text()
        
        # Remove espaços extras
        texto = ' '.join(texto.split())
        
        # Limita a 300 caracteres
        if len(texto) > 300:
            texto = texto[:297] + '...'
        
        return texto
    except:
        return descricao


def buscar_noticiario_empresarial(ticker: str) -> list:
    """
    Busca notícias do mercado sobre a empresa via Google News RSS.
    """
    try:
        ticker_clean = extrair_ticker_base(ticker)
        nome_empresa = buscar_nome_empresa_ticker(ticker)
        
        # Monta query de busca mais específica
        query = f'{nome_empresa} OR {ticker_clean} bolsa ações'
        
        # URL do Google News RSS
        url = f'https://news.google.com/rss/search?q={query}&hl=pt-BR&gl=BR&ceid=BR:pt-419'
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            itens = soup.find_all('item')
            
            noticias = []
            
            for item in itens[:30]:  # Limita a 30 notícias mais recentes
                try:
                    titulo = item.find('title').text if item.find('title') else "Título não disponível"
                    link = item.find('link').text if item.find('link') else None
                    descricao = item.find('description').text if item.find('description') else "Descrição não disponível"
                    
                    # Limpa descrição HTML
                    descricao_limpa = limpar_descricao_html(descricao)
                    
                    # Extrai data de publicação
                    data, data_hora = extrair_data_publicacao(item)
                    
                    # Extrai fonte
                    fonte = extrair_fonte_noticia(link) if link else 'Desconhecida'
                    
                    # Gera ID único baseado no título e data
                    id_noticia = hash(f"{titulo}{data_hora}") & 0x7FFFFFFF
                    
                    noticia = {
                        'id': id_noticia,
                        'data': data,
                        'data_hora': data_hora,
                        'titulo': titulo.strip(),
                        'descricao': descricao_limpa,
                        'fonte': fonte,
                        'url': link,
                        'tipo': 'noticia_mercado'
                    }
                    
                    noticias.append(noticia)
                
                except Exception as e:
                    print(f"⚠️ Erro ao processar item de notícia: {e}")
                    continue
            
            return noticias
        else:
            print(f"⚠️ Erro ao buscar notícias: Status {response.status_code}")
            return []
    
    except Exception as e:
        print(f"❌ Erro ao buscar noticiário empresarial: {e}")
        return []


def salvar_noticiario_json(ticker: str, noticias: list) -> Path | None:
    """
    Salva o noticiário em formato JSON na pasta do ticker.
    Acumula com notícias existentes, evitando duplicatas por ID.
    """
    try:
        pasta_ticker = obter_pasta_ticker(ticker)
        arquivo_json = pasta_ticker / 'noticiario.json'
        
        # Carrega notícias existentes se o arquivo já existir
        noticias_existentes = []
        if arquivo_json.exists():
            with open(arquivo_json, 'r', encoding='utf-8') as f:
                dados_existentes = json.load(f)
                noticias_existentes = dados_existentes.get('noticias', [])
        
        # Cria dicionário de notícias existentes por ID
        noticias_dict = {}
        for noticia in noticias_existentes:
            if noticia.get('id'):
                noticias_dict[noticia['id']] = noticia
        
        # Adiciona novas notícias (substitui se ID já existir)
        for noticia in noticias:
            if noticia.get('id'):
                noticias_dict[noticia['id']] = noticia
        
        # Converte de volta para lista e ordena por data
        noticias_finais = list(noticias_dict.values())
        noticias_finais.sort(key=lambda x: x['data_hora'], reverse=True)
        
        # Limita a 100 notícias mais recentes para não crescer indefinidamente
        noticias_finais = noticias_finais[:100]
        
        # Busca informações da empresa
        nome_empresa = buscar_nome_empresa_ticker(ticker)
        ticker_limpo = extrair_ticker_base(ticker)
        
        # Monta estrutura final
        dados_finais = {
            'empresa': {
                'ticker': ticker_limpo,
                'nome': nome_empresa
            },
            'ultima_atualizacao': datetime.now().isoformat(),
            'total_noticias': len(noticias_finais),
            'fonte': 'Google News',
            'noticias': noticias_finais
        }
        
        # Salva no arquivo JSON
        with open(arquivo_json, 'w', encoding='utf-8') as f:
            json.dump(dados_finais, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ {len(noticias_finais)} notícias | {arquivo_json}")
        return arquivo_json
    
    except Exception as e:
        print(f"  ❌ Erro ao salvar: {e}")
        return None


# ============================================================================
# PROCESSAMENTO EM LOTE
# ============================================================================

def processar_ticker(ticker: str) -> bool:
    """
    Processa um único ticker: busca e salva notícias.
    
    Returns:
        True se sucesso, False se erro
    """
    try:
        ticker_limpo = ticker.upper().strip()
        nome_empresa = buscar_nome_empresa_ticker(ticker_limpo)
        
        print(f"\n📰 {ticker_limpo} - {nome_empresa}")
        
        noticias = buscar_noticiario_empresarial(ticker_limpo)
        
        if noticias:
            arquivo_salvo = salvar_noticiario_json(ticker_limpo, noticias)
            return arquivo_salvo is not None
        else:
            print(f"  ⚠️ Nenhuma notícia encontrada")
            return False
            
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False


def processar_lote(df_sel: pd.DataFrame):
    """
    Processa um lote de empresas selecionadas.
    """
    print(f"\n{'='*70}")
    print(f"🚀 Processando {len(df_sel)} empresas...")
    print(f"{'='*70}")

    ok_count = 0
    err_count = 0

    for _, row in df_sel.iterrows():
        ticker = str(row["ticker"]).strip().upper()
        
        # Se ticker tem múltiplos valores (ex: PETR3;PETR4), pega o primeiro
        if ';' in ticker:
            ticker = ticker.split(';')[0].strip()
        
        sucesso = processar_ticker(ticker)
        
        if sucesso:
            ok_count += 1
        else:
            err_count += 1

    print(f"\n{'='*70}")
    print(f"✅ Finalizado: OK={ok_count} | ERRO={err_count}")
    print(f"{'='*70}\n")


# ============================================================================
# MAIN COM ARGPARSE
# ============================================================================

def main():
    """
    Função principal com suporte a argumentos CLI.
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
        default="10", 
        help="Quantidade de empresas (modo quantidade)"
    )
    parser.add_argument(
        "--ticker", 
        default="", 
        help="Ticker específico (modo ticker): ex: PETR4"
    )
    parser.add_argument(
        "--lista", 
        default="", 
        help="Lista de tickers (modo lista): ex: PETR4,VALE3,ITUB4"
    )
    parser.add_argument(
        "--faixa", 
        default="1-50", 
        help="Faixa de linhas (modo faixa): ex: 1-50, 51-150"
    )
    args = parser.parse_args()

    # Carregar mapeamento
    try:
        df = load_mapeamento_consolidado()
        df = df[df["ticker"].notna()].reset_index(drop=True)
    except Exception as e:
        print(f"❌ Erro ao carregar mapeamento: {e}")
        sys.exit(1)

    # Seleção baseada no modo
    if args.modo == "quantidade":
        limite = int(args.quantidade)
        df_sel = df.head(limite)

    elif args.modo == "ticker":
        ticker_upper = args.ticker.upper()
        # Buscar ticker em qualquer posição da string de tickers
        df_sel = df[df["ticker"].str.upper().str.contains(
            ticker_upper, 
            case=False, 
            na=False, 
            regex=False
        )]
        
        if df_sel.empty:
            print(f"❌ Ticker '{args.ticker}' não encontrado no mapeamento.")
            sys.exit(1)

    elif args.modo == "lista":
        tickers = [t.strip().upper() for t in args.lista.split(",") if t.strip()]
        
        if not tickers:
            print("❌ Lista de tickers vazia.")
            sys.exit(1)
        
        # Buscar cada ticker em qualquer posição
        mask = df["ticker"].str.upper().apply(
            lambda x: any(t in x for t in tickers) if pd.notna(x) else False
        )
        df_sel = df[mask]
        
        if df_sel.empty:
            print(f"❌ Nenhum ticker da lista encontrado: {', '.join(tickers)}")
            sys.exit(1)

    elif args.modo == "faixa":
        try:
            inicio, fim = map(int, args.faixa.split("-"))
            df_sel = df.iloc[inicio - 1: fim]
            
            if df_sel.empty:
                print(f"❌ Faixa {args.faixa} está fora do range disponível (1-{len(df)}).")
                sys.exit(1)
        except ValueError:
            print(f"❌ Formato de faixa inválido: '{args.faixa}'. Use formato: inicio-fim (ex: 1-50)")
            sys.exit(1)

    else:
        df_sel = df.head(10)

    # Exibir informações do job
    print(f"\n{'='*70}")
    print(f">>> JOB: CAPTURAR NOTICIÁRIO EMPRESARIAL <<<")
    print(f"{'='*70}")
    print(f"Modo: {args.modo}")
    print(f"Empresas selecionadas: {len(df_sel)}")
    print(f"Fonte: Google News RSS")
    print(f"Limite por empresa: 30 notícias novas (max 100 acumuladas)")
    print(f"Saída: balancos/<TICKER>/noticiario.json")
    print(f"{'='*70}")

    # Processar
    processar_lote(df_sel)


if __name__ == "__main__":
    main()
