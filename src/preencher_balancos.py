#!/usr/bin/env python3
"""
Script CORRETO de Preenchimento de DRE com Dados da BRAPI
Versão 3 - Baseado na estrutura REAL da API

Autor: Claude + Antonio Siqueira
Data: 2025-01-11
"""

import os
import sys
import pandas as pd
import numpy as np
import urllib.request
import json
from datetime import datetime

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

TOKEN_BRAPI = 'eq3dB3MBPiKUnzqa7My7MY'
ARQUIVO_EMPRESAS = 'empresas_listadas_bancos.xlsx'
ARQUIVO_DRE = 'dre_padronizado.csv'

# ============================================================================
# MAPEAMENTO CORRETO - BASEADO NA ESTRUTURA REAL DA BRAPI
# ============================================================================

MAPEAMENTO_DRE = {
    # cd_conta: (campo_brapi, operação, descrição)
    '3.01': ('totalRevenue', 'direto', 'Receitas de Intermediação Financeira'),
    '3.02': ('costOfRevenue', 'direto', 'Despesas de Intermediação Financeira'),  # JÁ É NEGATIVO!
    '3.03': ('grossProfit', 'direto', 'Resultado Bruto de Intermediação Financeira'),
    '3.04': ('operatingIncome', 'calculo', 'Outras Despesas e Receitas Operacionais'),  # operatingIncome - grossProfit
    '3.05': ('incomeBeforeTax', 'direto', 'Resultado antes dos Tributos sobre o Lucro'),
    '3.06': ('incomeTaxExpense', 'direto', 'Imposto de Renda e Contribuição Social sobre o Lucro'),
    '3.07': ('netIncomeFromContinuingOps', 'direto', 'Lucro ou Prejuízo das Operações Continuadas'),
    '3.08': ('discontinuedOperations', 'direto', 'Resultado Líquido das Operações Descontinuadas'),
    '3.09': ('incomeBeforeStatutoryParticipationsAndContributions', 'direto', 'Lucro ou Prejuízo antes das Participações e Contribuições Estatutárias'),
    '3.10': ('profitSharingAndStatutoryContributions', 'direto', 'Participações nos Lucros e Contribuições Estatutárias'),
    '3.11': ('netIncome', 'calculo', 'Lucro ou Prejuízo Líquido Consolidado do Período'),  # 3.09 - 3.10
    '3.99': ('basicEarningsPerCommonShare', 'direto', 'Lucro por Ação (Reais/Ação)'),
}

# ============================================================================
# FUNÇÕES DE BUSCA NA BRAPI
# ============================================================================

def buscar_dre_brapi(ticker, token):
    """
    Busca DRE trimestral de um ticker na BRAPI
    
    Returns:
        list: Lista de trimestres com dados da DRE ou None em caso de erro
    """
    url = f'https://brapi.dev/api/quote/{ticker}?modules=incomeStatementHistoryQuarterly'
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {token}')
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            
            if 'results' not in data or not data['results']:
                print(f"  ❌ Sem resultados para {ticker}")
                return None
            
            result = data['results'][0]
            
            if 'incomeStatementHistoryQuarterly' not in result:
                print(f"  ❌ Módulo DRE não disponível para {ticker}")
                return None
            
            statements = result['incomeStatementHistoryQuarterly']
            print(f"  ✅ {len(statements)} trimestres encontrados")
            
            return statements
            
    except urllib.error.HTTPError as e:
        print(f"  ❌ Erro HTTP {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return None

# ============================================================================
# FUNÇÕES DE PROCESSAMENTO
# ============================================================================

def trimestre_para_coluna(endDate):
    """
    Converte data (YYYY-MM-DD) para formato de coluna (YYYYTQ)
    
    Exemplos:
        2024-03-31 → 2024T1
        2024-06-30 → 2024T2
        2024-09-30 → 2024T3
        2024-12-31 → 2024T4
    """
    try:
        data = pd.to_datetime(endDate)
        ano = data.year
        mes = data.month
        
        if mes <= 3:
            trimestre = 1
        elif mes <= 6:
            trimestre = 2
        elif mes <= 9:
            trimestre = 3
        else:
            trimestre = 4
        
        return f"{ano}T{trimestre}"
    except:
        return None

def calcular_conta_304(dados):
    """
    Calcula conta 3.04: Outras Despesas e Receitas Operacionais
    = operatingIncome - grossProfit
    """
    operating = dados.get('operatingIncome')
    gross = dados.get('grossProfit')
    
    if pd.notna(operating) and pd.notna(gross):
        return operating - gross
    return None

def calcular_conta_311(dados):
    """
    Calcula conta 3.11: Lucro Líquido Consolidado
    = incomeBeforeStatutoryParticipationsAndContributions - profitSharingAndStatutoryContributions
    
    Se não tiver participações, usa o próprio incomeBeforeStatutory
    """
    antes_participacoes = dados.get('incomeBeforeStatutoryParticipationsAndContributions')
    participacoes = dados.get('profitSharingAndStatutoryContributions')
    
    if pd.notna(antes_participacoes):
        if pd.notna(participacoes):
            return antes_participacoes - participacoes
        else:
            # Se não tem participações, o lucro líquido é igual ao antes das participações
            return antes_participacoes
    
    # Fallback: tentar netIncome
    net_income = dados.get('netIncome')
    if pd.notna(net_income):
        return net_income
    
    return None

def processar_ticker_brapi(ticker, df_dre, ano_inicio=2010):
    """
    Processa um ticker: busca dados da BRAPI e preenche no DataFrame
    
    Args:
        ticker: Código do ativo
        df_dre: DataFrame com DRE padronizado
        ano_inicio: Ano inicial para buscar dados (default: 2010)
    
    Returns:
        int: Número de trimestres preenchidos
    """
    print(f"\n{'='*80}")
    print(f"Processando: {ticker}")
    print(f"{'='*80}")
    
    # Buscar dados na BRAPI
    statements = buscar_dre_brapi(ticker, TOKEN_BRAPI)
    
    if not statements:
        return 0
    
    trimestres_preenchidos = 0
    
    # Processar cada trimestre
    for stmt in statements:
        endDate = stmt.get('endDate')
        
        if not endDate:
            continue
        
        # Filtrar por ano
        ano = int(endDate[:4])
        if ano < ano_inicio:
            continue
        
        coluna = trimestre_para_coluna(endDate)
        
        if not coluna or coluna not in df_dre.columns:
            continue
        
        # Preencher cada conta
        for cd_conta, (campo_brapi, operacao, descricao) in MAPEAMENTO_DRE.items():
            try:
                # Verificar se já tem valor
                linha_idx = df_dre[df_dre['cd_conta'] == cd_conta].index
                
                if len(linha_idx) == 0:
                    continue
                
                linha_idx = linha_idx[0]
                valor_atual = df_dre.loc[linha_idx, coluna]
                
                # Só preenche se estiver vazio
                if pd.notna(valor_atual):
                    continue
                
                # Obter valor
                if operacao == 'direto':
                    valor = stmt.get(campo_brapi)
                elif operacao == 'calculo':
                    if cd_conta == '3.04':
                        valor = calcular_conta_304(stmt)
                    elif cd_conta == '3.11':
                        valor = calcular_conta_311(stmt)
                    else:
                        valor = None
                else:
                    valor = None
                
                # Preencher
                if pd.notna(valor):
                    df_dre.loc[linha_idx, coluna] = valor
                    trimestres_preenchidos += 1
                    
            except Exception as e:
                print(f"  ⚠️  Erro ao processar {cd_conta} em {coluna}: {e}")
                continue
    
    print(f"  ✅ {trimestres_preenchidos} valores preenchidos")
    
    return trimestres_preenchidos

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """
    Função principal
    """
    print("\n" + "="*80)
    print("PREENCHIMENTO DE DRE COM DADOS DA BRAPI")
    print("Versão 3 - ESTRUTURA CORRETA")
    print("="*80)
    
    # Verificar arquivos
    if not os.path.exists(ARQUIVO_EMPRESAS):
        print(f"\n❌ Arquivo não encontrado: {ARQUIVO_EMPRESAS}")
        return
    
    if not os.path.exists(ARQUIVO_DRE):
        print(f"\n❌ Arquivo não encontrado: {ARQUIVO_DRE}")
        return
    
    # Carregar dados
    print(f"\n📂 Carregando dados...")
    df_empresas = pd.read_excel(ARQUIVO_EMPRESAS)
    df_dre = pd.read_csv(ARQUIVO_DRE)
    
    print(f"  ✅ {len(df_empresas)} empresas carregadas")
    print(f"  ✅ {len(df_dre)} contas no DRE")
    
    # Processar primeira empresa como teste
    ticker = df_empresas.iloc[0]['ticker']
    
    processar_ticker_brapi(ticker, df_dre)
    
    # Salvar
    print(f"\n💾 Salvando arquivo...")
    df_dre.to_csv(ARQUIVO_DRE, index=False)
    print(f"  ✅ Arquivo salvo: {ARQUIVO_DRE}")
    
    print("\n" + "="*80)
    print("CONCLUÍDO!")
    print("="*80)

if __name__ == "__main__":
    main()
