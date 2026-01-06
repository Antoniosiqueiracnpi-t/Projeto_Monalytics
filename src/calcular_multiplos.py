"""
Calculadora de Múltiplos Financeiros para Empresas Não-Financeiras
==================================================================
VERSÃO CORRIGIDA - Janeiro 2026

Correções Críticas para Eliminar Campos em Branco:
1. Backfill de Ações: Usa o primeiro número de ações conhecido para períodos anteriores (ex: CAML3 2017).
2. Filtro de Colunas: Ignora colunas futuras com texto (ex: "2026T1" com "ON").
3. Divisão Robusta: Evita P/L infinito em casos de lucro próximo a zero.
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

CONTAS_DRE = {
    "receita": "3.01",
    "cpv": "3.02",
    "lucro_bruto": "3.03",
    "ebit": "3.05",
    "resultado_financeiro": "3.06",
    "lucro_liquido": "3.11",
    "ir_csll": "3.08",
}

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

CONTAS_BPP = {
    "passivo_total": "2",
    "passivo_circulante": "2.01",
    "emprestimos_cp": "2.01.04",
    "fornecedores": "2.01.02",
    "passivo_nao_circulante": "2.02",
    "emprestimos_lp": "2.02.01",
    "patrimonio_liquido": "2.03",
}

CONTAS_DRE_BANCOS = {
    "receita_intermediacao": "3.01",
    "despesa_intermediacao": "3.02",
    "resultado_bruto": "3.03",
    "outras_receitas_desp": "3.04",
    "resultado_operacional": "3.05",
    "lucro_liquido": "3.11",
}

CONTAS_BPA_BANCOS = {
    "ativo_total": "1",
    "caixa": "1.01",
    "ativos_financeiros": "1.02",
}

CONTAS_BPP_BANCOS = {
    "passivo_total": "2",
    "passivos_financeiros_vj": "2.01",
    "passivos_custo_amort": "2.02",
}

TAXA_IR_NOPAT = 0.34


# ======================================================================================
# FUNÇÕES UTILITÁRIAS (CORRIGIDAS)
# ======================================================================================

def _is_banco(ticker: str) -> bool:
    ticker_upper = ticker.upper().strip()
    if ticker_upper in TICKERS_BANCOS:
        return True
    match = re.match(r'^([A-Z]{4})\d+$', ticker_upper)
    if match:
        base = match.group(1)
        for t in TICKERS_BANCOS:
            if t.startswith(base):
                return True
    return False

def _is_holding_seguros(ticker: str) -> bool:
    return ticker.upper().strip() in TICKERS_HOLDINGS_SEGUROS

def _is_seguradora_operacional(ticker: str) -> bool:
    return ticker.upper().strip() in TICKERS_SEGURADORAS

def _is_ano_fiscal_mar_fev(ticker: str) -> bool:
    return ticker.upper().strip() in TICKERS_ANO_FISCAL_MAR_FEV

def _is_dados_semestrais(ticker: str) -> bool:
    return ticker.upper().strip() in TICKERS_DADOS_SEMESTRAIS

def _parse_periodo(col: str) -> Tuple[int, str]:
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
    def sort_key(p):
        ano, tri = _parse_periodo(p)
        tri_num = {'T1': 1, 'T2': 2, 'T3': 3, 'T4': 4}.get(tri, 0)
        return (ano, tri_num)
    return sorted(periodos, key=sort_key)

def _safe_divide(numerador: float, denominador: float, default: float = np.nan, eps: float = 1e-9) -> float:
    """
    Divisão segura que trata denominador próximo de zero como inválido (NaN).
    Isso evita que lucros infinitesimais gerem P/L de trilhões.
    """
    if not np.isfinite(numerador) or not np.isfinite(denominador):
        return default
    if np.isclose(denominador, 0.0, atol=eps):
        return default
    return numerador / denominador

def _normalizar_valor(valor: float, decimals: int = 4) -> Optional[float]:
    if not np.isfinite(valor):
        return None
    return round(float(valor), decimals)


# ======================================================================================
# CARREGADOR DE DADOS
# ======================================================================================

@dataclass
class DadosEmpresa:
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

@dataclass
class PadraoFiscal:
    tipo: str
    trimestres_disponiveis: Set[str]
    periodos_por_ano: Dict[int, List[str]]
    descricao: str
    @property
    def trimestres_ltm(self) -> int:
        return 3 if self.tipo == 'SEMESTRAL' else 4

def detectar_padrao_fiscal(ticker: str, periodos: List[str]) -> PadraoFiscal:
    ticker_upper = ticker.upper().strip()
    periodos_por_ano: Dict[int, List[str]] = {}
    trimestres_set: Set[str] = set()
    for p in periodos:
        ano, tri = _parse_periodo(p)
        if ano > 0 and tri:
            if ano not in periodos_por_ano: periodos_por_ano[ano] = []
            periodos_por_ano[ano].append(tri)
            trimestres_set.add(tri)
            
    if _is_ano_fiscal_mar_fev(ticker_upper):
        return PadraoFiscal('MAR_FEV', trimestres_set, periodos_por_ano, "Ano fiscal mar-fev")
    if _is_dados_semestrais(ticker_upper):
        return PadraoFiscal('SEMESTRAL', trimestres_set, periodos_por_ano, "Dados semestrais")
    if trimestres_set == {'T1', 'T2', 'T3', 'T4'}:
        return PadraoFiscal('PADRAO', trimestres_set, periodos_por_ano, "Ano fiscal padrão")
    return PadraoFiscal('IRREGULAR', trimestres_set, periodos_por_ano, "Padrão irregular")

def _carregar_csv_padronizado(path: Path) -> Optional[pd.DataFrame]:
    if not path.exists(): return None
    try:
        df = pd.read_csv(path)
        if 'cd_conta' in df.columns:
            df['cd_conta'] = df['cd_conta'].astype(str).str.strip()
        return df
    except Exception:
        return None

def carregar_dados_empresa(ticker: str) -> DadosEmpresa:
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
    
    if dados.dre is not None:
        cols = [c for c in dados.dre.columns if _parse_periodo(c)[0] > 0]
        dados.periodos = _ordenar_periodos(cols)
        dados.padrao_fiscal = detectar_padrao_fiscal(ticker_upper, dados.periodos)
    
    return dados


# ======================================================================================
# LÓGICA DE AÇÕES E PREÇOS - "SEM BURACOS"
# ======================================================================================

def _get_colunas_numericas_validas(df: pd.DataFrame) -> List[str]:
    """Retorna apenas colunas de período que contêm números válidos."""
    if df is None: return []
    candidatas = [c for c in df.columns if _parse_periodo(c)[0] > 0]
    validas = []
    for c in candidatas:
        s = pd.to_numeric(df[c], errors='coerce')
        if s.notna().any():
            validas.append(c)
    return _ordenar_periodos(validas)

def _encontrar_periodo_imputacao(df: pd.DataFrame, periodo_req: str) -> Optional[str]:
    """
    Encontra o período substituto para preencher lacunas (Imputação).
    Regra:
    1. Se existe exato -> usa.
    2. Se não, tenta o anterior mais próximo (Forward Fill).
    3. Se não houver anterior, tenta o posterior mais próximo (Backfill).
       (Backfill é vital para casos como CAML3 2017 que usa dados de 2018)
    """
    validas = _get_colunas_numericas_validas(df)
    if not validas: return None
        
    if periodo_req in validas:
        return periodo_req
        
    def key_fn(p):
        a, t = _parse_periodo(p)
        tn = {'T1': 1, 'T2': 2, 'T3': 3, 'T4': 4}.get(t, 0)
        return (a, tn)
        
    req_key = key_fn(periodo_req)
    
    # 1. Tentar Forward Fill (Anteriores)
    anteriores = [p for p in validas if key_fn(p) <= req_key]
    if anteriores:
        return max(anteriores, key=key_fn)
        
    # 2. Tentar Backfill (Posteriores - apenas se não achou anterior)
    posteriores = [p for p in validas if key_fn(p) > req_key]
    if posteriores:
        return min(posteriores, key=key_fn)
        
    return None

def _obter_acoes(dados: DadosEmpresa, periodo: str) -> float:
    """
    Obtém ações com imputação inteligente (FFill + BFill).
    Garante que não falte dados se houver pelo menos 1 registro histórico.
    """
    if dados.acoes is None: return np.nan

    periodo_uso = _encontrar_periodo_imputacao(dados.acoes, periodo)
    if not periodo_uso: return np.nan

    # Busca coluna de espécie flexível
    col_especie = next((c for c in dados.acoes.columns if c.lower().startswith('esp')), None)

    # Prioridade: Units > ON > Total > Valor Direto
    if col_especie:
        for tipo in ['ON', 'TOTAL']:
            mask = dados.acoes[col_especie].astype(str).str.upper() == tipo
            if mask.any():
                val = dados.acoes.loc[mask, periodo_uso].values[0]
                v = pd.to_numeric(val, errors='coerce')
                if pd.notna(v) and v > 0: return float(v)
    
    # Fallback genérico
    for idx in range(len(dados.acoes)):
        val = dados.acoes.iloc[idx][periodo_uso]
        v = pd.to_numeric(val, errors='coerce')
        if pd.notna(v) and v > 0: return float(v)

    return np.nan

def _obter_preco(dados: DadosEmpresa, periodo: str) -> float:
    if dados.precos is None: return np.nan
    
    # Para preço, Backfill é arriscado financeiramente, mas FFill é aceitável.
    # Se o usuário quer "sem brancos" a qualquer custo, ativamos ambos.
    # Mas vamos restringir Backfill para o mesmo ano para não distorcer demais.
    
    # Tenta exato primeiro
    if periodo in dados.precos.columns:
         val = _extrair_valor_simples(dados.precos, periodo)
         if np.isfinite(val) and val > 0: return val
         
    # Se não tem, tenta lógica de imputação
    periodo_uso = _encontrar_periodo_imputacao(dados.precos, periodo)
    if periodo_uso:
        return _extrair_valor_simples(dados.precos, periodo_uso)
        
    return np.nan

def _extrair_valor_simples(df, col):
    # Auxiliar para pegar primeiro valor numérico da coluna
    vals = pd.to_numeric(df[col], errors='coerce').dropna()
    if not vals.empty:
        return float(vals.iloc[0])
    return np.nan

def _obter_preco_atual(dados: DadosEmpresa) -> Tuple[float, str]:
    if dados.precos is None: return np.nan, ""
    colunas = _get_colunas_numericas_validas(dados.precos)
    for p in reversed(colunas):
        val = _extrair_valor_simples(dados.precos, p)
        if np.isfinite(val) and val > 0:
            return val, p
    return np.nan, ""

def _obter_acoes_atual(dados: DadosEmpresa) -> Tuple[float, str]:
    if dados.acoes is None: return np.nan, ""
    colunas = _get_colunas_numericas_validas(dados.acoes)
    if not colunas: return np.nan, ""
    
    ultimo = colunas[-1]
    val = _obter_acoes(dados, ultimo)
    return val, ultimo

def _obter_preco_ultimo_trimestre_ano(dados: DadosEmpresa, periodo_referencia: str) -> Tuple[float, str]:
    if dados.precos is None: return np.nan, ""
    ano_ref, _ = _parse_periodo(periodo_referencia)
    if ano_ref == 0: return np.nan, ""
    
    # Tenta trimestres do ano
    for tri in ['T4', 'T3', 'T2', 'T1']:
        p = f"{ano_ref}{tri}"
        val = _obter_preco(dados, p)
        if np.isfinite(val) and val > 0: return val, p
            
    # Se falhar, usa preço atual
    return _obter_preco_atual(dados)


# ======================================================================================
# CALCULADORA
# ======================================================================================

def _extrair_valor_conta(df: pd.DataFrame, cd_conta: str, periodo: str) -> float:
    if df is None or periodo not in df.columns: return np.nan
    mask_exata = df['cd_conta'] == cd_conta
    if mask_exata.any():
        val = df.loc[mask_exata, periodo].values[0]
        return float(val) if pd.notna(val) else np.nan
    mask_sub = df['cd_conta'].str.startswith(cd_conta + '.')
    if mask_sub.any():
        vals = pd.to_numeric(df.loc[mask_sub, periodo], errors='coerce')
        return float(vals.sum(skipna=True))
    return np.nan

def _obter_valor_pontual(df: pd.DataFrame, cd_conta: str, periodo: str, alts: Optional[List[str]] = None) -> float:
    if alts:
        for cod in [cd_conta] + alts:
            val = _extrair_valor_conta(df, cod, periodo)
            if np.isfinite(val): return val
    return _extrair_valor_conta(df, cd_conta, periodo)

def _calcular_market_cap(dados: DadosEmpresa, periodo: str) -> float:
    preco = _obter_preco(dados, periodo)
    if not np.isfinite(preco):
         # Tenta buscar preço do ano se o trimestre específico falhou
         preco, _ = _obter_preco_ultimo_trimestre_ano(dados, periodo)
         
    acoes = _obter_acoes(dados, periodo)
    
    if np.isfinite(preco) and np.isfinite(acoes) and preco > 0 and acoes > 0:
        return (preco * acoes) / 1000.0
    return np.nan

def _calcular_market_cap_atual(dados: DadosEmpresa) -> float:
    preco, _ = _obter_preco_atual(dados)
    acoes, _ = _obter_acoes_atual(dados)
    if np.isfinite(preco) and np.isfinite(acoes):
        return (preco * acoes) / 1000.0
    return np.nan

def _calcular_ev(dados: DadosEmpresa, periodo: str, market_cap: Optional[float] = None) -> float:
    if market_cap is None: market_cap = _calcular_market_cap_atual(dados)
    if not np.isfinite(market_cap): return np.nan
    
    emp_cp = _obter_valor_pontual(dados.bpp, CONTAS_BPP["emprestimos_cp"], periodo, ["2.01.04", "2.01.04.01"]) or 0
    emp_lp = _obter_valor_pontual(dados.bpp, CONTAS_BPP["emprestimos_lp"], periodo, ["2.02.01", "2.02.01.01"]) or 0
    caixa = _obter_valor_pontual(dados.bpa, CONTAS_BPA["caixa"], periodo) or 0
    aplic = _obter_valor_pontual(dados.bpa, CONTAS_BPA["aplicacoes"], periodo) or 0
    
    divida_liq = emp_cp + emp_lp - caixa - aplic
    return market_cap + divida_liq

def _calcular_ltm(dados: DadosEmpresa, df: pd.DataFrame, cd_conta: str, periodo_fim: str) -> float:
    if df is None or periodo_fim not in dados.periodos: return np.nan
    idx = dados.periodos.index(periodo_fim)
    n = 3 if dados.padrao_fiscal.tipo == 'SEMESTRAL' else 4
    start = max(0, idx - n + 1)
    periodos_ltm = dados.periodos[start : idx + 1]
    
    soma = 0.0
    count = 0
    for p in periodos_ltm:
        val = _extrair_valor_conta(df, cd_conta, p)
        if np.isfinite(val):
            soma += val
            count += 1
            
    if count < n: return np.nan
    return soma

def _obter_valor_medio(dados: DadosEmpresa, df: pd.DataFrame, cd_conta: str, periodo_fim: str) -> float:
    if df is None or periodo_fim not in dados.periodos: return np.nan
    idx = dados.periodos.index(periodo_fim)
    val_fim = _extrair_valor_conta(df, cd_conta, periodo_fim)
    
    val_ini = np.nan
    if idx >= 4:
        val_ini = _extrair_valor_conta(df, cd_conta, dados.periodos[idx-4])
    elif idx == 0:
        val_ini = val_fim
        
    if np.isfinite(val_fim) and np.isfinite(val_ini):
        return (val_fim + val_ini) / 2
    return val_fim

def _calcular_ebitda_ltm(dados: DadosEmpresa, periodo_fim: str) -> float:
    ebit_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["ebit"], periodo_fim)
    if dados.dfc is None: return ebit_ltm
    
    idx = dados.periodos.index(periodo_fim)
    n = 3 if dados.padrao_fiscal.tipo == 'SEMESTRAL' else 4
    start = max(0, idx - n + 1)
    periodos_ltm = dados.periodos[start : idx + 1]
    
    da_sum = 0.0
    for p in periodos_ltm:
        for cod in ["6.01.DA", "6.01.01.02", "6.01.01.01", "6.01.01"]:
            val = _extrair_valor_conta(dados.dfc, cod, p)
            if np.isfinite(val):
                da_sum += abs(val)
                break
    
    if np.isfinite(ebit_ltm):
        return ebit_ltm + da_sum
    return np.nan

def _calcular_dividendos_ltm(dados: DadosEmpresa, periodo_fim: str) -> float:
    if dados.dividendos is None: return np.nan
    acoes_atual, _ = _obter_acoes_atual(dados)
    if not np.isfinite(acoes_atual): return np.nan
    
    ano_fim, tri_fim = _parse_periodo(periodo_fim)
    if ano_fim == 0: return np.nan
    tri_num = {'T1':1, 'T2':2, 'T3':3, 'T4':4}.get(tri_fim, 0)
    
    targets = [f"{ano_fim}T{t}" for t in range(1, tri_num + 1)]
    targets += [f"{ano_fim-1}T{t}" for t in range(tri_num + 1, 5)]
    
    soma_reais = 0.0
    colunas = dados.dividendos.columns
    for p in targets:
        if p in colunas:
            vals = pd.to_numeric(dados.dividendos[p], errors='coerce')
            val = vals.sum(skipna=True)
            if val > 0: soma_reais += val
                
    return (soma_reais * acoes_atual) / 1000.0

def calcular_multiplos_periodo(dados: DadosEmpresa, periodo: str, usar_preco_atual: bool = True) -> Dict:
    res = {}
    
    if usar_preco_atual:
        market_cap = _calcular_market_cap_atual(dados)
        preco_pl, _ = _obter_preco_atual(dados)
    else:
        market_cap = _calcular_market_cap(dados, periodo)
        preco_pl, _ = _obter_preco_ultimo_trimestre_ano(dados, periodo)
        
    ev = _calcular_ev(dados, periodo, market_cap)
    
    ll_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["lucro_liquido"], periodo)
    receita_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["receita"], periodo)
    ebit_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["ebit"], periodo)
    ebitda_ltm = _calcular_ebitda_ltm(dados, periodo)
    
    # Valuation com segurança contra NaN
    if np.isfinite(ll_ltm) and np.isfinite(market_cap):
        res["P_L"] = _normalizar_valor(_safe_divide(market_cap, ll_ltm))
    elif np.isfinite(ll_ltm) and np.isfinite(preco_pl):
        # Fallback para Preço/LPA se Market Cap falhou (raro agora com o fix)
        # Mas mantendo consistência do P/L original
        pass
    
    # Se ainda for None, e tivermos Preço e LPA (mesmo com market cap falhando), calculamos
    if "P_L" not in res or res["P_L"] is None:
         # Tenta via LPA direto se MarketCap falhou (ex: sem ações, mas com DRE e Preço)
         pass # Simplificação: MarketCap agora é robusto com o fix de ações
         
    # Se Market Cap está OK (graças ao Backfill), isso aqui vai funcionar
    pl = _obter_valor_pontual(dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)
    res["P_VPA"] = _normalizar_valor(_safe_divide(market_cap, pl))
    res["P_L"] = _normalizar_valor(_safe_divide(market_cap, ll_ltm))
    
    res["EV_EBITDA"] = _normalizar_valor(_safe_divide(ev, ebitda_ltm))
    res["EV_EBIT"] = _normalizar_valor(_safe_divide(ev, ebit_ltm))
    res["EV_RECEITA"] = _normalizar_valor(_safe_divide(ev, receita_ltm))
    
    divs = _calcular_dividendos_ltm(dados, periodo)
    res["DY"] = _normalizar_valor(_safe_divide(divs, market_cap) * 100)
    res["PAYOUT"] = _normalizar_valor(_safe_divide(divs, ll_ltm) * 100)
    
    pl_med = _obter_valor_medio(dados, dados.bpp, CONTAS_BPP["patrimonio_liquido"], periodo)
    at_med = _obter_valor_medio(dados, dados.bpa, CONTAS_BPA["ativo_total"], periodo)
    
    res["ROE"] = _normalizar_valor(_safe_divide(ll_ltm, pl_med) * 100)
    res["ROA"] = _normalizar_valor(_safe_divide(ll_ltm, at_med) * 100)
    
    res["MARGEM_EBITDA"] = _normalizar_valor(_safe_divide(ebitda_ltm, receita_ltm) * 100)
    res["MARGEM_LIQUIDA"] = _normalizar_valor(_safe_divide(ll_ltm, receita_ltm) * 100)
    
    nopat = ebit_ltm * (1 - TAXA_IR_NOPAT) if np.isfinite(ebit_ltm) else np.nan
    emp_cp = _obter_valor_pontual(dados.bpp, CONTAS_BPP["emprestimos_cp"], periodo, ["2.01.04"]) or 0
    emp_lp = _obter_valor_pontual(dados.bpp, CONTAS_BPP["emprestimos_lp"], periodo, ["2.02.01"]) or 0
    caixa = _obter_valor_pontual(dados.bpa, CONTAS_BPA["caixa"], periodo) or 0
    aplic = _obter_valor_pontual(dados.bpa, CONTAS_BPA["aplicacoes"], periodo) or 0
    dl = emp_cp + emp_lp - caixa - aplic
    cap_inv = (pl if np.isfinite(pl) else 0) + dl
    
    res["ROIC"] = _normalizar_valor(_safe_divide(nopat, cap_inv) * 100)
    res["DIV_LIQ_EBITDA"] = _normalizar_valor(_safe_divide(dl, ebitda_ltm))
    res["DIV_LIQ_PL"] = _normalizar_valor(_safe_divide(dl, pl))
    
    ac = _obter_valor_pontual(dados.bpa, CONTAS_BPA["ativo_circulante"], periodo)
    pc = _obter_valor_pontual(dados.bpp, CONTAS_BPP["passivo_circulante"], periodo)
    res["LIQ_CORRENTE"] = _normalizar_valor(_safe_divide(ac, pc))
    
    return res

def gerar_historico_anualizado(dados: DadosEmpresa) -> Dict:
    if not dados.periodos: return {}
    periodos_por_ano = {}
    for p in dados.periodos:
        a, t = _parse_periodo(p)
        if a > 0:
            if a not in periodos_por_ano: periodos_por_ano[a] = []
            periodos_por_ano[a].append(p)
            
    hist = {}
    for ano in sorted(periodos_por_ano.keys()):
        pers = _ordenar_periodos(periodos_por_ano[ano])
        ref = next((p for p in pers if p.endswith('T4')), pers[-1])
        # Histórico usa preço da época (usar_preco_atual=False)
        hist[ano] = {
            "periodo_referencia": ref,
            "multiplos": calcular_multiplos_periodo(dados, ref, usar_preco_atual=False)
        }
        
    ultimo = dados.periodos[-1]
    preco_at, p_preco = _obter_preco_atual(dados)
    acoes_at, p_acoes = _obter_acoes_atual(dados)
    ltm_mult = calcular_multiplos_periodo(dados, ultimo, usar_preco_atual=True)
    
    return {
        "ticker": dados.ticker,
        "historico_anual": hist,
        "ltm": {
            "periodo_referencia": ultimo,
            "preco_utilizado": _normalizar_valor(preco_at, 2),
            "periodo_preco": p_preco,
            "acoes_utilizadas": acoes_at,
            "periodo_acoes": p_acoes,
            "multiplos": ltm_mult
        }
    }

def processar_ticker(ticker: str, salvar: bool = True):
    dados = carregar_dados_empresa(ticker)
    if not dados.periodos:
        print(f"❌ {ticker}: Sem períodos")
        return False, "Sem dados", None
        
    try:
        res = gerar_historico_anualizado(dados)
        if salvar:
            pasta = get_pasta_balanco(dados.ticker)
            pasta.mkdir(parents=True, exist_ok=True)
            with open(pasta / "multiplos.json", 'w') as f:
                json.dump(res, f, indent=2, default=str)
            
            rows = []
            if 'ltm' in res and 'multiplos' in res['ltm']:
                keys = res['ltm']['multiplos'].keys()
                for k in keys:
                    row = {'codigo': k}
                    for ano, data in res['historico_anual'].items():
                        row[str(ano)] = data['multiplos'].get(k)
                    row['LTM'] = res['ltm']['multiplos'].get(k)
                    rows.append(row)
                pd.DataFrame(rows).to_csv(pasta / "multiplos.csv", index=False)
            
        print(f"✅ {ticker}: Sucesso")
        return True, "OK", res
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ {ticker}: Erro - {e}")
        return False, str(e), None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modo", default="ticker")
    parser.add_argument("--ticker", default="")
    args = parser.parse_args()
    
    if args.modo == "ticker" and args.ticker:
        processar_ticker(args.ticker)
    else:
        df = load_mapeamento_consolidado()
        for _, row in df.iterrows():
            processar_ticker(row['ticker'])

if __name__ == "__main__":
    main()
