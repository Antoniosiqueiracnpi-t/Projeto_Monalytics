# src/padronizar_dre.py
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

# ADICIONAR NO TOPO DO ARQUIVO (após outros imports):
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from multi_ticker_utils import get_ticker_principal, get_pasta_balanco, load_mapeamento_consolidado

# ======================================================================================
# CONTAS PADRÃO (NÃO FINANCEIRAS) - DRE
# ======================================================================================


DRE_PADRAO: List[Tuple[str, str]] = [
    ("3.01", "Receita de Venda de Bens e/ou Serviços"),
    ("3.02", "Custo dos Bens e/ou Serviços Vendidos"),
    ("3.03", "Resultado Bruto"),
    ("3.04", "Despesas/Receitas Operacionais"),
    ("3.04.02", "Despesas Gerais e Administrativas"),        # ✅ ADICIONAR
    ("3.04.05", "Outras Despesas Operacionais"),             # ✅ ADICIONAR
    ("3.04.05.02", "Depreciação e amortização"),             # ✅ CRÍTICO WIZS3
    ("3.04.06", "Resultado de Equivalência Patrimonial"),    # ✅ CRÍTICO WIZS3
    ("3.05", "Resultado Antes do Resultado Financeiro e dos Tributos"),
    ("3.06", "Resultado Financeiro"),
    ("3.06.01", "Receitas Financeiras"),                     # ✅ ADICIONAR
    ("3.06.02", "Despesas Financeiras"),                     # ✅ ADICIONAR
    ("3.07", "Resultado Antes dos Tributos sobre o Lucro"),
    ("3.08", "Imposto de Renda e Contribuição Social sobre o Lucro"),
    ("3.09", "Resultado Líquido das Operações Continuadas"),
    ("3.10", "Resultado Líquido de Operações Descontinuadas"),
    ("3.11", "Lucro/Prejuízo Consolidado do Período"),
    ("3.11.01", "Atribuído a Sócios da Empresa Controladora"), # ✅ ADICIONAR
    ("3.11.02", "Atribuído a Sócios Não Controladores"),       # ✅ CRÍTICO WIZS3
]


# ======================================================================================
# CONTAS BANCOS (INSTITUIÇÕES FINANCEIRAS) - DRE
# ======================================================================================

DRE_BANCOS: List[Tuple[str, str]] = [
    ("3.01", "Receitas de Intermediação Financeira"),
    ("3.02", "Despesas de Intermediação Financeira"),
    ("3.03", "Resultado Bruto de Intermediação Financeira"),
    ("3.04", "Outras Despesas e Receitas Operacionais"),
    ("3.05", "Resultado antes dos Tributos sobre o Lucro"),
    ("3.06", "Imposto de Renda e Contribuição Social sobre o Lucro"),
    ("3.07", "Lucro ou Prejuízo das Operações Continuadas"),
    ("3.08", "Resultado Líquido das Operações Descontinuadas"),
    ("3.09", "Lucro ou Prejuízo antes das Participações e Contribuições Estatutárias"),
    ("3.10", "Participações nos Lucros e Contribuições Estatutárias"),
    ("3.11", "Lucro ou Prejuízo Líquido Consolidado do Período"),
]

# Lista de tickers de bancos/instituições financeiras
TICKERS_BANCOS: Set[str] = {
    "RPAD3", "RPAD5", "RPAD6",
    "ABCB4",
    "BMGB4",
    "BBDC3", "BBDC4",
    "BPAC3", "BPAC5", "BPAC11",
    "BSLI3", "BSLI4",
    "BBAS3",
    "BGIP3", "BGIP4",
    "BPAR3",
    "BRSR3", "BRSR5", "BRSR6",
    "BNBR3",
    "BMIN3", "BMIN4",
    "BMEB3", "BMEB4",
    "BPAN4",
    "PINE3", "PINE4",
    "SANB3", "SANB4", "SANB11",
    "BEES3", "BEES4",
    "ITUB3", "ITUB4",
}

# ======================================================================================
# CONTAS BBSE3 (BB SEGURIDADE) - ESTRUTURA ESPECÍFICA DE SEGUROS
# ======================================================================================
# Holding que lucra com corretagem (3.05) + equivalência patrimonial (3.06)

DRE_BBSE3: List[Tuple[str, str]] = [
    ("3.01", "Receitas das Atividades Seguradoras"),           # Sempre zero (holding não opera)
    ("3.02", "Despesas da Atividade Seguradora"),              # Sempre zero
    ("3.03", "Resultado Bruto"),                                # Sempre zero
    ("3.04", "Despesas Administrativas"),                       # Despesas operacionais da holding
    ("3.04.01", "Despesas com Pessoal Próprio"),
    ("3.04.02", "Despesas com Serviços de Terceiros"),
    ("3.04.03", "Despesas com Localização e Funcionamento"),
    ("3.04.04", "Despesas com Publicidade e Propaganda"),
    ("3.04.05", "Despesas com Tributos"),                       # NÃO é equivalência!
    ("3.04.06", "Despesas com Publicações"),
    ("3.05", "Outras Receitas e Despesas Operacionais"),       # ★ RECEITAS PRINCIPAIS ★
    ("3.05.01", "Receitas de Comissões (Líquidas)"),           # ✅ CORRETAGEM
    ("3.05.02", "Custo dos serviços prestados"),
    ("3.05.03", "Despesas com Pessoal"),
    ("3.05.04", "Despesas Administrativas e com Vendas"),
    ("3.05.05", "Despesas Tributárias"),
    ("3.05.06", "Outras receitas operacionais"),
    ("3.05.07", "Outras despesas operacionais"),
    ("3.06", "Resultado de Equivalência Patrimonial"),         # ★ CORAÇÃO DO LUCRO ★
    ("3.06.01", "Receitas de Equivalência Patrimonial"),       # ✅ LUCRO DAS INVESTIDAS
    ("3.06.02", "Despesas de Equivalência Patrimonial"),
    ("3.07", "EBIT"),
    ("3.08", "Resultado Financeiro"),
    ("3.08.01", "Receitas Financeiras"),
    ("3.08.02", "Despesas Financeiras"),
    ("3.09", "LAIR"),
    ("3.10", "IR/CSLL"),
    ("3.13", "Lucro Líquido"),
    ("3.13.01", "Atribuído a Sócios da Controladora"),
]

# ======================================================================================
# CONTAS CXSE3 (CAIXA SEGURIDADE) - ESTRUTURA TRADICIONAL
# ======================================================================================
# Holding que usa estrutura de empresa de serviços padrão

DRE_CXSE3: List[Tuple[str, str]] = [
    ("3.01", "Receita de Venda de Bens e/ou Serviços"),        # Sempre zero
    ("3.02", "Custo dos Bens e/ou Serviços Vendidos"),         # Sempre zero
    ("3.03", "Resultado Bruto"),                                # Sempre zero
    ("3.04", "Despesas/Receitas Operacionais"),                # ★ TUDO ESTÁ AQUI ★
    ("3.04.01", "Despesas com Vendas"),
    ("3.04.02", "Despesas Gerais e Administrativas"),
    ("3.04.03", "Perdas pela Não Recuperabilidade de Ativos"),
    ("3.04.04", "Outras Receitas Operacionais"),               # ✅ RECEITAS PRINCIPAIS
    ("3.04.04.01", "Receitas de Acesso à Rede e Uso da Marca"),
    ("3.04.04.02", "Receitas de prestação de serviços"),       # ✅ CORRETAGEM
    ("3.04.04.03", "Custo dos Serviços Prestados"),
    ("3.04.04.04", "Outras"),
    ("3.04.05", "Outras Despesas Operacionais"),
    ("3.04.05.01", "Despesas Tributárias"),
    ("3.04.05.02", "Outras receitas/despesas operacionais"),
    ("3.04.05.03", "Participações nos Resultados"),
    ("3.04.06", "Resultado de Equivalência Patrimonial"),      # ✅ LUCRO INVESTIDAS
    ("3.05", "EBIT"),
    ("3.06", "Resultado Financeiro"),
    ("3.06.01", "Receitas Financeiras"),
    ("3.06.02", "Despesas Financeiras"),
    ("3.07", "LAIR"),
    ("3.08", "IR/CSLL"),
    ("3.11", "Lucro Líquido"),
    ("3.11.01", "Atribuído a Controladora"),
]

# Listas de tickers separadas
TICKERS_BBSE3: Set[str] = {"BBSE3"}
TICKERS_CXSE3: Set[str] = {"CXSE3"}


# ======================================================================================
# EMPRESAS COM ANO FISCAL MARÇO-FEVEREIRO (CAML3, etc.)
# ======================================================================================

TICKERS_ANO_FISCAL_MAR_FEV: Set[str] = {
    "CAML3",  # Camil Alimentos - ano fiscal mar/YYYY a fev/YYYY+1
}

# ======================================================================================
# CONTAS IRBR3 (IRB BRASIL RESSEGUROS)
# ======================================================================================
# Resseguradora: assume risco de seguradoras, lucra com prêmios - sinistros + float

DRE_IRBR3: List[Tuple[str, str]] = [
    ("3.01", "Receitas das Operações"),
    ("3.01.01", "Operações de Seguros"),                       # Geralmente zero (é resseguradora)
    ("3.01.02", "Operações de Resseguros"),                    # ✅ RECEITA PRINCIPAL
    ("3.01.02.01", "Prêmios de Resseguros Ganhos"),           # ✅ Receita real
    ("3.01.02.02", "Outras Receitas de Resseguros"),
    ("3.02", "Sinistros e Despesas das Operações"),
    ("3.02.01", "Operações de Seguros"),                       # Geralmente zero
    ("3.02.02", "Operações de Resseguros"),                    # ✅ CUSTOS PRINCIPAIS
    ("3.02.02.01", "Sinistros Retidos de Resseguros"),        # ✅ O RISCO
    ("3.02.02.02", "Despesas de Comercialização"),            # ✅ Comissões
    ("3.02.02.03", "Outras Despesas de Resseguros"),
    ("3.03", "Resultado Bruto"),                               # ✅ Margem de subscrição
    ("3.04", "Despesas Administrativas"),
    ("3.05", "Outras Receitas e Despesas Operacionais"),
    ("3.06", "Resultado de Equivalência Patrimonial"),
    ("3.07", "EBIT"),
    ("3.08", "Resultado Financeiro"),                          # ★ FLOAT: 30-50% do lucro ★
    ("3.08.01", "Receitas Financeiras"),
    ("3.08.02", "Despesas Financeiras"),
    ("3.09", "LAIR"),
    ("3.10", "IR/CSLL"),
    ("3.13", "Lucro/Prejuízo Consolidado do Período"),
    ("3.13.01", "Atribuído aos Controladores"),
]

TICKERS_IRBR3: Set[str] = {"IRBR3"}

# ======================================================================================
# CONTAS PSSA3 (PORTO SEGURO) - COM QUEBRA IFRS 17 EM 2023
# ======================================================================================
# Seguradora operacional multi-linhas com mudança estrutural em 2023

DRE_PSSA3: List[Tuple[str, str]] = [
    # CONTAS USADAS EM AMBOS OS PERÍODOS
    ("3.01", "Receita de Venda de Bens e/ou Serviços"),
    ("3.03", "Resultado Bruto"),
    ("3.04", "Despesas/Receitas Operacionais"),
    ("3.04.02", "Despesas Gerais e Administrativas"),
    ("3.04.02.01", "Despesas administrativas"),
    ("3.04.02.02", "Despesas com tributos"),
    ("3.04.04", "Outras Receitas Operacionais"),
    ("3.04.05", "Outras Despesas Operacionais"),
    ("3.05", "EBIT"),
    ("3.06", "Resultado Financeiro"),
    ("3.06.01", "Receitas Financeiras"),
    ("3.06.02", "Despesas Financeiras"),
    ("3.11", "Lucro Líquido"),
    ("3.11.01", "Atribuído aos Controladores"),
    
    # CONTAS ANTIGAS (2015-2022) - Mantidas para compatibilidade
    ("3.01.01", "Prêmios de seguros emitidos"),               # ✅ Até 2022
    ("3.01.02", "(-) Prêmios de resseguro cedido"),
    ("3.01.03", "Receitas de operações de crédito"),
    ("3.01.04", "Receitas de prestações de serviços"),
    ("3.01.05", "Contribuições de planos de previdência"),
    ("3.01.06", "Receita com títulos de capitalização"),
    ("3.04.05.01", "Variação das provisões técnicas - seguros"),
    ("3.04.05.02", "Variação das provisões técnicas - previdência"),
    ("3.04.05.03", "Sinistros retidos - bruto"),              # ✅ Até 2022
    ("3.04.05.04", "Benefícios de planos de previdência"),
    ("3.04.05.05", "Recuperação de resseguradores"),
    ("3.04.05.06", "Recuperação de salvados e ressarcimentos"),
    ("3.04.05.07", "Custos de aquisição - seguros"),          # ✅ Até 2022
    ("3.04.05.08", "Custos de aquisição - outros"),           # ✅ Mantido após 2023
    ("3.04.05.09", "Custos dos serviços prestados"),
    ("3.04.05.10", "Outras despesas operacionais"),
    
    # CONTAS NOVAS (2023+) - IFRS 17
    ("3.01.07", "Receita de seguro/contrato de seguro"),      # ★ NOVA RECEITA (2023+) ★
    ("3.04.05.11", "Despesas de seguro/contrato de seguro"),  # ★ TUDO AGREGADO (2023+) ★
    ("3.04.05.12", "Despesas líquidas com resseguros/retrocessões"),
]

TICKERS_PSSA3: Set[str] = {"PSSA3"}


# ======================================================================================
# LUCRO POR AÇÃO (COMUM A TODOS)
# ======================================================================================

EPS_CODE = "3.99"
EPS_LABEL = "Lucro por Ação (Reais/Ação)"


def _is_banco(ticker: str) -> bool:
    """Verifica se o ticker é de uma instituição financeira (banco)."""
    return ticker.upper().strip() in TICKERS_BANCOS


def _is_bbse3(ticker: str) -> bool:
    """BB Seguridade - estrutura específica de seguros."""
    return ticker.upper().strip() in TICKERS_BBSE3

def _is_cxse3(ticker: str) -> bool:
    """Caixa Seguridade - estrutura tradicional."""
    return ticker.upper().strip() in TICKERS_CXSE3

def _is_irbr3(ticker: str) -> bool:
    """IRB Brasil Resseguros - estrutura de resseguros."""
    return ticker.upper().strip() in TICKERS_IRBR3

def _is_pssa3(ticker: str) -> bool:
    """Porto Seguro - com quebra IFRS 17 em 2023."""
    return ticker.upper().strip() in TICKERS_PSSA3


def _get_dre_schema(ticker: str) -> List[Tuple[str, str]]:
    """
    Retorna o esquema DRE apropriado para o ticker.
    CRÍTICO: BBSE3, CXSE3, IRBR3, PSSA3 têm estruturas únicas.
    """
    ticker_upper = ticker.upper().strip()
    
    # Holdings de seguros - estruturas DIFERENTES
    if ticker_upper in TICKERS_BBSE3:
        return DRE_BBSE3
    elif ticker_upper in TICKERS_CXSE3:
        return DRE_CXSE3
    
    # Seguradoras operacionais
    elif ticker_upper in TICKERS_IRBR3:
        return DRE_IRBR3
    elif ticker_upper in TICKERS_PSSA3:
        return DRE_PSSA3
    
    # Bancos
    elif _is_banco(ticker_upper):
        return DRE_BANCOS
    
    # Padrão (inclui WIZC3)
    else:
        return DRE_PADRAO

def _is_ano_fiscal_mar_fev(ticker: str) -> bool:
    """Verifica se o ticker tem ano fiscal março-fevereiro."""
    return ticker.upper().strip() in TICKERS_ANO_FISCAL_MAR_FEV


def _get_fiscal_year_mar_fev(data: pd.Timestamp) -> int:
    """
    Para empresas com ano fiscal mar-fev, retorna o ano fiscal.
    
    Regra da Camil e mercado brasileiro:
    - Ano Fiscal 2024 = mar/2024 a fev/2025
    - Ano Fiscal 2025 = mar/2025 a fev/2026
    
    Então:
    - maio/2024 → T1 → Ano Fiscal 2024
    - agosto/2024 → T2 → Ano Fiscal 2024
    - novembro/2024 → T3 → Ano Fiscal 2024
    - fevereiro/2025 → T4 → Ano Fiscal 2024 (pertence ao ano fiscal anterior!)
    
    - maio/2025 → T1 → Ano Fiscal 2025
    - agosto/2025 → T2 → Ano Fiscal 2025
    """
    if data.month >= 3:  # março a dezembro
        return data.year  # O ano fiscal é o próprio ano calendário
    else:  # janeiro a fevereiro
        return data.year - 1  # Jan/Fev pertencem ao ano fiscal ANTERIOR

def _infer_quarter_mar_fev(data: pd.Timestamp) -> str:
    """
    Infere o trimestre para empresas com ano fiscal mar-fev baseado no mês.
    
    Mapeamento:
    - Março, Abril, Maio (mês 3,4,5) → T1
    - Junho, Julho, Agosto (mês 6,7,8) → T2
    - Setembro, Outubro, Novembro (mês 9,10,11) → T3
    - Dezembro, Janeiro, Fevereiro (mês 12,1,2) → T4
    """
    month = data.month
    if month in (3, 4, 5):
        return "T1"
    elif month in (6, 7, 8):
        return "T2"
    elif month in (9, 10, 11):
        return "T3"
    else:  # 12, 1, 2
        return "T4"

# ======================================================================================
# UTILITÁRIOS
# ======================================================================================

def _to_datetime(df: pd.DataFrame, col: str = "data_fim") -> pd.Series:
    return pd.to_datetime(df[col], errors="coerce")


def _ensure_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype(float)


def _quarter_order(q: str) -> int:
    return {"T1": 1, "T2": 2, "T3": 3, "T4": 4}.get(q, 99)


def _normalize_value(v: float, decimals: int = 3) -> float:
    """
    Normaliza valor numérico para evitar erros de ponto flutuante.
    
    Regras:
    - Arredonda para 'decimals' casas decimais
    - Valores muito pequenos (EPS): mantém precisão adequada
    - NaN permanece NaN
    """
    if not np.isfinite(v):
        return np.nan
    return round(float(v), decimals)
    

def _carregar_acoes_por_ano(self, pasta_ticker: Path) -> Dict[int, int]:
    """
    Carrega quantidade de ações por ano do arquivo acoes_historico.csv.
    
    Arquivo esperado:
        especie,2021T4,2022T4,2023T4,2024T4
        ON,248517120,293183802,293380126,293472126
        TOTAL,248517120,293183802,293380126,293472126
    
    Retorna:
        Dict {ano: quantidade_total}
        Exemplo: {2021: 248517120, 2022: 293183802, ...}
    
    IMPORTANTE:
    - Usa linha TOTAL (soma de todas as classes)
    - Extrai ano de cada coluna (2021T4 → 2021)
    - Retorna dict para acesso rápido por ano
    """
    arquivo = pasta_ticker / "acoes_historico.csv"
    
    if not arquivo.exists():
        return {}
    
    try:
        df = pd.read_csv(arquivo, encoding="utf-8-sig")
        
        # Verificar estrutura
        if df.empty or "especie" not in df.columns:
            # Tentar com nome antigo
            if "Espécie_Acao" in df.columns:
                df = df.rename(columns={"Espécie_Acao": "especie"})
            else:
                return {}
        
        # Pegar linha TOTAL
        linha_total = df[df["especie"].str.upper() == "TOTAL"]
        
        if linha_total.empty:
            # Fallback: usar linha ON se não tem TOTAL
            linha_total = df[df["especie"].str.upper() == "ON"]
        
        if linha_total.empty:
            return {}
        
        # Extrair quantidade por ano
        acoes_por_ano = {}
        
        for col in df.columns:
            if col == "especie":
                continue
            
            # Extrair ano da coluna (ex: "2021T4" → 2021)
            try:
                ano = int(col[:4])
                qtd = int(linha_total[col].iloc[0])
                
                if qtd > 0:
                    acoes_por_ano[ano] = qtd
            except (ValueError, IndexError, TypeError):
                continue
        
        return acoes_por_ano
    
    except Exception as e:
        print(f"    ⚠️ Erro ao carregar ações: {e}")
        return {}


def _get_acoes_com_fallback(self, ano: int, acoes_por_ano: Dict[int, int]) -> Optional[int]:
    """
    Obtém quantidade de ações para um ano com fallback para anos anteriores.
    
    Lógica:
    1. Tenta ano exato (ex: 2025)
    2. Se não existe, tenta 2024, 2023, 2022, ...
    3. Busca até 10 anos no passado
    4. Se não encontrar nada, retorna None
    
    Args:
        ano: Ano desejado
        acoes_por_ano: Dict {ano: quantidade}
    
    Returns:
        Quantidade de ações ou None
    
    Exemplo:
        acoes_por_ano = {2021: 248M, 2022: 293M, 2023: 293M, 2024: 293M}
        _get_acoes_com_fallback(2025, acoes_por_ano) → 293M (usa 2024)
    """
    if not acoes_por_ano:
        return None
    
    # Tentar ano exato
    if ano in acoes_por_ano:
        return acoes_por_ano[ano]
    
    # Fallback: tentar anos anteriores (até 10 anos no passado)
    for ano_fallback in range(ano - 1, ano - 11, -1):
        if ano_fallback in acoes_por_ano:
            return acoes_por_ano[ano_fallback]
    
    # Último recurso: pegar qualquer ano disponível (mais recente)
    if acoes_por_ano:
        ano_mais_recente = max(acoes_por_ano.keys())
        return acoes_por_ano[ano_mais_recente]
    
    return None


def _calcular_lpa_quando_zerado(
    self, 
    df_horizontal: pd.DataFrame, 
    pasta_ticker: Path
) -> Tuple[pd.DataFrame, int]:
    """
    Calcula Lucro Por Ação (LPA) quando linha 3.99 está zerada.
    
    Fórmula:
        LPA = Lucro Líquido (3.11) ÷ Quantidade de Ações
    
    Regras:
    1. Apenas calcula se 3.99 existir no DataFrame
    2. Apenas substitui valores que sejam 0 ou NaN
    3. Usa quantidade de ações do arquivo acoes_historico.csv
    4. Aplica fallback para anos sem dados de ações
    5. Arredonda para 8 casas decimais (precisão adequada para LPA)
    
    Args:
        df_horizontal: DataFrame com DRE padronizado (formato horizontal)
        pasta_ticker: Path da pasta do ticker (para acessar acoes_historico.csv)
    
    Returns:
        (DataFrame atualizado, quantidade de períodos calculados)
    
    Exemplo:
        Entrada:  3.99 = [0, 0, 0, 0.4648]
                  3.11 = [94566, 22926, 59407, 136181] (milhares)
                  Ações = 248.517.120
        
        Saída:    3.99 = [0.3804, 0.0922, 0.2390, 0.4648]
                         ↑ calculado ↑ mantido original
    """
    df = df_horizontal.copy()
    
    # Verificar se linha 3.99 existe
    idx_lpa = df[df["cd_conta"] == EPS_CODE].index
    idx_ll = df[df["cd_conta"] == "3.11"].index
    
    if len(idx_lpa) == 0 or len(idx_ll) == 0:
        return df, 0
    
    idx_lpa = idx_lpa[0]
    idx_ll = idx_ll[0]
    
    # Carregar quantidade de ações por ano
    acoes_por_ano = self._carregar_acoes_por_ano(pasta_ticker)
    
    if not acoes_por_ano:
        return df, 0
    
    # Colunas de períodos (ex: 2021T1, 2021T2, ...)
    colunas_periodos = [c for c in df.columns if c not in ["cd_conta", "ds_conta"]]
    
    if not colunas_periodos:
        return df, 0
    
    # Processar cada período
    periodos_calculados = 0
    
    for col in colunas_periodos:
        # Extrair ano da coluna (ex: "2021T1" → 2021)
        try:
            ano = int(col[:4])
        except (ValueError, TypeError):
            continue
        
        # Verificar se LPA está zerado/vazio
        lpa_atual = df.at[idx_lpa, col]
        
        if pd.notna(lpa_atual) and lpa_atual != 0:
            continue  # Já tem valor, manter original
        
        # Obter lucro líquido (em milhares)
        lucro_liquido_mil = df.at[idx_ll, col]
        
        if pd.isna(lucro_liquido_mil):
            continue  # Sem lucro líquido, não pode calcular
        
        # Obter quantidade de ações do ano (com fallback)
        qtd_acoes = self._get_acoes_com_fallback(ano, acoes_por_ano)
        
        if qtd_acoes is None or qtd_acoes == 0:
            continue  # Sem dados de ações, não pode calcular
        
        # CÁLCULO DO LPA
        # Lucro Líquido está em MILHARES (exemplo: 94.566)
        # Quantidade de Ações está em UNIDADES (exemplo: 248.517.120)
        # LPA = (Lucro em milhares × 1000) ÷ Quantidade de Ações
        
        lucro_liquido_reais = float(lucro_liquido_mil) * 1000  # Converter para reais
        lpa_calculado = lucro_liquido_reais / float(qtd_acoes)
        
        # Arredondar para 8 casas decimais (precisão adequada)
        lpa_final = round(lpa_calculado, 8)
        
        # Atualizar DataFrame
        df.at[idx_lpa, col] = lpa_final
        periodos_calculados += 1
    
    return df, periodos_calculados



def _validate_account_sign(code: str, value: float) -> float:
    """
    Valida e corrige sinais de contas baseado em regras contábeis.
    
    REGRAS:
    - Receitas (3.01, 3.06.01): devem ser POSITIVAS
    - Custos/Despesas (3.02, 3.04, 3.06.02): devem ser NEGATIVOS
    - Lucros: podem ser positivos ou negativos (prejuízo)
    
    Returns:
        Valor com sinal correto
    """
    if pd.isna(value) or value == 0:
        return value
    
    # Contas que DEVEM ser positivas
    DEVE_SER_POSITIVO = [
        "3.01",      # Receita
        "3.03",      # Resultado Bruto
        "3.06.01",   # Receitas Financeiras
        "3.09",      # Lucro Operacional Continuado
        "3.11"       # Lucro Líquido
    ]
    
    # Contas que DEVEM ser negativas
    DEVE_SER_NEGATIVO = [
        "3.02",      # Custo dos Bens Vendidos
        "3.04",      # Despesas Operacionais
        "3.04.02",   # Despesas Administrativas
        "3.04.05",   # Outras Despesas
        "3.06.02",   # Despesas Financeiras
        "3.08"       # IR/CSLL
    ]
    
    # Aplicar correção se necessário
    if code in DEVE_SER_POSITIVO and value < 0:
        print(f"    ⚠️ Invertendo sinal de {code}: {value} → {-value}")
        return -value
    
    if code in DEVE_SER_NEGATIVO and value > 0:
        print(f"    ⚠️ Invertendo sinal de {code}: {value} → {-value}")
        return -value
    
    return value



def _pick_value_for_base_code(group: pd.DataFrame, base_code: str) -> float:
    """Extrai valor para um código base, buscando conta exata ou somando filhas."""
    exact = group[group["cd_conta"] == base_code]
    if not exact.empty:
        v = _ensure_numeric(exact["valor_mil"]).sum()
        v = _validate_account_sign(base_code, float(v))  # ← ADICIONAR
        return float(v) if np.isfinite(v) else np.nan

    children = group[group["cd_conta"].astype(str).str.startswith(base_code + ".")]
    if children.empty:
        return np.nan
    v = _ensure_numeric(children["valor_mil"]).sum()
    return float(v) if np.isfinite(v) else np.nan


def _compute_eps_value(group: pd.DataFrame) -> float:
    """
    EPS:
      - usar apenas ON/PN (folhas 3.99.*.*)
      - se valores iguais => NÃO somar (retorna um)
      - se ON != PN => soma ON + PN
      - se básico vs diluído divergente => NÃO soma, pega maior |valor| (por classe)
      - se subcontas ON/PN existem mas estão zeradas, usa valor direto de 3.99
    """
    g = group.copy()
    g["cd_conta"] = g["cd_conta"].astype(str)
    g["ds_conta"] = g["ds_conta"].astype(str)

    # Valor direto de 3.99 como fallback
    direct = g[g["cd_conta"] == EPS_CODE]
    direct_val = np.nan
    if not direct.empty:
        v = _ensure_numeric(direct["valor_mil"]).sum()
        direct_val = float(v) if np.isfinite(v) else np.nan

    leaf = g[g["cd_conta"].str.startswith(EPS_CODE + ".")]
    if leaf.empty:
        return direct_val

    leaf = leaf[leaf["ds_conta"].str.upper().isin(["ON", "PN"])].copy()
    if leaf.empty:
        return direct_val

    values_by_class: Dict[str, float] = {}

    for cls in ["ON", "PN"]:
        sub = leaf[leaf["ds_conta"].str.upper() == cls]
        if sub.empty:
            continue
        vals = _ensure_numeric(sub["valor_mil"]).dropna().values.astype(float)
        if len(vals) == 0:
            continue

        uniq = np.unique(np.round(vals, 10))
        if len(uniq) == 1:
            values_by_class[cls] = float(uniq[0])
        else:
            values_by_class[cls] = float(uniq[np.argmax(np.abs(uniq))])

    if not values_by_class:
        return direct_val

    # Se todos os valores ON/PN são zero, usar o valor direto de 3.99
    all_zero = all(v == 0.0 for v in values_by_class.values())
    if all_zero and np.isfinite(direct_val) and direct_val != 0.0:
        return direct_val

    if "ON" in values_by_class and "PN" in values_by_class:
        on = values_by_class["ON"]
        pn = values_by_class["PN"]
        if np.isfinite(on) and np.isfinite(pn) and np.isclose(on, pn, rtol=1e-9, atol=1e-12):
            return float(on)
        return float(on + pn)

    return float(values_by_class.get("ON", values_by_class.get("PN", np.nan)))


# ======================================================================================
# DETECTOR DE ANO FISCAL IRREGULAR
# ======================================================================================

@dataclass
class FiscalYearInfo:
    """Informações sobre o padrão de ano fiscal da empresa."""
    is_standard: bool  # True se ano fiscal = ano calendário (jan-dez)
    fiscal_end_month: int  # Mês de encerramento fiscal (12 = padrão)
    quarters_pattern: Set[str]  # Padrão de trimestres encontrados (ex: {"T1","T2","T3","T4"})
    has_all_quarters: bool  # True se tem T1, T2, T3, T4
    description: str  # Descrição para log


def _detect_fiscal_year_pattern(df_tri: pd.DataFrame, df_anu: pd.DataFrame, ticker: str = "") -> FiscalYearInfo:
    """
    Detecta o padrão de ano fiscal da empresa de forma CIRÚRGICA.
    
    CASOS ESPECIAIS:
    - Empresas em TICKERS_ANO_FISCAL_MAR_FEV: tratamento específico (is_standard=False, mas com cálculo de T4)
    
    Critérios para ano fiscal PADRÃO (calendário):
    1. Dados anuais encerram em dezembro (mês 12)
    2. Dados trimestrais contêm T1, T2, T3, T4 para a maioria dos anos
    3. Média de pelo menos 3.5 trimestres por ano
    
    Se qualquer critério falhar => empresa tem ano fiscal IRREGULAR.
    """
    # CASO ESPECIAL: Empresas com ano fiscal março-fevereiro
    if _is_ano_fiscal_mar_fev(ticker):
        return FiscalYearInfo(
            is_standard=False,
            fiscal_end_month=2,  # Fevereiro
            quarters_pattern={"T1", "T2", "T3"},  # T4 será calculado
            has_all_quarters=False,
            description="Ano fiscal ESPECIAL mar-fev (T4 será calculado)"
        )
    
    # 1. Verificar mês de encerramento dos dados ANUAIS
    if df_anu is not None and not df_anu.empty:
        dt_anu = _to_datetime(df_anu, "data_fim").dropna()
        if not dt_anu.empty:
            anu_months = dt_anu.dt.month.value_counts()
            most_common_anu_month = int(anu_months.index[0])
        else:
            most_common_anu_month = 12
    else:
        most_common_anu_month = 12

    # 2. Verificar padrão de trimestres nos dados TRIMESTRAIS
    if df_tri is not None and not df_tri.empty:
        df_tri_copy = df_tri.copy()
        df_tri_copy["data_fim"] = _to_datetime(df_tri_copy, "data_fim")
        df_tri_copy = df_tri_copy.dropna(subset=["data_fim"])
        
        if "trimestre" in df_tri_copy.columns:
            all_quarters = set(df_tri_copy["trimestre"].dropna().unique())
        else:
            all_quarters = set()
        
        # Verificar por ano quantos trimestres existem
        df_tri_copy["ano"] = df_tri_copy["data_fim"].dt.year
        quarters_per_year = df_tri_copy.groupby("ano")["trimestre"].nunique()
        avg_quarters = quarters_per_year.mean() if len(quarters_per_year) > 0 else 0
        
    else:
        all_quarters = set()
        avg_quarters = 0

    # 3. DECISÃO: ano fiscal padrão ou irregular?
    has_all_quarters = {"T1", "T2", "T3", "T4"}.issubset(all_quarters)
    is_december_fiscal = (most_common_anu_month == 12)
    
    is_standard = is_december_fiscal
    
    # Descrição para log
    if is_standard:
        if has_all_quarters:
            description = "Ano fiscal padrão (jan-dez) com T1-T4 completos"
        else:
            description = f"Ano fiscal padrão (jan-dez) - trimestres disponíveis: {sorted(all_quarters)}"
    else:
        description = f"Ano fiscal IRREGULAR (encerramento em mês {most_common_anu_month}, trimestres: {sorted(all_quarters)})"

    return FiscalYearInfo(
        is_standard=is_standard,
        fiscal_end_month=most_common_anu_month,
        quarters_pattern=all_quarters,
        has_all_quarters=has_all_quarters,
        description=description
    )
    
def _fill_resultado_operacoes_continuadas(self, qiso: pd.DataFrame) -> pd.DataFrame:
    """
    Preenche 3.09 com 3.11 quando vazio.
    RECV3 e outras empresas reportam lucro em 3.11 mas deixam 3.09 vazio.
    """
    out = qiso.copy()
    
    has_309 = '3.09' in out['code'].values
    has_311 = '3.11' in out['code'].values
    
    if not has_311 or not has_309:
        return out
    
    new_rows = []
    
    for (ano, trimestre), g in out.groupby(['ano', 'trimestre'], sort=False):
        val_311 = g.loc[g['code'] == '3.11', 'valor'].values
        val_309 = g.loc[g['code'] == '3.09', 'valor'].values
        
        # Se 3.11 tem valor
        if len(val_311) > 0 and pd.notna(val_311[0]) and val_311[0] != 0:
            # Se 3.09 não existe ou está vazio
            if len(val_309) == 0 or pd.isna(val_309[0]) or val_309[0] == 0:
                new_rows.append({
                    'ano': ano,
                    'trimestre': trimestre,
                    'code': '3.09',
                    'valor': float(val_311[0])
                })
    
    if new_rows:
        out = out[~((out['code'] == '3.09') & (out['valor'].isna() | (out['valor'] == 0)))]
        out = pd.concat([out, pd.DataFrame(new_rows)], ignore_index=True)
    
    return out


# ======================================================================================
# PADRONIZADOR
# ======================================================================================

@dataclass
class CheckupResult:
    """Resultado do check-up linha a linha."""
    code: str
    ano: int
    soma_trimestral: float
    valor_anual: float
    diferenca: float
    percentual_diff: float
    status: str  # "OK", "DIVERGE", "SEM_ANUAL", "INCOMPLETO", "IRREGULAR_SKIP"


@dataclass
class PadronizadorDRE:
    pasta_balancos: Path = Path("balancos")
    checkup_results: List[CheckupResult] = field(default_factory=list)
    _current_ticker: str = field(default="", repr=False)  # Ticker sendo processado
    
    def _get_current_schema(self) -> List[Tuple[str, str]]:
        """Retorna o esquema DRE para o ticker atual (banco ou padrão)."""
        return _get_dre_schema(self._current_ticker)

    def _load_inputs(self, ticker: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
            pasta = get_pasta_balanco(ticker)
            tri_path = pasta / "dre_consolidado.csv"
            anu_path = pasta / "dre_anual.csv"
        
            if not tri_path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {tri_path}")
            if not anu_path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {anu_path}")
        
            df_tri = pd.read_csv(tri_path)
            df_anu = pd.read_csv(anu_path)
        
            for df in (df_tri, df_anu):
                df["cd_conta"] = df["cd_conta"].astype(str).str.strip()
                df["ds_conta"] = df["ds_conta"].astype(str).str.strip()
                df["valor_mil"] = _ensure_numeric(df["valor_mil"])
                df["data_fim"] = _to_datetime(df, "data_fim")
        
            df_tri = df_tri.dropna(subset=["data_fim"])
            df_anu = df_anu.dropna(subset=["data_fim"])
            
            # ADAPTAÇÃO: Para empresas mar-fev com trimestre vazio, inferir do mês
            if _is_ano_fiscal_mar_fev(ticker):
                # Verificar se coluna trimestre está vazia ou ausente
                if "trimestre" not in df_tri.columns:
                    df_tri["trimestre"] = ""
                
                # Preencher trimestres vazios baseado no mês
                mask_vazio = df_tri["trimestre"].isna() | (df_tri["trimestre"].astype(str).str.strip() == "")
                if mask_vazio.any():
                    df_tri.loc[mask_vazio, "trimestre"] = df_tri.loc[mask_vazio, "data_fim"].apply(_infer_quarter_mar_fev)
        
            return df_tri, df_anu

    def _build_quarter_totals(self, df_tri: pd.DataFrame) -> pd.DataFrame:
            """
            Constrói totais trimestrais preservando trimestres originais.
            
            IMPORTANTE: Para empresas com ano fiscal mar-fev, usa ano fiscal
            (não ano calendário) para agrupar corretamente.
            """
            dre_schema = self._get_current_schema()
            target_codes = [c for c, _ in dre_schema]
            wanted_prefixes = tuple([c + "." for c in target_codes] + [EPS_CODE + "."])
    
            mask = (
                df_tri["cd_conta"].isin(target_codes + [EPS_CODE])
                | df_tri["cd_conta"].astype(str).str.startswith(wanted_prefixes)
            )
            df = df_tri[mask].copy()
            
            # ADAPTAÇÃO: Para empresas mar-fev, usar ano fiscal
            if _is_ano_fiscal_mar_fev(self._current_ticker):
                df["ano"] = df["data_fim"].apply(_get_fiscal_year_mar_fev)
            else:
                df["ano"] = df["data_fim"].dt.year
            
            rows = []
            for (ano, trimestre), g in df.groupby(["ano", "trimestre"], sort=False):
                for code, _name in dre_schema:
                    v = _pick_value_for_base_code(g, code)
                    rows.append((int(ano), str(trimestre), code, v))
                rows.append((int(ano), str(trimestre), EPS_CODE, _compute_eps_value(g)))
    
            return pd.DataFrame(rows, columns=["ano", "trimestre", "code", "valor"])

    def _filter_empty_quarters(qtot: pd.DataFrame, threshold: float = 0.01) -> pd.DataFrame:
        """
        Remove trimestres completamente zerados ou com valores insignificantes.
        
        Critério: Se TODAS as contas principais têm |valor| < threshold (milhares),
        o trimestre é considerado vazio e removido.
        
        Exemplo: 2021T1 da RECV3 (todas contas = 0.0) seria removido.
        """
        main_accounts = ["3.01", "3.03", "3.11"]  # Receita, Lucro Bruto, Lucro Líquido
        
        quarters_to_remove = []
        
        for (ano, trimestre), g in qtot.groupby(['ano', 'trimestre'], sort=False):
            main_values = g[g['code'].isin(main_accounts)]['valor'].abs()
            
            # Se TODOS os valores principais são zero/insignificantes
            if (main_values < threshold).all():
                quarters_to_remove.append((ano, trimestre))
        
        if quarters_to_remove:
            print(f"  ℹ️  Removendo trimestres zerados: {quarters_to_remove}")
            mask = ~qtot.apply(lambda x: (x['ano'], x['trimestre']) in quarters_to_remove, axis=1)
            return qtot[mask]
        
        return qtot


    

    def _extract_annual_values(self, df_anu: pd.DataFrame) -> pd.DataFrame:
            """
            Extrai valores anuais para comparação no check-up, incluindo EPS.
            
            IMPORTANTE: Para empresas com ano fiscal mar-fev, usa ano fiscal.
            """
            dre_schema = self._get_current_schema()
            target_codes = [c for c, _ in dre_schema]
            wanted_prefixes = tuple([c + "." for c in target_codes] + [EPS_CODE + "."])
    
            mask = (
                df_anu["cd_conta"].isin(target_codes + [EPS_CODE])
                | df_anu["cd_conta"].astype(str).str.startswith(wanted_prefixes)
            )
            df = df_anu[mask].copy()
            
            # ADAPTAÇÃO: Para empresas mar-fev, usar ano fiscal
            if _is_ano_fiscal_mar_fev(self._current_ticker):
                df["ano"] = df["data_fim"].apply(_get_fiscal_year_mar_fev)
            else:
                df["ano"] = df["data_fim"].dt.year
    
            rows = []
            for ano, g in df.groupby("ano", sort=False):
                for code, _name in dre_schema:
                    v = _pick_value_for_base_code(g, code)
                    rows.append((int(ano), code, v))
                # Incluir EPS anual
                eps_val = _compute_eps_value(g)
                rows.append((int(ano), EPS_CODE, eps_val))
    
            return pd.DataFrame(rows, columns=["ano", "code", "anual_val"])

    def _detect_cumulative_years(
        self,
        qtot: pd.DataFrame,
        anual: pd.DataFrame,
        fiscal_info: FiscalYearInfo,
        base_code_for_detection: str = "3.01",
        ratio_threshold: float = 1.10,
    ) -> Dict[int, bool]:
        """
        Detecta se o trimestral está acumulado (YTD) por ano usando 3.01.
        
        IMPORTANTE: Só faz sentido para empresas com ano fiscal PADRÃO.
        Para empresas irregulares, retorna dict vazio (não tenta converter).
        """
        # Para ano fiscal irregular, não tenta detectar acumulado
        if not fiscal_info.is_standard:
            return {}
        
        anual_map = anual.set_index(["ano", "code"])["anual_val"].to_dict()
        out: Dict[int, bool] = {}

        for ano, g in qtot[qtot["code"] == base_code_for_detection].groupby("ano"):
            a = anual_map.get((int(ano), base_code_for_detection), np.nan)
            if not np.isfinite(a) or a == 0:
                continue
            s = float(np.nansum(g["valor"].values))
            out[int(ano)] = bool(np.isfinite(s) and abs(s) > abs(a) * ratio_threshold)

        return out

    def _to_isolated_quarters(
        self, 
        qtot: pd.DataFrame, 
        cumulative_years: Dict[int, bool],
        fiscal_info: FiscalYearInfo
    ) -> pd.DataFrame:
        """
        Converte dados acumulados (YTD) para trimestres isolados quando necessário.
        
        Para empresas com ano fiscal IRREGULAR: preserva valores originais.
        """
        out_rows = []

        for (ano, code), g in qtot.groupby(["ano", "code"], sort=False):
            g = g.copy()
            g["qord"] = g["trimestre"].apply(_quarter_order)
            g = g.sort_values("qord")

            vals = g["valor"].values.astype(float)
            qs = g["trimestre"].tolist()

            # Só converte se:
            # 1. Ano detectado como acumulado
            # 2. Não é EPS (EPS nunca é acumulado)
            # 3. Empresa tem ano fiscal padrão
            if (cumulative_years.get(int(ano), False) and 
                code != EPS_CODE and 
                fiscal_info.is_standard):
                qords = g["qord"].values
                # só converte se for sequência contínua (1,2,3... ou 1,2,3,4)
                if len(qords) >= 2 and np.array_equal(qords, np.arange(1, len(qords) + 1)):
                    iso = []
                    prev = None
                    for v in vals:
                        iso.append(v if prev is None else (v - prev))
                        prev = v
                    vals = np.array(iso, dtype=float)

            for tq, v in zip(qs, vals):
                out_rows.append((int(ano), tq, code, float(v) if np.isfinite(v) else np.nan))

        return pd.DataFrame(out_rows, columns=["ano", "trimestre", "code", "valor"])

    def _add_t4_from_annual_when_missing(
            self, 
            qiso: pd.DataFrame, 
            anual: pd.DataFrame,
            fiscal_info: FiscalYearInfo
        ) -> pd.DataFrame:
            """
            Adiciona T4 calculado quando faltante.
            
            CASOS:
            1. Ano fiscal PADRÃO (jan-dez): T4 = Anual - (T1 + T2 + T3)
            2. Ano fiscal MAR-FEV (CAML3 etc.): T4 = Anual - (T1 + T2 + T3) usando ano fiscal
            3. Outros irregulares: NÃO adiciona trimestres artificiais
            
            REGRA: T4 = Anual - (T1 + T2 + T3) para TODAS as contas, incluindo EPS.
            """
            # CASO 1: Ano fiscal padrão - comportamento original
            # CASO 2: Ano fiscal mar-fev - permite cálculo de T4
            # CASO 3: Outros irregulares - não cria T4
            
            is_mar_fev = _is_ano_fiscal_mar_fev(self._current_ticker)
            
            if not fiscal_info.is_standard and not is_mar_fev:
                # Outros irregulares: não criar trimestres artificiais
                return qiso
            
            dre_schema = self._get_current_schema()
            anual_map = anual.set_index(["ano", "code"])["anual_val"].to_dict()
            out = qiso.copy()
    
            # Lista completa de códigos: DRE + EPS
            all_codes = [c for c, _ in dre_schema] + [EPS_CODE]
    
            for ano in sorted(out["ano"].unique()):
                g = out[out["ano"] == ano]
                quarters = set(g["trimestre"].unique())
    
                if "T4" in quarters:
                    continue
                if not {"T1", "T2", "T3"}.issubset(quarters):
                    continue
    
                new_rows = []
                for code in all_codes:
                    a = anual_map.get((int(ano), code), np.nan)
                    if not np.isfinite(a):
                        continue
                    s = g[(g["code"] == code) & (g["trimestre"].isin(["T1", "T2", "T3"]))]["valor"].sum(skipna=True)
                    t4_val = float(a - s)
                    
                    # Para EPS: normalizar valores com escala errada
                    if code == EPS_CODE and np.isfinite(t4_val):
                        if abs(t4_val) > 100:
                            t4_val = t4_val / 1000.0
                    
                    new_rows.append((int(ano), "T4", code, t4_val))
    
                if new_rows:
                    out = pd.concat([out, pd.DataFrame(new_rows, columns=out.columns)], ignore_index=True)
    
            return out

    def _fill_lucro_liquido_banco(self, qiso: pd.DataFrame) -> pd.DataFrame:
        """
        Para bancos: preenche 3.11 (Lucro Líquido) com valor de 3.09 quando vazio.
        
        PROBLEMA: DRE de bancos tem Lucro Líquido em 3.09, mas o esquema padrão
        espera em 3.11 para cálculo de múltiplos.
        
        SOLUÇÃO: Copiar 3.09 → 3.11 quando 3.11 estiver vazio/NaN.
        """
        if not _is_banco(self._current_ticker):
            return qiso
        
        out = qiso.copy()
        
        # Verificar se 3.11 existe no DataFrame
        has_311 = '3.11' in out['code'].values
        has_309 = '3.09' in out['code'].values
        
        if not has_309:
            return out
        
        # Para cada combinação (ano, trimestre), verificar e copiar
        new_rows = []
        
        for (ano, trimestre), g in out.groupby(['ano', 'trimestre'], sort=False):
            val_309 = g.loc[g['code'] == '3.09', 'valor'].values
            val_311 = g.loc[g['code'] == '3.11', 'valor'].values
            
            # Se 3.09 tem valor
            if len(val_309) > 0 and pd.notna(val_309[0]) and val_309[0] != 0:
                # Se 3.11 não existe ou está vazio
                if len(val_311) == 0 or pd.isna(val_311[0]) or val_311[0] == 0:
                    new_rows.append({
                        'ano': ano,
                        'trimestre': trimestre,
                        'code': '3.11',
                        'valor': float(val_309[0])
                    })
        
        if new_rows:
            # Remover linhas 3.11 vazias existentes
            out = out[~((out['code'] == '3.11') & (out['valor'].isna() | (out['valor'] == 0)))]
            # Adicionar novas linhas com valores de 3.09
            out = pd.concat([out, pd.DataFrame(new_rows)], ignore_index=True)
        
        return out    
    

    def _build_horizontal(self, qiso: pd.DataFrame) -> pd.DataFrame:
        """
        Constrói tabela horizontal (períodos como colunas).
        Aplica normalização de valores para evitar erros de ponto flutuante.
        Usa esquema DRE correto (banco ou padrão) baseado no ticker.
        """
        dre_schema = self._get_current_schema()
        
        periods = (
            qiso[["ano", "trimestre"]]
            .drop_duplicates()
            .assign(qord=lambda x: x["trimestre"].apply(_quarter_order))
            .sort_values(["ano", "qord"])
        )

        col_labels = [f"{int(r.ano)}{r.trimestre}" for r in periods.itertuples(index=False)]
        ordered_cols = [(int(r.ano), r.trimestre) for r in periods.itertuples(index=False)]

        pivot = qiso.pivot_table(
            index="code",
            columns=["ano", "trimestre"],
            values="valor",
            aggfunc="first",
        ).reindex(columns=ordered_cols)

        idx_codes = [c for c, _ in dre_schema] + [EPS_CODE]
        pivot = pivot.reindex(idx_codes)
        pivot.columns = col_labels

        # Normalizar valores numéricos para evitar erros de ponto flutuante
        # EPS usa 8 casas decimais, demais usam 3 casas
        for col in col_labels:
            for idx in pivot.index:
                val = pivot.at[idx, col]
                if pd.notna(val):
                    decimals = 8 if idx == EPS_CODE else 3
                    pivot.at[idx, col] = _normalize_value(float(val), decimals)

        names = {c: n for c, n in dre_schema}
        names[EPS_CODE] = EPS_LABEL
        
        # Inserir código e nome da conta como colunas separadas
        # cd_conta como string para preservar formatação (ex: 3.10 não virar 3.1)
        pivot.insert(0, "ds_conta", [names.get(c, '') for c in pivot.index])
        pivot.insert(0, "cd_conta", [str(c) for c in pivot.index])

        return pivot.reset_index(drop=True)

    def _validar_sinais_pos_processamento(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Valida e corrige sinais de contas APÓS construir tabela horizontal.
        
        OBJETIVO: Corrigir valores que escaparam da validação inicial em _pick_value_for_base_code.
        
        CONTAS VALIDADAS:
        - 3.01 (Receita): deve ser POSITIVO
        - 3.06.01 (Receitas Financeiras): deve ser POSITIVO
        - 3.06.02 (Despesas Financeiras): deve ser NEGATIVO
        - 3.04 (Despesas Operacionais): deve ser NEGATIVO
        - 3.04.02 (Despesas Administrativas): deve ser NEGATIVO
        - 3.04.05 (Outras Despesas): deve ser NEGATIVO
        - 3.08 (IR/CSLL): deve ser NEGATIVO
        
        Args:
            df: DataFrame horizontal (cd_conta, ds_conta, períodos)
        
        Returns:
            DataFrame com sinais corrigidos
        """
        df = df.copy()
        
        # Dicionário: {conta: sinal_esperado}
        contas_validar = {
            "3.01": "positivo",      # Receita de Vendas
            "3.06.01": "positivo",   # Receitas Financeiras
            "3.06.02": "negativo",   # Despesas Financeiras
            "3.04": "negativo",      # Despesas/Receitas Operacionais
            "3.04.02": "negativo",   # Despesas Administrativas
            "3.04.05": "negativo",   # Outras Despesas Operacionais
            "3.08": "negativo"       # IR/CSLL
        }
        
        # Colunas de períodos (ignorar cd_conta e ds_conta)
        colunas_periodos = [c for c in df.columns if c not in ["cd_conta", "ds_conta"]]
        
        if not colunas_periodos:
            return df
        
        # Iterar sobre cada conta que precisa validação
        for idx, row in df.iterrows():
            cd_conta = str(row["cd_conta"])
            
            if cd_conta not in contas_validar:
                continue
            
            sinal_esperado = contas_validar[cd_conta]
            
            # Validar cada período
            for col in colunas_periodos:
                valor = row[col]
                
                # Pular valores nulos ou zeros
                if pd.isna(valor) or valor == 0:
                    continue
                
                # Aplicar correção se necessário
                if sinal_esperado == "positivo" and valor < 0:
                    df.at[idx, col] = -valor
                    print(f"    🔧 Corrigindo {cd_conta} ({col}): {valor} → {-valor}")
                
                elif sinal_esperado == "negativo" and valor > 0:
                    df.at[idx, col] = -valor
                    print(f"    🔧 Corrigindo {cd_conta} ({col}): {valor} → {-valor}")
        
        return df
    

    def _carregar_acoes_por_ano(self, pasta_ticker: Path) -> Dict[int, int]:
        """
        Carrega quantidade de ações por ano do arquivo acoes_historico.csv.
        """
        arquivo = pasta_ticker / "acoes_historico.csv"
        
        if not arquivo.exists():
            return {}
        
        try:
            df = pd.read_csv(arquivo, encoding="utf-8-sig")
            
            # Verificar estrutura
            if df.empty or "especie" not in df.columns:
                if "Espécie_Acao" in df.columns:
                    df = df.rename(columns={"Espécie_Acao": "especie"})
                else:
                    return {}
            
            # Pegar linha TOTAL
            linha_total = df[df["especie"].str.upper() == "TOTAL"]
            
            if linha_total.empty:
                linha_total = df[df["especie"].str.upper() == "ON"]
            
            if linha_total.empty:
                return {}
            
            # Extrair quantidade por ano
            acoes_por_ano = {}
            
            for col in df.columns:
                if col == "especie":
                    continue
                
                try:
                    ano = int(col[:4])
                    qtd = int(linha_total[col].iloc[0])
                    
                    if qtd > 0:
                        acoes_por_ano[ano] = qtd
                except (ValueError, IndexError, TypeError):
                    continue
            
            return acoes_por_ano
        
        except Exception as e:
            print(f"    ⚠️ Erro ao carregar ações: {e}")
            return {}
    
    def _get_acoes_com_fallback(self, ano: int, acoes_por_ano: Dict[int, int]) -> Optional[int]:
        """
        Obtém quantidade de ações para um ano com fallback para anos anteriores.
        """
        if not acoes_por_ano:
            return None
        
        # Tentar ano exato
        if ano in acoes_por_ano:
            return acoes_por_ano[ano]
        
        # Fallback: tentar anos anteriores
        for ano_fallback in range(ano - 1, ano - 11, -1):
            if ano_fallback in acoes_por_ano:
                return acoes_por_ano[ano_fallback]
        
        # Último recurso: pegar ano mais recente
        if acoes_por_ano:
            ano_mais_recente = max(acoes_por_ano.keys())
            return acoes_por_ano[ano_mais_recente]
        
        return None
    
    def _calcular_lpa_quando_zerado(
        self, 
        df_horizontal: pd.DataFrame, 
        pasta_ticker: Path
    ) -> Tuple[pd.DataFrame, int]:
        """
        Calcula Lucro Por Ação (LPA) quando linha 3.99 está zerada.
        """
        df = df_horizontal.copy()
        
        # Verificar se linha 3.99 existe
        idx_lpa = df[df["cd_conta"] == EPS_CODE].index
        idx_ll = df[df["cd_conta"] == "3.11"].index
        
        if len(idx_lpa) == 0 or len(idx_ll) == 0:
            return df, 0
        
        idx_lpa = idx_lpa[0]
        idx_ll = idx_ll[0]
        
        # Carregar quantidade de ações por ano
        acoes_por_ano = self._carregar_acoes_por_ano(pasta_ticker)
        
        if not acoes_por_ano:
            return df, 0
        
        # Colunas de períodos
        colunas_periodos = [c for c in df.columns if c not in ["cd_conta", "ds_conta"]]
        
        if not colunas_periodos:
            return df, 0
        
        # Processar cada período
        periodos_calculados = 0
        
        for col in colunas_periodos:
            try:
                ano = int(col[:4])
            except (ValueError, TypeError):
                continue
            
            # Verificar se LPA está zerado/vazio
            lpa_atual = df.at[idx_lpa, col]
            
            if pd.notna(lpa_atual) and lpa_atual != 0:
                continue
            
            # Obter lucro líquido (em milhares)
            lucro_liquido_mil = df.at[idx_ll, col]
            
            if pd.isna(lucro_liquido_mil):
                continue
            
            # Obter quantidade de ações do ano (com fallback)
            qtd_acoes = self._get_acoes_com_fallback(ano, acoes_por_ano)
            
            if qtd_acoes is None or qtd_acoes == 0:
                continue
            
            # CÁLCULO DO LPA
            lucro_liquido_reais = float(lucro_liquido_mil) * 1000
            lpa_calculado = lucro_liquido_reais / float(qtd_acoes)
            lpa_final = round(lpa_calculado, 8)
            
            # Atualizar DataFrame
            df.at[idx_lpa, col] = lpa_final
            periodos_calculados += 1
        
        return df, periodos_calculados
    

    def _checkup_linha_a_linha(
            self, 
            qiso: pd.DataFrame, 
            anual: pd.DataFrame,
            fiscal_info: FiscalYearInfo,
            tolerancia_percentual: float = 0.1  # 0.1% de tolerância
        ) -> Tuple[List[CheckupResult], int, int, int, int]:
            """
            Realiza check-up LINHA A LINHA comparando soma trimestral vs anual.
            
            CASOS:
            1. Ano fiscal PADRÃO: check-up normal
            2. Ano fiscal MAR-FEV: check-up normal (já com ano fiscal correto)
            3. Outros IRREGULAR: check-up é PULADO
            """
            dre_schema = self._get_current_schema()
            results: List[CheckupResult] = []
            
            diverge_count = 0
            incompleto_count = 0
            sem_anual_count = 0
            irregular_skip_count = 0
    
            is_mar_fev = _is_ano_fiscal_mar_fev(self._current_ticker)
    
            # Para empresas com ano fiscal IRREGULAR (exceto mar-fev): pular check-up
            if not fiscal_info.is_standard and not is_mar_fev:
                for ano in sorted(qiso["ano"].unique()):
                    for code, _name in dre_schema:
                        g_code = qiso[(qiso["ano"] == ano) & (qiso["code"] == code)]
                        soma_tri = float(g_code["valor"].sum(skipna=True))
                        
                        results.append(CheckupResult(
                            code=code,
                            ano=int(ano),
                            soma_trimestral=soma_tri,
                            valor_anual=np.nan,
                            diferenca=np.nan,
                            percentual_diff=np.nan,
                            status="IRREGULAR_SKIP"
                        ))
                        irregular_skip_count += 1
                
                return results, diverge_count, incompleto_count, sem_anual_count, irregular_skip_count
    
            # Para empresas com ano fiscal PADRÃO ou MAR-FEV: fazer check-up normal
            anual_map = anual.set_index(["ano", "code"])["anual_val"].to_dict()
            expected_quarters = {"T1", "T2", "T3", "T4"}
    
            for ano in sorted(qiso["ano"].unique()):
                g_ano = qiso[qiso["ano"] == ano]
                quarters_present = set(g_ano["trimestre"].unique())
                
                for code, _name in dre_schema:
                    anual_val = anual_map.get((int(ano), code), np.nan)
                    
                    # Soma trimestral
                    g_code = g_ano[g_ano["code"] == code]
                    soma_tri = float(g_code["valor"].sum(skipna=True))
                    
                    # Determinar status
                    if not np.isfinite(anual_val):
                        status = "SEM_ANUAL"
                        sem_anual_count += 1
                        diferenca = np.nan
                        percentual = np.nan
                    elif not expected_quarters.issubset(quarters_present):
                        status = "INCOMPLETO"
                        incompleto_count += 1
                        diferenca = soma_tri - anual_val
                        percentual = (diferenca / abs(anual_val) * 100) if anual_val != 0 else np.nan
                    else:
                        diferenca = soma_tri - anual_val
                        percentual = (diferenca / abs(anual_val) * 100) if anual_val != 0 else 0.0
                        
                        # Verificar tolerância
                        if abs(percentual) <= tolerancia_percentual:
                            status = "OK"
                        else:
                            status = "DIVERGE"
                            diverge_count += 1
                    
                    results.append(CheckupResult(
                        code=code,
                        ano=int(ano),
                        soma_trimestral=soma_tri,
                        valor_anual=anual_val,
                        diferenca=diferenca,
                        percentual_diff=percentual,
                        status=status
                    ))
    
            return results, diverge_count, incompleto_count, sem_anual_count, irregular_skip_count

    def _generate_checkup_report(
        self, 
        results: List[CheckupResult],
        fiscal_info: FiscalYearInfo
    ) -> pd.DataFrame:
        """Gera relatório de check-up em formato DataFrame."""
        rows = []
        for r in results:
            rows.append({
                "ano": r.ano,
                "codigo": r.code,
                "soma_trimestral": r.soma_trimestral,
                "valor_anual": r.valor_anual,
                "diferenca": r.diferenca,
                "diff_%": r.percentual_diff,
                "status": r.status
            })
        
        df = pd.DataFrame(rows)
        return df

    def padronizar_e_salvar_ticker(self, ticker: str, salvar_checkup: bool = True) -> Tuple[bool, str]:
        """
        Padroniza DRE de um ticker e salva resultado.
        Agora usa get_pasta_balanco() para garantir pasta correta.
        """
        ticker = ticker.upper().strip()
        self._current_ticker = ticker
        pasta = get_pasta_balanco(ticker)
    
        # 1. Carregar dados
        df_tri, df_anu = self._load_inputs(ticker)
        
        # 2. DETECTAR PADRÃO FISCAL (CRÍTICO!)
        fiscal_info = _detect_fiscal_year_pattern(df_tri, df_anu, ticker)
        
        # 3. Construir totais trimestrais (preserva originais)
        qtot = self._build_quarter_totals(df_tri)
        
        # 4. Extrair valores anuais
        anu = self._extract_annual_values(df_anu)
        
        # 5. Detectar e converter dados acumulados (YTD) - só para padrão
        cumulative_years = self._detect_cumulative_years(qtot, anu, fiscal_info)
        qiso = self._to_isolated_quarters(qtot, cumulative_years, fiscal_info)
    
        # 6. Adicionar T4 quando faltante (APENAS para ano fiscal padrão)
        qiso = self._add_t4_from_annual_when_missing(qiso, anu, fiscal_info)
        
        # 6.1 BANCOS: Copiar 3.09 → 3.11 (Lucro Líquido)
        qiso = self._fill_lucro_liquido_banco(qiso)

        # 6.2 NÃO-FINANCEIRAS: Copiar 3.11 → 3.09 quando vazio
        qiso = self._fill_resultado_operacoes_continuadas(qiso)        
        
        # 7. Ordenar
        qiso = qiso.assign(qord=qiso["trimestre"].apply(_quarter_order)).sort_values(["ano", "qord", "code"])
        qiso = qiso.drop(columns=["qord"])
        
        # 8. Construir tabela horizontal
        df_out = self._build_horizontal(qiso)

        # 8.1 VALIDAR SINAIS PÓS-PROCESSAMENTO
        df_out = self._validar_sinais_pos_processamento(df_out)
        
        # 8.2 CALCULAR LPA QUANDO ZERADO
        lpa_calculados = 0
        try:
            df_out, lpa_calculados = self._calcular_lpa_quando_zerado(df_out, pasta)
            if lpa_calculados > 0:
                print(f"  ℹ️  LPA calculado para {lpa_calculados} período(s)")
        except Exception as e:
            print(f"  ⚠️ Erro ao calcular LPA: {e}")
        
        
        # ============================================================================
        # 8.1 NOVO: CALCULAR LPA QUANDO ZERADO
        # ============================================================================
        lpa_calculados = 0
        try:
            df_out, lpa_calculados = self._calcular_lpa_quando_zerado(df_out, pasta)
            if lpa_calculados > 0:
                print(f"  ℹ️  LPA calculado para {lpa_calculados} período(s)")
        except Exception as e:
            print(f"  ⚠️ Erro ao calcular LPA: {e}")
        # ============================================================================
        
        # 9. CHECK-UP LINHA A LINHA
        checkup_results, diverge, incompleto, sem_anual, irregular_skip = self._checkup_linha_a_linha(
            qiso, anu, fiscal_info
        )
        self.checkup_results = checkup_results
        
        # 10. Salvar arquivos
        pasta.mkdir(parents=True, exist_ok=True)
        
        # Arquivo principal
        out_path = pasta / "dre_padronizado.csv"
        df_out.to_csv(out_path, index=False, encoding="utf-8")
        
        # Relatório de check-up (SEMPRE salva se solicitado)
        checkup_saved = False
        if salvar_checkup:
            try:
                checkup_df = self._generate_checkup_report(checkup_results, fiscal_info)
                checkup_path = pasta / "dre_checkup.csv"
                
                # Salvar com cabeçalho informativo
                with open(checkup_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Padrão Fiscal: {fiscal_info.description}\n")
                    f.write(f"# Trimestres encontrados: {sorted(fiscal_info.quarters_pattern)}\n")
                    f.write(f"# Data geração: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                checkup_df.to_csv(checkup_path, index=False, encoding="utf-8", mode='a')
                checkup_saved = True
            except Exception as e:
                print(f"  ⚠️ Erro ao salvar check-up: {e}")
        
        # 11. Construir mensagem de retorno
        is_mar_fev = _is_ano_fiscal_mar_fev(ticker)
        if fiscal_info.is_standard:
            fiscal_status = "PADRÃO"
        elif is_mar_fev:
            fiscal_status = "MAR-FEV"
        else:
            fiscal_status = "IRREGULAR"
        tipo_dre = "BANCO" if _is_banco(ticker) else "PADRÃO"
        
        # Para ano fiscal padrão OU mar-fev: mostrar resultados do check-up
        if fiscal_info.is_standard or is_mar_fev:
            msg_parts = [
                f"tipo={tipo_dre}",
                f"fiscal={fiscal_status}",
                f"DIVERGE={diverge}",
                f"INCOMPLETO={incompleto}",
                f"SEM_ANUAL={sem_anual}"
            ]
            ok = (diverge == 0)
        else:
            # Outros irregulares: pular check-up
            msg_parts = [
                f"tipo={tipo_dre}",
                f"fiscal={fiscal_status}",
                f"CHECK-UP=PULADO",
                f"trimestres={sorted(fiscal_info.quarters_pattern)}"
            ]
            ok = True
        
        if checkup_saved:
            msg_parts.append("checkup=SALVO")
        
        # Adicionar info de LPA calculado
        if lpa_calculados > 0:
            msg_parts.append(f"LPA={lpa_calculados}períodos")
        
        msg = f"dre_padronizado.csv | {' | '.join(msg_parts)}"
        
        return ok, msg




# ======================================================================================
# CLI
# ======================================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modo", default="quantidade", choices=["quantidade", "ticker", "lista", "faixa"])
    parser.add_argument("--quantidade", default="10")
    parser.add_argument("--ticker", default="")
    parser.add_argument("--lista", default="")
    parser.add_argument("--faixa", default="1-50")
    parser.add_argument("--no-checkup", action="store_true", help="Não salvar relatório de check-up")
    args = parser.parse_args()

    # Tentar carregar mapeamento consolidado, fallback para original
    df = load_mapeamento_consolidado()
    df = df[df["cnpj"].notna()].reset_index(drop=True)

    if args.modo == "quantidade":
        limite = int(args.quantidade)
        df_sel = df.head(limite)

    elif args.modo == "ticker":
        ticker_upper = args.ticker.upper()
        df_sel = df[df["ticker"].str.upper().str.contains(ticker_upper, case=False, na=False, regex=False)]

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

    print(f"\n>>> JOB: PADRONIZAR DRE <<<")
    print(f"Modo: {args.modo} | Selecionadas: {len(df_sel)}")
    print("Saída: balancos/<TICKER>/dre_padronizado.csv + dre_checkup.csv\n")

    pad = PadronizadorDRE()

    ok_count = 0
    warn_count = 0
    err_count = 0
    irregular_count = 0

    salvar_checkup = not args.no_checkup

    for _, row in df_sel.iterrows():
        ticker_str = str(row["ticker"]).upper().strip()
        ticker = ticker_str.split(';')[0] if ';' in ticker_str else ticker_str

        pasta = get_pasta_balanco(ticker)
        if not pasta.exists():
            err_count += 1
            print(f"❌ {ticker}: pasta {pasta} não existe (captura ausente)")
            continue

        try:
            ok, msg = pad.padronizar_e_salvar_ticker(ticker, salvar_checkup=salvar_checkup)
            
            if "IRREGULAR" in msg:
                irregular_count += 1
            
            if ok:
                ok_count += 1
                print(f"✅ {ticker}: {msg}")
            else:
                warn_count += 1
                print(f"⚠️ {ticker}: {msg}")

        except FileNotFoundError as e:
            err_count += 1
            print(f"❌ {ticker}: arquivos ausentes ({e})")
        except Exception as e:
            err_count += 1
            import traceback
            print(f"❌ {ticker}: erro ({type(e).__name__}: {e})")
            traceback.print_exc()

    print("\n" + "="*70)
    print(f"Finalizado: OK={ok_count} | WARN(DIVERGE)>0={warn_count} | ERRO={err_count}")
    if irregular_count > 0:
        print(f"            Anos fiscais irregulares: {irregular_count} (check-up pulado)")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
