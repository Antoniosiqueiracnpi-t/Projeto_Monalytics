"""
Preencher Balanços Financeiros com BRAPI
Versão GitHub Actions
Monalisa Research - Antonio Siqueira
"""

import pandas as pd
import json
import urllib.request
from datetime import datetime
from pathlib import Path
import sys
import os
import argparse
import time

# Token BRAPI - usar variável de ambiente
BRAPI_TOKEN = os.getenv('BRAPI_TOKEN', 'ukQzv8YM3L28VarpcbLDEV')

# Mapeamento de contas - igual ao original
MAPA_DRE = {
    'financialIntermediationRevenue': ('3.01', 'Receitas de Intermediação Financeira'),
    'financialIntermediationExpenses': ('3.02', 'Despesas de Intermediação Financeira'),
    'totalRevenue': ('3.01', 'Receitas de Intermediação Financeira'),
    'costOfRevenue': ('3.02', 'Despesas de Intermediação Financeira'),
    'grossProfit': ('3.03', 'Resultado Bruto de Intermediação Financeira'),
    'operatingExpenses': ('3.04', 'Outras Despesas e Receitas Operacionais'),
    'sellingGeneralAdministrative': ('3.04', 'Outras Despesas e Receitas Operacionais'),
    'incomeBeforeTax': ('3.05', 'Resultado antes dos Tributos sobre o Lucro'),
    'incomeTaxExpense': ('3.06', 'Imposto de Renda e Contribuição Social sobre o Lucro'),
    'netIncomeFromContinuingOps': ('3.07', 'Lucro ou Prejuízo das Operações Continuadas'),
    'discontinuedOperations': ('3.08', 'Resultado Líquido das Operações Descontinuadas'),
    'netIncome': ('3.09', 'Lucro ou Prejuízo antes das Participações e Contribuições Estatutárias'),
    'netIncomeApplicableToCommonShares': ('3.11', 'Lucro ou Prejuízo Líquido Consolidado do Período'),
    'basicEarningsPerShare': ('3.99', 'Lucro por Ação (Reais/Ação)'),
    'dilutedEarningsPerShare': ('3.99', 'Lucro por Ação (Reais/Ação)'),
}

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
    """Busca dados na BRAPI"""
    url = f'https://brapi.dev/api/quote/{ticker}?modules={modulo}'
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {BRAPI_TOKEN}')
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"❌ Erro ao buscar {ticker}: {e}")
        return None


def extrair_trimestre_ano(data_str):
    """Converte YYYY-MM-DD para YYYYTQ"""
    try:
        data = datetime.strptime(data_str, '%Y-%m-%d')
        trimestre = (data.month - 1) // 3 + 1
        return f"{data.year}T{trimestre}"
    except:
        return None


def identificar_trimestres_faltantes(df_atual, ano_inicio=2010):
    """Identifica trimestres faltantes"""
    colunas_trim = [col for col in df_atual.columns if 'T' in str(col) and len(str(col)) == 6]
    trimestres_existentes = set(colunas_trim)
    
    ano_atual = datetime.now().year
    todos_trimestres = []
    
    for ano in range(ano_inicio, ano_atual + 1):
        for trim in range(1, 5):
            todos_trimestres.append(f"{ano}T{trim}")
    
    trimestres_faltantes = [t for t in todos_trimestres if t not in trimestres_existentes]
    
    if trimestres_existentes:
        ultimo_existente = max(trimestres_existentes)
        trimestres_faltantes = [t for t in trimestres_faltantes if t < ultimo_existente]
    
    return sorted(trimestres_faltantes)


def mapear_campo_brapi(campo_brapi, tipo_balanco):
    """Mapeia campo BRAPI para formato padronizado"""
    mapas = {'dre': MAPA_DRE, 'bpa': MAPA_BPA, 'bpp': MAPA_BPP}
    mapa = mapas.get(tipo_balanco)
    return mapa.get(campo_brapi) if mapa else None


def processar_demonstrativo(ticker, df_atual, modulo, tipo, ano_inicio=2010):
    """Processa um demonstrativo (DRE, BPA ou BPP)"""
    
    # Buscar dados
    dados = buscar_dados_brapi(ticker, modulo)
    if not dados or 'results' not in dados:
        return None
    
    result = dados['results'][0]
    chave = modulo if modulo in result else None
    
    if not chave or not result.get(chave):
        return None
    
    dados_trimestrais = result[chave]
    
    # Identificar trimestres faltantes
    trimestres_faltantes = identificar_trimestres_faltantes(df_atual, ano_inicio)
    
    if not trimestres_faltantes:
        return df_atual
    
    # Criar cópia
    df_novo = df_atual.copy()
    
    # Processar registros
    trimestres_preenchidos = []
    for registro in dados_trimestrais:
        if 'endDate' not in registro:
            continue
        
        trimestre = extrair_trimestre_ano(registro['endDate'])
        if not trimestre or trimestre not in trimestres_faltantes:
            continue
        
        # Adicionar coluna se não existir
        if trimestre not in df_novo.columns:
            df_novo[trimestre] = None
        
        # Preencher valores
        for campo_brapi, valor in registro.items():
            if campo_brapi == 'endDate' or valor is None:
                continue
            
            mapeamento = mapear_campo_brapi(campo_brapi, tipo)
            if not mapeamento:
                continue
            
            cd_conta, descricao = mapeamento
            
            # Nome da coluna de descrição
            col_desc = 'ds_conta' if tipo == 'dre' else 'conta'
            
            # Encontrar linha
            mask = df_novo['cd_conta'] == cd_conta
            if mask.any():
                df_novo.loc[mask, trimestre] = valor
            else:
                # Adicionar nova linha
                nova_linha = {'cd_conta': cd_conta, col_desc: descricao, trimestre: valor}
                df_novo = pd.concat([df_novo, pd.DataFrame([nova_linha])], ignore_index=True)
        
        trimestres_preenchidos.append(trimestre)
    
    # Ordenar colunas
    colunas_trim = sorted([col for col in df_novo.columns if 'T' in str(col)])
    col_desc = 'ds_conta' if tipo == 'dre' else 'conta'
    df_novo = df_novo[['cd_conta', col_desc] + colunas_trim]
    
    print(f"  ✅ Preenchidos {len(trimestres_preenchidos)} trimestres")
    
    return df_novo


def processar_ticker(ticker, ano_inicio=2010):
    """Processa todos os balanços de um ticker"""
    print(f"\n{'='*60}")
    print(f"🏦 Processando {ticker}")
    print(f"{'='*60}")
    
    base_dir = Path('balancos') / ticker
    if not base_dir.exists():
        print(f"⚠️  Diretório não encontrado: {base_dir}")
        return False
    
    sucesso = False
    
    # Processar DRE
    dre_path = base_dir / 'dre_padronizado.csv'
    if dre_path.exists():
        print(f"\n📊 Processando DRE de {ticker}...")
        try:
            df_dre = pd.read_csv(dre_path)
            df_dre_novo = processar_demonstrativo(
                ticker, df_dre, 'incomeStatementHistoryQuarterly', 'dre', ano_inicio
            )
            if df_dre_novo is not None:
                df_dre_novo.to_csv(dre_path, index=False)
                print(f"  💾 DRE salvo: {dre_path}")
                sucesso = True
        except Exception as e:
            print(f"  ❌ Erro no DRE: {e}")
    
    # Processar BPA
    bpa_path = base_dir / 'bpa_padronizado.csv'
    if bpa_path.exists():
        print(f"\n📊 Processando BPA de {ticker}...")
        try:
            df_bpa = pd.read_csv(bpa_path)
            df_bpa_novo = processar_demonstrativo(
                ticker, df_bpa, 'balanceSheetHistoryQuarterly', 'bpa', ano_inicio
            )
            if df_bpa_novo is not None:
                df_bpa_novo.to_csv(bpa_path, index=False)
                print(f"  💾 BPA salvo: {bpa_path}")
                sucesso = True
        except Exception as e:
            print(f"  ❌ Erro no BPA: {e}")
    
    # Processar BPP
    bpp_path = base_dir / 'bpp_padronizado.csv'
    if bpp_path.exists():
        print(f"\n📊 Processando BPP de {ticker}...")
        try:
            df_bpp = pd.read_csv(bpp_path)
            df_bpp_novo = processar_demonstrativo(
                ticker, df_bpp, 'balanceSheetHistoryQuarterly', 'bpp', ano_inicio
            )
            if df_bpp_novo is not None:
                df_bpp_novo.to_csv(bpp_path, index=False)
                print(f"  💾 BPP salvo: {bpp_path}")
                sucesso = True
        except Exception as e:
            print(f"  ❌ Erro no BPP: {e}")
    
    if sucesso:
        print(f"\n✅ {ticker} processado com sucesso!")
    
    return sucesso


def obter_lista_tickers():
    """Obtém lista de todos os tickers disponíveis"""
    balancos_dir = Path('balancos')
    if not balancos_dir.exists():
        return []
    
    tickers = []
    for item in balancos_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Verificar se tem pelo menos um arquivo padronizado
            if any((item / f).exists() for f in ['dre_padronizado.csv', 'bpa_padronizado.csv', 'bpp_padronizado.csv']):
                tickers.append(item.name)
    
    return sorted(tickers)


def selecionar_tickers(modo, quantidade=None, ticker=None, lista=None, faixa=None):
    """Seleciona tickers baseado no modo escolhido"""
    
    todos_tickers = obter_lista_tickers()
    total_disponivel = len(todos_tickers)
    
    print(f"\n📋 Total de tickers disponíveis: {total_disponivel}")
    
    if modo == 'ticker':
        if not ticker:
            print("❌ Modo 'ticker' requer o parâmetro --ticker")
            return []
        return [ticker.upper()]
    
    elif modo == 'lista':
        if not lista:
            print("❌ Modo 'lista' requer o parâmetro --lista")
            return []
        return [t.strip().upper() for t in lista.split(',')]
    
    elif modo == 'quantidade':
        qtd = int(quantidade) if quantidade else 10
        if qtd >= total_disponivel:
            qtd = total_disponivel
        return todos_tickers[:qtd]
    
    elif modo == 'faixa':
        if not faixa or '-' not in faixa:
            print("❌ Modo 'faixa' requer formato: 1-50")
            return []
        
        try:
            inicio, fim = map(int, faixa.split('-'))
            inicio = max(1, inicio)
            fim = min(fim, total_disponivel)
            return todos_tickers[inicio-1:fim]
        except ValueError:
            print("❌ Formato de faixa inválido. Use: 1-50")
            return []
    
    return []


def main():
    parser = argparse.ArgumentParser(
        description='Preencher balanços financeiros com dados da BRAPI'
    )
    parser.add_argument('--modo', required=True, 
                       choices=['quantidade', 'ticker', 'lista', 'faixa'],
                       help='Modo de seleção de tickers')
    parser.add_argument('--quantidade', default='10',
                       help='Quantidade de tickers (modo quantidade)')
    parser.add_argument('--ticker', default='',
                       help='Ticker único (modo ticker)')
    parser.add_argument('--lista', default='',
                       help='Lista de tickers separados por vírgula (modo lista)')
    parser.add_argument('--faixa', default='1-50',
                       help='Faixa de tickers (modo faixa)')
    parser.add_argument('--ano-inicio', type=int, default=2010,
                       help='Ano de início para preencher (padrão: 2010)')
    
    args = parser.parse_args()
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  Preencher Balanços Financeiros com BRAPI                   ║")
    print("║  Monalisa Research - Antonio Siqueira                        ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    # Verificar token
    if BRAPI_TOKEN == 'ukQzv8YM3L28VarpcbLDEV':
        print("⚠️  Usando token padrão. Configure BRAPI_TOKEN para produção!")
    
    # Selecionar tickers
    tickers = selecionar_tickers(
        args.modo,
        args.quantidade,
        args.ticker,
        args.lista,
        args.faixa
    )
    
    if not tickers:
        print("❌ Nenhum ticker selecionado!")
        sys.exit(1)
    
    print(f"\n🎯 Selecionados {len(tickers)} tickers para processar:")
    for i, t in enumerate(tickers, 1):
        print(f"  {i:3d}. {t}")
    
    print(f"\n⏰ Ano de início: {args.ano_inicio}")
    print(f"\n{'='*60}")
    
    # Processar cada ticker
    sucessos = []
    falhas = []
    
    for i, ticker in enumerate(tickers, 1):
        print(f"\n[{i}/{len(tickers)}]")
        try:
            if processar_ticker(ticker, args.ano_inicio):
                sucessos.append(ticker)
            else:
                falhas.append(ticker)
            
            # Aguardar entre requisições para não sobrecarregar API
            if i < len(tickers):
                time.sleep(2)
                
        except Exception as e:
            print(f"❌ Erro crítico em {ticker}: {e}")
            falhas.append(ticker)
    
    # Resumo final
    print(f"\n{'='*60}")
    print("📊 RESUMO FINAL")
    print(f"{'='*60}")
    print(f"✅ Sucessos: {len(sucessos)}/{len(tickers)}")
    print(f"❌ Falhas: {len(falhas)}/{len(tickers)}")
    
    if sucessos:
        print(f"\n✅ Processados com sucesso:")
        for t in sucessos:
            print(f"  • {t}")
    
    if falhas:
        print(f"\n❌ Falhas:")
        for t in falhas:
            print(f"  • {t}")
    
    print(f"\n{'='*60}")
    
    # Exit code baseado em sucessos
    sys.exit(0 if sucessos else 1)


if __name__ == "__main__":
    main()
