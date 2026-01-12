# src/calcular_multiplos.py
"""
Calculadora de Múltiplos Financeiros para Empresas Não-Financeiras
==================================================================
VERSÃO CORRIGIDA - Janeiro 2025

Calcula 22 múltiplos organizados em 5 categorias (empresas não-financeiras):
- Valuation (7): P/L, P/VPA, EV/EBITDA, EV/EBIT, EV/Receita, DY, Payout
- Rentabilidade (5): ROE, ROA, ROIC, Margem EBITDA, Margem Líquida
- Endividamento (4): Dív.Líq/EBITDA, Dív.Líq/PL, ICJ, Composição Dívida
- Liquidez (3): Corrente, Seca, Geral
- Eficiência (4): Giro Ativo, Ciclo Caixa, PME, NCG/Receita

Calcula 8 múltiplos essenciais para bancos:
- Valuation (4): P/L, P/VPA, DY, Payout
- Rentabilidade (3): ROE, ROA, Margem Líquida
- Estrutura (1): PL/Ativos

CORREÇÕES APLICADAS:
1. Busca robusta de preços (período atual ou mais recente disponível)
2. Busca robusta de ações (período atual ou mais recente disponível)
3. Cálculo de EBITDA revisado
4. Cálculo de ROIC com taxa de IR correta
5. Dividend Yield calculado corretamente
6. Múltiplos bancários simplificados para máxima confiabilidade

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

# Holdings de seguros (BBSE3, CXSE3)
TICKERS_HOLDINGS_SEGUROS: Set[str] = {
    "BBSE3",  # BB Seguridade
    "CXSE3",  # Caixa Seguridade
}

# Seguradoras operacionais (IRBR3, PSSA3)
TICKERS_SEGURADORAS: Set[str] = {
    "IRBR3",  # IRB Brasil Resseguros
    "PSSA3",  # Porto Seguro
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
}

CONTAS_BPA_BANCOS = {
    "ativo_total": "1",
    "caixa": "1.01",
    "ativos_financeiros": "1.02",         # Agregado - sempre existe
}

CONTAS_BPP_BANCOS = {
    "passivo_total": "2",
    "passivos_financeiros_vj": "2.01",
    "passivos_custo_amort": "2.02",       # Agregado - inclui depósitos
}

# ======================================================================================
# MAPEAMENTO DE CONTAS - HOLDINGS DE SEGUROS
# ======================================================================================

CONTAS_DRE_HOLDINGS_SEGUROS = {
    "receita": "3.01",                    # Receita de Corretagem
    "cpv": "3.02",                        # Custo dos Serviços
    "lucro_bruto": "3.03",                # Resultado Bruto
    "despesas_vendas": "3.04.01",         # Despesas com Vendas
    "despesas_admin": "3.04.02",          # Despesas Gerais e Administrativas
    "equivalencia": "3.04.05",            # Equivalência Patrimonial (coração do lucro)
    "ebit": "3.05",                       # EBIT
    "resultado_financeiro": "3.06",       # Resultado Financeiro
    "lair": "3.08",                       # LAIR
    "ir_csll": "3.09",                    # IR e CSLL
    "lucro_liquido": "3.11",              # Lucro Líquido
}


# ======================================================================================
# MAPEAMENTO DE CONTAS - SEGURADORAS OPERACIONAIS
# ======================================================================================

CONTAS_DRE_SEGURADORAS = {
    "premios_ganhos": "3.01",             # Prêmios Ganhos
    "premios_emitidos": "3.01.01",        # Prêmios Emitidos (bruto)
    "var_provisoes": "3.01.04",           # Variação Provisões Técnicas
    "sinistros": "3.02",                  # Sinistros Retidos
    "custos_aquisicao": "3.03",           # Custos de Aquisição
    "despesas_admin": "3.04",             # Despesas Administrativas
    "despesas_tributos": "3.05",          # Despesas com Tributos
    "resultado_financeiro": "3.06",       # Resultado Financeiro (Float)
    "resultado_operacional": "3.07",      # Resultado Operacional
    "lair": "3.08",                       # LAIR
    "ir_csll": "3.09",                    # IR e CSLL
    "lucro_liquido": "3.11",              # Lucro Líquido
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

def _is_holding_seguros(ticker: str) -> bool:
    """Verifica se ticker é de holding de seguros (BBSE3 ou CXSE3)."""
    ticker_upper = ticker.upper().strip()
    return ticker_upper in {"BBSE3", "CXSE3"}

def _is_seguradora_operacional(ticker: str) -> bool:
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


def _safe_divide(numerador: float, denominador: float, default: float = np.nan, eps: float = 1e-9) -> float:
    if not np.isfinite(numerador) or not np.isfinite(denominador):
        return default
    if np.isclose(denominador, 0.0, atol=eps):
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

# ======================================================================================
# ✅ CORREÇÃO 2: FILTRO DE COLUNAS SUJAS
# ======================================================================================

def _get_colunas_numericas_validas(df: pd.DataFrame) -> List[str]:
    """
    ✅ CORREÇÃO 2: Retorna apenas colunas de período que contêm NÚMEROS válidos.

    Problema: BEEF3 tem coluna "2026T1" com valores "ON", "TOTAL" (texto)
    Solução: Testa se a coluna tem pelo menos 1 valor numérico válido

    Exemplo:
        2026T1: ["ON", "TOTAL"] → EXCLUÍDA (100% texto)
        2025T4: ["15.50", "TOTAL"] → INCLUÍDA (tem número)

    Args:
        df: DataFrame com colunas de períodos

    Returns:
        Lista ordenada de períodos com dados numéricos
    """
    if df is None:
        return []

    # Candidatas: colunas que parecem períodos (formato YYYYTX)
    candidatas = [c for c in df.columns if _parse_periodo(c)[0] > 0]

    validas = []
    for c in candidatas:
        # Tenta converter para numérico
        s = pd.to_numeric(df[c], errors='coerce')
        # Se tiver PELO MENOS 1 número válido, a coluna é válida
        if s.notna().any():
            validas.append(c)

    return _ordenar_periodos(validas)


# ======================================================================================
# ✅ CORREÇÃO 1: BACKFILL DE AÇÕES (CAML3 2017)
# ======================================================================================

def _encontrar_periodo_imputacao(df: pd.DataFrame, periodo_req: str) -> Optional[str]:
    """
    ✅ CORREÇÃO 1: Encontra período substituto para preencher lacunas.

    Problema: CAML3 IPO 2018, mas precisa calcular múltiplos de 2017
    Solução: Backfill - usa primeiro dado disponível (ações de 2018 para 2017)

    Lógica:
        1. Se período existe → usa exato
        2. Se não, tenta anterior mais próximo (Forward Fill)
        3. Se não houver anterior, tenta posterior mais próximo (Backfill) ← NOVO!

    Args:
        df: DataFrame com colunas de períodos
        periodo_req: Período solicitado (ex: "2017T4")

    Returns:
        Período a usar ou None se nenhum dado disponível

    Exemplo CAML3:
        Solicitado: 2017T4
        Disponível: [2018T4, 2019T1, ...]
        Retorna: 2018T4 (Backfill)
    """
    validas = _get_colunas_numericas_validas(df)
    if not validas:
        return None

    # 1. Exato
    if periodo_req in validas:
        return periodo_req

    def key_fn(p):
        a, t = _parse_periodo(p)
        tn = {'T1': 1, 'T2': 2, 'T3': 3, 'T4': 4}.get(t, 0)
        return (a, tn)

    req_key = key_fn(periodo_req)

    # 2. Forward Fill (Anteriores)
    anteriores = [p for p in validas if key_fn(p) <= req_key]
    if anteriores:
        return max(anteriores, key=key_fn)

    # 3. ✅ BACKFILL (Posteriores) - NOVO!
    posteriores = [p for p in validas if key_fn(p) > req_key]
    if posteriores:
        return min(posteriores, key=key_fn)

    return None

def _obter_preco(dados: DadosEmpresa, periodo: str, ticker_preco: Optional[str] = None) -> float:
    """
    Obtém preço da ação no período específico.

    Suporta 2 formatos de precos_trimestrais.csv:

    (A) Formato antigo (1 linha):
        Preço_Fechamento,2015T1,2015T2,...
        Preço de Fechamento Ajustado,2.11,2.12,...

    (B) Formato multi-classes (várias linhas, coluna Ticker):
        Ticker,Preço_Fechamento,2015T1,2015T2,...
        BBDC3,Preço de Fechamento Ajustado,....
        BBDC4,Preço de Fechamento Ajustado,....

    Args:
        dados: Dados da empresa
        periodo: ex. "2024T4"
        ticker_preco: ticker específico (ex. "BBDC4"). Se None, usa dados.ticker.
    """
    if dados.precos is None or dados.precos.empty:
        return np.nan

    df = dados.precos

    # Detectar coluna de ticker (formato multi-classes)
    col_ticker = None
    for c in ["Ticker", "ticker", "TICKER"]:
        if c in df.columns:
            col_ticker = c
            break

    if periodo not in df.columns:
        return np.nan

    # Se multi-classes, filtrar pelo ticker desejado
    if col_ticker:
        alvo = (ticker_preco or dados.ticker or "")
        alvo = str(alvo).upper().strip()
        sub = df[df[col_ticker].astype(str).str.upper().str.strip() == alvo]
        if sub.empty:
            # fallback: se não achou, tenta usar a 1ª linha numérica disponível
            sub = df
        df_use = sub
    else:
        df_use = df

    # ==================== SELEÇÃO DO PREÇO (CORREÇÃO) ====================
    # Objetivo: alinhar múltiplos com plataformas como StatusInvest/Investidor10.
    # Se existir mais de uma linha de preço (ex.: "Preço de Fechamento" e "Ajustado"),
    # preferir SEMPRE o "Preço de Fechamento" (não-ajustado).
    df_sel = df_use
    col_tipo = None
    for c in ["Preço_Fechamento", "Preco_Fechamento", "PRECO_FECHAMENTO", "tipo_preco", "Tipo", "tipo"]:
        if c in df_sel.columns:
            col_tipo = c
            break

    if col_tipo:
        tipo = df_sel[col_tipo].astype(str).str.strip().str.lower()
        mask_fech = tipo.str.contains(r"pre[çc]o\s*de\s*fechamento", regex=True)
        mask_aj = tipo.str.contains(r"ajust", regex=True)

        # não-ajustado primeiro
        if (mask_fech & ~mask_aj).any():
            df_sel = df_sel.loc[mask_fech & ~mask_aj].copy()
        elif mask_fech.any():
            df_sel = df_sel.loc[mask_fech].copy()
        elif mask_aj.any():
            df_sel = df_sel.loc[mask_aj].copy()

    # Buscar valor numérico na coluna do período
    s = pd.to_numeric(df_sel[periodo], errors="coerce")
    if s.notna().any():
        # pega o primeiro valor numérico válido
        return float(s.dropna().iloc[0])

    return np.nan



def _obter_preco_atual(dados: DadosEmpresa, ticker_preco: Optional[str] = None) -> Tuple[float, str]:
    """
    Obtém o preço mais recente disponível (último trimestre com dado numérico).

    Suporta formato antigo e multi-classes (com coluna Ticker).
    """
    if dados.precos is None or dados.precos.empty:
        return np.nan, ""

    df = dados.precos

    # Detectar coluna de ticker
    col_ticker = None
    for c in ["Ticker", "ticker", "TICKER"]:
        if c in df.columns:
            col_ticker = c
            break

    if col_ticker:
        alvo = (ticker_preco or dados.ticker or "")
        alvo = str(alvo).upper().strip()
        sub = df[df[col_ticker].astype(str).str.upper().str.strip() == alvo]
        if sub.empty:
            sub = df
        df_use = sub
    else:
        df_use = df

    colunas_precos = _get_colunas_numericas_validas(df_use)
    if not colunas_precos:
        return np.nan, ""

    for p in reversed(colunas_precos):
        preco = _obter_preco(dados, p, ticker_preco=ticker_preco)
        if np.isfinite(preco) and preco > 0:
            return preco, p

    return np.nan, ""



def _detectar_coluna_especie(df: pd.DataFrame) -> Optional[str]:
    if df is None:
        return None
    # candidatos comuns no seu projeto
    candidatos = {"espécie_acao", "especie_acao", "espécie_ação", "especie", "espécie", "espécie_acao", "Espécie_Acao"}
    mapa = {c.lower().strip(): c for c in df.columns}
    for key, original in mapa.items():
        if key in candidatos:
            return original
    return None


def _obter_acoes_especie(dados: DadosEmpresa, especie: str, periodo: str) -> float:
    """
    Obtém ações de uma espécie específica (ex.: 'ON', 'PN') no período.

    Usa _encontrar_periodo_imputacao para selecionar a melhor coluna de período,
    evitando cair em períodos antigos quando a coluna não existe (ex.: 2025T3).
    """
    if dados.acoes is None or dados.acoes.empty:
        return np.nan

    df = dados.acoes
    col_especie = _detectar_coluna_especie(df)
    if not col_especie:
        return np.nan

    # Escolher coluna de período (imputação)
    periodo_busca = _encontrar_periodo_imputacao(df, periodo)
    if not periodo_busca:
        col_periodos = _get_colunas_numericas_validas(df)
        if not col_periodos:
            return np.nan
        periodo_busca = col_periodos[-1]

    serie = df[col_especie].astype(str).str.upper().str.strip()
    mask = serie.eq(str(especie).upper().strip())
    if not mask.any():
        return np.nan

    val = pd.to_numeric(df.loc[mask, periodo_busca], errors="coerce").iloc[0]
    return float(val) if pd.notna(val) else np.nan


def _obter_acoes_total_ex11(dados: DadosEmpresa, periodo: str) -> float:
    """
    Retorna o total de ações considerando APENAS classes 3 e 4 (ON+PN), ignorando UNIT (11),
    sempre que possível.

    Prioridade:
      1) ON + PN (se ambos existirem e forem válidos)
      2) ON (se só existir ON)
      3) PN (se só existir PN)
      4) TOTAL (fallback)
    """
    if dados.acoes is None or dados.acoes.empty:
        return np.nan

    on = _obter_acoes_especie(dados, "ON", periodo)
    pn = _obter_acoes_especie(dados, "PN", periodo)

    if np.isfinite(on) and on > 0 and np.isfinite(pn) and pn > 0:
        return on + pn
    if np.isfinite(on) and on > 0:
        return on
    if np.isfinite(pn) and pn > 0:
        return pn

    # fallback TOTAL
    df = dados.acoes
    col_especie = _detectar_coluna_especie(df)
    periodo_busca = _encontrar_periodo_imputacao(df, periodo)
    if not periodo_busca:
        col_periodos = _get_colunas_numericas_validas(df)
        if not col_periodos:
            return np.nan
        periodo_busca = col_periodos[-1]

    if col_especie:
        serie = df[col_especie].astype(str).str.upper().str.strip()
        mask = serie.eq("TOTAL")
        if mask.any():
            val = pd.to_numeric(df.loc[mask, periodo_busca], errors="coerce").iloc[0]
            return float(val) if pd.notna(val) else np.nan

    # fallback: primeira célula numérica disponível
    s = pd.to_numeric(df[periodo_busca], errors="coerce")
    if s.notna().any():
        return float(s.dropna().iloc[0])

    return np.nan


def _periodos_numericos(df: pd.DataFrame) -> List[str]:
    if df is None:
        return []
    periodos = [c for c in df.columns if _parse_periodo(c)[0] > 0]
    validos = []
    for c in periodos:
        s = pd.to_numeric(df[c], errors="coerce")
        if s.notna().any():
            validos.append(c)
    return _ordenar_periodos(validos)

def _melhor_periodo(periodos_validos: List[str], periodo_req: str) -> Optional[str]:
    if not periodos_validos:
        return None
    if periodo_req in periodos_validos:
        return periodo_req
    ano_req, tri_req = _parse_periodo(periodo_req)
    if ano_req == 0:
        return periodos_validos[-1]

    def key(p: str):
        a, t = _parse_periodo(p)
        tn = {"T1": 1, "T2": 2, "T3": 3, "T4": 4}.get(t, 0)
        return (a, tn)

    reqk = key(periodo_req)
    leq = [p for p in periodos_validos if key(p) <= reqk]
    return max(leq, key=key) if leq else periodos_validos[-1]




def _obter_acoes(dados: DadosEmpresa, periodo: str) -> float:
    """
    Obtém número de ações no período específico.

    ✅ Regra geral do projeto:
    - Para múltiplos, priorizar ON+PN (ignorar UNIT/11 quando possível).
    - Se o período não existir na tabela de ações, usar imputação (período mais próximo),
      evitando cair no período mais antigo.

    Retorna ações em UNIDADES.
    """
    if dados.acoes is None or dados.acoes.empty:
        return np.nan

    return _obter_acoes_total_ex11(dados, periodo)



def _obter_acoes_atual(dados: DadosEmpresa) -> Tuple[float, str]:
    """
    Obtém o número de ações mais recente disponível (baseado no acoes_historico.csv).

    ✅ Não depende de dados.periodos (DRE), usa as colunas do próprio arquivo de ações.
    ✅ Retorna total ON+PN sempre que possível (ignora UNIT/11).
    """
    if dados.acoes is None or dados.acoes.empty:
        return np.nan, ""

    col_periodos = _get_colunas_numericas_validas(dados.acoes)
    if not col_periodos:
        return np.nan, ""

    periodo_mais_recente = col_periodos[-1]
    acoes = _obter_acoes_total_ex11(dados, periodo_mais_recente)

    if np.isfinite(acoes) and acoes > 0:
        return acoes, periodo_mais_recente

    return np.nan, ""



def _calcular_market_cap(dados: DadosEmpresa, periodo: str) -> float:
    """
    Calcula Market Cap (R$ mil) no período.

    ✅ Regra correta (empresa com classe 3 e 4):
        VM = (Preço3 × AçõesON) + (Preço4 × AçõesPN)

    Ações: como acoes_historico costuma estar anual (T4), usa imputação para
    pegar o melhor período disponível (ex.: para 2025T3 usa 2024T4).
    """
    ticker = (dados.ticker or "").upper().strip()
    if len(ticker) < 4:
        return np.nan
    raiz = ticker[:4]
    t3 = f"{raiz}3"
    t4 = f"{raiz}4"

    p3 = _obter_preco(dados, periodo, ticker_preco=t3)
    p4 = _obter_preco(dados, periodo, ticker_preco=t4)

    acoes_on = _obter_acoes_especie(dados, "ON", periodo)
    acoes_pn = _obter_acoes_especie(dados, "PN", periodo)

    parts = []
    if np.isfinite(p3) and p3 > 0 and np.isfinite(acoes_on) and acoes_on > 0:
        parts.append(p3 * acoes_on)
    if np.isfinite(p4) and p4 > 0 and np.isfinite(acoes_pn) and acoes_pn > 0:
        parts.append(p4 * acoes_pn)

    if parts:
        return sum(parts) / 1000.0

    preco = _obter_preco(dados, periodo)
    acoes = _obter_acoes(dados, periodo)
    if np.isfinite(preco) and preco > 0 and np.isfinite(acoes) and acoes > 0:
        return (preco * acoes) / 1000.0

    return np.nan



def _calcular_market_cap_atual(dados: DadosEmpresa) -> float:
    """
    Calcula Valor de Mercado (Market Cap) atual em R$ mil.

    ✅ Regra correta (empresa com classe 3 e 4):
        VM = (Preço3 × AçõesON) + (Preço4 × AçõesPN)
    - Ignora UNIT/11 em múltiplos.
    - Se não existirem as duas classes, usa a(s) disponível(is).
    - Se não for possível obter ON/PN, faz fallback para TOTAL × preço base.
    """
    ticker = (dados.ticker or "").upper().strip()
    if len(ticker) < 4:
        return np.nan
    raiz = ticker[:4]

    # Tickers de classe
    t3 = f"{raiz}3"
    t4 = f"{raiz}4"

    # Preços atuais por classe (se existirem no precos_trimestrais multi-classe)
    p3, _ = _obter_preco_atual(dados, ticker_preco=t3)
    p4, _ = _obter_preco_atual(dados, ticker_preco=t4)

    # Ações mais recentes (geralmente anual/T4)
    acoes_on, per_on = np.nan, ""
    acoes_pn, per_pn = np.nan, ""
    if dados.acoes is not None and not dados.acoes.empty:
        col_periodos = _get_colunas_numericas_validas(dados.acoes)
        if col_periodos:
            per_mais_recente = col_periodos[-1]
            acoes_on = _obter_acoes_especie(dados, "ON", per_mais_recente)
            acoes_pn = _obter_acoes_especie(dados, "PN", per_mais_recente)

    parts = []
    if np.isfinite(p3) and p3 > 0 and np.isfinite(acoes_on) and acoes_on > 0:
        parts.append(p3 * acoes_on)
    if np.isfinite(p4) and p4 > 0 and np.isfinite(acoes_pn) and acoes_pn > 0:
        parts.append(p4 * acoes_pn)

    if parts:
        return sum(parts) / 1000.0

    # fallback: preço base × total ON+PN (ex11)
    preco_base, _ = _obter_preco_atual(dados)
    acoes_base, _ = _obter_acoes_atual(dados)

    if np.isfinite(preco_base) and preco_base > 0 and np.isfinite(acoes_base) and acoes_base > 0:
        return (preco_base * acoes_base) / 1000.0

    return np.nan



def _calcular_ev(dados: DadosEmpresa, periodo: str, market_cap: Optional[float] = None) -> float:
    """
    Calcula Enterprise Value = Market Cap + Dívida Líquida
    
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

def _calcular_vpa(dados: DadosEmpresa, periodo: str) -> float:
    """
    Calcula Valor Patrimonial por Ação (VPA) de um período.
    
    VPA = Patrimônio Líquido / Número de Ações
    
    Args:
        dados: Dados da empresa
        periodo: Período desejado (ex: "2024T4")
    
    Returns:
        VPA em R$/ação ou np.nan se dados insuficientes
    
    Unidades:
        - PL em R$ MIL (balanços CVM)
        - Ações em UNIDADES
        - VPA = (PL × 1000) / Ações → R$/ação
    
    Exemplo:
        PL = 50.000.000 R$ mil = R$ 50 bilhões
        Ações = 10.000.000.000 unidades
        VPA = 50.000.000.000 / 10.000.000.000 = R$ 5,00/ação
    """
    pl = _obter_valor_pontual(dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)
    acoes = _obter_acoes(dados, periodo)
    
    if not np.isfinite(pl) or not np.isfinite(acoes):
        return np.nan
    
    if acoes <= 0:
        return np.nan
    
    # Converter PL de R$ mil para R$ (× 1000), depois dividir por ações
    vpa = (pl * 1000.0) / acoes
    
    return vpa


def _calcular_vpa_banco(dados: DadosEmpresa, periodo: str, pl_code: str) -> float:
    """
    Calcula VPA para bancos (PL pode estar em 2.07 ou 2.08).
    
    Args:
        dados: Dados da empresa
        periodo: Período desejado
        pl_code: Código da conta PL ("2.07" ou "2.08")
    
    Returns:
        VPA em R$/ação ou np.nan se dados insuficientes
    """
    pl = _obter_valor_pontual(dados.bpp, pl_code, periodo)
    acoes = _obter_acoes(dados, periodo)
    
    if not np.isfinite(pl) or not np.isfinite(acoes):
        return np.nan
    
    if acoes <= 0:
        return np.nan
    
    # Converter PL de R$ mil para R$ (× 1000), depois dividir por ações
    vpa = (pl * 1000.0) / acoes
    
    return vpa



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
    """
    if dados.dfc is None:
        return np.nan
    
    codigos_da = ["6.01.DA", "6.01.01.02", "6.01.01.01", "6.01.01"]
    
    for cod in codigos_da:
        val = _extrair_valor_conta(dados.dfc, cod, periodo)
        if np.isfinite(val):
            return abs(val)
    
    return np.nan


def _calcular_ebitda_periodo(dados: DadosEmpresa, periodo: str) -> float:
    """
    Calcula EBITDA de um período: EBIT + |D&A|
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
    
    CORREÇÃO APLICADA: Remove lógica duplicada que somava trimestres extras.
    
    Exemplo: Se periodo_fim = "2025T3"
    - LTM correto = 2024T4 + 2025T1 + 2025T2 + 2025T3 (4 trimestres)
    
    Lógica:
    - Ano atual: T1 até T_fim
    - Ano anterior: T(tri_fim + 1) até T4
    - Total: SEMPRE 4 trimestres
    
    Returns:
        Dividendos totais em R$ MIL (dividendos por ação × número de ações / 1000)
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
    
    periodos_12m = []
    
    # ========== LÓGICA CORRIGIDA ==========
    
    # Passo 1: Ano atual - T1 até T_fim
    # Ex: Se tri_fim=3 (2025T3) → adiciona 2025T1, 2025T2, 2025T3
    for t in range(1, tri_num + 1):
        periodos_12m.append(f"{ano_fim}T{t}")
    
    # Passo 2: Ano anterior - T(tri_fim + 1) até T4
    # Ex: Se tri_fim=3 (2025T3) → adiciona 2024T4
    for t in range(tri_num + 1, 5):
        periodos_12m.append(f"{ano_fim - 1}T{t}")
    
    # ✅ CORREÇÃO: REMOVIDO loop duplicado que adicionava trimestres extras
    # ANTES (BUG):
    # for t in range(1, tri_num + 1):
    #     p = f"{ano_fim - 1}T{t}"
    #     if p not in periodos_12m:
    #         periodos_12m.append(p)
    # ↑ Isso adicionava 2024T1, 2024T2, 2024T3 → total = 7 trimestres (errado!)
    
    # AGORA: Total sempre = 4 trimestres ✅
    
    # ========================================
    
    # Buscar dividendos em todos esses períodos (4 trimestres)
    soma = 0.0
    
    for p in periodos_12m:
        if p in colunas_div:
            vals = pd.to_numeric(dados.dividendos[p], errors='coerce').dropna()
            if len(vals) > 0:
                div_por_acao = float(vals.iloc[0])
                if np.isfinite(div_por_acao) and div_por_acao > 0:
                    # Converter dividendos por ação em dividendos totais (R$ MIL)
                    div_total_mil = (div_por_acao * num_acoes) / 1000.0
                    soma += div_total_mil
    
    return soma if soma > 0 else np.nan

# ======================================================================================
# NOVAS FUNÇÕES PARA CÁLCULO DE P/L COM LPA
# ======================================================================================

def _obter_lpa_periodo(dados: DadosEmpresa, periodo: str) -> float:
    """
    Obtém Lucro por Ação (LPA) de um período específico.
    
    LPA está na conta 3.99 do DRE (já calculado pela CVM).
    
    Args:
        dados: Dados da empresa
        periodo: Período desejado (ex: "2025T3")
    
    Returns:
        LPA em R$/ação ou np.nan se não disponível
    """
    if dados.dre is None:
        return np.nan
    
    # Conta 3.99 = Lucro por Ação (Reais/Ação)
    lpa = _extrair_valor_conta(dados.dre, "3.99", periodo)
    
    return lpa if np.isfinite(lpa) else np.nan


def _calcular_lpa_ltm(dados: DadosEmpresa, periodo_fim: str) -> float:
    """
    Calcula Lucro por Ação LTM (anualizado) somando últimos 4 trimestres.
    
    Para empresas semestrais (AGRO3): usa 3 trimestres
    Para empresas padrão: usa 4 trimestres
    
    Args:
        dados: Dados da empresa
        periodo_fim: Período final para cálculo LTM
    
    Returns:
        LPA LTM em R$/ação ou np.nan se dados insuficientes
    
    Exemplo:
        LTM 2025T3 = LPA(2024T4) + LPA(2025T1) + LPA(2025T2) + LPA(2025T3)
    """
    if dados.dre is None or dados.padrao_fiscal is None:
        return np.nan
    
    periodos = dados.periodos
    if periodo_fim not in periodos:
        return np.nan
    
    idx_fim = periodos.index(periodo_fim)
    padrao = dados.padrao_fiscal
    
    # Determinar número de trimestres para LTM
    if padrao.tipo == 'SEMESTRAL':
        n_trimestres = 3
    else:
        n_trimestres = 4
    
    # Obter períodos LTM
    start_idx = max(0, idx_fim - n_trimestres + 1)
    periodos_ltm = periodos[start_idx:idx_fim + 1]
    
    # Somar LPA dos períodos
    soma_lpa = 0.0
    count_valid = 0
    
    for p in periodos_ltm:
        lpa = _obter_lpa_periodo(dados, p)
        if np.isfinite(lpa):
            soma_lpa += lpa
            count_valid += 1
    
    # Validar mínimo de períodos
    min_periodos = 3 if padrao.tipo == 'SEMESTRAL' else 4
    if count_valid < min_periodos:
        return np.nan
    
    return soma_lpa


def _obter_preco_ultimo_trimestre_ano(dados: DadosEmpresa, periodo_referencia: str) -> Tuple[float, str]:
    """
    Obtém preço do último trimestre disponível DO ANO de referência.
    
    USO: Histórico anualizado (colunas de anos específicos no CSV)
    
    Lógica:
    1. Extrai ano do período de referência
    2. Tenta buscar T4 do ano (se existir, ano está fechado)
    3. Se não existir T4, busca T3, depois T2, depois T1 DO MESMO ANO
    
    Args:
        dados: Dados da empresa
        periodo_referencia: Período de referência (ex: "2025T3")
    
    Returns:
        (preço, período_usado)
    
    Exemplo:
        Para 2025T3 → busca 2025T4 (não existe) → busca 2025T3 (11.46)
    """
    if dados.precos is None or not dados.periodos:
        return np.nan, ""
    
    # Extrair ano do período de referência
    ano_ref, _ = _parse_periodo(periodo_referencia)
    if ano_ref == 0:
        return np.nan, ""
    
    # Tentar períodos do ano em ordem decrescente: T4 → T3 → T2 → T1
    for tri in ['T4', 'T3', 'T2', 'T1']:
        periodo_teste = f"{ano_ref}{tri}"
        preco = _obter_preco(dados, periodo_teste)
        if np.isfinite(preco) and preco > 0:
            return preco, periodo_teste
    
    # Se nenhum período do ano existe, busca último disponível
    return _obter_preco_atual(dados)


# ======================================================================================
# FUNÇÕES PARA OBTER RECEITA CORRETA POR TIPO DE EMPRESA
# ======================================================================================

def _obter_receita_holding_bbse3(dados: DadosEmpresa, periodo: str) -> float:
    """
    Obtém receita total da BBSE3: Comissões (3.05.01) + Equivalência (3.06.01).
    
    BBSE3 é holding que lucra com:
    - Corretagem de seguros (3.05.01)
    - Lucro das seguradoras investidas (3.06.01)
    """
    comissoes = _extrair_valor_conta(dados.dre, "3.05.01", periodo)
    equivalencia = _extrair_valor_conta(dados.dre, "3.06.01", periodo)
    
    comissoes = comissoes if np.isfinite(comissoes) else 0
    equivalencia = equivalencia if np.isfinite(equivalencia) else 0
    
    return comissoes + equivalencia


def _obter_receita_holding_cxse3(dados: DadosEmpresa, periodo: str) -> float:
    """
    Obtém receita total da CXSE3: Prestação Serviços (3.04.04.02) + Equivalência (3.04.06).
    
    CXSE3 usa estrutura tradicional:
    - Receitas de prestação de serviços (3.04.04.02)
    - Resultado de Equivalência Patrimonial (3.04.06)
    """
    servicos = _extrair_valor_conta(dados.dre, "3.04.04.02", periodo)
    equivalencia = _extrair_valor_conta(dados.dre, "3.04.06", periodo)
    
    servicos = servicos if np.isfinite(servicos) else 0
    equivalencia = equivalencia if np.isfinite(equivalencia) else 0
    
    return servicos + equivalencia


def _obter_receita_irbr3(dados: DadosEmpresa, periodo: str) -> float:
    """
    Obtém receita da IRBR3: Receitas com Resseguros (3.01.02).
    
    IRBR3 é resseguradora - receita está em subconta específica.
    """
    receita = _extrair_valor_conta(dados.dre, "3.01.02", periodo)
    return receita if np.isfinite(receita) else np.nan


def _obter_receita_pssa3(dados: DadosEmpresa, periodo: str) -> float:
    """
    Obtém receita da PSSA3 considerando quebra IFRS 17 em 2023.
    
    ANTES (2015-2022): 3.01.01 (Prêmios Emitidos)
    DEPOIS (2023+): 3.01.07 (Receita de Contrato de Seguro)
    """
    ano, _ = _parse_periodo(periodo)
    
    if ano >= 2023:
        # IFRS 17: usa receita agregada
        receita = _extrair_valor_conta(dados.dre, "3.01.07", periodo)
    else:
        # Estrutura antiga: usa prêmios emitidos
        receita = _extrair_valor_conta(dados.dre, "3.01.01", periodo)
    
    return receita if np.isfinite(receita) else np.nan


def _calcular_receita_ltm_holding_bbse3(dados: DadosEmpresa, periodo_fim: str) -> float:
    """Calcula receita LTM para BBSE3 (Comissões + Equivalência)."""
    if dados.padrao_fiscal is None:
        return np.nan
    
    periodos = dados.periodos
    if periodo_fim not in periodos:
        return np.nan
    
    idx_fim = periodos.index(periodo_fim)
    n_trimestres = 3 if dados.padrao_fiscal.tipo == 'SEMESTRAL' else 4
    start_idx = max(0, idx_fim - n_trimestres + 1)
    periodos_ltm = periodos[start_idx:idx_fim + 1]
    
    soma = 0.0
    count = 0
    
    for p in periodos_ltm:
        val = _obter_receita_holding_bbse3(dados, p)
        if np.isfinite(val):
            soma += val
            count += 1
    
    min_periodos = 3 if dados.padrao_fiscal.tipo == 'SEMESTRAL' else 4
    if count < min_periodos:
        return np.nan
    
    return soma


def _calcular_receita_ltm_holding_cxse3(dados: DadosEmpresa, periodo_fim: str) -> float:
    """Calcula receita LTM para CXSE3 (Serviços + Equivalência)."""
    if dados.padrao_fiscal is None:
        return np.nan
    
    periodos = dados.periodos
    if periodo_fim not in periodos:
        return np.nan
    
    idx_fim = periodos.index(periodo_fim)
    n_trimestres = 3 if dados.padrao_fiscal.tipo == 'SEMESTRAL' else 4
    start_idx = max(0, idx_fim - n_trimestres + 1)
    periodos_ltm = periodos[start_idx:idx_fim + 1]
    
    soma = 0.0
    count = 0
    
    for p in periodos_ltm:
        val = _obter_receita_holding_cxse3(dados, p)
        if np.isfinite(val):
            soma += val
            count += 1
    
    min_periodos = 3 if dados.padrao_fiscal.tipo == 'SEMESTRAL' else 4
    if count < min_periodos:
        return np.nan
    
    return soma

# ======================================================================================
# CALCULADORA DE MÚLTIPLOS - EMPRESAS NÃO-FINANCEIRAS (22 MÚLTIPLOS)
# ======================================================================================

def calcular_multiplos_periodo(dados: DadosEmpresa, periodo: str, usar_preco_atual: bool = True) -> Dict[str, Optional[float]]:
    """
    Calcula todos os 22 múltiplos para um período específico (empresas não-financeiras).
    
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

    # ✅ Expor Valor de Mercado (R$ mil)
    resultado["VALOR_MERCADO"] = _normalizar_valor(market_cap, decimals=2)
    
    ev = _calcular_ev(dados, periodo, market_cap)

    # ==================== LUCRO LÍQUIDO LTM (para PAYOUT) ====================
    
    ll_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["lucro_liquido"], periodo)
    
    # ==================== VALUATION ====================
    
    # P/L = Preço / EPS (Lucro Líquido LTM / Ações)
    # ✅ Alinha com o padrão clássico (Investidor10): EPS = Lucro Líquido LTM / Ações (ON+PN quando possível)
    acoes_ref = _obter_acoes(dados, periodo)
    eps_ltm = (ll_ltm * 1000.0) / acoes_ref if np.isfinite(ll_ltm) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan

    if usar_preco_atual:
        preco_pl, periodo_preco_pl = _obter_preco_atual(dados)
    else:
        preco_pl, periodo_preco_pl = _obter_preco_ultimo_trimestre_ano(dados, periodo)

    # ✅ Alinhamento com StatusInvest/Investidor10:
    # Preferir múltiplos baseados em Valor de Mercado (Market Cap) quando disponível,
    # pois é robusto para empresas multi-classe e evita distorções com UNIT/11.
    p_l_vm = _safe_divide(market_cap, ll_ltm)  # ambos em R$ mil
    p_l_preco = _safe_divide(preco_pl, eps_ltm)
    resultado["P_L"] = _normalizar_valor(p_l_vm if np.isfinite(p_l_vm) else p_l_preco)

    # Obter Patrimônio Líquido (usado em P/VPA, ROIC, Dív.Líq/PL)
    pl = _obter_valor_pontual(dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)

    # P/VPA = Preço / VPA (PL / Ações)
    vpa = (pl * 1000.0) / acoes_ref if np.isfinite(pl) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan
    p_vpa_vm = _safe_divide(market_cap, pl)  # ambos em R$ mil
    p_vpa_preco = _safe_divide(preco_pl, vpa)
    resultado["P_VPA"] = _normalizar_valor(p_vpa_vm if np.isfinite(p_vpa_vm) else p_vpa_preco)
    
    ebitda_ltm = _calcular_ebitda_ltm(dados, periodo)
    resultado["EV_EBITDA"] = _normalizar_valor(_safe_divide(ev, ebitda_ltm))
    
    ebit_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["ebit"], periodo)
    resultado["EV_EBIT"] = _normalizar_valor(_safe_divide(ev, ebit_ltm))
    
    receita_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["receita"], periodo)
    resultado["EV_RECEITA"] = _normalizar_valor(_safe_divide(ev, receita_ltm))
    
    # ==================== DIVIDENDOS ====================
    
    dividendos_ltm = _calcular_dividendos_ltm(dados, periodo)
    
    # Dividend Yield (padrão clássico) = (Dividendos por Ação LTM / Preço) × 100
    # dividendos_ltm está em R$ mil (total); converter para R$/ação usando acoes_ref
    dps_ltm = (dividendos_ltm * 1000.0) / acoes_ref if np.isfinite(dividendos_ltm) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan
    dy_vm = _safe_divide(dividendos_ltm, market_cap) * 100 if np.isfinite(market_cap) and market_cap > 0 else np.nan
    dy_preco = _safe_divide(dps_ltm, preco_pl) * 100
    resultado["DY"] = _normalizar_valor(dy_vm if np.isfinite(dy_vm) else dy_preco)

    # Payout (padrão clássico) = Dividendos por Ação / EPS × 100
    payout_vm = _safe_divide(dividendos_ltm, ll_ltm) * 100 if np.isfinite(ll_ltm) and ll_ltm > 0 else np.nan
    payout_preco = _safe_divide(dps_ltm, eps_ltm) * 100
    resultado["PAYOUT"] = _normalizar_valor(payout_vm if np.isfinite(payout_vm) else payout_preco)
    
    # ==================== RENTABILIDADE ====================
    
    pl_medio = _obter_valor_medio(dados, dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)
    resultado["ROE"] = _normalizar_valor(_safe_divide(ll_ltm, pl_medio) * 100)
    
    at_medio = _obter_valor_medio(dados, dados.bpa, CONTAS_BPA["ativo_total"], periodo)
    resultado["ROA"] = _normalizar_valor(_safe_divide(ll_ltm, at_medio) * 100)
    
    # ROIC = NOPAT / Capital Investido
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
    
    #resultado_fin = _calcular_ltm(dados, dados.dre, CONTAS_DRE["resultado_financeiro"], periodo)
    #desp_fin = abs(resultado_fin) if np.isfinite(resultado_fin) and resultado_fin < 0 else np.nan

    desp_fin_ltm = _calcular_ltm(dados, dados.dre, "3.06.02", periodo)
    desp_fin = abs(desp_fin_ltm) if np.isfinite(desp_fin_ltm) else np.nan
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
# METADADOS DOS MÚLTIPLOS - EMPRESAS NÃO-FINANCEIRAS
# ======================================================================================

MULTIPLOS_METADATA = {
    "VALOR_MERCADO": {"nome": "Valor de Mercado", "categoria": "Valuation", "formula": "Preço × Ações (3+4)", "unidade": "R$ mil", "usa_preco": True},
    #"P_L": {"nome": "P/L", "categoria": "Valuation", "formula": "Market Cap / Lucro Líquido LTM", "unidade": "x", "usa_preco": True},
    "P_L": {"nome": "P/L", "categoria": "Valuation", "formula": "Preço / Lucro por Ação LTM", "unidade": "x", "usa_preco": True},
    #"P_VPA": {"nome": "P/VPA", "categoria": "Valuation", "formula": "Market Cap / Patrimônio Líquido", "unidade": "x", "usa_preco": True},
    "P_VPA": {"nome": "P/VPA", "categoria": "Valuation", "formula": "Preço / Valor Patrimonial por Ação", "unidade": "x", "usa_preco": True},
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
# METADADOS DOS MÚLTIPLOS - BANCOS (8 ESSENCIAIS)
# ======================================================================================

MULTIPLOS_BANCOS_METADATA = {
    "VALOR_MERCADO": {
        "nome": "Valor de Mercado",
        "categoria": "Valuation",
        "formula": "Preço × Ações (3+4)",
        "unidade": "R$ mil",
        "usa_preco": True
    },
    # Valuation (4 múltiplos)
    "P_L": {
        "nome": "P/L",
        "categoria": "Valuation",
        #"formula": "Market Cap / Lucro Líquido LTM",
        "formula": "Preço / Lucro por Ação LTM",
        "unidade": "x",
        "usa_preco": True
    },
    "P_VPA": {
        "nome": "P/VPA",
        "categoria": "Valuation",
        "formula": "Preço / Valor Patrimonial por Ação",
        "unidade": "x",
        "usa_preco": True
    },
    "DY": {
        "nome": "Dividend Yield",
        "categoria": "Valuation",
        "formula": "Dividendos LTM / Market Cap × 100",
        "unidade": "%",
        "usa_preco": True
    },
    "PAYOUT": {
        "nome": "Payout",
        "categoria": "Valuation",
        "formula": "Dividendos LTM / Lucro Líquido LTM × 100",
        "unidade": "%",
        "usa_preco": False
    },
    
    # Rentabilidade (3 múltiplos)
    "ROE": {
        "nome": "ROE",
        "categoria": "Rentabilidade",
        "formula": "Lucro Líquido LTM / PL Médio × 100",
        "unidade": "%",
        "usa_preco": False
    },
    "ROA": {
        "nome": "ROA",
        "categoria": "Rentabilidade",
        "formula": "Lucro Líquido LTM / Ativo Total Médio × 100",
        "unidade": "%",
        "usa_preco": False
    },
    "MARGEM_LIQUIDA": {
        "nome": "Margem Líquida",
        "categoria": "Rentabilidade",
        "formula": "Lucro Líquido LTM / Receita Intermediação LTM × 100",
        "unidade": "%",
        "usa_preco": False
    },
    
    # Estrutura (1 múltiplo)
    "PL_ATIVOS": {
        "nome": "PL/Ativos",
        "categoria": "Estrutura",
        "formula": "Patrimônio Líquido / Ativo Total × 100",
        "unidade": "%",
        "usa_preco": False
    },
}


# ======================================================================================
# METADADOS DOS MÚLTIPLOS - HOLDINGS DE SEGUROS (10 MÚLTIPLOS)
# ======================================================================================

MULTIPLOS_HOLDINGS_SEGUROS_METADATA = {
    "VALOR_MERCADO": {
        "nome": "Valor de Mercado",
        "categoria": "Valuation",
        "formula": "Preço × Ações (3+4)",
        "unidade": "R$ mil",
        "usa_preco": True
    },
    # Valuation (5 múltiplos)
    "P_L": {
        "nome": "P/L",
        "categoria": "Valuation",
        #"formula": "Market Cap / Lucro Líquido LTM",
        "formula": "Preço / Lucro por Ação LTM",
        "unidade": "x",
        "usa_preco": True
    },
    "P_VPA": {
        "nome": "P/VPA",
        "categoria": "Valuation",
        "formula": "Preço / Valor Patrimonial por Ação",
        "unidade": "x",
        "usa_preco": True
    },
    "DY": {
        "nome": "Dividend Yield",
        "categoria": "Valuation",
        "formula": "Dividendos LTM / Market Cap × 100",
        "unidade": "%",
        "usa_preco": True
    },
    "PAYOUT": {
        "nome": "Payout",
        "categoria": "Valuation",
        "formula": "Dividendos LTM / Lucro Líquido LTM × 100",
        "unidade": "%",
        "usa_preco": False
    },
    "EV_RECEITA": {
        "nome": "EV/Receita",
        "categoria": "Valuation",
        "formula": "Enterprise Value / Receita Corretagem LTM",
        "unidade": "x",
        "usa_preco": True
    },
    
    # Rentabilidade (4 múltiplos)
    "ROE": {
        "nome": "ROE",
        "categoria": "Rentabilidade",
        "formula": "Lucro Líquido LTM / PL Médio × 100",
        "unidade": "%",
        "usa_preco": False
    },
    "ROA": {
        "nome": "ROA",
        "categoria": "Rentabilidade",
        "formula": "Lucro Líquido LTM / Ativo Total Médio × 100",
        "unidade": "%",
        "usa_preco": False
    },
    "MARGEM_LIQUIDA": {
        "nome": "Margem Líquida",
        "categoria": "Rentabilidade",
        "formula": "Lucro Líquido LTM / Receita Corretagem LTM × 100",
        "unidade": "%",
        "usa_preco": False
    },
    "MARGEM_OPERACIONAL": {
        "nome": "Margem Operacional",
        "categoria": "Rentabilidade",
        "formula": "EBIT / Receita Corretagem LTM × 100",
        "unidade": "%",
        "usa_preco": False
    },
    
    # Eficiência (1 múltiplo)
    "INDICE_EFICIENCIA": {
        "nome": "Índice Eficiência",
        "categoria": "Eficiência",
        "formula": "(Desp. Vendas + Desp. Admin.) / Receita × 100",
        "unidade": "%",
        "usa_preco": False
    },
}


# ======================================================================================
# METADADOS DOS MÚLTIPLOS - SEGURADORAS OPERACIONAIS (10 MÚLTIPLOS)
# ======================================================================================

MULTIPLOS_SEGURADORAS_METADATA = {
    "VALOR_MERCADO": {
        "nome": "Valor de Mercado",
        "categoria": "Valuation",
        "formula": "Preço × Ações (3+4)",
        "unidade": "R$ mil",
        "usa_preco": True
    },
    # Valuation (4 múltiplos)
    "P_L": {
        "nome": "P/L",
        "categoria": "Valuation",
        #"formula": "Market Cap / Lucro Líquido LTM",
        "formula": "Preço / Lucro por Ação LTM",
        "unidade": "x",
        "usa_preco": True
    },
    "P_VPA": {
        "nome": "P/VPA",
        "categoria": "Valuation",
        "formula": "Preço / Valor Patrimonial por Ação",
        "unidade": "x",
        "usa_preco": True
    },
    "DY": {
        "nome": "Dividend Yield",
        "categoria": "Valuation",
        "formula": "Dividendos LTM / Market Cap × 100",
        "unidade": "%",
        "usa_preco": True
    },
    "PAYOUT": {
        "nome": "Payout",
        "categoria": "Valuation",
        "formula": "Dividendos LTM / Lucro Líquido LTM × 100",
        "unidade": "%",
        "usa_preco": False
    },
    
    # Rentabilidade (2 múltiplos)
    "ROE": {
        "nome": "ROE",
        "categoria": "Rentabilidade",
        "formula": "Lucro Líquido LTM / PL Médio × 100",
        "unidade": "%",
        "usa_preco": False
    },
    "ROA": {
        "nome": "ROA",
        "categoria": "Rentabilidade",
        "formula": "Lucro Líquido LTM / Ativo Total Médio × 100",
        "unidade": "%",
        "usa_preco": False
    },
    
    # Estrutura (1 múltiplo)
    "PL_ATIVOS": {
        "nome": "PL/Ativos",
        "categoria": "Estrutura",
        "formula": "Patrimônio Líquido / Ativo Total × 100",
        "unidade": "%",
        "usa_preco": False
    },
    
    # Operacional (3 múltiplos - específicos de seguros)
    "COMBINED_RATIO": {
        "nome": "Combined Ratio",
        "categoria": "Operacional",
        "formula": "(Sinistros + Custos Aq. + Desp. Admin.) / Prêmios Ganhos × 100",
        "unidade": "%",
        "usa_preco": False
    },
    "SINISTRALIDADE": {
        "nome": "Sinistralidade",
        "categoria": "Operacional",
        "formula": "Sinistros Retidos / Prêmios Ganhos × 100",
        "unidade": "%",
        "usa_preco": False
    },
    "MARGEM_SUBSCRICAO": {
        "nome": "Margem Subscrição",
        "categoria": "Operacional",
        "formula": "(Prêmios - Sinistros - Custos Aq.) / Prêmios × 100",
        "unidade": "%",
        "usa_preco": False
    },
}


# ======================================================================================
# DETECTOR DE CÓDIGO DO PL PARA BANCOS
# ======================================================================================

def _detectar_codigo_pl_banco(df_bpp: pd.DataFrame) -> str:
    """
    Detecta dinamicamente o código do Patrimônio Líquido no BPP do banco.
    
    O PL pode estar em 2.07 (BBAS3, BBDC4) ou 2.08 (ITUB4).
    """
    if df_bpp is None or df_bpp.empty:
        return "2.07"
    
    for idx, row in df_bpp.iterrows():
        cd = str(row.get('cd_conta', ''))
        conta = str(row.get('conta', '')).lower()
        if 'patrimônio líquido' in conta or 'patrimonio liquido' in conta:
            if cd.startswith('2.0') and len(cd) == 4:  # 2.07 ou 2.08
                return cd
    return "2.07"


# ======================================================================================
# CALCULADORA DE MÚLTIPLOS - BANCOS (8 ESSENCIAIS)
# ======================================================================================

def calcular_multiplos_banco(dados: DadosEmpresa, periodo: str, usar_preco_atual: bool = True) -> Dict[str, Optional[float]]:
    """
    Calcula 8 múltiplos essenciais para bancos usando apenas contas agregadas robustas.
    
    FILOSOFIA: Prioriza CONFIABILIDADE sobre abrangência.
    - Usa apenas contas de nível superior que sempre existem
    - Evita dependência de subcontas que variam entre bancos
    - Detecção automática do código do PL (2.07 ou 2.08)
    
    Múltiplos calculados:
    ✅ Valuation (4): P/L, P/VPA, DY, Payout
    ✅ Rentabilidade (3): ROE, ROA, Margem Líquida
    ✅ Estrutura (1): PL/Ativos
    
    Args:
        dados: Dados completos da empresa
        periodo: Período de referência (ex: "2024T4")
        usar_preco_atual: Se True, usa preço mais recente para valuation
    
    Returns:
        Dicionário com 8 múltiplos essenciais
    """
    resultado: Dict[str, Optional[float]] = {}
    
    # Detectar código do PL dinamicamente (2.07 ou 2.08)
    pl_code = _detectar_codigo_pl_banco(dados.bpp)
    
    # ==================== MARKET CAP ====================
    
    if usar_preco_atual:
        market_cap = _calcular_market_cap_atual(dados)
    else:
        market_cap = _calcular_market_cap(dados, periodo)


    # ✅ Expor Valor de Mercado (R$ mil)
    resultado["VALOR_MERCADO"] = _normalizar_valor(market_cap, decimals=2)
    
    # ==================== VALORES BASE (CONTAS AGREGADAS) ====================
    
    # Lucro Líquido LTM - Conta 3.11 (sempre existe)
    ll_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE_BANCOS["lucro_liquido"], periodo)
    
    # Ativo Total - Conta 1 (sempre existe)
    at = _obter_valor_pontual(dados.bpa, CONTAS_BPA_BANCOS["ativo_total"], periodo)
    at_medio = _obter_valor_medio(dados, dados.bpa, CONTAS_BPA_BANCOS["ativo_total"], periodo)
    
    # Receita de Intermediação LTM - Conta 3.01 (sempre existe)
    receita_interm = _calcular_ltm(dados, dados.dre, CONTAS_DRE_BANCOS["receita_intermediacao"], periodo)
    
    # Dividendos LTM
    dividendos_ltm = _calcular_dividendos_ltm(dados, periodo)
    
    # ==================== VALUATION (4 MÚLTIPLOS) ====================
    
    # P/L = Preço / EPS (Lucro Líquido LTM / Ações)
    acoes_ref = _obter_acoes(dados, periodo)
    eps_ltm = (ll_ltm * 1000.0) / acoes_ref if np.isfinite(ll_ltm) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan

    if usar_preco_atual:
        preco_pl, periodo_preco_pl = _obter_preco_atual(dados)
    else:
        preco_pl, periodo_preco_pl = _obter_preco_ultimo_trimestre_ano(dados, periodo)

    # ✅ Alinhamento com StatusInvest/Investidor10:
    # Preferir múltiplos baseados em Valor de Mercado (Market Cap) quando disponível,
    # pois é robusto para empresas multi-classe e evita distorções com UNIT/11.
    p_l_vm = _safe_divide(market_cap, ll_ltm)  # ambos em R$ mil
    p_l_preco = _safe_divide(preco_pl, eps_ltm)
    resultado["P_L"] = _normalizar_valor(p_l_vm if np.isfinite(p_l_vm) else p_l_preco)

    # Patrimônio Líquido - Código detectado automaticamente (2.07 ou 2.08)
    pl = _obter_valor_pontual(dados.bpp, pl_code, periodo)
    pl_medio = _obter_valor_medio(dados, dados.bpp, pl_code, periodo)

    # P/VPA = Preço / VPA (PL / Ações)
    vpa = (pl * 1000.0) / acoes_ref if np.isfinite(pl) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan
    p_vpa_vm = _safe_divide(market_cap, pl)  # ambos em R$ mil
    p_vpa_preco = _safe_divide(preco_pl, vpa)
    resultado["P_VPA"] = _normalizar_valor(p_vpa_vm if np.isfinite(p_vpa_vm) else p_vpa_preco)
    
    # Dividend Yield (padrão clássico) = (Dividendos por Ação LTM / Preço) × 100
    dps_ltm = (dividendos_ltm * 1000.0) / acoes_ref if np.isfinite(dividendos_ltm) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan
    dy_vm = _safe_divide(dividendos_ltm, market_cap) * 100 if np.isfinite(market_cap) and market_cap > 0 else np.nan
    dy_preco = _safe_divide(dps_ltm, preco_pl) * 100
    resultado["DY"] = _normalizar_valor(dy_vm if np.isfinite(dy_vm) else dy_preco)

    # Payout (padrão clássico) = Dividendos por Ação / EPS × 100
    payout_vm = _safe_divide(dividendos_ltm, ll_ltm) * 100 if np.isfinite(ll_ltm) and ll_ltm > 0 else np.nan
    payout_preco = _safe_divide(dps_ltm, eps_ltm) * 100
    resultado["PAYOUT"] = _normalizar_valor(payout_vm if np.isfinite(payout_vm) else payout_preco)
    
    # ==================== RENTABILIDADE (3 MÚLTIPLOS) ====================
    
    # ROE = (Lucro Líquido LTM / PL Médio) × 100
    resultado["ROE"] = _normalizar_valor(
        _safe_divide(ll_ltm, pl_medio) * 100 if np.isfinite(pl_medio) and pl_medio > 0 else np.nan
    )
    
    # ROA = (Lucro Líquido LTM / Ativo Total Médio) × 100
    resultado["ROA"] = _normalizar_valor(
        _safe_divide(ll_ltm, at_medio) * 100 if np.isfinite(at_medio) and at_medio > 0 else np.nan
    )
    
    # Margem Líquida = (Lucro Líquido LTM / Receita Intermediação LTM) × 100
    resultado["MARGEM_LIQUIDA"] = _normalizar_valor(
        _safe_divide(ll_ltm, receita_interm) * 100 if np.isfinite(receita_interm) and receita_interm > 0 else np.nan
    )
    
    # ==================== ESTRUTURA (1 MÚLTIPLO) ====================
    
    # PL/Ativos = (Patrimônio Líquido / Ativo Total) × 100
    resultado["PL_ATIVOS"] = _normalizar_valor(
        _safe_divide(pl, at) * 100 if np.isfinite(at) and at > 0 else np.nan
    )
    
    return resultado

# ======================================================================================
# CALCULADORA DE MÚLTIPLOS - HOLDINGS DE SEGUROS (10 MÚLTIPLOS)
# ======================================================================================
def calcular_multiplos_holding_seguros(dados: DadosEmpresa, periodo: str, usar_preco_atual: bool = True) -> Dict[str, Optional[float]]:
    """
    Calcula 10 múltiplos essenciais para holdings de seguros (BBSE3, CXSE3).
    
    CORREÇÃO CRÍTICA: BBSE3 e CXSE3 têm estruturas DRE DIFERENTES!
    - BBSE3: Receita em 3.05.01 (Comissões) + 3.06.01 (Equivalência)
    - CXSE3: Receita em 3.04.04.02 (Serviços) + 3.04.06 (Equivalência)
    
    Múltiplos calculados:
    ✅ Valuation (5): P/L, P/VPA, DY, Payout, EV/Receita
    ✅ Rentabilidade (4): ROE, ROA, Margem Líquida, Margem Operacional
    ✅ Eficiência (1): Índice de Eficiência
    """
    resultado: Dict[str, Optional[float]] = {}
    ticker_upper = dados.ticker.upper().strip()
    
    # ==================== MARKET CAP E EV ====================
    
    if usar_preco_atual:
        market_cap = _calcular_market_cap_atual(dados)
    else:
        market_cap = _calcular_market_cap(dados, periodo)


    # ✅ Expor Valor de Mercado (R$ mil)
    resultado["VALOR_MERCADO"] = _normalizar_valor(market_cap, decimals=2)
    
    ev = _calcular_ev(dados, periodo, market_cap)
    
    # ==================== VALORES BASE - ESPECÍFICOS POR TICKER ====================
    
    # Lucro Líquido LTM - conta varia por ticker
    if ticker_upper == "BBSE3":
        ll_ltm = _calcular_ltm(dados, dados.dre, "3.13", periodo)  # BBSE3 usa 3.13
        ll_ltm_controladora = _calcular_ltm(dados, dados.dre, "3.13.01", periodo)
    else:  # CXSE3
        ll_ltm = _calcular_ltm(dados, dados.dre, "3.11", periodo)  # CXSE3 usa 3.11
        ll_ltm_controladora = _calcular_ltm(dados, dados.dre, "3.11.01", periodo)
    
    # Ativo Total
    at = _obter_valor_pontual(dados.bpa, CONTAS_BPA["ativo_total"], periodo)
    at_medio = _obter_valor_medio(dados, dados.bpa, CONTAS_BPA["ativo_total"], periodo)
    
    # Receita LTM - CORRIGIDO: usa função específica por ticker
    if ticker_upper == "BBSE3":
        receita_ltm = _calcular_receita_ltm_holding_bbse3(dados, periodo)
    else:  # CXSE3
        receita_ltm = _calcular_receita_ltm_holding_cxse3(dados, periodo)
    
    # EBIT LTM - conta varia por ticker
    if ticker_upper == "BBSE3":
        ebit_ltm = _calcular_ltm(dados, dados.dre, "3.07", periodo)  # BBSE3 usa 3.07
    else:  # CXSE3
        ebit_ltm = _calcular_ltm(dados, dados.dre, "3.05", periodo)  # CXSE3 usa 3.05
    
    # Despesas Operacionais LTM
    if ticker_upper == "BBSE3":
        desp_admin_ltm = _calcular_ltm(dados, dados.dre, "3.04", periodo)
        desp_vendas_ltm = 0.0  # BBSE3 não tem despesas com vendas separadas
    else:  # CXSE3
        desp_admin_ltm = _calcular_ltm(dados, dados.dre, "3.04.02", periodo)
        desp_vendas_ltm = _calcular_ltm(dados, dados.dre, "3.04.01", periodo)
        desp_vendas_ltm = desp_vendas_ltm if np.isfinite(desp_vendas_ltm) else 0.0
    
    # Dividendos LTM
    dividendos_ltm = _calcular_dividendos_ltm(dados, periodo)
    
    # ==================== VALUATION (4 MÚLTIPLOS) ====================
    
    # P/L = Preço / EPS (Lucro Líquido LTM / Ações)
    acoes_ref = _obter_acoes(dados, periodo)
    eps_ltm = (ll_ltm * 1000.0) / acoes_ref if np.isfinite(ll_ltm) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan

    if usar_preco_atual:
        preco_pl, periodo_preco_pl = _obter_preco_atual(dados)
    else:
        preco_pl, periodo_preco_pl = _obter_preco_ultimo_trimestre_ano(dados, periodo)

    # ✅ Alinhamento com StatusInvest/Investidor10:
    # Preferir múltiplos baseados em Valor de Mercado (Market Cap) quando disponível,
    # pois é robusto para empresas multi-classe e evita distorções com UNIT/11.
    p_l_vm = _safe_divide(market_cap, ll_ltm)  # ambos em R$ mil
    p_l_preco = _safe_divide(preco_pl, eps_ltm)
    resultado["P_L"] = _normalizar_valor(p_l_vm if np.isfinite(p_l_vm) else p_l_preco)

    # Patrimônio Líquido - Código detectado automaticamente (2.07 ou 2.08)
    pl = _obter_valor_pontual(dados.bpp, pl_code, periodo)
    pl_medio = _obter_valor_medio(dados, dados.bpp, pl_code, periodo)

    # P/VPA = Preço / VPA (PL / Ações)
    vpa = (pl * 1000.0) / acoes_ref if np.isfinite(pl) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan
    p_vpa_vm = _safe_divide(market_cap, pl)  # ambos em R$ mil
    p_vpa_preco = _safe_divide(preco_pl, vpa)
    resultado["P_VPA"] = _normalizar_valor(p_vpa_vm if np.isfinite(p_vpa_vm) else p_vpa_preco)
    
    # Dividend Yield (padrão clássico) = (Dividendos por Ação LTM / Preço) × 100
    dps_ltm = (dividendos_ltm * 1000.0) / acoes_ref if np.isfinite(dividendos_ltm) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan
    dy_vm = _safe_divide(dividendos_ltm, market_cap) * 100 if np.isfinite(market_cap) and market_cap > 0 else np.nan
    dy_preco = _safe_divide(dps_ltm, preco_pl) * 100
    resultado["DY"] = _normalizar_valor(dy_vm if np.isfinite(dy_vm) else dy_preco)

    # Payout (padrão clássico) = Dividendos por Ação / EPS × 100
    payout_vm = _safe_divide(dividendos_ltm, ll_ltm) * 100 if np.isfinite(ll_ltm) and ll_ltm > 0 else np.nan
    payout_preco = _safe_divide(dps_ltm, eps_ltm) * 100
    resultado["PAYOUT"] = _normalizar_valor(payout_vm if np.isfinite(payout_vm) else payout_preco)
    
    # EV/Receita = Enterprise Value / Receita LTM (CORRIGIDO!)
    resultado["EV_RECEITA"] = _normalizar_valor(_safe_divide(ev, receita_ltm))
    
    # ==================== RENTABILIDADE (4 MÚLTIPLOS) ====================
    
    # ROE = (Lucro Líquido LTM / PL Médio) × 100
    resultado["ROE"] = _normalizar_valor(
        _safe_divide(ll_ltm, pl_medio) * 100 if np.isfinite(pl_medio) and pl_medio > 0 else np.nan
    )
    
    # ROA = (Lucro Líquido LTM / Ativo Total Médio) × 100
    resultado["ROA"] = _normalizar_valor(
        _safe_divide(ll_ltm, at_medio) * 100 if np.isfinite(at_medio) and at_medio > 0 else np.nan
    )
    
    # Margem Líquida = (Lucro Líquido LTM / Receita LTM) × 100 (CORRIGIDO!)
    resultado["MARGEM_LIQUIDA"] = _normalizar_valor(
        _safe_divide(ll_ltm, receita_ltm) * 100 if np.isfinite(receita_ltm) and receita_ltm > 0 else np.nan
    )
    
    # Margem Operacional = (EBIT / Receita LTM) × 100 (CORRIGIDO!)
    resultado["MARGEM_OPERACIONAL"] = _normalizar_valor(
        _safe_divide(ebit_ltm, receita_ltm) * 100 if np.isfinite(receita_ltm) and receita_ltm > 0 else np.nan
    )
    
    # ==================== EFICIÊNCIA (1 MÚLTIPLO) ====================
    
    # Índice de Eficiência = (Desp. Vendas + Desp. Admin.) / Receita × 100 (CORRIGIDO!)
    desp_admin_val = abs(desp_admin_ltm) if np.isfinite(desp_admin_ltm) else 0
    desp_vendas_val = abs(desp_vendas_ltm) if np.isfinite(desp_vendas_ltm) else 0
    total_despesas = desp_admin_val + desp_vendas_val
    
    resultado["INDICE_EFICIENCIA"] = _normalizar_valor(
        _safe_divide(total_despesas, receita_ltm) * 100 if np.isfinite(receita_ltm) and receita_ltm > 0 else np.nan
    )
    
    return resultado


# ======================================================================================
# CALCULADORA DE MÚLTIPLOS - SEGURADORAS OPERACIONAIS (10 MÚLTIPLOS)
# ======================================================================================

def calcular_multiplos_seguradora(dados: DadosEmpresa, periodo: str, usar_preco_atual: bool = True) -> Dict[str, Optional[float]]:
    """
    Calcula 10 múltiplos essenciais para seguradoras operacionais (IRBR3, PSSA3).
    
    CORREÇÕES APLICADAS:
    - IRBR3: Suporta contas 3.11 e 3.13 para Lucro Líquido
    - PSSA3: Trata quebra IFRS 17 (2023+)
    - Margem Subscrição: usa 3.03 (Resultado Bruto) DIRETAMENTE
    - Combined Ratio: calcula corretamente para ambas estruturas
    """
    resultado: Dict[str, Optional[float]] = {}
    ticker_upper = dados.ticker.upper().strip()
    
    # ==================== MARKET CAP ====================
    
    if usar_preco_atual:
        market_cap = _calcular_market_cap_atual(dados)
    else:
        market_cap = _calcular_market_cap(dados, periodo)


    # ✅ Expor Valor de Mercado (R$ mil)
    resultado["VALOR_MERCADO"] = _normalizar_valor(market_cap, decimals=2)
    
    # ==================== LUCRO LÍQUIDO - SUPORTA 3.11 E 3.13 ====================
    
    # Tentar ambas as contas (IRBR3 pode usar qualquer uma)
    ll_ltm_3_13 = _calcular_ltm(dados, dados.dre, "3.13", periodo)
    ll_ltm_3_11 = _calcular_ltm(dados, dados.dre, "3.11", periodo)
    
    # Usar a que estiver preenchida
    if np.isfinite(ll_ltm_3_13) and ll_ltm_3_13 != 0:
        ll_ltm = ll_ltm_3_13
        conta_ll = "3.13"
    elif np.isfinite(ll_ltm_3_11) and ll_ltm_3_11 != 0:
        ll_ltm = ll_ltm_3_11
        conta_ll = "3.11"
    else:
        ll_ltm = np.nan
        conta_ll = None
    
    # Lucro Controladora
    if conta_ll == "3.13":
        ll_ltm_controladora = _calcular_ltm(dados, dados.dre, "3.13.01", periodo)
    elif conta_ll == "3.11":
        ll_ltm_controladora = _calcular_ltm(dados, dados.dre, "3.11.01", periodo)
    else:
        ll_ltm_controladora = np.nan
    
    # ==================== PATRIMÔNIO E ATIVO ====================
    
    at = _obter_valor_pontual(dados.bpa, CONTAS_BPA["ativo_total"], periodo)
    at_medio = _obter_valor_medio(dados, dados.bpa, CONTAS_BPA["ativo_total"], periodo)
    
    # ==================== PRÊMIOS - SUPORTA IFRS 17 ====================
    
    ano_periodo, _ = _parse_periodo(periodo)
    
    if ticker_upper == "IRBR3":
        # IRBR3: sempre 3.01.02 (Receitas com Resseguros)
        premios_ltm = _calcular_ltm(dados, dados.dre, "3.01.02", periodo)
    else:  # PSSA3
        if ano_periodo >= 2023:
            # IFRS 17: Receita de Contrato de Seguro
            premios_ltm = _calcular_ltm(dados, dados.dre, "3.01.07", periodo)
        else:
            # Estrutura antiga: Prêmios Ganhos
            premios_ltm = _calcular_ltm(dados, dados.dre, "3.01", periodo)
    
    # ==================== SINISTROS E CUSTOS - SUPORTA IFRS 17 ====================
    
    if ticker_upper == "IRBR3":
        # IRBR3: estrutura fixa
        sinistros_ltm = _calcular_ltm(dados, dados.dre, "3.02.02.01", periodo)
        custos_aq_ltm = _calcular_ltm(dados, dados.dre, "3.02.02.02", periodo)
        desp_admin_ltm = _calcular_ltm(dados, dados.dre, "3.04", periodo)
        
        sinistros_ltm = abs(sinistros_ltm) if np.isfinite(sinistros_ltm) else 0.0
        custos_aq_ltm = abs(custos_aq_ltm) if np.isfinite(custos_aq_ltm) else 0.0
        desp_admin_ltm = abs(desp_admin_ltm) if np.isfinite(desp_admin_ltm) else 0.0
        
    else:  # PSSA3
        if ano_periodo >= 2023:
            # IFRS 17: despesas agregadas
            despesas_seg_ltm = _calcular_ltm(dados, dados.dre, "3.04.05.11", periodo)
            despesas_res_ltm = _calcular_ltm(dados, dados.dre, "3.04.05.12", periodo)
            custos_out_ltm = _calcular_ltm(dados, dados.dre, "3.04.05.08", periodo)
            desp_admin_ltm = _calcular_ltm(dados, dados.dre, "3.04.02", periodo)
            
            # Sinistralidade não pode ser separada (agregado)
            sinistros_ltm = np.nan
            custos_aq_ltm = abs(custos_out_ltm) if np.isfinite(custos_out_ltm) else 0.0
            desp_admin_ltm = abs(desp_admin_ltm) if np.isfinite(desp_admin_ltm) else 0.0
            
            # Total para Combined Ratio
            total_despesas = (
                (abs(despesas_seg_ltm) if np.isfinite(despesas_seg_ltm) else 0.0) +
                (abs(despesas_res_ltm) if np.isfinite(despesas_res_ltm) else 0.0) +
                custos_aq_ltm +
                desp_admin_ltm
            )
        else:
            # Estrutura antiga (até 2022)
            sinistros_ltm = _calcular_ltm(dados, dados.dre, "3.04.05.03", periodo)
            custos_aq_ltm = _calcular_ltm(dados, dados.dre, "3.04.05.07", periodo)
            desp_admin_ltm = _calcular_ltm(dados, dados.dre, "3.04.02", periodo)
            
            sinistros_ltm = abs(sinistros_ltm) if np.isfinite(sinistros_ltm) else 0.0
            custos_aq_ltm = abs(custos_aq_ltm) if np.isfinite(custos_aq_ltm) else 0.0
            desp_admin_ltm = abs(desp_admin_ltm) if np.isfinite(desp_admin_ltm) else 0.0
    
    # Dividendos LTM
    dividendos_ltm = _calcular_dividendos_ltm(dados, periodo)
    
    # ==================== VALUATION (4 MÚLTIPLOS) ====================
    
    # P/L = Preço / EPS (Lucro Líquido LTM / Ações)
    acoes_ref = _obter_acoes(dados, periodo)
    eps_ltm = (ll_ltm * 1000.0) / acoes_ref if np.isfinite(ll_ltm) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan

    if usar_preco_atual:
        preco_pl, periodo_preco_pl = _obter_preco_atual(dados)
    else:
        preco_pl, periodo_preco_pl = _obter_preco_ultimo_trimestre_ano(dados, periodo)

    # ✅ Alinhamento com StatusInvest/Investidor10:
    # Preferir múltiplos baseados em Valor de Mercado (Market Cap) quando disponível,
    # pois é robusto para empresas multi-classe e evita distorções com UNIT/11.
    p_l_vm = _safe_divide(market_cap, ll_ltm)  # ambos em R$ mil
    p_l_preco = _safe_divide(preco_pl, eps_ltm)
    resultado["P_L"] = _normalizar_valor(p_l_vm if np.isfinite(p_l_vm) else p_l_preco)

    # ✅ ADICIONAR: Obter PL (usado em P/VPA, ROE, ROA, PL/Ativos)
    pl = _obter_valor_pontual(dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)
    pl_medio = _obter_valor_medio(dados, dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)

    # P/VPA = Preço / VPA (PL / Ações)
    vpa = (pl * 1000.0) / acoes_ref if np.isfinite(pl) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan
    p_vpa_vm = _safe_divide(market_cap, pl)  # ambos em R$ mil
    p_vpa_preco = _safe_divide(preco_pl, vpa)
    resultado["P_VPA"] = _normalizar_valor(p_vpa_vm if np.isfinite(p_vpa_vm) else p_vpa_preco)
    
    # Dividend Yield (padrão clássico) = (Dividendos por Ação LTM / Preço) × 100
    dps_ltm = (dividendos_ltm * 1000.0) / acoes_ref if np.isfinite(dividendos_ltm) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan
    dy_vm = _safe_divide(dividendos_ltm, market_cap) * 100 if np.isfinite(market_cap) and market_cap > 0 else np.nan
    dy_preco = _safe_divide(dps_ltm, preco_pl) * 100
    resultado["DY"] = _normalizar_valor(dy_vm if np.isfinite(dy_vm) else dy_preco)

    # Payout (padrão clássico) = Dividendos por Ação / EPS × 100
    payout_vm = _safe_divide(dividendos_ltm, ll_ltm) * 100 if np.isfinite(ll_ltm) and ll_ltm > 0 else np.nan
    payout_preco = _safe_divide(dps_ltm, eps_ltm) * 100
    resultado["PAYOUT"] = _normalizar_valor(payout_vm if np.isfinite(payout_vm) else payout_preco)
    
    # ==================== RENTABILIDADE (2 MÚLTIPLOS) ====================
    
    resultado["ROE"] = _normalizar_valor(
        _safe_divide(ll_ltm, pl_medio) * 100 if np.isfinite(pl_medio) and pl_medio > 0 else np.nan
    )
    
    resultado["ROA"] = _normalizar_valor(
        _safe_divide(ll_ltm, at_medio) * 100 if np.isfinite(at_medio) and at_medio > 0 else np.nan
    )
    
    # ==================== ESTRUTURA (1 MÚLTIPLO) ====================
    
    resultado["PL_ATIVOS"] = _normalizar_valor(
        _safe_divide(pl, at) * 100 if np.isfinite(at) and at > 0 else np.nan
    )
    
    # ==================== OPERACIONAL (3 MÚLTIPLOS) ====================
    
    # Combined Ratio
    if ticker_upper == "PSSA3" and ano_periodo >= 2023:
        # IFRS 17: usa total_despesas calculado acima
        numerador_combined = total_despesas
    else:
        # IRBR3 ou PSSA3 pré-2023
        numerador_combined = sinistros_ltm + custos_aq_ltm + desp_admin_ltm
    
    resultado["COMBINED_RATIO"] = _normalizar_valor(
        _safe_divide(numerador_combined, premios_ltm) * 100 if np.isfinite(premios_ltm) and premios_ltm > 0 else np.nan
    )
    
    # Sinistralidade
    if ticker_upper == "PSSA3" and ano_periodo >= 2023:
        # IFRS 17: não pode calcular (agregado)
        resultado["SINISTRALIDADE"] = None
    else:
        resultado["SINISTRALIDADE"] = _normalizar_valor(
            _safe_divide(sinistros_ltm, premios_ltm) * 100 if np.isfinite(premios_ltm) and premios_ltm > 0 else np.nan
        )
    
    # Margem de Subscrição - USA 3.03 (RESULTADO BRUTO) DIRETAMENTE
    resultado_bruto_ltm = _calcular_ltm(dados, dados.dre, "3.03", periodo)
    resultado["MARGEM_SUBSCRICAO"] = _normalizar_valor(
        _safe_divide(resultado_bruto_ltm, premios_ltm) * 100 if np.isfinite(premios_ltm) and premios_ltm > 0 else np.nan
    )
    
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

    # Mantém ano_atual (pode ser útil para debug/metadata), mas o histórico anual NÃO deve usar preço atual
    ano_atual = datetime.now().year

    for ano in sorted(periodos_por_ano.keys()):
        periodos_ano = _ordenar_periodos(periodos_por_ano[ano])

        # Regra do período de referência do ANO:
        # - Se existir T4 do ano, usa T4 (ano fechado)
        # - Caso contrário (ano não fechado), usa o último trimestre reportado (ex.: 2025T3)
        periodo_t4 = f"{ano}T4"
        if periodo_t4 in periodos_ano:
            periodo_referencia = periodo_t4
        else:
            periodo_referencia = periodos_ano[-1]

        # ✅ CORREÇÃO: histórico anual sempre usa preço do período de referência (não "preço atual")
        # Isso garante que, ao anualizar (T1–T3 ano + T4 ano anterior), o preço usado é do último trimestre reportado.
        usar_preco_atual_hist = False

        # Determinar qual função de cálculo usar (mantém a lógica existente)
        if _is_banco(dados.ticker):
            multiplos = calcular_multiplos_banco(dados, periodo_referencia, usar_preco_atual=usar_preco_atual_hist)
        elif _is_holding_seguros(dados.ticker):
            multiplos = calcular_multiplos_holding_seguros(dados, periodo_referencia, usar_preco_atual=usar_preco_atual_hist)
        elif _is_seguradora_operacional(dados.ticker):
            multiplos = calcular_multiplos_seguradora(dados, periodo_referencia, usar_preco_atual=usar_preco_atual_hist)
        else:
            multiplos = calcular_multiplos_periodo(dados, periodo_referencia, usar_preco_atual=usar_preco_atual_hist)

        historico_anual[ano] = {
            "periodo_referencia": periodo_referencia,
            "multiplos": multiplos
        }

    # LTM: Sempre usar último período disponível com preço atual (mantém comportamento atual)
    ultimo_periodo = dados.periodos[-1]

    #if _is_banco(dados.ticker):
    #    multiplos_ltm = calcular_multiplos_banco(dados, ultimo_periodo, usar_preco_atual=False)
    #elif _is_holding_seguros(dados.ticker):
    #    multiplos_ltm = calcular_multiplos_holding_seguros(dados, ultimo_periodo, usar_preco_atual=False)
    #elif _is_seguradora_operacional(dados.ticker):
    #    multiplos_ltm = calcular_multiplos_seguradora(dados, ultimo_periodo, usar_preco_atual=False)
    #else:
    #    multiplos_ltm = calcular_multiplos_periodo(dados, ultimo_periodo, usar_preco_atual=False)
    

    # LTM usa preço MAIS RECENTE disponível (usar_preco_atual=True)
    if _is_banco(dados.ticker):
        multiplos_ltm = calcular_multiplos_banco(dados, ultimo_periodo, usar_preco_atual=True)
    elif _is_holding_seguros(dados.ticker):
        multiplos_ltm = calcular_multiplos_holding_seguros(dados, ultimo_periodo, usar_preco_atual=True)
    elif _is_seguradora_operacional(dados.ticker):
        multiplos_ltm = calcular_multiplos_seguradora(dados, ultimo_periodo, usar_preco_atual=True)
    else:
        multiplos_ltm = calcular_multiplos_periodo(dados, ultimo_periodo, usar_preco_atual=True)

    

    # Informações de preço e ações utilizados (LTM)
    preco_atual, periodo_preco = _obter_preco_atual(dados)
    acoes_atual, periodo_acoes = _obter_acoes_atual(dados)

    return {
        "ticker": dados.ticker,
        "padrao_fiscal": {
            "tipo": dados.padrao_fiscal.tipo,
            "descricao": dados.padrao_fiscal.descricao,
            "trimestres_ltm": dados.padrao_fiscal.trimestres_ltm
        },
        "metadata": (
            MULTIPLOS_BANCOS_METADATA if _is_banco(dados.ticker)
            else MULTIPLOS_HOLDINGS_SEGUROS_METADATA if _is_holding_seguros(dados.ticker)
            else MULTIPLOS_SEGURADORAS_METADATA if _is_seguradora_operacional(dados.ticker)
            else MULTIPLOS_METADATA
        ),
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
        "erros": dados.erros
    }



# ======================================================================================
# PROCESSADOR PRINCIPAL
# ======================================================================================

def processar_ticker(ticker: str, salvar: bool = True) -> Tuple[bool, str, Optional[Dict]]:
    """Processa um ticker e calcula todos os múltiplos."""
    ticker_upper = ticker.upper().strip()
    
    # >>>>>> SEM EXCLUSÃO - AGORA SUPORTAMOS SEGURADORAS <<<<
    
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
    
    tipo_empresa = "BANCO" if _is_banco(ticker_upper) else "GERAL"
    n_multiplos = len(MULTIPLOS_BANCOS_METADATA) if _is_banco(ticker_upper) else len(MULTIPLOS_METADATA)
    
    msg = f"OK | {n_anos} anos | fiscal={padrao} | LTM={ultimo} | Preço=R${preco} | Tipo={tipo_empresa} | {n_multiplos} múltiplos"
    
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
    elif _is_holding_seguros(ticker):
        multiplos_codigos = list(MULTIPLOS_HOLDINGS_SEGUROS_METADATA.keys())
    elif _is_seguradora_operacional(ticker):
        multiplos_codigos = list(MULTIPLOS_SEGURADORAS_METADATA.keys())
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
        description="Calculadora de Múltiplos Financeiros"
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
    print(f">>> CALCULADORA DE MÚLTIPLOS FINANCEIROS <<<")
    print(f"{'='*70}")
    print(f"Modo: {args.modo} | Selecionadas: {len(df_sel)}")
    print(f"Empresas: 22 múltiplos | Bancos: 8 | Holdings Seguros: 10 | Seguradoras: 10")
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
                if "seguradora" in msg.lower() or "holding" in msg.lower():
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
    print(f"RESUMO: OK={ok_count} | SKIP(Seguradoras)={skip_count} | ERRO={err_count}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
