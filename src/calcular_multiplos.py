#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculadora de Múltiplos Financeiros - Monalytics
Versão adaptada para suportar múltiplas classes de ações por empresa
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import argparse
import sys

# ============================================================================
# CONFIGURAÇÕES GLOBAIS
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
BALANCOS_DIR = BASE_DIR / "balancos"

# Metadados dos múltiplos (mantidos do original)
MULTIPLOS_METADATA = {
    "P_L": {"nome": "P/L", "categoria": "Valuation", "unidade": "x"},
    "P_VPA": {"nome": "P/VPA", "categoria": "Valuation", "unidade": "x"},
    "EV_EBITDA": {"nome": "EV/EBITDA", "categoria": "Valuation", "unidade": "x"},
    "EV_EBIT": {"nome": "EV/EBIT", "categoria": "Valuation", "unidade": "x"},
    "EV_RECEITA": {"nome": "EV/Receita", "categoria": "Valuation", "unidade": "x"},
    "VALOR_MERCADO": {"nome": "Valor de Mercado", "categoria": "Valuation", "unidade": "R$ mil"},
    "DY": {"nome": "Dividend Yield", "categoria": "Dividendos", "unidade": "%"},
    "PAYOUT": {"nome": "Payout", "categoria": "Dividendos", "unidade": "%"},
    "ROE": {"nome": "ROE", "categoria": "Rentabilidade", "unidade": "%"},
    "ROA": {"nome": "ROA", "categoria": "Rentabilidade", "unidade": "%"},
    "ROIC": {"nome": "ROIC", "categoria": "Rentabilidade", "unidade": "%"},
    "MARGEM_EBITDA": {"nome": "Margem EBITDA", "categoria": "Rentabilidade", "unidade": "%"},
    "MARGEM_LIQUIDA": {"nome": "Margem Líquida", "categoria": "Rentabilidade", "unidade": "%"},
    "DIV_LIQ_EBITDA": {"nome": "Dív.Líq/EBITDA", "categoria": "Endividamento", "unidade": "x"},
    "DIV_LIQ_PL": {"nome": "Dív.Líq/PL", "categoria": "Endividamento", "unidade": "x"},
    "ICJ": {"nome": "Cobertura de Juros", "categoria": "Endividamento", "unidade": "x"},
    "COMPOSICAO_DIVIDA": {"nome": "% Dívida CP", "categoria": "Endividamento", "unidade": "%"},
    "LIQ_CORRENTE": {"nome": "Liquidez Corrente", "categoria": "Liquidez", "unidade": "x"},
    "LIQ_SECA": {"nome": "Liquidez Seca", "categoria": "Liquidez", "unidade": "x"},
    "LIQ_GERAL": {"nome": "Liquidez Geral", "categoria": "Liquidez", "unidade": "x"},
    "GIRO_ATIVO": {"nome": "Giro do Ativo", "categoria": "Eficiência", "unidade": "x"},
    "CICLO_CAIXA": {"nome": "Ciclo de Caixa", "categoria": "Eficiência", "unidade": "dias"},
}

# Metadados para bancos, seguradoras, holdings (mantidos do original)
MULTIPLOS_BANCOS_METADATA = {}  # Adicione conforme necessário
MULTIPLOS_HOLDINGS_SEGUROS_METADATA = {}
MULTIPLOS_SEGURADORAS_METADATA = {}

# ============================================================================
# CLASSES DE DADOS
# ============================================================================

class DadosEmpresa:
    """Estrutura para armazenar dados de uma empresa"""
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.dre: Optional[pd.DataFrame] = None
        self.bpa: Optional[pd.DataFrame] = None
        self.bpp: Optional[pd.DataFrame] = None
        self.dfc: Optional[pd.DataFrame] = None
        self.acoes: Optional[pd.DataFrame] = None
        self.dividendos: Optional[pd.DataFrame] = None
        self.precos: Optional[pd.DataFrame] = None
        self.periodos: List[str] = []
        self.padrao_fiscal: Optional[Dict] = None
        self.erros: List[str] = []

# ============================================================================
# FUNÇÕES AUXILIARES - DETECÇÃO DE CLASSES
# ============================================================================

def _detectar_classes_disponiveis(dados: DadosEmpresa) -> List[str]:
    """
    Detecta automaticamente quais classes de ticker estão disponíveis
    em precos_trimestrais.csv.

    Suporta qualquer classe (3, 4, 5, 6, 11, 33, etc.)

    Returns:
        Lista de tickers (ex: ['KLBN3', 'KLBN4', 'KLBN11'])
    """
    if dados.precos is None or dados.precos.empty:
        return []

    df = dados.precos

    # Busca coluna de Ticker
    col_ticker = None
    for c in ["Ticker", "ticker", "TICKER"]:
        if c in df.columns:
            col_ticker = c
            break

    if not col_ticker:
        print("⚠️ Coluna 'Ticker' não encontrada em precos_trimestrais.csv")
        return []

    # Extrai classes únicas
    classes = df[col_ticker].astype(str).str.upper().str.strip().unique().tolist()
    classes = [c for c in classes if c and c not in ['NAN', 'NONE', '']]

    return sorted(classes)

def _extrair_tipo_classe(ticker: str) -> Optional[str]:
    """
    Extrai o tipo de classe do ticker (últimos dígitos).

    Exemplos:
        KLBN3 → "3"
        KLBN4 → "4"
        KLBN11 → "11"
        ITSA3 → "3"
        BBDC33 → "33"

    Returns:
        String com o tipo de classe ou None
    """
    ticker_upper = ticker.upper().strip()

    # Remove letras do final para pegar apenas números
    import re
    match = re.search(r'(\d+)$', ticker_upper)

    if match:
        return match.group(1)

    return None

def _is_unit(ticker: str) -> bool:
    """
    Verifica se o ticker é uma UNIT (classe 11).

    UNITS são pacotes que combinam ações ON + PN.
    """
    tipo = _extrair_tipo_classe(ticker)
    return tipo == "11"

def _is_on(ticker: str) -> bool:
    """Verifica se é ação ordinária (classe 3)"""
    tipo = _extrair_tipo_classe(ticker)
    return tipo == "3"

def _is_pn(ticker: str) -> bool:
    """Verifica se é ação preferencial (classe 4, 5, 6, etc.)"""
    tipo = _extrair_tipo_classe(ticker)
    return tipo in ["4", "5", "6"]

# ============================================================================
# FUNÇÕES AUXILIARES - MANIPULAÇÃO DE DADOS
# ============================================================================

def _safe_divide(a: float, b: float) -> float:
    """Divisão segura que retorna np.nan em caso de erro"""
    if not (np.isfinite(a) and np.isfinite(b) and b != 0):
        return np.nan
    return a / b

def _normalizar_valor(valor: float, decimals: int = 2) -> Optional[float]:
    """Normaliza valor para JSON (converte np.nan para None)"""
    if not np.isfinite(valor):
        return None
    return round(float(valor), decimals)

def _parse_periodo(periodo: str) -> Tuple[int, int]:
    """
    Parse de período no formato YYYYTQ.

    Returns:
        Tupla (ano, trimestre)
    """
    try:
        if 'T' in periodo:
            ano_str, trim_str = periodo.split('T')
            return int(ano_str), int(trim_str)
    except:
        pass
    return 0, 0

def _ordenar_periodos(periodos: List[str]) -> List[str]:
    """Ordena lista de períodos cronologicamente"""
    return sorted(periodos, key=lambda p: _parse_periodo(p))

def _get_colunas_numericas_validas(df: pd.DataFrame) -> List[str]:
    """Retorna colunas que representam períodos (YYYYTQ)"""
    if df is None or df.empty:
        return []

    colunas = []
    for col in df.columns:
        ano, trim = _parse_periodo(str(col))
        if ano > 0 and 1 <= trim <= 4:
            colunas.append(col)

    return _ordenar_periodos(colunas)

def _periodo_anterior(periodo: str) -> str:
    """Retorna o período anterior (trimestre anterior)"""
    ano, trim = _parse_periodo(periodo)

    if trim == 1:
        return f"{ano-1}T4"
    else:
        return f"{ano}T{trim-1}"

# ============================================================================
# FUNÇÕES DE CARREGAMENTO DE DADOS
# ============================================================================

def get_pasta_balanco(ticker: str) -> Path:
    """Retorna o caminho da pasta de balanços do ticker"""
    # Remove números do final para pegar ticker base
    import re
    ticker_base = re.sub(r'\d+$', '', ticker.upper().strip())

    # Tenta encontrar pasta que começa com ticker_base
    for pasta in BALANCOS_DIR.iterdir():
        if pasta.is_dir() and pasta.name.upper().startswith(ticker_base):
            return pasta

    # Fallback: usa ticker completo
    return BALANCOS_DIR / ticker.upper().strip()

def carregar_dados_empresa(ticker: str) -> DadosEmpresa:
    """
    Carrega todos os dados necessários de uma empresa.

    Args:
        ticker: Código do ticker (ex: KLBN3, KLBN4, KLBN11)

    Returns:
        Objeto DadosEmpresa com todos os dados carregados
    """
    dados = DadosEmpresa(ticker)
    pasta = get_pasta_balanco(ticker)

    if not pasta.exists():
        dados.erros.append(f"Pasta não encontrada: {pasta}")
        return dados

    # Carrega DRE
    dre_path = pasta / "dre_padronizado.csv"
    if dre_path.exists():
        try:
            dados.dre = pd.read_csv(dre_path, encoding='utf-8-sig')
        except Exception as e:
            dados.erros.append(f"Erro ao carregar DRE: {e}")

    # Carrega BPA
    bpa_path = pasta / "bpa_padronizado.csv"
    if bpa_path.exists():
        try:
            dados.bpa = pd.read_csv(bpa_path, encoding='utf-8-sig')
        except Exception as e:
            dados.erros.append(f"Erro ao carregar BPA: {e}")

    # Carrega BPP
    bpp_path = pasta / "bpp_padronizado.csv"
    if bpp_path.exists():
        try:
            dados.bpp = pd.read_csv(bpp_path, encoding='utf-8-sig')
        except Exception as e:
            dados.erros.append(f"Erro ao carregar BPP: {e}")

    # Carrega DFC
    dfc_path = pasta / "dfc_padronizado.csv"
    if dfc_path.exists():
        try:
            dados.dfc = pd.read_csv(dfc_path, encoding='utf-8-sig')
        except Exception as e:
            dados.erros.append(f"Erro ao carregar DFC: {e}")

    # Carrega Ações
    acoes_path = pasta / "acoes_historico.csv"
    if acoes_path.exists():
        try:
            dados.acoes = pd.read_csv(acoes_path, encoding='utf-8-sig')
        except Exception as e:
            dados.erros.append(f"Erro ao carregar ações: {e}")

    # Carrega Dividendos
    div_path = pasta / "dividendos_trimestrais.csv"
    if div_path.exists():
        try:
            dados.dividendos = pd.read_csv(div_path, encoding='utf-8-sig')
        except Exception as e:
            dados.erros.append(f"Erro ao carregar dividendos: {e}")

    # Carrega Preços Trimestrais (FUNDAMENTAL PARA MÚLTIPLAS CLASSES)
    precos_path = pasta / "precos_trimestrais.csv"
    if precos_path.exists():
        try:
            dados.precos = pd.read_csv(precos_path, encoding='utf-8-sig')
        except Exception as e:
            dados.erros.append(f"Erro ao carregar preços: {e}")
    else:
        dados.erros.append("Arquivo precos_trimestrais.csv não encontrado")

    # Extrai períodos disponíveis
    if dados.dre is not None:
        dados.periodos = _get_colunas_numericas_validas(dados.dre)

    # Detecta padrão fiscal (simplificado)
    if dados.periodos:
        dados.padrao_fiscal = {"tipo": "T4", "trimestre_encerramento": 4}

    return dados

# ============================================================================
# FUNÇÕES DE OBTENÇÃO DE PREÇOS (ADAPTADAS PARA MÚLTIPLAS CLASSES)
# ============================================================================

def _obter_preco(dados: DadosEmpresa, periodo: str, ticker_classe: Optional[str] = None) -> float:
    """
    Obtém preço de fechamento ajustado do ticker específico no período.

    Args:
        dados: Dados da empresa
        periodo: Ex: "2023T4"
        ticker_classe: Ex: "KLBN3", "KLBN4", "KLBN11" (opcional)

    Returns:
        Preço de fechamento ajustado (float) ou np.nan
    """
    if dados.precos is None or dados.precos.empty:
        return np.nan

    df = dados.precos

    # Identifica coluna de Ticker
    col_ticker = None
    for c in ["Ticker", "ticker", "TICKER"]:
        if c in df.columns:
            col_ticker = c
            break

    # Se especificou classe, filtra
    if col_ticker and ticker_classe:
        ticker_upper = ticker_classe.upper().strip()
        df_filtrado = df[df[col_ticker].astype(str).str.upper().str.strip() == ticker_upper]

        if df_filtrado.empty:
            return np.nan

        df = df_filtrado

    # Verifica se o período existe
    if periodo not in df.columns:
        return np.nan

    # Obtém o preço
    preco_serie = pd.to_numeric(df[periodo], errors="coerce")

    if preco_serie.notna().any():
        return float(preco_serie.dropna().iloc[0])

    return np.nan

def _obter_preco_atual(dados: DadosEmpresa, ticker_classe: Optional[str] = None) -> Tuple[float, str]:
    """
    Obtém o último preço válido da classe específica.

    Args:
        dados: Dados da empresa
        ticker_classe: Ex: "KLBN3", "KLBN4", "KLBN11" (opcional)

    Returns:
        Tupla (preco, periodo)
    """
    if dados.precos is None or dados.precos.empty:
        return np.nan, ""

    df = dados.precos

    # Identifica coluna de ticker
    col_ticker = None
    for c in ["Ticker", "ticker", "TICKER"]:
        if c in df.columns:
            col_ticker = c
            break

    # Filtra por classe se especificado
    if col_ticker and ticker_classe:
        ticker_upper = ticker_classe.upper().strip()
        df_filtrado = df[df[col_ticker].astype(str).str.upper().str.strip() == ticker_upper]

        if df_filtrado.empty:
            return np.nan, ""

        df = df_filtrado

    # Busca coluna mais recente com preço válido
    colunas = _get_colunas_numericas_validas(df)

    for periodo in reversed(colunas):
        preco = _obter_preco(dados, periodo, ticker_classe=ticker_classe)
        if np.isfinite(preco) and preco > 0:
            return preco, periodo

    return np.nan, ""

# ============================================================================
# FUNÇÕES DE OBTENÇÃO DE AÇÕES (ADAPTADAS PARA MÚLTIPLAS CLASSES)
# ============================================================================

def _obter_acoes_especie(dados: DadosEmpresa, especie: str, periodo: str) -> float:
    """
    Obtém quantidade de ações de uma espécie (ON ou PN).

    Args:
        dados: Dados da empresa
        especie: "ON" ou "PN"
        periodo: Ex: "2023T4"

    Returns:
        Quantidade de ações em milhares
    """
    if dados.acoes is None or dados.acoes.empty:
        return np.nan

    df = dados.acoes

    # Busca linha da espécie
    especie_upper = especie.upper().strip()
    linhas = df[df.iloc[:, 0].astype(str).str.upper().str.strip() == especie_upper]

    if linhas.empty:
        return np.nan

    if periodo not in df.columns:
        return np.nan

    valor = pd.to_numeric(linhas[periodo], errors="coerce")
    if valor.notna().any():
        return float(valor.dropna().iloc[0])

    return np.nan

def _obter_acoes(dados: DadosEmpresa, periodo: str) -> float:
    """
    Obtém quantidade total de ações (ON + PN).

    Args:
        dados: Dados da empresa
        periodo: Ex: "2023T4"

    Returns:
        Quantidade total de ações em milhares
    """
    on = _obter_acoes_especie(dados, "ON", periodo)
    pn = _obter_acoes_especie(dados, "PN", periodo)

    on_val = on if np.isfinite(on) else 0
    pn_val = pn if np.isfinite(pn) else 0

    total = on_val + pn_val

    return total if total > 0 else np.nan

def _obter_acoes_para_classe(dados: DadosEmpresa, ticker_classe: str, periodo: str) -> float:
    """
    Obtém quantidade de ações adaptada por classe.

    Regras:
    - Classe 3 (ON) → apenas ações ON
    - Classe 4, 5, 6 (PN) → apenas ações PN
    - Classe 11 (UNIT) → ON + PN (pacote)
    - Classe 33 → tratamento especial se necessário

    Args:
        dados: Dados da empresa
        ticker_classe: Ex: "KLBN3", "KLBN4", "KLBN11"
        periodo: Ex: "2023T4"

    Returns:
        Quantidade de ações (em milhares)
    """
    tipo = _extrair_tipo_classe(ticker_classe)

    if not tipo:
        # Fallback: usa total
        return _obter_acoes(dados, periodo)

    # Obtém ações ON e PN
    on = _obter_acoes_especie(dados, "ON", periodo)
    pn = _obter_acoes_especie(dados, "PN", periodo)

    # UNIT (11) = pacote ON + PN
    if tipo == "11":
        on_val = on if np.isfinite(on) else 0
        pn_val = pn if np.isfinite(pn) else 0
        total = on_val + pn_val
        return total if total > 0 else np.nan

    # ON (3)
    if tipo == "3":
        return on if np.isfinite(on) else np.nan

    # PN (4, 5, 6)
    if tipo in ["4", "5", "6"]:
        return pn if np.isfinite(pn) else np.nan

    # Classe 33 ou outras: usa total
    return _obter_acoes(dados, periodo)

# ============================================================================
# FUNÇÕES DE BUSCA DE CONTAS CONTÁBEIS
# ============================================================================

def _buscar_conta_flexivel(df: pd.DataFrame, conta: str, periodo: str) -> float:
    """
    Busca valor de uma conta contábil no período.

    Args:
        df: DataFrame (DRE, BPA, BPP, etc.)
        conta: Código da conta (ex: "3.01", "1.01.01")
        periodo: Ex: "2023T4"

    Returns:
        Valor da conta ou np.nan
    """
    if df is None or df.empty:
        return np.nan

    if periodo not in df.columns:
        return np.nan

    # Busca pela coluna cd_conta ou conta
    col_conta = None
    for c in ["cd_conta", "conta", "Conta", "CD_CONTA"]:
        if c in df.columns:
            col_conta = c
            break

    if not col_conta:
        return np.nan

    # Filtra linha da conta
    linhas = df[df[col_conta].astype(str).str.strip() == conta]

    if linhas.empty:
        return np.nan

    valor = pd.to_numeric(linhas[periodo], errors="coerce")

    if valor.notna().any():
        return float(valor.dropna().iloc[0])

    return np.nan

def _obter_valor_flexivel(dados: DadosEmpresa, df: pd.DataFrame, conta: str, periodo: str) -> float:
    """Alias para _buscar_conta_flexivel"""
    return _buscar_conta_flexivel(df, conta, periodo)

# ============================================================================
# FUNÇÕES DE CÁLCULO LTM (Last Twelve Months)
# ============================================================================

def _calcular_ltm(dados: DadosEmpresa, df: pd.DataFrame, conta: str, periodo: str) -> float:
    """
    Calcula valor LTM (últimos 12 meses) de uma conta.

    Args:
        dados: Dados da empresa
        df: DataFrame (DRE, Dividendos, etc.)
        conta: Código da conta
        periodo: Período de referência (ex: "2023T4")

    Returns:
        Soma dos últimos 4 trimestres
    """
    if df is None or df.empty:
        return np.nan

    ano, trim = _parse_periodo(periodo)

    if ano == 0:
        return np.nan

    # Gera lista dos últimos 4 trimestres
    periodos_ltm = []

    for i in range(4):
        if trim - i >= 1:
            p = f"{ano}T{trim - i}"
        else:
            ano_anterior = ano - 1
            trim_anterior = 4 - (i - trim)
            p = f"{ano_anterior}T{trim_anterior}"

        periodos_ltm.append(p)

    # Soma valores
    soma = 0
    count = 0

    for p in periodos_ltm:
        valor = _buscar_conta_flexivel(df, conta, p)
        if np.isfinite(valor):
            soma += valor
            count += 1

    return soma if count == 4 else np.nan

def _calcular_ebitda_ltm(dados: DadosEmpresa, periodo: str) -> float:
    """
    Calcula EBITDA LTM.

    EBITDA = EBIT + Depreciação + Amortização
    """
    ebit_ltm = _calcular_ltm(dados, dados.dre, "3.05", periodo)

    # Busca D&A no DFC
    if dados.dfc is not None:
        da_ltm = _calcular_ltm(dados, dados.dfc, "6.01.DA", periodo)
    else:
        da_ltm = np.nan

    if np.isfinite(ebit_ltm) and np.isfinite(da_ltm):
        return ebit_ltm + da_ltm
    elif np.isfinite(ebit_ltm):
        return ebit_ltm
    else:
        return np.nan

def _calcular_divida_liquida(dados: DadosEmpresa, periodo: str) -> float:
    """
    Calcula Dívida Líquida.

    Dívida Líquida = Empréstimos CP + Empréstimos LP - Caixa - Aplicações
    """
    emp_cp = _buscar_conta_flexivel(dados.bpp, "2.01.04", periodo)
    emp_lp = _buscar_conta_flexivel(dados.bpp, "2.02.01", periodo)
    caixa = _buscar_conta_flexivel(dados.bpa, "1.01.01", periodo)
    aplicacoes = _buscar_conta_flexivel(dados.bpa, "1.01.02", periodo)

    divida_bruta = (emp_cp if np.isfinite(emp_cp) else 0) + (emp_lp if np.isfinite(emp_lp) else 0)
    disponibilidades = (caixa if np.isfinite(caixa) else 0) + (aplicacoes if np.isfinite(aplicacoes) else 0)

    return divida_bruta - disponibilidades

# ============================================================================
# FUNÇÃO PRINCIPAL DE CÁLCULO DE MÚLTIPLOS (ADAPTADA)
# ============================================================================

def calcular_multiplos_periodo(
    dados: DadosEmpresa,
    periodo: str,
    usar_preco_atual: bool = False,
    ticker_classe: Optional[str] = None
) -> Dict[str, Optional[float]]:
    """
    Calcula múltiplos financeiros para uma classe específica de ticker.

    Args:
        dados: Dados da empresa
        periodo: Período de referência (ex: "2025T4")
        usar_preco_atual: Se True, usa preço atual; senão, usa preço do período
        ticker_classe: Classe específica (ex: "KLBN3", "KLBN4", "KLBN11")

    Returns:
        Dicionário com múltiplos calculados
    """
    resultado = {}

    try:
        # ========== PREÇO E MARKET CAP (ESPECÍFICO DA CLASSE) ==========

        if usar_preco_atual:
            preco, periodo_preco = _obter_preco_atual(dados, ticker_classe=ticker_classe)
        else:
            preco = _obter_preco(dados, periodo, ticker_classe=ticker_classe)
            periodo_preco = periodo

        # Ações adaptadas por classe
        acoes_ref = _obter_acoes_para_classe(dados, ticker_classe, periodo) if ticker_classe else _obter_acoes(dados, periodo)

        # Market Cap específico da classe
        if np.isfinite(preco) and preco > 0 and np.isfinite(acoes_ref) and acoes_ref > 0:
            market_cap = float(preco * acoes_ref / 1000.0)
        else:
            market_cap = np.nan

        resultado["VALOR_MERCADO"] = _normalizar_valor(market_cap, decimals=0)

        # ========== MÚLTIPLOS DE VALUATION ==========

        # P/L
        eps_ltm = _calcular_ltm(dados, dados.dre, "3.99", periodo)
        if not (np.isfinite(eps_ltm) and eps_ltm != 0):
            ll_ltm = _calcular_ltm(dados, dados.dre, "3.11", periodo)
            eps_ltm = (ll_ltm * 1000.0) / acoes_ref if acoes_ref > 0 else np.nan

        resultado["P_L"] = _normalizar_valor(_safe_divide(preco, eps_ltm))

        # P/VPA
        pl = _buscar_conta_flexivel(dados.bpp, "2.03", periodo)
        vpa = _safe_divide((pl * 1000.0), acoes_ref) if acoes_ref > 0 else np.nan
        resultado["P_VPA"] = _normalizar_valor(_safe_divide(preco, vpa))

        # EV/EBITDA
        ebitda_ltm = _calcular_ebitda_ltm(dados, periodo)
        div_liq = _calcular_divida_liquida(dados, periodo)
        ev = market_cap + div_liq if np.isfinite(market_cap) and np.isfinite(div_liq) else np.nan
        resultado["EV_EBITDA"] = _normalizar_valor(_safe_divide(ev, ebitda_ltm))

        # EV/EBIT
        ebit_ltm = _calcular_ltm(dados, dados.dre, "3.05", periodo)
        resultado["EV_EBIT"] = _normalizar_valor(_safe_divide(ev, ebit_ltm))

        # EV/RECEITA
        receita_ltm = _calcular_ltm(dados, dados.dre, "3.01", periodo)
        resultado["EV_RECEITA"] = _normalizar_valor(_safe_divide(ev, receita_ltm))

        # ========== MÚLTIPLOS DE DIVIDENDOS ==========

        dividendos_ltm = _calcular_ltm(dados, dados.dividendos, "Dividendos_Pagos", periodo) if dados.dividendos is not None else np.nan
        dps = (dividendos_ltm * 1000.0) / acoes_ref if acoes_ref > 0 and np.isfinite(dividendos_ltm) else np.nan

        resultado["DY"] = _normalizar_valor(_safe_divide(dps, preco) * 100 if preco > 0 else np.nan)
        resultado["PAYOUT"] = _normalizar_valor(_safe_divide(dps, eps_ltm) * 100 if eps_ltm > 0 else np.nan)

        # ========== MÚLTIPLOS DE RENTABILIDADE ==========

        ll_ltm = _calcular_ltm(dados, dados.dre, "3.11", periodo)
        pl_atual = _buscar_conta_flexivel(dados.bpp, "2.03", periodo)
        pl_anterior = _buscar_conta_flexivel(dados.bpp, "2.03", _periodo_anterior(periodo))
        pl_medio = (pl_atual + pl_anterior) / 2 if np.isfinite(pl_atual) and np.isfinite(pl_anterior) else pl_atual

        resultado["ROE"] = _normalizar_valor(_safe_divide(ll_ltm, pl_medio) * 100 if pl_medio > 0 else np.nan)

        ativo_total_atual = _buscar_conta_flexivel(dados.bpa, "1", periodo)
        ativo_total_anterior = _buscar_conta_flexivel(dados.bpa, "1", _periodo_anterior(periodo))
        ativo_medio = (ativo_total_atual + ativo_total_anterior) / 2 if np.isfinite(ativo_total_atual) and np.isfinite(ativo_total_anterior) else ativo_total_atual

        resultado["ROA"] = _normalizar_valor(_safe_divide(ll_ltm, ativo_medio) * 100 if ativo_medio > 0 else np.nan)

        # ROIC
        nopat = ebit_ltm * 0.66 if np.isfinite(ebit_ltm) else np.nan
        capital_investido = pl_medio + div_liq if np.isfinite(pl_medio) and np.isfinite(div_liq) else np.nan
        resultado["ROIC"] = _normalizar_valor(_safe_divide(nopat, capital_investido) * 100 if capital_investido > 0 else np.nan)

        resultado["MARGEM_EBITDA"] = _normalizar_valor(_safe_divide(ebitda_ltm, receita_ltm) * 100 if receita_ltm > 0 else np.nan)
        resultado["MARGEM_LIQUIDA"] = _normalizar_valor(_safe_divide(ll_ltm, receita_ltm) * 100 if receita_ltm > 0 else np.nan)

        # ========== MÚLTIPLOS DE ENDIVIDAMENTO ==========

        resultado["DIV_LIQ_EBITDA"] = _normalizar_valor(_safe_divide(div_liq, ebitda_ltm))
        resultado["DIV_LIQ_PL"] = _normalizar_valor(_safe_divide(div_liq, pl_medio))

        desp_fin_ltm = _calcular_ltm(dados, dados.dre, "3.06.02", periodo)
        desp_fin_abs = abs(desp_fin_ltm) if np.isfinite(desp_fin_ltm) else np.nan
        resultado["ICJ"] = _normalizar_valor(_safe_divide(ebit_ltm, desp_fin_abs))

        emp_cp = _buscar_conta_flexivel(dados.bpp, "2.01.04", periodo) or 0
        emp_lp = _buscar_conta_flexivel(dados.bpp, "2.02.01", periodo) or 0
        div_bruta = emp_cp + emp_lp
        resultado["COMPOSICAO_DIVIDA"] = _normalizar_valor(_safe_divide(emp_cp, div_bruta) * 100 if div_bruta > 0 else np.nan)

        # ========== MÚLTIPLOS DE LIQUIDEZ ==========

        ac = _buscar_conta_flexivel(dados.bpa, "1.01", periodo)
        pc = _buscar_conta_flexivel(dados.bpp, "2.01", periodo)
        resultado["LIQ_CORRENTE"] = _normalizar_valor(_safe_divide(ac, pc))

        estoques = _buscar_conta_flexivel(dados.bpa, "1.01.04", periodo) or 0
        resultado["LIQ_SECA"] = _normalizar_valor(_safe_divide(ac - estoques, pc))

        rlp = _buscar_conta_flexivel(dados.bpa, "1.02.01", periodo) or 0
        pnc = _buscar_conta_flexivel(dados.bpp, "2.02", periodo) or 0
        resultado["LIQ_GERAL"] = _normalizar_valor(_safe_divide(ac + rlp, pc + pnc))

        # ========== MÚLTIPLOS DE EFICIÊNCIA ==========

        resultado["GIRO_ATIVO"] = _normalizar_valor(_safe_divide(receita_ltm, ativo_total_atual))

        cpv_ltm = _calcular_ltm(dados, dados.dre, "3.02", periodo)
        pme = _safe_divide(estoques * 360, cpv_ltm) if cpv_ltm > 0 else np.nan
        resultado["PME"] = _normalizar_valor(pme, decimals=0)

        contas_receber = _buscar_conta_flexivel(dados.bpa, "1.01.03", periodo) or 0
        fornecedores = _buscar_conta_flexivel(dados.bpp, "2.01.02", periodo) or 0

        pmr = _safe_divide(contas_receber * 360, receita_ltm) if receita_ltm > 0 else np.nan
        pmp = _safe_divide(fornecedores * 360, cpv_ltm) if cpv_ltm > 0 else np.nan

        ciclo = pmr + pme - pmp if np.isfinite(pmr) and np.isfinite(pme) and np.isfinite(pmp) else np.nan
        resultado["CICLO_CAIXA"] = _normalizar_valor(ciclo, decimals=0)

        return resultado

    except Exception as e:
        print(f"❌ Erro ao calcular múltiplos para {ticker_classe}: {e}")
        return {k: None for k in MULTIPLOS_METADATA.keys()}

# ============================================================================
# FUNÇÃO DE GERAÇÃO DE HISTÓRICO ANUALIZADO (ADAPTADA)
# ============================================================================

def gerar_historico_anualizado(dados: DadosEmpresa, ticker_classe: Optional[str] = None) -> Dict[str, Any]:
    """
    Gera histórico de múltiplos anualizado para uma classe específica.

    Args:
        dados: Dados da empresa
        ticker_classe: Classe específica (ex: "KLBN3", "KLBN4", "KLBN11")
    """
    if not dados.periodos or dados.padrao_fiscal is None:
        return {"erro": "Dados insuficientes", "ticker": dados.ticker}

    resultado = {
        "ticker": ticker_classe or dados.ticker,
        "ticker_classe": ticker_classe,
        "padrao_fiscal": dados.padrao_fiscal,
        "historico_anual": {},
        "ltm": {}
    }

    # Agrupa períodos por ano
    periodos_por_ano = {}
    for p in dados.periodos:
        ano, trim = _parse_periodo(p)
        if ano not in periodos_por_ano:
            periodos_por_ano[ano] = []
        periodos_por_ano[ano].append(p)

    # Calcula múltiplos para cada ano (último trimestre)
    for ano in sorted(periodos_por_ano.keys()):
        trimestres = sorted(periodos_por_ano[ano], key=lambda x: _parse_periodo(x)[1])
        periodo_referencia = trimestres[-1]  # Último trimestre do ano

        multiplos = calcular_multiplos_periodo(
            dados, 
            periodo_referencia, 
            usar_preco_atual=False, 
            ticker_classe=ticker_classe
        )

        resultado["historico_anual"][str(ano)] = {
            "periodo_referencia": periodo_referencia,
            "multiplos": multiplos
        }

    # Calcula LTM (usando preço atual)
    ultimo_periodo = dados.periodos[-1]
    multiplos_ltm = calcular_multiplos_periodo(
        dados, 
        ultimo_periodo, 
        usar_preco_atual=True, 
        ticker_classe=ticker_classe
    )

    preco_atual, periodo_preco = _obter_preco_atual(dados, ticker_classe=ticker_classe)

    resultado["ltm"] = {
        "periodo_referencia": ultimo_periodo,
        "preco_utilizado": _normalizar_valor(preco_atual),
        "periodo_preco": periodo_preco,
        "multiplos": multiplos_ltm
    }

    return resultado

# ============================================================================
# FUNÇÃO DE SALVAMENTO CSV
# ============================================================================

def _salvar_csv_historico(resultado: Dict, csv_path: Path) -> None:
    """Salva histórico de múltiplos em CSV"""
    try:
        linhas = []

        # Cabeçalho
        anos = sorted(resultado.get("historico_anual", {}).keys())
        colunas = ["Múltiplo"] + anos + ["LTM"]

        # Dados
        for multiplo_key in MULTIPLOS_METADATA.keys():
            linha = [MULTIPLOS_METADATA[multiplo_key]["nome"]]

            for ano in anos:
                valor = resultado["historico_anual"][ano]["multiplos"].get(multiplo_key)
                linha.append(valor if valor is not None else "")

            # LTM
            valor_ltm = resultado["ltm"]["multiplos"].get(multiplo_key)
            linha.append(valor_ltm if valor_ltm is not None else "")

            linhas.append(linha)

        # Cria DataFrame e salva
        df = pd.DataFrame(linhas, columns=colunas)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    except Exception as e:
        print(f"⚠️ Erro ao salvar CSV: {e}")

# ============================================================================
# FUNÇÕES DE IDENTIFICAÇÃO DE TIPO DE EMPRESA
# ============================================================================

def _is_banco(ticker: str) -> bool:
    """Verifica se é banco"""
    bancos = ["BBAS3", "ITUB4", "BBDC4", "SANB11", "BPAC11"]
    return ticker.upper() in bancos

def _is_holding_seguro(ticker: str) -> bool:
    """Verifica se é holding de seguros"""
    holdings = ["BBSE3", "PSSA3"]
    return ticker.upper() in holdings

def _is_seguradora(ticker: str) -> bool:
    """Verifica se é seguradora"""
    seguradoras = ["SULA11", "WIZC3"]
    return ticker.upper() in seguradoras

# ============================================================================
# FUNÇÃO PRINCIPAL DE PROCESSAMENTO (ADAPTADA PARA MÚLTIPLAS CLASSES)
# ============================================================================

def processar_ticker(ticker: str, salvar: bool = True) -> Tuple[bool, str, Optional[Dict]]:
    """
    Processa um ticker e calcula todos os múltiplos.
    Se o ticker tiver múltiplas classes (KLBN3, KLBN4, KLBN11), processa todas.

    Args:
        ticker: Código do ticker (ex: KLBN3, KLBN4, KLBN11, ou apenas KLBN)
        salvar: Se True, salva os arquivos JSON e CSV (padrão: True)

    Returns:
        Tupla (sucesso, mensagem, resultado_dict)
    """
    ticker_upper = ticker.upper().strip()

    # Carrega dados da empresa
    dados = carregar_dados_empresa(ticker_upper)

    if dados.erros:
        erros_str = "; ".join(dados.erros)
        return False, f"Erros ao carregar: {erros_str}", None

    if not dados.periodos:
        return False, "Nenhum período disponível", None

    # Detecta classes disponíveis
    classes = _detectar_classes_disponiveis(dados)

    if not classes:
        # Fallback: processa como ticker único
        classes = [ticker_upper]

    print(f"📊 Classes detectadas: {classes}")

    # Processa cada classe separadamente
    resultados = {}
    mensagens = []

    for classe in classes:
        print(f"\n{'='*60}")
        print(f"🔍 Processando: {classe}")
        print(f"{'='*60}")

        # Gera histórico anualizado para esta classe
        resultado = gerar_historico_anualizado(dados, ticker_classe=classe)

        resultados[classe] = resultado

        # Salvamento condicional
        if salvar:
            pasta = get_pasta_balanco(ticker_upper)
            pasta.mkdir(parents=True, exist_ok=True)

            # Salva JSON com nome específico da classe
            output_path = pasta / f"multiplos_{classe}.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2, default=str)

            # Salva CSV com nome específico da classe
            csv_path = pasta / f"multiplos_{classe}.csv"
            _salvar_csv_historico(resultado, csv_path)

            print(f"💾 Arquivos salvos: {output_path.name}, {csv_path.name}")

        # Metadados do resultado
        n_anos = len(resultado.get("historico_anual", {}))
        padrao = resultado.get("padrao_fiscal", {}).get("tipo", "?")
        ultimo = resultado.get("ltm", {}).get("periodo_referencia", "?")
        preco = resultado.get("ltm", {}).get("preco_utilizado", "?")

        # Identifica tipo de empresa
        if _is_banco(ticker_upper):
            tipo_empresa = "BANCO"
            n_multiplos = len(MULTIPLOS_BANCOS_METADATA) if MULTIPLOS_BANCOS_METADATA else len(MULTIPLOS_METADATA)
        elif _is_holding_seguro(ticker_upper):
            tipo_empresa = "HOLDING_SEGURO"
            n_multiplos = len(MULTIPLOS_HOLDINGS_SEGUROS_METADATA) if MULTIPLOS_HOLDINGS_SEGUROS_METADATA else len(MULTIPLOS_METADATA)
        elif _is_seguradora(ticker_upper):
            tipo_empresa = "SEGURADORA"
            n_multiplos = len(MULTIPLOS_SEGURADORAS_METADATA) if MULTIPLOS_SEGURADORAS_METADATA else len(MULTIPLOS_METADATA)
        else:
            tipo_empresa = "GERAL"
            n_multiplos = len(MULTIPLOS_METADATA)

        msg = (
            f"{classe}: OK | {n_anos} anos | fiscal={padrao} | LTM={ultimo} | "
            f"Preço=R${preco} | Tipo={tipo_empresa} | {n_multiplos} múltiplos"
        )

        mensagens.append(msg)
        print(f"✅ {msg}")

    # Retorna resumo consolidado
    msg_final = " | ".join(mensagens)

    return True, msg_final, resultados

# ============================================================================
# FUNÇÃO MAIN (CLI)
# ============================================================================

def main():
    """Função principal com interface de linha de comando"""
    parser = argparse.ArgumentParser(description="Calculadora de Múltiplos Financeiros")

    parser.add_argument("--modo", choices=["ticker", "lista", "quantidade", "faixa"], 
                       default="ticker", help="Modo de seleção")
    parser.add_argument("--ticker", type=str, default="", help="Ticker único")
    parser.add_argument("--lista", type=str, default="", help="Lista de tickers separados por vírgula")
    parser.add_argument("--quantidade", type=int, default=10, help="Quantidade de tickers")
    parser.add_argument("--faixa", type=str, default="1-50", help="Faixa de tickers (ex: 1-50)")
    parser.add_argument("--no-save", action="store_true", help="Não salvar arquivos (dry-run)")

    args = parser.parse_args()

    salvar = not args.no_save

    print("="*70)
    print(">>> CALCULADORA DE MÚLTIPLOS FINANCEIROS <<<")
    print("="*70)
    print(f"Modo: {args.modo} | Salvar: {salvar}")
    print("="*70)

    # Determina lista de tickers
    tickers = []

    if args.modo == "ticker" and args.ticker:
        tickers = [args.ticker]
    elif args.modo == "lista" and args.lista:
        tickers = [t.strip() for t in args.lista.split(",")]
    elif args.modo == "quantidade":
        # Busca primeiros N tickers
        pastas = sorted([p.name for p in BALANCOS_DIR.iterdir() if p.is_dir()])
        tickers = pastas[:args.quantidade]
    elif args.modo == "faixa":
        try:
            inicio, fim = map(int, args.faixa.split("-"))
            pastas = sorted([p.name for p in BALANCOS_DIR.iterdir() if p.is_dir()])
            tickers = pastas[inicio-1:fim]
        except:
            print(f"❌ Faixa inválida: {args.faixa}")
            return

    if not tickers:
        print("❌ Nenhum ticker selecionado")
        return

    print(f"📊 Processando {len(tickers)} ticker(s)...")
    print("="*70)

    # Processa cada ticker
    ok_count = 0
    erro_count = 0

    for ticker in tickers:
        try:
            sucesso, msg, _ = processar_ticker(ticker, salvar=salvar)

            if sucesso:
                print(f"✅ {ticker}: {msg}")
                ok_count += 1
            else:
                print(f"❌ {ticker}: {msg}")
                erro_count += 1

        except Exception as e:
            print(f"❌ {ticker}: ERRO - {e}")
            erro_count += 1

    print("="*70)
    print(f"RESUMO: OK={ok_count} | ERRO={erro_count}")
    print("="*70)

if __name__ == "__main__":
    main()
