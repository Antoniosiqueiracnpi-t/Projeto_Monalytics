#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calcular_multiplos.py - Versão 3.0 CORRIGIDA
============================================

BUGS CORRIGIDOS NESTA VERSÃO:
1. KLBN11 (UNIT): Valor de Mercado estava 5x maior - fator UNIT agora usa mapeamento padrão
2. PETR4 DY: Dividend Yield estava 3x maior - dividendos agora somam DPA diretamente
3. BBDC4 P/L: P/L estava com metade do valor - LPA agora usa conta 3.99 quando disponível

FÓRMULAS ALINHADAS:
- DY = (DPA_LTM / Preço) × 100 (sem conversões intermediárias)
- PAYOUT = (DPA_LTM / LPA_LTM) × 100
- P/L = Preço / LPA_LTM
- ROIC = NOPAT / (PL + Dívida BRUTA)
- Giro do Ativo = Receita / Ativo MÉDIO
- PME = Estoque MÉDIO × 360 / CPV

Autor: Antonio Siqueira / Monalisa Research
Data: Janeiro 2026
"""

import os
import sys
import json
import re
import warnings
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np

warnings.filterwarnings("ignore", category=FutureWarning)

# ======================================================================================
# CONFIGURAÇÕES
# ======================================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
BASE_DIR = SCRIPT_DIR.parent

TAXA_IR_NOPAT = 0.34  # 25% IR + 9% CSLL

# Empresas com múltiplas classes de ações (UNIT)
# Mapeamento: ticker -> fator da UNIT (quantas ações por UNIT)
FATOR_UNIT_PADRAO = {
    "KLBN": 5,   # KLBN11 = 1 ON + 4 PN = 5 ações
    "BPAC": 3,   # BPAC11 = 1 ON + 2 PN = 3 ações
    "SANB": 2,   # SANB11 = 1 ON + 1 PN = 2 ações
    "TAEE": 2,   # TAEE11 = 1 ON + 1 PN = 2 ações
    "ALUP": 2,   # ALUP11 = 1 ON + 1 PN = 2 ações
    "ENGI": 2,   # ENGI11 = 1 ON + 1 PN = 2 ações
    "SAPR": 2,   # SAPR11 = 1 ON + 1 PN = 2 ações
    "SULA": 2,   # SULA11 = 1 ON + 1 PN = 2 ações
}

# Bancos (usam estrutura contábil diferente)
BANCOS = {
    "ITUB", "BBDC", "BBAS", "SANB", "ITSA", "BPAC", "ABCB", "BPAN", 
    "BRSR", "BMGB", "BIDI", "BMIN", "PINE", "BGIP", "BSLI", "MODL",
    "BPAR", "BAZA"
}

# Holdings de Seguros
HOLDINGS_SEGUROS = {"BBSE", "CXSE"}

# Seguradoras
SEGURADORAS = {"PSSA", "SULA", "IRBR", "CSAB", "WIZC", "BBSE", "CXSE"}

# Contas DRE padrão
CONTAS_DRE = {
    "receita": "3.01",
    "custo": "3.02",
    "lucro_bruto": "3.03",
    "ebit": "3.05",
    "lucro_liquido": "3.11",
    "lpa": "3.99",           # Lucro por Ação (CVM)
    "resultado_financeiro": "3.06",
    "despesa_financeira": "3.06.02",
}

# Contas BPA padrão
CONTAS_BPA = {
    "ativo_total": "1",
    "ativo_circulante": "1.01",
    "caixa": "1.01.01",
    "aplicacoes": "1.01.02",
    "contas_receber": "1.01.03",
    "estoques": "1.01.04",
    "realizavel_lp": "1.02",
}

# Contas BPP padrão
CONTAS_BPP = {
    "passivo_circulante": "2.01",
    "emprestimos_cp": "2.01.04",
    "fornecedores": "2.01.02",
    "passivo_nao_circulante": "2.02",
    "emprestimos_lp": "2.02.01",
    "patrimonio_liquido": "2.03",
}

# Contas DRE Bancos
CONTAS_DRE_BANCOS = {
    "receita_intermediacao": "3.01",
    "despesa_intermediacao": "3.02",
    "resultado_bruto": "3.03",
    "resultado_operacional": "3.05",
    "lucro_liquido": "3.11",
    "lpa": "3.99",
}

# Contas BPA Bancos
CONTAS_BPA_BANCOS = {
    "ativo_total": "1",
    "disponibilidades": "1.01.01",
    "titulos_valores": "1.02",
    "operacoes_credito": "1.03",
}

# Contas BPP Bancos (PL pode estar em 2.07 ou 2.08)
CONTAS_BPP_BANCOS = {
    "patrimonio_liquido_1": "2.07",
    "patrimonio_liquido_2": "2.08",
}


# ======================================================================================
# ESTRUTURAS DE DADOS
# ======================================================================================

@dataclass
class PadraoFiscal:
    """Representa o padrão fiscal detectado."""
    tipo: str = "PADRAO"  # PADRAO, MAR_FEV, SEMESTRAL, IRREGULAR
    trimestres_disponiveis: List[str] = field(default_factory=list)
    n_periodos_ltm: int = 4


@dataclass
class DadosEmpresa:
    """Container para todos os dados de uma empresa."""
    ticker: str = ""
    dre: Optional[pd.DataFrame] = None
    bpa: Optional[pd.DataFrame] = None
    bpp: Optional[pd.DataFrame] = None
    dfc: Optional[pd.DataFrame] = None
    precos: Optional[pd.DataFrame] = None
    acoes: Optional[pd.DataFrame] = None
    dividendos: Optional[pd.DataFrame] = None
    padrao_fiscal: Optional[PadraoFiscal] = None
    periodos: List[str] = field(default_factory=list)


# ======================================================================================
# FUNÇÕES UTILITÁRIAS
# ======================================================================================

def _safe_divide(a: float, b: float) -> float:
    """Divisão segura que retorna np.nan se b for zero ou inválido."""
    if not np.isfinite(a) or not np.isfinite(b) or b == 0:
        return np.nan
    return a / b


def _normalizar_valor(valor: float, decimals: int = 4) -> Optional[float]:
    """Normaliza valor para saída, retornando None se inválido."""
    if not np.isfinite(valor):
        return None
    return round(float(valor), decimals)


def _parse_periodo(periodo: str) -> Tuple[int, str]:
    """Extrai ano e trimestre de um período."""
    if not periodo:
        return 0, ""
    periodo = str(periodo).upper().strip()
    match = re.match(r'^(\d{4})T([1-4])$', periodo)
    if match:
        return int(match.group(1)), f"T{match.group(2)}"
    return 0, ""


def _extrair_classe_ticker(ticker: str) -> str:
    """Extrai a classe numérica do ticker (ex.: KLBN11 -> '11', PETR4 -> '4')."""
    ticker = (ticker or "").upper().strip()
    if len(ticker) < 5:
        return ""
    classe = ticker[4:]
    if classe.isdigit():
        return classe
    return ""


def _classificar_tipo_ticker(classe: str) -> str:
    """Classifica o tipo de ação pela classe numérica."""
    if classe == "3":
        return "ON"
    elif classe in {"4", "5", "6", "7", "8"}:
        return "PN"
    elif classe == "11":
        return "UNIT"
    return "OUTRO"


def _eh_banco(ticker: str) -> bool:
    """Verifica se o ticker é de um banco."""
    raiz = (ticker or "").upper().strip()[:4]
    return raiz in BANCOS


def _eh_holding_seguros(ticker: str) -> bool:
    """Verifica se o ticker é de uma holding de seguros."""
    raiz = (ticker or "").upper().strip()[:4]
    return raiz in HOLDINGS_SEGUROS


def _eh_seguradora(ticker: str) -> bool:
    """Verifica se o ticker é de uma seguradora."""
    raiz = (ticker or "").upper().strip()[:4]
    return raiz in SEGURADORAS


def _get_colunas_numericas_validas(df: pd.DataFrame) -> List[str]:
    """Retorna lista de colunas que são períodos válidos (YYYYT[1-4])."""
    if df is None or df.empty:
        return []
    colunas = []
    for c in df.columns:
        ano, tri = _parse_periodo(str(c))
        if ano > 0:
            colunas.append(str(c))
    return sorted(colunas)


def _extrair_valor_conta(df: pd.DataFrame, cd_conta: str, periodo: str) -> float:
    """Extrai valor de uma conta em um período específico."""
    if df is None or df.empty or 'cd_conta' not in df.columns:
        return np.nan
    if periodo not in df.columns:
        return np.nan
    
    mask = df['cd_conta'].astype(str).str.startswith(cd_conta)
    if mask.any():
        val = pd.to_numeric(df.loc[mask, periodo], errors='coerce').dropna()
        if len(val) > 0:
            return float(val.iloc[0])
    return np.nan


def _buscar_conta_flexivel(df: pd.DataFrame, codigos: List[str], periodo: str) -> float:
    """Busca valor em uma lista de códigos de conta, retornando o primeiro encontrado."""
    for cd in codigos:
        val = _extrair_valor_conta(df, cd, periodo)
        if np.isfinite(val):
            return val
    return np.nan


# ======================================================================================
# FUNÇÕES DE PREÇO E AÇÕES
# ======================================================================================

def _obter_preco(dados: DadosEmpresa, periodo: str, ticker_preco: Optional[str] = None) -> float:
    """Obtém preço de fechamento para um período específico."""
    if dados.precos is None or dados.precos.empty:
        return np.nan
    
    ticker_preco = (ticker_preco or dados.ticker or "").upper().strip()
    if not ticker_preco:
        return np.nan
    
    df = dados.precos
    
    # Verificar se tem coluna Ticker
    col_ticker = None
    for c in ["Ticker", "ticker", "TICKER"]:
        if c in df.columns:
            col_ticker = c
            break
    
    if col_ticker:
        mask = df[col_ticker].astype(str).str.upper().str.strip() == ticker_preco
        if mask.any():
            if periodo in df.columns:
                val = pd.to_numeric(df.loc[mask, periodo], errors='coerce').dropna()
                if len(val) > 0:
                    return float(val.iloc[0])
    else:
        # Arquivo sem coluna Ticker (uma linha só)
        if periodo in df.columns:
            val = pd.to_numeric(df[periodo], errors='coerce').dropna()
            if len(val) > 0:
                return float(val.iloc[0])
    
    return np.nan


def _obter_preco_atual(dados: DadosEmpresa, ticker_preco: Optional[str] = None) -> Tuple[float, str]:
    """Obtém preço mais recente disponível."""
    if dados.precos is None or dados.precos.empty:
        return np.nan, ""
    
    periodos = _get_colunas_numericas_validas(dados.precos)
    if not periodos:
        return np.nan, ""
    
    for periodo in reversed(periodos):
        preco = _obter_preco(dados, periodo, ticker_preco)
        if np.isfinite(preco) and preco > 0:
            return preco, periodo
    
    return np.nan, ""


def _obter_acoes_especie(dados: DadosEmpresa, especie: str, periodo: str) -> float:
    """Obtém quantidade de ações de uma espécie específica (ON, PN, UNIT)."""
    if dados.acoes is None or dados.acoes.empty:
        return np.nan
    
    df = dados.acoes
    especie = especie.upper().strip()
    
    col_especie = None
    for c in ["Especie", "especie", "ESPECIE", "Tipo", "tipo"]:
        if c in df.columns:
            col_especie = c
            break
    
    if not col_especie:
        return np.nan
    
    mask = df[col_especie].astype(str).str.upper().str.strip() == especie
    if mask.any() and periodo in df.columns:
        val = pd.to_numeric(df.loc[mask, periodo], errors='coerce').dropna()
        if len(val) > 0:
            return float(val.iloc[0])
    
    return np.nan


def _obter_acoes_total_ex11(dados: DadosEmpresa, periodo: str) -> float:
    """
    Obtém total de ações ON + PN, EXCLUINDO UNIT (classe 11).
    Isso evita dupla contagem quando existe UNIT.
    """
    on = _obter_acoes_especie(dados, "ON", periodo)
    pn = _obter_acoes_especie(dados, "PN", periodo)
    
    on_val = on if np.isfinite(on) else 0
    pn_val = pn if np.isfinite(pn) else 0
    
    total = on_val + pn_val
    return total if total > 0 else np.nan


def _obter_acoes_unit(dados: DadosEmpresa, periodo: str) -> float:
    """Obtém quantidade de UNITs (se existir no acoes_historico.csv)."""
    for rotulo in ["UNIT", "UNITS", "UNT"]:
        v = _obter_acoes_especie(dados, rotulo, periodo)
        if np.isfinite(v) and v > 0:
            return float(v)
    return np.nan


def _obter_acoes(dados: DadosEmpresa, periodo: str) -> float:
    """Obtém total de ações (ON + PN, excluindo UNIT)."""
    return _obter_acoes_total_ex11(dados, periodo)


def _obter_acoes_atual(dados: DadosEmpresa) -> Tuple[float, str]:
    """Obtém número de ações mais recente (ON + PN)."""
    if dados.acoes is None or dados.acoes.empty:
        return np.nan, ""
    
    periodos = _get_colunas_numericas_validas(dados.acoes)
    if not periodos:
        return np.nan, ""
    
    for periodo in reversed(periodos):
        acoes = _obter_acoes_total_ex11(dados, periodo)
        if np.isfinite(acoes) and acoes > 0:
            return acoes, periodo
    
    return np.nan, ""


def _calcular_fator_unit_pacote(dados: DadosEmpresa, periodo: str) -> int:
    """
    Calcula fator da UNIT: quantas ações (ON+PN) correspondem a 1 UNIT.
    
    CORREÇÃO v3.0: Usa mapeamento padrão quando não consegue calcular do arquivo.
    """
    # Primeiro, tentar calcular do arquivo de ações
    total_ex11 = _obter_acoes_total_ex11(dados, periodo)
    units = _obter_acoes_unit(dados, periodo)
    
    if np.isfinite(total_ex11) and total_ex11 > 0 and np.isfinite(units) and units > 0:
        f = total_ex11 / units
        f_int = int(round(f))
        if f_int >= 1 and abs(f - f_int) <= 0.15:
            return f_int
        return max(1, int(round(f)))
    
    # CORREÇÃO v3.0: Usar mapeamento padrão
    raiz = (dados.ticker or "").upper().strip()[:4]
    if raiz in FATOR_UNIT_PADRAO:
        return FATOR_UNIT_PADRAO[raiz]
    
    return 1


def _ajustar_acoes_para_ticker_preco(
    dados: DadosEmpresa, 
    periodo: str, 
    ticker_preco: Optional[str]
) -> Tuple[float, str, int]:
    """
    Retorna (acoes_equivalentes, periodo_usado, fator_unit).
    
    CORREÇÃO v3.0:
    - Para UNIT (classe 11): converte ON+PN para quantidade de UNITs usando fator correto
    - Para ON/PN: retorna quantidade específica da espécie
    """
    ticker_preco = (ticker_preco or dados.ticker or "").upper().strip()
    classe = _extrair_classe_ticker(ticker_preco)
    
    # Encontrar período com dados
    periodos = _get_colunas_numericas_validas(dados.acoes) if dados.acoes is not None else []
    periodo_use = periodo if periodo in periodos else (periodos[-1] if periodos else periodo)
    
    if classe == "11":
        # UNIT: converter ON+PN para quantidade de UNITs
        # Primeiro tentar usar linha UNIT diretamente
        a_unit = _obter_acoes_unit(dados, periodo_use)
        if np.isfinite(a_unit) and a_unit > 0:
            fator = _calcular_fator_unit_pacote(dados, periodo_use)
            return float(a_unit), periodo_use, fator
        
        # Fallback: dividir ON+PN pelo fator
        total_ex11 = _obter_acoes_total_ex11(dados, periodo_use)
        fator = _calcular_fator_unit_pacote(dados, periodo_use)
        
        if np.isfinite(total_ex11) and total_ex11 > 0 and fator >= 1:
            return float(total_ex11 / fator), periodo_use, fator
        
        return np.nan, periodo_use, fator
    
    elif classe == "3":
        # ON: retorna apenas ações ON
        a = _obter_acoes_especie(dados, "ON", periodo_use)
        return float(a) if np.isfinite(a) else np.nan, periodo_use, 1
    
    elif classe in {"4", "5", "6", "7", "8"}:
        # PN: retorna apenas ações PN
        a = _obter_acoes_especie(dados, "PN", periodo_use)
        return float(a) if np.isfinite(a) else np.nan, periodo_use, 1
    
    else:
        # Outros: ON + PN
        a = _obter_acoes_total_ex11(dados, periodo_use)
        return float(a) if np.isfinite(a) else np.nan, periodo_use, 1


# ======================================================================================
# MARKET CAP E ENTERPRISE VALUE
# ======================================================================================

def _calcular_market_cap(dados: DadosEmpresa, periodo: str, ticker_preco: Optional[str] = None) -> float:
    """
    Calcula Market Cap (R$ mil) para um período.
    
    CORREÇÃO v3.0:
    - Para UNIT: usa ações equivalentes em UNIT corretamente
    - Para ON/PN: usa ações da espécie específica
    """
    if not periodo:
        return np.nan
    
    if ticker_preco:
        tpx = str(ticker_preco).upper().strip()
        classe = _extrair_classe_ticker(tpx)
        preco = _obter_preco(dados, periodo, tpx)
        
        if not (np.isfinite(preco) and preco > 0):
            return np.nan
        
        # Obter ações ajustadas para o ticker de preço
        acoes, _, _ = _ajustar_acoes_para_ticker_preco(dados, periodo, tpx)
        
        if np.isfinite(acoes) and acoes > 0:
            return float((preco * acoes) / 1000.0)
        return np.nan
    
    # Modo empresa: soma VM de ON e PN
    ticker = (dados.ticker or "").upper().strip()
    if len(ticker) < 4:
        return np.nan
    
    raiz = ticker[:4]
    
    # Buscar preços de ON e PN
    p_on = _obter_preco(dados, periodo, f"{raiz}3")
    p_pn = _obter_preco(dados, periodo, f"{raiz}4")
    
    a_on = _obter_acoes_especie(dados, "ON", periodo)
    a_pn = _obter_acoes_especie(dados, "PN", periodo)
    
    parts = []
    if np.isfinite(p_on) and p_on > 0 and np.isfinite(a_on) and a_on > 0:
        parts.append(p_on * a_on)
    if np.isfinite(p_pn) and p_pn > 0 and np.isfinite(a_pn) and a_pn > 0:
        parts.append(p_pn * a_pn)
    
    if parts:
        return float(sum(parts) / 1000.0)
    
    # Fallback
    preco = _obter_preco(dados, periodo, ticker)
    acoes = _obter_acoes_total_ex11(dados, periodo)
    if np.isfinite(preco) and preco > 0 and np.isfinite(acoes) and acoes > 0:
        return float((preco * acoes) / 1000.0)
    
    return np.nan


def _calcular_market_cap_atual(dados: DadosEmpresa, ticker_preco: Optional[str] = None) -> float:
    """Calcula Market Cap atual (R$ mil)."""
    preco, periodo = _obter_preco_atual(dados, ticker_preco)
    if not np.isfinite(preco):
        return np.nan
    
    if ticker_preco:
        acoes, _, _ = _ajustar_acoes_para_ticker_preco(dados, periodo or "9999T4", ticker_preco)
    else:
        acoes, _ = _obter_acoes_atual(dados)
    
    if np.isfinite(acoes) and acoes > 0:
        return float((preco * acoes) / 1000.0)
    
    return np.nan


def _calcular_ev(dados: DadosEmpresa, periodo: str, market_cap: Optional[float] = None) -> float:
    """
    Calcula Enterprise Value (R$ mil).
    EV = Market Cap + Dívida Líquida
    """
    if market_cap is None:
        market_cap = _calcular_market_cap_atual(dados)
    
    if not np.isfinite(market_cap):
        return np.nan
    
    # Buscar empréstimos (CP e LP) com fallback para debêntures
    emp_cp = _buscar_conta_flexivel(dados.bpp, ["2.01.04", "2.01.04.01", "2.01.05"], periodo) if dados.bpp is not None else np.nan
    emp_lp = _buscar_conta_flexivel(dados.bpp, ["2.02.01", "2.02.01.01", "2.02.02"], periodo) if dados.bpp is not None else np.nan
    caixa = _extrair_valor_conta(dados.bpa, "1.01.01", periodo) if dados.bpa is not None else np.nan
    aplic = _extrair_valor_conta(dados.bpa, "1.01.02", periodo) if dados.bpa is not None else np.nan
    
    emp_cp = emp_cp if np.isfinite(emp_cp) else 0
    emp_lp = emp_lp if np.isfinite(emp_lp) else 0
    caixa = caixa if np.isfinite(caixa) else 0
    aplic = aplic if np.isfinite(aplic) else 0
    
    divida_liquida = emp_cp + emp_lp - caixa - aplic
    
    return market_cap + divida_liquida


# ======================================================================================
# CÁLCULOS LTM (Last Twelve Months)
# ======================================================================================

def _calcular_ltm(
    dados: DadosEmpresa,
    df: pd.DataFrame,
    cd_conta: str,
    periodo_fim: str,
    codigos_alternativos: Optional[List[str]] = None
) -> float:
    """Calcula valor LTM (últimos 12 meses) para uma conta."""
    if df is None or dados.padrao_fiscal is None:
        return np.nan
    
    periodos = dados.periodos
    if periodo_fim not in periodos:
        return np.nan
    
    idx_fim = periodos.index(periodo_fim)
    padrao = dados.padrao_fiscal
    
    # Determinar quantos períodos somar
    if padrao.tipo == 'SEMESTRAL':
        n_periodos = 3
    else:
        n_periodos = 4
    
    # Selecionar períodos para LTM
    start_idx = max(0, idx_fim - n_periodos + 1)
    periodos_ltm = periodos[start_idx:idx_fim + 1]
    
    soma = 0.0
    count_valid = 0
    
    for p in periodos_ltm:
        if codigos_alternativos:
            val = _buscar_conta_flexivel(df, [cd_conta] + codigos_alternativos, p)
        else:
            val = _extrair_valor_conta(df, cd_conta, p)
        
        if np.isfinite(val):
            soma += val
            count_valid += 1
    
    # Exigir número mínimo de períodos válidos
    min_periodos = n_periodos
    if count_valid < min_periodos:
        return np.nan
    
    return soma


def _obter_valor_pontual(
    df: pd.DataFrame,
    cd_conta: str,
    periodo: str,
    codigos_alternativos: Optional[List[str]] = None
) -> float:
    """Obtém valor pontual (balanço) de uma conta em um período."""
    if codigos_alternativos:
        return _buscar_conta_flexivel(df, [cd_conta] + codigos_alternativos, periodo)
    return _extrair_valor_conta(df, cd_conta, periodo)


def _obter_valor_medio(
    dados: DadosEmpresa,
    df: pd.DataFrame,
    cd_conta: str,
    periodo_fim: str,
    codigos_alternativos: Optional[List[str]] = None
) -> float:
    """
    Calcula média entre período atual e 4 trimestres atrás.
    CORREÇÃO v3.0: Usado para Giro do Ativo, PME, ROE, ROA.
    """
    if df is None:
        return np.nan
    
    periodos = dados.periodos
    if periodo_fim not in periodos:
        return np.nan
    
    idx_fim = periodos.index(periodo_fim)
    val_atual = _obter_valor_pontual(df, cd_conta, periodo_fim, codigos_alternativos)
    
    if idx_fim >= 4:
        periodo_ant = periodos[idx_fim - 4]
        val_ant = _obter_valor_pontual(df, cd_conta, periodo_ant, codigos_alternativos)
    else:
        val_ant = np.nan
    
    if np.isfinite(val_atual) and np.isfinite(val_ant):
        return (val_atual + val_ant) / 2
    
    return val_atual


# ======================================================================================
# CÁLCULO DE DIVIDENDOS E LPA - CORREÇÃO v3.0
# ======================================================================================

def _obter_dpa_periodo(dados: DadosEmpresa, periodo: str) -> float:
    """
    Obtém Dividendo por Ação (DPA) de um período específico.
    
    CORREÇÃO v3.0: Retorna DPA diretamente do arquivo de dividendos, 
    sem conversões intermediárias.
    """
    if dados.dividendos is None:
        return np.nan
    
    if periodo not in dados.dividendos.columns:
        return np.nan
    
    vals = pd.to_numeric(dados.dividendos[periodo], errors='coerce').dropna()
    if len(vals) > 0:
        return float(vals.iloc[0])
    
    return np.nan


def _calcular_dpa_ltm(dados: DadosEmpresa, periodo_fim: str) -> float:
    """
    Calcula DPA LTM (Dividendo por Ação dos últimos 12 meses).
    
    CORREÇÃO v3.0: Soma DPA diretamente dos 4 trimestres, sem multiplicar/dividir por ações.
    
    Fórmula: DPA_LTM = DPA_T1 + DPA_T2 + DPA_T3 + DPA_T4
    """
    if dados.dividendos is None:
        return np.nan
    
    ano_fim, tri_fim = _parse_periodo(periodo_fim)
    if ano_fim == 0:
        return np.nan
    
    tri_num = {'T1': 1, 'T2': 2, 'T3': 3, 'T4': 4}.get(tri_fim, 0)
    if tri_num == 0:
        return np.nan
    
    # Construir lista de 4 períodos para LTM
    periodos_ltm = []
    
    # Ano atual: T1 até T_fim
    for t in range(1, tri_num + 1):
        periodos_ltm.append(f"{ano_fim}T{t}")
    
    # Ano anterior: T(tri_fim + 1) até T4
    for t in range(tri_num + 1, 5):
        periodos_ltm.append(f"{ano_fim - 1}T{t}")
    
    # Somar DPA de todos os períodos
    soma_dpa = 0.0
    count_valid = 0
    
    for p in periodos_ltm:
        dpa = _obter_dpa_periodo(dados, p)
        if np.isfinite(dpa) and dpa >= 0:
            soma_dpa += dpa
            count_valid += 1
    
    # Se não encontrou nenhum período válido, retorna nan
    if count_valid == 0:
        return np.nan
    
    return soma_dpa


def _obter_lpa_periodo(dados: DadosEmpresa, periodo: str) -> float:
    """
    Obtém Lucro por Ação (LPA) de um período.
    LPA está na conta 3.99 do DRE (calculado pela CVM).
    """
    if dados.dre is None:
        return np.nan
    
    return _extrair_valor_conta(dados.dre, "3.99", periodo)


def _calcular_lpa_ltm(dados: DadosEmpresa, periodo_fim: str) -> float:
    """
    Calcula LPA LTM usando conta 3.99.
    
    CORREÇÃO v3.0: Prioriza conta 3.99 (LPA CVM) em vez de calcular manualmente.
    """
    return _calcular_ltm(dados, dados.dre, "3.99", periodo_fim)


def _calcular_dividendos_ltm(dados: DadosEmpresa, periodo_fim: str) -> float:
    """
    Calcula dividendos totais LTM em R$ mil.
    
    CORREÇÃO v3.0: Usa DPA_LTM × ações atuais para obter dividendos totais.
    Usado apenas internamente quando necessário calcular total em R$.
    """
    dpa_ltm = _calcular_dpa_ltm(dados, periodo_fim)
    if not np.isfinite(dpa_ltm):
        return np.nan
    
    acoes, _ = _obter_acoes_atual(dados)
    if not np.isfinite(acoes) or acoes <= 0:
        return np.nan
    
    # DPA × ações = total em R$, dividido por 1000 = R$ mil
    return (dpa_ltm * acoes) / 1000.0


# ======================================================================================
# CÁLCULO DE EBITDA
# ======================================================================================

def _calcular_da_periodo(dados: DadosEmpresa, periodo: str) -> float:
    """Calcula D&A (Depreciação e Amortização) de um período."""
    if dados.dfc is None or periodo not in dados.dfc.columns:
        return np.nan
    
    dfc = dados.dfc
    if 'cd_conta' not in dfc.columns:
        return np.nan
    
    # Prioridade: códigos específicos de D&A
    for cd in ["6.01.DA", "6.01.01.02", "6.01.01.01"]:
        val = _extrair_valor_conta(dfc, cd, periodo)
        if np.isfinite(val):
            return abs(val)
    
    return np.nan


def _calcular_ebitda_periodo(dados: DadosEmpresa, periodo: str) -> float:
    """Calcula EBITDA de um período (EBIT + D&A)."""
    ebit = _extrair_valor_conta(dados.dre, CONTAS_DRE["ebit"], periodo)
    da = _calcular_da_periodo(dados, periodo)
    
    if np.isfinite(ebit):
        if np.isfinite(da):
            return ebit + da
        return ebit  # Fallback: EBITDA ≈ EBIT
    
    return np.nan


def _calcular_ebitda_ltm(dados: DadosEmpresa, periodo_fim: str) -> float:
    """Calcula EBITDA LTM."""
    if dados.dre is None or dados.padrao_fiscal is None:
        return np.nan
    
    periodos = dados.periodos
    if periodo_fim not in periodos:
        return np.nan
    
    idx_fim = periodos.index(periodo_fim)
    n_periodos = 3 if dados.padrao_fiscal.tipo == 'SEMESTRAL' else 4
    
    start_idx = max(0, idx_fim - n_periodos + 1)
    periodos_ltm = periodos[start_idx:idx_fim + 1]
    
    soma = 0.0
    count_valid = 0
    
    for p in periodos_ltm:
        val = _calcular_ebitda_periodo(dados, p)
        if np.isfinite(val):
            soma += val
            count_valid += 1
    
    if count_valid < n_periodos:
        return np.nan
    
    return soma


# ======================================================================================
# DETECTOR DE CÓDIGO PL PARA BANCOS
# ======================================================================================

def _detectar_codigo_pl_banco(dados: DadosEmpresa, periodo: str) -> str:
    """
    Detecta se PL do banco está em 2.07 ou 2.08.
    
    CORREÇÃO v3.0: Verifica qual conta tem valor válido.
    """
    if dados.bpp is None:
        return "2.07"
    
    for cd in ["2.07", "2.08"]:
        val = _extrair_valor_conta(dados.bpp, cd, periodo)
        if np.isfinite(val) and val > 0:
            return cd
    
    return "2.07"


# ======================================================================================
# CALCULADORA PRINCIPAL - EMPRESAS NÃO-FINANCEIRAS
# ======================================================================================

def calcular_multiplos_empresa(
    dados: DadosEmpresa, 
    periodo: str, 
    usar_preco_atual: bool = True,
    ticker_preco: Optional[str] = None
) -> Dict[str, Optional[float]]:
    """
    Calcula 24 múltiplos para empresas não-financeiras.
    
    CORREÇÃO v3.0:
    - DY: (DPA_LTM / Preço) × 100
    - PAYOUT: (DPA_LTM / LPA_LTM) × 100
    - ROIC: NOPAT / (PL + Dívida BRUTA)
    - Giro do Ativo: Receita / Ativo MÉDIO
    - PME: Estoque MÉDIO × 360 / CPV
    """
    resultado: Dict[str, Optional[float]] = {}
    
    # ==================== MARKET CAP E EV ====================
    
    if usar_preco_atual:
        market_cap = _calcular_market_cap_atual(dados, ticker_preco)
    else:
        market_cap = _calcular_market_cap(dados, periodo, ticker_preco)
    
    resultado["VALOR_MERCADO"] = _normalizar_valor(market_cap, decimals=2)
    
    ev = _calcular_ev(dados, periodo, market_cap)
    
    # ==================== DADOS BASE ====================
    
    # Lucro Líquido LTM
    ll_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["lucro_liquido"], periodo)
    
    # Ações ajustadas para o ticker de preço
    acoes_ref, periodo_acoes, fator_unit = _ajustar_acoes_para_ticker_preco(dados, periodo, ticker_preco)
    
    # Preço
    if usar_preco_atual:
        preco, periodo_preco = _obter_preco_atual(dados, ticker_preco)
    else:
        preco = _obter_preco(dados, periodo, ticker_preco)
        periodo_preco = periodo
    
    # ==================== P/L ====================
    
    # CORREÇÃO v3.0: Priorizar conta 3.99 (LPA CVM)
    lpa_ltm = _calcular_lpa_ltm(dados, periodo)
    
    # Se LPA da CVM não disponível, calcular manualmente
    if not np.isfinite(lpa_ltm) or lpa_ltm == 0:
        if np.isfinite(ll_ltm) and np.isfinite(acoes_ref) and acoes_ref > 0:
            lpa_ltm = (ll_ltm * 1000.0) / acoes_ref
    
    # Para UNIT, ajustar LPA pelo fator
    if fator_unit > 1 and np.isfinite(lpa_ltm):
        lpa_ltm = lpa_ltm * fator_unit
    
    resultado["P_L"] = _normalizar_valor(_safe_divide(preco, lpa_ltm))
    
    # ==================== P/VPA ====================
    
    pl = _obter_valor_pontual(dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)
    
    # VPA = (PL × 1000) / Ações
    vpa = (pl * 1000.0) / acoes_ref if np.isfinite(pl) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan
    
    # Para UNIT, VPA é multiplicado pelo fator
    if fator_unit > 1 and np.isfinite(vpa):
        vpa = vpa * fator_unit
    
    resultado["P_VPA"] = _normalizar_valor(_safe_divide(preco, vpa))
    
    # ==================== EV/EBITDA, EV/EBIT, EV/RECEITA ====================
    
    ebitda_ltm = _calcular_ebitda_ltm(dados, periodo)
    resultado["EV_EBITDA"] = _normalizar_valor(_safe_divide(ev, ebitda_ltm))
    
    ebit_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["ebit"], periodo)
    resultado["EV_EBIT"] = _normalizar_valor(_safe_divide(ev, ebit_ltm))
    
    receita_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["receita"], periodo)
    resultado["EV_RECEITA"] = _normalizar_valor(_safe_divide(ev, receita_ltm))
    
    # ==================== DY E PAYOUT - CORREÇÃO v3.0 ====================
    
    # CORREÇÃO: Calcular DPA_LTM diretamente, sem conversões
    dpa_ltm = _calcular_dpa_ltm(dados, periodo)
    
    # Para UNIT, DPA é multiplicado pelo fator (UNIT = pacote de ações)
    if fator_unit > 1 and np.isfinite(dpa_ltm):
        dpa_ltm = dpa_ltm * fator_unit
    
    # DY = (DPA_LTM / Preço) × 100
    resultado["DY"] = _normalizar_valor(_safe_divide(dpa_ltm, preco) * 100)
    
    # PAYOUT = (DPA_LTM / LPA_LTM) × 100
    resultado["PAYOUT"] = _normalizar_valor(_safe_divide(dpa_ltm, lpa_ltm) * 100)
    
    # ==================== RENTABILIDADE ====================
    
    # ROE = LL_LTM / PL_Médio × 100
    pl_medio = _obter_valor_medio(dados, dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)
    resultado["ROE"] = _normalizar_valor(_safe_divide(ll_ltm, pl_medio) * 100)
    
    # ROA = LL_LTM / Ativo_Médio × 100
    at_medio = _obter_valor_medio(dados, dados.bpa, CONTAS_BPA["ativo_total"], periodo)
    resultado["ROA"] = _normalizar_valor(_safe_divide(ll_ltm, at_medio) * 100)
    
    # ROIC = NOPAT / Capital Investido × 100
    # CORREÇÃO v3.0: Capital Investido = PL + Dívida BRUTA (não líquida)
    nopat = ebit_ltm * (1 - TAXA_IR_NOPAT) if np.isfinite(ebit_ltm) else np.nan
    
    emp_cp = _obter_valor_pontual(dados.bpp, CONTAS_BPP["emprestimos_cp"], periodo, ["2.01.04"])
    emp_lp = _obter_valor_pontual(dados.bpp, CONTAS_BPP["emprestimos_lp"], periodo, ["2.02.01"])
    
    emp_cp_val = emp_cp if np.isfinite(emp_cp) else 0
    emp_lp_val = emp_lp if np.isfinite(emp_lp) else 0
    divida_bruta = emp_cp_val + emp_lp_val
    
    capital_investido = pl + divida_bruta if np.isfinite(pl) else np.nan
    resultado["ROIC"] = _normalizar_valor(_safe_divide(nopat, capital_investido) * 100)
    
    # Margens
    resultado["MARGEM_EBITDA"] = _normalizar_valor(_safe_divide(ebitda_ltm, receita_ltm) * 100)
    resultado["MARGEM_LIQUIDA"] = _normalizar_valor(_safe_divide(ll_ltm, receita_ltm) * 100)
    
    # ==================== ENDIVIDAMENTO ====================
    
    caixa = _obter_valor_pontual(dados.bpa, CONTAS_BPA["caixa"], periodo)
    aplic = _obter_valor_pontual(dados.bpa, CONTAS_BPA["aplicacoes"], periodo)
    caixa_val = caixa if np.isfinite(caixa) else 0
    aplic_val = aplic if np.isfinite(aplic) else 0
    
    divida_liquida = divida_bruta - caixa_val - aplic_val
    
    resultado["DIV_LIQ_EBITDA"] = _normalizar_valor(_safe_divide(divida_liquida, ebitda_ltm))
    resultado["DIV_LIQ_PL"] = _normalizar_valor(_safe_divide(divida_liquida, pl))
    
    # ICJ = EBIT / Despesas Financeiras
    # CORREÇÃO v3.0: Busca flexível
    desp_fin = _calcular_ltm(dados, dados.dre, CONTAS_DRE["despesa_financeira"], periodo)
    if not np.isfinite(desp_fin) or desp_fin == 0:
        res_fin = _calcular_ltm(dados, dados.dre, CONTAS_DRE["resultado_financeiro"], periodo)
        if np.isfinite(res_fin) and res_fin < 0:
            desp_fin = abs(res_fin)
    
    resultado["ICJ"] = _normalizar_valor(_safe_divide(ebit_ltm, desp_fin))
    
    # Composição da Dívida = Emp.CP / Dív.Bruta × 100
    resultado["COMPOSICAO_DIVIDA"] = _normalizar_valor(_safe_divide(emp_cp_val, divida_bruta) * 100)
    
    # ==================== LIQUIDEZ ====================
    
    ac = _obter_valor_pontual(dados.bpa, CONTAS_BPA["ativo_circulante"], periodo)
    pc = _obter_valor_pontual(dados.bpp, CONTAS_BPP["passivo_circulante"], periodo)
    estoques = _obter_valor_pontual(dados.bpa, CONTAS_BPA["estoques"], periodo)
    rlp = _obter_valor_pontual(dados.bpa, CONTAS_BPA["realizavel_lp"], periodo)
    pnc = _obter_valor_pontual(dados.bpp, CONTAS_BPP["passivo_nao_circulante"], periodo)
    
    resultado["LIQ_CORRENTE"] = _normalizar_valor(_safe_divide(ac, pc))
    
    ac_val = ac if np.isfinite(ac) else 0
    est_val = estoques if np.isfinite(estoques) else 0
    resultado["LIQ_SECA"] = _normalizar_valor(_safe_divide(ac_val - est_val, pc))
    
    rlp_val = rlp if np.isfinite(rlp) else 0
    pc_val = pc if np.isfinite(pc) else 0
    pnc_val = pnc if np.isfinite(pnc) else 0
    resultado["LIQ_GERAL"] = _normalizar_valor(_safe_divide(ac_val + rlp_val, pc_val + pnc_val))
    
    # ==================== EFICIÊNCIA ====================
    
    # CORREÇÃO v3.0: Giro do Ativo usa Ativo MÉDIO
    resultado["GIRO_ATIVO"] = _normalizar_valor(_safe_divide(receita_ltm, at_medio))
    
    # PMR, PME, PMP e Ciclo de Caixa
    contas_receber = _obter_valor_pontual(dados.bpa, CONTAS_BPA["contas_receber"], periodo)
    fornecedores = _obter_valor_pontual(dados.bpp, CONTAS_BPP["fornecedores"], periodo)
    
    cpv_ltm = abs(_calcular_ltm(dados, dados.dre, CONTAS_DRE["custo"], periodo)) if dados.dre is not None else np.nan
    
    # CORREÇÃO v3.0: PME usa Estoque MÉDIO
    estoque_medio = _obter_valor_medio(dados, dados.bpa, CONTAS_BPA["estoques"], periodo)
    
    pmr = _safe_divide(contas_receber, receita_ltm) * 360 if np.isfinite(contas_receber) and np.isfinite(receita_ltm) else np.nan
    pme = _safe_divide(estoque_medio, cpv_ltm) * 360 if np.isfinite(estoque_medio) and np.isfinite(cpv_ltm) else np.nan
    pmp = _safe_divide(fornecedores, cpv_ltm) * 360 if np.isfinite(fornecedores) and np.isfinite(cpv_ltm) else np.nan
    
    ciclo_caixa = np.nan
    if np.isfinite(pmr) and np.isfinite(pme) and np.isfinite(pmp):
        ciclo_caixa = pmr + pme - pmp
    
    resultado["CICLO_CAIXA"] = _normalizar_valor(ciclo_caixa)
    resultado["PME"] = _normalizar_valor(pme)
    
    # NCG/Receita
    ncg = (contas_receber if np.isfinite(contas_receber) else 0) + \
          (estoques if np.isfinite(estoques) else 0) - \
          (fornecedores if np.isfinite(fornecedores) else 0)
    resultado["NCG_RECEITA"] = _normalizar_valor(_safe_divide(ncg, receita_ltm) * 100)
    
    return resultado


# ======================================================================================
# CALCULADORA - BANCOS
# ======================================================================================

def calcular_multiplos_banco(
    dados: DadosEmpresa,
    periodo: str,
    usar_preco_atual: bool = True,
    ticker_preco: Optional[str] = None
) -> Dict[str, Optional[float]]:
    """
    Calcula 9 múltiplos para bancos.
    
    CORREÇÃO v3.0:
    - P/L usa LPA da conta 3.99 quando disponível
    - Detecta PL em 2.07 ou 2.08 automaticamente
    """
    resultado: Dict[str, Optional[float]] = {}
    
    # Detectar código do PL
    pl_code = _detectar_codigo_pl_banco(dados, periodo)
    
    # ==================== MARKET CAP ====================
    
    if usar_preco_atual:
        market_cap = _calcular_market_cap_atual(dados, ticker_preco)
    else:
        market_cap = _calcular_market_cap(dados, periodo, ticker_preco)
    
    resultado["VALOR_MERCADO"] = _normalizar_valor(market_cap, decimals=2)
    
    # ==================== DADOS BASE ====================
    
    ll_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE_BANCOS["lucro_liquido"], periodo)
    at = _obter_valor_pontual(dados.bpa, CONTAS_BPA_BANCOS["ativo_total"], periodo)
    at_medio = _obter_valor_medio(dados, dados.bpa, CONTAS_BPA_BANCOS["ativo_total"], periodo)
    receita_interm = _calcular_ltm(dados, dados.dre, CONTAS_DRE_BANCOS["receita_intermediacao"], periodo)
    
    acoes_ref, _, fator_unit = _ajustar_acoes_para_ticker_preco(dados, periodo, ticker_preco)
    
    if usar_preco_atual:
        preco, _ = _obter_preco_atual(dados, ticker_preco)
    else:
        preco = _obter_preco(dados, periodo, ticker_preco)
    
    # ==================== P/L - CORREÇÃO v3.0 ====================
    
    # Priorizar conta 3.99 (LPA CVM)
    lpa_ltm = _calcular_lpa_ltm(dados, periodo)
    
    # Fallback: calcular manualmente
    if not np.isfinite(lpa_ltm) or lpa_ltm == 0:
        if np.isfinite(ll_ltm) and np.isfinite(acoes_ref) and acoes_ref > 0:
            lpa_ltm = (ll_ltm * 1000.0) / acoes_ref
    
    # Para UNIT, ajustar LPA pelo fator
    if fator_unit > 1 and np.isfinite(lpa_ltm):
        lpa_ltm = lpa_ltm * fator_unit
    
    resultado["P_L"] = _normalizar_valor(_safe_divide(preco, lpa_ltm))
    
    # ==================== P/VPA ====================
    
    pl = _obter_valor_pontual(dados.bpp, pl_code, periodo)
    pl_medio = _obter_valor_medio(dados, dados.bpp, pl_code, periodo)
    
    vpa = (pl * 1000.0) / acoes_ref if np.isfinite(pl) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan
    
    if fator_unit > 1 and np.isfinite(vpa):
        vpa = vpa * fator_unit
    
    resultado["P_VPA"] = _normalizar_valor(_safe_divide(preco, vpa))
    
    # ==================== DY E PAYOUT ====================
    
    dpa_ltm = _calcular_dpa_ltm(dados, periodo)
    
    if fator_unit > 1 and np.isfinite(dpa_ltm):
        dpa_ltm = dpa_ltm * fator_unit
    
    resultado["DY"] = _normalizar_valor(_safe_divide(dpa_ltm, preco) * 100)
    resultado["PAYOUT"] = _normalizar_valor(_safe_divide(dpa_ltm, lpa_ltm) * 100)
    
    # ==================== RENTABILIDADE ====================
    
    resultado["ROE"] = _normalizar_valor(_safe_divide(ll_ltm, pl_medio) * 100)
    resultado["ROA"] = _normalizar_valor(_safe_divide(ll_ltm, at_medio) * 100)
    resultado["MARGEM_LIQUIDA"] = _normalizar_valor(_safe_divide(ll_ltm, receita_interm) * 100)
    
    # ==================== ESTRUTURA ====================
    
    resultado["PL_ATIVOS"] = _normalizar_valor(_safe_divide(pl, at) * 100)
    
    return resultado


# ======================================================================================
# CALCULADORA - HOLDINGS DE SEGUROS
# ======================================================================================

def calcular_multiplos_holding_seguros(
    dados: DadosEmpresa,
    periodo: str,
    usar_preco_atual: bool = True,
    ticker_preco: Optional[str] = None
) -> Dict[str, Optional[float]]:
    """
    Calcula 11 múltiplos para holdings de seguros (BBSE3, CXSE3).
    
    CORREÇÃO v3.0: Usa conta PL correta (2.03).
    """
    resultado: Dict[str, Optional[float]] = {}
    ticker_upper = dados.ticker.upper().strip()
    
    # ==================== MARKET CAP E EV ====================
    
    if usar_preco_atual:
        market_cap = _calcular_market_cap_atual(dados, ticker_preco)
    else:
        market_cap = _calcular_market_cap(dados, periodo, ticker_preco)
    
    resultado["VALOR_MERCADO"] = _normalizar_valor(market_cap, decimals=2)
    
    ev = _calcular_ev(dados, periodo, market_cap)
    
    # ==================== DADOS BASE ====================
    
    ll_ltm = _calcular_ltm(dados, dados.dre, "3.11", periodo)
    
    # Receita específica por ticker
    if ticker_upper.startswith("BBSE"):
        # BBSE3: Comissões (3.05.01) + Equivalência (3.06.01)
        r1 = _calcular_ltm(dados, dados.dre, "3.05.01", periodo)
        r2 = _calcular_ltm(dados, dados.dre, "3.06.01", periodo)
    else:
        # CXSE3: Serviços (3.04.04.02) + Equivalência (3.04.06)
        r1 = _calcular_ltm(dados, dados.dre, "3.04.04.02", periodo)
        r2 = _calcular_ltm(dados, dados.dre, "3.04.06", periodo)
    
    r1_val = r1 if np.isfinite(r1) else 0
    r2_val = r2 if np.isfinite(r2) else 0
    receita_ltm = r1_val + r2_val if (r1_val + r2_val) > 0 else np.nan
    
    # Resultado Operacional
    res_op = _calcular_ltm(dados, dados.dre, "3.05", periodo)
    
    acoes_ref, _, fator_unit = _ajustar_acoes_para_ticker_preco(dados, periodo, ticker_preco)
    
    if usar_preco_atual:
        preco, _ = _obter_preco_atual(dados, ticker_preco)
    else:
        preco = _obter_preco(dados, periodo, ticker_preco)
    
    # ==================== P/L ====================
    
    lpa_ltm = _calcular_lpa_ltm(dados, periodo)
    if not np.isfinite(lpa_ltm) or lpa_ltm == 0:
        if np.isfinite(ll_ltm) and np.isfinite(acoes_ref) and acoes_ref > 0:
            lpa_ltm = (ll_ltm * 1000.0) / acoes_ref
    
    if fator_unit > 1 and np.isfinite(lpa_ltm):
        lpa_ltm = lpa_ltm * fator_unit
    
    resultado["P_L"] = _normalizar_valor(_safe_divide(preco, lpa_ltm))
    
    # ==================== P/VPA ====================
    
    # CORREÇÃO v3.0: Usa conta correta 2.03
    pl = _obter_valor_pontual(dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)
    pl_medio = _obter_valor_medio(dados, dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)
    
    vpa = (pl * 1000.0) / acoes_ref if np.isfinite(pl) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan
    
    if fator_unit > 1 and np.isfinite(vpa):
        vpa = vpa * fator_unit
    
    resultado["P_VPA"] = _normalizar_valor(_safe_divide(preco, vpa))
    
    # ==================== EV/RECEITA ====================
    
    resultado["EV_RECEITA"] = _normalizar_valor(_safe_divide(ev, receita_ltm))
    
    # ==================== DY E PAYOUT ====================
    
    dpa_ltm = _calcular_dpa_ltm(dados, periodo)
    
    if fator_unit > 1 and np.isfinite(dpa_ltm):
        dpa_ltm = dpa_ltm * fator_unit
    
    resultado["DY"] = _normalizar_valor(_safe_divide(dpa_ltm, preco) * 100)
    resultado["PAYOUT"] = _normalizar_valor(_safe_divide(dpa_ltm, lpa_ltm) * 100)
    
    # ==================== RENTABILIDADE ====================
    
    at = _obter_valor_pontual(dados.bpa, "1", periodo)
    at_medio = _obter_valor_medio(dados, dados.bpa, "1", periodo)
    
    resultado["ROE"] = _normalizar_valor(_safe_divide(ll_ltm, pl_medio) * 100)
    resultado["ROA"] = _normalizar_valor(_safe_divide(ll_ltm, at_medio) * 100)
    resultado["MARGEM_LIQUIDA"] = _normalizar_valor(_safe_divide(ll_ltm, receita_ltm) * 100)
    resultado["MARGEM_OPERACIONAL"] = _normalizar_valor(_safe_divide(res_op, receita_ltm) * 100)
    
    # ==================== EFICIÊNCIA ====================
    
    desp_adm = _calcular_ltm(dados, dados.dre, "3.04", periodo)
    resultado["INDICE_EFICIENCIA"] = _normalizar_valor(_safe_divide(desp_adm, receita_ltm) * 100)
    
    return resultado


# ======================================================================================
# CALCULADORA - SEGURADORAS
# ======================================================================================

def calcular_multiplos_seguradora(
    dados: DadosEmpresa,
    periodo: str,
    usar_preco_atual: bool = True,
    ticker_preco: Optional[str] = None
) -> Dict[str, Optional[float]]:
    """Calcula 11 múltiplos para seguradoras."""
    resultado: Dict[str, Optional[float]] = {}
    
    # ==================== MARKET CAP ====================
    
    if usar_preco_atual:
        market_cap = _calcular_market_cap_atual(dados, ticker_preco)
    else:
        market_cap = _calcular_market_cap(dados, periodo, ticker_preco)
    
    resultado["VALOR_MERCADO"] = _normalizar_valor(market_cap, decimals=2)
    
    # ==================== DADOS BASE ====================
    
    ll_ltm = _calcular_ltm(dados, dados.dre, "3.11", periodo)
    
    acoes_ref, _, fator_unit = _ajustar_acoes_para_ticker_preco(dados, periodo, ticker_preco)
    
    if usar_preco_atual:
        preco, _ = _obter_preco_atual(dados, ticker_preco)
    else:
        preco = _obter_preco(dados, periodo, ticker_preco)
    
    # ==================== P/L ====================
    
    lpa_ltm = _calcular_lpa_ltm(dados, periodo)
    if not np.isfinite(lpa_ltm) or lpa_ltm == 0:
        if np.isfinite(ll_ltm) and np.isfinite(acoes_ref) and acoes_ref > 0:
            lpa_ltm = (ll_ltm * 1000.0) / acoes_ref
    
    if fator_unit > 1 and np.isfinite(lpa_ltm):
        lpa_ltm = lpa_ltm * fator_unit
    
    resultado["P_L"] = _normalizar_valor(_safe_divide(preco, lpa_ltm))
    
    # ==================== P/VPA ====================
    
    pl = _obter_valor_pontual(dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)
    pl_medio = _obter_valor_medio(dados, dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)
    
    vpa = (pl * 1000.0) / acoes_ref if np.isfinite(pl) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan
    
    if fator_unit > 1 and np.isfinite(vpa):
        vpa = vpa * fator_unit
    
    resultado["P_VPA"] = _normalizar_valor(_safe_divide(preco, vpa))
    
    # ==================== DY E PAYOUT ====================
    
    dpa_ltm = _calcular_dpa_ltm(dados, periodo)
    
    if fator_unit > 1 and np.isfinite(dpa_ltm):
        dpa_ltm = dpa_ltm * fator_unit
    
    resultado["DY"] = _normalizar_valor(_safe_divide(dpa_ltm, preco) * 100)
    resultado["PAYOUT"] = _normalizar_valor(_safe_divide(dpa_ltm, lpa_ltm) * 100)
    
    # ==================== RENTABILIDADE ====================
    
    at = _obter_valor_pontual(dados.bpa, "1", periodo)
    at_medio = _obter_valor_medio(dados, dados.bpa, "1", periodo)
    
    resultado["ROE"] = _normalizar_valor(_safe_divide(ll_ltm, pl_medio) * 100)
    resultado["ROA"] = _normalizar_valor(_safe_divide(ll_ltm, at_medio) * 100)
    
    # ==================== ESTRUTURA ====================
    
    resultado["PL_ATIVOS"] = _normalizar_valor(_safe_divide(pl, at) * 100)
    
    # ==================== OPERACIONAL ====================
    
    # Sinistros e Prêmios
    premios = _calcular_ltm(dados, dados.dre, "3.01", periodo)
    sinistros = _calcular_ltm(dados, dados.dre, "3.02.01", periodo)
    desp_com = _calcular_ltm(dados, dados.dre, "3.04.01", periodo)
    desp_adm = _calcular_ltm(dados, dados.dre, "3.04.02", periodo)
    
    # Sinistralidade = Sinistros / Prêmios × 100
    sinistralidade = _safe_divide(abs(sinistros) if np.isfinite(sinistros) else np.nan, premios) * 100
    resultado["SINISTRALIDADE"] = _normalizar_valor(sinistralidade)
    
    # Combined Ratio = (Sinistros + Despesas) / Prêmios × 100
    sin_val = abs(sinistros) if np.isfinite(sinistros) else 0
    desp_com_val = abs(desp_com) if np.isfinite(desp_com) else 0
    desp_adm_val = abs(desp_adm) if np.isfinite(desp_adm) else 0
    
    combined = _safe_divide(sin_val + desp_com_val + desp_adm_val, premios) * 100
    resultado["COMBINED_RATIO"] = _normalizar_valor(combined)
    
    # Margem de Subscrição = (Prêmios - Sinistros - Despesas) / Prêmios × 100
    premios_val = premios if np.isfinite(premios) else 0
    margem_sub = _safe_divide(premios_val - sin_val - desp_com_val - desp_adm_val, premios) * 100
    resultado["MARGEM_SUBSCRICAO"] = _normalizar_valor(margem_sub)
    
    return resultado


# ======================================================================================
# SELETOR DE CALCULADORA
# ======================================================================================

def calcular_multiplos(
    dados: DadosEmpresa,
    periodo: str,
    usar_preco_atual: bool = True,
    ticker_preco: Optional[str] = None
) -> Dict[str, Optional[float]]:
    """
    Seleciona e executa a calculadora apropriada baseado no tipo de empresa.
    """
    ticker = (dados.ticker or "").upper().strip()
    
    if _eh_banco(ticker):
        return calcular_multiplos_banco(dados, periodo, usar_preco_atual, ticker_preco)
    elif _eh_holding_seguros(ticker):
        return calcular_multiplos_holding_seguros(dados, periodo, usar_preco_atual, ticker_preco)
    elif _eh_seguradora(ticker):
        return calcular_multiplos_seguradora(dados, periodo, usar_preco_atual, ticker_preco)
    else:
        return calcular_multiplos_empresa(dados, periodo, usar_preco_atual, ticker_preco)


# ======================================================================================
# FUNÇÕES DE CARREGAMENTO E PROCESSAMENTO
# ======================================================================================

def detectar_padrao_fiscal(dados: DadosEmpresa) -> PadraoFiscal:
    """Detecta o padrão fiscal da empresa baseado nos períodos disponíveis."""
    if dados.dre is None or dados.dre.empty:
        return PadraoFiscal()
    
    periodos = _get_colunas_numericas_validas(dados.dre)
    if not periodos:
        return PadraoFiscal()
    
    # Verificar se é semestral (apenas T2 e T4)
    trimestres = set()
    for p in periodos:
        _, tri = _parse_periodo(p)
        if tri:
            trimestres.add(tri)
    
    if trimestres == {"T2", "T4"} or trimestres == {"T4"}:
        return PadraoFiscal(tipo="SEMESTRAL", trimestres_disponiveis=periodos, n_periodos_ltm=3)
    
    return PadraoFiscal(tipo="PADRAO", trimestres_disponiveis=periodos, n_periodos_ltm=4)


def carregar_dados_empresa(ticker: str, base_path: str) -> Optional[DadosEmpresa]:
    """
    Carrega todos os dados de uma empresa.
    
    Espera a seguinte estrutura de diretórios:
    base_path/
        dre_consolidado.csv
        bpa_consolidado.csv
        bpp_consolidado.csv
        dfc_consolidado.csv (opcional)
        precos_trimestrais.csv
        acoes_historico.csv
        dividendos.csv (opcional)
    """
    base = Path(base_path)
    
    dados = DadosEmpresa(ticker=ticker)
    
    # Carregar DRE
    dre_path = base / "dre_consolidado.csv"
    if dre_path.exists():
        dados.dre = pd.read_csv(dre_path)
    
    # Carregar BPA
    bpa_path = base / "bpa_consolidado.csv"
    if bpa_path.exists():
        dados.bpa = pd.read_csv(bpa_path)
    
    # Carregar BPP
    bpp_path = base / "bpp_consolidado.csv"
    if bpp_path.exists():
        dados.bpp = pd.read_csv(bpp_path)
    
    # Carregar DFC
    dfc_path = base / "dfc_consolidado.csv"
    if dfc_path.exists():
        dados.dfc = pd.read_csv(dfc_path)
    
    # Carregar Preços
    precos_path = base / "precos_trimestrais.csv"
    if precos_path.exists():
        dados.precos = pd.read_csv(precos_path)
    
    # Carregar Ações
    acoes_path = base / "acoes_historico.csv"
    if acoes_path.exists():
        dados.acoes = pd.read_csv(acoes_path)
    
    # Carregar Dividendos
    div_path = base / "dividendos.csv"
    if div_path.exists():
        dados.dividendos = pd.read_csv(div_path)
    
    # Detectar padrão fiscal
    dados.padrao_fiscal = detectar_padrao_fiscal(dados)
    
    # Definir períodos disponíveis
    if dados.dre is not None:
        dados.periodos = _get_colunas_numericas_validas(dados.dre)
    
    return dados


def _listar_tickers_saida_multiclasse(dados: DadosEmpresa, ticker_seed: str) -> List[str]:
    """
    Lista tickers disponíveis no arquivo de preços para a mesma empresa.
    Ex.: KLBN11 -> ['KLBN3', 'KLBN4', 'KLBN11']
    """
    seed = (ticker_seed or dados.ticker or "").upper().strip()
    if len(seed) < 4 or dados.precos is None or dados.precos.empty:
        return [seed] if seed else []
    
    raiz = seed[:4]
    df = dados.precos
    
    col_ticker = None
    for c in ["Ticker", "ticker", "TICKER"]:
        if c in df.columns:
            col_ticker = c
            break
    
    if not col_ticker:
        return [seed]
    
    tickers = df[col_ticker].astype(str).str.upper().str.strip().unique().tolist()
    tickers = [t for t in tickers if t.startswith(raiz)]
    
    # Ordenar: 3 (ON), 4-8 (PN), 11 (UNIT)
    def sort_key(t):
        classe = _extrair_classe_ticker(t)
        if classe == "3":
            return 0
        elif classe in {"4", "5", "6", "7", "8"}:
            return 1
        elif classe == "11":
            return 2
        return 3
    
    return sorted(tickers, key=sort_key)


# ======================================================================================
# METADADOS DOS MÚLTIPLOS
# ======================================================================================

METADADOS_MULTIPLOS = {
    "VALOR_MERCADO": {"nome": "Valor de Mercado", "categoria": "Valuation", "unidade": "R$ mil"},
    "P_L": {"nome": "P/L", "categoria": "Valuation", "unidade": "x"},
    "P_VPA": {"nome": "P/VPA", "categoria": "Valuation", "unidade": "x"},
    "EV_EBITDA": {"nome": "EV/EBITDA", "categoria": "Valuation", "unidade": "x"},
    "EV_EBIT": {"nome": "EV/EBIT", "categoria": "Valuation", "unidade": "x"},
    "EV_RECEITA": {"nome": "EV/Receita", "categoria": "Valuation", "unidade": "x"},
    "DY": {"nome": "Dividend Yield", "categoria": "Valuation", "unidade": "%"},
    "PAYOUT": {"nome": "Payout", "categoria": "Valuation", "unidade": "%"},
    "ROE": {"nome": "ROE", "categoria": "Rentabilidade", "unidade": "%"},
    "ROA": {"nome": "ROA", "categoria": "Rentabilidade", "unidade": "%"},
    "ROIC": {"nome": "ROIC", "categoria": "Rentabilidade", "unidade": "%"},
    "MARGEM_EBITDA": {"nome": "Margem EBITDA", "categoria": "Rentabilidade", "unidade": "%"},
    "MARGEM_LIQUIDA": {"nome": "Margem Líquida", "categoria": "Rentabilidade", "unidade": "%"},
    "DIV_LIQ_EBITDA": {"nome": "Dív.Líq/EBITDA", "categoria": "Endividamento", "unidade": "x"},
    "DIV_LIQ_PL": {"nome": "Dív.Líq/PL", "categoria": "Endividamento", "unidade": "x"},
    "ICJ": {"nome": "ICJ", "categoria": "Endividamento", "unidade": "x"},
    "COMPOSICAO_DIVIDA": {"nome": "Composição Dívida", "categoria": "Endividamento", "unidade": "%"},
    "LIQ_CORRENTE": {"nome": "Liquidez Corrente", "categoria": "Liquidez", "unidade": "x"},
    "LIQ_SECA": {"nome": "Liquidez Seca", "categoria": "Liquidez", "unidade": "x"},
    "LIQ_GERAL": {"nome": "Liquidez Geral", "categoria": "Liquidez", "unidade": "x"},
    "GIRO_ATIVO": {"nome": "Giro do Ativo", "categoria": "Eficiência", "unidade": "x"},
    "CICLO_CAIXA": {"nome": "Ciclo de Caixa", "categoria": "Eficiência", "unidade": "dias"},
    "PME": {"nome": "PME", "categoria": "Eficiência", "unidade": "dias"},
    "NCG_RECEITA": {"nome": "NCG/Receita", "categoria": "Eficiência", "unidade": "%"},
    "PL_ATIVOS": {"nome": "PL/Ativos", "categoria": "Estrutura", "unidade": "%"},
    "MARGEM_OPERACIONAL": {"nome": "Margem Operacional", "categoria": "Rentabilidade", "unidade": "%"},
    "INDICE_EFICIENCIA": {"nome": "Índice de Eficiência", "categoria": "Eficiência", "unidade": "%"},
    "SINISTRALIDADE": {"nome": "Sinistralidade", "categoria": "Operacional", "unidade": "%"},
    "COMBINED_RATIO": {"nome": "Combined Ratio", "categoria": "Operacional", "unidade": "%"},
    "MARGEM_SUBSCRICAO": {"nome": "Margem de Subscrição", "categoria": "Operacional", "unidade": "%"},
}


# ======================================================================================
# GERAÇÃO DE HISTÓRICO E ARQUIVOS DE SAÍDA
# ======================================================================================

def gerar_historico_anualizado(
    dados: DadosEmpresa,
    ticker_preco: Optional[str] = None
) -> Dict[str, Dict[str, Optional[float]]]:
    """
    Gera múltiplos anualizados (T4 de cada ano) + LTM atual.
    """
    if not dados.periodos:
        return {}
    
    resultado = {}
    
    # Agrupar períodos por ano (pegar T4 de cada ano)
    periodos_t4 = [p for p in dados.periodos if p.endswith("T4")]
    
    # Calcular múltiplos para cada T4 (usando preço do período)
    for periodo in periodos_t4:
        ano, _ = _parse_periodo(periodo)
        multiplos = calcular_multiplos(dados, periodo, usar_preco_atual=False, ticker_preco=ticker_preco)
        resultado[str(ano)] = multiplos
    
    # Calcular LTM (usando preço atual)
    if dados.periodos:
        periodo_ltm = dados.periodos[-1]
        multiplos_ltm = calcular_multiplos(dados, periodo_ltm, usar_preco_atual=True, ticker_preco=ticker_preco)
        resultado["LTM"] = multiplos_ltm
    
    return resultado


def salvar_multiplos_csv(
    historico: Dict[str, Dict[str, Optional[float]]],
    ticker: str,
    output_path: str
) -> None:
    """Salva múltiplos em formato CSV."""
    if not historico:
        return
    
    # Coletar todos os códigos de múltiplos
    todos_codigos = set()
    for periodo_data in historico.values():
        todos_codigos.update(periodo_data.keys())
    
    # Ordenar períodos (anos + LTM no final)
    periodos = sorted([p for p in historico.keys() if p != "LTM"])
    if "LTM" in historico:
        periodos.append("LTM")
    
    # Criar linhas
    linhas = []
    for codigo in sorted(todos_codigos):
        meta = METADADOS_MULTIPLOS.get(codigo, {"nome": codigo, "categoria": "Outro", "unidade": ""})
        linha = {
            "codigo": codigo,
            "nome": meta["nome"],
            "categoria": meta["categoria"],
            "unidade": meta["unidade"],
        }
        for periodo in periodos:
            valor = historico.get(periodo, {}).get(codigo)
            linha[periodo] = valor if valor is not None else ""
        linhas.append(linha)
    
    # Salvar CSV
    df = pd.DataFrame(linhas)
    colunas = ["codigo", "nome", "categoria", "unidade"] + periodos
    df = df[colunas]
    df.to_csv(output_path, index=False)


def salvar_multiplos_js(
    historico: Dict[str, Dict[str, Optional[float]]],
    ticker: str,
    output_path: str
) -> None:
    """Salva múltiplos em formato JavaScript."""
    if not historico:
        return
    
    # Coletar todos os códigos
    todos_codigos = set()
    for periodo_data in historico.values():
        todos_codigos.update(periodo_data.keys())
    
    # Ordenar períodos
    periodos = sorted([p for p in historico.keys() if p != "LTM"])
    if "LTM" in historico:
        periodos.append("LTM")
    
    # Criar estrutura JS
    dados_js = {}
    for codigo in sorted(todos_codigos):
        meta = METADADOS_MULTIPLOS.get(codigo, {"nome": codigo, "categoria": "Outro", "unidade": ""})
        valores = {}
        for periodo in periodos:
            valor = historico.get(periodo, {}).get(codigo)
            valores[periodo] = valor
        dados_js[codigo] = {
            "nome": meta["nome"],
            "categoria": meta["categoria"],
            "unidade": meta["unidade"],
            "valores": valores,
        }
    
    # Salvar JS
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"const multiplos_{ticker} = ")
        json.dump(dados_js, f, ensure_ascii=False, indent=2)
        f.write(";\n")


def processar_ticker(
    ticker: str,
    input_dir: str,
    output_dir: str
) -> Tuple[bool, str, Optional[Dict]]:
    """
    Processa um ticker: carrega dados, calcula múltiplos, salva arquivos.
    
    Retorna (sucesso, mensagem, resultado).
    """
    try:
        # Carregar dados
        dados = carregar_dados_empresa(ticker, input_dir)
        if dados is None:
            return False, f"Erro ao carregar dados de {ticker}", None
        
        # Listar tickers disponíveis (multi-classe)
        tickers_saida = _listar_tickers_saida_multiclasse(dados, ticker)
        
        resultado_geral = {}
        
        for ticker_preco in tickers_saida:
            # Gerar histórico
            historico = gerar_historico_anualizado(dados, ticker_preco)
            
            if not historico:
                continue
            
            # Salvar arquivos
            csv_path = os.path.join(output_dir, f"multiplos_{ticker_preco}.csv")
            js_path = os.path.join(output_dir, f"multiplos_{ticker_preco}.js")
            
            salvar_multiplos_csv(historico, ticker_preco, csv_path)
            salvar_multiplos_js(historico, ticker_preco, js_path)
            
            resultado_geral[ticker_preco] = historico
        
        return True, f"Processado {ticker} ({len(tickers_saida)} classe(s))", resultado_geral
    
    except Exception as e:
        return False, f"Erro ao processar {ticker}: {str(e)}", None


# ======================================================================================
# MAIN
# ======================================================================================

def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Calcula múltiplos fundamentalistas v3.0")
    parser.add_argument("--ticker", type=str, help="Ticker específico")
    parser.add_argument("--input", type=str, required=True, help="Diretório de entrada com dados")
    parser.add_argument("--output", type=str, required=True, help="Diretório de saída")
    
    args = parser.parse_args()
    
    # Criar diretório de saída
    os.makedirs(args.output, exist_ok=True)
    
    if args.ticker:
        # Processar ticker específico
        sucesso, msg, resultado = processar_ticker(args.ticker, args.input, args.output)
        print(f"{'✅' if sucesso else '❌'} {msg}")
    else:
        print("Uso: python calcular_multiplos.py --ticker PETR4 --input ./dados --output ./saida")


if __name__ == "__main__":
    main()
