- name: Diagnóstico API B3
  run: |
    python3 << 'EOF'
    import requests
    import base64
    import json
    import warnings
    warnings.filterwarnings('ignore')

    def testar_b3(ticker):
        codigo = ''.join([c for c in ticker.upper() if not c.isdigit()])
        
        # Etapa 1: Buscar empresa
        params = {"language": "pt-br", "pageNumber": 1, "pageSize": 20, "company": codigo}
        params_b64 = base64.b64encode(json.dumps(params).encode()).decode()
        url = f"https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetInitialCompanies/{params_b64}"
        
        r1 = requests.get(url, timeout=15, verify=False)
        print(f"\n{'='*60}")
        print(f"TICKER: {ticker} (código: {codigo})")
        print(f"{'='*60}")
        print(f"Etapa 1 - Status: {r1.status_code}")
        
        if r1.status_code != 200:
            print(f"Resposta: {r1.text[:500]}")
            return
        
        data1 = r1.json()
        results = data1.get('results', [])
        print(f"Empresas encontradas: {len(results)}")
        
        if not results:
            return
        
        # Mostrar primeira empresa
        empresa = results[0]
        trading_name = empresa.get('tradingName', '').replace('/', '').replace('.', '')
        print(f"Trading Name: {trading_name}")
        print(f"Keys da empresa: {list(empresa.keys())}")
        
        # Etapa 2: Buscar dividendos
        params = {"language": "pt-br", "pageNumber": 1, "pageSize": 5, "tradingName": trading_name}
        params_b64 = base64.b64encode(json.dumps(params).encode()).decode()
        url = f"https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetListedCashDividends/{params_b64}"
        
        r2 = requests.get(url, timeout=15, verify=False)
        print(f"\nEtapa 2 - Status: {r2.status_code}")
        
        if r2.status_code != 200:
            print(f"Resposta: {r2.text[:500]}")
            return
        
        data2 = r2.json()
        divs = data2.get('results', [])
        print(f"Dividendos encontrados: {len(divs)}")
        
        if divs:
            print(f"\nPRIMEIRO DIVIDENDO (estrutura completa):")
            print(json.dumps(divs[0], indent=2, ensure_ascii=False))

    # Testar alguns tickers
    for ticker in ['VALE3', 'PETR4', 'ITUB4']:
        testar_b3(ticker)
    EOF
