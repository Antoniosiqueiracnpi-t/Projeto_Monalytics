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

# CORREÇÃO v3.0: Mapeamento padrão de fatores UNIT
# Usado quando não é possível calcular o fator do arquivo de ações
FATOR_UNIT_PADRAO: Dict[str, int] = {
    "KLBN": 5,   # KLBN11 = 1 ON + 4 PN = 5 ações
    "BPAC": 3,   # BPAC11 = 1 ON + 2 PN = 3 ações
    "SANB": 2,   # SANB11 = 1 ON + 1 PN = 2 ações
    "TAEE": 2,   # TAEE11 = 1 ON + 1 PN = 2 ações
    "ALUP": 2,   # ALUP11 = 1 ON + 1 PN = 2 ações
    "ENGI": 2,   # ENGI11 = 1 ON + 1 PN = 2 ações
    "SAPR": 2,   # SAPR11 = 1 ON + 1 PN = 2 ações
    "AURE": 2,   # AURE11 = 1 ON + 1 PN = 2 ações
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


def _to_float_smart(x) -> float:
    """Converte string/objeto em float, tolerando formato pt-BR (1.234,56) e EN (1234.56)."""
    if x is None:
        return np.nan
    try:
        if isinstance(x, (int, float, np.integer, np.floating)):
            v = float(x)
            return v if np.isfinite(v) else np.nan
    except Exception:
        pass

    s = str(x).strip()
    if s == "" or s.lower() in {"nan", "none", "null", "-", "—"}:
        return np.nan
    s = s.replace(" ", "")

    # pt-BR: 1.234,56 -> 1234.56
    if "," in s:
        if "." in s:
            s = s.replace(".", "")
        s = s.replace(",", ".")

    s = re.sub(r"[^0-9eE\+\-\.]", "", s)

    try:
        v = float(s)
        return v if np.isfinite(v) else np.nan
    except Exception:
        return np.nan


def _series_to_numeric_smart(ser: pd.Series) -> pd.Series:
    return ser.apply(_to_float_smart)



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
    Retorna apenas colunas de período que contêm números válidos.

    ✅ Robustez: tolera formato pt-BR (vírgula decimal) e EN.
    """
    if df is None:
        return []

    candidatas = [c for c in df.columns if _parse_periodo(c)[0] > 0]
    validas: List[str] = []

    for c in candidatas:
        s = _series_to_numeric_smart(df[c])
        if s.notna().any():
            validas.append(c)

    return _ordenar_periodos(validas)

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
    Obtém preço no período.

    ✅ Suporta precos_trimestrais.csv em formato antigo (1 linha) e multi-classes (várias linhas com coluna Ticker).
    ✅ Prioriza linha "Ajustado" quando existir.
    ✅ Robustez pt-BR: aceita 1.234,56 / 1234.56.
    ✅ Importante: se ticker_preco for informado e não existir linha para ele, retorna NaN (sem fallback silencioso),
       evitando múltiplos idênticos entre classes por uso do "primeiro número" de outra classe.
    """
    if dados.precos is None or dados.precos.empty:
        return np.nan

    df = dados.precos
    if periodo not in df.columns:
        return np.nan

    # coluna ticker (multi-classes)
    col_ticker = None
    for c in ("Ticker", "ticker", "TICKER"):
        if c in df.columns:
            col_ticker = c
            break

    # coluna tipo de preço (para selecionar "Ajustado")
    col_tipo = None
    for c in ("Preço_Fechamento", "preco_fechamento", "PRECO_FECHAMENTO", "tipo_preco", "Tipo_Preco", "TIPO_PRECO", "nome"):
        if c in df.columns:
            col_tipo = c
            break

    df_use = df

    if col_ticker:
        alvo = (ticker_preco or dados.ticker or "")
        alvo = str(alvo).upper().strip().replace(".SA", "")
        ser_t = df[col_ticker].astype(str).str.upper().str.strip().str.replace(".SA", "", regex=False)
        df_use = df[ser_t.eq(alvo)]
        if df_use.empty:
            return np.nan

    if col_tipo and not df_use.empty:
        st = df_use[col_tipo].astype(str).str.upper()
        sub_aj = df_use[st.str.contains("AJUST", na=False)]
        if not sub_aj.empty:
            df_use = sub_aj

    s = _series_to_numeric_smart(df_use[periodo])
    if s.notna().any():
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


def _selecionar_ticker_preco_multi(dados: DadosEmpresa, raiz: str, sufixos: List[str]) -> str:
    """
    Seleciona um ticker existente no dataframe de preços (multi-classes) a partir de uma raiz (ex.: 'BPAC')
    e uma lista de sufixos preferenciais (ex.: ['3','4','5','6','7','8','11']).

    Retorna "" se não encontrar.
    """
    if dados.precos is None or dados.precos.empty:
        return ""

    df = dados.precos

    # Detectar coluna de ticker
    col_ticker = None
    for c in ["Ticker", "ticker", "TICKER"]:
        if c in df.columns:
            col_ticker = c
            break
    if not col_ticker:
        return ""

    tickers = df[col_ticker].astype(str).str.upper().str.strip().unique().tolist()
    raiz = str(raiz or "").upper().strip()
    if not raiz or len(raiz) < 4:
        return ""

    for suf in sufixos:
        suf = str(suf).upper().strip()
        if not suf:
            continue
        cand = f"{raiz}{suf}" if not suf.startswith(raiz) else suf
        if cand in tickers:
            return cand

    return ""





def _extrair_classe_ticker(ticker: str) -> str:
    """Extrai a classe numérica do ticker (ex.: KLBN11 -> '11', AURA33 -> '33')."""
    t = (ticker or "").upper().strip()
    m = re.match(r"^([A-Z]{4})(\d+)$", t)
    return m.group(2) if m else ""


def _classe_para_especie(classe: str) -> str:
    """
    Mapeia a classe do ticker para a espécie no acoes_historico.csv.

    - 3  -> ON
    - 4/5/6/7/8 -> PN (preferenciais e variações)
    - 11 -> UNIT
    - demais -> TOTAL (fallback)
    """
    c = str(classe or "").strip()
    if c == "3":
        return "ON"
    if c in {"4", "5", "6", "7", "8"}:
        return "PN"
    if c == "11":
        return "UNIT"
    return "TOTAL"


def _obter_acoes_unit(dados: DadosEmpresa, periodo: str) -> float:
    """Obtém quantidade de UNITS (se existir no acoes_historico.csv)."""
    # nomes comuns observados em bases: UNIT, UNT, UNITS
    for rotulo in ["UNIT", "UNITS", "UNT"]:
        v = _obter_acoes_especie(dados, rotulo, periodo)
        if np.isfinite(v) and v > 0:
            return float(v)
    return np.nan


def _calcular_fator_unit_pacote(dados: DadosEmpresa, periodo: str) -> int:
    """
    Calcula o fator do pacote da UNIT: quantas ações (ON+PN) correspondem a 1 UNIT.

    Regra:
      fator = (ações ON+PN) / (quantidade de UNIT)

    CORREÇÃO v3.0: Usa mapeamento FATOR_UNIT_PADRAO quando não consegue calcular.

    Retorna inteiro >= 1. Se não for possível calcular, usa mapeamento padrão ou retorna 1.
    """
    total_ex11 = _obter_acoes_total_ex11(dados, periodo)
    units = _obter_acoes_unit(dados, periodo)

    if np.isfinite(total_ex11) and total_ex11 > 0 and np.isfinite(units) and units > 0:
        f = total_ex11 / units
        # arredonda para inteiro se estiver "quase inteiro"
        f_int = int(round(f))
        if f_int >= 1 and abs(f - f_int) <= 0.15:
            return f_int
        # fallback: ainda assim garante >=1
        return max(1, int(round(f)))
    
    # CORREÇÃO v3.0: Usar mapeamento padrão quando não consegue calcular
    raiz = (dados.ticker or "").upper().strip()[:4]
    if raiz in FATOR_UNIT_PADRAO:
        return FATOR_UNIT_PADRAO[raiz]
    
    return 1


def _ajustar_acoes_para_ticker_preco(dados: DadosEmpresa, periodo: str, ticker_preco: Optional[str]) -> Tuple[float, str, int]:
    """
    Retorna (acoes_equivalentes, periodo_acoes_usado, fator_unit).

    Objetivo:
    - Se o ticker_preco for UNIT (classe 11), converte ações totais (ON+PN) para "unidades de UNIT"
      (ou usa a linha UNIT do acoes_historico.csv se existir).
    - Caso contrário, mantém a regra do projeto (ON+PN sempre que possível).

    Isso garante que múltiplos por ação (EPS, VPA, dividendos/ação, etc.) fiquem consistentes com o preço
    utilizado (por exemplo, UNIT tem preço por "pacote", então precisa de ações equivalentes em UNIT).
    """
    ticker_preco = (ticker_preco or dados.ticker or "").upper().strip()
    classe = _extrair_classe_ticker(ticker_preco)

    # período usado para ações (imputação robusta já existe em _obter_acoes_especie/_obter_acoes_total_ex11)
    periodo_use = periodo

    if classe == "11":
        # tenta usar a própria linha de UNIT se existir
        a_unit = _obter_acoes_unit(dados, periodo_use)
        if np.isfinite(a_unit) and a_unit > 0:
            return float(a_unit), _encontrar_periodo_imputacao(dados.acoes, periodo_use) or periodo_use, _calcular_fator_unit_pacote(dados, periodo_use)

        # fallback: converte ON+PN em "quantidade de UNIT"
        total_ex11 = _obter_acoes_total_ex11(dados, periodo_use)
        fator = _calcular_fator_unit_pacote(dados, periodo_use)
        if np.isfinite(total_ex11) and total_ex11 > 0 and fator >= 1:
            return float(total_ex11 / fator), _encontrar_periodo_imputacao(dados.acoes, periodo_use) or periodo_use, fator

        return np.nan, _encontrar_periodo_imputacao(dados.acoes, periodo_use) or periodo_use, fator

    # não-unit: regra geral (ON+PN)
    a = _obter_acoes(dados, periodo_use)
    return float(a) if np.isfinite(a) else np.nan, _encontrar_periodo_imputacao(dados.acoes, periodo_use) or periodo_use, 1


def _listar_tickers_saida_multiclasse(dados: DadosEmpresa, ticker_seed: str) -> List[str]:
    """
    Lista tickers (com classe) disponíveis no arquivo de preços para a mesma empresa (mesma raiz de 4 letras).

    Ex.: KLBN11 -> ['KLBN3','KLBN4','KLBN11'] (se existirem no precos_trimestrais.csv).
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
        # arquivo antigo (uma linha sem coluna de ticker)
        return [seed]

    tickers = (
        df[col_ticker]
        .astype(str)
        .str.upper()
        .str.strip()
        .unique()
        .tolist()
    )
    tickers = [t for t in tickers if t.startswith(raiz)]
    # ordenação: 3,4,5..,11 por preferência
    def key(t: str):
        c = _extrair_classe_ticker(t)
        # peso menor = vem antes
        if c == "3":
            w = 10
        elif c in {"4", "5", "6", "7", "8"}:
            w = 20 + int(c)
        elif c == "11":
            w = 90
        else:
            w = 50 + (int(c) if c.isdigit() else 99)
        return (w, t)

    out = sorted(set(tickers), key=key)
    if seed and seed not in out:
        out.append(seed)
    return out


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

    ✅ Robustez: tolera formato pt-BR/EN.
    ✅ Usa imputação de período para evitar cair em colunas inexistentes.
    """
    if dados.acoes is None or dados.acoes.empty:
        return np.nan

    df = dados.acoes
    col_especie = _detectar_coluna_especie(df)
    if not col_especie:
        return np.nan

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

    val = _to_float_smart(df.loc[mask, periodo_busca].iloc[0])
    return float(val) if np.isfinite(val) else np.nan

def _obter_acoes_total_ex11(dados: DadosEmpresa, periodo: str) -> float:
    """
    Retorna o total de ações considerando APENAS classes 3 e 4 (ON+PN), ignorando UNIT (11),
    sempre que possível.

    ✅ Robustez: tolera formato pt-BR/EN.
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
            val = _to_float_smart(df.loc[mask, periodo_busca].iloc[0])
            return float(val) if np.isfinite(val) else np.nan

    s = _series_to_numeric_smart(df[periodo_busca])
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



def _calcular_market_cap(dados: DadosEmpresa, periodo: str, ticker_preco: Optional[str] = None) -> float:
    """
    Calcula Market Cap (R$ mil) para um período.

    Modos:
    - ticker_preco=None: mantém a regra "empresa" (VM = p_ON*a_ON + p_PN*a_PN), usando preços do PERÍODO.
    - ticker_preco informada:
        * classe 3  -> VM = preço(ticker_preco) × ações ON
        * classe 4/5/6/7/8 -> VM = preço(ticker_preco) × ações PN
        * classe 11 (UNIT) -> VM = preço(ticker_preco) × ações equivalentes em UNIT
        * demais -> VM = preço(ticker_preco) × ações ON+PN (fallback)

    Observação:
    - Ações são obtidas com imputação via _obter_acoes_especie/_obter_acoes_total_ex11.
    - Preço do período usa a coluna do próprio período; se faltar, cai no último preço disponível.
    """
    periodo = str(periodo or "").upper().strip()
    if not periodo:
        return np.nan

    # helper: preço do período com fallback robusto
    def preco_periodo(t: Optional[str]) -> float:
        p = _obter_preco(dados, periodo, ticker_preco=t)
        if np.isfinite(p) and p > 0:
            return float(p)
        p2, _ = _obter_preco_atual(dados, ticker_preco=t)
        return float(p2) if np.isfinite(p2) else np.nan

    # modo classe específica
    if ticker_preco:
        tpx = str(ticker_preco).upper().strip()
        classe = _extrair_classe_ticker(tpx)
        p = preco_periodo(tpx)

        if not (np.isfinite(p) and p > 0):
            return np.nan

        if classe == "11":
            a_equiv, _, _ = _ajustar_acoes_para_ticker_preco(dados, periodo, tpx)
            if np.isfinite(a_equiv) and a_equiv > 0:
                return float((p * a_equiv) / 1000.0)
            return np.nan

        if classe == "3":
            a = _obter_acoes_especie(dados, "ON", periodo)
        elif classe in {"4", "5", "6", "7", "8"}:
            a = _obter_acoes_especie(dados, "PN", periodo)
        else:
            a = _obter_acoes_total_ex11(dados, periodo)

        if np.isfinite(a) and a > 0:
            return float((p * a) / 1000.0)
        return np.nan

    # modo empresa (ON + PN)
    ticker = (dados.ticker or "").upper().strip()
    if len(ticker) < 4:
        return np.nan

    raiz = ticker[:4]
    ticker_on = _selecionar_ticker_preco_multi(dados, raiz, ["3"])
    ticker_pn = _selecionar_ticker_preco_multi(dados, raiz, ["4", "5", "6", "7", "8"])

    p_on = preco_periodo(ticker_on) if ticker_on else np.nan
    p_pn = preco_periodo(ticker_pn) if ticker_pn else np.nan

    a_on = _obter_acoes_especie(dados, "ON", periodo)
    a_pn = _obter_acoes_especie(dados, "PN", periodo)

    parts: List[float] = []
    if np.isfinite(p_on) and p_on > 0 and np.isfinite(a_on) and a_on > 0:
        parts.append(p_on * a_on)
    if np.isfinite(p_pn) and p_pn > 0 and np.isfinite(a_pn) and a_pn > 0:
        parts.append(p_pn * a_pn)

    if parts:
        return float(sum(parts) / 1000.0)

    # fallback compatível: total × preço do ticker base
    p = preco_periodo(None)
    a = _obter_acoes_total_ex11(dados, periodo)
    if np.isfinite(p) and p > 0 and np.isfinite(a) and a > 0:
        return float((p * a) / 1000.0)

    return np.nan


def _calcular_market_cap_atual(dados: DadosEmpresa, ticker_preco: Optional[str] = None) -> float:
    """
    Calcula Valor de Mercado (Market Cap) atual em R$ mil.

    Modos:
    - ticker_preco=None: VM da empresa = (Preço_ON × Ações_ON) + (Preço_PN × Ações_PN)
    - ticker_preco informada:
        * classe 3  -> VM = preço(ticker_preco) × ações ON
        * classe 4/5/6/7/8 -> VM = preço(ticker_preco) × ações PN
        * classe 11 (UNIT) -> VM = preço(ticker_preco) × ações equivalentes em UNIT
        * demais -> VM = preço(ticker_preco) × ações ON+PN (fallback)

    Observação: mantém compatibilidade quando ticker_preco não é informada.
    """
    # modo classe específica
    if ticker_preco:
        tpx = str(ticker_preco).upper().strip()
        classe = _extrair_classe_ticker(tpx)
        p, periodo_p = _obter_preco_atual(dados, ticker_preco=tpx)
        if not (np.isfinite(p) and p > 0):
            return np.nan

        if classe == "11":
            a_equiv, _, _ = _ajustar_acoes_para_ticker_preco(dados, periodo_p or "9999T4", tpx)
            if np.isfinite(a_equiv) and a_equiv > 0:
                return float((p * a_equiv) / 1000.0)
            return np.nan

        if classe == "3":
            a = _obter_acoes_especie(dados, "ON", periodo_p or "9999T4")
        elif classe in {"4", "5", "6", "7", "8"}:
            a = _obter_acoes_especie(dados, "PN", periodo_p or "9999T4")
        else:
            a = _obter_acoes_total_ex11(dados, periodo_p or "9999T4")

        if np.isfinite(a) and a > 0:
            return float((p * a) / 1000.0)
        return np.nan

    # modo empresa (ON + PN) - comportamento original
    ticker = (dados.ticker or "").upper().strip()
    if len(ticker) < 4:
        return np.nan

    raiz = ticker[:4]

    ticker_on = _selecionar_ticker_preco_multi(dados, raiz, ["3"])
    ticker_pn = _selecionar_ticker_preco_multi(dados, raiz, ["4", "5", "6", "7", "8"])

    p_on, periodo_on = _obter_preco_atual(dados, ticker_preco=ticker_on) if ticker_on else (np.nan, "")
    p_pn, periodo_pn = _obter_preco_atual(dados, ticker_preco=ticker_pn) if ticker_pn else (np.nan, "")

    # referência de período para ações (usa o mais recente entre preços disponíveis)
    periodo_ref = ""
    if dados.precos is not None and not dados.precos.empty:
        col_periodos = _get_colunas_numericas_validas(dados.precos)
        if col_periodos:
            periodo_ref = col_periodos[-1]

    a_on = _obter_acoes_especie(dados, "ON", periodo_ref or "9999T4")
    a_pn = _obter_acoes_especie(dados, "PN", periodo_ref or "9999T4")

    parts: List[float] = []
    if np.isfinite(p_on) and p_on > 0 and np.isfinite(a_on) and a_on > 0:
        parts.append(p_on * a_on)
    if np.isfinite(p_pn) and p_pn > 0 and np.isfinite(a_pn) and a_pn > 0:
        parts.append(p_pn * a_pn)

    if parts:
        return float(sum(parts) / 1000.0)

    # Fallback compatível
    preco, periodo_p = _obter_preco_atual(dados)
    acoes = _obter_acoes(dados, periodo_ref or "9999T4")
    if np.isfinite(preco) and preco > 0 and np.isfinite(acoes) and acoes > 0:
        return float((preco * acoes) / 1000.0)

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
    Calcula D&A (Depreciação e Amortização) de um período de forma **robusta**.

    Problema comum (que derruba EV/EBITDA): usar agregadores amplos de DFC (ex.: 6.01.01)
    como se fossem D&A. Em muitas companhias, 6.01.01 representa "Ajustes" (com vários itens),
    o que superestima o EBITDA.

    Regra (universal):
    1) Prioriza código sintético 6.01.DA (se existir).
    2) Depois tenta códigos específicos de D&A (6.01.01.02 e 6.01.01.01).
    3) Se não encontrar, NÃO usa o agregador 6.01.01 (evita superestimar); retorna NaN.
       Nesse caso, o EBITDA do período vira uma aproximação conservadora (= EBIT).
    """
    if dados.dfc is None or periodo not in dados.dfc.columns:
        return np.nan

    dfc = dados.dfc
    if 'cd_conta' not in dfc.columns:
        return np.nan

    def _val_exato(cd: str) -> float:
        mask = (dfc['cd_conta'] == cd)
        if mask.any():
            v = pd.to_numeric(dfc.loc[mask, periodo], errors='coerce').values[0]
            return float(v) if pd.notna(v) else np.nan
        return np.nan

    # 1) Preferência máxima: código sintético gerado pelo seu pipeline (quando existir)
    val = _val_exato("6.01.DA")
    if np.isfinite(val):
        return abs(val)

    # 2) Preferência: códigos específicos de D&A (podem ter subcontas; aqui permitimos soma do ramo específico)
    for cd in ("6.01.01.02", "6.01.01.01"):
        v = _extrair_valor_conta(dfc, cd, periodo)
        if np.isfinite(v):
            return abs(v)

    # 3) Fallback: tentar encontrar qualquer subconta típica de D&A sob 6.01.01.*
    # (sem recorrer ao agregador 6.01.01, que costuma englobar diversos "Ajustes")
    try:
        ser_cd = dfc['cd_conta'].astype(str)
    except Exception:
        return np.nan

    # Preferir padrões clássicos: ...01 ou ...02 logo abaixo de 6.01.01
    candidatos = dfc[ser_cd.str.match(r"^6\.01\.01\.(01|02)(\.|$)", na=False)]
    if not candidatos.empty:
        vals = pd.to_numeric(candidatos[periodo], errors='coerce')
        soma = float(np.nansum(np.abs(vals.values)))
        return soma if np.isfinite(soma) and soma > 0 else np.nan

    # Não usar 6.01.01 (agregador amplo) para não superestimar EBITDA
    return np.nan

def _calcular_ebitda_periodo(dados: DadosEmpresa, periodo: str) -> float:
    """
    Calcula EBITDA de um período.

    Regra: EBITDA = EBIT + D&A (D&A robusto via DFC; se D&A indisponível, aproxima por EBIT).
    Isso evita superestimar EBITDA quando o DFC traz um agregador amplo de ajustes.
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


def _calcular_dpa_ltm(dados: DadosEmpresa, periodo_fim: str) -> float:
    """
    CORREÇÃO v3.0: Calcula DPA LTM (Dividendo por Ação) somando diretamente dos 4 trimestres.
    
    Esta função evita as conversões DPA → Total → DPA que causavam erros.
    
    Exemplo: Se periodo_fim = "2025T3"
    - LTM = DPA(2024T4) + DPA(2025T1) + DPA(2025T2) + DPA(2025T3)
    
    Returns:
        DPA LTM em R$/ação (soma direta, sem conversões)
    """
    if dados.dividendos is None:
        return np.nan
    
    # Parsear período fim
    ano_fim, tri_fim = _parse_periodo(periodo_fim)
    if ano_fim == 0:
        return np.nan
    
    tri_num = {'T1': 1, 'T2': 2, 'T3': 3, 'T4': 4}.get(tri_fim, 0)
    if tri_num == 0:
        return np.nan
    
    # Obter colunas de dividendos disponíveis
    colunas_div = [c for c in dados.dividendos.columns if _parse_periodo(c)[0] > 0]
    
    # Construir lista de 4 períodos para LTM
    periodos_12m = []
    
    # Ano atual: T1 até T_fim
    for t in range(1, tri_num + 1):
        periodos_12m.append(f"{ano_fim}T{t}")
    
    # Ano anterior: T(tri_fim + 1) até T4
    for t in range(tri_num + 1, 5):
        periodos_12m.append(f"{ano_fim - 1}T{t}")
    
    # Somar DPA diretamente (sem converter para total)
    soma_dpa = 0.0
    
    for p in periodos_12m:
        if p in colunas_div:
            vals = pd.to_numeric(dados.dividendos[p], errors='coerce').dropna()
            if len(vals) > 0:
                dpa = float(vals.iloc[0])
                if np.isfinite(dpa) and dpa >= 0:
                    soma_dpa += dpa
    
    return soma_dpa if soma_dpa > 0 else np.nan

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


def _obter_preco_ultimo_trimestre_ano(
    dados: DadosEmpresa,
    periodo_referencia: str,
    ticker_preco: Optional[str] = None
) -> Tuple[float, str]:
    """
    Obtém o preço do último trimestre disponível do ANO do período de referência, para o ticker escolhido.

    Ex.: periodo_referencia='2024T4' -> tenta 2024T4, depois 2024T3, 2024T2, 2024T1.
    Se não encontrar, cai no último preço disponível.

    Args:
        dados: Dados da empresa
        periodo_referencia: Ex: '2024T4' (apenas o ano é usado)
        ticker_preco: Ticker cujo preço deve ser utilizado (ex.: KLBN3, KLBN4, KLBN11)
    """
    # Extrair ano do período
    try:
        ano_ref = int(str(periodo_referencia)[:4])
    except Exception:
        return _obter_preco_atual(dados, ticker_preco=ticker_preco)

    # Tentar períodos do ano em ordem decrescente: T4 → T3 → T2 → T1
    for tri in ['T4', 'T3', 'T2', 'T1']:
        periodo_teste = f"{ano_ref}{tri}"
        preco = _obter_preco(dados, periodo_teste, ticker_preco=ticker_preco)
        if np.isfinite(preco) and preco > 0:
            return float(preco), periodo_teste

    # Se nenhum período do ano existe, busca último disponível
    return _obter_preco_atual(dados, ticker_preco=ticker_preco)


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

def calcular_multiplos_periodo(dados: DadosEmpresa, periodo: str, usar_preco_atual: bool = True, ticker_preco: Optional[str] = None) -> Dict[str, Optional[float]]:
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
        market_cap = _calcular_market_cap_atual(dados, ticker_preco=ticker_preco)
    else:
        market_cap = _calcular_market_cap(dados, periodo, ticker_preco=ticker_preco)

    # ✅ Expor Valor de Mercado (R$ mil)
    resultado["VALOR_MERCADO"] = _normalizar_valor(market_cap, decimals=2)
    
    ev = _calcular_ev(dados, periodo, market_cap)

    # ==================== LUCRO LÍQUIDO LTM (para PAYOUT) ====================
    
    ll_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["lucro_liquido"], periodo)
    
    # ==================== VALUATION ====================
    
    # P/L = Preço / EPS (Lucro Líquido LTM / Ações)
    # ✅ Alinha com o padrão clássico (Investidor10): EPS = Lucro Líquido LTM / Ações (ON+PN quando possível)
    acoes_ref, _periodo_acoes_ref, _fator_unit = _ajustar_acoes_para_ticker_preco(dados, periodo, ticker_preco)

    # EPS LTM:
    # ✅ Preferir "Lucro por Ação (3.99)" quando existir, pois já embute a média ponderada de ações
    # e tende a bater melhor com StatusInvest/Investidor10.
    eps_ltm = _calcular_ltm(dados, dados.dre, "3.99", periodo)
    if not (np.isfinite(eps_ltm) and eps_ltm != 0):
        eps_ltm = (ll_ltm * 1000.0) / acoes_ref if np.isfinite(ll_ltm) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan

    if usar_preco_atual:
        preco_pl, periodo_preco_pl = _obter_preco_atual(dados, ticker_preco=ticker_preco)
    else:
        preco_pl, periodo_preco_pl = _obter_preco_ultimo_trimestre_ano(dados, periodo, ticker_preco=ticker_preco)

    resultado["P_L"] = _normalizar_valor(_safe_divide(preco_pl, eps_ltm))

    # Obter Patrimônio Líquido (usado em P/VPA, ROIC, Dív.Líq/PL)
    pl = _obter_valor_pontual(dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)

    # P/VPA = Preço / VPA (PL / Ações)
    vpa = (pl * 1000.0) / acoes_ref if np.isfinite(pl) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan
    resultado["P_VPA"] = _normalizar_valor(_safe_divide(preco_pl, vpa))
    
    ebitda_ltm = _calcular_ebitda_ltm(dados, periodo)
    resultado["EV_EBITDA"] = _normalizar_valor(_safe_divide(ev, ebitda_ltm))
    
    ebit_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["ebit"], periodo)
    resultado["EV_EBIT"] = _normalizar_valor(_safe_divide(ev, ebit_ltm))
    
    receita_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["receita"], periodo)
    resultado["EV_RECEITA"] = _normalizar_valor(_safe_divide(ev, receita_ltm))
    
    # ==================== DIVIDENDOS ====================
    
    # CORREÇÃO v3.0: Usar _calcular_dpa_ltm que soma DPA diretamente
    dpa_ltm = _calcular_dpa_ltm(dados, periodo)
    
    # Dividend Yield (padrão clássico) = (DPA LTM / Preço) × 100
    resultado["DY"] = _normalizar_valor(_safe_divide(dpa_ltm, preco_pl) * 100)

    # Payout (padrão clássico) = DPA / LPA × 100
    resultado["PAYOUT"] = _normalizar_valor(_safe_divide(dpa_ltm, eps_ltm) * 100)
    
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

def calcular_multiplos_banco(dados: DadosEmpresa, periodo: str, usar_preco_atual: bool = True, ticker_preco: Optional[str] = None) -> Dict[str, Optional[float]]:
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
        market_cap = _calcular_market_cap_atual(dados, ticker_preco=ticker_preco)
    else:
        market_cap = _calcular_market_cap(dados, periodo, ticker_preco=ticker_preco)


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
    
    # CORREÇÃO v3.0: Usar _calcular_dpa_ltm que soma DPA diretamente
    dpa_ltm = _calcular_dpa_ltm(dados, periodo)
    
    # ==================== VALUATION (4 MÚLTIPLOS) ====================
    
    # P/L = Preço / EPS (Lucro Líquido LTM / Ações)
    acoes_ref, _periodo_acoes_ref, _fator_unit = _ajustar_acoes_para_ticker_preco(dados, periodo, ticker_preco)
    eps_ltm = (ll_ltm * 1000.0) / acoes_ref if np.isfinite(ll_ltm) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan

    if usar_preco_atual:
        preco_pl, periodo_preco_pl = _obter_preco_atual(dados, ticker_preco=ticker_preco)
    else:
        preco_pl, periodo_preco_pl = _obter_preco_ultimo_trimestre_ano(dados, periodo, ticker_preco=ticker_preco)

    resultado["P_L"] = _normalizar_valor(_safe_divide(preco_pl, eps_ltm))

    # Patrimônio Líquido - Código detectado automaticamente (2.07 ou 2.08)
    pl = _obter_valor_pontual(dados.bpp, pl_code, periodo)
    pl_medio = _obter_valor_medio(dados, dados.bpp, pl_code, periodo)

    # P/VPA = Preço / VPA (PL / Ações)
    vpa = (pl * 1000.0) / acoes_ref if np.isfinite(pl) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan
    resultado["P_VPA"] = _normalizar_valor(_safe_divide(preco_pl, vpa))
    
    # Dividend Yield (padrão clássico) = (DPA LTM / Preço) × 100
    resultado["DY"] = _normalizar_valor(_safe_divide(dpa_ltm, preco_pl) * 100)

    # Payout (padrão clássico) = DPA / EPS × 100
    resultado["PAYOUT"] = _normalizar_valor(_safe_divide(dpa_ltm, eps_ltm) * 100)
    
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


def calcular_multiplos_holding_seguros(dados: DadosEmpresa, periodo: str, usar_preco_atual: bool = True, ticker_preco: Optional[str] = None) -> Dict[str, Optional[float]]:
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
        market_cap = _calcular_market_cap_atual(dados, ticker_preco=ticker_preco)
    else:
        market_cap = _calcular_market_cap(dados, periodo, ticker_preco=ticker_preco)


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
    
    # CORREÇÃO v3.0: Usar _calcular_dpa_ltm que soma DPA diretamente
    dpa_ltm = _calcular_dpa_ltm(dados, periodo)
    
    # ==================== VALUATION (4 MÚLTIPLOS) ====================
    
    # P/L = Preço / EPS (Lucro Líquido LTM / Ações)
    acoes_ref, _periodo_acoes_ref, _fator_unit = _ajustar_acoes_para_ticker_preco(dados, periodo, ticker_preco)
    eps_ltm = (ll_ltm * 1000.0) / acoes_ref if np.isfinite(ll_ltm) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan

    if usar_preco_atual:
        preco_pl, periodo_preco_pl = _obter_preco_atual(dados, ticker_preco=ticker_preco)
    else:
        preco_pl, periodo_preco_pl = _obter_preco_ultimo_trimestre_ano(dados, periodo, ticker_preco=ticker_preco)

    resultado["P_L"] = _normalizar_valor(_safe_divide(preco_pl, eps_ltm))

    # Patrimônio Líquido - Código detectado automaticamente (2.07 ou 2.08)
    pl = _obter_valor_pontual(dados.bpp, pl_code, periodo)
    pl_medio = _obter_valor_medio(dados, dados.bpp, pl_code, periodo)

    # P/VPA = Preço / VPA (PL / Ações)
    vpa = (pl * 1000.0) / acoes_ref if np.isfinite(pl) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan
    resultado["P_VPA"] = _normalizar_valor(_safe_divide(preco_pl, vpa))
    
    # Dividend Yield (padrão clássico) = (DPA LTM / Preço) × 100
    resultado["DY"] = _normalizar_valor(_safe_divide(dpa_ltm, preco_pl) * 100)

    # Payout (padrão clássico) = DPA / EPS × 100
    resultado["PAYOUT"] = _normalizar_valor(_safe_divide(dpa_ltm, eps_ltm) * 100)
    
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


def calcular_multiplos_seguradora(dados: DadosEmpresa, periodo: str, usar_preco_atual: bool = True, ticker_preco: Optional[str] = None) -> Dict[str, Optional[float]]:
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
        market_cap = _calcular_market_cap_atual(dados, ticker_preco=ticker_preco)
    else:
        market_cap = _calcular_market_cap(dados, periodo, ticker_preco=ticker_preco)


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
    
    # CORREÇÃO v3.0: Usar _calcular_dpa_ltm que soma DPA diretamente
    dpa_ltm = _calcular_dpa_ltm(dados, periodo)
    
    # ==================== VALUATION (4 MÚLTIPLOS) ====================
    
    # P/L = Preço / EPS (Lucro Líquido LTM / Ações)
    acoes_ref, _periodo_acoes_ref, _fator_unit = _ajustar_acoes_para_ticker_preco(dados, periodo, ticker_preco)
    eps_ltm = (ll_ltm * 1000.0) / acoes_ref if np.isfinite(ll_ltm) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan

    if usar_preco_atual:
        preco_pl, periodo_preco_pl = _obter_preco_atual(dados, ticker_preco=ticker_preco)
    else:
        preco_pl, periodo_preco_pl = _obter_preco_ultimo_trimestre_ano(dados, periodo, ticker_preco=ticker_preco)

    resultado["P_L"] = _normalizar_valor(_safe_divide(preco_pl, eps_ltm))

    # ✅ ADICIONAR: Obter PL (usado em P/VPA, ROE, ROA, PL/Ativos)
    pl = _obter_valor_pontual(dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)
    pl_medio = _obter_valor_medio(dados, dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)

    # P/VPA = Preço / VPA (PL / Ações)
    vpa = (pl * 1000.0) / acoes_ref if np.isfinite(pl) and np.isfinite(acoes_ref) and acoes_ref > 0 else np.nan
    resultado["P_VPA"] = _normalizar_valor(_safe_divide(preco_pl, vpa))
    
    # Dividend Yield (padrão clássico) = (DPA LTM / Preço) × 100
    resultado["DY"] = _normalizar_valor(_safe_divide(dpa_ltm, preco_pl) * 100)

    # Payout (padrão clássico) = DPA / EPS × 100
    resultado["PAYOUT"] = _normalizar_valor(_safe_divide(dpa_ltm, eps_ltm) * 100)
    
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


def gerar_historico_anualizado(dados: DadosEmpresa, ticker_preco: Optional[str] = None, ticker_saida: Optional[str] = None) -> Dict[str, Any]:
    """Gera histórico de múltiplos anualizado."""
    if not dados.periodos or dados.padrao_fiscal is None:
        return {"erro": "Dados insuficientes", "ticker": dados.ticker}

    # Ticker efetivo de saída (novo padrão: arquivos por classe)
    ticker_out = (ticker_saida or getattr(dados, "ticker", "") or "").upper().strip()

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

        # ✅ CORREÇÃO APLICADA: Propagar ticker_preco para todas as funções de cálculo
        # Determinar qual função de cálculo usar (mantém a lógica existente)
        if _is_banco(dados.ticker):
            multiplos = calcular_multiplos_banco(dados, periodo_referencia, usar_preco_atual=usar_preco_atual_hist, ticker_preco=ticker_preco)
        elif _is_holding_seguros(dados.ticker):
            multiplos = calcular_multiplos_holding_seguros(dados, periodo_referencia, usar_preco_atual=usar_preco_atual_hist, ticker_preco=ticker_preco)
        elif _is_seguradora_operacional(dados.ticker):
            multiplos = calcular_multiplos_seguradora(dados, periodo_referencia, usar_preco_atual=usar_preco_atual_hist, ticker_preco=ticker_preco)
        else:
            multiplos = calcular_multiplos_periodo(dados, periodo_referencia, usar_preco_atual=usar_preco_atual_hist, ticker_preco=ticker_preco)

        historico_anual[ano] = {
            "periodo_referencia": periodo_referencia,
            "multiplos": multiplos
        }

    # LTM: Sempre usar último período disponível com preço atual (mantém comportamento atual)
    ultimo_periodo = dados.periodos[-1]

    # ✅ CORREÇÃO APLICADA: Propagar ticker_preco para todas as funções de cálculo do LTM
    # LTM usa preço MAIS RECENTE disponível (usar_preco_atual=True)
    if _is_banco(dados.ticker):
        multiplos_ltm = calcular_multiplos_banco(dados, ultimo_periodo, usar_preco_atual=True, ticker_preco=ticker_preco)
    elif _is_holding_seguros(dados.ticker):
        multiplos_ltm = calcular_multiplos_holding_seguros(dados, ultimo_periodo, usar_preco_atual=True, ticker_preco=ticker_preco)
    elif _is_seguradora_operacional(dados.ticker):
        multiplos_ltm = calcular_multiplos_seguradora(dados, ultimo_periodo, usar_preco_atual=True, ticker_preco=ticker_preco)
    else:
        multiplos_ltm = calcular_multiplos_periodo(dados, ultimo_periodo, usar_preco_atual=True, ticker_preco=ticker_preco)    

    # Informações de preço e ações utilizados (LTM)
    preco_atual, periodo_preco = _obter_preco_atual(dados, ticker_preco=ticker_preco)
    acoes_atual, periodo_acoes = _obter_acoes_atual(dados)
    # Ajustar ações ao ticker de preço (ex.: UNIT -> quantidade de UNIT)
    if periodo_acoes:
        acoes_eq, _, _ = _ajustar_acoes_para_ticker_preco(dados, periodo_acoes, ticker_preco)
        if np.isfinite(acoes_eq) and acoes_eq > 0:
            acoes_atual = acoes_eq

    return {
        "ticker": ticker_out,
        "ticker_preco": (ticker_preco or ticker_out).upper().strip(),
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
    """
    Processa um ticker e gera múltiplos.

    NOVO PADRÃO (multi-classes):
    - Para empresas com mais de uma classe disponível no precos_trimestrais.csv, gera arquivos por classe:
        multiplos_<TICKER>.csv
        multiplos_<TICKER>.js

      Ex.: KLBN -> multiplos_KLBN3.*, multiplos_KLBN4.*, multiplos_KLBN11.*

    - Para UNIT (classe 11), ajusta a quantidade de ações para equivaler a "quantidade de UNIT"
      (UNIT = pacote de ações ON+PN), usando o fator derivado do acoes_historico.csv quando possível.

    Retorna:
        (sucesso, mensagem, resultado_seed)
    """
    ticker_upper = (ticker or "").upper().strip()
    if not ticker_upper:
        return False, "Ticker vazio.", None

    try:
        dados = carregar_dados_empresa(ticker_upper)

        if not dados.periodos:
            return False, "Nenhum período encontrado nos dados.", None

        pasta = get_pasta_balanco(ticker_upper)

        # lista de saídas por classe disponível
        tickers_saida = _listar_tickers_saida_multiclasse(dados, ticker_upper)
        if not tickers_saida:
            tickers_saida = [ticker_upper]

        # gera sempre por classe (novo padrão)
        resultado_seed: Optional[Dict] = None

        for t_out in tickers_saida:
            resultado = gerar_historico_anualizado(dados, ticker_preco=t_out, ticker_saida=t_out)
            if resultado_seed is None and t_out == ticker_upper:
                resultado_seed = resultado

            if salvar:
                js_path = pasta / f"multiplos_{t_out}.js"
                csv_path = pasta / f"multiplos_{t_out}.csv"

                _salvar_js_historico(resultado, js_path, ticker=t_out)
                _salvar_csv_historico(resultado, csv_path)

        if resultado_seed is None:
            # se o seed não estava na lista, usa o primeiro
            resultado_seed = gerar_historico_anualizado(dados, ticker_preco=tickers_saida[0], ticker_saida=tickers_saida[0])

        msg = f"OK - gerados {len(tickers_saida)} arquivo(s): " + ", ".join(tickers_saida)
        return True, msg, resultado_seed

    except Exception as e:
        return False, f"ERRO - {str(e)}", None


def _salvar_csv_historico(resultado: Dict, path: Path):
    """Salva histórico em formato CSV (por classe)."""
    historico = resultado.get("historico_anual", {})
    ltm_data = resultado.get("ltm", {})
    metadata = resultado.get("metadata", {})
    ticker = resultado.get("ticker", "")
    ticker_preco = resultado.get("ticker_preco", "")

    if not historico:
        raise ValueError(f"{ticker}: histórico anual vazio (ticker_preco={ticker_preco})")

    anos = sorted(historico.keys())

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

    # Validação: não aceitar CSV "todo vazio"
    cols_val = [c for c in df.columns if re.fullmatch(r"\d{4}", str(c)) or str(c).upper() == "LTM"]
    if cols_val:
        any_value = df[cols_val].apply(pd.to_numeric, errors="coerce").notna().any().any()
        if not any_value:
            raise ValueError(f"{ticker}: CSV sem valores numéricos (ticker_preco={ticker_preco}). "
                             "Cheque precos_trimestrais.csv / acoes_historico.csv e o filtro por ticker/classe.")

    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")

def _salvar_js_historico(resultado: Dict[str, Any], output_path: Path, ticker: Optional[str] = None) -> None:
    """
    Salva o resultado como JavaScript (para consumo direto via <script src=...>).

    Padrão:
      window.MONALYTICS.multiplos["TICKER"] = {...};

    Args:
        resultado: dict do histórico (mesma estrutura do JSON)
        output_path: caminho .js
        ticker: chave do dicionário (default: resultado['ticker'])
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        t = (ticker or resultado.get("ticker") or "").upper().strip() or "TICKER"

        payload = json.dumps(resultado, ensure_ascii=False, indent=2)

        js = (
            "// Arquivo gerado automaticamente por calcular_multiplos.py\n"
            "(function(){\n"
            "  window.MONALYTICS = window.MONALYTICS || {};\n"
            "  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};\n"
            f"  window.MONALYTICS.multiplos[{json.dumps(t)}] = {payload};\n"
            "})();\n"
        )
        output_path.write_text(js, encoding="utf-8")
    except Exception as e:
        print(f"⚠️ Erro ao salvar JS em {output_path}: {e}")


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
    print(f"Saída: balancos/<TICKER>/multiplos_<TICKER>.js + multiplos_<TICKER>.csv (por classe)")
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
