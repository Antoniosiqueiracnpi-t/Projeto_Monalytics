"""
CAPTURA DE LOGOS - INVESTIDOR10

FONTE DE DADOS:
- Site: https://investidor10.com.br/acoes/{ticker}/
- Formato: PNG ou JPG
- Saída: balancos/<TICKER>/logo.png

ESTRATÉGIAS DE CAPTURA:
1. Imagens em /storage/companies/ (padrão oficial do Investidor10)
2. Imagens próximas ao ticker no HTML
3. Imagens com 'company/ticker' na classe
4. Imagens em /uploads/companies/, /assets/companies/

IMPORTANTE:
- Logos são compartilhados entre tickers (ITUB3 e ITUB4 = mesmo logo)
- Usa pasta existente (reutiliza get_pasta_balanco)
- Formato final: logo.png
"""

import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path
from datetime import datetime
import argparse
import time
from PIL import Image
from io import BytesIO


# ============================================================================
# UTILITÁRIOS MULTI-TICKER
# ============================================================================

def load_mapeamento_consolidado():
    """Carrega CSV de mapeamento."""
    import pandas as pd
    
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


def extrair_ticker_inteligente(ticker_str: str) -> str:
    """Prioriza ON (3) > PN (4) > outros."""
    ticker_str = ticker_str.strip().upper()
    
    if ';' not in ticker_str:
        return ticker_str
    
    tickers = [t.strip() for t in ticker_str.split(';') if t.strip()]
    
    if not tickers:
        return ticker_str
    
    tickers_3 = [t for t in tickers if t.endswith('3')]
    if tickers_3:
        return tickers_3[0]
    
    tickers_4 = [t for t in tickers if t.endswith('4')]
    if tickers_4:
        return tickers_4[0]
    
    return tickers[0]


def get_pasta_balanco(ticker: str) -> Path:
    """
    Retorna Path da pasta de balanços.
    Verifica se já existe pasta com ticker base antes de criar nova.
    """
    ticker_clean = extrair_ticker_inteligente(ticker)
    base_dir = Path("balancos")
    base_dir.mkdir(exist_ok=True)
    
    # Extrair ticker base (ITUB4 → ITUB)
    ticker_base = ticker_clean.rstrip("0123456789")
    
    # Verificar se já existe alguma pasta com esse ticker base
    pastas_existentes = list(base_dir.glob(f"{ticker_base}*"))
    
    if pastas_existentes:
        return pastas_existentes[0]
    
    return base_dir / ticker_clean


# ============================================================================
# CAPTURADOR DE LOGOS
# ============================================================================

class CapturadorLogos:
    """
    Captura logos de empresas do site Investidor10.
    
    ESTRATÉGIAS (em ordem de prioridade):
    ------------------------------------
    1. Imagens em /storage/companies/ - Padrão oficial do Investidor10
    2. Imagens próximas ao ticker - Contexto do header/topo
    3. Imagens com 'company/ticker' na classe - Semântica HTML
    4. Imagens em /uploads/companies/ ou /assets/companies/ - Padrões alternativos
    
    FORMATO DE SAÍDA:
    ----------------
    - Arquivo: balancos/<TICKER>/logo.png
    - Formato: PNG (convertido se necessário)
    - Compartilhado entre tickers da mesma empresa
    """
    
    def __init__(self):
        self.pasta_balancos = Path("balancos")
        self.pasta_balancos.mkdir(exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        self.timeout = 30
        self.delay = 1  # Delay entre requests (respeitar servidor)
    
    # ----------------------- DOWNLOAD E PARSING -----------------------
    
    def _get_page(self, ticker: str) -> BeautifulSoup | None:
        """Baixa página do Investidor10 e retorna BeautifulSoup."""
        ticker_lower = ticker.lower()
        url = f"https://investidor10.com.br/acoes/{ticker_lower}/"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"  [ERRO] Falha ao acessar {url}: {e}")
            return None
    
    def _find_logo_url(self, soup: BeautifulSoup, ticker: str) -> str | None:
        """
        Tenta encontrar URL do logo usando múltiplas estratégias.
        Retorna primeira URL válida encontrada.
        """
        # Estratégia 1: Imagem em /storage/companies/ (LOGO DA EMPRESA)
        all_images = soup.find_all('img')
        for img in all_images:
            src = img.get('src', '') or img.get('data-src', '')
            if '/storage/companies/' in src:
                if self._is_valid_logo_url(src):
                    print(f"  ✅ Logo encontrado: /storage/companies/")
                    return src
        
        # Estratégia 2: Imagens próximas ao ticker (header/topo)
        # Procurar elementos que contenham o ticker
        ticker_elements = soup.find_all(string=re.compile(ticker, re.I))
        for elem in ticker_elements[:5]:  # Primeiros 5 ocorrências
            parent = elem.parent
            # Procurar imgs no mesmo parent ou próximas
            imgs_nearby = parent.find_all('img')
            for img in imgs_nearby:
                src = img.get('src', '') or img.get('data-src', '')
                # Evitar logo do site Investidor10
                if src and 'investidor10' in src.lower() and 'logo' in src.lower():
                    continue
                if src and self._is_valid_logo_url(src):
                    print(f"  ✅ Logo encontrado: próximo ao ticker")
                    return src
        
        # Estratégia 3: Imagem com 'company' ou 'ticker' na classe
        company_imgs = soup.find_all('img', class_=re.compile(r'(company|ticker|symbol|empresa)', re.I))
        for img in company_imgs:
            src = img.get('src', '') or img.get('data-src', '')
            # Evitar logo do site
            if src and 'investidor10' in src.lower() and 'logo' in src.lower():
                continue
            if src and self._is_valid_logo_url(src):
                print(f"  ✅ Logo encontrado: class com 'company/ticker'")
                return src
        
        # Estratégia 4: Imagens em /uploads/, /assets/companies/
        for img in all_images:
            src = img.get('src', '') or img.get('data-src', '')
            if any(x in src.lower() for x in ['/uploads/companies/', '/assets/companies/', '/images/companies/']):
                if self._is_valid_logo_url(src):
                    print(f"  ✅ Logo encontrado: padrão de upload")
                    return src
        
        # Se nenhuma estratégia funcionou
        print(f"  ⚠️  Nenhuma estratégia encontrou o logo")
        return None
    
    def _is_valid_logo_url(self, url: str) -> bool:
        """Valida se URL parece ser de uma imagem."""
        if not url:
            return False
        
        # Aceitar URLs relativas ou absolutas
        if url.startswith('//'):
            url = 'https:' + url
        elif url.startswith('/'):
            url = 'https://investidor10.com.br' + url
        
        # Padrões específicos de logo de empresa (sempre válidos)
        logo_patterns = ['/storage/companies/', '/uploads/companies/', '/assets/companies/', '/images/companies/']
        if any(pattern in url.lower() for pattern in logo_patterns):
            return True
        
        # Verificar se é uma URL de imagem por extensão
        img_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg']
        url_lower = url.lower()
        
        return any(ext in url_lower for ext in img_extensions)
    
    def _download_image(self, url: str) -> bytes | None:
        """Baixa imagem da URL."""
        # Normalizar URL
        if url.startswith('//'):
            url = 'https:' + url
        elif url.startswith('/'):
            url = 'https://investidor10.com.br' + url
        
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            return response.content
        except Exception as e:
            print(f"  [ERRO] Falha ao baixar imagem: {e}")
            return None
    
    def _convert_to_png(self, image_bytes: bytes) -> bytes | None:
        """Converte imagem para PNG se necessário."""
        try:
            img = Image.open(BytesIO(image_bytes))
            
            # Se já for PNG, retornar original
            if img.format == 'PNG':
                return image_bytes
            
            # Converter para PNG
            output = BytesIO()
            
            # Converter RGBA se necessário
            if img.mode in ('RGBA', 'LA', 'P'):
                # Manter transparência
                img.save(output, format='PNG')
            else:
                # Converter para RGB primeiro
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(output, format='PNG')
            
            return output.getvalue()
        except Exception as e:
            print(f"  [AVISO] Erro ao converter para PNG: {e}")
            # Retornar original em caso de erro
            return image_bytes
    
    # ----------------------- PROCESSAMENTO -----------------------
    
    def processar_empresa(self, ticker: str, nome_empresa: str):
        """
        Captura logo de uma empresa do Investidor10.
        """
        print(f"\n{'='*50}")
        print(f"🖼️  {ticker} - {nome_empresa}")
        
        pasta = get_pasta_balanco(ticker)
        pasta.mkdir(exist_ok=True)
        
        ticker_display = extrair_ticker_inteligente(ticker)
        if pasta.name != ticker_display:
            print(f"  ℹ️  Usando pasta existente: {pasta.name}")
        
        # Verificar se logo já existe
        logo_path = pasta / "logo.png"
        if logo_path.exists():
            print(f"  ℹ️  Logo já existe: {logo_path.name} ({logo_path.stat().st_size / 1024:.1f} KB)")
            print(f"  ⏭️  Pulando download")
            return
        
        # Baixar página
        print(f"  📥 Acessando Investidor10...")
        soup = self._get_page(ticker_display)
        
        if soup is None:
            print(f"  ❌ Falha ao acessar página")
            return
        
        # Buscar URL do logo
        print(f"  🔍 Procurando logo...")
        logo_url = self._find_logo_url(soup, ticker_display)
        
        if logo_url is None:
            print(f"  ❌ Logo não encontrado na página")
            return
        
        # Baixar imagem
        print(f"  📥 Baixando logo...")
        print(f"     URL: {logo_url[:80]}...")
        image_bytes = self._download_image(logo_url)
        
        if image_bytes is None:
            print(f"  ❌ Falha ao baixar imagem")
            return
        
        # Converter para PNG se necessário
        print(f"  🔄 Convertendo para PNG...")
        png_bytes = self._convert_to_png(image_bytes)
        
        if png_bytes is None:
            print(f"  ❌ Falha ao converter imagem")
            return
        
        # Salvar
        logo_path.write_bytes(png_bytes)
        tamanho_kb = len(png_bytes) / 1024
        
        print(f"  ✅ Logo salvo: logo.png ({tamanho_kb:.1f} KB)")
        
        # Delay para não sobrecarregar servidor
        time.sleep(self.delay)
    
    def processar_lote(self, df_sel):
        """Processa lote de empresas."""
        import pandas as pd
        
        print(f"\n🚀 Processando {len(df_sel)} empresas...\n")
        
        ok_count = 0
        skip_count = 0
        err_count = 0
        
        for _, row in df_sel.iterrows():
            try:
                ticker_str = str(row["ticker"]).strip().upper()
                ticker_cvm = extrair_ticker_inteligente(ticker_str)
                nome_empresa = str(row.get("nome_empresa", row.get("denominacao_social", ""))).strip()
                
                # Verificar se já existe
                pasta = get_pasta_balanco(ticker_cvm)
                logo_path = pasta / "logo.png"
                
                if logo_path.exists():
                    skip_count += 1
                else:
                    self.processar_empresa(ticker_cvm, nome_empresa)
                    ok_count += 1
                    
            except Exception as e:
                err_count += 1
                ticker_str = str(row.get("ticker", "UNKNOWN")).strip().upper()
                ticker_display = extrair_ticker_inteligente(ticker_str)
                print(f"❌ {ticker_display}: erro ({type(e).__name__}: {e})")
        
        print(f"\n{'='*70}")
        print(f"Finalizado: OK={ok_count} | SKIP={skip_count} | ERRO={err_count}")
        print(f"{'='*70}\n")


# ============================================================================
# MAIN
# ============================================================================

def main():
    import pandas as pd
    
    parser = argparse.ArgumentParser(
        description="Captura logos de empresas do Investidor10"
    )
    parser.add_argument(
        "--modo",
        choices=["quantidade", "ticker", "lista", "faixa"],
        default="quantidade",
        help="Modo de seleção",
    )
    parser.add_argument("--quantidade", default="10", help="Quantidade de empresas")
    parser.add_argument("--ticker", default="", help="Ticker específico")
    parser.add_argument("--lista", default="", help="Lista de tickers")
    parser.add_argument("--faixa", default="1-50", help="Faixa de linhas")
    args = parser.parse_args()
    
    # Carregar mapeamento
    df = load_mapeamento_consolidado()
    df = df[df["cnpj"].notna()].reset_index(drop=True)
    
    # Seleção
    if args.modo == "quantidade":
        df_sel = df.head(int(args.quantidade))
    elif args.modo == "ticker":
        df_sel = df[df["ticker"].str.upper().str.contains(
            args.ticker.upper(), case=False, na=False, regex=False
        )]
    elif args.modo == "lista":
        tickers = [t.strip().upper() for t in args.lista.split(",") if t.strip()]
        mask = df["ticker"].str.upper().apply(
            lambda x: any(t in x for t in tickers) if pd.notna(x) else False
        )
        df_sel = df[mask]
    elif args.modo == "faixa":
        inicio, fim = map(int, args.faixa.split("-"))
        df_sel = df.iloc[inicio - 1: fim]
    else:
        df_sel = df.head(10)
    
    # Exibir info
    print(f"\n{'='*70}")
    print(f">>> CAPTURA DE LOGOS - INVESTIDOR10 <<<")
    print(f"{'='*70}")
    print(f"Modo: {args.modo}")
    print(f"Empresas: {len(df_sel)}")
    print(f"Fonte: https://investidor10.com.br/")
    print(f"Formato: PNG")
    print(f"Saída: balancos/<TICKER>/logo.png")
    print(f"{'='*70}")
    print(f"ℹ️  OBSERVAÇÕES:")
    print(f"   - Logos compartilhados entre tickers (ITUB3/ITUB4 = mesmo)")
    print(f"   - Logos existentes serão pulados")
    print(f"   - Delay de 1s entre requests (respeitar servidor)")
    print(f"{'='*70}\n")
    
    # Processar
    capturador = CapturadorLogos()
    capturador.processar_lote(df_sel)


if __name__ == "__main__":
    main()
