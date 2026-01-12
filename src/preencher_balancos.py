"""
Preencher Balanços Financeiros com BRAPI - Versão 2.0
Versão melhorada com suporte específico para bancos
Monalisa Research - Antonio Siqueira
"""

import pandas as pd
import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
import sys
import os
import argparse
import time

# Token BRAPI - usar variável de ambiente
BRAPI_TOKEN = os.getenv('BRAPI_TOKEN', '')

# Se não tiver token em variável de ambiente, tentar valor padrão
if not BRAPI_TOKEN:
    BRAPI_TOKEN = 'ukQzv8YM3L28VarpcbLDEV'
    print("⚠️  BRAPI_TOKEN não encontrado em variável de ambiente")
    print(f"    Usando token padrão: {BRAPI_TOKEN[:10]}...")

# ============================================================================
# LISTA DE BANCOS CONHECIDOS
# ============================================================================
BANCOS_CONHECIDOS = [
    'BBAS3',   # Banco do Brasil
    'ITUB3', 'ITUB4',  # Itaú Unibanco
    'BBDC3', 'BBDC4',  # Bradesco
    'SANB3', 'SANB4', 'SANB11',  # Santander
    'BPAC3', 'BPAC5', 'BPAC11',  # BTG Pactual
    'BBSE3',   # BB Seguridade
    'BAZA3',   # Banco da Amazônia
    'PINE4',   # Pine
    'BMGB4',   # Banco BMG
    'BRSR6',   # Banrisul
    'BIDI3', 'BIDI4', 'BIDI11',  # Banco Inter
    'BMEB4',   # Banco Mercantil do Brasil
]

# ============================================================================
# MAPEAMENTOS ESPECÍFICOS PARA BANCOS
# ============================================================================

MAPA_BPA_BANCOS = {
    'cash': ('1.01', 'Caixa e Equivalentes de Caixa'),
    'cashAndCashEquivalents': ('1.01', 'Caixa e Equivalentes de Caixa'),
    'financialAssets': ('1.02', 'Ativos Financeiros'),
    'currentAndDeferredTaxes': ('1.03', 'Tributos'),
    'taxesToRecover': ('1.03', 'Tributos'),
    'otherAssets': ('1.04', 'Outros Ativos'),
    'investments': ('1.05', 'Investimentos'),
    'propertyPlantEquipment': ('1.06', 'Imobilizado'),
    'intangibleAssets': ('1.07', 'Intangível'),
    'intangibleAsset': ('1.07', 'Intangível'),
    'totalAssets': ('1', 'Ativo Total'),
}

MAPA_BPP_BANCOS = {
    'financialLiabilitiesMeasuredAtFairValueThroughIncome': ('2.01', 'Passivos Financeiros ao Valor Justo através do Resultado'),
    'financialLiabilitiesAtAmortizedCost': ('2.02', 'Passivos Financeiros ao Custo Amortizado'),
    'provisions': ('2.03', 'Provisões'),
    'taxLiabilities': ('2.04', 'Passivos Fiscais'),
    'otherLiabilities': ('2.05', 'Outros Passivos'),
    'totalStockholderEquity': ('2.07', 'Patrimônio Líquido Consolidado'),
    'shareholdersEquity': ('2.07', 'Patrimônio Líquido Consolidado'),
    'totalEquity': ('2.07', 'Patrimônio Líquido Consolidado'),
    'totalLiabilities': ('2', 'Passivo Total'),
    'totalLiab': ('2', 'Passivo Total'),
}

MAPA_DRE_BANCOS = {
    # Campos específicos de bancos (prioridade alta)
    'financialIntermediationRevenue': ('3.01', 'Receitas de Intermediação Financeira'),
    'financialIntermediationExpenses': ('3.02', 'Despesas de Intermediação Financeira'),
    
    # Campos genéricos (prioridade baixa - fallback)
    'totalRevenue': ('3.01', 'Receitas de Intermediação Financeira'),
    'costOfRevenue': ('3.02', 'Despesas de Intermediação Financeira'),
    
    # Campos comuns
    'grossProfit': ('3.03', 'Resultado Bruto de Intermediação Financeira'),
    'sellingGeneralAdministrative': ('3.04', 'Outras Despesas e Receitas Operacionais'),
    'operatingExpenses': ('3.04', 'Outras Despesas e Receitas Operacionais'),
    'incomeBeforeTax': ('3.05', 'Resultado antes dos Tributos sobre o Lucro'),
    'incomeTaxExpense': ('3.06', 'Imposto de Renda e Contribuição Social sobre o Lucro'),
    'netIncomeFromContinuingOps': ('3.07', 'Lucro ou Prejuízo das Operações Continuadas'),
    'discontinuedOperations': ('3.08', 'Resultado Líquido das Operações Descontinuadas'),
    'netIncome': ('3.09', 'Lucro ou Prejuízo antes das Participações e Contribuições Estatutárias'),
    'netIncomeApplicableToCommonShares': ('3.11', 'Lucro ou Prejuízo Líquido Consolidado do Período'),
    'earningsPerShare': ('3.99', 'Lucro por Ação (Reais/Ação)'),
    'basicEarningsPerShare': ('3.99', 'Lucro por Ação (Reais/Ação)'),
    'dilutedEarningsPerShare': ('3.99', 'Lucro por Ação (Reais/Ação)'),
}

# ============================================================================
# MAPEAMENTOS PARA EMPRESAS NÃO-FINANCEIRAS (mantido do original)
# ============================================================================

MAPA_BPA_EMPRESAS = {
    'totalAssets': ('1', 'Ativo Total'),
    'cash': ('1.01', 'Caixa e Equivalentes de Caixa'),
    'cashAndCashEquivalents': ('1.01', 'Caixa e Equivalentes de Caixa'),
    'shortTermInvestments': ('1.02', 'Aplicações Financeiras'),
    'netReceivables': ('1.03', 'Contas a Receber'),
    'inventory': ('1.04', 'Estoques'),
    'otherCurrentAssets': ('1.05', 'Outros Ativos Circulantes'),
    'investments': ('1.06', 'Investimentos'),
    'propertyPlantEquipment': ('1.07', 'Imobilizado'),
    'intangibleAssets': ('1.08', 'Intangível'),
    'otherAssets': ('1.09', 'Outros Ativos'),
}

MAPA_BPP_EMPRESAS = {
    'totalLiab': ('2', 'Passivo Total'),
    'accountsPayable': ('2.01', 'Fornecedores'),
    'providers': ('2.01', 'Fornecedores'),
    'shortLongTermDebt': ('2.02', 'Empréstimos e Financiamentos Circulantes'),
    'loansAndFinancing': ('2.02', 'Empréstimos e Financiamentos Circulantes'),
    'otherCurrentLiab': ('2.03', 'Outros Passivos Circulantes'),
    'longTermDebt': ('2.04', 'Empréstimos e Financiamentos Não Circulantes'),
    'longTermLoansAndFinancing': ('2.04', 'Empréstimos e Financiamentos Não Circulantes'),
    'otherLiab': ('2.05', 'Outros Passivos Não Circulantes'),
    'totalStockholderEquity': ('2.06', 'Patrimônio Líquido'),
    'shareholdersEquity': ('2.06', 'Patrimônio Líquido'),
}

MAPA_DRE_EMPRESAS = {
    'totalRevenue': ('3.01', 'Receita Líquida de Vendas'),
    'costOfRevenue': ('3.02', 'Custo dos Produtos Vendidos'),
    'grossProfit': ('3.03', 'Lucro Bruto'),
    'operatingExpenses': ('3.04', 'Despesas Operacionais'),
    'sellingGeneralAdministrative': ('3.04', 'Despesas Operacionais'),
    'operatingIncome': ('3.05', 'Lucro Operacional'),
    'ebit': ('3.05', 'Lucro Operacional'),
    'incomeBeforeTax': ('3.06', 'Resultado antes dos Tributos'),
    'incomeTaxExpense': ('3.07', 'Imposto de Renda e Contribuição Social'),
    'netIncomeFromContinuingOps': ('3.08', 'Lucro das Operações Continuadas'),
    'netIncome': ('3.09', 'Lucro Líquido'),
    'netIncomeApplicableToCommonShares': ('3.10', 'Lucro Líquido Atribuível aos Acionistas'),
    'earningsPerShare': ('3.99', 'Lucro por Ação'),
    'basicEarningsPerShare': ('3.99', 'Lucro por Ação'),
    'dilutedEarningsPerShare': ('3.99', 'Lucro por Ação'),
}

# Definir prioridade de campos (campos mais específicos têm prioridade)
PRIORIDADE_CAMPOS = {
    'financialIntermediationRevenue': 10,
    'financialIntermediationExpenses': 10,
    'totalRevenue': 5,
    'costOfRevenue': 5,
    'financialAssets': 10,
    'currentAndDeferredTaxes': 8,
    'taxesToRecover': 7,
}


def is_banco(ticker):
    """Verifica se o ticker é de um banco"""
    return ticker.upper() in BANCOS_CONHECIDOS




def validar_token_brapi():
    """
    Valida se o token BRAPI está funcionando
    Testa com PETR4 que é um ticker gratuito
    """
    print("\n🔐 Validando token BRAPI...")
    
    if not BRAPI_TOKEN:
        print("❌ Token BRAPI não configurado!")
        print("\nComo configurar:")
        print("  1. No GitHub: Settings → Secrets → BRAPI_TOKEN")
        print("  2. Localmente: export BRAPI_TOKEN='seu_token'")
        return False
    
    # Testar com PETR4 (ação gratuita da BRAPI)
    url = 'https://brapi.dev/api/quote/PETR4'
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {BRAPI_TOKEN}')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if 'results' in data and len(data['results']) > 0:
                print(f"✅ Token válido! Testado com PETR4")
                print(f"   Preço PETR4: R$ {data['results'][0].get('regularMarketPrice', 'N/A')}")
                return True
            else:
                print("⚠️  Token válido mas resposta inesperada")
                return False
                
    except urllib.error.HTTPError as e:
        print(f"❌ Erro HTTP {e.code}: {e.reason}")
        
        if e.code == 401:
            print("\n🔴 Token inválido ou expirado!")
            print("\nSoluções:")
            print("  1. Verificar se o token está correto")
            print("  2. Gerar novo token em: https://brapi.dev/dashboard")
            print("  3. Configurar no GitHub: Settings → Secrets → BRAPI_TOKEN")
            
        elif e.code == 402:
            print("\n🔴 Limite de requisições excedido!")
            print("   Considere upgrade do plano BRAPI")
            
        elif e.code == 429:
            print("\n🔴 Rate limit excedido!")
            print("   Aguarde alguns minutos e tente novamente")
        
        return False
        
    except Exception as e:
        print(f"❌ Erro ao validar token: {e}")
        return False


def buscar_dados_brapi(ticker, modulo='balanceSheetHistoryQuarterly'):
    """Busca dados na BRAPI com tratamento de erros melhorado"""
    url = f'https://brapi.dev/api/quote/{ticker}?modules={modulo}'
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {BRAPI_TOKEN}')
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
            
    except urllib.error.HTTPError as e:
        error_msg = f"HTTP {e.code}"
        
        try:
            error_body = json.loads(e.read().decode())
            if 'message' in error_body:
                error_msg += f": {error_body['message']}"
        except:
            error_msg += f": {e.reason}"
        
        print(f"❌ Erro ao buscar {ticker} ({modulo}): {error_msg}")
        return None
        
    except Exception as e:
        print(f"❌ Erro ao buscar {ticker}: {e}")
        return None


from datetime import datetime

def extrair_trimestre_ano(data_str):
    """Converte YYYY-MM-DD para YYYYTn."""
    try:
        data = datetime.strptime(data_str, '%Y-%m-%d')
        trimestre = (data.month - 1) // 3 + 1
        return f"{data.year}T{trimestre}"
    except (ValueError, TypeError):
        return None


# ✅ COMPAT: o processar_demonstrativo() chama extrair_trimestre(end_date)
def extrair_trimestre(end_date):
    """
    Converte endDate do BRAPI para 'YYYYTn'.
    Aceita:
      - 'YYYY-MM-DD'
      - 'YYYY-MM-DDTHH:MM:SS...'
      - 'YYYY-MM-DDTHH:MM:SSZ'
    """
    if not end_date:
        return None

    s = str(end_date).strip()
    if not s:
        return None

    # Pega só a parte da data (primeiros 10 chars) quando vier com timestamp
    data_str = s[:10]

    return extrair_trimestre_ano(data_str)


def extrair_trimestre_ano(data_str):
    """Converte YYYY-MM-DD para YYYYTQ"""
    try:
        data = datetime.strptime(data_str, '%Y-%m-%d')
        trimestre = (data.month - 1) // 3 + 1
        return f"{data.year}T{trimestre}"
    except (ValueError, AttributeError):
        return None


def identificar_primeiro_trimestre_completo(df_atual):
    """
    Identifica o primeiro trimestre que tem dados completos (não vazios)
    Retorna None se não encontrar nenhum trimestre completo
    """
    colunas_trim = [col for col in df_atual.columns if 'T' in str(col) and len(str(col)) == 6]
    
    if not colunas_trim:
        return None
    
    # Ordenar trimestres
    colunas_trim_ordenadas = sorted(colunas_trim)
    
    # Procurar primeiro trimestre com dados não nulos
    for trimestre in colunas_trim_ordenadas:
        valores_nao_nulos = df_atual[trimestre].notna().sum()
        total_linhas = len(df_atual)
        
        # Considerar completo se tiver pelo menos 50% dos dados preenchidos
        if valores_nao_nulos >= total_linhas * 0.5:
            return trimestre
    
    return None


def identificar_trimestres_faltantes(df_atual, primeiro_trimestre_completo, ano_inicio=2010):
    """
    Identifica trimestres faltantes entre ano_inicio e primeiro_trimestre_completo.

    Regra (coerente com 'primeiro_trimestre_completo'):
    - Se a coluna não existe -> faltante
    - Se a coluna existe mas tem menos de 50% das linhas preenchidas -> tratar como faltante
      (permite preencher trimestres parcialmente vazios, sem sobrescrever valores existentes)
    """
    if not primeiro_trimestre_completo:
        return []

    colunas_trim = [col for col in df_atual.columns if 'T' in str(col) and len(str(col)) == 6]
    trimestres_existentes = set(colunas_trim)

    ano_limite = int(primeiro_trimestre_completo[:4])
    trim_limite = int(primeiro_trimestre_completo[5])

    todos_trimestres = []
    for ano in range(ano_inicio, ano_limite + 1):
        for trim in range(1, 5):
            trimestre = f"{ano}T{trim}"
            if ano == ano_limite and trim > trim_limite:
                break
            todos_trimestres.append(trimestre)

    total_linhas = len(df_atual)
    trimestres_faltantes = []

    for t in todos_trimestres:
        if t not in trimestres_existentes:
            trimestres_faltantes.append(t)
            continue

        # Coluna existe: considerar faltante se estiver "pouco preenchida"
        preenchidos = df_atual[t].notna().sum()
        if preenchidos < total_linhas * 0.5:
            trimestres_faltantes.append(t)

    return sorted(trimestres_faltantes)



def mapear_campo_brapi(campo_brapi, tipo_balanco, ticker):
    """Mapeia campo BRAPI para formato padronizado"""
    # Selecionar mapeamento apropriado
    if is_banco(ticker):
        mapas = {
            'dre': MAPA_DRE_BANCOS, 
            'bpa': MAPA_BPA_BANCOS, 
            'bpp': MAPA_BPP_BANCOS
        }
    else:
        mapas = {
            'dre': MAPA_DRE_EMPRESAS, 
            'bpa': MAPA_BPA_EMPRESAS, 
            'bpp': MAPA_BPP_EMPRESAS
        }
    
    mapa = mapas.get(tipo_balanco)
    return mapa.get(campo_brapi) if mapa else None


def normalizar_valor(valor):
    """
    Normaliza valores da BRAPI para o padrão dos arquivos CSV
    
    BRAPI retorna valores em unidades (ex: 81013704000)
    CSV armazena valores em milhares (ex: 81013704.0)
    
    Conversão: dividir por 1000
    """
    if valor is None:
        return None
    
    try:
        # Converter para float e dividir por 1000
        valor_float = float(valor)
        valor_normalizado = valor_float / 1000.0
        return valor_normalizado
    except (ValueError, TypeError):
        return None


def processar_demonstrativo(ticker, df_atual, modulo, tipo, ano_inicio=2010):
    """Processa um demonstrativo (DRE, BPA ou BPP)"""
    
    print(f"  🔍 Identificando primeiro trimestre completo...")
    primeiro_trimestre_completo = identificar_primeiro_trimestre_completo(df_atual)
    
    if not primeiro_trimestre_completo:
        print(f"  ⚠️  Nenhum trimestre completo encontrado")
        return None
    
    print(f"  📅 Primeiro trimestre completo: {primeiro_trimestre_completo}")
    
    # Buscar dados
    dados = buscar_dados_brapi(ticker, modulo)
    if not dados or 'results' not in dados or len(dados['results']) == 0:
        return None
    
    result = dados['results'][0]
    chave = modulo if modulo in result else None
    
    if not chave or not result.get(chave):
        return None
    
    registros = result[chave]
    if not isinstance(registros, list) or len(registros) == 0:
        return None
    
    # Identificar trimestres faltantes
    trimestres_faltantes = identificar_trimestres_faltantes(df_atual, primeiro_trimestre_completo, ano_inicio)
    
    if not trimestres_faltantes:
        print(f"  ✅ Nenhum trimestre faltante para preencher")
        return df_atual
    
    print(f"  📊 Trimestres faltantes: {len(trimestres_faltantes)}")
    
    # Organizar dados por trimestre
    dados_por_trimestre = {}
    
    for registro in registros:
        if not isinstance(registro, dict):
            continue
        
        end_date = registro.get('endDate')
        trimestre = extrair_trimestre(end_date)
        
        if not trimestre or trimestre not in trimestres_faltantes:
            continue
        
        if trimestre not in dados_por_trimestre:
            dados_por_trimestre[trimestre] = {}
        
        # Processar cada campo do registro
        for campo_brapi, valor in registro.items():
            if campo_brapi == 'endDate' or valor is None:
                continue
            
            mapeamento = mapear_campo_brapi(campo_brapi, tipo, ticker)
            if not mapeamento:
                continue
            
            cd_conta, _ = mapeamento
            
            # Normalizar valor (dividir por 1000)
            valor_normalizado = normalizar_valor(valor)
            if valor_normalizado is None:
                continue
            
            # Verificar prioridade de campos
            prioridade_atual = PRIORIDADE_CAMPOS.get(campo_brapi, 5)
            
            # Se já existe valor para esta conta, só sobrescrever se prioridade for maior
            if cd_conta in dados_por_trimestre[trimestre]:
                campo_existente = dados_por_trimestre[trimestre][cd_conta].get('campo', '')
                prioridade_existente = PRIORIDADE_CAMPOS.get(campo_existente, 5)
                
                if prioridade_atual <= prioridade_existente:
                    continue
            
            dados_por_trimestre[trimestre][cd_conta] = {
                'valor': valor_normalizado,
                'campo': campo_brapi
            }
    
    if not dados_por_trimestre:
        print(f"  ⚠️  Nenhum dado encontrado para os trimestres faltantes")
        return df_atual
    
    # Criar dataframe novo baseado no atual
    df_novo = df_atual.copy()
    
    # Garantir que colunas de trimestres existam (inserir com None na posição correta)
    colunas_trim = [col for col in df_novo.columns if 'T' in str(col) and len(str(col)) == 6]
    
    for trimestre in trimestres_faltantes:
        if trimestre not in df_novo.columns:
            # Encontrar posição correta baseada na ordenação
            colunas_trim_ordenadas = sorted(colunas_trim + [trimestre])
            idx_novo = colunas_trim_ordenadas.index(trimestre)
            
            if idx_novo == 0:
                # Inserir no início dos trimestres
                col_desc = 'ds_conta' if tipo == 'dre' else 'conta'
                pos = df_novo.columns.get_loc(col_desc) + 1
                df_novo.insert(pos, trimestre, None)
            else:
                # Inserir após o trimestre anterior
                trimestre_anterior = colunas_trim_ordenadas[idx_novo - 1]
                pos = df_novo.columns.get_loc(trimestre_anterior) + 1
                df_novo.insert(pos, trimestre, None)
    
    # Preencher valores nas linhas EXISTENTES (não adicionar novas linhas)
    trimestres_preenchidos = []
    valores_preenchidos = 0
    
    def _norm_cd(v):
        """Normaliza cd_conta para comparação (suporta float/int/str)."""
        if v is None:
            return ''
        try:
            if pd.isna(v):
                return ''
        except Exception:
            pass
        s = str(v).strip()
        # Se veio como float tipo '1.0' -> '1'
        if s.endswith('.0'):
            s = s[:-2]
        # Remove zeros à direita em decimais ('2.0700' -> '2.07')
        if '.' in s:
            s = s.rstrip('0').rstrip('.')
        return s
    
    # Pré-computar normalização do cd_conta do DF (evita recomputar a cada conta)
    cd_norm_series = df_novo['cd_conta'].map(_norm_cd)
    
    for trimestre, dados_contas in dados_por_trimestre.items():
        for cd_conta, info in dados_contas.items():
            valor = info['valor']
            
            # Encontrar linha existente com este cd_conta (comparação normalizada)
            cd_alvo = _norm_cd(cd_conta)
            mask = cd_norm_series == cd_alvo
            
            if mask.any():
                # NÃO sobrescrever valores já existentes: preencher só onde é NaN
                fill_mask = mask & df_novo[trimestre].isna()
                if fill_mask.any():
                    df_novo.loc[fill_mask, trimestre] = valor
                    valores_preenchidos += int(fill_mask.sum())
            else:
                # Linha não existe - NÃO ADICIONAR (conforme requisito)
                # Apenas ignorar se for relevante
                if cd_conta not in ['1', '2', '3']:
                    pass
        
        if trimestre not in trimestres_preenchidos:
            trimestres_preenchidos.append(trimestre)
    
    if not trimestres_preenchidos:
        print(f"  ⚠️  Nenhum trimestre foi preenchido")
        return df_atual
    
    # Ordenar colunas: cd_conta, descrição, trimestres ordenados
    col_desc = 'ds_conta' if tipo == 'dre' else 'conta'
    colunas_trim_final = sorted([col for col in df_novo.columns if 'T' in str(col) and len(str(col)) == 6])
    df_novo = df_novo[['cd_conta', col_desc] + colunas_trim_final]
    
    print(f"  ✅ Preenchidos {len(trimestres_preenchidos)} trimestres: {', '.join(trimestres_preenchidos[:5])}{'...' if len(trimestres_preenchidos) > 5 else ''}")
    print(f"  💾 Total de valores preenchidos: {valores_preenchidos}")
    
    return df_novo



def processar_ticker(ticker, ano_inicio=2010):
    """Processa todos os balanços de um ticker"""
    print(f"\n{'='*60}")
    print(f"🏦 Processando {ticker} {'[BANCO]' if is_banco(ticker) else '[EMPRESA]'}")
    print(f"{'='*60}")
    
    base_dir = Path('balancos') / ticker
    if not base_dir.exists():
        print(f"⚠️  Diretório não encontrado: {base_dir}")
        return False
    
    sucesso = False
    arquivos_processados = []
    
    # Lista de demonstrativos para processar
    demonstrativos = [
        ('dre', 'dre_padronizado.csv', 'incomeStatementHistoryQuarterly'),
        ('bpa', 'bpa_padronizado.csv', 'balanceSheetHistoryQuarterly'),
        ('bpp', 'bpp_padronizado.csv', 'balanceSheetHistoryQuarterly'),
    ]
    
    for tipo, arquivo, modulo in demonstrativos:
        arquivo_path = base_dir / arquivo
        
        if not arquivo_path.exists():
            continue
        
        print(f"\n📊 Processando {tipo.upper()} de {ticker}...")
        
        try:
            # Ler arquivo atual
            df_atual = pd.read_csv(arquivo_path)
            linhas_originais = len(df_atual)
            
            print(f"  📁 Arquivo atual: {linhas_originais} linhas")
            
            # Processar demonstrativo
            df_novo = processar_demonstrativo(ticker, df_atual, modulo, tipo, ano_inicio)
            
            if df_novo is not None:
                linhas_finais = len(df_novo)
                
                # VALIDAÇÃO: Número de linhas deve ser EXATAMENTE o mesmo
                if linhas_finais != linhas_originais:
                    print(f"  ⚠️  ERRO: Número de linhas mudou! Original={linhas_originais}, Novo={linhas_finais}")
                    print(f"  ❌ Abortando salvamento do {tipo.upper()} para preservar estrutura")
                    continue
                
                # Verificar se houve mudanças
                if not df_novo.equals(df_atual):
                    # Salvar arquivo
                    df_novo.to_csv(arquivo_path, index=False)
                    print(f"  💾 {tipo.upper()} salvo: {arquivo_path}")
                    print(f"  ✅ Estrutura preservada: {linhas_finais} linhas mantidas")
                    arquivos_processados.append(tipo.upper())
                    sucesso = True
                else:
                    print(f"  ℹ️  {tipo.upper()} já estava completo")
            else:
                print(f"  ⚠️  {tipo.upper()} não foi processado")
                
        except Exception as e:
            print(f"  ❌ Erro no {tipo.upper()}: {e}")
            import traceback
            traceback.print_exc()
    
    if sucesso:
        print(f"\n✅ {ticker} processado com sucesso!")
        print(f"   Arquivos atualizados: {', '.join(arquivos_processados)}")
    else:
        print(f"\n⚠️  {ticker} não teve alterações ou houve erros")
    
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
        description='Preencher balanços financeiros com dados da BRAPI - Versão 2.0'
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
    parser.add_argument('--validar-token', action='store_true',
                       help='Apenas validar token e sair')
    
    args = parser.parse_args()
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  Preencher Balanços Financeiros com BRAPI - Versão 2.0      ║")
    print("║  Suporte específico para Bancos e Empresas                  ║")
    print("║  Monalisa Research - Antonio Siqueira                        ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    # Validar token
    if not validar_token_brapi():
        print("\n❌ Falha na validação do token. Abortando.")
        sys.exit(1)
    
    # Se só quer validar, sair aqui
    if args.validar_token:
        print("\n✅ Token validado com sucesso!")
        sys.exit(0)
    
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
    
    # Separar bancos e empresas para melhor visualização
    bancos = [t for t in tickers if is_banco(t)]
    empresas = [t for t in tickers if not is_banco(t)]
    
    if bancos:
        print(f"\n  🏦 BANCOS ({len(bancos)}):")
        for i, t in enumerate(bancos, 1):
            print(f"    {i:3d}. {t}")
    
    if empresas:
        print(f"\n  🏢 EMPRESAS ({len(empresas)}):")
        for i, t in enumerate(empresas, 1):
            print(f"    {i:3d}. {t}")
    
    print(f"\n⏰ Ano de início: {args.ano_inicio}")
    print(f"📅 Processamento: {args.ano_inicio} até primeiro trimestre completo")
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
            
            # Aguardar entre requisições
            if i < len(tickers):
                time.sleep(2)
                
        except Exception as e:
            print(f"❌ Erro crítico em {ticker}: {e}")
            import traceback
            traceback.print_exc()
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
            tipo = "🏦 [BANCO]" if is_banco(t) else "🏢 [EMPRESA]"
            print(f"  • {t} {tipo}")
    
    if falhas:
        print(f"\n❌ Falhas:")
        for t in falhas:
            tipo = "🏦 [BANCO]" if is_banco(t) else "🏢 [EMPRESA]"
            print(f"  • {t} {tipo}")
    
    print(f"\n{'='*60}")
    
    # Exit code baseado em sucessos
    sys.exit(0 if sucessos else 1)


if __name__ == "__main__":
    main()
