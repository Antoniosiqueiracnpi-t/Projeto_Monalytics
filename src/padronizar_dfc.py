# src/padronizar_dfc.py
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple

import numpy as np
import pandas as pd

# ADICIONAR NO TOPO DO ARQUIVO (após outros imports):
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from multi_ticker_utils import get_ticker_principal, get_pasta_balanco, load_mapeamento_consolidado

# ======================================================================================
# EMPRESAS COM ANO FISCAL MARÇO-FEVEREIRO
# ======================================================================================

TICKERS_MAR_FEV: Set[str] = {
    "CAML3",  # Camil - ano fiscal mar/YYYY a fev/YYYY+1
}


def _is_mar_fev_company(ticker: str) -> bool:
    """Verifica se a empresa tem ano fiscal março-fevereiro."""
    return ticker.upper().strip() in TICKERS_MAR_FEV


def _get_fiscal_year_mar_fev(data: pd.Timestamp) -> int:
    """
    Para empresas com ano fiscal mar-fev, retorna o ano fiscal.
    
    Convenção do mercado brasileiro (Camil, Raízen, etc.):
    - Ano Fiscal 2024 = mar/2024 a fev/2025
    - Ano Fiscal 2025 = mar/2025 a fev/2026
    
    Mapeamento:
    - maio/2024 (T1) → Ano Fiscal 2024
    - agosto/2024 (T2) → Ano Fiscal 2024
    - novembro/2024 (T3) → Ano Fiscal 2024
    - fevereiro/2025 (T4) → Ano Fiscal 2024 (pertence ao AF anterior)
    
    - maio/2025 (T1) → Ano Fiscal 2025
    - agosto/2025 (T2) → Ano Fiscal 2025
    """
    if data.month >= 3:  # março a dezembro
        return data.year  # Ano fiscal = ano calendário
    else:  # janeiro a fevereiro
        return data.year - 1  # Pertence ao ano fiscal anterior


def _infer_quarter_mar_fev(data: pd.Timestamp) -> str:
    """
    Infere o trimestre fiscal para empresas com ano fiscal março-fevereiro.
    
    Mapeamento:
    - Mar/Abr/Mai → T1 (1º trimestre fiscal)
    - Jun/Jul/Ago → T2 (2º trimestre fiscal)
    - Set/Out/Nov → T3 (3º trimestre fiscal)
    - Dez/Jan/Fev → T4 (4º trimestre fiscal)
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
# CONTAS DFC - PADRÃO PARA TODAS AS EMPRESAS
# ======================================================================================

DFC_CONTAS: List[Tuple[str, str]] = [
    ("6.01", "Caixa Líquido das Atividades Operacionais"),
    ("6.02", "Caixa Líquido Atividades de Investimento"),
    ("6.03", "Caixa Líquido Atividades de Financiamento"),
    ("6.04", "Variação Cambial s/ Caixa e Equivalentes"),
    ("6.05", "Aumento (Redução) de Caixa e Equivalentes"),
]

# Código especial para Depreciação e Amortização (subconta de 6.01)
DEPREC_CODE = "6.01.DA"
DEPREC_LABEL = "Depreciação e Amortização"


# ======================================================================================
# TICKERS DE BANCOS E SEGURADORAS (NÃO incluem D&A)
# ======================================================================================

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

TICKERS_HOLDINGS_SEGUROS: Set[str] = {
    "BBSE3",
    "CXSE3",
}

TICKERS_SEGURADORAS: Set[str] = {
    "IRBR3",
    "PSSA3",
}


def _is_financeira_ou_seguradora(ticker: str) -> bool:
    """
    Verifica se o ticker é banco, holding de seguros ou seguradora.
    Essas empresas NÃO incluem Depreciação e Amortização no DFC padronizado.
    """
    t = ticker.upper().strip()
    return t in TICKERS_BANCOS or t in TICKERS_HOLDINGS_SEGUROS or t in TICKERS_SEGURADORAS


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
    """Normaliza valor numérico para evitar erros de ponto flutuante."""
    if not np.isfinite(v):
        return np.nan
    return round(float(v), decimals)


def _pick_value_for_code(group: pd.DataFrame, code: str) -> float:
    """Extrai valor para um código, buscando conta exata ou somando filhas."""
    exact = group[group["cd_conta"] == code]
    if not exact.empty:
        v = _ensure_numeric(exact["valor_mil"]).sum()
        return float(v) if np.isfinite(v) else np.nan

    children = group[group["cd_conta"].astype(str).str.startswith(code + ".")]
    if children.empty:
        return np.nan
    v = _ensure_numeric(children["valor_mil"]).sum()
    return float(v) if np.isfinite(v) else np.nan


# ======================================================================================
# EXTRAÇÃO DE DEPRECIAÇÃO E AMORTIZAÇÃO
# ======================================================================================

DEPREC_PATTERNS = [
    # Depreciação + Depleção + Amortização (TODOS OS 3 TERMOS)
    r"deprecia[çc][aã]o\s*,?\s*deple[çc][aã]o\s*(e|ou|,)\s*amortiza[çc][aã]o",
    r"deprecia[çc][aã]o\s*,?\s*amortiza[çc][aã]o\s*(e|ou|,)\s*deple[çc][aã]o",
    r"deple[çc][aã]o\s*,?\s*deprecia[çc][aã]o\s*(e|ou|,)\s*amortiza[çc][aã]o",
    r"amortiza[çc][aã]o\s*,?\s*deprecia[çc][aã]o\s*(e|ou|,)\s*deple[çc][aã]o",
    
    # Depreciação + Depleção (sem Amortização)
    r"deprecia[çc][aã]o\s*(e|ou)\s*deple[çc][aã]o",
    r"deple[çc][aã]o\s*(e|ou)\s*deprecia[çc][aã]o",
    
    # Depleção + Amortização (sem Depreciação)
    r"deple[çc][aã]o\s*(e|ou)\s*amortiza[çc][aã]o",
    r"amortiza[çc][aã]o\s*(e|ou)\s*deple[çc][aã]o",
    
    # Depleção isolada
    r"^deple[çc][oõ]es?\s*$",
    r"^deple[çc][aã]o\s*$",
    
    # Depreciação + Amortização (padrões existentes)
    r"deprecia[çc][aã]o\s*(e|ou)?\s*amortiza[çc][aã]o",
    r"amortiza[çc][aã]o\s*(e|ou)?\s*deprecia[çc][aã]o",
    
    # Depreciação + Amortização + Impairment
    r"deprecia[çc][aã]o\s*,?\s*amortiza[çc][aã]o\s*(e|ou)\s*(impairment|redução ao valor recuper[aá]vel)",
    r"deprecia[çc][aã]o\s*,?\s*(impairment|redução ao valor recuper[aá]vel)\s*(e|ou)\s*amortiza[çc][aã]o",
    r"amortiza[çc][aã]o\s*,?\s*deprecia[çc][aã]o\s*(e|ou)\s*(impairment|redução ao valor recuper[aá]vel)",
    
    # Depreciação + Impairment (sem Amortização)
    r"deprecia[çc][aã]o\s*(e|ou)\s*(impairment|redução ao valor recuper[aá]vel)",
    r"(impairment|redução ao valor recuper[aá]vel)\s*(e|ou)\s*deprecia[çc][aã]o",
    
    # Amortização + Impairment (sem Depreciação)
    r"amortiza[çc][aã]o\s*(e|ou)\s*(impairment|redução ao valor recuper[aá]vel)",
    r"(impairment|redução ao valor recuper[aá]vel)\s*(e|ou)\s*amortiza[çc][aã]o",
    
    # Somente Impairment (casos isolados)
    r"^(impairment|redução ao valor recuper[aá]vel)\s*$",
    
    # Depreciação ou Amortização isoladas (padrões existentes)
    r"^deprecia[çc][oõ]es?\s*$",
    r"^amortiza[çc][oõ]es?\s*$",
    r"^deprecia[çc][aã]o\s*$",
    r"^amortiza[çc][aã]o\s*$",
    
    # Abreviações e formatos especiais
    r"deprec\.\s*(e|ou)?\s*amort\.",
    r"d&a",
    r"deprec\s*/\s*amort",
    r"d\s*,?\s*a\s*(e|ou)?\s*i",
    r"d&a&i",
]


DEPREC_REGEX = [re.compile(p, re.IGNORECASE) for p in DEPREC_PATTERNS]


def _is_deprec_amort_account(ds_conta: str) -> bool:
    """
    Verifica se o nome da conta corresponde a Depreciação, Amortização e/ou Impairment.
    
    Captura variações como:
    - Depreciação e Amortização
    - Depreciação, Amortização e Impairment
    - Depreciação, Amortização e Redução ao Valor Recuperável
    - D&A, D&A&I, D, A e I
    """
    ds_clean = ds_conta.strip()
    for regex in DEPREC_REGEX:
        if regex.search(ds_clean):
            return True
    return False


def _compute_deprec_amort_value(group: pd.DataFrame) -> float:
    """
    Calcula o valor de Depreciação e Amortização para um período.
    """
    subcontas_601 = group[group["cd_conta"].astype(str).str.startswith("6.01.")]
    if subcontas_601.empty:
        return np.nan

    mask = subcontas_601["ds_conta"].apply(_is_deprec_amort_account)
    deprec_rows = subcontas_601[mask]
    if deprec_rows.empty:
        return np.nan

    total = _ensure_numeric(deprec_rows["valor_mil"]).sum()
    return float(total) if np.isfinite(total) else np.nan

# ======================================================================================
# DETECÇÃO AUTOMÁTICA DE ESCALA E VALIDAÇÃO
# ======================================================================================

def detectar_escala_automatica(df, coluna_valor='valor_mil'):
    """
    Detecta automaticamente a escala dos valores no DataFrame.
    
    Retorna:
        dict: {
            'divisor': float - Fator de divisão (1.0 ou 10_000_000_000),
            'justificativa': str - Razão da decisão,
            'magnitude_p50': float - Mediana da magnitude,
            'magnitude_max': float - Máxima magnitude
        }
    """
    # Filtrar valores não-zero
    valores = df[df[coluna_valor] != 0][coluna_valor].dropna()
    
    if len(valores) == 0:
        return {
            'divisor': 1.0,
            'justificativa': 'SEM_DADOS',
            'magnitude_p50': None,
            'magnitude_max': None
        }
    
    # Calcular magnitudes (log10 dos valores absolutos)
    valores_abs = valores.abs()
    mag_p50 = np.log10(valores_abs.quantile(0.50))
    mag_max = np.log10(valores_abs.max())
    
    # Lógica de detecção
    if mag_p50 > 15:
        divisor = 10_000_000_000
        justificativa = "NOTACAO_CIENTIFICA"
    elif mag_p50 < 9:
        divisor = 1.0
        justificativa = "JA_EM_MILHARES"
    elif 9 <= mag_p50 <= 15:
        if mag_max > 14:
            divisor = 10_000_000_000
            justificativa = "ZONA_CINZA_CONVERTIDO"
        else:
            divisor = 1.0
            justificativa = "ZONA_CINZA_MANTIDO"
    else:
        divisor = 1.0
        justificativa = "PADRAO"
    
    return {
        'divisor': divisor,
        'justificativa': justificativa,
        'magnitude_p50': round(mag_p50, 2),
        'magnitude_max': round(mag_max, 2)
    }


def validar_dfc_coerencia(df_periodo, periodo_str="?"):
    """
    Valida coerência do DFC para um período específico.
    Verifica se: 6.05 (Variação Caixa) = 6.01 (Operacional) + 6.02 (Investimento) + 6.03 (Financiamento) + 6.04 (Cambial)
    
    Args:
        df_periodo: DataFrame com dados de um período (já filtrado)
        periodo_str: String identificando o período (para log)
    
    Retorna:
        dict com 'valido', 'operacional', 'investimento', 'financiamento', 'cambial', 'variacao_caixa', 'calculado', 'diff', 'diff_percent'
    """
    try:
        # Buscar componentes do fluxo de caixa
        fc_oper_rows = df_periodo[df_periodo['cd_conta'] == '6.01']
        fc_oper = float(fc_oper_rows['valor_mil'].iloc[0]) if not fc_oper_rows.empty else 0.0
        
        fc_invest_rows = df_periodo[df_periodo['cd_conta'] == '6.02']
        fc_invest = float(fc_invest_rows['valor_mil'].iloc[0]) if not fc_invest_rows.empty else 0.0
        
        fc_financ_rows = df_periodo[df_periodo['cd_conta'] == '6.03']
        fc_financ = float(fc_financ_rows['valor_mil'].iloc[0]) if not fc_financ_rows.empty else 0.0
        
        fc_cambial_rows = df_periodo[df_periodo['cd_conta'] == '6.04']
        fc_cambial = float(fc_cambial_rows['valor_mil'].iloc[0]) if not fc_cambial_rows.empty else 0.0
        
        # Buscar Variação de Caixa (6.05)
        var_caixa_rows = df_periodo[df_periodo['cd_conta'] == '6.05']
        var_caixa = float(var_caixa_rows['valor_mil'].iloc[0]) if not var_caixa_rows.empty else 0.0
        
        # Calcular variação esperada
        var_calculada = fc_oper + fc_invest + fc_financ + fc_cambial
        
        # Calcular diferença
        diff = abs(var_caixa - var_calculada)
        
        # Usar maior valor absoluto como base para percentual
        base = max(abs(var_caixa), abs(var_calculada), 1.0)
        diff_percent = (diff / base * 100) if base != 0 else 0.0
        
        # Tolerância de 1%
        valido = diff_percent <= 1.0
        
        return {
            'valido': valido,
            'operacional': fc_oper,
            'investimento': fc_invest,
            'financiamento': fc_financ,
            'cambial': fc_cambial,
            'variacao_caixa': var_caixa,
            'calculado': var_calculada,
            'diff': diff,
            'diff_percent': diff_percent,
            'periodo': periodo_str
        }
        
    except Exception as e:
        return {
            'valido': False,
            'operacional': 0,
            'investimento': 0,
            'financiamento': 0,
            'cambial': 0,
            'variacao_caixa': 0,
            'calculado': 0,
            'diff': 0,
            'diff_percent': 0,
            'periodo': periodo_str,
            'erro': str(e)
        }



# ======================================================================================
# DETECTOR DE ANO FISCAL IRREGULAR
# ======================================================================================

@dataclass
class FiscalYearInfo:
    """Informações sobre o padrão de ano fiscal da empresa."""
    is_standard: bool
    fiscal_end_month: int
    quarters_pattern: Set[str]
    has_all_quarters: bool
    description: str
    is_mar_fev: bool = False  # NOVO: flag para ano fiscal março-fevereiro


def _detect_fiscal_year_pattern(df_tri: pd.DataFrame, df_anu: pd.DataFrame, ticker: str = "") -> FiscalYearInfo:
    """
    Detecta o padrão de ano fiscal da empresa.
    MODIFICADO: Detecta empresas com ano fiscal março-fevereiro.
    """
    # Verificar se é empresa mar-fev conhecida
    is_mar_fev = _is_mar_fev_company(ticker)
    
    quarters_found = set(df_tri["trimestre"].dropna().unique())

    if "data_fim" in df_anu.columns and not df_anu.empty:
        end_months = df_anu["data_fim"].dropna().dt.month.unique()
        if len(end_months) == 1 and end_months[0] == 12:
            fiscal_end = 12
            is_standard = True
        elif len(end_months) == 1 and end_months[0] == 2:
            # Ano fiscal termina em fevereiro (CAML3)
            fiscal_end = 2
            is_standard = False
            is_mar_fev = True
        elif len(end_months) >= 1:
            mode_month = df_anu["data_fim"].dt.month.mode()
            fiscal_end = int(mode_month.iloc[0]) if not mode_month.empty else 12
            is_standard = (fiscal_end == 12)
            if fiscal_end == 2:
                is_mar_fev = True
        else:
            fiscal_end = 12
            is_standard = True
    else:
        fiscal_end = 12
        is_standard = True

    has_all = {"T1", "T2", "T3", "T4"}.issubset(quarters_found)

    if is_mar_fev:
        desc = "Ano fiscal março-fevereiro (MAR-FEV)"
    elif is_standard:
        desc = "Ano fiscal padrão (jan-dez)"
    else:
        desc = f"Ano fiscal irregular (encerra em mês {fiscal_end})"

    return FiscalYearInfo(
        is_standard=is_standard,
        fiscal_end_month=fiscal_end,
        quarters_pattern=quarters_found,
        has_all_quarters=has_all,
        description=desc,
        is_mar_fev=is_mar_fev,
    )


# ======================================================================================
# CLASSE PRINCIPAL - PADRONIZADOR DFC
# ======================================================================================

@dataclass
class PadronizadorDFC:
    pasta_balancos: Path = Path("balancos")
    _current_ticker: str = field(default="", repr=False)

    def _include_deprec_amort(self) -> bool:
        """Retorna True se deve incluir D&A (empresas não-financeiras)."""
        return not _is_financeira_ou_seguradora(self._current_ticker)

    def _get_dfc_schema(self) -> List[Tuple[str, str]]:
        """Retorna o esquema DFC para o ticker atual."""
        schema = list(DFC_CONTAS)
        if self._include_deprec_amort():
            schema.insert(1, (DEPREC_CODE, DEPREC_LABEL))
        return schema

    def _load_inputs(self, ticker: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Carrega arquivos DFC trimestral e anual.
        MODIFICADO: Preenche trimestres vazios para empresas mar-fev.
        """
        pasta = get_pasta_balanco(ticker)
        tri_path = pasta / "dfc_mi_consolidado.csv"
        anu_path = pasta / "dfc_mi_anual.csv"
    
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

        # ✅ DETECÇÃO AUTOMÁTICA DE ESCALA
        escala_dfc_tri = detectar_escala_automatica(df_tri)
        escala_dfc_anu = detectar_escala_automatica(df_anu)
        
        # Usar o maior divisor detectado (mais conservador)
        divisor_dfc = max(escala_dfc_tri['divisor'], escala_dfc_anu['divisor'])
        
        # Aplicar conversão se necessário
        if divisor_dfc != 1.0:
            df_tri["valor_mil"] = df_tri["valor_mil"] / divisor_dfc
            df_anu["valor_mil"] = df_anu["valor_mil"] / divisor_dfc
            print(f"    Escala DFC: {escala_dfc_tri['justificativa']} (P50={escala_dfc_tri['magnitude_p50']}, divisor={divisor_dfc:,.0f})")
        
        # ✅ VALIDAÇÃO DE COERÊNCIA (6.01 + 6.02 + 6.03 + 6.04 = 6.05)
        periodos_dfc = df_tri.groupby(['data_fim', 'trimestre'])
        validacoes = []
        
        for (data_fim, trimestre), grupo in periodos_dfc:
            periodo_str = f"{data_fim} ({trimestre})"
            val = validar_dfc_coerencia(grupo, periodo_str)
            validacoes.append(val)
            
            if not val['valido'] and abs(val.get('variacao_caixa', 0)) > 1:
                print(f"    ⚠️ Incoerência DFC {periodo_str}: 6.05={val['variacao_caixa']:,.0f} ≠ Calculado={val['calculado']:,.0f} (Diff: {val['diff_percent']:.2f}%)")
        
        # Estatísticas de validação
        validos = sum(1 for v in validacoes if v['valido'])
        total = len(validacoes)
        if total > 0:
            print(f"    Validação: {validos}/{total} períodos coerentes ({validos/total*100:.1f}%)")       
    
    
        # NOVO: Preencher trimestres vazios para empresas mar-fev
        if _is_mar_fev_company(ticker):
            # Verificar se coluna trimestre está vazia/nan
            if df_tri["trimestre"].isna().all() or (df_tri["trimestre"].astype(str).str.strip() == "").all():
                df_tri["trimestre"] = df_tri["data_fim"].apply(_infer_quarter_mar_fev)
    
        return df_tri, df_anu
        

    def _build_quarter_totals(self, df_tri: pd.DataFrame, fiscal_info: FiscalYearInfo) -> pd.DataFrame:
        """
        Constrói totais trimestrais preservando trimestres originais.
        MODIFICADO: Usa ano fiscal correto para empresas mar-fev.
        MODIFICADO: Converte D&A de YTD para isolado quando necessário.
        """
        target_codes = [c for c, _ in DFC_CONTAS]
        wanted_prefixes = tuple([c + "." for c in target_codes])
    
        mask = (
            df_tri["cd_conta"].isin(target_codes)
            | df_tri["cd_conta"].astype(str).str.startswith(wanted_prefixes)
        )
        df = df_tri[mask].copy()
        
        # MODIFICADO: Calcular ano fiscal correto
        if fiscal_info.is_mar_fev:
            df["ano"] = df["data_fim"].apply(_get_fiscal_year_mar_fev)
        else:
            df["ano"] = df["data_fim"].dt.year
    
        rows = []
        for (ano, trimestre), g in df.groupby(["ano", "trimestre"], sort=False):
            for code, _name in DFC_CONTAS:
                v = _pick_value_for_code(g, code)
                rows.append((int(ano), str(trimestre), code, v))
    
            if self._include_deprec_amort():
                deprec_val = _compute_deprec_amort_value(g)
                rows.append((int(ano), str(trimestre), DEPREC_CODE, deprec_val))
    
        result = pd.DataFrame(rows, columns=["ano", "trimestre", "code", "valor"])
        
        # ==================================================================================
        # CORREÇÃO: Converter D&A de YTD para isolado em empresas mar-fev
        # As subcontas 6.01.01.* (onde está D&A) são reportadas como YTD acumulado,
        # diferente das contas principais (6.01, 6.02, etc.) que são isoladas.
        # ==================================================================================
        if fiscal_info.is_mar_fev and self._include_deprec_amort():
            result = self._convert_deprec_ytd_to_isolated(result)
        
        return result
    
    
    def _convert_deprec_ytd_to_isolated(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Converte valores de D&A de YTD (acumulado) para isolado.
        
        Para empresas mar-fev, as subcontas 6.01.01.* são reportadas como YTD:
        - T1: valor isolado do T1
        - T2: valor acumulado T1+T2
        - T3: valor acumulado T1+T2+T3
        
        Esta função detecta o padrão YTD e converte para valores isolados.
        """
        quarter_order = {"T1": 1, "T2": 2, "T3": 3, "T4": 4}
        
        # Separar D&A das outras contas
        mask_da = df["code"] == DEPREC_CODE
        df_da = df[mask_da].copy()
        df_other = df[~mask_da].copy()
        
        if df_da.empty:
            return df
        
        converted_rows = []
        
        for ano in df_da["ano"].unique():
            ano_data = df_da[df_da["ano"] == ano].copy()
            ano_data = ano_data.sort_values("trimestre", key=lambda x: x.map(quarter_order))
            
            quarters = ano_data["trimestre"].tolist()
            values = ano_data["valor"].tolist()
            
            # Detectar se está em YTD: valores crescentes (T2 > T1, T3 > T2)
            is_ytd = False
            if len(values) >= 2:
                # Verificar se os valores são crescentes (típico de YTD para D&A positiva)
                valid_values = [v for v in values if pd.notna(v) and np.isfinite(v)]
                if len(valid_values) >= 2:
                    # D&A é sempre positiva, então YTD significa valores crescentes
                    is_ytd = all(valid_values[i] <= valid_values[i+1] for i in range(len(valid_values)-1))
                    # Verificação adicional: T3 deve ser aproximadamente T1+T2+T3_isolado
                    # Se T2 > T1 * 1.5 e T3 > T2 * 1.2, provavelmente é YTD
                    if len(valid_values) >= 2 and valid_values[0] > 0:
                        ratio = valid_values[1] / valid_values[0]
                        is_ytd = is_ytd and ratio > 1.3  # T2 deve ser significativamente maior que T1
            
            if is_ytd:
                # Converter YTD para isolado
                isolated = []
                prev = 0.0
                for v in values:
                    if pd.isna(v) or not np.isfinite(v):
                        isolated.append(np.nan)
                    else:
                        isolated.append(v - prev)
                        prev = v
                
                for q, v in zip(quarters, isolated):
                    converted_rows.append((int(ano), q, DEPREC_CODE, v))
            else:
                # Manter valores originais
                for q, v in zip(quarters, values):
                    converted_rows.append((int(ano), q, DEPREC_CODE, v))
        
        # Reconstruir DataFrame
        df_da_converted = pd.DataFrame(converted_rows, columns=["ano", "trimestre", "code", "valor"])
        
        return pd.concat([df_other, df_da_converted], ignore_index=True)

    def _extract_annual_values(self, df_anu: pd.DataFrame, fiscal_info: FiscalYearInfo) -> pd.DataFrame:
        """
        Extrai valores anuais para cálculo do T4.
        MODIFICADO: Usa ano fiscal correto para empresas mar-fev.
        """
        target_codes = [c for c, _ in DFC_CONTAS]
        wanted_prefixes = tuple([c + "." for c in target_codes])

        mask = (
            df_anu["cd_conta"].isin(target_codes)
            | df_anu["cd_conta"].astype(str).str.startswith(wanted_prefixes)
        )
        df = df_anu[mask].copy()
        
        # MODIFICADO: Calcular ano fiscal correto
        if fiscal_info.is_mar_fev:
            df["ano"] = df["data_fim"].apply(_get_fiscal_year_mar_fev)
        else:
            df["ano"] = df["data_fim"].dt.year

        rows = []
        for ano, g in df.groupby("ano", sort=False):
            for code, _name in DFC_CONTAS:
                v = _pick_value_for_code(g, code)
                rows.append((int(ano), code, v))

            if self._include_deprec_amort():
                deprec_val = _compute_deprec_amort_value(g)
                rows.append((int(ano), DEPREC_CODE, deprec_val))

        return pd.DataFrame(rows, columns=["ano", "code", "anual_val"])

    # ==================================================================================
    # CORREÇÃO CIRÚRGICA: DETECÇÃO DE ANOS ACUMULADOS (YTD)
    # - Mantém fluxo/arquitetura intactos.
    # - Ajusta apenas o critério para não "falhar" quando a soma simples cancela por sinais.
    # ==================================================================================
    def _detect_cumulative_years(
        self,
        qtot: pd.DataFrame,
        anual: pd.DataFrame,
        fiscal_info: FiscalYearInfo,
        base_code_for_detection: str = "6.01",
        ratio_threshold: float = 1.10,
    ) -> Dict[int, bool]:
        """
        Detecta se o trimestral está acumulado (YTD) por ano.

        Correção (cirúrgica):
        - Antes: usava apenas abs(sum(valores)) > abs(anual)*threshold
          -> falha quando há cancelamento de sinais (muito comum em DFC).
        - Agora: mantém a mesma regra, mas adiciona também uma verificação por
          abs-sum (soma das magnitudes), que é robusta a cancelamentos:
              sum(|valores|) > |anual|*threshold
        - Mantém todo o restante idêntico.
        
        MODIFICADO: Para empresas mar-fev, não tenta detectar acumulado
        (os dados já são isolados por trimestre).
        """
        # Para empresas mar-fev, os dados trimestrais são isolados
        if fiscal_info.is_mar_fev:
            return {}
        
        if not fiscal_info.is_standard:
            return {}

        anual_map = anual.set_index(["ano", "code"])["anual_val"].to_dict()
        out: Dict[int, bool] = {}

        # Fallback leve: se base_code não tiver anual para um ano, tenta 6.05 (mais estável em DFC)
        fallback_codes = [base_code_for_detection]
        if base_code_for_detection != "6.05":
            fallback_codes.append("6.05")

        for ano in sorted(qtot["ano"].unique()):
            decided = False

            for base_code in fallback_codes:
                a = anual_map.get((int(ano), base_code), np.nan)
                if (not np.isfinite(a)) or a == 0:
                    continue

                g = qtot[(qtot["ano"] == int(ano)) & (qtot["code"] == base_code)]
                if g.empty:
                    continue

                vals = g["valor"].astype(float).values
                s_raw = float(np.nansum(vals))
                s_abs = float(np.nansum(np.abs(vals)))

                # Regra original (mantida) + robustez contra cancelamento de sinal
                is_cum = (
                    (np.isfinite(s_raw) and (abs(s_raw) > abs(a) * ratio_threshold))
                    or (np.isfinite(s_abs) and (s_abs > abs(a) * ratio_threshold))
                )

                out[int(ano)] = bool(is_cum)
                decided = True
                break

            if not decided:
                # Sem dados suficientes para decidir: não marca como acumulado
                # (mantém comportamento de "não mexer" quando não há base)
                continue

        return out

    def _to_isolated_quarters(
        self,
        qtot: pd.DataFrame,
        cumulative_years: Dict[int, bool],
        fiscal_info: FiscalYearInfo,
    ) -> pd.DataFrame:
        """
        Converte dados acumulados (YTD) para trimestres isolados quando necessário.
        MODIFICADO: Para empresas mar-fev, não aplica conversão (já são isolados).
        """
        out_rows = []

        for (ano, code), g in qtot.groupby(["ano", "code"], sort=False):
            g = g.copy()
            g["qord"] = g["trimestre"].apply(_quarter_order)
            g = g.sort_values("qord")

            vals = g["valor"].values.astype(float)
            qs = g["trimestre"].tolist()

            # Para empresas mar-fev, não converte (dados já são isolados)
            if fiscal_info.is_mar_fev:
                pass  # Mantém vals como está
            elif (cumulative_years.get(int(ano), False) and fiscal_info.is_standard):
                qords = g["qord"].values
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
        fiscal_info: FiscalYearInfo,
    ) -> pd.DataFrame:
        """
        Adiciona T4 calculado quando faltante.
        T4 = Anual - (T1 + T2 + T3)
        
        MODIFICADO: Também funciona para empresas mar-fev.
        """
        # Para empresas mar-fev, também calcular T4 quando faltante
        if not fiscal_info.is_standard and not fiscal_info.is_mar_fev:
            return qiso

        anual_map = anual.set_index(["ano", "code"])["anual_val"].to_dict()
        out = qiso.copy()

        all_codes = [c for c, _ in DFC_CONTAS]
        if self._include_deprec_amort():
            all_codes.append(DEPREC_CODE)

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
                new_rows.append((int(ano), "T4", code, t4_val))

            if new_rows:
                out = pd.concat([out, pd.DataFrame(new_rows, columns=out.columns)], ignore_index=True)

        return out

    def _build_horizontal(self, qiso: pd.DataFrame) -> pd.DataFrame:
        """
        Constrói tabela horizontal (períodos como colunas).
        """
        dfc_schema = self._get_dfc_schema()

        qiso = qiso.copy()
        qiso["periodo"] = qiso["ano"].astype(str) + qiso["trimestre"]
        qiso["valor"] = qiso["valor"].apply(lambda x: _normalize_value(x, 3))

        piv = qiso.pivot_table(
            index="code", columns="periodo", values="valor", aggfunc="first"
        )

        def sort_key(p):
            try:
                return (int(p[:4]), _quarter_order(p[4:]))
            except Exception:
                return (9999, 99)

        cols = sorted(piv.columns, key=sort_key)
        piv = piv[cols]

        code_order = {c: i for i, (c, _) in enumerate(dfc_schema)}
        piv = piv.reindex(sorted(piv.index, key=lambda x: code_order.get(x, 999)))

        code_to_name = {c: n for c, n in dfc_schema}
        piv.insert(0, "conta", piv.index.map(lambda x: code_to_name.get(x, x)))
        piv = piv.reset_index().rename(columns={"code": "cd_conta"})

        return piv

    def padronizar_e_salvar_ticker(self, ticker: str) -> Tuple[bool, str]:
        """
        Pipeline completo de padronização do DFC.
        Agora usa get_pasta_balanco() para garantir pasta correta.
        MODIFICADO: Passa ticker para _detect_fiscal_year_pattern e fiscal_info para métodos.
        """
        self._current_ticker = ticker.upper().strip()
    
        df_tri, df_anu = self._load_inputs(ticker)
    
        # MODIFICADO: Passa ticker para detectar empresas mar-fev
        fiscal_info = _detect_fiscal_year_pattern(df_tri, df_anu, ticker)
    
        # MODIFICADO: Passa fiscal_info para _build_quarter_totals
        qtot = self._build_quarter_totals(df_tri, fiscal_info)
    
        # MODIFICADO: Passa fiscal_info para _extract_annual_values
        anual = self._extract_annual_values(df_anu, fiscal_info)
    
        cumulative_years = self._detect_cumulative_years(qtot, anual, fiscal_info)
    
        qiso = self._to_isolated_quarters(qtot, cumulative_years, fiscal_info)
    
        qiso = self._add_t4_from_annual_when_missing(qiso, anual, fiscal_info)
    
        df_out = self._build_horizontal(qiso)
    
        pasta = get_pasta_balanco(ticker)
        out_path = pasta / "dfc_padronizado.csv"
        #df_out.to_csv(out_path, index=False, encoding="utf-8")
        df_out.to_csv(out_path, index=False, encoding="utf-8", float_format='%.3f')
    
        # MODIFICADO: Mensagem para empresas mar-fev
        if fiscal_info.is_mar_fev:
            fiscal_status = "MAR-FEV"
        elif fiscal_info.is_standard:
            fiscal_status = "PADRÃO"
        else:
            fiscal_status = "IRREGULAR"
            
        tipo = "FINANCEIRA" if _is_financeira_ou_seguradora(ticker) else "GERAL"
    
        n_periodos = len([c for c in df_out.columns if c not in ["cd_conta", "conta"]])
    
        msg_parts = [
            f"Fiscal: {fiscal_status}",
            f"Tipo: {tipo}",
            f"Períodos: {n_periodos}",
        ]
    
        if self._include_deprec_amort():
            has_deprec = not df_out[df_out["cd_conta"] == DEPREC_CODE].empty
            if has_deprec:
                deprec_row = df_out[df_out["cd_conta"] == DEPREC_CODE].iloc[0]
                non_null = sum(
                    1
                    for c in df_out.columns
                    if c not in ["cd_conta", "conta"] and pd.notna(deprec_row[c])
                )
                msg_parts.append(f"D&A: {non_null} períodos")
            else:
                msg_parts.append("D&A: não encontrada")
    
        msg = f"dfc_padronizado.csv | {' | '.join(msg_parts)}"
        return True, msg


# ======================================================================================
# CLI - MAIN
# ======================================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Padroniza DFC das empresas (trimestres isolados + T4)"
    )
    parser.add_argument(
        "--modo",
        choices=["quantidade", "ticker", "lista", "faixa"],
        default="quantidade",
        help="Modo de seleção: quantidade, ticker, lista, faixa",
    )
    parser.add_argument("--quantidade", default="10", help="Quantidade de empresas")
    parser.add_argument("--ticker", default="", help="Ticker específico")
    parser.add_argument("--lista", default="", help="Lista de tickers separados por vírgula")
    parser.add_argument("--faixa", default="", help="Faixa de linhas: inicio-fim (ex: 1-50)")
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
        df_sel = df.iloc[inicio - 1: fim]

    else:
        df_sel = df.head(10)

    print(f"\n>>> JOB: PADRONIZAR DFC <<<")
    print(f"Modo: {args.modo} | Selecionadas: {len(df_sel)}")
    print("Saída: balancos/<TICKER>/dfc_padronizado.csv\n")

    pad = PadronizadorDFC()

    ok_count = 0
    err_count = 0
    irregular_count = 0

    for _, row in df_sel.iterrows():
        ticker_str = str(row["ticker"]).upper().strip()
        ticker = ticker_str.split(';')[0] if ';' in ticker_str else ticker_str

        pasta = get_pasta_balanco(ticker)
        if not pasta.exists():
            err_count += 1
            print(f"❌ {ticker}: pasta {pasta} não existe")
            continue

        try:
            ok, msg = pad.padronizar_e_salvar_ticker(ticker)

            if "IRREGULAR" in msg or "MAR-FEV" in msg:
                irregular_count += 1

            if ok:
                ok_count += 1
                print(f"✅ {ticker}: {msg}")
            else:
                err_count += 1
                print(f"⚠️ {ticker}: {msg}")

        except FileNotFoundError as e:
            err_count += 1
            print(f"❌ {ticker}: arquivos ausentes ({e})")
        except Exception as e:
            err_count += 1
            import traceback
            print(f"❌ {ticker}: erro ({type(e).__name__}: {e})")
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"Finalizado: OK={ok_count} | ERRO={err_count}")
    if irregular_count > 0:
        print(f"            Anos fiscais irregulares/MAR-FEV: {irregular_count}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
