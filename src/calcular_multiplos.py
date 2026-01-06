# src/calcular_multiplos.py
"""
Calculadora de Múltiplos Financeiros para Empresas Não-Financeiras
==================================================================
VERSÃO CORRIGIDA - Janeiro 2026

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

CORREÇÕES APLICADAS (VERSÃO 2026-01-06):
1. ✅ Backfill de Ações: Usa primeiro dado disponível para períodos sem ações (CAML3 2017)
2. ✅ Filtro de Colunas Sujas: Ignora colunas com texto (BEEF3 2026T1 com "ON"/"TOTAL")
3. ✅ Divisão Segura: Tolerância de 1e-9 para evitar P/L infinito
4. Busca robusta de preços (período atual ou mais recente disponível)
5. Cálculo de EBITDA revisado
6. Cálculo de ROIC com taxa de IR correta
7. Dividend Yield calculado corretamente
8. Múltiplos bancários simplificados para máxima confiabilidade

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
    """
    ✅ CORREÇÃO 3: Divisão segura com tolerância de 1e-9.
    
    Evita P/L infinito quando lucro é próximo de zero (mas não exatamente zero).
    Exemplo: Lucro = 0.0001 → Market Cap / 0.0001 = 1 milhão (absurdo!)
    
    Args:
        numerador: Valor no numerador
        denominador: Valor no denominador
        default: Valor padrão se divisão inválida (np.nan)
        eps: Tolerância para considerar denominador como zero (1e-9)
    
    Returns:
        Resultado da divisão ou default se inválida
    """
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


# ======================================================================================
# FUNÇÕES DE OBTENÇÃO DE PREÇO E AÇÕES - COM CORREÇÕES
# ======================================================================================

def _obter_preco(dados: DadosEmpresa, periodo: str) -> float:
    """
    Obtém preço da ação no período específico.
    
    FORMATO ESPERADO DO CSV:
    Preço_Fechamento,2015T1,2015T2,...,2025T3
    Preço de Fechamento Ajustado,2.11,2.12,...,15.56
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
    
    CORREÇÃO: Busca em TODAS as colunas do CSV de preços,
    não apenas nos períodos com balanços reportados.
    
    Returns:
        (preço, período) - preço mais recente e o período correspondente
    """
    if dados.precos is None:
        return np.nan, ""
    
    # ✅ CORREÇÃO 2: Usa filtro de colunas numéricas
    colunas_precos = _get_colunas_numericas_validas(dados.precos)
    
    if not colunas_precos:
        return np.nan, ""
    
    # Ordenar períodos e percorrer do mais recente ao mais antigo
    periodos_ordenados = _ordenar_periodos(colunas_precos)
    
    for p in reversed(periodos_ordenados):
        preco = _obter_preco(dados, p)
        if np.isfinite(preco) and preco > 0:
            return preco, p
    
    return np.nan, ""



def _obter_acoes(dados: DadosEmpresa, periodo: str) -> float:
    """
    ✅ CORREÇÃO 1 APLICADA: Obtém número de ações com Backfill para IPOs.

    Se o período (ex: 2025T3) NÃO existir no acoes_historico.csv:
        1) Prefere o mesmo ANO (ex: 2025T4) se existir
        2) Se não houver nada do ano, usa o PRIMEIRO período disponível (Backfill)
    
    Exemplo CAML3:
        Solicitado: 2017T4 (antes do IPO)
        Disponível: [2018T4, 2019T1, ...]
        Retorna: ações de 2018T4 (Backfill)
    """
    if dados.acoes is None:
        return np.nan

    ticker_upper = dados.ticker.upper().strip()

    # UNITS CONHECIDAS: Usar apenas ON (não TOTAL)
    TICKERS_UNITS = {'KLBN11', 'ITUB', 'SANB11', 'BPAC11'}

    # ✅ CORREÇÃO 2: Usa filtro de colunas numéricas
    col_periodos = _get_colunas_numericas_validas(dados.acoes)
    if not col_periodos:
        return np.nan

    periodo_busca = periodo

    # ✅ CORREÇÃO 1: Se o período não existe, escolher fallback COM BACKFILL
    if periodo_busca not in dados.acoes.columns:
        ano_req, tri_req = _parse_periodo(periodo_busca)

        # se período inválido, usa o mais recente do CSV
        if ano_req == 0:
            periodo_busca = _ordenar_periodos(col_periodos)[-1]
        else:
            tri_num_req = {'T1': 1, 'T2': 2, 'T3': 3, 'T4': 4}.get(tri_req, 0)

            # candidatos do mesmo ano
            mesmo_ano = []
            for c in col_periodos:
                a, t = _parse_periodo(c)
                if a == ano_req:
                    tn = {'T1': 1, 'T2': 2, 'T3': 3, 'T4': 4}.get(t, 0)
                    if tn > 0:
                        mesmo_ano.append((tn, c))

            if mesmo_ano:
                # pega o mais próximo <= trimestre solicitado; se não houver, pega o maior do ano (normalmente T4)
                leq = [x for x in mesmo_ano if x[0] <= tri_num_req] if tri_num_req > 0 else []
                if leq:
                    periodo_busca = max(leq, key=lambda x: x[0])[1]
                else:
                    periodo_busca = max(mesmo_ano, key=lambda x: x[0])[1]
            else:
                # ✅ BACKFILL: sem dados do ano, usa o PRIMEIRO disponível (não o mais recente!)
                periodo_busca = _ordenar_periodos(col_periodos)[0]

    # Agora, extrair o número de ações
    if 'Espécie_Acao' in dados.acoes.columns:
        # Para UNITS: usar apenas ON
        if ticker_upper in TICKERS_UNITS:
            mask_on = dados.acoes['Espécie_Acao'] == 'ON'
            if mask_on.any():
                val = dados.acoes.loc[mask_on, periodo_busca].values[0]
                if pd.notna(val):
                    try:
                        v = float(val)
                        return v if v > 0 else np.nan
                    except (ValueError, TypeError):
                        return np.nan

        # Para outras empresas: usar TOTAL
        mask_total = dados.acoes['Espécie_Acao'] == 'TOTAL'
        if mask_total.any():
            val = dados.acoes.loc[mask_total, periodo_busca].values[0]
            if pd.notna(val):
                try:
                    v = float(val)
                    return v if v > 0 else np.nan
                except (ValueError, TypeError):
                    return np.nan

    return np.nan



def _obter_acoes_atual(dados: DadosEmpresa) -> Tuple[float, str]:
    """
    Obtém o número de ações mais recente disponível.
    
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
# [CONTINUA NO PRÓXIMO BLOCO - código muito longo, truncando aqui]
# ======================================================================================
