"""
TESTE: Verificar estrutura da API B3 e se retorna dividendos futuros

Este script faz uma análise detalhada do retorno da API B3 para:
1. Ver todos os campos disponíveis
2. Verificar se há dividendos com data_ex > hoje (futuros)
3. Identificar o campo correto de data de pagamento

Rodar: python src/teste_api_b3_estrutura.py
"""

import json
import base64
import requests
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass


HOJE = datetime.now().strftime('%Y-%m-%d')
print(f"Data de hoje: {HOJE}")
print("="*80)


def parse_data_b3(data_str: str) -> str:
    """Converte DD/MM/YYYY para YYYY-MM-DD."""
    if not data_str:
        return None
    try:
        if '/' in data_str:
            partes = data_str.split('/')
            if len(partes) == 3:
                dia, mes, ano = partes
                return f"{ano}-{mes}-{dia}"
        elif '-' in data_str and len(data_str) >= 10:
            return data_str[:10]
        return None
    except:
        return None


def testar_empresa(trading_name: str, ticker: str):
    """Testa uma empresa específica."""
    print(f"\n{'='*80}")
    print(f"TESTANDO: {ticker} ({trading_name})")
    print(f"{'='*80}")
    
    params = {
        "language": "pt-br",
        "pageNumber": 1,
        "pageSize": 20,  # Apenas 20 para análise
        "tradingName": trading_name
    }
    
    params_b64 = base64.b64encode(json.dumps(params).encode()).decode()
    url = f"https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetListedCashDividends/{params_b64}"
    
    try:
        response = requests.get(url, timeout=15, verify=False)
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Erro: {response.text[:500]}")
            return
        
        data = response.json()
        results = data.get('results', [])
        print(f"Total de resultados: {len(results)}")
        
        if not results:
            print("Nenhum resultado encontrado!")
            return
        
        # Mostrar estrutura completa do primeiro resultado
        print(f"\n--- ESTRUTURA COMPLETA (1º registro) ---")
        for key, value in results[0].items():
            print(f"  {key}: {value}")
        
        # Analisar todos os resultados
        print(f"\n--- ANÁLISE DOS {len(results)} RESULTADOS ---")
        
        futuros = []
        passados = []
        
        for i, d in enumerate(results):
            # Extrair data ex
            data_ex_raw = d.get('lastDatePriorEx', '')
            data_ex = parse_data_b3(data_ex_raw)
            
            # Verificar se é futuro
            if data_ex and data_ex >= HOJE:
                futuros.append(d)
            else:
                passados.append(d)
        
        print(f"\n✅ Dividendos com data_ex >= hoje ({HOJE}): {len(futuros)}")
        print(f"📅 Dividendos com data_ex < hoje: {len(passados)}")
        
        # Mostrar os futuros se houver
        if futuros:
            print(f"\n🔮 DIVIDENDOS FUTUROS ENCONTRADOS:")
            for d in futuros[:10]:
                data_ex = parse_data_b3(d.get('lastDatePriorEx', ''))
                valor = d.get('valueCash', '0').replace(',', '.')
                tipo = d.get('corporateAction', '')
                tipo_acao = d.get('typeStock', '')
                
                # Procurar campo de data de pagamento
                data_pag = (
                    d.get('paymentDate') or 
                    d.get('datePayment') or 
                    d.get('payDate') or
                    d.get('dateApproval') or
                    'N/A'
                )
                
                print(f"  {data_ex} | {tipo_acao} | R${valor} | {tipo} | Pag: {data_pag}")
        else:
            print(f"\n⚠️ NENHUM DIVIDENDO FUTURO encontrado para {ticker}")
            print("Mostrando os 5 mais recentes:")
            for d in results[:5]:
                data_ex = parse_data_b3(d.get('lastDatePriorEx', ''))
                valor = d.get('valueCash', '0').replace(',', '.')
                tipo = d.get('corporateAction', '')
                print(f"  {data_ex} | R${valor} | {tipo}")
        
        return results
        
    except Exception as e:
        print(f"Erro: {e}")
        return None


def main():
    # Empresas para testar (baseado no que o Investidor10 mostra para fevereiro 2026)
    empresas = [
        ("BANCO BRADESCO", "BBDC4"),
        ("BANCO ITAU", "ITUB4"),
        ("ISA ENERGIA", "ISAE4"),  # ISA CTEEP
        ("JHSF", "JHSF3"),
        ("CAMIL", "CAML3"),
        ("M DIAS BRANCO", "MDIA3"),
        ("BANESTES", "BEES4"),
        ("PETROBRAS", "PETR4"),
        ("VALE", "VALE3"),
    ]
    
    todos_resultados = {}
    
    for trading_name, ticker in empresas:
        results = testar_empresa(trading_name, ticker)
        if results:
            todos_resultados[ticker] = results
    
    # Resumo final
    print("\n" + "="*80)
    print("RESUMO FINAL")
    print("="*80)
    
    total_futuros = 0
    for ticker, results in todos_resultados.items():
        futuros_ticker = 0
        for d in results:
            data_ex = parse_data_b3(d.get('lastDatePriorEx', ''))
            if data_ex and data_ex >= HOJE:
                futuros_ticker += 1
        total_futuros += futuros_ticker
        print(f"{ticker}: {futuros_ticker} futuros de {len(results)} total")
    
    print(f"\nTOTAL DE DIVIDENDOS FUTUROS: {total_futuros}")
    
    if total_futuros == 0:
        print("\n⚠️ A API B3 parece NÃO retornar dividendos com data_ex futura")
        print("   Provavelmente ela só retorna após a data COM passar.")
        print("   O Investidor10 pode usar outra fonte de dados.")


if __name__ == "__main__":
    main()
