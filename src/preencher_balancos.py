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


import re

def normalize_cd_conta(cd):
    """Normaliza cd_conta para comparação robusta (aceita '1', '1.00', 1.0, etc)."""
    if cd is None:
        return ""
    s = str(cd).strip()
    if s == "" or s.lower() == "nan":
        return ""
    s = s.replace(",", ".")
    # manter apenas dígitos e pontos
    s = re.sub(r"[^0-9.]", "", s)
    if s == "":
        return ""
    parts = s.split(".")
    if len(parts) == 1:
        return parts[0].lstrip("0") or "0"
    head = parts[0].lstrip("0") or "0"
    tail = parts[1]
    # remove zeros finais, mas preserva zeros à esquerda (ex.: '01')
    tail = tail.rstrip("0")
    if tail == "":
        return head
    return head + "." + tail


def _get_value_cell(v):
    """Considera 0, NaN e strings vazias como 'vazio' para fins de preenchimento."""
    if v is None:
        return None
    if isinstance(v, str):
        v2 = v.strip()
        if v2 == "" or v2.lower() == "nan":
            return None
        try:
            return float(v2)
        except Exception:
            return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    # tratar 0 como vazio (bug comum do padronizado)
    try:
        if float(v) == 0.0:
            return None
    except Exception:
        pass
    return v

# Token BRAPI - usar variável de ambiente (OBRIGATÓRIO)
BRAPI_TOKEN = (os.getenv('BRAPI_TOKEN', '') or '').strip()

if not BRAPI_TOKEN:
    print("❌ BRAPI_TOKEN não encontrado em variável de ambiente.")
    print("   Configure o secret BRAPI_TOKEN (ou BRAPI_TOKEN_PRO no workflow) e injete como env BRAPI_TOKEN.")
    raise SystemExit(2)

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
    # Ativo
    'totalAssets': ('1.00', 'Ativo Total'),
    'cash': ('1.01', 'Caixa e Equivalentes de Caixa'),
    'cashAndCashEquivalents': ('1.01', 'Caixa e Equivalentes de Caixa'),

    # Ativos Financeiros (genérico BRAPI)
    'shortTermInvestments': ('1.02', 'Ativos Financeiros'),
    'netReceivables': ('1.02', 'Ativos Financeiros'),

    # Tributos
    'taxesToRecover': ('1.03', 'Tributos'),
    'currentAndDeferredTaxes': ('1.03', 'Tributos'),

    # Outros Ativos
    'otherCurrentAssets': ('1.04', 'Outros Ativos'),
    'otherAssets': ('1.04', 'Outros Ativos'),

    # Investimentos / Imobilizado / Intangível
    'investments': ('1.05', 'Investimentos'),
    'longTermInvestments': ('1.05', 'Investimentos'),
    'propertyPlantEquipment': ('1.06', 'Imobilizado'),
    'intangibleAssets': ('1.07', 'Intangível'),
    'intangibleAsset': ('1.07', 'Intangível'),
}

MAPA_BPP_BANCOS = {
    # Passivo
    'totalLiab': ('2.00', 'Passivo Total'),

    # BRAPI não expõe (no schema atual) as mesmas quebras do COSIF; usamos campos genéricos
    'accountsPayable': ('2.01', 'Passivos Financeiros (genérico)'),
    'shortLongTermDebt': ('2.02', 'Passivos Financeiros ao Custo Amortizado'),
    'longTermDebt': ('2.02', 'Passivos Financeiros ao Custo Amortizado'),

    'provisions': ('2.03', 'Provisões'),
    'taxLiabilities': ('2.04', 'Passivos Fiscais'),
    'otherLiab': ('2.05', 'Outros Passivos'),

    # PL
    'totalStockholderEquity': ('2.07', 'Patrimônio Líquido Consolidado'),
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


def extrair_trimestre_ano(data_str):
    """Converte YYYY-MM-DD para YYYYTQ"""
    try:
        data = datetime.strptime(data_str, '%Y-%m-%d')
        trimestre = (data.month - 1) // 3 + 1
        return f"{data.year}T{trimestre}"
    except (ValueError, AttributeError):
        return None



# Compatibilidade: versões anteriores chamavam extrair_trimestre()
def extrair_trimestre(data_str):
    return extrair_trimestre_ano(data_str)


def identificar_primeiro_trimestre_completo(df_atual, min_ratio=0.7):
    """
    Identifica o primeiro trimestre que tem dados suficientemente preenchidos.
    IMPORTANTÍSSIMO: trata 0 como vazio (bug comum nos padronizados).
    """
    colunas_trim = [col for col in df_atual.columns if re.match(r"^\d{4}T[1-4]$", str(col))]
    if not colunas_trim:
        return None

    colunas_trim_ordenadas = sorted(colunas_trim)

    total_linhas = len(df_atual)
    if total_linhas == 0:
        return None

    for trimestre in colunas_trim_ordenadas:
        serie = df_atual[trimestre].apply(_get_value_cell)
        preenchidos = serie.notna().sum()

        if preenchidos >= total_linhas * float(min_ratio):
            return trimestre

    return None



def identificar_trimestres_faltantes(df_atual, primeiro_trimestre_completo, ano_inicio=2010):
    """
    Identifica trimestres faltantes entre ano_inicio e primeiro_trimestre_completo
    """
    if not primeiro_trimestre_completo:
        return []
    
    colunas_trim = [col for col in df_atual.columns if 'T' in str(col) and len(str(col)) == 6]
    trimestres_existentes = set(colunas_trim)
    
    # Extrair ano e trimestre do primeiro completo
    ano_limite = int(primeiro_trimestre_completo[:4])
    trim_limite = int(primeiro_trimestre_completo[5])
    
    # Gerar todos os trimestres desde ano_inicio até o primeiro completo
    todos_trimestres = []
    for ano in range(ano_inicio, ano_limite + 1):
        for trim in range(1, 5):
            trimestre = f"{ano}T{trim}"
            # Parar quando atingir o primeiro trimestre completo
            if ano == ano_limite and trim > trim_limite:
                break
            todos_trimestres.append(trimestre)
    
    # Identificar faltantes (que não existem OU que existem mas estão vazios)
    trimestres_faltantes = []
    for t in todos_trimestres:
        if t not in trimestres_existentes:
            trimestres_faltantes.append(t)
        elif t in df_atual.columns and df_atual[t].isna().all():
            # Trimestre existe mas está completamente vazio
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
    """Processa um demonstrativo (DRE, BPA ou BPP), preenchendo trimestres e contas faltantes."""

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
    if modulo not in result or not result.get(modulo):
        print(f"  ⚠️  Módulo {modulo} não disponível para {ticker}")
        return None

    dados_trimestrais = result[modulo]
    if isinstance(dados_trimestrais, dict) and modulo in dados_trimestrais and isinstance(dados_trimestrais[modulo], list):
        dados_trimestrais = dados_trimestrais[modulo]
    if not isinstance(dados_trimestrais, list):
        print(f"  ⚠️  Estrutura inesperada do módulo {modulo} para {ticker}")
        return None

    print(f"  📊 Obtidos {len(dados_trimestrais)} trimestres da BRAPI")

    # Trimestres a preencher: do ano_inicio até o primeiro trimestre completo (inclusive)
    ano_limite = int(primeiro_trimestre_completo[:4])
    trim_limite = int(primeiro_trimestre_completo[5])

    trimestres_alvo = []
    for ano in range(int(ano_inicio), ano_limite + 1):
        for trim in range(1, 5):
            trimestre = f"{ano}T{trim}"
            trimestres_alvo.append(trimestre)
            if ano == ano_limite and trim == trim_limite:
                break
        if ano == ano_limite:
            break

    # Garantir colunas de trimestre (se faltarem colunas, cria)
    df_novo = df_atual.copy()
    for t in trimestres_alvo:
        if t not in df_novo.columns:
            df_novo[t] = None

    # Mapeamento de campos BRAPI -> cd_conta do padronizado
    if is_banco(ticker):
        if tipo == 'dre':
            mapa = MAPA_DRE_BANCOS
        elif tipo == 'bpa':
            mapa = MAPA_BPA_BANCOS
        else:
            mapa = MAPA_BPP_BANCOS
    else:
        if tipo == 'dre':
            mapa = MAPA_DRE_EMPRESAS
        elif tipo == 'bpa':
            mapa = MAPA_BPA_EMPRESAS
        else:
            mapa = MAPA_BPP_EMPRESAS

    # Preparar chave normalizada de cd_conta para casar com mapeamento
    if 'cd_conta' in df_novo.columns:
        df_novo['_cd_key'] = df_novo['cd_conta'].apply(normalize_cd_conta)
    else:
        # fallback: alguns arquivos usam 'cd_conta' como primeiro campo mesmo; se não existir, não tem como preencher
        print("  ❌ Coluna cd_conta não encontrada; abortando para preservar estrutura")
        return None

    # Coletar melhor valor por (trimestre, cd_conta) respeitando prioridade
    melhores = {}  # (trimestre, cd_key) -> (prioridade, valor)

    for registro in dados_trimestrais:
        end_date = registro.get('endDate')
        if not end_date:
            continue

        trimestre = extrair_trimestre_ano(end_date)
        if not trimestre or trimestre not in trimestres_alvo:
            continue

        for campo_brapi, (cd_conta, _desc) in mapa.items():
            if campo_brapi not in registro:
                continue
            valor = registro.get(campo_brapi)
            if valor is None:
                continue

            # EPS NÃO deve ser dividido por 1000
            if campo_brapi in ('earningsPerShare', 'basicEarningsPerShare', 'dilutedEarningsPerShare'):
                try:
                    valor_norm = float(valor)
                except Exception:
                    continue
            else:
                valor_norm = normalizar_valor(valor)
                if valor_norm is None:
                    continue

            prioridade = PRIORIDADE_CAMPOS.get(campo_brapi, 1)
            key = (trimestre, normalize_cd_conta(cd_conta))

            if key not in melhores or prioridade > melhores[key][0]:
                melhores[key] = (prioridade, valor_norm)

    # Aplicar preenchimento: só preenche se célula estiver vazia (NaN/0/string vazia)
    preenchidos = 0
    for (trimestre, cd_key), (_p, valor) in melhores.items():
        if trimestre not in df_novo.columns:
            continue

        mask = df_novo['_cd_key'] == cd_key
        if not mask.any():
            continue

        for idx in df_novo.index[mask]:
            atual = _get_value_cell(df_novo.at[idx, trimestre])
            if atual is None:
                df_novo.at[idx, trimestre] = valor
                preenchidos += 1

    # Regra adicional (BANCO): 3.10 = 3.09 - 3.11 quando faltar
    if tipo == 'dre':
        cd_309 = normalize_cd_conta('3.09')
        cd_310 = normalize_cd_conta('3.10')
        cd_311 = normalize_cd_conta('3.11')

        for trimestre in trimestres_alvo:
            try:
                idx_309 = df_novo.index[df_novo['_cd_key'] == cd_309].tolist()
                idx_310 = df_novo.index[df_novo['_cd_key'] == cd_310].tolist()
                idx_311 = df_novo.index[df_novo['_cd_key'] == cd_311].tolist()
                if not idx_309 or not idx_310 or not idx_311:
                    continue

                v309 = _get_value_cell(df_novo.at[idx_309[0], trimestre])
                v310 = _get_value_cell(df_novo.at[idx_310[0], trimestre])
                v311 = _get_value_cell(df_novo.at[idx_311[0], trimestre])

                if v310 is None and (v309 is not None) and (v311 is not None):
                    df_novo.at[idx_310[0], trimestre] = float(v309) - float(v311)
                    preenchidos += 1
            except Exception:
                continue

    df_novo.drop(columns=['_cd_key'], inplace=True, errors='ignore')

    if preenchidos == 0:
        print("  ℹ️  Nenhuma célula nova foi preenchida (ou BRAPI sem dados para o intervalo)")
    else:
        print(f"  ✅ Células preenchidas: {preenchidos}")

    return df_novo




def processar_ticker(ticker, ano_inicio=2010):
    """Processa todos os balanços de um ticker. Retorna (ok, alterou)."""
    print(f"\n{'='*60}")
    print(f"🏦 Processando {ticker} {'[BANCO]' if is_banco(ticker) else '[EMPRESA]'}")
    print(f"{'='*60}")

    base_dir = Path('balancos') / ticker
    if not base_dir.exists():
        print(f"⚠️  Diretório não encontrado: {base_dir}")
        return (False, False)

    alterou = False
    erro = False
    arquivos_atualizados = []

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
            df_atual = pd.read_csv(arquivo_path, dtype={'cd_conta': str})
            linhas_originais = len(df_atual)
            print(f"  📁 Arquivo atual: {linhas_originais} linhas")

            df_novo = processar_demonstrativo(ticker, df_atual, modulo, tipo, ano_inicio)

            if df_novo is None:
                print(f"  ⚠️  {tipo.upper()} não foi processado")
                # Não é necessariamente erro fatal; BRAPI pode não ter módulo para alguns tickers.
                continue

            linhas_finais = len(df_novo)
            if linhas_finais != linhas_originais:
                print(f"  ⚠️  ERRO: Número de linhas mudou! Original={linhas_originais}, Novo={linhas_finais}")
                print(f"  ❌ Abortando salvamento do {tipo.upper()} para preservar estrutura")
                erro = True
                continue

            if not df_novo.equals(df_atual):
                df_novo.to_csv(arquivo_path, index=False)
                print(f"  💾 {tipo.upper()} salvo: {arquivo_path}")
                print(f"  ✅ Estrutura preservada: {linhas_finais} linhas mantidas")
                arquivos_atualizados.append(tipo.upper())
                alterou = True
            else:
                print(f"  ℹ️  {tipo.upper()} sem alterações (já estava preenchido para o intervalo)")

        except Exception as e:
            erro = True
            print(f"  ❌ Erro no {tipo.upper()}: {e}")
            import traceback
            traceback.print_exc()

    if erro:
        print(f"\n❌ {ticker} finalizado com erros.")
    else:
        if alterou:
            print(f"\n✅ {ticker} processado com sucesso! Arquivos atualizados: {', '.join(arquivos_atualizados)}")
        else:
            print(f"\n✅ {ticker} processado com sucesso (sem mudanças necessárias).")

    return (not erro), alterou



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
    alterados = []
    falhas = []
    
    for i, ticker in enumerate(tickers, 1):
        print(f"\n[{i}/{len(tickers)}]")
        try:
            ok, alterou = processar_ticker(ticker, args.ano_inicio)
            if ok:
                sucessos.append(ticker)
                if alterou:
                    alterados.append(ticker)
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
    print(f"✅ Processados (sem erro): {len(sucessos)}/{len(tickers)}")
    print(f"📝 Com alterações (arquivos atualizados): {len(alterados)}/{len(tickers)}")
    print(f"❌ Falhas: {len(falhas)}/{len(tickers)}")

    if alterados:
        print(f"\n📝 Tickers com arquivos atualizados:")
        for t in alterados:
            tipo = "🏦 [BANCO]" if is_banco(t) else "🏢 [EMPRESA]"
            print(f"  • {t} {tipo}")

    if falhas:
        print(f"\n❌ Falhas:")
        for t in falhas:
            tipo = "🏦 [BANCO]" if is_banco(t) else "🏢 [EMPRESA]"
            print(f"  • {t} {tipo}")

    print(f"\n{'='*60}")

    # Exit code: só falha se houve ERRO real em algum ticker
    sys.exit(0 if len(falhas) == 0 else 1)


if __name__ == "__main__":
    main()
