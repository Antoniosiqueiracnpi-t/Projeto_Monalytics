"""
Script para preencher trimestres faltantes nos balanços financeiros usando dados da BRAPI
Autor: Antonio Siqueira - Monalisa Research
Data: Janeiro 2026
"""

import pandas as pd
import json
import urllib.request
from datetime import datetime
from pathlib import Path
import sys

# Token BRAPI
BRAPI_TOKEN = 'ukQzv8YM3L28VarpcbLDEV'

# Mapeamento de contas DRE (BRAPI -> Formato Padronizado)
MAPA_DRE = {
    # Receitas e Despesas Financeiras
    'financialIntermediationRevenue': ('3.01', 'Receitas de Intermediação Financeira'),
    'financialIntermediationExpenses': ('3.02', 'Despesas de Intermediação Financeira'),
    'totalRevenue': ('3.01', 'Receitas de Intermediação Financeira'),  # fallback
    'costOfRevenue': ('3.02', 'Despesas de Intermediação Financeira'),  # fallback
    
    # Resultados
    'grossProfit': ('3.03', 'Resultado Bruto de Intermediação Financeira'),
    'operatingExpenses': ('3.04', 'Outras Despesas e Receitas Operacionais'),
    'sellingGeneralAdministrative': ('3.04', 'Outras Despesas e Receitas Operacionais'),
    'incomeBeforeTax': ('3.05', 'Resultado antes dos Tributos sobre o Lucro'),
    'incomeTaxExpense': ('3.06', 'Imposto de Renda e Contribuição Social sobre o Lucro'),
    'netIncomeFromContinuingOps': ('3.07', 'Lucro ou Prejuízo das Operações Continuadas'),
    'discontinuedOperations': ('3.08', 'Resultado Líquido das Operações Descontinuadas'),
    'netIncome': ('3.09', 'Lucro ou Prejuízo antes das Participações e Contribuições Estatutárias'),
    'netIncomeApplicableToCommonShares': ('3.11', 'Lucro ou Prejuízo Líquido Consolidado do Período'),
    
    # LPA
    'basicEarningsPerShare': ('3.99', 'Lucro por Ação (Reais/Ação)'),
    'dilutedEarningsPerShare': ('3.99', 'Lucro por Ação (Reais/Ação)'),
}

# Mapeamento de contas BPA (Ativo)
MAPA_BPA = {
    'totalAssets': ('1', 'Ativo Total'),
    'cashAndCashEquivalents': ('1.01', 'Caixa e Equivalentes de Caixa'),
    'cash': ('1.01', 'Caixa e Equivalentes de Caixa'),
    'financialAssets': ('1.02', 'Ativos Financeiros'),
    'taxesToRecover': ('1.03', 'Tributos'),
    'otherAssets': ('1.04', 'Outros Ativos'),
    'investments': ('1.05', 'Investimentos'),
    'propertyPlantEquipment': ('1.06', 'Imobilizado'),
    'intangibleAssets': ('1.07', 'Intangível'),
}

# Mapeamento de contas BPP (Passivo)
MAPA_BPP = {
    'totalLiabilities': ('2', 'Passivo Total'),
    'financialLiabilitiesMeasuredAtFairValueThroughIncome': ('2.01', 'Passivos Financeiros ao Valor Justo através do Resultado'),
    'financialLiabilitiesAtAmortizedCost': ('2.02', 'Passivos Financeiros ao Custo Amortizado'),
    'provisions': ('2.03', 'Provisões'),
    'taxLiabilities': ('2.04', 'Passivos Fiscais'),
    'otherLiabilities': ('2.05', 'Outros Passivos'),
    'totalLiab': ('2.06', 'Passivos sobre Ativos Não Correntes a Venda'),
    'totalStockholderEquity': ('2.07', 'Patrimônio Líquido Consolidado'),
    'totalEquity': ('2.07', 'Patrimônio Líquido Consolidado'),
}


def buscar_dados_brapi(ticker, modulo='balanceSheetHistoryQuarterly'):
    """
    Busca dados de um ticker na BRAPI
    
    Args:
        ticker: Código da ação (ex: BBAS3)
        modulo: Módulo a buscar (balanceSheetHistoryQuarterly, incomeStatementHistoryQuarterly, etc)
    
    Returns:
        dict: Dados retornados pela API ou None em caso de erro
    """
    url = f'https://brapi.dev/api/quote/{ticker}?modules={modulo}'
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {BRAPI_TOKEN}')
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            return data
    except Exception as e:
        print(f"❌ Erro ao buscar dados de {ticker} ({modulo}): {e}")
        return None


def extrair_trimestre_ano(data_str):
    """
    Converte data no formato YYYY-MM-DD para formato YYYYTQ
    
    Args:
        data_str: Data no formato YYYY-MM-DD
    
    Returns:
        str: Data no formato YYYYTQ (ex: 2024T1)
    """
    try:
        data = datetime.strptime(data_str, '%Y-%m-%d')
        ano = data.year
        mes = data.month
        
        # Determinar trimestre baseado no mês
        if mes in [1, 2, 3]:
            trimestre = 1
        elif mes in [4, 5, 6]:
            trimestre = 2
        elif mes in [7, 8, 9]:
            trimestre = 3
        else:  # [10, 11, 12]
            trimestre = 4
        
        return f"{ano}T{trimestre}"
    except:
        return None


def identificar_trimestres_faltantes(df_atual, ano_inicio=2010):
    """
    Identifica quais trimestres estão faltando no DataFrame
    
    Args:
        df_atual: DataFrame atual com dados
        ano_inicio: Ano de início para verificar (padrão: 2010)
    
    Returns:
        list: Lista de trimestres faltantes no formato YYYYTQ
    """
    # Extrair colunas que são trimestres
    colunas_trim = [col for col in df_atual.columns if 'T' in str(col) and len(str(col)) == 6]
    trimestres_existentes = set(colunas_trim)
    
    # Gerar todos os trimestres possíveis desde ano_inicio até hoje
    ano_atual = datetime.now().year
    todos_trimestres = []
    
    for ano in range(ano_inicio, ano_atual + 1):
        for trim in range(1, 5):
            todos_trimestres.append(f"{ano}T{trim}")
    
    # Identificar faltantes
    trimestres_faltantes = [t for t in todos_trimestres if t not in trimestres_existentes]
    
    # Filtrar apenas os que são anteriores ao último trimestre disponível
    if trimestres_existentes:
        ultimo_existente = max(trimestres_existentes)
        trimestres_faltantes = [t for t in trimestres_faltantes if t < ultimo_existente]
    
    return sorted(trimestres_faltantes)


def mapear_campo_brapi(campo_brapi, tipo_balanco):
    """
    Mapeia um campo da BRAPI para o formato padronizado
    
    Args:
        campo_brapi: Nome do campo na BRAPI
        tipo_balanco: 'dre', 'bpa' ou 'bpp'
    
    Returns:
        tuple: (cd_conta, ds_conta) ou None se não encontrado
    """
    mapas = {
        'dre': MAPA_DRE,
        'bpa': MAPA_BPA,
        'bpp': MAPA_BPP
    }
    
    mapa = mapas.get(tipo_balanco)
    if not mapa:
        return None
    
    return mapa.get(campo_brapi)


def processar_dre(ticker, df_atual):
    """
    Processa DRE e preenche trimestres faltantes
    
    Args:
        ticker: Código da ação
        df_atual: DataFrame com dados atuais da DRE
    
    Returns:
        DataFrame: DataFrame atualizado ou None em caso de erro
    """
    print(f"\n📊 Processando DRE de {ticker}...")
    
    # Buscar dados da BRAPI
    dados = buscar_dados_brapi(ticker, 'incomeStatementHistoryQuarterly')
    if not dados or 'results' not in dados:
        print(f"❌ Não foi possível obter dados de {ticker}")
        return None
    
    result = dados['results'][0]
    if 'incomeStatementHistoryQuarterly' not in result:
        print(f"❌ Dados de DRE não disponíveis para {ticker}")
        return None
    
    dre_trimestral = result['incomeStatementHistoryQuarterly']
    print(f"✅ Obtidos {len(dre_trimestral)} trimestres da BRAPI")
    
    # Identificar trimestres faltantes
    trimestres_faltantes = identificar_trimestres_faltantes(df_atual)
    print(f"📋 Trimestres faltantes identificados: {len(trimestres_faltantes)}")
    
    if not trimestres_faltantes:
        print("✅ Não há trimestres faltantes!")
        return df_atual
    
    # Criar cópia do DataFrame para modificação
    df_novo = df_atual.copy()
    
    # Processar cada registro da BRAPI
    trimestres_preenchidos = []
    for registro in dre_trimestral:
        if 'endDate' not in registro:
            continue
        
        trimestre = extrair_trimestre_ano(registro['endDate'])
        if not trimestre or trimestre not in trimestres_faltantes:
            continue
        
        # Adicionar coluna se não existir
        if trimestre not in df_novo.columns:
            df_novo[trimestre] = None
        
        # Preencher valores para cada conta
        for campo_brapi, valor in registro.items():
            if campo_brapi == 'endDate' or valor is None:
                continue
            
            # Mapear campo
            mapeamento = mapear_campo_brapi(campo_brapi, 'dre')
            if not mapeamento:
                continue
            
            cd_conta, ds_conta = mapeamento
            
            # Encontrar a linha correspondente
            mask = df_novo['cd_conta'] == cd_conta
            if mask.any():
                df_novo.loc[mask, trimestre] = valor
            else:
                # Adicionar nova linha se não existir
                nova_linha = {'cd_conta': cd_conta, 'ds_conta': ds_conta, trimestre: valor}
                df_novo = pd.concat([df_novo, pd.DataFrame([nova_linha])], ignore_index=True)
        
        trimestres_preenchidos.append(trimestre)
    
    # Ordenar colunas (cd_conta, ds_conta, depois trimestres em ordem)
    colunas_trim = sorted([col for col in df_novo.columns if 'T' in str(col)])
    df_novo = df_novo[['cd_conta', 'ds_conta'] + colunas_trim]
    
    print(f"✅ Preenchidos {len(trimestres_preenchidos)} trimestres: {trimestres_preenchidos[:5]}...")
    
    return df_novo


def processar_bpa(ticker, df_atual):
    """
    Processa BPA (Balanço Patrimonial Ativo) e preenche trimestres faltantes
    
    Args:
        ticker: Código da ação
        df_atual: DataFrame com dados atuais do BPA
    
    Returns:
        DataFrame: DataFrame atualizado ou None em caso de erro
    """
    print(f"\n📊 Processando BPA de {ticker}...")
    
    # Buscar dados da BRAPI
    dados = buscar_dados_brapi(ticker, 'balanceSheetHistoryQuarterly')
    if not dados or 'results' not in dados:
        print(f"❌ Não foi possível obter dados de {ticker}")
        return None
    
    result = dados['results'][0]
    if 'balanceSheetHistoryQuarterly' not in result:
        print(f"❌ Dados de Balanço não disponíveis para {ticker}")
        return None
    
    balanco_trimestral = result['balanceSheetHistoryQuarterly']
    print(f"✅ Obtidos {len(balanco_trimestral)} trimestres da BRAPI")
    
    # Identificar trimestres faltantes
    trimestres_faltantes = identificar_trimestres_faltantes(df_atual)
    print(f"📋 Trimestres faltantes identificados: {len(trimestres_faltantes)}")
    
    if not trimestres_faltantes:
        print("✅ Não há trimestres faltantes!")
        return df_atual
    
    # Criar cópia do DataFrame para modificação
    df_novo = df_atual.copy()
    
    # Processar cada registro da BRAPI
    trimestres_preenchidos = []
    for registro in balanco_trimestral:
        if 'endDate' not in registro:
            continue
        
        trimestre = extrair_trimestre_ano(registro['endDate'])
        if not trimestre or trimestre not in trimestres_faltantes:
            continue
        
        # Adicionar coluna se não existir
        if trimestre not in df_novo.columns:
            df_novo[trimestre] = None
        
        # Preencher valores para cada conta (ATIVOS)
        for campo_brapi, valor in registro.items():
            if campo_brapi == 'endDate' or valor is None:
                continue
            
            # Mapear campo
            mapeamento = mapear_campo_brapi(campo_brapi, 'bpa')
            if not mapeamento:
                continue
            
            cd_conta, conta = mapeamento
            
            # Encontrar a linha correspondente
            mask = df_novo['cd_conta'] == cd_conta
            if mask.any():
                df_novo.loc[mask, trimestre] = valor
            else:
                # Adicionar nova linha se não existir
                nova_linha = {'cd_conta': cd_conta, 'conta': conta, trimestre: valor}
                df_novo = pd.concat([df_novo, pd.DataFrame([nova_linha])], ignore_index=True)
        
        trimestres_preenchidos.append(trimestre)
    
    # Ordenar colunas
    colunas_trim = sorted([col for col in df_novo.columns if 'T' in str(col)])
    df_novo = df_novo[['cd_conta', 'conta'] + colunas_trim]
    
    print(f"✅ Preenchidos {len(trimestres_preenchidos)} trimestres")
    
    return df_novo


def processar_bpp(ticker, df_atual):
    """
    Processa BPP (Balanço Patrimonial Passivo) e preenche trimestres faltantes
    
    Args:
        ticker: Código da ação
        df_atual: DataFrame com dados atuais do BPP
    
    Returns:
        DataFrame: DataFrame atualizado ou None em caso de erro
    """
    print(f"\n📊 Processando BPP de {ticker}...")
    
    # Buscar dados da BRAPI
    dados = buscar_dados_brapi(ticker, 'balanceSheetHistoryQuarterly')
    if not dados or 'results' not in dados:
        print(f"❌ Não foi possível obter dados de {ticker}")
        return None
    
    result = dados['results'][0]
    if 'balanceSheetHistoryQuarterly' not in result:
        print(f"❌ Dados de Balanço não disponíveis para {ticker}")
        return None
    
    balanco_trimestral = result['balanceSheetHistoryQuarterly']
    print(f"✅ Obtidos {len(balanco_trimestral)} trimestres da BRAPI")
    
    # Identificar trimestres faltantes
    trimestres_faltantes = identificar_trimestres_faltantes(df_atual)
    print(f"📋 Trimestres faltantes identificados: {len(trimestres_faltantes)}")
    
    if not trimestres_faltantes:
        print("✅ Não há trimestres faltantes!")
        return df_atual
    
    # Criar cópia do DataFrame para modificação
    df_novo = df_atual.copy()
    
    # Processar cada registro da BRAPI
    trimestres_preenchidos = []
    for registro in balanco_trimestral:
        if 'endDate' not in registro:
            continue
        
        trimestre = extrair_trimestre_ano(registro['endDate'])
        if not trimestre or trimestre not in trimestres_faltantes:
            continue
        
        # Adicionar coluna se não existir
        if trimestre not in df_novo.columns:
            df_novo[trimestre] = None
        
        # Preencher valores para cada conta (PASSIVOS)
        for campo_brapi, valor in registro.items():
            if campo_brapi == 'endDate' or valor is None:
                continue
            
            # Mapear campo
            mapeamento = mapear_campo_brapi(campo_brapi, 'bpp')
            if not mapeamento:
                continue
            
            cd_conta, conta = mapeamento
            
            # Encontrar a linha correspondente
            mask = df_novo['cd_conta'] == cd_conta
            if mask.any():
                df_novo.loc[mask, trimestre] = valor
            else:
                # Adicionar nova linha se não existir
                nova_linha = {'cd_conta': cd_conta, 'conta': conta, trimestre: valor}
                df_novo = pd.concat([df_novo, pd.DataFrame([nova_linha])], ignore_index=True)
        
        trimestres_preenchidos.append(trimestre)
    
    # Ordenar colunas
    colunas_trim = sorted([col for col in df_novo.columns if 'T' in str(col)])
    df_novo = df_novo[['cd_conta', 'conta'] + colunas_trim]
    
    print(f"✅ Preenchidos {len(trimestres_preenchidos)} trimestres")
    
    return df_novo


def processar_ticker(ticker, diretorio_entrada, diretorio_saida):
    """
    Processa todos os balanços de um ticker
    
    Args:
        ticker: Código da ação
        diretorio_entrada: Diretório com arquivos atuais
        diretorio_saida: Diretório para salvar arquivos atualizados
    
    Returns:
        bool: True se sucesso, False caso contrário
    """
    print(f"\n{'='*60}")
    print(f"🏦 Processando {ticker}")
    print(f"{'='*60}")
    
    try:
        # Criar diretório de saída se não existir
        Path(diretorio_saida).mkdir(parents=True, exist_ok=True)
        
        # Processar DRE
        dre_path = Path(diretorio_entrada) / 'dre_padronizado.csv'
        if dre_path.exists():
            df_dre = pd.read_csv(dre_path)
            df_dre_novo = processar_dre(ticker, df_dre)
            if df_dre_novo is not None:
                output_path = Path(diretorio_saida) / 'dre_padronizado.csv'
                df_dre_novo.to_csv(output_path, index=False)
                print(f"✅ DRE salvo em: {output_path}")
        
        # Processar BPA
        bpa_path = Path(diretorio_entrada) / 'bpa_padronizado.csv'
        if bpa_path.exists():
            df_bpa = pd.read_csv(bpa_path)
            df_bpa_novo = processar_bpa(ticker, df_bpa)
            if df_bpa_novo is not None:
                output_path = Path(diretorio_saida) / 'bpa_padronizado.csv'
                df_bpa_novo.to_csv(output_path, index=False)
                print(f"✅ BPA salvo em: {output_path}")
        
        # Processar BPP
        bpp_path = Path(diretorio_entrada) / 'bpp_padronizado.csv'
        if bpp_path.exists():
            df_bpp = pd.read_csv(bpp_path)
            df_bpp_novo = processar_bpp(ticker, df_bpp)
            if df_bpp_novo is not None:
                output_path = Path(diretorio_saida) / 'bpp_padronizado.csv'
                df_bpp_novo.to_csv(output_path, index=False)
                print(f"✅ BPP salvo em: {output_path}")
        
        print(f"\n✅ {ticker} processado com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao processar {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Exemplo de uso
    if len(sys.argv) > 1:
        ticker = sys.argv[1]
        dir_entrada = sys.argv[2] if len(sys.argv) > 2 else '.'
        dir_saida = sys.argv[3] if len(sys.argv) > 3 else './output'
        
        processar_ticker(ticker, dir_entrada, dir_saida)
    else:
        print("""
╔══════════════════════════════════════════════════════════════╗
║  Preencher Balanços Financeiros com Dados da BRAPI          ║
║  Monalisa Research - Antonio Siqueira                        ║
╚══════════════════════════════════════════════════════════════╝

Uso:
    python preencher_balancos_brapi.py TICKER [DIR_ENTRADA] [DIR_SAIDA]

Exemplo:
    python preencher_balancos_brapi.py BBAS3 ./balancos/BBAS3 ./output/BBAS3

O script irá:
1. Ler os arquivos existentes (dre_padronizado.csv, bpa_padronizado.csv, bpp_padronizado.csv)
2. Identificar trimestres faltantes desde 2010
3. Buscar dados na BRAPI
4. Preencher os gaps mantendo o formato original
5. Salvar arquivos atualizados no diretório de saída
        """)
