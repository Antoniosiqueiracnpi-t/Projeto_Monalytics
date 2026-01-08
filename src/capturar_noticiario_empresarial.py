import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import re
from urllib.parse import urlparse, parse_qs

def obter_pasta_ticker(ticker):
    """
    Determina a pasta correta para salvar os dados do ticker.
    """
    base_path = "balancos"
    ticker_base = re.sub(r'\d+$', '', ticker.upper())
    
    if os.path.exists(base_path):
        for pasta in os.listdir(base_path):
            if pasta.startswith(ticker_base):
                return os.path.join(base_path, pasta)
    
    pasta_ticker = os.path.join(base_path, ticker.upper())
    os.makedirs(pasta_ticker, exist_ok=True)
    return pasta_ticker

def buscar_nome_empresa_ticker(ticker):
    """
    Busca o nome da empresa associada ao ticker no mapeamento_b3_consolidado.csv.
    """
    try:
        if os.path.exists('mapeamento_b3_consolidado.csv'):
            import csv
            with open('mapeamento_b3_consolidado.csv', 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                ticker_limpo = ticker.upper().strip()
                
                for row in reader:
                    # Coluna ticker pode ter múltiplos tickers separados por ;
                    tickers_linha = row['ticker'].split(';')
                    for t in tickers_linha:
                        if t.strip().upper() == ticker_limpo:
                            return row['empresa'].strip()
        
        return ticker
    except Exception as e:
        print(f"Erro ao buscar nome da empresa: {e}")
        return ticker


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

def extrair_fonte_noticia(link):
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

def limpar_descricao_html(descricao):
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

def buscar_noticiario_empresarial(ticker):
    """
    Busca notícias do mercado sobre a empresa via Google News RSS.
    """
    try:
        ticker_clean = re.sub(r'\d+$', '', ticker.upper())
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
                    print(f"Erro ao processar item de notícia: {e}")
                    continue
            
            return noticias
        else:
            print(f"Erro ao buscar notícias: Status {response.status_code}")
            return []
    
    except Exception as e:
        print(f"Erro ao buscar noticiário empresarial: {e}")
        return []

def salvar_noticiario_json(ticker, noticias):
    """
    Salva o noticiário em formato JSON na pasta do ticker.
    Acumula com notícias existentes, evitando duplicatas por ID.
    """
    try:
        pasta_ticker = obter_pasta_ticker(ticker)
        arquivo_json = os.path.join(pasta_ticker, 'noticiario.json')
        
        # Carrega notícias existentes se o arquivo já existir
        noticias_existentes = []
        if os.path.exists(arquivo_json):
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
        ticker_limpo = re.sub(r'\d+$', '', ticker.upper())
        
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
        
        print(f"✅ {len(noticias_finais)} notícias salvas em: {arquivo_json}")
        return arquivo_json
    
    except Exception as e:
        print(f"❌ Erro ao salvar noticiário: {e}")
        return None

def exibir_noticiario_formatado(noticias, limite=5):
    """
    Exibe o noticiário em formato bonito e amigável.
    """
    if not noticias:
        print("Nenhuma notícia encontrada.")
        return
    
    noticias_exibir = noticias[:limite]
    
    print(f"\n{'=' * 100}")
    print(f"📰 NOTICIÁRIO EMPRESARIAL ({len(noticias)} notícias)")
    print(f"{'=' * 100}\n")
    
    for i, noticia in enumerate(noticias_exibir, 1):
        print(f"{'-' * 100}")
        print(f"{i}. \033[1m{noticia['titulo']}\033[0m")
        print(f"   📅 {noticia['data_hora']} | 📰 {noticia['fonte']}")
        print(f"   \033[94m{noticia['descricao']}\033[0m")
        if noticia.get('url'):
            print(f"   🔗 {noticia['url']}")
        print(f"{'-' * 100}\n")

def main():
    """
    Função principal para executar a captura de noticiário.
    """
    import sys
    
    if len(sys.argv) < 2:
        print("❌ Uso: python capturar_noticiario_empresarial.py TICKER")
        print("   Exemplo: python capturar_noticiario_empresarial.py ABEV3")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    
    print(f"🔍 Buscando noticiário empresarial de {ticker}...")
    print(f"⏳ Aguarde, isso pode levar alguns segundos...\n")
    
    noticias = buscar_noticiario_empresarial(ticker)
    
    if noticias:
        print(f"✅ {len(noticias)} notícias encontradas!")
        
        # Salva em JSON
        arquivo_salvo = salvar_noticiario_json(ticker, noticias)
        
        if arquivo_salvo:
            # Exibe preview
            exibir_noticiario_formatado(noticias, limite=5)
            print(f"\n💾 Arquivo salvo: {arquivo_salvo}")
        else:
            print("\n❌ Erro ao salvar arquivo JSON")
    else:
        print("❌ Nenhuma notícia encontrada ou erro na busca")

if __name__ == "__main__":
    main()
