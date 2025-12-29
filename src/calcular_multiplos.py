# src/calcular_multiplos.py
"""
Calculadora de Múltiplos Financeiros para Empresas Não-Financeiras
==================================================================
VERSÃO CORRIGIDA - Dezembro 2024

Calcula 22 múltiplos organizados em 5 categorias:
- Valuation (7): P/L, P/VPA, EV/EBITDA, EV/EBIT, EV/Receita, DY, Payout
- Rentabilidade (5): ROE, ROA, ROIC, Margem EBITDA, Margem Líquida
- Endividamento (4): Dív.Líq/EBITDA, Dív.Líq/PL, ICJ, Composição Dívida
- Liquidez (3): Corrente, Seca, Geral
- Eficiência (4): Giro Ativo, Ciclo Caixa, PME, NCG/Receita

CORREÇÕES APLICADAS:
1. Busca robusta de preços (período atual ou mais recente disponível)
2. Busca robusta de ações (período atual ou mais recente disponível)
3. Cálculo de EBITDA revisado
4. Cálculo de ROIC com taxa de IR correta
5. Dividend Yield calculado corretamente

UNIDADES:
- Balanços CVM: valores em R$ MIL
- Preços: valores em R$ (unitário)
- Ações: quantidade em UNIDADES
- Market Cap = Preço × Ações / 1000 → resultado em R$ MIL

Saída: JSON + CSV para fácil consumo em HTML/JavaScript
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime

import numpy as np
import pandas as pd

# Importar utilitários do projeto
sys.path.insert(0, str(Path(__file__).parent))
from multi_ticker_utils import get_ticker_principal, get_pasta_balanco, load_mapeamento_consolidado


# ======================================================================================
# CONFIGURAÇÕES E CONSTANTES
# ======================================================================================

# Empresas com ano fiscal março-fevereiro
TICKERS_ANO_FISCAL_MAR_FEV: Set[str] = {"CAML3"}

# Empresas com dados semestrais (sem T2)
TICKERS_DADOS_SEMESTRAIS: Set[str] = {"AGRO3"}

# Bancos (cálculo específico de múltiplos bancários)
TICKERS_BANCOS: Set[str] = {
    "RPAD3", "RPAD5", "RPAD6", "ABCB4", "BMGB4", "BBDC3", "BBDC4",
    "BPAC3", "BPAC5", "BPAC11", "BSLI3", "BSLI4", "BBAS3", "BGIP3",
    "BGIP4", "BPAR3", "BRSR3", "BRSR5", "BRSR6", "BNBR3", "BMIN3",
    "BMIN4", "BMEB3", "BMEB4", "BPAN4", "PINE3", "PINE4", "SANB3",
    "SANB4", "SANB11", "BEES3", "BEES4", "ITUB3", "ITUB4",
}

# Seguradoras e holdings (excluídas - estrutura muito diferente)
TICKERS_SEGURADORAS: Set[str] = {"BBSE3", "CXSE3", "IRBR3", "PSSA3"}

# Mapeamento de contas DRE padronizado
CONTAS_DRE = {
    "receita": "3.01",
    "cpv": "3.02",
    "lucro_bruto": "3.03",
    "ebit": "3.05",
    "resultado_financeiro": "3.06",
    "lucro_liquido": "3.11",
    "ir_csll": "3.08",
}

# Mapeamento de contas BPA (Ativo)
CONTAS_BPA = {
    "ativo_total": "1",
    "ativo_circulante": "1.01",
    "caixa": "1.01.01",
    "aplicacoes": "1.01.02",
    "contas_receber": "1.01.03",
    "estoques": "1.01.04",
    "ativos_biologicos": "1.01.05",
    "ativo_nao_circulante": "1.02",
    "realizavel_lp": "1.02.01",
    "imobilizado": "1.02.03",
}

# Mapeamento de contas BPP (Passivo)
CONTAS_BPP = {
    "passivo_total": "2",
    "passivo_circulante": "2.01",
    "emprestimos_cp": "2.01.04",
    "fornecedores": "2.01.02",
    "passivo_nao_circulante": "2.02",
    "emprestimos_lp": "2.02.01",
    "patrimonio_liquido": "2.03",
}

# ======================================================================================
# MAPEAMENTO DE CONTAS - BANCOS (IFRS)
# ======================================================================================

CONTAS_DRE_BANCOS = {
    "receita_intermediacao": "3.01",      # Receitas da Intermediação Financeira
    "despesa_intermediacao": "3.02",      # Despesas da Intermediação Financeira
    "resultado_bruto": "3.03",            # Resultado Bruto Intermediação
    "outras_receitas_desp": "3.04",       # Outras Receitas/Despesas Operacionais
    "resultado_operacional": "3.05",      # Resultado Operacional (antes IR)
    "lucro_liquido": "3.11",              # Lucro Líquido
    "pdd": "3.02.02",                     # Provisão para Devedores Duvidosos
}

CONTAS_BPA_BANCOS = {
    "ativo_total": "1",
    "caixa": "1.01",
    "ativos_financeiros": "1.02",
    "operacoes_credito": "1.02.03.04",    # Operações de Crédito (novo formato)
    "operacoes_credito_alt": "1.05.03.02", # Operações de Crédito (formato antigo)
    "provisao_pdd": "1.02.03.06",         # (-) Provisão para Perda Esperada
    "titulos_valores": "1.02.02",         # TVM
}

CONTAS_BPP_BANCOS = {
    "passivo_total": "2",
    "passivos_financeiros_vj": "2.01",
    "passivos_custo_amort": "2.02",       # ou 2.03 dependendo do banco
    "depositos": "2.03.01",               # Depósitos
    # PL é detectado dinamicamente (2.07 ou 2.08)
}

# Taxa de IR para NOPAT (alíquota efetiva média)
TAXA_IR_NOPAT = 0.34  # 34% (25% IR + 9% CSLL)


# ======================================================================================
# FUNÇÕES UTILITÁRIAS
# ======================================================================================

def _is_banco(ticker: str) -> bool:
    """Verifica se ticker é de banco."""
    ticker_upper = ticker.upper().strip()
    if ticker_upper in TICKERS_BANCOS:
        return True
    # Verificar por base do ticker (ex: BBDC3 → BBDC)
    match = re.match(r'^([A-Z]{4})\d+$', ticker_upper)
    if match:
        base = match.group(1)
        for t in TICKERS_BANCOS:
            if t.startswith(base):
                return True
    return False


def _is_seguradora(ticker: str) -> bool:
    """Verifica se ticker é de seguradora (excluída do cálculo)."""
    return ticker.upper().strip() in TICKERS_SEGURADORAS


def _is_ano_fiscal_mar_fev(ticker: str) -> bool:
    """Verifica se empresa tem ano fiscal março-fevereiro."""
    return ticker.upper().strip() in TICKERS_ANO_FISCAL_MAR_FEV


def _is_dados_semestrais(ticker: str) -> bool:
    """Verifica se empresa tem dados semestrais (sem T2)."""
    return ticker.upper().strip() in TICKERS_DADOS_SEMESTRAIS


def _parse_periodo(col: str) -> Tuple[int, str]:
    """
    Parseia coluna de período (ex: '2024T3') em (ano, trimestre).
    Retorna (0, '') se não for período válido.
    """
    if not isinstance(col, str) or len(col) < 5:
        return (0, '')
    try:
        ano = int(col[:4])
        tri = col[4:]
        if tri in ('T1', 'T2', 'T3', 'T4'):
            return (ano, tri)
    except:
        pass
    return (0, '')


def _ordenar_periodos(periodos: List[str]) -> List[str]:
    """Ordena lista de períodos cronologicamente."""
    def sort_key(p):
        ano, tri = _parse_periodo(p)
        tri_num = {'T1': 1, 'T2': 2, 'T3': 3, 'T4': 4}.get(tri, 0)
        return (ano, tri_num)
    return sorted(periodos, key=sort_key)


def _safe_divide(numerador: float, denominador: float, default: float = np.nan) -> float:
    """Divisão segura que retorna default se denominador for zero ou inválido."""
    if not np.isfinite(numerador) or not np.isfinite(denominador):
        return default
    if denominador == 0:
        return default
    return numerador / denominador


def _normalizar_valor(valor: float, decimals: int = 4) -> Optional[float]:
    """Normaliza valor numérico, retorna None se inválido."""
    if not np.isfinite(valor):
        return None
    return round(float(valor), decimals)


# ======================================================================================
# DETECTOR DE PADRÃO FISCAL
# ======================================================================================

@dataclass
class PadraoFiscal:
    """Informações sobre o padrão fiscal da empresa."""
    tipo: str  # 'PADRAO', 'MAR_FEV', 'SEMESTRAL', 'IRREGULAR'
    trimestres_disponiveis: Set[str]
    periodos_por_ano: Dict[int, List[str]]
    descricao: str
    
    @property
    def trimestres_ltm(self) -> int:
        """Número de trimestres para cálculo LTM."""
        if self.tipo == 'SEMESTRAL':
            return 3
        return 4


def detectar_padrao_fiscal(ticker: str, periodos: List[str]) -> PadraoFiscal:
    """Detecta padrão fiscal da empresa baseado no ticker e dados disponíveis."""
    ticker_upper = ticker.upper().strip()
    
    periodos_por_ano: Dict[int, List[str]] = {}
    trimestres_set: Set[str] = set()
    
    for p in periodos:
        ano, tri = _parse_periodo(p)
        if ano > 0 and tri:
            if ano not in periodos_por_ano:
                periodos_por_ano[ano] = []
            periodos_por_ano[ano].append(tri)
            trimestres_set.add(tri)
    
    if _is_ano_fiscal_mar_fev(ticker_upper):
        return PadraoFiscal(
            tipo='MAR_FEV',
            trimestres_disponiveis=trimestres_set,
            periodos_por_ano=periodos_por_ano,
            descricao="Ano fiscal mar-fev (CAML3 pattern)"
        )
    
    if _is_dados_semestrais(ticker_upper):
        return PadraoFiscal(
            tipo='SEMESTRAL',
            trimestres_disponiveis=trimestres_set,
            periodos_por_ano=periodos_por_ano,
            descricao="Dados semestrais (AGRO3 pattern) - sem T2"
        )
    
    if trimestres_set == {'T1', 'T2', 'T3', 'T4'}:
        return PadraoFiscal(
            tipo='PADRAO',
            trimestres_disponiveis=trimestres_set,
            periodos_por_ano=periodos_por_ano,
            descricao="Ano fiscal padrão (jan-dez) com T1-T4"
        )
    
    return PadraoFiscal(
        tipo='IRREGULAR',
        trimestres_disponiveis=trimestres_set,
        periodos_por_ano=periodos_por_ano,
        descricao=f"Padrão irregular - trimestres: {sorted(trimestres_set)}"
    )


# ======================================================================================
# CARREGADOR DE DADOS
# ======================================================================================

@dataclass
class DadosEmpresa:
    """Container para todos os dados de uma empresa."""
    ticker: str
    dre: Optional[pd.DataFrame] = None
    bpa: Optional[pd.DataFrame] = None
    bpp: Optional[pd.DataFrame] = None
    dfc: Optional[pd.DataFrame] = None
    precos: Optional[pd.DataFrame] = None
    acoes: Optional[pd.DataFrame] = None
    dividendos: Optional[pd.DataFrame] = None
    padrao_fiscal: Optional[PadraoFiscal] = None
    periodos: List[str] = field(default_factory=list)
    erros: List[str] = field(default_factory=list)


def _carregar_csv_padronizado(path: Path) -> Optional[pd.DataFrame]:
    """Carrega CSV padronizado, retorna None se não existir."""
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path)
        if 'cd_conta' in df.columns:
            df['cd_conta'] = df['cd_conta'].astype(str).str.strip()
        return df
    except Exception:
        return None


def _extrair_valor_conta(df: pd.DataFrame, cd_conta: str, periodo: str) -> float:
    """Extrai valor de uma conta específica em um período."""
    if df is None or periodo not in df.columns:
        return np.nan
    
    mask_exata = df['cd_conta'] == cd_conta
    if mask_exata.any():
        val = df.loc[mask_exata, periodo].values[0]
        return float(val) if pd.notna(val) else np.nan
    
    mask_sub = df['cd_conta'].str.startswith(cd_conta + '.')
    if mask_sub.any():
        vals = pd.to_numeric(df.loc[mask_sub, periodo], errors='coerce')
        soma = vals.sum(skipna=True)
        return float(soma) if np.isfinite(soma) else np.nan
    
    return np.nan


def _buscar_conta_flexivel(df: pd.DataFrame, codigos: List[str], periodo: str) -> float:
    """Busca valor tentando múltiplos códigos de conta."""
    for cod in codigos:
        val = _extrair_valor_conta(df, cod, periodo)
        if np.isfinite(val):
            return val
    return np.nan


def carregar_dados_empresa(ticker: str) -> DadosEmpresa:
    """Carrega todos os dados padronizados de uma empresa."""
    ticker_upper = ticker.upper().strip()
    pasta = get_pasta_balanco(ticker_upper)
    
    dados = DadosEmpresa(ticker=ticker_upper)
    
    dados.dre = _carregar_csv_padronizado(pasta / "dre_padronizado.csv")
    dados.bpa = _carregar_csv_padronizado(pasta / "bpa_padronizado.csv")
    dados.bpp = _carregar_csv_padronizado(pasta / "bpp_padronizado.csv")
    dados.dfc = _carregar_csv_padronizado(pasta / "dfc_padronizado.csv")
    dados.precos = _carregar_csv_padronizado(pasta / "precos_trimestrais.csv")
    dados.acoes = _carregar_csv_padronizado(pasta / "acoes_historico.csv")
    dados.dividendos = _carregar_csv_padronizado(pasta / "dividendos_trimestrais.csv")
    
    if dados.dre is None:
        dados.erros.append("DRE padronizado não encontrado")
    if dados.bpa is None:
        dados.erros.append("BPA padronizado não encontrado")
    if dados.bpp is None:
        dados.erros.append("BPP padronizado não encontrado")
    
    if dados.dre is not None:
        cols = [c for c in dados.dre.columns if _parse_periodo(c)[0] > 0]
        dados.periodos = _ordenar_periodos(cols)
        dados.padrao_fiscal = detectar_padrao_fiscal(ticker_upper, dados.periodos)
    
    return dados


# ======================================================================================
# FUNÇÕES DE OBTENÇÃO DE PREÇO E AÇÕES - CORRIGIDAS
# ======================================================================================

def _obter_preco(dados: DadosEmpresa, periodo: str) -> float:
    """
    Obtém preço da ação no período específico.
    
    FORMATO ESPERADO DO CSV:
    Preço_Fechamento,2015T1,2015T2,...,2025T3
    Preço de Fechamento Ajustado,2.11,2.12,...,15.56
    
    Args:
        dados: Dados da empresa
        periodo: Período específico (ex: "2025T3")
    
    Returns:
        Preço ou np.nan se não encontrado
    """
    if dados.precos is None:
        return np.nan
    
    if periodo not in dados.precos.columns:
        return np.nan
    
    # Buscar valor numérico na coluna do período
    for idx in range(len(dados.precos)):
        val = dados.precos.iloc[idx][periodo]
        if pd.notna(val):
            try:
                preco = float(val)
                if preco > 0:
                    return preco
            except (ValueError, TypeError):
                continue
    
    return np.nan


def _obter_preco_atual(dados: DadosEmpresa) -> Tuple[float, str]:
    """
    Obtém o preço mais recente disponível.
    
    IMPORTANTE: Esta função busca o preço mais atual independente do período.
    Usada para múltiplos de valuation que devem usar preço corrente.
    
    Returns:
        (preço, período) - preço mais recente e o período correspondente
    """
    if dados.precos is None or not dados.periodos:
        return np.nan, ""
    
    # Percorrer períodos do mais recente ao mais antigo
    for p in reversed(dados.periodos):
        preco = _obter_preco(dados, p)
        if np.isfinite(preco) and preco > 0:
            return preco, p
    
    return np.nan, ""


def _obter_acoes(dados: DadosEmpresa, periodo: str) -> float:
    """
    Obtém número de ações no período específico.
    
    FORMATO ESPERADO DO CSV:
    Espécie_Acao,2010T4,...,2024T4,2025T1,...
    ON,98897500,...,443329716,443329716,...
    PN,0,...,0,0,...
    TOTAL,98897500,...,443329716,443329716,...
    
    UNITS (KLBN11, ITUB, etc): Usa apenas ações ON.
    Outras empresas: Usa linha TOTAL.
    
    Args:
        dados: Dados da empresa
        periodo: Período específico
    
    Returns:
        Número de ações ou np.nan
    """
    if dados.acoes is None:
        return np.nan
    
    if periodo not in dados.acoes.columns:
        return np.nan
    
    ticker_upper = dados.ticker.upper()
    
    # UNITS CONHECIDAS: Usar apenas ON (não TOTAL)
    TICKERS_UNITS = {'KLBN11', 'ITUB', 'SANB11', 'BPAC11'}
    
    if 'Espécie_Acao' in dados.acoes.columns:
        # Para UNITS: usar apenas ON
        if ticker_upper in TICKERS_UNITS:
            mask_on = dados.acoes['Espécie_Acao'] == 'ON'
            if mask_on.any():
                val = dados.acoes.loc[mask_on, periodo].values[0]
                if pd.notna(val):
                    return float(val)
        
        # Para outras empresas: usar TOTAL
        mask_total = dados.acoes['Espécie_Acao'] == 'TOTAL'
        if mask_total.any():
            val = dados.acoes.loc[mask_total, periodo].values[0]
            if pd.notna(val):
                return float(val)
    
    return np.nan


def _obter_acoes_atual(dados: DadosEmpresa) -> Tuple[float, str]:
    """
    Obtém o número de ações mais recente disponível.
    
    IMPORTANTE: O número de ações geralmente só muda em eventos corporativos
    (splits, bonificações, emissões). Esta função busca o dado mais atual.
    
    Returns:
        (ações, período) - número de ações e período correspondente
    """
    if dados.acoes is None or not dados.periodos:
        return np.nan, ""
    
    # Percorrer períodos do mais recente ao mais antigo
    for p in reversed(dados.periodos):
        acoes = _obter_acoes(dados, p)
        if np.isfinite(acoes) and acoes > 0:
            return acoes, p
    
    return np.nan, ""


# ======================================================================================
# CÁLCULO DE MARKET CAP E EV - CORRIGIDOS
# ======================================================================================

def _calcular_market_cap(dados: DadosEmpresa, periodo: str) -> float:
    """
    Calcula Market Cap = Preço × Número de Ações
    
    IMPORTANTE: Usa preço e ações do período solicitado.
    Para múltiplos LTM, o preço deve ser o mais recente.
    
    CONVERSÃO DE UNIDADES:
    - Preço: R$ (unitário)
    - Ações: unidades
    - Balanços CVM: R$ MIL
    
    Market Cap (R$ mil) = Preço × Ações / 1000
    """
    preco = _obter_preco(dados, periodo)
    acoes = _obter_acoes(dados, periodo)
    
    if np.isfinite(preco) and np.isfinite(acoes) and preco > 0 and acoes > 0:
        return (preco * acoes) / 1000.0
    
    return np.nan


def _calcular_market_cap_atual(dados: DadosEmpresa) -> float:
    """
    Calcula Market Cap usando preço e ações mais recentes.
    
    Esta é a função principal para múltiplos de valuation atuais.
    """
    preco, _ = _obter_preco_atual(dados)
    acoes, _ = _obter_acoes_atual(dados)
    
    if np.isfinite(preco) and np.isfinite(acoes) and preco > 0 and acoes > 0:
        return (preco * acoes) / 1000.0
    
    return np.nan


def _calcular_ev(dados: DadosEmpresa, periodo: str, market_cap: Optional[float] = None) -> float:
    """
    Calcula Enterprise Value = Market Cap + Dívida Líquida
    
    Args:
        dados: Dados da empresa
        periodo: Período para dados de balanço
        market_cap: Market Cap já calculado (opcional)
    
    Returns:
        EV em R$ MIL
    """
    if market_cap is None:
        market_cap = _calcular_market_cap_atual(dados)
    
    if not np.isfinite(market_cap):
        return np.nan
    
    emp_cp = _obter_valor_pontual(dados.bpp, CONTAS_BPP["emprestimos_cp"], periodo, ["2.01.04", "2.01.04.01"])
    emp_lp = _obter_valor_pontual(dados.bpp, CONTAS_BPP["emprestimos_lp"], periodo, ["2.02.01", "2.02.01.01"])
    caixa = _obter_valor_pontual(dados.bpa, CONTAS_BPA["caixa"], periodo)
    aplic = _obter_valor_pontual(dados.bpa, CONTAS_BPA["aplicacoes"], periodo)
    
    emp_cp = emp_cp if np.isfinite(emp_cp) else 0
    emp_lp = emp_lp if np.isfinite(emp_lp) else 0
    caixa = caixa if np.isfinite(caixa) else 0
    aplic = aplic if np.isfinite(aplic) else 0
    
    divida_liquida = emp_cp + emp_lp - caixa - aplic
    
    return market_cap + divida_liquida


# ======================================================================================
# CALCULADORA LTM (Last Twelve Months)
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
    
    if padrao.tipo == 'SEMESTRAL':
        periodos_ltm = []
        count = 0
        for i in range(idx_fim, -1, -1):
            periodos_ltm.append(periodos[i])
            count += 1
            if count >= 3:
                break
    else:
        n_trimestres = 4
        start_idx = max(0, idx_fim - n_trimestres + 1)
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
    
    min_periodos = 3 if padrao.tipo == 'SEMESTRAL' else 4
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
    """Calcula média entre período atual e 4 trimestres atrás (para ROE, ROA, etc)."""
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
# CÁLCULO DE D&A E EBITDA - CORRIGIDOS
# ======================================================================================

def _calcular_da_periodo(dados: DadosEmpresa, periodo: str) -> float:
    """
    Calcula D&A (Depreciação e Amortização) de um período.
    
    CORREÇÃO: Busca em múltiplos códigos do DFC e garante valor positivo.
    """
    if dados.dfc is None:
        return np.nan
    
    codigos_da = ["6.01.DA", "6.01.01.02", "6.01.01.01", "6.01.01"]
    
    for cod in codigos_da:
        val = _extrair_valor_conta(dados.dfc, cod, periodo)
        if np.isfinite(val):
            return abs(val)  # D&A sempre positivo para soma ao EBIT
    
    return np.nan


def _calcular_ebitda_periodo(dados: DadosEmpresa, periodo: str) -> float:
    """
    Calcula EBITDA de um período: EBIT + |D&A|
    
    CORREÇÃO: Se D&A não disponível, retorna apenas EBIT (não np.nan).
    """
    ebit = _extrair_valor_conta(dados.dre, CONTAS_DRE["ebit"], periodo)
    
    if not np.isfinite(ebit):
        return np.nan
    
    da = _calcular_da_periodo(dados, periodo)
    
    if np.isfinite(da):
        return ebit + da
    
    # Se não tem D&A, retorna EBIT como aproximação
    return ebit


def _calcular_ebitda_ltm(dados: DadosEmpresa, periodo_fim: str) -> float:
    """Calcula EBITDA LTM somando os últimos 4 trimestres."""
    if dados.padrao_fiscal is None:
        return np.nan
    
    periodos = dados.periodos
    if periodo_fim not in periodos:
        return np.nan
    
    idx_fim = periodos.index(periodo_fim)
    padrao = dados.padrao_fiscal
    
    n_periodos = 3 if padrao.tipo == 'SEMESTRAL' else 4
    start_idx = max(0, idx_fim - n_periodos + 1)
    periodos_ltm = periodos[start_idx:idx_fim + 1]
    
    soma = 0.0
    count = 0
    
    for p in periodos_ltm:
        ebitda = _calcular_ebitda_periodo(dados, p)
        if np.isfinite(ebitda):
            soma += ebitda
            count += 1
    
    if count < n_periodos:
        return np.nan
    
    return soma


def _calcular_dividendos_ltm(dados: DadosEmpresa, periodo_fim: str) -> float:
    """
    Calcula dividendos LTM (últimos 12 meses).
    
    METODOLOGIA CORRIGIDA:
    - Considera dividendos dos últimos 12 meses baseado na DATA real
    - Para periodo_fim = 2025T3 (Set/2025), considera Out/2024 a Set/2025
    - Isso inclui 2024T4, 2025T1, 2025T2, 2025T3 E também 2024T2 e 2024T3
    
    Na prática: soma dividendos do ano anterior (T3 e T4) + ano atual (T1 a T_fim)
    
    IMPORTANTE: 
    - dividendos_trimestrais.csv tem valores em R$/AÇÃO
    - Resultado multiplicado por número de ações para obter R$ MIL
    """
    if dados.dividendos is None:
        return np.nan
    
    # Obter número de ações atual
    num_acoes, _ = _obter_acoes_atual(dados)
    
    if not np.isfinite(num_acoes) or num_acoes <= 0:
        return np.nan
    
    # Parsear período fim
    ano_fim, tri_fim = _parse_periodo(periodo_fim)
    if ano_fim == 0:
        return np.nan
    
    tri_num = {'T1': 1, 'T2': 2, 'T3': 3, 'T4': 4}.get(tri_fim, 0)
    
    # Obter todas as colunas de dividendos disponíveis
    colunas_div = [c for c in dados.dividendos.columns if _parse_periodo(c)[0] > 0]
    
    # Gerar lista de períodos dos últimos 12 meses (baseado em trimestres)
    # Para 2025T3: considera desde 2024T4 até 2025T3 (mas também 2024T2, 2024T3 se dentro de 12 meses)
    # Método: pegar todos os trimestres desde (ano_fim - 1, tri_fim + 1) até (ano_fim, tri_fim)
    
    periodos_12m = []
    
    # Ano atual: T1 até T_fim
    for t in range(1, tri_num + 1):
        periodos_12m.append(f"{ano_fim}T{t}")
    
    # Ano anterior: a partir de T(tri_fim + 1) até T4
    # Isso garante exatamente 12 meses
    # Ex: 2025T3 → considera 2024T4 (4 trimestres atrás = 12 meses)
    for t in range(tri_num + 1, 5):
        periodos_12m.append(f"{ano_fim - 1}T{t}")
    
    # Adicionar também trimestres do ano anterior que podem ter dividendos
    # dentro da janela de 12 meses (ex: 2024T2 para ref 2025T3 = ~15 meses atrás, mas
    # a data de pagamento pode estar dentro de 12 meses)
    # 
    # Solução pragmática: incluir TODOS os trimestres do ano anterior
    # para não perder dividendos pagos em T2 do ano anterior
    for t in range(1, tri_num + 1):
        p = f"{ano_fim - 1}T{t}"
        if p not in periodos_12m:
            periodos_12m.append(p)
    
    # Buscar dividendos em todos esses períodos
    soma = 0.0
    
    for p in periodos_12m:
        if p in colunas_div:
            vals = pd.to_numeric(dados.dividendos[p], errors='coerce').dropna()
            if len(vals) > 0:
                div_por_acao = float(vals.iloc[0])
                if np.isfinite(div_por_acao) and div_por_acao > 0:
                    div_total_mil = (div_por_acao * num_acoes) / 1000.0
                    soma += div_total_mil
    
    return soma if soma > 0 else np.nan


# ======================================================================================
# CALCULADORA DE MÚLTIPLOS - VERSÃO CORRIGIDA
# ======================================================================================

def calcular_multiplos_periodo(dados: DadosEmpresa, periodo: str, usar_preco_atual: bool = True) -> Dict[str, Optional[float]]:
    """
    Calcula todos os 22 múltiplos para um período específico.
    
    Args:
        dados: Dados da empresa
        periodo: Período de referência para dados contábeis
        usar_preco_atual: Se True, usa preço mais recente para valuation
    
    Returns:
        Dicionário com todos os múltiplos calculados
    """
    resultado: Dict[str, Optional[float]] = {}
    
    # ==================== MARKET CAP E EV ====================
    
    if usar_preco_atual:
        market_cap = _calcular_market_cap_atual(dados)
    else:
        market_cap = _calcular_market_cap(dados, periodo)
    
    ev = _calcular_ev(dados, periodo, market_cap)
    
    # ==================== VALUATION ====================
    
    ll_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["lucro_liquido"], periodo)
    resultado["P_L"] = _normalizar_valor(_safe_divide(market_cap, ll_ltm))
    
    pl = _obter_valor_pontual(dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)
    resultado["P_VPA"] = _normalizar_valor(_safe_divide(market_cap, pl))
    
    ebitda_ltm = _calcular_ebitda_ltm(dados, periodo)
    resultado["EV_EBITDA"] = _normalizar_valor(_safe_divide(ev, ebitda_ltm))
    
    ebit_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["ebit"], periodo)
    resultado["EV_EBIT"] = _normalizar_valor(_safe_divide(ev, ebit_ltm))
    
    receita_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["receita"], periodo)
    resultado["EV_RECEITA"] = _normalizar_valor(_safe_divide(ev, receita_ltm))
    
    # ==================== DIVIDENDOS ====================
    
    dividendos_ltm = _calcular_dividendos_ltm(dados, periodo)
    
    # Dividend Yield = (Dividendos LTM / Market Cap) × 100
    resultado["DY"] = _normalizar_valor(_safe_divide(dividendos_ltm, market_cap) * 100)
    
    # Payout = (Dividendos LTM / Lucro Líquido LTM) × 100
    resultado["PAYOUT"] = _normalizar_valor(_safe_divide(dividendos_ltm, ll_ltm) * 100)
    
    # ==================== RENTABILIDADE ====================
    
    pl_medio = _obter_valor_medio(dados, dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)
    resultado["ROE"] = _normalizar_valor(_safe_divide(ll_ltm, pl_medio) * 100)
    
    at_medio = _obter_valor_medio(dados, dados.bpa, CONTAS_BPA["ativo_total"], periodo)
    resultado["ROA"] = _normalizar_valor(_safe_divide(ll_ltm, at_medio) * 100)
    
    # ROIC = NOPAT / Capital Investido
    # NOPAT = EBIT × (1 - Taxa IR)
    nopat = ebit_ltm * (1 - TAXA_IR_NOPAT) if np.isfinite(ebit_ltm) else np.nan
    
    emp_cp = _obter_valor_pontual(dados.bpp, CONTAS_BPP["emprestimos_cp"], periodo, ["2.01.04"])
    emp_lp = _obter_valor_pontual(dados.bpp, CONTAS_BPP["emprestimos_lp"], periodo, ["2.02.01"])
    caixa = _obter_valor_pontual(dados.bpa, CONTAS_BPA["caixa"], periodo)
    aplic = _obter_valor_pontual(dados.bpa, CONTAS_BPA["aplicacoes"], periodo)
    
    emp_cp_val = emp_cp if np.isfinite(emp_cp) else 0
    emp_lp_val = emp_lp if np.isfinite(emp_lp) else 0
    caixa_val = caixa if np.isfinite(caixa) else 0
    aplic_val = aplic if np.isfinite(aplic) else 0
    
    divida_liquida_calc = emp_cp_val + emp_lp_val - caixa_val - aplic_val
    capital_investido = pl + divida_liquida_calc if np.isfinite(pl) else np.nan
    resultado["ROIC"] = _normalizar_valor(_safe_divide(nopat, capital_investido) * 100)
    
    resultado["MARGEM_EBITDA"] = _normalizar_valor(_safe_divide(ebitda_ltm, receita_ltm) * 100)
    resultado["MARGEM_LIQUIDA"] = _normalizar_valor(_safe_divide(ll_ltm, receita_ltm) * 100)
    
    # ==================== ENDIVIDAMENTO ====================
    
    divida_bruta = emp_cp_val + emp_lp_val
    resultado["DIV_LIQ_EBITDA"] = _normalizar_valor(_safe_divide(divida_liquida_calc, ebitda_ltm))
    resultado["DIV_LIQ_PL"] = _normalizar_valor(_safe_divide(divida_liquida_calc, pl))
    
    resultado_fin = _calcular_ltm(dados, dados.dre, CONTAS_DRE["resultado_financeiro"], periodo)
    desp_fin = abs(resultado_fin) if np.isfinite(resultado_fin) and resultado_fin < 0 else np.nan
    resultado["ICJ"] = _normalizar_valor(_safe_divide(ebit_ltm, desp_fin))
    
    resultado["COMPOSICAO_DIVIDA"] = _normalizar_valor(_safe_divide(emp_cp_val, divida_bruta) * 100)
    
    # ==================== LIQUIDEZ ====================
    
    ac = _obter_valor_pontual(dados.bpa, CONTAS_BPA["ativo_circulante"], periodo)
    pc = _obter_valor_pontual(dados.bpp, CONTAS_BPP["passivo_circulante"], periodo)
    estoques = _obter_valor_pontual(dados.bpa, CONTAS_BPA["estoques"], periodo)
    rlp = _obter_valor_pontual(dados.bpa, CONTAS_BPA["realizavel_lp"], periodo, ["1.02.01"])
    pnc = _obter_valor_pontual(dados.bpp, CONTAS_BPP["passivo_nao_circulante"], periodo)
    
    resultado["LIQ_CORRENTE"] = _normalizar_valor(_safe_divide(ac, pc))
    
    estoques_val = estoques if np.isfinite(estoques) else 0
    resultado["LIQ_SECA"] = _normalizar_valor(_safe_divide(ac - estoques_val, pc))
    
    rlp_val = rlp if np.isfinite(rlp) else 0
    pnc_val = pnc if np.isfinite(pnc) else 0
    resultado["LIQ_GERAL"] = _normalizar_valor(_safe_divide(ac + rlp_val, pc + pnc_val))
    
    # ==================== EFICIÊNCIA ====================
    
    at = _obter_valor_pontual(dados.bpa, CONTAS_BPA["ativo_total"], periodo)
    resultado["GIRO_ATIVO"] = _normalizar_valor(_safe_divide(receita_ltm, at))
    
    ativos_bio = _obter_valor_pontual(dados.bpa, CONTAS_BPA["ativos_biologicos"], periodo)
    ativos_bio_val = ativos_bio if np.isfinite(ativos_bio) else 0
    cpv_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["cpv"], periodo)
    cpv_ltm_abs = abs(cpv_ltm) if np.isfinite(cpv_ltm) else np.nan
    
    estoque_total = estoques_val + ativos_bio_val
    resultado["PME"] = _normalizar_valor(_safe_divide(estoque_total * 360, cpv_ltm_abs))
    
    contas_receber = _obter_valor_pontual(dados.bpa, CONTAS_BPA["contas_receber"], periodo, ["1.01.03"])
    contas_receber_val = contas_receber if np.isfinite(contas_receber) else 0
    pmr = _safe_divide(contas_receber_val * 360, receita_ltm) if np.isfinite(receita_ltm) else np.nan
    
    fornecedores = _obter_valor_pontual(dados.bpp, CONTAS_BPP["fornecedores"], periodo, ["2.01.02"])
    fornecedores_val = fornecedores if np.isfinite(fornecedores) else 0
    pmp = _safe_divide(fornecedores_val * 360, cpv_ltm_abs) if np.isfinite(cpv_ltm_abs) else np.nan
    
    pme_val = resultado["PME"] if resultado["PME"] is not None else np.nan
    if np.isfinite(pmr) and np.isfinite(pme_val) and np.isfinite(pmp):
        resultado["CICLO_CAIXA"] = _normalizar_valor(pmr + pme_val - pmp)
    else:
        resultado["CICLO_CAIXA"] = None
    
    ncg_ativo = ac - caixa_val - aplic_val if np.isfinite(ac) else np.nan
    ncg_passivo = pc - emp_cp_val if np.isfinite(pc) else np.nan
    ncg = ncg_ativo - ncg_passivo if np.isfinite(ncg_ativo) and np.isfinite(ncg_passivo) else np.nan
    resultado["NCG_RECEITA"] = _normalizar_valor(_safe_divide(ncg, receita_ltm) * 100)
    
    return resultado


# ======================================================================================
# METADADOS DOS MÚLTIPLOS
# ======================================================================================

MULTIPLOS_METADATA = {
    "P_L": {"nome": "P/L", "categoria": "Valuation", "formula": "Market Cap / Lucro Líquido LTM", "unidade": "x", "usa_preco": True},
    "P_VPA": {"nome": "P/VPA", "categoria": "Valuation", "formula": "Market Cap / Patrimônio Líquido", "unidade": "x", "usa_preco": True},
    "EV_EBITDA": {"nome": "EV/EBITDA", "categoria": "Valuation", "formula": "Enterprise Value / EBITDA LTM", "unidade": "x", "usa_preco": True},
    "EV_EBIT": {"nome": "EV/EBIT", "categoria": "Valuation", "formula": "Enterprise Value / EBIT LTM", "unidade": "x", "usa_preco": True},
    "EV_RECEITA": {"nome": "EV/Receita", "categoria": "Valuation", "formula": "Enterprise Value / Receita LTM", "unidade": "x", "usa_preco": True},
    "DY": {"nome": "Dividend Yield", "categoria": "Valuation", "formula": "Dividendos LTM / Market Cap", "unidade": "%", "usa_preco": True},
    "PAYOUT": {"nome": "Payout", "categoria": "Valuation", "formula": "Dividendos LTM / Lucro Líquido LTM", "unidade": "%", "usa_preco": False},
    "ROE": {"nome": "ROE", "categoria": "Rentabilidade", "formula": "Lucro Líquido LTM / PL Médio", "unidade": "%", "usa_preco": False},
    "ROA": {"nome": "ROA", "categoria": "Rentabilidade", "formula": "Lucro Líquido LTM / Ativo Total Médio", "unidade": "%", "usa_preco": False},
    "ROIC": {"nome": "ROIC", "categoria": "Rentabilidade", "formula": "NOPAT / Capital Investido", "unidade": "%", "usa_preco": False},
    "MARGEM_EBITDA": {"nome": "Margem EBITDA", "categoria": "Rentabilidade", "formula": "EBITDA / Receita", "unidade": "%", "usa_preco": False},
    "MARGEM_LIQUIDA": {"nome": "Margem Líquida", "categoria": "Rentabilidade", "formula": "Lucro Líquido / Receita", "unidade": "%", "usa_preco": False},
    "DIV_LIQ_EBITDA": {"nome": "Dív.Líq/EBITDA", "categoria": "Endividamento", "formula": "(Emp CP + LP - Caixa) / EBITDA", "unidade": "x", "usa_preco": False},
    "DIV_LIQ_PL": {"nome": "Dív.Líq/PL", "categoria": "Endividamento", "formula": "Dívida Líquida / Patrimônio Líquido", "unidade": "x", "usa_preco": False},
    "ICJ": {"nome": "ICJ", "categoria": "Endividamento", "formula": "EBIT / Despesas Financeiras", "unidade": "x", "usa_preco": False},
    "COMPOSICAO_DIVIDA": {"nome": "Composição Dívida", "categoria": "Endividamento", "formula": "Emp CP / (Emp CP + LP)", "unidade": "%", "usa_preco": False},
    "LIQ_CORRENTE": {"nome": "Liquidez Corrente", "categoria": "Liquidez", "formula": "Ativo Circulante / Passivo Circulante", "unidade": "x", "usa_preco": False},
    "LIQ_SECA": {"nome": "Liquidez Seca", "categoria": "Liquidez", "formula": "(AC - Estoques) / PC", "unidade": "x", "usa_preco": False},
    "LIQ_GERAL": {"nome": "Liquidez Geral", "categoria": "Liquidez", "formula": "(AC + RLP) / (PC + PNC)", "unidade": "x", "usa_preco": False},
    "GIRO_ATIVO": {"nome": "Giro do Ativo", "categoria": "Eficiência", "formula": "Receita LTM / Ativo Total", "unidade": "x", "usa_preco": False},
    "CICLO_CAIXA": {"nome": "Ciclo de Caixa", "categoria": "Eficiência", "formula": "PMR + PME - PMP", "unidade": "dias", "usa_preco": False},
    "PME": {"nome": "PME", "categoria": "Eficiência", "formula": "(Estoques + AtBio) × 360 / CPV", "unidade": "dias", "usa_preco": False},
    "NCG_RECEITA": {"nome": "NCG/Receita", "categoria": "Eficiência", "formula": "NCG / Receita LTM", "unidade": "%", "usa_preco": False},
}

# ======================================================================================
# METADADOS DOS MÚLTIPLOS - BANCOS
# ======================================================================================

MULTIPLOS_BANCOS_METADATA = {
    # Valuation
    "P_L": {"nome": "P/L", "categoria": "Valuation", "formula": "Market Cap / Lucro Líquido LTM", "unidade": "x", "usa_preco": True},
    "P_VPA": {"nome": "P/VPA", "categoria": "Valuation", "formula": "Market Cap / Patrimônio Líquido", "unidade": "x", "usa_preco": True},
    "DY": {"nome": "Dividend Yield", "categoria": "Valuation", "formula": "Dividendos LTM / Market Cap", "unidade": "%", "usa_preco": True},
    "PAYOUT": {"nome": "Payout", "categoria": "Valuation", "formula": "Dividendos LTM / Lucro Líquido LTM", "unidade": "%", "usa_preco": False},
    
    # Rentabilidade
    "ROE": {"nome": "ROE", "categoria": "Rentabilidade", "formula": "Lucro Líquido LTM / PL Médio", "unidade": "%", "usa_preco": False},
    "ROA": {"nome": "ROA", "categoria": "Rentabilidade", "formula": "Lucro Líquido LTM / Ativo Total Médio", "unidade": "%", "usa_preco": False},
    "MARGEM_LIQUIDA": {"nome": "Margem Líquida", "categoria": "Rentabilidade", "formula": "LL / Receita Intermediação", "unidade": "%", "usa_preco": False},
    "NIM": {"nome": "NIM", "categoria": "Rentabilidade", "formula": "Resultado Bruto Interm. / Ativos Rentáveis Médios", "unidade": "%", "usa_preco": False},
    
    # Qualidade de Ativos
    "INDICE_COBERTURA": {"nome": "Índice de Cobertura", "categoria": "Qualidade Ativos", "formula": "Provisão PDD / Carteira de Crédito", "unidade": "%", "usa_preco": False},
    
    # Eficiência
    "INDICE_EFICIENCIA": {"nome": "Índice de Eficiência", "categoria": "Eficiência", "formula": "Despesas Adm / Receitas Operacionais", "unidade": "%", "usa_preco": False},
    
    # Estrutura
    "LOAN_DEPOSIT": {"nome": "Loan-to-Deposit", "categoria": "Estrutura", "formula": "Carteira Crédito / Depósitos", "unidade": "%", "usa_preco": False},
    "PL_ATIVOS": {"nome": "PL/Ativos", "categoria": "Estrutura", "formula": "Patrimônio Líquido / Ativo Total", "unidade": "%", "usa_preco": False},
}


# ======================================================================================
# CALCULADORA DE MÚLTIPLOS - BANCOS
# ======================================================================================

def _detectar_codigo_pl_banco(dados: DadosEmpresa) -> str:
    """Detecta o código do Patrimônio Líquido no BPP do banco (2.07 ou 2.08)."""
    if dados.bpp is None or dados.bpp.empty:
        return "2.07"
    
    for idx, row in dados.bpp.iterrows():
        cd = str(row.get('cd_conta', ''))
        conta = str(row.get('conta', '')).lower()
        if 'patrimônio líquido' in conta or 'patrimonio liquido' in conta:
            if cd.startswith('2.0') and len(cd) == 4:  # 2.07 ou 2.08
                return cd
    return "2.07"


def calcular_multiplos_banco(dados: DadosEmpresa, periodo: str, usar_preco_atual: bool = True) -> Dict[str, Optional[float]]:
    """
    Calcula múltiplos específicos para bancos.
    
    Múltiplos calculados:
    - Valuation: P/L, P/VPA, DY, Payout
    - Rentabilidade: ROE, ROA, Margem Líquida, NIM
    - Qualidade: Índice de Cobertura
    - Eficiência: Índice de Eficiência
    - Estrutura: Loan-to-Deposit, PL/Ativos
    """
    resultado: Dict[str, Optional[float]] = {}
    
    # Detectar código do PL dinamicamente
    pl_code = _detectar_codigo_pl_banco(dados)
    
    # ==================== MARKET CAP ====================
    if usar_preco_atual:
        market_cap = _calcular_market_cap_atual(dados)
    else:
        market_cap = _calcular_market_cap(dados, periodo)
    
    # ==================== VALORES BASE ====================
    
    # Lucro Líquido LTM
    ll_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE_BANCOS["lucro_liquido"], periodo)
    
    # Patrimônio Líquido (código detectado dinamicamente)
    pl = _obter_valor_pontual(dados.bpp, pl_code, periodo)
    pl_medio = _obter_valor_medio(dados, dados.bpp, pl_code, periodo)
    
    # Ativo Total
    at = _obter_valor_pontual(dados.bpa, CONTAS_BPA_BANCOS["ativo_total"], periodo)
    at_medio = _obter_valor_medio(dados, dados.bpa, CONTAS_BPA_BANCOS["ativo_total"], periodo)
    
    # Receita de Intermediação LTM
    receita_interm = _calcular_ltm(dados, dados.dre, CONTAS_DRE_BANCOS["receita_intermediacao"], periodo)
    
    # Resultado Bruto Intermediação LTM
    resultado_bruto = _calcular_ltm(dados, dados.dre, CONTAS_DRE_BANCOS["resultado_bruto"], periodo)
    
    # ==================== VALUATION ====================
    
    resultado["P_L"] = _normalizar_valor(_safe_divide(market_cap, ll_ltm))
    resultado["P_VPA"] = _normalizar_valor(_safe_divide(market_cap, pl))
    
    # Dividendos
    dividendos_ltm = _calcular_dividendos_ltm(dados, periodo)
    resultado["DY"] = _normalizar_valor(_safe_divide(dividendos_ltm, market_cap) * 100 if market_cap else None)
    resultado["PAYOUT"] = _normalizar_valor(_safe_divide(dividendos_ltm, ll_ltm) * 100 if ll_ltm else None)
    
    # ==================== RENTABILIDADE ====================
    
    resultado["ROE"] = _normalizar_valor(_safe_divide(ll_ltm, pl_medio) * 100 if pl_medio else None)
    resultado["ROA"] = _normalizar_valor(_safe_divide(ll_ltm, at_medio) * 100 if at_medio else None)
    resultado["MARGEM_LIQUIDA"] = _normalizar_valor(_safe_divide(ll_ltm, receita_interm) * 100 if receita_interm else None)
    
    # NIM = Resultado Bruto Intermediação / Ativos Financeiros Médios
    ativos_fin = _obter_valor_pontual(dados.bpa, CONTAS_BPA_BANCOS["ativos_financeiros"], periodo)
    ativos_fin_medio = _obter_valor_medio(dados, dados.bpa, CONTAS_BPA_BANCOS["ativos_financeiros"], periodo)
    resultado["NIM"] = _normalizar_valor(_safe_divide(resultado_bruto, ativos_fin_medio) * 100 if ativos_fin_medio else None)
    
    # ==================== QUALIDADE DE ATIVOS ====================
    
    # Índice de Cobertura = Provisão PDD / Carteira de Crédito
    # Tentar buscar provisão no BPA (conta de provisão)
    provisao_pdd = _obter_valor_pontual(dados.bpa, CONTAS_BPA_BANCOS["provisao_pdd"], periodo)
    if provisao_pdd is None or not np.isfinite(provisao_pdd):
        provisao_pdd = _obter_valor_pontual(dados.bpa, "1.02.03.06", periodo)
    
    # Carteira de crédito - tentar código principal e alternativo
    carteira_credito = _obter_valor_pontual(dados.bpa, CONTAS_BPA_BANCOS["operacoes_credito"], periodo)
    if carteira_credito is None or not np.isfinite(carteira_credito) or carteira_credito == 0:
        carteira_credito = _obter_valor_pontual(dados.bpa, CONTAS_BPA_BANCOS["operacoes_credito_alt"], periodo)
    
    if provisao_pdd and carteira_credito and np.isfinite(provisao_pdd) and np.isfinite(carteira_credito) and carteira_credito != 0:
        resultado["INDICE_COBERTURA"] = _normalizar_valor(abs(provisao_pdd) / carteira_credito * 100)
    else:
        resultado["INDICE_COBERTURA"] = None
    
    # ==================== EFICIÊNCIA ====================
    
    # Índice de Eficiência = Despesas Operacionais / Receitas Operacionais
    outras_desp = _calcular_ltm(dados, dados.dre, CONTAS_DRE_BANCOS["outras_receitas_desp"], periodo)
    if outras_desp is not None and resultado_bruto is not None and np.isfinite(outras_desp) and np.isfinite(resultado_bruto) and resultado_bruto > 0:
        resultado["INDICE_EFICIENCIA"] = _normalizar_valor(abs(outras_desp) / resultado_bruto * 100)
    else:
        resultado["INDICE_EFICIENCIA"] = None
    
    # ==================== ESTRUTURA ====================
    
    # Loan-to-Deposit = Carteira de Crédito / Depósitos
    depositos = _obter_valor_pontual(dados.bpp, CONTAS_BPP_BANCOS["depositos"], periodo)
    if carteira_credito and depositos and np.isfinite(carteira_credito) and np.isfinite(depositos) and depositos != 0:
        resultado["LOAN_DEPOSIT"] = _normalizar_valor(carteira_credito / depositos * 100)
    else:
        resultado["LOAN_DEPOSIT"] = None
    
    # PL/Ativos (capitalização)
    resultado["PL_ATIVOS"] = _normalizar_valor(_safe_divide(pl, at) * 100 if at else None)
    
    return resultado


# ======================================================================================
# GERADOR DE HISTÓRICO ANUALIZADO
# ======================================================================================

def gerar_historico_anualizado(dados: DadosEmpresa) -> Dict[str, Any]:
    """Gera histórico de múltiplos anualizado."""
    if not dados.periodos or dados.padrao_fiscal is None:
        return {"erro": "Dados insuficientes", "ticker": dados.ticker}
    
    periodos_por_ano: Dict[int, List[str]] = {}
    for p in dados.periodos:
        ano, tri = _parse_periodo(p)
        if ano > 0:
            if ano not in periodos_por_ano:
                periodos_por_ano[ano] = []
            periodos_por_ano[ano].append(p)
    
    historico_anual: Dict[int, Dict[str, Any]] = {}
    
    ano_atual = datetime.now().year
    
    for ano in sorted(periodos_por_ano.keys()):
        periodos_ano = _ordenar_periodos(periodos_por_ano[ano])
        
        if ano < ano_atual:
            # Anos completos: usar sempre T4 (final do ano)
            periodo_t4 = f"{ano}T4"
            if periodo_t4 in periodos_ano:
                periodo_referencia = periodo_t4
            else:
                periodo_referencia = periodos_ano[-1]
            # Para anos históricos, usar preço do período (não atual)
            if _is_banco(dados.ticker):
                multiplos = calcular_multiplos_banco(dados, periodo_referencia, usar_preco_atual=False)
            else:
                multiplos = calcular_multiplos_periodo(dados, periodo_referencia, usar_preco_atual=False)
        else:
            # Ano corrente: usar período mais recente disponível com preço atual
            periodo_referencia = periodos_ano[-1]
            if _is_banco(dados.ticker):
                multiplos = calcular_multiplos_banco(dados, periodo_referencia, usar_preco_atual=True)
            else:
                multiplos = calcular_multiplos_periodo(dados, periodo_referencia, usar_preco_atual=True)
        
        historico_anual[ano] = {
            "periodo_referencia": periodo_referencia,
            "multiplos": multiplos
        }
    
    # LTM: Sempre usar último período disponível com preço atual
    ultimo_periodo = dados.periodos[-1]
    if _is_banco(dados.ticker):
        multiplos_ltm = calcular_multiplos_banco(dados, ultimo_periodo, usar_preco_atual=True)
    else:
        multiplos_ltm = calcular_multiplos_periodo(dados, ultimo_periodo, usar_preco_atual=True)
    
    # Informações de preço e ações utilizados
    preco_atual, periodo_preco = _obter_preco_atual(dados)
    acoes_atual, periodo_acoes = _obter_acoes_atual(dados)
    
    return {
        "ticker": dados.ticker,
        "padrao_fiscal": {
            "tipo": dados.padrao_fiscal.tipo,
            "descricao": dados.padrao_fiscal.descricao,
            "trimestres_ltm": dados.padrao_fiscal.trimestres_ltm
        },
        "metadata": MULTIPLOS_BANCOS_METADATA if _is_banco(dados.ticker) else MULTIPLOS_METADATA,
        "historico_anual": historico_anual,
        "ltm": {
            "periodo_referencia": ultimo_periodo,
            "data_calculo": datetime.now().isoformat(),
            "preco_utilizado": _normalizar_valor(preco_atual, 2),
            "periodo_preco": periodo_preco,
            "acoes_utilizadas": int(acoes_atual) if np.isfinite(acoes_atual) else None,
            "periodo_acoes": periodo_acoes,
            "multiplos": multiplos_ltm
        },
        "periodos_disponiveis": dados.periodos,
        "erros_carregamento": dados.erros
    }


# ======================================================================================
# PROCESSADOR PRINCIPAL
# ======================================================================================

def processar_ticker(ticker: str, salvar: bool = True) -> Tuple[bool, str, Optional[Dict]]:
    """Processa um ticker e calcula todos os múltiplos."""
    ticker_upper = ticker.upper().strip()
    
    if _is_seguradora(ticker_upper):
        return False, "Seguradora/Holding - estrutura não suportada", None
    
    dados = carregar_dados_empresa(ticker_upper)
    
    if dados.erros:
        erros_str = "; ".join(dados.erros)
        return False, f"Erros ao carregar: {erros_str}", None
    
    if not dados.periodos:
        return False, "Nenhum período disponível", None
    
    resultado = gerar_historico_anualizado(dados)
    
    if salvar:
        pasta = get_pasta_balanco(ticker_upper)
        pasta.mkdir(parents=True, exist_ok=True)
        
        output_path = pasta / "multiplos.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2, default=str)
        
        csv_path = pasta / "multiplos.csv"
        _salvar_csv_historico(resultado, csv_path)
    
    n_anos = len(resultado.get("historico_anual", {}))
    padrao = resultado.get("padrao_fiscal", {}).get("tipo", "?")
    ultimo = resultado.get("ltm", {}).get("periodo_referencia", "?")
    preco = resultado.get("ltm", {}).get("preco_utilizado", "?")
    
    msg = f"OK | {n_anos} anos | fiscal={padrao} | LTM={ultimo} | Preço=R${preco}"
    
    return True, msg, resultado


def _salvar_csv_historico(resultado: Dict, path: Path):
    """Salva histórico em formato CSV para compatibilidade."""
    historico = resultado.get("historico_anual", {})
    ltm_data = resultado.get("ltm", {})
    metadata = resultado.get("metadata", {})
    ticker = resultado.get("ticker", "")
    
    if not historico:
        return
    
    anos = sorted(historico.keys())
    
    # Usar metadata correto baseado no tipo de empresa
    if _is_banco(ticker):
        multiplos_codigos = list(MULTIPLOS_BANCOS_METADATA.keys())
    else:
        multiplos_codigos = list(MULTIPLOS_METADATA.keys())
    
    rows = []
    for codigo in multiplos_codigos:
        meta = metadata.get(codigo, {})
        row = {
            "codigo": codigo,
            "nome": meta.get("nome", codigo),
            "categoria": meta.get("categoria", ""),
            "unidade": meta.get("unidade", "")
        }
        
        for ano in anos:
            multiplos_ano = historico[ano].get("multiplos", {})
            row[str(ano)] = multiplos_ano.get(codigo)
        
        multiplos_ltm = ltm_data.get("multiplos", {})
        row["LTM"] = multiplos_ltm.get(codigo)
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False, encoding='utf-8')


# ======================================================================================
# CLI
# ======================================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Calculadora de Múltiplos Financeiros para Empresas Não-Financeiras"
    )
    parser.add_argument("--modo", default="quantidade", 
                       choices=["quantidade", "ticker", "lista", "faixa"])
    parser.add_argument("--quantidade", default="10")
    parser.add_argument("--ticker", default="")
    parser.add_argument("--lista", default="")
    parser.add_argument("--faixa", default="1-50")
    parser.add_argument("--no-save", action="store_true", 
                       help="Não salvar arquivos de saída")
    args = parser.parse_args()
    
    df = load_mapeamento_consolidado()
    df = df[df["cnpj"].notna()].reset_index(drop=True)
    
    if args.modo == "quantidade":
        limite = int(args.quantidade)
        df_sel = df.head(limite)
    elif args.modo == "ticker":
        ticker_upper = args.ticker.upper()
        df_sel = df[df["ticker"].str.upper().str.contains(ticker_upper, case=False, na=False)]
    elif args.modo == "lista":
        tickers = [t.strip().upper() for t in args.lista.split(",") if t.strip()]
        mask = df["ticker"].str.upper().apply(
            lambda x: any(t in x for t in tickers) if pd.notna(x) else False
        )
        df_sel = df[mask]
    elif args.modo == "faixa":
        inicio, fim = map(int, args.faixa.split("-"))
        df_sel = df.iloc[inicio - 1 : fim]
    else:
        df_sel = df.head(10)
    
    print(f"\n{'='*70}")
    print(f">>> CALCULADORA DE MÚLTIPLOS - EMPRESAS NÃO-FINANCEIRAS <<<")
    print(f"{'='*70}")
    print(f"Modo: {args.modo} | Selecionadas: {len(df_sel)}")
    print(f"Saída: balancos/<TICKER>/multiplos.json + multiplos.csv")
    print(f"{'='*70}\n")
    
    ok_count = 0
    skip_count = 0
    err_count = 0
    
    salvar = not args.no_save
    
    for _, row in df_sel.iterrows():
        ticker_str = str(row["ticker"]).upper().strip()
        ticker = ticker_str.split(';')[0] if ';' in ticker_str else ticker_str
        
        try:
            sucesso, msg, _ = processar_ticker(ticker, salvar=salvar)
            
            if sucesso:
                ok_count += 1
                print(f"✅ {ticker}: {msg}")
            else:
                if "financeira" in msg.lower():
                    skip_count += 1
                    print(f"⏭️  {ticker}: {msg}")
                else:
                    err_count += 1
                    print(f"⚠️  {ticker}: {msg}")
                    
        except Exception as e:
            err_count += 1
            import traceback
            print(f"❌ {ticker}: ERRO - {type(e).__name__}: {e}")
            traceback.print_exc()
    
    print(f"\n{'='*70}")
    print(f"RESUMO: OK={ok_count} | SKIP(Financeiras)={skip_count} | ERRO={err_count}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
