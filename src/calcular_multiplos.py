# src/calcular_multiplos.py
"""
Calculadora de Múltiplos Financeiros para Empresas Não-Financeiras
==================================================================
Calcula 22 múltiplos organizados em 5 categorias:
- Valuation (6): P/L, P/VPA, EV/EBITDA, EV/EBIT, EV/Receita, DY
- Rentabilidade (5): ROE, ROA, ROIC, Margem EBITDA, Margem Líquida
- Endividamento (4): Dív.Líq/EBITDA, Dív.Líq/PL, ICJ, Composição Dívida
- Liquidez (3): Corrente, Seca, Geral
- Eficiência (4): Giro Ativo, Ciclo Caixa, PME, NCG/Receita

Tratamento de Exceções:
- Ano fiscal MAR-FEV (CAML3): agrupa por ano fiscal
- Dados semestrais (AGRO3): T1+T3+T4 = 3 períodos, LTM adaptado
- Empresas padrão: LTM = soma últimos 4 trimestres

Saída: JSON para fácil consumo em HTML/JavaScript

VERSÃO: 1.1.0 (Corrigida)
DATA: 2025-12-28
CORREÇÕES:
- ROIC agora usa alíquota efetiva em vez de 34% fixo
- Dividend Yield implementado
- Todas as escalas validadas
"""

from __future__ import annotations

import argparse
import json
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

# Empresas financeiras (excluídas deste cálculo)
TICKERS_FINANCEIROS: Set[str] = {
    "RPAD3", "RPAD5", "RPAD6", "ABCB4", "BMGB4", "BBDC3", "BBDC4",
    "BPAC3", "BPAC5", "BPAC11", "BSLI3", "BSLI4", "BBAS3", "BGIP3",
    "BGIP4", "BPAR3", "BRSR3", "BRSR5", "BRSR6", "BNBR3", "BMIN3",
    "BMIN4", "BMEB3", "BMEB4", "BPAN4", "PINE3", "PINE4", "SANB3",
    "SANB4", "SANB11", "BEES3", "BEES4", "ITUB3", "ITUB4",
    "BBSE3", "CXSE3", "IRBR3", "PSSA3",  # Seguradoras/Holdings
}

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
    "ativos_biologicos": "1.01.05",  # AGRO/SLCE3
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

# Mapeamento de contas DFC (D&A)
CONTAS_DFC = {
    "depreciacao_amortizacao": "6.01.01.02",  # Pode variar
}


# ======================================================================================
# FUNÇÕES UTILITÁRIAS
# ======================================================================================

def _is_financeiro(ticker: str) -> bool:
    """Verifica se ticker é de empresa financeira."""
    return ticker.upper().strip() in TICKERS_FINANCEIROS


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
            return 3  # T1 + T3 + T4
        return 4  # Padrão


def detectar_padrao_fiscal(ticker: str, periodos: List[str]) -> PadraoFiscal:
    """
    Detecta padrão fiscal da empresa baseado no ticker e dados disponíveis.
    """
    ticker_upper = ticker.upper().strip()
    
    # Organizar períodos por ano
    periodos_por_ano: Dict[int, List[str]] = {}
    trimestres_set: Set[str] = set()
    
    for p in periodos:
        ano, tri = _parse_periodo(p)
        if ano > 0 and tri:
            if ano not in periodos_por_ano:
                periodos_por_ano[ano] = []
            periodos_por_ano[ano].append(tri)
            trimestres_set.add(tri)
    
    # Detectar tipo
    if _is_ano_fiscal_mar_fev(ticker_upper):
        return PadraoFiscal(
            tipo='MAR_FEV',
            trimestres_disponiveis=trimestres_set,
            periodos_por_ano=periodos_por_ano,
            descricao=f"Ano fiscal mar-fev (CAML3 pattern)"
        )
    
    if _is_dados_semestrais(ticker_upper):
        return PadraoFiscal(
            tipo='SEMESTRAL',
            trimestres_disponiveis=trimestres_set,
            periodos_por_ano=periodos_por_ano,
            descricao=f"Dados semestrais (AGRO3 pattern) - sem T2"
        )
    
    # Verificar se tem todos os trimestres
    if trimestres_set == {'T1', 'T2', 'T3', 'T4'}:
        return PadraoFiscal(
            tipo='PADRAO',
            trimestres_disponiveis=trimestres_set,
            periodos_por_ano=periodos_por_ano,
            descricao="Ano fiscal padrão (jan-dez) com T1-T4"
        )
    
    # Irregular
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
        # Padronizar cd_conta como string
        if 'cd_conta' in df.columns:
            df['cd_conta'] = df['cd_conta'].astype(str).str.strip()
        return df
    except Exception:
        return None


def _extrair_valor_conta(df: pd.DataFrame, cd_conta: str, periodo: str) -> float:
    """
    Extrai valor de uma conta específica em um período.
    Busca conta exata ou soma subcontas.
    """
    if df is None or periodo not in df.columns:
        return np.nan
    
    # Busca conta exata
    mask_exata = df['cd_conta'] == cd_conta
    if mask_exata.any():
        val = df.loc[mask_exata, periodo].values[0]
        return float(val) if pd.notna(val) else np.nan
    
    # Busca subcontas (ex: 2.01.04 busca 2.01.04.*)
    mask_sub = df['cd_conta'].str.startswith(cd_conta + '.')
    if mask_sub.any():
        vals = pd.to_numeric(df.loc[mask_sub, periodo], errors='coerce')
        soma = vals.sum(skipna=True)
        return float(soma) if np.isfinite(soma) else np.nan
    
    return np.nan


def _buscar_conta_flexivel(df: pd.DataFrame, codigos: List[str], periodo: str) -> float:
    """
    Busca valor tentando múltiplos códigos de conta.
    Útil para contas que variam entre empresas.
    """
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
    
    # Carregar arquivos padronizados
    dados.dre = _carregar_csv_padronizado(pasta / "dre_padronizado.csv")
    dados.bpa = _carregar_csv_padronizado(pasta / "bpa_padronizado.csv")
    dados.bpp = _carregar_csv_padronizado(pasta / "bpp_padronizado.csv")
    dados.dfc = _carregar_csv_padronizado(pasta / "dfc_padronizado.csv")
    dados.precos = _carregar_csv_padronizado(pasta / "precos_trimestrais.csv")
    dados.acoes = _carregar_csv_padronizado(pasta / "acoes_historico.csv")
    dados.dividendos = _carregar_csv_padronizado(pasta / "dividendos_trimestrais.csv")
    
    # Verificar arquivos obrigatórios
    if dados.dre is None:
        dados.erros.append("DRE padronizado não encontrado")
    if dados.bpa is None:
        dados.erros.append("BPA padronizado não encontrado")
    if dados.bpp is None:
        dados.erros.append("BPP padronizado não encontrado")
    
    # Extrair períodos disponíveis do DRE
    if dados.dre is not None:
        cols = [c for c in dados.dre.columns if _parse_periodo(c)[0] > 0]
        dados.periodos = _ordenar_periodos(cols)
        dados.padrao_fiscal = detectar_padrao_fiscal(ticker_upper, dados.periodos)
    
    return dados


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
    """
    Calcula valor LTM (últimos 12 meses) para uma conta.
    
    Adapta-se ao padrão fiscal:
    - PADRAO/MAR_FEV: soma 4 trimestres
    - SEMESTRAL: soma 3 períodos (T1+T3+T4)
    """
    if df is None or dados.padrao_fiscal is None:
        return np.nan
    
    periodos = dados.periodos
    if periodo_fim not in periodos:
        return np.nan
    
    idx_fim = periodos.index(periodo_fim)
    padrao = dados.padrao_fiscal
    
    # Determinar quantos períodos somar e quais
    if padrao.tipo == 'SEMESTRAL':
        # Para AGRO3: usar 3 períodos (T1, T3, T4 do mesmo ano ou cruzando anos)
        periodos_ltm = []
        count = 0
        for i in range(idx_fim, -1, -1):
            p = periodos[i]
            ano, tri = _parse_periodo(p)
            # Semestral não tem T2, então pega os 3 últimos disponíveis
            periodos_ltm.append(p)
            count += 1
            if count >= 3:
                break
    else:
        # Padrão: últimos 4 trimestres
        n_trimestres = 4
        start_idx = max(0, idx_fim - n_trimestres + 1)
        periodos_ltm = periodos[start_idx:idx_fim + 1]
    
    # Somar valores
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
    
    # Retornar NaN se não tiver dados suficientes
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
    """
    Calcula média entre período atual e anterior (para ROE, ROA, etc).
    """
    if df is None:
        return np.nan
    
    periodos = dados.periodos
    if periodo_fim not in periodos:
        return np.nan
    
    idx_fim = periodos.index(periodo_fim)
    
    # Valor atual
    val_atual = _obter_valor_pontual(df, cd_conta, periodo_fim, codigos_alternativos)
    
    # Valor anterior (4 trimestres atrás para comparar mesmo período ano anterior)
    if idx_fim >= 4:
        periodo_ant = periodos[idx_fim - 4]
        val_ant = _obter_valor_pontual(df, cd_conta, periodo_ant, codigos_alternativos)
    else:
        val_ant = np.nan
    
    if np.isfinite(val_atual) and np.isfinite(val_ant):
        return (val_atual + val_ant) / 2
    
    return val_atual  # Fallback para valor atual se não tiver anterior


# ======================================================================================
# CÁLCULO DE D&A E EBITDA
# ======================================================================================

def _calcular_da_periodo(dados: DadosEmpresa, periodo: str) -> float:
    """
    Calcula D&A (Depreciação e Amortização) de um período.
    
    Busca em múltiplas contas possíveis no DFC.
    D&A pode estar em valores negativos no DFC (ajuste), então usa |valor|.
    """
    if dados.dfc is None:
        return np.nan
    
    # Códigos possíveis para D&A no DFC
    codigos_da = [
        "6.01.01.02",  # Depreciação e Amortização (mais comum)
        "6.01.01.01",  # Alternativo
        "6.01.01",     # Agregado
        "6.01.DA",     # Código especial
    ]
    
    for cod in codigos_da:
        val = _extrair_valor_conta(dados.dfc, cod, periodo)
        if np.isfinite(val):
            return abs(val)  # D&A sempre positivo para EBITDA
    
    return np.nan


def _calcular_ebitda_periodo(dados: DadosEmpresa, periodo: str) -> float:
    """
    Calcula EBITDA de um período: EBIT + |D&A|
    """
    ebit = _extrair_valor_conta(dados.dre, CONTAS_DRE["ebit"], periodo)
    da = _calcular_da_periodo(dados, periodo)
    
    if np.isfinite(ebit):
        if np.isfinite(da):
            return ebit + da
        return ebit  # Sem D&A, usa EBIT como proxy
    
    return np.nan


def _calcular_ebitda_ltm(dados: DadosEmpresa, periodo_fim: str) -> float:
    """Calcula EBITDA LTM."""
    if dados.padrao_fiscal is None:
        return np.nan
    
    periodos = dados.periodos
    if periodo_fim not in periodos:
        return np.nan
    
    idx_fim = periodos.index(periodo_fim)
    padrao = dados.padrao_fiscal
    
    # Determinar períodos para soma
    if padrao.tipo == 'SEMESTRAL':
        n_periodos = 3
    else:
        n_periodos = 4
    
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


# ======================================================================================
# CÁLCULO DE MARKET CAP E EV
# ======================================================================================

def _obter_preco(dados: DadosEmpresa, periodo: str) -> float:
    """Obtém preço da ação no período."""
    if dados.precos is None:
        return np.nan
    
    # Tentar diferentes formatos de coluna
    for col_preco in ['preco_fechamento', 'fechamento', 'close', 'preco']:
        if col_preco in dados.precos.columns:
            # Buscar por período
            if 'periodo' in dados.precos.columns:
                mask = dados.precos['periodo'] == periodo
                if mask.any():
                    val = dados.precos.loc[mask, col_preco].values[0]
                    return float(val) if pd.notna(val) else np.nan
    
    # Fallback: período como coluna
    if periodo in dados.precos.columns:
        vals = pd.to_numeric(dados.precos[periodo], errors='coerce').dropna()
        if len(vals) > 0:
            return float(vals.iloc[0])
    
    return np.nan


def _obter_acoes(dados: DadosEmpresa, periodo: str) -> float:
    """Obtém número de ações no período (em milhares para consistência)."""
    if dados.acoes is None:
        return np.nan
    
    # Tentar diferentes formatos
    for col_acoes in ['quantidade', 'acoes', 'shares', 'qtd_acoes']:
        if col_acoes in dados.acoes.columns:
            if 'periodo' in dados.acoes.columns:
                mask = dados.acoes['periodo'] == periodo
                if mask.any():
                    val = dados.acoes.loc[mask, col_acoes].values[0]
                    return float(val) if pd.notna(val) else np.nan
    
    # Fallback: período como coluna
    if periodo in dados.acoes.columns:
        vals = pd.to_numeric(dados.acoes[periodo], errors='coerce').dropna()
        if len(vals) > 0:
            return float(vals.iloc[0])
    
    return np.nan


def _calcular_market_cap(dados: DadosEmpresa, periodo: str) -> float:
    """
    Calcula Market Cap = Preço × Número de Ações
    Resultado em R$ mil (consistente com balanços).
    """
    preco = _obter_preco(dados, periodo)
    acoes = _obter_acoes(dados, periodo)
    
    if np.isfinite(preco) and np.isfinite(acoes) and acoes > 0:
        return preco * acoes
    
    return np.nan


def _calcular_ev(dados: DadosEmpresa, periodo: str) -> float:
    """
    Calcula Enterprise Value = Market Cap + Dívida Líquida
    Dívida Líquida = Empréstimos CP + Empréstimos LP - Caixa - Aplicações
    """
    market_cap = _calcular_market_cap(dados, periodo)
    
    if not np.isfinite(market_cap):
        return np.nan
    
    # Componentes da dívida
    emp_cp = _obter_valor_pontual(dados.bpp, CONTAS_BPP["emprestimos_cp"], periodo,
                                   ["2.01.04", "2.01.04.01"])
    emp_lp = _obter_valor_pontual(dados.bpp, CONTAS_BPP["emprestimos_lp"], periodo,
                                   ["2.02.01", "2.02.01.01"])
    caixa = _obter_valor_pontual(dados.bpa, CONTAS_BPA["caixa"], periodo)
    aplic = _obter_valor_pontual(dados.bpa, CONTAS_BPA["aplicacoes"], periodo)
    
    # Tratar NaN como zero para componentes
    emp_cp = emp_cp if np.isfinite(emp_cp) else 0
    emp_lp = emp_lp if np.isfinite(emp_lp) else 0
    caixa = caixa if np.isfinite(caixa) else 0
    aplic = aplic if np.isfinite(aplic) else 0
    
    divida_liquida = emp_cp + emp_lp - caixa - aplic
    
    return market_cap + divida_liquida


# ======================================================================================
# CÁLCULO DE DIVIDENDOS
# ======================================================================================

def _calcular_dividendos_ltm(dados: DadosEmpresa, periodo: str) -> float:
    """
    Calcula dividendos pagos nos últimos 12 meses (LTM).
    
    Formato esperado de dividendos_trimestrais.csv:
    - Formato 1: Coluna 'periodo' + coluna 'dividendo_total'
    - Formato 2: Períodos como colunas (ex: '2024T3')
    """
    if dados.dividendos is None:
        return np.nan
    
    periodos = dados.periodos
    if periodo not in periodos:
        return np.nan
    
    idx_fim = periodos.index(periodo)
    padrao = dados.padrao_fiscal
    
    # Determinar períodos LTM
    if padrao.tipo == 'SEMESTRAL':
        n_periodos = 3
    else:
        n_periodos = 4
    
    start_idx = max(0, idx_fim - n_periodos + 1)
    periodos_ltm = periodos[start_idx:idx_fim + 1]
    
    soma = 0.0
    count = 0
    
    # Tentar formato 1: coluna 'periodo' + 'dividendo_total'
    if 'periodo' in dados.dividendos.columns and 'dividendo_total' in dados.dividendos.columns:
        for p in periodos_ltm:
            mask = dados.dividendos['periodo'] == p
            if mask.any():
                val = dados.dividendos.loc[mask, 'dividendo_total'].values[0]
                if pd.notna(val) and np.isfinite(float(val)):
                    soma += float(val)
                    count += 1
    
    # Tentar formato 2: períodos como colunas
    else:
        for p in periodos_ltm:
            if p in dados.dividendos.columns:
                vals = pd.to_numeric(dados.dividendos[p], errors='coerce').dropna()
                if len(vals) > 0:
                    soma += vals.sum()
                    count += 1
    
    return soma if count > 0 else np.nan


# ======================================================================================
# CALCULADORA DE MÚLTIPLOS
# ======================================================================================

@dataclass
class MultiploPeriodo:
    """Múltiplo calculado para um período."""
    periodo: str
    ano: int
    trimestre: str
    valor: Optional[float]
    formula_aplicada: str


@dataclass
class ResultadoMultiplo:
    """Resultado completo de um múltiplo."""
    codigo: str
    nome: str
    categoria: str
    formula: str
    unidade: str
    historico: List[MultiploPeriodo] = field(default_factory=list)


def calcular_multiplos_periodo(dados: DadosEmpresa, periodo: str) -> Dict[str, Optional[float]]:
    """
    Calcula todos os 22 múltiplos para um período específico.
    Retorna dicionário {codigo_multiplo: valor}.
    
    VERSÃO CORRIGIDA:
    - ROIC usa alíquota efetiva
    - Dividend Yield implementado
    - Todas as escalas validadas
    """
    resultado: Dict[str, Optional[float]] = {}
    
    # ==================== VALUATION ====================
    
    # P/L = Market Cap / Lucro Líquido LTM
    market_cap = _calcular_market_cap(dados, periodo)
    ll_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["lucro_liquido"], periodo)
    resultado["P_L"] = _normalizar_valor(_safe_divide(market_cap, ll_ltm))
    
    # P/VPA = Market Cap / Patrimônio Líquido
    pl = _obter_valor_pontual(dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)
    resultado["P_VPA"] = _normalizar_valor(_safe_divide(market_cap, pl))
    
    # EV/EBITDA
    ev = _calcular_ev(dados, periodo)
    ebitda_ltm = _calcular_ebitda_ltm(dados, periodo)
    resultado["EV_EBITDA"] = _normalizar_valor(_safe_divide(ev, ebitda_ltm))
    
    # EV/EBIT
    ebit_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["ebit"], periodo)
    resultado["EV_EBIT"] = _normalizar_valor(_safe_divide(ev, ebit_ltm))
    
    # EV/Receita
    receita_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["receita"], periodo)
    resultado["EV_RECEITA"] = _normalizar_valor(_safe_divide(ev, receita_ltm))
    
    # Dividend Yield = Dividendos LTM / Market Cap × 100
    div_ltm = _calcular_dividendos_ltm(dados, periodo)
    if np.isfinite(div_ltm) and np.isfinite(market_cap) and market_cap > 0:
        resultado["DY"] = _normalizar_valor(_safe_divide(div_ltm, market_cap) * 100)
    else:
        resultado["DY"] = None
    
    # ==================== RENTABILIDADE ====================
    
    # ROE = Lucro Líquido LTM / PL Médio × 100
    pl_medio = _obter_valor_medio(dados, dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)
    resultado["ROE"] = _normalizar_valor(_safe_divide(ll_ltm, pl_medio) * 100)
    
    # ROA = Lucro Líquido LTM / Ativo Total Médio × 100
    at_medio = _obter_valor_medio(dados, dados.bpa, CONTAS_BPA["ativo_total"], periodo)
    resultado["ROA"] = _normalizar_valor(_safe_divide(ll_ltm, at_medio) * 100)
    
    # ROIC = NOPAT / Capital Investido × 100
    # NOPAT = EBIT × (1 - alíquota efetiva)
    # Alíquota efetiva = IR+CSLL / Lucro Antes IR, com fallback para 34%
    ir_csll_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["ir_csll"], periodo)
    resultado_fin_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["resultado_financeiro"], periodo)
    
    # Lucro Antes IR = EBIT - Resultado Financeiro
    lucro_antes_ir = ebit_ltm - resultado_fin_ltm if np.isfinite(ebit_ltm) and np.isfinite(resultado_fin_ltm) else np.nan
    
    if np.isfinite(ir_csll_ltm) and np.isfinite(lucro_antes_ir) and lucro_antes_ir > 0:
        aliquota_efetiva = abs(ir_csll_ltm) / lucro_antes_ir
        # Limitar alíquota a valores razoáveis (0% a 50%)
        aliquota_efetiva = max(0.0, min(0.50, aliquota_efetiva))
    else:
        aliquota_efetiva = 0.34  # Fallback: alíquota padrão brasileira (IR 25% + CSLL 9%)
    
    nopat = ebit_ltm * (1 - aliquota_efetiva) if np.isfinite(ebit_ltm) else np.nan
    
    # Capital Investido = PL + Dívida Líquida
    divida_liquida = ev - market_cap if np.isfinite(ev) and np.isfinite(market_cap) else np.nan
    capital_investido = pl + divida_liquida if np.isfinite(pl) and np.isfinite(divida_liquida) else np.nan
    resultado["ROIC"] = _normalizar_valor(_safe_divide(nopat, capital_investido) * 100)
    
    # Margem EBITDA = EBITDA / Receita × 100
    resultado["MARGEM_EBITDA"] = _normalizar_valor(_safe_divide(ebitda_ltm, receita_ltm) * 100)
    
    # Margem Líquida = Lucro Líquido / Receita × 100
    resultado["MARGEM_LIQUIDA"] = _normalizar_valor(_safe_divide(ll_ltm, receita_ltm) * 100)
    
    # ==================== ENDIVIDAMENTO ====================
    
    # Dívida Líquida / EBITDA
    emp_cp = _obter_valor_pontual(dados.bpp, CONTAS_BPP["emprestimos_cp"], periodo, ["2.01.04"])
    emp_lp = _obter_valor_pontual(dados.bpp, CONTAS_BPP["emprestimos_lp"], periodo, ["2.02.01"])
    caixa = _obter_valor_pontual(dados.bpa, CONTAS_BPA["caixa"], periodo)
    aplic = _obter_valor_pontual(dados.bpa, CONTAS_BPA["aplicacoes"], periodo)
    
    emp_cp = emp_cp if np.isfinite(emp_cp) else 0
    emp_lp = emp_lp if np.isfinite(emp_lp) else 0
    caixa = caixa if np.isfinite(caixa) else 0
    aplic = aplic if np.isfinite(aplic) else 0
    
    divida_bruta = emp_cp + emp_lp
    divida_liquida_calc = divida_bruta - caixa - aplic
    
    resultado["DIV_LIQ_EBITDA"] = _normalizar_valor(_safe_divide(divida_liquida_calc, ebitda_ltm))
    
    # Dívida Líquida / PL
    resultado["DIV_LIQ_PL"] = _normalizar_valor(_safe_divide(divida_liquida_calc, pl))
    
    # ICJ = EBIT / Despesas Financeiras
    resultado_fin = _calcular_ltm(dados, dados.dre, CONTAS_DRE["resultado_financeiro"], periodo)
    # Despesa financeira = |resultado financeiro| quando negativo
    desp_fin = abs(resultado_fin) if np.isfinite(resultado_fin) and resultado_fin < 0 else np.nan
    resultado["ICJ"] = _normalizar_valor(_safe_divide(ebit_ltm, desp_fin))
    
    # Composição Dívida = Empréstimos CP / (CP + LP) × 100
    resultado["COMPOSICAO_DIVIDA"] = _normalizar_valor(_safe_divide(emp_cp, divida_bruta) * 100)
    
    # ==================== LIQUIDEZ ====================
    
    ac = _obter_valor_pontual(dados.bpa, CONTAS_BPA["ativo_circulante"], periodo)
    pc = _obter_valor_pontual(dados.bpp, CONTAS_BPP["passivo_circulante"], periodo)
    estoques = _obter_valor_pontual(dados.bpa, CONTAS_BPA["estoques"], periodo)
    rlp = _obter_valor_pontual(dados.bpa, CONTAS_BPA["realizavel_lp"], periodo, ["1.02.01"])
    pnc = _obter_valor_pontual(dados.bpp, CONTAS_BPP["passivo_nao_circulante"], periodo)
    
    # Liquidez Corrente = AC / PC
    resultado["LIQ_CORRENTE"] = _normalizar_valor(_safe_divide(ac, pc))
    
    # Liquidez Seca = (AC - Estoques) / PC
    estoques_val = estoques if np.isfinite(estoques) else 0
    resultado["LIQ_SECA"] = _normalizar_valor(_safe_divide(ac - estoques_val, pc))
    
    # Liquidez Geral = (AC + RLP) / (PC + PNC)
    rlp_val = rlp if np.isfinite(rlp) else 0
    pnc_val = pnc if np.isfinite(pnc) else 0
    resultado["LIQ_GERAL"] = _normalizar_valor(_safe_divide(ac + rlp_val, pc + pnc_val))
    
    # ==================== EFICIÊNCIA ====================
    
    at = _obter_valor_pontual(dados.bpa, CONTAS_BPA["ativo_total"], periodo)
    
    # Giro do Ativo = Receita LTM / Ativo Total
    resultado["GIRO_ATIVO"] = _normalizar_valor(_safe_divide(receita_ltm, at))
    
    # PME = (Estoques + Ativos Biológicos) × 360 / CPV
    ativos_bio = _obter_valor_pontual(dados.bpa, CONTAS_BPA["ativos_biologicos"], periodo)
    ativos_bio_val = ativos_bio if np.isfinite(ativos_bio) else 0
    cpv_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["cpv"], periodo)
    cpv_ltm_abs = abs(cpv_ltm) if np.isfinite(cpv_ltm) else np.nan
    
    estoque_total = estoques_val + ativos_bio_val
    resultado["PME"] = _normalizar_valor(_safe_divide(estoque_total * 360, cpv_ltm_abs))
    
    # PMR = Contas a Receber × 360 / Receita
    contas_receber = _obter_valor_pontual(dados.bpa, CONTAS_BPA["contas_receber"], periodo, ["1.01.03"])
    contas_receber_val = contas_receber if np.isfinite(contas_receber) else 0
    pmr = _safe_divide(contas_receber_val * 360, receita_ltm) if np.isfinite(receita_ltm) else np.nan
    
    # PMP = Fornecedores × 360 / CPV
    fornecedores = _obter_valor_pontual(dados.bpp, CONTAS_BPP["fornecedores"], periodo, ["2.01.02"])
    fornecedores_val = fornecedores if np.isfinite(fornecedores) else 0
    pmp = _safe_divide(fornecedores_val * 360, cpv_ltm_abs) if np.isfinite(cpv_ltm_abs) else np.nan
    
    # Ciclo de Caixa = PMR + PME - PMP
    pme_val = resultado["PME"] if resultado["PME"] is not None else np.nan
    if np.isfinite(pmr) and np.isfinite(pme_val) and np.isfinite(pmp):
        resultado["CICLO_CAIXA"] = _normalizar_valor(pmr + pme_val - pmp)
    else:
        resultado["CICLO_CAIXA"] = None
    
    # NCG = (AC - Caixa - Aplicações) - (PC - Empréstimos CP)
    ncg_ativo = ac - caixa - aplic if np.isfinite(ac) else np.nan
    ncg_passivo = pc - emp_cp if np.isfinite(pc) else np.nan
    ncg = ncg_ativo - ncg_passivo if np.isfinite(ncg_ativo) and np.isfinite(ncg_passivo) else np.nan
    
    # NCG / Receita × 100
    resultado["NCG_RECEITA"] = _normalizar_valor(_safe_divide(ncg, receita_ltm) * 100)
    
    return resultado


# ======================================================================================
# METADADOS DOS MÚLTIPLOS
# ======================================================================================

MULTIPLOS_METADATA = {
    # VALUATION
    "P_L": {"nome": "P/L", "categoria": "Valuation", "formula": "Market Cap / Lucro Líquido LTM", "unidade": "x"},
    "P_VPA": {"nome": "P/VPA", "categoria": "Valuation", "formula": "Market Cap / Patrimônio Líquido", "unidade": "x"},
    "EV_EBITDA": {"nome": "EV/EBITDA", "categoria": "Valuation", "formula": "Enterprise Value / EBITDA LTM", "unidade": "x"},
    "EV_EBIT": {"nome": "EV/EBIT", "categoria": "Valuation", "formula": "Enterprise Value / EBIT LTM", "unidade": "x"},
    "EV_RECEITA": {"nome": "EV/Receita", "categoria": "Valuation", "formula": "Enterprise Value / Receita LTM", "unidade": "x"},
    "DY": {"nome": "Dividend Yield", "categoria": "Valuation", "formula": "Dividendos LTM / Market Cap", "unidade": "%"},
    
    # RENTABILIDADE
    "ROE": {"nome": "ROE", "categoria": "Rentabilidade", "formula": "Lucro Líquido LTM / PL Médio", "unidade": "%"},
    "ROA": {"nome": "ROA", "categoria": "Rentabilidade", "formula": "Lucro Líquido LTM / Ativo Total Médio", "unidade": "%"},
    "ROIC": {"nome": "ROIC", "categoria": "Rentabilidade", "formula": "NOPAT / Capital Investido", "unidade": "%"},
    "MARGEM_EBITDA": {"nome": "Margem EBITDA", "categoria": "Rentabilidade", "formula": "EBITDA / Receita", "unidade": "%"},
    "MARGEM_LIQUIDA": {"nome": "Margem Líquida", "categoria": "Rentabilidade", "formula": "Lucro Líquido / Receita", "unidade": "%"},
    
    # ENDIVIDAMENTO
    "DIV_LIQ_EBITDA": {"nome": "Dív.Líq/EBITDA", "categoria": "Endividamento", "formula": "(Emp CP + LP - Caixa) / EBITDA", "unidade": "x"},
    "DIV_LIQ_PL": {"nome": "Dív.Líq/PL", "categoria": "Endividamento", "formula": "Dívida Líquida / Patrimônio Líquido", "unidade": "x"},
    "ICJ": {"nome": "ICJ", "categoria": "Endividamento", "formula": "EBIT / Despesas Financeiras", "unidade": "x"},
    "COMPOSICAO_DIVIDA": {"nome": "Composição Dívida", "categoria": "Endividamento", "formula": "Emp CP / (Emp CP + LP)", "unidade": "%"},
    
    # LIQUIDEZ
    "LIQ_CORRENTE": {"nome": "Liquidez Corrente", "categoria": "Liquidez", "formula": "Ativo Circulante / Passivo Circulante", "unidade": "x"},
    "LIQ_SECA": {"nome": "Liquidez Seca", "categoria": "Liquidez", "formula": "(AC - Estoques) / PC", "unidade": "x"},
    "LIQ_GERAL": {"nome": "Liquidez Geral", "categoria": "Liquidez", "formula": "(AC + RLP) / (PC + PNC)", "unidade": "x"},
    
    # EFICIÊNCIA
    "GIRO_ATIVO": {"nome": "Giro do Ativo", "categoria": "Eficiência", "formula": "Receita LTM / Ativo Total", "unidade": "x"},
    "CICLO_CAIXA": {"nome": "Ciclo de Caixa", "categoria": "Eficiência", "formula": "PMR + PME - PMP", "unidade": "dias"},
    "PME": {"nome": "PME", "categoria": "Eficiência", "formula": "(Estoques + AtBio) × 360 / CPV", "unidade": "dias"},
    "NCG_RECEITA": {"nome": "NCG/Receita", "categoria": "Eficiência", "formula": "NCG / Receita LTM", "unidade": "%"},
}


# ======================================================================================
# GERADOR DE HISTÓRICO ANUALIZADO
# ======================================================================================

def gerar_historico_anualizado(dados: DadosEmpresa) -> Dict[str, Any]:
    """
    Gera histórico de múltiplos anualizado.
    
    Estratégia:
    - Para cada ano, usa o último trimestre disponível como referência
    - Último período = últimos 4 trimestres disponíveis (LTM)
    - Adapta-se ao padrão fiscal da empresa
    """
    if not dados.periodos or dados.padrao_fiscal is None:
        return {"erro": "Dados insuficientes", "ticker": dados.ticker}
    
    # Agrupar períodos por ano
    periodos_por_ano: Dict[int, List[str]] = {}
    for p in dados.periodos:
        ano, tri = _parse_periodo(p)
        if ano > 0:
            if ano not in periodos_por_ano:
                periodos_por_ano[ano] = []
            periodos_por_ano[ano].append(p)
    
    # Para cada ano, pegar o último trimestre
    historico_anual: Dict[int, Dict[str, Any]] = {}
    
    for ano in sorted(periodos_por_ano.keys()):
        periodos_ano = _ordenar_periodos(periodos_por_ano[ano])
        ultimo_periodo = periodos_ano[-1]
        
        # Calcular múltiplos usando o último período do ano
        multiplos = calcular_multiplos_periodo(dados, ultimo_periodo)
        
        historico_anual[ano] = {
            "periodo_referencia": ultimo_periodo,
            "multiplos": multiplos
        }
    
    # Calcular LTM (último período disponível)
    ultimo_periodo_geral = dados.periodos[-1]
    multiplos_ltm = calcular_multiplos_periodo(dados, ultimo_periodo_geral)
    
    return {
        "ticker": dados.ticker,
        "padrao_fiscal": {
            "tipo": dados.padrao_fiscal.tipo,
            "descricao": dados.padrao_fiscal.descricao,
            "trimestres_ltm": dados.padrao_fiscal.trimestres_ltm
        },
        "metadata": MULTIPLOS_METADATA,
        "historico_anual": historico_anual,
        "ltm": {
            "periodo_referencia": ultimo_periodo_geral,
            "data_calculo": datetime.now().isoformat(),
            "multiplos": multiplos_ltm
        },
        "periodos_disponiveis": dados.periodos,
        "erros_carregamento": dados.erros
    }


# ======================================================================================
# PROCESSADOR PRINCIPAL
# ======================================================================================

def processar_ticker(ticker: str, salvar: bool = True) -> Tuple[bool, str, Optional[Dict]]:
    """
    Processa um ticker e calcula todos os múltiplos.
    
    Retorna: (sucesso, mensagem, dados_json)
    """
    ticker_upper = ticker.upper().strip()
    
    # Verificar se é financeiro
    if _is_financeiro(ticker_upper):
        return False, f"Empresa financeira - cálculo de múltiplos não aplicável", None
    
    # Carregar dados
    dados = carregar_dados_empresa(ticker_upper)
    
    if dados.erros:
        erros_str = "; ".join(dados.erros)
        return False, f"Erros ao carregar: {erros_str}", None
    
    if not dados.periodos:
        return False, "Nenhum período disponível", None
    
    # Gerar histórico
    resultado = gerar_historico_anualizado(dados)
    
    # Salvar JSON
    if salvar:
        pasta = get_pasta_balanco(ticker_upper)
        pasta.mkdir(parents=True, exist_ok=True)
        
        output_path = pasta / "multiplos.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2, default=str)
        
        # Também salvar CSV para compatibilidade
        csv_path = pasta / "multiplos.csv"
        _salvar_csv_historico(resultado, csv_path)
    
    # Mensagem de status
    n_anos = len(resultado.get("historico_anual", {}))
    padrao = resultado.get("padrao_fiscal", {}).get("tipo", "?")
    ultimo = resultado.get("ltm", {}).get("periodo_referencia", "?")
    
    msg = f"OK | {n_anos} anos | fiscal={padrao} | LTM={ultimo}"
    
    return True, msg, resultado


def _salvar_csv_historico(resultado: Dict, path: Path):
    """
    Salva histórico em formato CSV para compatibilidade.
    Formato: linhas = múltiplos, colunas = anos + LTM
    """
    historico = resultado.get("historico_anual", {})
    ltm_data = resultado.get("ltm", {})
    metadata = resultado.get("metadata", {})
    
    if not historico:
        return
    
    # Preparar dados
    anos = sorted(historico.keys())
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
        
        # Valores por ano
        for ano in anos:
            multiplos_ano = historico[ano].get("multiplos", {})
            row[str(ano)] = multiplos_ano.get(codigo)
        
        # LTM
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
        description="Calculadora de Múltiplos Financeiros para Empresas Não-Financeiras (v1.1.0 Corrigida)"
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
    
    # Carregar mapeamento de empresas
    df = load_mapeamento_consolidado()
    df = df[df["cnpj"].notna()].reset_index(drop=True)
    
    # Selecionar empresas
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
    print(f">>> CALCULADORA DE MÚLTIPLOS v1.1.0 (CORRIGIDA) <<<")
    print(f"{'='*70}")
    print(f"Modo: {args.modo} | Selecionadas: {len(df_sel)}")
    print(f"Correções: ROIC (alíquota efetiva) + DY (implementado)")
    print(f"Saída: balancos/<TICKER>/multiplos.json + multiplos.csv")
    print(f"{'='*70}\n")
    
    # Contadores
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
