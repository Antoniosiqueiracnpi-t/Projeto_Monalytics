# padronizar_bp.py
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

# ======================================================================================
# FUNÇÕES AUXILIARES
# ======================================================================================

def get_ticker_principal(ticker: str) -> str:
    """Retorna o ticker principal (primeiro se houver múltiplos)."""
    return ticker.split(';')[0].strip().upper()


def load_mapeamento_consolidado() -> pd.DataFrame:
    """Carrega mapeamento consolidado ou fallback para original."""
    path_consolidado = Path("mapeamento_cnpj_consolidado.csv")
    path_original = Path("mapeamento_cnpj_ticker.csv")
    
    if path_consolidado.exists():
        return pd.read_csv(path_consolidado)
    elif path_original.exists():
        return pd.read_csv(path_original)
    else:
        raise FileNotFoundError("Nenhum arquivo de mapeamento encontrado")


# ======================================================================================
# CORREÇÃO 1: BUSCA INTELIGENTE DE PASTA POR VARIANTES DE TICKER
# ======================================================================================

def get_pasta_balanco(ticker: str, pasta_base: Path = Path("balancos")) -> Path:
    """
    Retorna o caminho da pasta de balanços do ticker.
    
    CORREÇÃO: Busca variantes do ticker (3, 4, 5, 6, 11) se pasta exata não existir.
    Exemplo: Se buscar BBDC3 e não existir, procura BBDC4, BBDC5, etc.
    """
    ticker_clean = get_ticker_principal(ticker).upper().strip()
    
    # Tentar pasta exata primeiro
    pasta_exata = pasta_base / ticker_clean
    if pasta_exata.exists():
        return pasta_exata
    
    # Extrair base do ticker (sem número final)
    match = re.match(r'^([A-Z]{4})(\d+)?$', ticker_clean)
    if not match:
        return pasta_exata
    
    base = match.group(1)  # Ex: "BBDC" de "BBDC3"
    
    # Variantes comuns na B3: 3 (ON), 4 (PN), 5 (PNA), 6 (PNB), 11 (Units)
    variantes = ['3', '4', '5', '6', '11', '33', '34']
    
    for var in variantes:
        pasta_variante = pasta_base / f"{base}{var}"
        if pasta_variante.exists():
            return pasta_variante
    
    return pasta_exata


# ======================================================================================
# EMPRESAS COM ANO FISCAL MARÇO-FEVEREIRO
# ======================================================================================

TICKERS_MAR_FEV: Set[str] = {"CAML3"}


def _is_mar_fev_company(ticker: str) -> bool:
    return ticker.upper().strip() in TICKERS_MAR_FEV


def _get_fiscal_year_mar_fev(data: pd.Timestamp) -> int:
    if pd.isna(data):
        return 0
    return data.year if data.month >= 3 else data.year - 1


def _infer_quarter_mar_fev(data: pd.Timestamp) -> str:
    if pd.isna(data):
        return ""
    month = data.month
    if month in (3, 4, 5):
        return "T1"
    elif month in (6, 7, 8):
        return "T2"
    elif month in (9, 10, 11):
        return "T3"
    return "T4"


# ======================================================================================
# CONTAS BPA - BALANÇO PATRIMONIAL ATIVO (EMPRESAS NÃO FINANCEIRAS)
# ======================================================================================

BPA_PADRAO: List[Tuple[str, str]] = [
    ("1", "Ativo Total"),
    ("1.01", "Ativo Circulante"),
    ("1.01.01", "Caixa e Equivalentes de Caixa"),
    ("1.01.02", "Aplicações Financeiras"),
    ("1.01.03", "Contas a Receber"),
    ("1.01.04", "Estoques"),
    ("1.01.05", "Ativos Biológicos"),
    ("1.01.06", "Tributos a Recuperar"),
    ("1.01.07", "Despesas Antecipadas"),
    ("1.01.08", "Outros Ativos Circulantes"),
    ("1.02", "Ativo Não Circulante"),
    ("1.02.01", "Ativo Realizável a Longo Prazo"),
    ("1.02.02", "Investimentos"),
    ("1.02.03", "Imobilizado"),
    ("1.02.04", "Intangível"),
]

# ======================================================================================
# CONTAS BPP - BALANÇO PATRIMONIAL PASSIVO (EMPRESAS NÃO FINANCEIRAS)
# ======================================================================================

BPP_PADRAO: List[Tuple[str, str]] = [
    ("2", "Passivo Total"),
    ("2.01", "Passivo Circulante"),
    ("2.01.01", "Obrigações Sociais e Trabalhistas"),
    ("2.01.02", "Fornecedores"),
    ("2.01.03", "Obrigações Fiscais"),
    ("2.01.04", "Empréstimos e Financiamentos"),
    ("2.01.05", "Outras Obrigações"),
    ("2.01.06", "Provisões"),
    ("2.01.07", "Passivos sobre Ativos Não-Correntes a Venda e Descontinuados"),
    ("2.02", "Passivo Não Circulante"),
    ("2.02.01", "Empréstimos e Financiamentos"),
    ("2.02.02", "Outras Obrigações"),
    ("2.02.03", "Tributos Diferidos"),
    ("2.02.04", "Provisões"),
    ("2.02.05", "Passivos sobre Ativos Não-Correntes a Venda e Descontinuados"),
    ("2.02.06", "Lucros e Receitas a Apropriar"),
    ("2.03", "Patrimônio Líquido Consolidado"),
    ("2.03.01", "Capital Social Realizado"),
    ("2.03.02", "Reservas de Capital"),
    ("2.03.03", "Reservas de Reavaliação"),
    ("2.03.04", "Reservas de Lucros"),
    ("2.03.05", "Lucros/Prejuízos Acumulados"),
    ("2.03.06", "Ajustes de Avaliação Patrimonial"),
    ("2.03.07", "Ajustes Acumulados de Conversão"),
    ("2.03.08", "Outros Resultados Abrangentes"),
    ("2.03.09", "Participação dos Acionistas Não Controladores"),
]


# ======================================================================================
# CONTAS BPA - BANCOS (INSTITUIÇÕES FINANCEIRAS)
# ======================================================================================

BPA_BANCOS: List[Tuple[str, str]] = [
    ("1", "Ativo Total"),
    ("1.01", "Caixa e Equivalentes de Caixa"),
    ("1.02", "Ativos Financeiros"),
    ("1.03", "Tributos"),
    ("1.04", "Outros Ativos"),
    ("1.05", "Investimentos"),
    ("1.06", "Imobilizado"),
    ("1.07", "Intangível"),
]


# ======================================================================================
# CORREÇÃO 2: DETECÇÃO DINÂMICA DO CÓDIGO DO PATRIMÔNIO LÍQUIDO PARA BANCOS
# ======================================================================================

def _detect_pl_code_from_data(df_bpp: pd.DataFrame) -> str:
    """
    Detecta dinamicamente o código do Patrimônio Líquido nos dados do BPP.
    
    CORREÇÃO: O PL pode estar em 2.07 (BBAS3, BBDC4) ou 2.08 (ITUB4).
    Busca por descrição contendo "Patrimônio Líquido" no nível 2.XX.
    """
    # Buscar conta que contém "Patrimônio Líquido" na descrição
    mask_pl = df_bpp["ds_conta"].str.contains(
        r"Patrim[oô]nio\s+L[ií]quido", 
        case=False, 
        regex=True, 
        na=False
    )
    
    df_pl = df_bpp[mask_pl].copy()
    
    if df_pl.empty:
        return "2.07"  # Fallback padrão mais comum
    
    # Filtrar apenas códigos no formato 2.XX (nível principal do PL)
    df_pl_main = df_pl[df_pl["cd_conta"].str.match(r'^2\.\d{2}$', na=False)]
    
    if not df_pl_main.empty:
        return str(df_pl_main["cd_conta"].iloc[0])
    
    # Tentar extrair código base de subcontas (ex: 2.07 de 2.07.01)
    for codigo in df_pl["cd_conta"].unique():
        parts = str(codigo).split('.')
        if len(parts) >= 2:
            return f"{parts[0]}.{parts[1]}"
    
    return "2.07"


def _build_bpp_schema_for_bank(df_bpp: pd.DataFrame) -> List[Tuple[str, str]]:
    """
    Constrói esquema BPP dinâmico para bancos baseado nos dados reais.
    
    CORREÇÃO: Detecta automaticamente onde está o PL (2.07 ou 2.08).
    """
    pl_code = _detect_pl_code_from_data(df_bpp)
    
    # Esquema base - contas antes do PL
    schema = [
        ("2", "Passivo Total"),
        ("2.01", "Passivos Financeiros ao Valor Justo através do Resultado"),
        ("2.02", "Passivos Financeiros ao Custo Amortizado"),
        ("2.02.01", "Depósitos"),
        ("2.02.02", "Captações no Mercado Aberto"),
        ("2.02.03", "Recursos de Mercados Interbancários"),
        ("2.02.04", "Outras Captações"),
        ("2.03", "Provisões"),
        ("2.04", "Passivos Fiscais"),
        ("2.05", "Outros Passivos"),
        ("2.06", "Passivos sobre Ativos Não Correntes a Venda"),
    ]
    
    # Adicionar conta 2.07 intermediária se PL estiver em 2.08
    pl_num = int(pl_code.split('.')[1])
    if pl_num > 7:
        schema.append(("2.07", "Passivos sobre Ativos Descontinuados"))
    
    # Adicionar PL e subcontas com código detectado
    schema.extend([
        (pl_code, "Patrimônio Líquido Consolidado"),
        (f"{pl_code}.01", "Patrimônio Líquido Atribuído ao Controlador"),
        (f"{pl_code}.01.01", "Capital Social Realizado"),
        (f"{pl_code}.01.02", "Reservas de Capital"),
        (f"{pl_code}.01.04", "Reservas de Lucros"),
        (f"{pl_code}.01.05", "Lucros/Prejuízos Acumulados"),
        (f"{pl_code}.01.08", "Outros Resultados Abrangentes"),
        (f"{pl_code}.02", "Patrimônio Líquido Atribuído aos Não Controladores"),
    ])
    
    return schema


# ======================================================================================
# CONTAS BPA/BPP - SEGURADORAS E HOLDINGS
# ======================================================================================

BPA_SEGURADORAS: List[Tuple[str, str]] = [
    ("1", "Ativo Total"),
    ("1.01", "Ativo Circulante"),
    ("1.01.01", "Caixa e Equivalentes de Caixa"),
    ("1.01.02", "Aplicações Financeiras"),
    ("1.01.03", "Créditos das Operações de Seguros"),
    ("1.01.06", "Ativos de Resseguro"),
    ("1.01.08", "Custos de Aquisição Diferidos"),
    ("1.02", "Ativo Não Circulante"),
    ("1.02.01", "Ativo Realizável a Longo Prazo"),
    ("1.02.02", "Investimentos"),
    ("1.02.03", "Imobilizado"),
    ("1.02.04", "Intangível"),
]

BPP_SEGURADORAS: List[Tuple[str, str]] = [
    ("2", "Passivo Total"),
    ("2.01", "Passivo Circulante"),
    ("2.01.01", "Obrigações a Pagar"),
    ("2.01.04", "Provisões Técnicas de Seguros"),
    ("2.01.05", "Débitos de Operações com Seguros"),
    ("2.02", "Passivo Não Circulante"),
    ("2.03", "Patrimônio Líquido Consolidado"),
    ("2.03.01", "Capital Social Realizado"),
    ("2.03.02", "Reservas de Capital"),
    ("2.03.04", "Reservas de Lucros"),
]

BPA_HOLDINGS_SEGUROS: List[Tuple[str, str]] = [
    ("1", "Ativo Total"),
    ("1.01", "Ativo Circulante"),
    ("1.01.01", "Caixa e Equivalentes de Caixa"),
    ("1.01.02", "Aplicações Financeiras"),
    ("1.01.03", "Contas a Receber"),
    ("1.02", "Ativo Não Circulante"),
    ("1.02.02", "Investimentos"),
    ("1.02.03", "Imobilizado"),
    ("1.02.04", "Intangível"),
]

BPP_HOLDINGS_SEGUROS: List[Tuple[str, str]] = [
    ("2", "Passivo Total"),
    ("2.01", "Passivo Circulante"),
    ("2.01.01", "Obrigações Sociais e Trabalhistas"),
    ("2.01.02", "Obrigações Fiscais"),
    ("2.01.05", "Outras Obrigações"),
    ("2.02", "Passivo Não Circulante"),
    ("2.03", "Patrimônio Líquido Consolidado"),
    ("2.03.01", "Capital Social Realizado"),
    ("2.03.04", "Reservas de Lucros"),
]


# ======================================================================================
# TICKERS DE BANCOS E SEGURADORAS
# ======================================================================================

TICKERS_BANCOS: Set[str] = {
    "RPAD3", "RPAD5", "RPAD6", "ABCB4", "BMGB4",
    "BBDC3", "BBDC4", "BPAC3", "BPAC5", "BPAC11",
    "BSLI3", "BSLI4", "BBAS3", "BGIP3", "BGIP4",
    "BPAR3", "BRSR3", "BRSR5", "BRSR6", "BNBR3",
    "BMIN3", "BMIN4", "BMEB3", "BMEB4", "BPAN4",
    "PINE3", "PINE4", "SANB3", "SANB4", "SANB11",
    "BEES3", "BEES4", "ITUB3", "ITUB4",
}

TICKERS_HOLDINGS_SEGUROS: Set[str] = {"BBSE3", "CXSE3"}
TICKERS_SEGURADORAS: Set[str] = {"IRBR3", "PSSA3"}


def _is_banco(ticker: str) -> bool:
    """Verifica se é banco - também por variantes."""
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


def _get_bpa_schema(ticker: str) -> List[Tuple[str, str]]:
    ticker_upper = ticker.upper().strip()
    if _is_holding_seguros(ticker_upper):
        return BPA_HOLDINGS_SEGUROS
    elif _is_seguradora_operacional(ticker_upper):
        return BPA_SEGURADORAS
    elif _is_banco(ticker_upper):
        return BPA_BANCOS
    return BPA_PADRAO


def _get_bpp_schema(ticker: str, df_bpp: Optional[pd.DataFrame] = None) -> List[Tuple[str, str]]:
    """Retorna o esquema BPP apropriado. Para bancos, usa detecção dinâmica."""
    ticker_upper = ticker.upper().strip()
    
    if _is_holding_seguros(ticker_upper):
        return BPP_HOLDINGS_SEGUROS
    elif _is_seguradora_operacional(ticker_upper):
        return BPP_SEGURADORAS
    elif _is_banco(ticker_upper):
        if df_bpp is not None and not df_bpp.empty:
            return _build_bpp_schema_for_bank(df_bpp)
        # Fallback genérico
        return [
            ("2", "Passivo Total"),
            ("2.01", "Passivos Financeiros ao Valor Justo"),
            ("2.02", "Passivos Financeiros ao Custo Amortizado"),
            ("2.03", "Provisões"),
            ("2.04", "Passivos Fiscais"),
            ("2.05", "Outros Passivos"),
            ("2.07", "Patrimônio Líquido Consolidado"),
        ]
    return BPP_PADRAO


def _get_tipo_empresa(ticker: str) -> str:
    ticker_upper = ticker.upper().strip()
    if _is_holding_seguros(ticker_upper):
        return "HOLDING SEGUROS"
    elif _is_seguradora_operacional(ticker_upper):
        return "SEGURADORA"
    elif _is_banco(ticker_upper):
        return "BANCO"
    elif _is_mar_fev_company(ticker_upper):
        return "MAR-FEV"
    return "GERAL"


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
    if not np.isfinite(v):
        return np.nan
    return round(float(v), decimals)


def _pick_value_for_code(group: pd.DataFrame, code: str) -> float:
    exact = group[group["cd_conta"] == code]
    if not exact.empty:
        v = _ensure_numeric(exact["valor_mil"]).iloc[0]
        return float(v) if np.isfinite(v) else np.nan
    return np.nan


# ======================================================================================
# DETECTOR DE ANO FISCAL
# ======================================================================================

@dataclass
class FiscalYearInfo:
    is_standard: bool
    fiscal_end_month: int
    quarters_pattern: Set[str]
    has_all_quarters: bool
    description: str
    is_mar_fev: bool = False


def _detect_fiscal_year_pattern(df_tri: pd.DataFrame, df_anu: pd.DataFrame, ticker: str = "") -> FiscalYearInfo:
    is_mar_fev = _is_mar_fev_company(ticker)
    quarters_found = set(df_tri["trimestre"].dropna().unique())
    
    if "data_fim" in df_anu.columns and not df_anu.empty:
        end_months = df_anu["data_fim"].dropna().dt.month.unique()
        
        if len(end_months) == 1 and end_months[0] == 12:
            fiscal_end, is_standard = 12, True
        elif len(end_months) == 1 and end_months[0] == 2:
            fiscal_end, is_standard, is_mar_fev = 2, False, True
        elif len(end_months) >= 1:
            mode_month = df_anu["data_fim"].dt.month.mode()
            fiscal_end = int(mode_month.iloc[0]) if not mode_month.empty else 12
            is_standard = (fiscal_end == 12)
            if fiscal_end == 2:
                is_mar_fev = True
        else:
            fiscal_end, is_standard = 12, True
    else:
        fiscal_end, is_standard = 12, True
    
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
# CLASSE PRINCIPAL - PADRONIZADOR BP
# ======================================================================================

@dataclass
class PadronizadorBP:
    pasta_balancos: Path = Path("balancos")
    _current_ticker: str = field(default="", repr=False)

    def _load_inputs(self, ticker: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Carrega os 4 arquivos de entrada usando get_pasta_balanco() melhorado."""
        pasta = get_pasta_balanco(ticker, self.pasta_balancos)
        is_mar_fev = _is_mar_fev_company(ticker)
        
        bpa_tri = pd.read_csv(pasta / "bpa_consolidado.csv")
        bpa_anu = pd.read_csv(pasta / "bpa_anual.csv")
        bpp_tri = pd.read_csv(pasta / "bpp_consolidado.csv")
        bpp_anu = pd.read_csv(pasta / "bpp_anual.csv")
    
        for df in (bpa_tri, bpa_anu, bpp_tri, bpp_anu):
            df["cd_conta"] = df["cd_conta"].astype(str).str.strip()
            df["ds_conta"] = df["ds_conta"].astype(str).str.strip()
            df["valor_mil"] = _ensure_numeric(df["valor_mil"])
            df["data_fim"] = _to_datetime(df, "data_fim")
    
        bpa_tri = bpa_tri.dropna(subset=["data_fim"])
        bpa_anu = bpa_anu.dropna(subset=["data_fim"])
        bpp_tri = bpp_tri.dropna(subset=["data_fim"])
        bpp_anu = bpp_anu.dropna(subset=["data_fim"])
        
        if is_mar_fev:
            for df in (bpa_tri, bpp_tri):
                if "trimestre" not in df.columns:
                    df["trimestre"] = ""
                mask_empty = df["trimestre"].isna() | (df["trimestre"].astype(str).str.strip() == "")
                if mask_empty.any():
                    df.loc[mask_empty, "trimestre"] = df.loc[mask_empty, "data_fim"].apply(_infer_quarter_mar_fev)
    
        return bpa_tri, bpa_anu, bpp_tri, bpp_anu

    def _build_quarter_values(
        self, 
        df_tri: pd.DataFrame, 
        schema: List[Tuple[str, str]],
        fiscal_info: FiscalYearInfo
    ) -> pd.DataFrame:
        """Extrai valores trimestrais para as contas do esquema."""
        target_codes = [c for c, _ in schema]
        df = df_tri[df_tri["cd_conta"].isin(target_codes)].copy()
        
        if fiscal_info.is_mar_fev:
            df["ano"] = df["data_fim"].apply(_get_fiscal_year_mar_fev)
        else:
            df["ano"] = df["data_fim"].dt.year
        
        rows = []
        for (ano, trimestre), g in df.groupby(["ano", "trimestre"], sort=False):
            for code, _ in schema:
                v = _pick_value_for_code(g, code)
                rows.append((int(ano), str(trimestre), code, v))

        return pd.DataFrame(rows, columns=["ano", "trimestre", "code", "valor"])

    def _extract_annual_values(
        self, 
        df_anu: pd.DataFrame, 
        schema: List[Tuple[str, str]],
        fiscal_info: FiscalYearInfo
    ) -> pd.DataFrame:
        """Extrai valores anuais para inclusão como T4."""
        target_codes = [c for c, _ in schema]
        df = df_anu[df_anu["cd_conta"].isin(target_codes)].copy()
        
        if fiscal_info.is_mar_fev:
            df["ano"] = df["data_fim"].apply(_get_fiscal_year_mar_fev)
        else:
            df["ano"] = df["data_fim"].dt.year

        rows = []
        for ano, g in df.groupby("ano", sort=False):
            for code, _ in schema:
                v = _pick_value_for_code(g, code)
                rows.append((int(ano), code, v))

        return pd.DataFrame(rows, columns=["ano", "code", "anual_val"])

    def _add_t4_from_annual(
        self, 
        qtot: pd.DataFrame, 
        anual: pd.DataFrame,
        fiscal_info: FiscalYearInfo,
        schema: List[Tuple[str, str]]
    ) -> pd.DataFrame:
        """Adiciona T4 usando valor anual (BP é posição, não fluxo)."""
        if not fiscal_info.is_standard and not fiscal_info.is_mar_fev:
            return qtot
        
        anual_map = anual.set_index(["ano", "code"])["anual_val"].to_dict()
        out = qtot.copy()
        all_codes = [c for c, _ in schema]

        for ano in sorted(out["ano"].unique()):
            g = out[out["ano"] == ano]
            if "T4" in set(g["trimestre"].unique()):
                continue

            new_rows = []
            for code in all_codes:
                a = anual_map.get((int(ano), code), np.nan)
                if np.isfinite(a):
                    new_rows.append((int(ano), "T4", code, float(a)))

            if new_rows:
                out = pd.concat([out, pd.DataFrame(new_rows, columns=out.columns)], ignore_index=True)

        return out

    def _build_horizontal(
        self, 
        qdata: pd.DataFrame, 
        schema: List[Tuple[str, str]]
    ) -> pd.DataFrame:
        """Constrói tabela horizontal (períodos como colunas)."""
        qdata = qdata.copy()
        qdata["periodo"] = qdata["ano"].astype(str) + qdata["trimestre"]
        qdata["valor"] = qdata["valor"].apply(lambda x: _normalize_value(x, 3))

        piv = qdata.pivot_table(
            index="code", columns="periodo", values="valor", aggfunc="first"
        )

        def sort_key(p):
            try:
                return (int(p[:4]), _quarter_order(p[4:]))
            except:
                return (9999, 99)

        cols = sorted(piv.columns, key=sort_key)
        piv = piv[cols]

        code_order = {c: i for i, (c, _) in enumerate(schema)}
        piv = piv.reindex(sorted(piv.index, key=lambda x: code_order.get(x, 999)))

        code_to_name = {c: n for c, n in schema}
        piv.insert(0, "conta", piv.index.map(lambda x: code_to_name.get(x, x)))
        piv = piv.reset_index().rename(columns={"code": "cd_conta"})

        return piv

    def padronizar_e_salvar_ticker(self, ticker: str) -> Tuple[bool, str]:
        """Pipeline completo de padronização do BP (BPA + BPP)."""
        self._current_ticker = ticker.upper().strip()
        
        # 1. Carregar dados (usa pasta com variantes)
        bpa_tri, bpa_anu, bpp_tri, bpp_anu = self._load_inputs(ticker)
        
        # 2. Detectar padrão fiscal
        fiscal_info = _detect_fiscal_year_pattern(bpa_tri, bpa_anu, ticker)
        
        # 3. Obter esquemas - CORREÇÃO: passa df_bpp para detecção dinâmica do PL
        bpa_schema = _get_bpa_schema(ticker)
        bpp_schema = _get_bpp_schema(ticker, bpp_tri)
        
        # ========== PROCESSAR BPA ==========
        bpa_qtot = self._build_quarter_values(bpa_tri, bpa_schema, fiscal_info)
        bpa_anual = self._extract_annual_values(bpa_anu, bpa_schema, fiscal_info)
        bpa_qtot = self._add_t4_from_annual(bpa_qtot, bpa_anual, fiscal_info, bpa_schema)
        bpa_out = self._build_horizontal(bpa_qtot, bpa_schema)
        
        # ========== PROCESSAR BPP ==========
        bpp_qtot = self._build_quarter_values(bpp_tri, bpp_schema, fiscal_info)
        bpp_anual = self._extract_annual_values(bpp_anu, bpp_schema, fiscal_info)
        bpp_qtot = self._add_t4_from_annual(bpp_qtot, bpp_anual, fiscal_info, bpp_schema)
        bpp_out = self._build_horizontal(bpp_qtot, bpp_schema)
        
        # 8. Salvar - CORREÇÃO: salva na pasta encontrada (variante)
        pasta = get_pasta_balanco(ticker, self.pasta_balancos)
        
        bpa_out.to_csv(pasta / "bpa_padronizado.csv", index=False, encoding="utf-8")
        bpp_out.to_csv(pasta / "bpp_padronizado.csv", index=False, encoding="utf-8")
        
        # 9. Mensagem de retorno
        fiscal_status = "MAR-FEV" if fiscal_info.is_mar_fev else ("PADRÃO" if fiscal_info.is_standard else "IRREGULAR")
        tipo = _get_tipo_empresa(ticker)
        pl_code = _detect_pl_code_from_data(bpp_tri) if _is_banco(ticker) else "2.03"
        
        n_periodos_bpa = len([c for c in bpa_out.columns if c not in ["cd_conta", "conta"]])
        n_periodos_bpp = len([c for c in bpp_out.columns if c not in ["cd_conta", "conta"]])
        
        pasta_usada = pasta.name
        pasta_info = f" (pasta: {pasta_usada})" if pasta_usada != ticker.upper() else ""
        
        msg_parts = [
            f"Fiscal: {fiscal_status}",
            f"Tipo: {tipo}",
            f"PL: {pl_code}" if _is_banco(ticker) else None,
            f"BPA: {n_periodos_bpa} períodos",
            f"BPP: {n_periodos_bpp} períodos",
        ]
        
        msg = f"bpa_padronizado.csv + bpp_padronizado.csv{pasta_info} | {' | '.join(m for m in msg_parts if m)}"
        
        return True, msg


# ======================================================================================
# CLI - MAIN
# ======================================================================================

def main():
    parser = argparse.ArgumentParser(description="Padroniza BPA e BPP das empresas")
    parser.add_argument("--modo", choices=["quantidade", "ticker", "lista", "faixa"], default="quantidade")
    parser.add_argument("--quantidade", default="10")
    parser.add_argument("--ticker", default="")
    parser.add_argument("--lista", default="")
    parser.add_argument("--faixa", default="")
    args = parser.parse_args()

    df = load_mapeamento_consolidado()
    df = df[df["cnpj"].notna()].reset_index(drop=True)

    if args.modo == "quantidade":
        df_sel = df.head(int(args.quantidade))
    elif args.modo == "ticker":
        ticker_upper = args.ticker.upper()
        df_sel = df[df["ticker"].str.upper().str.contains(ticker_upper, case=False, na=False, regex=False)]
    elif args.modo == "lista":
        tickers = [t.strip().upper() for t in args.lista.split(",") if t.strip()]
        mask = df["ticker"].str.upper().apply(lambda x: any(t in x for t in tickers) if pd.notna(x) else False)
        df_sel = df[mask]
    elif args.modo == "faixa":
        inicio, fim = map(int, args.faixa.split("-"))
        df_sel = df.iloc[inicio - 1 : fim]
    else:
        df_sel = df.head(10)

    print(f"\n>>> JOB: PADRONIZAR BP (BPA + BPP) <<<")
    print(f"Modo: {args.modo} | Selecionadas: {len(df_sel)}")
    print("Saída: balancos/<TICKER>/bpa_padronizado.csv + bpp_padronizado.csv\n")

    pad = PadronizadorBP()
    ok_count, err_count, irregular_count = 0, 0, 0

    for _, row in df_sel.iterrows():
        ticker_str = str(row["ticker"]).upper().strip()
        ticker = ticker_str.split(';')[0] if ';' in ticker_str else ticker_str

        # CORREÇÃO: Usa get_pasta_balanco que busca variantes
        pasta = get_pasta_balanco(ticker)
        if not pasta.exists():
            err_count += 1
            print(f"❌ {ticker}: pasta {pasta} não existe (nem variantes)")
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

    print("\n" + "="*70)
    print(f"Finalizado: OK={ok_count} | ERRO={err_count}")
    if irregular_count > 0:
        print(f"            Anos fiscais especiais (MAR-FEV/irregular): {irregular_count}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
