"""
GERADOR DE MAPEAMENTO TICKER → TRADING NAME (API B3)

Este script consulta a API B3 para cada ticker e gera um arquivo CSV
com o tradingName correto para busca de dividendos.

RODAR UMA VEZ para gerar o mapeamento, depois usar nos scripts de dividendos.

USO:
python gerar_mapeamento_b3_tradingname.py

SAÍDA:
- mapeamento_tradingname_b3.csv (ticker;trading_name;issuing_company)
"""

import requests
import base64
import json
import pandas as pd
import time
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass


def extrair_ticker_principal(ticker_raw: str) -> str:
    """Extrai ticker limpo."""
    if not ticker_raw:
        return ""
    ticker = str(ticker_raw).strip().strip('"').strip("'")
    ticker = ticker.replace('.SA', '').replace('.sa', '')
    if ';' in ticker:
        ticker = ticker.split(';')[0]
    return ticker.strip().upper()


def extrair_codigo_negociacao(ticker: str) -> str:
    """PETR4 → PETR, VALE3 → VALE, TAEE11 → TAEE"""
    ticker_clean = extrair_ticker_principal(ticker)
    return ''.join([c for c in ticker_clean if not c.isdigit()])


def buscar_trading_name(ticker: str, max_retries: int = 3) -> dict:
    """
    Busca o tradingName correto na API B3.
    
    Returns:
        dict com 'ticker', 'codigo', 'trading_name', 'issuing_company', 'status'
    """
    ticker_clean = extrair_ticker_principal(ticker)
    codigo = extrair_codigo_negociacao(ticker)
    
    resultado = {
        'ticker': ticker_clean,
        'codigo': codigo,
        'trading_name': '',
        'issuing_company': '',
        'status': 'erro'
    }
    
    if not codigo:
        resultado['status'] = 'codigo_vazio'
        return resultado
    
    for attempt in range(max_retries):
        try:
            params = {
                "language": "pt-br",
                "pageNumber": 1,
                "pageSize": 100,
                "company": codigo
            }
            
            params_b64 = base64.b64encode(json.dumps(params).encode()).decode()
            url = f"https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetInitialCompanies/{params_b64}"
            
            response = requests.get(url, timeout=15, verify=False)
            
            # Retry em caso de erro 5xx
            if response.status_code >= 500:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                resultado['status'] = f'erro_{response.status_code}'
                return resultado
            
            response.raise_for_status()
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                resultado['status'] = 'nao_encontrado'
                return resultado
            
            # Buscar empresa com issuingCompany == codigo
            empresa_correta = None
            for emp in results:
                if emp.get('issuingCompany', '').upper() == codigo.upper():
                    empresa_correta = emp
                    break
            
            if empresa_correta:
                trading_name = empresa_correta.get('tradingName', '')
                # Limpar caracteres especiais
                trading_name = trading_name.replace('/', '').replace('.', '')
                
                resultado['trading_name'] = trading_name
                resultado['issuing_company'] = empresa_correta.get('issuingCompany', '')
                resultado['status'] = 'ok'
            else:
                # Se não encontrou exato, marcar para revisão manual
                resultado['status'] = 'nao_encontrado_exato'
                # Guardar as opções disponíveis para debug
                opcoes = [f"{e.get('issuingCompany')}:{e.get('tradingName')}" for e in results[:5]]
                resultado['opcoes'] = '|'.join(opcoes)
            
            return resultado
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            resultado['status'] = 'timeout'
            return resultado
        except Exception as e:
            resultado['status'] = f'erro:{type(e).__name__}'
            return resultado
    
    return resultado


def main():
    print("=" * 70)
    print("GERADOR DE MAPEAMENTO TICKER → TRADING NAME (API B3)")
    print("=" * 70)
    
    # Carregar mapeamento original
    arquivo_entrada = "mapeamento_b3_consolidado.csv"
    
    try:
        df_input = pd.read_csv(arquivo_entrada, sep=';', encoding='utf-8-sig')
        print(f"✓ Carregado: {arquivo_entrada} ({len(df_input)} linhas)")
    except Exception as e:
        print(f"❌ Erro ao carregar {arquivo_entrada}: {e}")
        return
    
    # Extrair tickers únicos
    tickers_unicos = []
    for ticker_raw in df_input['ticker'].unique():
        ticker_clean = extrair_ticker_principal(ticker_raw)
        if ticker_clean and ticker_clean not in tickers_unicos:
            tickers_unicos.append(ticker_clean)
    
    print(f"✓ Tickers únicos: {len(tickers_unicos)}")
    print()
    
    # Buscar trading name para cada ticker
    resultados = []
    ok_count = 0
    erro_count = 0
    
    for i, ticker in enumerate(tickers_unicos, 1):
        print(f"[{i:3}/{len(tickers_unicos)}] {ticker:10} ", end='', flush=True)
        
        resultado = buscar_trading_name(ticker)
        resultados.append(resultado)
        
        if resultado['status'] == 'ok':
            print(f"✓ {resultado['trading_name']}")
            ok_count += 1
        else:
            print(f"✗ {resultado['status']}")
            erro_count += 1
        
        # Pequena pausa para não sobrecarregar a API
        time.sleep(0.3)
    
    # Criar DataFrame de saída
    df_output = pd.DataFrame(resultados)
    
    # Salvar CSV
    arquivo_saida = "mapeamento_tradingname_b3.csv"
    df_output.to_csv(arquivo_saida, sep=';', index=False, encoding='utf-8-sig')
    
    print()
    print("=" * 70)
    print("RESUMO")
    print("=" * 70)
    print(f"✅ Sucesso: {ok_count}")
    print(f"❌ Erro: {erro_count}")
    print(f"📁 Salvo: {arquivo_saida}")
    
    # Mostrar erros para revisão
    erros = df_output[df_output['status'] != 'ok']
    if not erros.empty:
        print()
        print("⚠️ Tickers que precisam de revisão:")
        for _, row in erros.iterrows():
            print(f"   {row['ticker']:10} → {row['status']}")


if __name__ == "__main__":
    main()
