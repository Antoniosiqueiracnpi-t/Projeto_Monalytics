# padronizar_bp.py
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

import numpy as np
import pandas as pd

# ======================================================================================
# DETECÇÃO INTELIGENTE DE CONTAS BANCÁRIAS
# ======================================================================================

# Padrões de busca por descrição (regex) - ordem de prioridade
PATTERNS_OPERACOES_CREDITO = [
    r"Opera[çc][õo]es\s+de\s+Cr[ée]dito",  # "Operações de Crédito"
    r"Carteira\s+de\s+Cr[ée]dito",          # "Carteira de Crédito"
    r"Empr[ée]stimos\s+e\s+Receb[ií]veis",  # "Empréstimos e Recebíveis"
]

PATTERNS_PROVISAO_PDD = [
    r"Provis[ãa]o\s+para\s+Perda[s]?\s+Esperada[s]?",           # "Provisão para Perdas Esperadas"
    r"\(-?\)\s*Provis[ãa]o\s+para\s+Perda",                      # "(-) Provisão para Perda"
    r"Provis[ãa]o\s+para\s+Perda[s]?\s+Esperada[s]?\s+Associada", # Completo
    r"PCLD",                                                      # Sigla antiga
    r"Provis[ãa]o\s+para\s+Cr[ée]ditos?\s+de\s+Liquida[çc][ãa]o", # "Provisão para Créditos..."
]

PATTERNS_DEPOSITOS = [
    r"^Dep[óo]sitos$",           # "Depósitos" (exato)
    r"^Dep[óo]sitos\s*$",        # "Depósitos " (com espaço)
]

# Códigos conhecidos por banco (fallback)
CODIGOS_OPERACOES_CREDITO = [
    "1.02.04.04",  # BBAS3, BBDC4
    "1.02.03.04",  # ITUB4
    "1.05.03.02",  # Formato antigo (pré-IFRS9)
    "1.02.01",     # Alguns bancos menores
]

CODIGOS_PROVISAO_PDD = [
    "1.02.04.05",  # BBAS3, BBDC4
    "1.02.03.06",  # ITUB4
    "1.05.03.03",  # Formato antigo
    "1.02.02",     # Alguns bancos menores
]

CODIGOS_DEPOSITOS = [
    "2.02.01",  # BBAS3, BBDC4
    "2.03.01",  # ITUB4
]


def _detect_account_by_patterns(
    df: pd.DataFrame, 
    patterns: List[str], 
    fallback_codes: List[str],
    prefer_nonzero: bool = True,
    level_filter: Optional[str] = None
) -> Optional[str]:
    """
    Detecta código de conta por padrões de descrição, com fallback para códigos conhecidos.
    
    Args:
        df: DataFrame com colunas 'cd_conta', 'ds_conta', 'valor_mil'
        patterns: Lista de regex para buscar na descrição
        fallback_codes: Lista de códigos conhecidos como fallback
        prefer_nonzero: Se True, prefere contas com valor != 0
        level_filter: Se definido, filtra códigos que começam com este prefixo (ex: "1.02")
    
    Returns:
        Código da conta encontrada ou None
    """
    if df.empty:
        return fallback_codes[0] if fallback_codes else None
    
    # Garantir que temos as colunas necessárias
    if "ds_conta" not in df.columns or "cd_conta" not in df.columns:
        return fallback_codes[0] if fallback_codes else None
    
    # 1. Buscar por padrão de descrição
    for pattern in patterns:
        mask = df["ds_conta"].str.contains(pattern, case=False, regex=True, na=False)
        matches = df[mask]
        
        if level_filter:
            matches = matches[matches["cd_conta"].str.startswith(level_filter)]
        
        if not matches.empty:
            if prefer_nonzero and "valor_mil" in df.columns:
                # Preferir conta com valor diferente de zero
                nonzero = matches[matches["valor_mil"].abs() > 0]
                if not nonzero.empty:
                    return str(nonzero["cd_conta"].iloc[0])
            return str(matches["cd_conta"].iloc[0])
    
    # 2. Fallback: buscar códigos conhecidos que existam no DataFrame
    for code in fallback_codes:
        if code in df["cd_conta"].values:
            if prefer_nonzero and "valor_mil" in df.columns:
                row = df[df["cd_conta"] == code]
                if not row.empty and row["valor_mil"].abs().iloc[0] > 0:
                    return code
            else:
                return code
    
    # 3. Último fallback: primeiro código conhecido
    return fallback_codes[0] if fallback_codes else None


def _detect_operacoes_credito(df_bpa: pd.DataFrame) -> str:
    """Detecta código de Operações de Crédito no BPA."""
    return _detect_account_by_patterns(
        df_bpa, 
        PATTERNS_OPERACOES_CREDITO, 
        CODIGOS_OPERACOES_CREDITO,
        prefer_nonzero=True,
        level_filter="1.02"
    ) or "1.02.04.04"


def _detect_provisao_pdd(df_bpa: pd.DataFrame) -> str:
    """Detecta código de Provisão PDD no BPA."""
    return _detect_account_by_patterns(
        df_bpa, 
        PATTERNS_PROVISAO_PDD, 
        CODIGOS_PROVISAO_PDD,
        prefer_nonzero=True,  # Importante: alguns bancos têm a conta mas valor=0
        level_filter="1.02"
    ) or "1.02.04.05"


def _detect_depositos(df_bpp: pd.DataFrame) -> str:
    """Detecta código de Depósitos no BPP."""
    return _detect_account_by_patterns(
        df_bpp, 
        PATTERNS_DEPOSITOS, 
        CODIGOS_DEPOSITOS,
        prefer_nonzero=True,
        level_filter="2.0"
    ) or "2.02.01"


# ======================================================================================
# MAPEAMENTOS SEMÂNTICOS PARA DETECÇÃO ADAPTATIVA DE ESTRUTURA
# ======================================================================================

# Mapeamentos semânticos para contas de bancos (descrição → conta padronizada)
# Usado quando há mudança de estrutura entre períodos

SEMANTIC_MAP_BPA_BANCOS: Dict[str, List[str]] = {
    # Conta padronizada: [padrões regex de descrição]
    "1": [r"^Ativo\s+Total$"],
    "1.01": [r"^Caixa\s+e\s+Equivalentes", r"^Disponibilidades$"],
    "1.02": [r"^Ativos?\s+Financeiros?$"],
    
    # Depósito Compulsório - pode estar em diferentes níveis
    "1.02.01": [
        r"Dep[óo]sito[s]?\s+Compuls[óo]rio",
        r"Compuls[óo]rio.*Banco\s+Central",
        r"Ativos\s+Financeiros.*Valor\s+Justo.*Resultado",  # Estrutura antiga
    ],
    
    # Ativos ao Valor Justo
    "1.02.02": [
        r"Ativos\s+Financeiros.*Valor\s+Justo.*Outros\s+Resultados",
        r"Valor\s+Justo.*ORA",
        r"FVOCI",
    ],
    
    # Ativos ao Custo Amortizado
    "1.02.03": [
        r"Ativos\s+Financeiros.*Custo\s+Amortizado",
        r"Custo\s+Amortizado",
    ],
    
    # Estrutura nova (2025+)
    "1.02.04": [
        r"Ativos\s+Financeiros.*Custo\s+Amortizado",
    ],
    
    # Operações de Crédito
    "1.02.04.04": [
        r"Opera[çc][õo]es\s+de\s+Cr[ée]dito",
        r"Empr[ée]stimos.*Adiantamentos.*Clientes",
    ],
    
    # Provisão PDD
    "1.02.04.05": [
        r"Provis[ãa]o.*Perda[s]?\s+Esperada",
        r"PCLD",
        r"Provis[ãa]o.*Risco.*Cr[ée]dito",
    ],
    
    # Tributos
    "1.03": [r"^Tributos", r"^Tributos\s+Diferidos"],
    
    # Outros Ativos
    "1.04": [r"^Outros\s+Ativos$"],
    
    # Investimentos
    "1.05": [r"^Investimentos$"],
    
    # Imobilizado
    "1.06": [r"^Imobilizado$"],
    
    # Intangível
    "1.07": [r"^Intang[íi]vel$"],
}

SEMANTIC_MAP_BPP_BANCOS: Dict[str, List[str]] = {
    # Passivo Total
    "2": [r"^Passivo\s+Total$"],
    
    # Passivos ao Valor Justo
    "2.01": [
        r"Passivos?\s+Financeiros?.*Valor\s+Justo",
        r"FVTPL",
    ],
    
    # Passivos ao Custo Amortizado
    "2.02": [
        r"Passivos?\s+Financeiros?.*Custo\s+Amortizado",
    ],
    
    # Depósitos
    "2.02.01": [
        r"^Dep[óo]sitos$",
        r"Dep[óo]sitos\s+de\s+Clientes",
    ],
    
    # Captações
    "2.02.02": [
        r"Capta[çc][õo]es.*Mercado\s+Aberto",
    ],
    
    # Recursos Interbancários
    "2.02.03": [
        r"Recursos.*Mercado\s+Interfinanceiro",
        r"Recursos.*Interbancário",
    ],
    
    # Outras Captações
    "2.02.04": [
        r"Outras\s+Capta[çc][õo]es",
    ],
    
    # Provisões - estrutura antiga era 2.04, nova é 2.03
    "2.03": [
        r"^Provis[õo]es$",
        r"Provis[ãa]o.*Contingentes",
        r"Passivos\s+Financeiros.*Custo\s+Amortizado",  # Estrutura antiga
    ],
    
    # Passivos Fiscais
    "2.04": [
        r"^Passivos?\s+Fiscais?$",
        r"^Provis[õo]es$",  # Estrutura antiga
    ],
    
    # Outros Passivos
    "2.05": [
        r"^Outros\s+Passivos$",
        r"^Passivos?\s+Fiscais?$",  # Estrutura antiga
    ],
    
    # Passivos sobre Ativos Não Correntes
    "2.06": [
        r"Ativos\s+N[ãa]o\s+Correntes?\s+a\s+Venda",
        r"^Outros\s+Passivos$",  # Estrutura antiga
    ],
    
    # Patrimônio Líquido - pode estar em 2.07 ou 2.08
    "2.07": [
        r"Patrim[oô]nio\s+L[íi]quido.*Consolidado",
        r"^Patrim[oô]nio\s+L[íi]quido$",
        r"Ativos\s+N[ãa]o\s+Correntes",  # Estrutura antiga
    ],
    
    "2.08": [
        r"Patrim[oô]nio\s+L[íi]quido.*Consolidado",
        r"^Patrim[oô]nio\s+L[íi]quido$",
    ],
    
    # Subcontas do PL
    "2.07.01": [
        r"Patrim[oô]nio.*Atribu[íi]do.*Controlador",
        r"Capital\s+Social\s+Realizado",
    ],
    
    "2.08.01": [
        r"Capital\s+Social\s+Realizado",
        r"Patrim[oô]nio.*Atribu[íi]do.*Controlador",
    ],
    
    "2.07.01.01": [r"^Capital\s+Social\s+Realizado$"],
    "2.08.01.01": [r"^Capital\s+Social\s+Realizado$"],
    
    "2.07.01.02": [r"^Reservas?\s+de\s+Capital$"],
    "2.08.02": [r"^Reservas?\s+de\s+Capital$"],
    
    "2.07.01.04": [r"^Reservas?\s+de\s+Lucros?$"],
    "2.08.04": [r"^Reservas?\s+de\s+Lucros?$"],
    
    "2.07.01.05": [r"Lucros.*Acumulados", r"Preju[íi]zos.*Acumulados"],
    "2.08.05": [r"Lucros.*Acumulados", r"Preju[íi]zos.*Acumulados"],
    
    "2.07.01.08": [r"Outros\s+Resultados\s+Abrangentes"],
    "2.08.08": [r"Outros\s+Resultados\s+Abrangentes"],
    
    "2.07.02": [r"N[ãa]o\s+Controladores", r"Minorit[áa]rios"],
    "2.08.09": [r"N[ãa]o\s+Controladores", r"Minorit[áa]rios"],
}


# ======================================================================================
# FUNÇÕES AUXILIARES
# ======================================================================================

def get_ticker_principal(ticker: str) -> str:
    """Retorna o ticker principal (primeiro se houver múltiplos)."""
    return ticker.split(';')[0].strip().upper()


def load_mapeamento_consolidado() -> pd.DataFrame:
    """Carrega mapeamento consolidado (preferencial) ou fallback robusto."""
    # 1) Preferir multi_ticker_utils (mas NÃO quebrar se o CSV não estiver no cwd)
    try:
        from multi_ticker_utils import load_mapeamento_consolidado as load_map
        try:
            return load_map()
        except FileNotFoundError:
            # cai no fallback abaixo
            pass
    except ImportError:
        pass

    # 2) Fallback: buscar arquivo em múltiplos locais e com múltiplos nomes
    base_dirs = []
    try:
        base_dirs.append(Path.cwd())
    except Exception:
        pass

    # repo root provável: .../src/padronizar_bp.py -> parents[1] = raiz do repo
    try:
        base_dirs.append(Path(__file__).resolve().parents[1])
        base_dirs.append(Path(__file__).resolve().parent)  # /src
    except Exception:
        pass

    # remover duplicados preservando ordem
    seen = set()
    base_dirs = [p for p in base_dirs if not (str(p) in seen or seen.add(str(p)))]

    filenames = [
        # nomes usados no Projeto_Monalytics
        "mapeamento_b3_consolidado.csv",
        "mapeamento_final_b3_completo_utf8.csv",
        # legados (caso existam em algum ambiente)
        "mapeamento_cnpj_consolidado.csv",
        "mapeamento_cnpj_ticker.csv",
        # às vezes ficam dentro de src/
        "src/mapeamento_b3_consolidado.csv",
        "src/mapeamento_final_b3_completo_utf8.csv",
        "src/mapeamento_cnpj_consolidado.csv",
        "src/mapeamento_cnpj_ticker.csv",
    ]

    tried = []
    for d in base_dirs:
        for fname in filenames:
            p = (d / fname).resolve()
            tried.append(str(p))
            if p.exists():
                # tentar com separador ; e encodings comuns
                for enc in ("utf-8-sig", "utf-8", "latin1"):
                    try:
                        return pd.read_csv(p, sep=";", encoding=enc)
                    except Exception:
                        pass
                # fallback final sem encoding explícito
                try:
                    return pd.read_csv(p, sep=";")
                except Exception:
                    return pd.read_csv(p)

    raise FileNotFoundError(
        "Nenhum arquivo de mapeamento encontrado. Procurado em:\n- " + "\n- ".join(tried)
    )


# ======================================================================================
# CORREÇÃO 1: BUSCA INTELIGENTE DE PASTA POR VARIANTES DE TICKER
# ======================================================================================

def _find_balancos_dir() -> Path:
    """Encontra o diretório 'balancos' em múltiplos locais possíveis."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    search_paths = [
        Path("balancos"),              # Diretório atual
        script_dir / "balancos",       # src/balancos
        project_root / "balancos",     # raiz/balancos
    ]
    
    for path in search_paths:
        if path.exists() and path.is_dir():
            return path
    
    # Fallback para o caminho padrão (será criado se necessário)
    return project_root / "balancos"


def get_pasta_balanco(ticker: str, pasta_base: Optional[Path] = None) -> Path:
    """
    Retorna o caminho da pasta de balanços do ticker.
    
    CORREÇÃO: Busca variantes do ticker (3, 4, 5, 6, 11) se pasta exata não existir.
    Exemplo: Se buscar BBDC3 e não existir, procura BBDC4, BBDC5, etc.
    """
    if pasta_base is None:
        pasta_base = _find_balancos_dir()
    
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

# Esquema BASE para bancos - será expandido dinamicamente com contas detectadas
BPA_BANCOS_BASE: List[Tuple[str, str]] = [
    ("1", "Ativo Total"),
    ("1.01", "Caixa e Equivalentes de Caixa"),
    ("1.02", "Ativos Financeiros"),
    ("1.02.01", "Depósito Compulsório Banco Central"),
    ("1.02.02", "Ativos Financeiros ao Valor Justo através do Resultado"),
    ("1.02.03", "Ativos Financeiros ao Valor Justo através de ORA"),
    ("1.02.04", "Ativos Financeiros ao Custo Amortizado"),
    # Contas de crédito serão adicionadas dinamicamente
    ("1.03", "Tributos"),
    ("1.04", "Outros Ativos"),
    ("1.05", "Investimentos"),
    ("1.06", "Imobilizado"),
    ("1.07", "Intangível"),
]

# Manter compatibilidade com código existente
BPA_BANCOS = BPA_BANCOS_BASE


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
    # Nota: Depósitos podem estar em 2.02.01 (alguns bancos) ou 2.03.01 (ITUB4, outros)
    schema = [
        ("2", "Passivo Total"),
        ("2.01", "Passivos Financeiros ao Valor Justo através do Resultado"),
        ("2.02", "Passivos Financeiros ao Custo Amortizado"),
        ("2.02.01", "Depósitos"),
        ("2.02.02", "Captações no Mercado Aberto"),
        ("2.02.03", "Recursos de Mercados Interbancários"),
        ("2.02.04", "Outras Captações"),
        ("2.03", "Provisões"),
        ("2.03.01", "Depósitos"),  # Formato alternativo (ITUB4)
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


def _build_bpa_schema_for_bank(df_bpa: pd.DataFrame) -> List[Tuple[str, str]]:
    """
    Constrói esquema BPA dinâmico para bancos baseado nos dados reais.
    
    CORREÇÃO: Detecta automaticamente os códigos de:
    - Operações de Crédito (varia: 1.02.03.04, 1.02.04.04)
    - Provisão PDD (varia: 1.02.03.06, 1.02.04.05)
    """
    # Detectar códigos reais
    cod_credito = _detect_operacoes_credito(df_bpa)
    cod_provisao = _detect_provisao_pdd(df_bpa)
    
    # Extrair prefixo comum (ex: "1.02.04" de "1.02.04.04")
    prefix_credito = ".".join(cod_credito.split(".")[:-1]) if "." in cod_credito else "1.02.04"
    
    schema = [
        ("1", "Ativo Total"),
        ("1.01", "Caixa e Equivalentes de Caixa"),
        ("1.02", "Ativos Financeiros"),
        ("1.02.01", "Depósito Compulsório Banco Central"),
        ("1.02.02", "Ativos Financeiros ao Valor Justo através do Resultado"),
        ("1.02.03", "Ativos Financeiros ao Valor Justo através de ORA"),
        ("1.02.04", "Ativos Financeiros ao Custo Amortizado"),
    ]
    
    # Adicionar conta pai se diferente (ex: 1.02.03 para ITUB4)
    if prefix_credito not in ["1.02.03", "1.02.04"]:
        schema.append((prefix_credito, "Empréstimos e Recebíveis"))
    
    # Adicionar contas de crédito detectadas
    schema.append((cod_credito, "Operações de Crédito"))
    schema.append((cod_provisao, "Provisão para Perdas Esperadas"))
    
    # Contas finais
    schema.extend([
        ("1.03", "Tributos"),
        ("1.04", "Outros Ativos"),
        ("1.05", "Investimentos"),
        ("1.06", "Imobilizado"),
        ("1.07", "Intangível"),
    ])
    
    return schema


def _build_bpp_schema_for_bank_v2(df_bpp: pd.DataFrame) -> List[Tuple[str, str]]:
    """
    Constrói esquema BPP dinâmico para bancos baseado nos dados reais.
    
    CORREÇÃO v2: Detecta automaticamente:
    - Código do Patrimônio Líquido (2.07 ou 2.08)
    - Código dos Depósitos (2.02.01 ou 2.03.01)
    """
    pl_code = _detect_pl_code_from_data(df_bpp)
    cod_depositos = _detect_depositos(df_bpp)
    
    # Determinar se depósitos estão em 2.02 ou 2.03
    depositos_prefix = cod_depositos.split(".")[1] if "." in cod_depositos else "02"
    
    schema = [
        ("2", "Passivo Total"),
        ("2.01", "Passivos Financeiros ao Valor Justo através do Resultado"),
        ("2.02", "Passivos Financeiros ao Custo Amortizado"),
    ]
    
    # Adicionar Depósitos no local correto
    if depositos_prefix == "02":
        schema.append(("2.02.01", "Depósitos"))
        schema.extend([
            ("2.02.02", "Captações no Mercado Aberto"),
            ("2.02.03", "Recursos Mercado Interfinanceiro"),
            ("2.02.04", "Outras Captações"),
            ("2.03", "Provisões"),
        ])
    else:
        schema.extend([
            ("2.02.01", "Depósitos"),  # Pode não existir
            ("2.02.02", "Captações no Mercado Aberto"),
            ("2.02.03", "Recursos Mercado Interfinanceiro"),
            ("2.02.04", "Outras Captações"),
            ("2.03", "Provisões"),
            ("2.03.01", "Depósitos"),  # ITUB4
        ])
    
    schema.extend([
        ("2.04", "Passivos Fiscais"),
        ("2.05", "Outros Passivos"),
        ("2.06", "Passivos sobre Ativos Não Correntes a Venda"),
    ])
    
    # Adicionar conta 2.07 intermediária se PL estiver em 2.08
    pl_num = int(pl_code.split('.')[1]) if '.' in pl_code else 7
    if pl_num > 7:
        schema.append(("2.07", "Passivos sobre Ativos Descontinuados"))
    
    # Adicionar PL e subcontas
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
    ("1.01.02", "Aplicações Financeiras"),  # Float investido - Ativo Principal
    ("1.01.03", "Contas a Receber"),
    ("1.01.03.01", "Créditos das Operações"),  # Prêmios a receber
    ("1.01.03.01.01", "Prêmios a Receber de Segurados"),
    ("1.01.06", "Tributos a Recuperar"),
    ("1.01.08", "Outros Ativos Circulantes"),
    ("1.01.08.03.02", "Ativos de Resseguro"),  # CRÍTICO: Recuperação de sinistros
    ("1.01.08.03.03", "Custos de Aquisição Diferidos"),  # CRÍTICO: Comissões diferidas
    ("1.02", "Ativo Não Circulante"),
    ("1.02.01", "Ativo Realizável a Longo Prazo"),
    ("1.02.01.01", "Aplicações Financeiras LP"),
    ("1.02.01.06", "Tributos Diferidos"),
    ("1.02.02", "Investimentos"),
    ("1.02.02.02", "Propriedades para Investimento"),
    ("1.02.03", "Imobilizado"),
    ("1.02.04", "Intangível"),
]

BPP_SEGURADORAS: List[Tuple[str, str]] = [
    ("2", "Passivo Total"),
    ("2.01", "Passivo Circulante"),
    ("2.01.01", "Obrigações Sociais e Trabalhistas"),
    ("2.01.02", "Fornecedores"),
    ("2.01.03", "Obrigações Fiscais"),
    ("2.01.04", "Empréstimos e Financiamentos"),  # Alguns têm (PSSA3)
    ("2.01.05", "Outras Obrigações"),
    ("2.01.05.02.01", "Dividendos e JCP a Pagar"),
    ("2.01.05.02.04", "Passivos de Contratos de Seguros"),  # CRÍTICO: Provisões Técnicas CP
    ("2.01.05.02.05", "Débitos de Operações com Seguros"),
    ("2.01.05.02.06", "Passivos Financeiros"),  # PSSA3 tem debêntures
    ("2.02", "Passivo Não Circulante"),
    ("2.02.01", "Empréstimos e Financiamentos"),
    ("2.02.02", "Outras Obrigações"),
    ("2.02.02.02.03", "Passivos de Contratos de Seguros LP"),  # CRÍTICO: Provisões Técnicas LP
    ("2.02.03", "Tributos Diferidos"),
    ("2.02.04", "Provisões"),
    ("2.03", "Patrimônio Líquido Consolidado"),
    ("2.03.01", "Capital Social Realizado"),
    ("2.03.02", "Reservas de Capital"),
    ("2.03.02.05", "Ações em Tesouraria"),
    ("2.03.04", "Reservas de Lucros"),
    ("2.03.09", "Participação dos Acionistas Não Controladores"),
]

BPA_HOLDINGS_SEGUROS: List[Tuple[str, str]] = [
    ("1", "Ativo Total"),
    ("1.01", "Ativo Circulante"),
    ("1.01.01", "Caixa e Equivalentes de Caixa"),
    ("1.01.02", "Aplicações Financeiras"),
    ("1.01.03", "Contas a Receber"),
    ("1.01.06", "Tributos a Recuperar"),
    ("1.01.08", "Outros Ativos Circulantes"),
    ("1.02", "Ativo Não Circulante"),
    ("1.02.01", "Ativo Realizável a Longo Prazo"),
    ("1.02.02", "Investimentos"),  # CRÍTICO: Participações nas seguradoras coligadas
    ("1.02.03", "Imobilizado"),
    ("1.02.04", "Intangível"),
]

BPP_HOLDINGS_SEGUROS: List[Tuple[str, str]] = [
    ("2", "Passivo Total"),
    ("2.01", "Passivo Circulante"),
    ("2.01.01", "Obrigações Sociais e Trabalhistas"),
    ("2.01.02", "Fornecedores"),
    ("2.01.03", "Obrigações Fiscais"),
    ("2.01.04", "Empréstimos e Financiamentos"),
    ("2.01.05", "Outras Obrigações"),
    ("2.01.05.02.01", "Dividendos e JCP a Pagar"),
    ("2.01.05.02.03", "Comissões a Apropriar"),  # CRÍTICO: BBSE3 específico
    ("2.02", "Passivo Não Circulante"),
    ("2.02.01", "Empréstimos e Financiamentos"),
    ("2.02.01.04.01", "Comissões a Apropriar LP"),  # CRÍTICO: BBSE3 LP
    ("2.02.02", "Outras Obrigações"),
    ("2.03", "Patrimônio Líquido Consolidado"),
    ("2.03.01", "Capital Social Realizado"),
    ("2.03.02", "Reservas de Capital"),
    ("2.03.04", "Reservas de Lucros"),
    ("2.03.09", "Participação dos Acionistas Não Controladores"),
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
# Empresa de tecnologia/marketplace (será tratada como empresa geral)
TICKERS_TECH_MARKETPLACE: Set[str] = {"WIZC3"}


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


def _get_bpa_schema(ticker: str, df_bpa: Optional[pd.DataFrame] = None) -> List[Tuple[str, str]]:
    """Retorna o esquema BPA apropriado. Para bancos, usa detecção dinâmica."""
    ticker_upper = ticker.upper().strip()
    
    if _is_holding_seguros(ticker_upper):
        return BPA_HOLDINGS_SEGUROS
    elif _is_seguradora_operacional(ticker_upper):
        return BPA_SEGURADORAS
    elif _is_banco(ticker_upper):
        if df_bpa is not None and not df_bpa.empty:
            return _build_bpa_schema_for_bank(df_bpa)
        return BPA_BANCOS_BASE
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
            return _build_bpp_schema_for_bank_v2(df_bpp)
        # Fallback genérico
        return [
            ("2", "Passivo Total"),
            ("2.01", "Passivos Financeiros ao Valor Justo"),
            ("2.02", "Passivos Financeiros ao Custo Amortizado"),
            ("2.02.01", "Depósitos"),
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


def _normalizar_escala_monetaria(valor: float) -> float:
    """Conversão de unidade (centavos → R$ mil)"""
    if not np.isfinite(valor) or valor == 0:
        return valor
    return valor / 10_000_000

def _normalize_value(v: float, decimals: int = 3) -> float:
    """Arredondamento de precisão"""
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
# DETECÇÃO E TRATAMENTO DE MUDANÇA DE ESTRUTURA DE PLANO DE CONTAS
# ======================================================================================

def _detect_structure_change(df: pd.DataFrame, key_accounts: List[str]) -> bool:
    """
    Detecta se houve mudança de estrutura do plano de contas entre períodos.
    
    Verifica se os mesmos códigos de conta existem em todos os períodos.
    Se um código importante desaparece ou surge, indica mudança de estrutura.
    
    Args:
        df: DataFrame com dados trimestrais
        key_accounts: Lista de códigos de conta chave para verificar
    
    Returns:
        True se detectou mudança de estrutura, False caso contrário
    """
    if df.empty or "data_fim" not in df.columns:
        return False
    
    df = df.copy()
    
    # Agrupar por período
    df["_periodo"] = df["data_fim"].dt.to_period("Q")
    periodos = df["_periodo"].unique()
    
    if len(periodos) < 2:
        return False
    
    # Para cada período, verificar quais contas-chave existem
    structure_by_period = {}
    for periodo in periodos:
        df_periodo = df[df["_periodo"] == periodo]
        codes_present = set(df_periodo["cd_conta"].unique())
        # Verificar quais contas-chave estão presentes
        key_present = frozenset(c for c in key_accounts if c in codes_present)
        structure_by_period[periodo] = key_present
    
    # Se estrutura variou entre períodos, houve mudança
    unique_structures = set(structure_by_period.values())
    return len(unique_structures) > 1


def _find_account_by_description(
    df_periodo: pd.DataFrame, 
    patterns: List[str],
    level_hint: Optional[str] = None
) -> Optional[Tuple[str, float]]:
    """
    Busca conta por padrões de descrição em um período específico.
    
    Args:
        df_periodo: DataFrame de um período específico
        patterns: Lista de regex para buscar na descrição
        level_hint: Prefixo esperado do código (ex: "1.02", "2.03")
    
    Returns:
        Tupla (código_encontrado, valor) ou None
    """
    for pattern in patterns:
        mask = df_periodo["ds_conta"].str.contains(pattern, case=False, regex=True, na=False)
        matches = df_periodo[mask]
        
        if level_hint:
            matches = matches[matches["cd_conta"].str.startswith(level_hint)]
        
        if not matches.empty:
            # Preferir conta com valor não-zero
            if "valor_mil" in matches.columns:
                nonzero = matches[matches["valor_mil"].abs() > 0]
                if not nonzero.empty:
                    row = nonzero.iloc[0]
                else:
                    row = matches.iloc[0]
            else:
                row = matches.iloc[0]
            
            valor = float(row["valor_mil"]) if "valor_mil" in row and pd.notna(row["valor_mil"]) else np.nan
            return (str(row["cd_conta"]), valor)
    
    return None


def _build_semantic_mapping_for_period(
    df_periodo: pd.DataFrame,
    semantic_map: Dict[str, List[str]],
    is_bpa: bool = True
) -> Dict[str, Tuple[str, float]]:
    """
    Constrói mapeamento semântico de contas para um período específico.
    
    Mapeia cada conta padronizada para o código real + valor naquele período.
    
    Args:
        df_periodo: DataFrame com dados de um período específico
        semantic_map: Dicionário de padrões semânticos
        is_bpa: True se BPA, False se BPP
    
    Returns:
        Dicionário mapeando código padrão → (código real, valor)
    """
    mapping = {}
    
    for padrao_key, patterns in semantic_map.items():
        # Extrair hint de nível do código padrão
        base_code = padrao_key.split("_")[0] if "_" in padrao_key else padrao_key
        level_hint = ".".join(base_code.split(".")[:2]) if "." in base_code else base_code[:1]
        
        result = _find_account_by_description(df_periodo, patterns, level_hint)
        if result:
            mapping[padrao_key] = result
    
    return mapping


class PeriodAwareExtractor:
    """
    Extrator de valores que lida com mudanças de estrutura entre períodos.
    
    Para bancos com mudança de plano de contas, extrai valores baseado em
    descrição semântica em vez de códigos fixos.
    """
    
    def __init__(self, df_tri: pd.DataFrame, df_anu: pd.DataFrame, is_bpa: bool = True):
        self.df_tri = df_tri.copy()
        self.df_anu = df_anu.copy()
        self.is_bpa = is_bpa
        self.semantic_map = SEMANTIC_MAP_BPA_BANCOS if is_bpa else SEMANTIC_MAP_BPP_BANCOS
        
        # Detectar se há mudança de estrutura
        key_accounts = self._get_key_accounts()
        self.has_structure_change = _detect_structure_change(df_tri, key_accounts)
        
        # Cache de mapeamentos por período
        self._period_mappings: Dict[str, Dict] = {}
    
    def _get_key_accounts(self) -> List[str]:
        """Retorna contas-chave para detectar mudança de estrutura."""
        if self.is_bpa:
            return ["1.02.01", "1.02.02", "1.02.03", "1.02.04", "1.03", "1.04"]
        else:
            return ["2.01", "2.02", "2.03", "2.04", "2.07", "2.08"]
    
    def _get_period_key(self, ano: int, trimestre: str) -> str:
        return f"{ano}{trimestre}"
    
    def _get_mapping_for_period(self, ano: int, trimestre: str) -> Dict[str, Tuple[str, float]]:
        """Obtém ou calcula mapeamento semântico para um período."""
        key = self._get_period_key(ano, trimestre)
        
        if key not in self._period_mappings:
            # Filtrar dados do período
            mask = (self.df_tri["trimestre"] == trimestre)
            if "data_fim" in self.df_tri.columns:
                mask = mask & (self.df_tri["data_fim"].dt.year == ano)
            
            df_periodo = self.df_tri[mask]
            
            if df_periodo.empty:
                self._period_mappings[key] = {}
            else:
                self._period_mappings[key] = _build_semantic_mapping_for_period(
                    df_periodo, self.semantic_map, self.is_bpa
                )
        
        return self._period_mappings[key]
    
    def get_value_semantic(
        self, 
        standard_code: str, 
        ano: int, 
        trimestre: str,
        df_periodo: pd.DataFrame
    ) -> float:
        """
        Obtém valor para uma conta padrão usando busca semântica.
        
        Args:
            standard_code: Código padrão da conta (ex: "1.02.01")
            ano: Ano fiscal
            trimestre: Trimestre (T1, T2, T3, T4)
            df_periodo: DataFrame filtrado para o período
        
        Returns:
            Valor encontrado ou np.nan
        """
        # Buscar nos padrões semânticos
        patterns = self.semantic_map.get(standard_code, [])
        
        if not patterns:
            # Sem padrão semântico definido, tentar busca direta
            return _pick_value_for_code(df_periodo, standard_code)
        
        # Buscar por descrição
        level_hint = ".".join(standard_code.split(".")[:2]) if "." in standard_code else standard_code[:1]
        result = _find_account_by_description(df_periodo, patterns, level_hint)
        
        if result:
            return result[1]  # Retorna o valor
        
        # Fallback: busca direta pelo código
        return _pick_value_for_code(df_periodo, standard_code)


def _build_quarter_values_adaptive(
    df_tri: pd.DataFrame,
    schema: List[Tuple[str, str]],
    fiscal_info: FiscalYearInfo,
    extractor: PeriodAwareExtractor
) -> pd.DataFrame:
    """
    Versão adaptativa de _build_quarter_values que lida com mudança de estrutura.
    
    Usa extração semântica baseada em descrição quando detecta mudança de estrutura
    entre períodos.
    
    Args:
        df_tri: DataFrame com dados trimestrais
        schema: Lista de tuplas (código, descrição) do esquema padrão
        fiscal_info: Informações sobre ano fiscal
        extractor: Extrator adaptativo configurado
    
    Returns:
        DataFrame com valores extraídos por período
    """
    df = df_tri.copy()
    
    if fiscal_info.is_mar_fev:
        df["ano"] = df["data_fim"].apply(_get_fiscal_year_mar_fev)
    else:
        df["ano"] = df["data_fim"].dt.year
    
    rows = []
    
    # Agrupar por ano e trimestre
    for (ano, trimestre), g in df.groupby(["ano", "trimestre"], sort=False):
        ano = int(ano)
        trimestre = str(trimestre)
        
        for code, _ in schema:
            # Usar extração semântica
            v = extractor.get_value_semantic(code, ano, trimestre, g)
            rows.append((ano, trimestre, code, v))
    
    return pd.DataFrame(rows, columns=["ano", "trimestre", "code", "valor"])


# ======================================================================================
# CLASSE PRINCIPAL - PADRONIZADOR BP
# ======================================================================================

@dataclass
class PadronizadorBP:
    pasta_balancos: Path = field(default_factory=lambda: Path("balancos"))
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
        """
        Constrói tabela horizontal (períodos como colunas).
        Aplica conversão de escala monetária (centavos CVM → R$ mil)
        e normalização de precisão numérica.
        """
        qdata = qdata.copy()
        qdata["periodo"] = qdata["ano"].astype(str) + qdata["trimestre"]
        
        # Pipeline de normalização: escala monetária → precisão numérica
        qdata["valor"] = qdata["valor"].apply(
            lambda x: _normalize_value(
                _normalizar_escala_monetaria(x), 
                decimals=3
            )
        )
    
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


    @staticmethod
    def _period_to_tuple(periodo: str) -> Tuple[int, int]:
        """Converte 'YYYYT#' em (YYYY, #)."""
        m = re.match(r"^(\d{4})T([1-4])$", str(periodo).strip())
        if not m:
            return (9999, 99)
        return (int(m.group(1)), int(m.group(2)))

    @classmethod
    def _make_full_period_cols(cls, period_cols: List[str]) -> List[str]:
        """Gera lista contínua de períodos trimestrais entre min e max (inclusive)."""
        parsed = [cls._period_to_tuple(c) for c in period_cols]
        parsed = [p for p in parsed if p != (9999, 99)]
        if not parsed:
            return list(period_cols)

        min_y, min_q = min(parsed)
        max_y, max_q = max(parsed)

        out: List[str] = []
        y, q = min_y, min_q
        while True:
            out.append(f"{y}T{q}")
            if (y, q) == (max_y, max_q):
                break
            q += 1
            if q > 4:
                q = 1
                y += 1
            # segurança
            if len(out) > 400:
                break
        return out

    def _bank_postprocess_horizontal(self, df_out: pd.DataFrame, min_fill: float = 0.70) -> pd.DataFrame:
        """
        Exclusivo para BANCOS (BPA/BPP padronizado):
        - Mantém apenas contas principais (nível 1) e primeira subconta (nível 2): ex. '1' e '1.01'
        - Filtra contas com preenchimento >= min_fill (proporção de períodos com valor),
          MAS garante que Patrimônio Líquido nunca seja removido (mesmo se < min_fill)
        - Preenche trimestres faltantes por interpolação (linear) e, nas bordas, ffill/bfill
        - Normaliza o código do PL para um padrão único ('2.07') no output

        ✅ CORREÇÃO CRÍTICA:
        Quando o PL original é 2.08, o schema pode inserir uma conta 2.07 "Passivos sobre Ativos Descontinuados".
        Se o PL for normalizado para 2.07 sem tratar isso, ficam DUAS linhas 2.07 e o pipeline pode capturar a errada.
        Esta função remove a 2.07 "Passivos..." (quando aplicável) e garante unicidade do cd_conta.
        """
        df = df_out.copy()

        meta_cols = ["cd_conta", "conta"]
        if df.empty or any(c not in df.columns for c in meta_cols):
            return df

        period_cols = [c for c in df.columns if c not in meta_cols]

        # 1) Garantir colunas contínuas de períodos (caso falte um trimestre no dataset)
        full_period_cols = self._make_full_period_cols(period_cols)
        for c in full_period_cols:
            if c not in df.columns:
                df[c] = np.nan

        # Reordenar colunas
        full_period_cols = [c for c in full_period_cols if c in df.columns]
        df = df[meta_cols + full_period_cols]

        # 2) Converter valores para numérico
        for c in full_period_cols:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        # 3) Manter apenas níveis 1 e 2 (primeira subconta)
        cd = df["cd_conta"].astype(str).str.strip()
        is_lvl1 = cd.str.fullmatch(r"\d+")
        is_lvl2 = cd.str.fullmatch(r"\d+\.\d+")
        df = df[is_lvl1 | is_lvl2].copy()

        if df.empty:
            return df

        # -----------------------------
        # ✅ DETECÇÃO/PROTEÇÃO DO PL
        # -----------------------------
        conta_s = df["conta"].astype(str)
        cd_s = df["cd_conta"].astype(str).str.strip()

        pl_mask = conta_s.str.contains(r"Patrim[oô]nio\s+L[ií]quido", case=False, na=False)
        # Caso raríssimo: descrição não bate, mas código do PL está explícito
        pl_mask = pl_mask | cd_s.eq("2.07") | cd_s.eq("2.08")

        # (A) Se PL veio em 2.08 e existe a linha 2.07 "Passivos sobre Ativos Descontinuados",
        #     remover essa 2.07 para evitar colisão quando normalizarmos o PL para 2.07.
        #     Isso só faz sentido para BPP (contas 2.*).
        is_bpp_like = cd_s.str.startswith("2")
        passivos_descont_mask = (
            is_bpp_like
            & cd_s.eq("2.07")
            & conta_s.str.contains(r"Passivos\s+sobre\s+Ativos\s+Descontinuados", case=False, na=False)
        )

        pl_in_208 = (pl_mask & cd_s.eq("2.08")).any()
        if pl_in_208 and passivos_descont_mask.any():
            df = df[~passivos_descont_mask].copy()
            conta_s = df["conta"].astype(str)
            cd_s = df["cd_conta"].astype(str).str.strip()
            pl_mask = conta_s.str.contains(r"Patrim[oô]nio\s+L[ií]quido", case=False, na=False) | cd_s.eq("2.08") | cd_s.eq("2.07")

        # (B) Normaliza o PL para cd_conta fixo 2.07 e nome padrão no output
        if pl_mask.any():
            df.loc[pl_mask, "cd_conta"] = "2.07"
            df.loc[pl_mask, "conta"] = "Patrimônio Líquido Consolidado"

        # (C) Garantir unicidade do cd_conta (evita “pegar a linha errada” no cálculo de múltiplos)
        #     Se ainda houver duplicatas, preferir a linha do PL quando cd_conta=2.07.
        df["__is_pl"] = df["conta"].astype(str).str.contains(r"Patrim[oô]nio\s+L[ií]quido", case=False, na=False)
        # ordena para manter o PL como "primeiro" em caso de duplicata
        df = df.sort_values(by=["cd_conta", "__is_pl"], ascending=[True, False]).drop_duplicates(subset=["cd_conta"], keep="first")
        df = df.drop(columns=["__is_pl"])

        # Recalcular máscaras após dedupe
        conta_s = df["conta"].astype(str)
        cd_s = df["cd_conta"].astype(str).str.strip()
        pl_mask = conta_s.str.contains(r"Patrim[oô]nio\s+L[ií]quido", case=False, na=False) | cd_s.eq("2.07")

        # 4) Filtrar por preenchimento mínimo (ANTES de preencher), preservando PL sempre
        # ✅ CORREÇÃO: ignorar colunas que estão 100% vazias no dataset (sem dados reais)
        available_cols = [c for c in full_period_cols if df[c].notna().any()]
        cols_for_ratio = available_cols if available_cols else full_period_cols
        
        fill_ratio = df[cols_for_ratio].notna().mean(axis=1)
        
        keep_mask = (fill_ratio >= float(min_fill)) | pl_mask
        df = df[keep_mask].copy()


        if df.empty:
            return df

        # 5) Interpolação (somente lacunas internas), depois ffill/bfill nas extremidades
        vals = df[full_period_cols].astype(float)
        vals = vals.interpolate(axis=1, limit_area="inside")
        vals = vals.ffill(axis=1).bfill(axis=1)

        # 6) Garantir que o PL exista e não esteja vazio (edge cases)
        #    Aqui, como cd_conta=2.07 é único e é PL, não há risco de preencher a conta errada.
        if "2.07" in df["cd_conta"].astype(str).values:
            pl_mask2 = df["cd_conta"].astype(str).str.strip().eq("2.07")
            pl_vals = vals.loc[pl_mask2.values, :]
            if not pl_vals.empty and pl_vals.isna().all(axis=1).any():
                print("⚠️ Banco: Patrimônio Líquido sem períodos após preenchimento. Forçando 0.0 para evitar lacunas.")
                vals.loc[pl_mask2.values, :] = vals.loc[pl_mask2.values, :].fillna(0.0)

        df[full_period_cols] = vals
        return df


    def padronizar_e_salvar_ticker(self, ticker: str) -> Tuple[bool, str]:
        """Pipeline completo de padronização do BP (BPA + BPP)."""
        self._current_ticker = ticker.upper().strip()
        
        # 1. Carregar dados (usa pasta com variantes)
        bpa_tri, bpa_anu, bpp_tri, bpp_anu = self._load_inputs(ticker)
        
        # 2. Detectar padrão fiscal
        fiscal_info = _detect_fiscal_year_pattern(bpa_tri, bpa_anu, ticker)
        
        # 3. Obter esquemas - CORREÇÃO: passa df para detecção dinâmica
        bpa_schema = _get_bpa_schema(ticker, bpa_tri)
        bpp_schema = _get_bpp_schema(ticker, bpp_tri)
        
        # 4. NOVO: Criar extratores adaptativos para bancos
        bpa_extractor = None
        bpp_extractor = None
        structure_changed = False
        
        if _is_banco(ticker):
            bpa_extractor = PeriodAwareExtractor(bpa_tri, bpa_anu, is_bpa=True)
            bpp_extractor = PeriodAwareExtractor(bpp_tri, bpp_anu, is_bpa=False)
            structure_changed = bpa_extractor.has_structure_change or bpp_extractor.has_structure_change
        
        # ========== PROCESSAR BPA ==========
        if structure_changed and bpa_extractor:
            bpa_qtot = _build_quarter_values_adaptive(bpa_tri, bpa_schema, fiscal_info, bpa_extractor)
        else:
            bpa_qtot = self._build_quarter_values(bpa_tri, bpa_schema, fiscal_info)
        
        bpa_anual = self._extract_annual_values(bpa_anu, bpa_schema, fiscal_info)
        bpa_qtot = self._add_t4_from_annual(bpa_qtot, bpa_anual, fiscal_info, bpa_schema)
        bpa_out = self._build_horizontal(bpa_qtot, bpa_schema)
        
        # ========== PROCESSAR BPP ==========
        if structure_changed and bpp_extractor:
            bpp_qtot = _build_quarter_values_adaptive(bpp_tri, bpp_schema, fiscal_info, bpp_extractor)
        else:
            bpp_qtot = self._build_quarter_values(bpp_tri, bpp_schema, fiscal_info)
        
        bpp_anual = self._extract_annual_values(bpp_anu, bpp_schema, fiscal_info)
        bpp_qtot = self._add_t4_from_annual(bpp_qtot, bpp_anual, fiscal_info, bpp_schema)
        bpp_out = self._build_horizontal(bpp_qtot, bpp_schema)
        # 7B. Exclusivo bancos: reduzir contas (nível 1/2), filtrar >=70%,
        #     garantir PL sempre presente e preencher lacunas por interpolação
        if _is_banco(ticker):
            bpa_out = self._bank_postprocess_horizontal(bpa_out, min_fill=0.70)
            bpp_out = self._bank_postprocess_horizontal(bpp_out, min_fill=0.70)

        # 8. Salvar - CORREÇÃO: salva na pasta encontrada (variante)
        pasta = get_pasta_balanco(ticker, self.pasta_balancos)
        
        #bpa_out.to_csv(pasta / "bpa_padronizado.csv", index=False, encoding="utf-8")
        #bpp_out.to_csv(pasta / "bpp_padronizado.csv", index=False, encoding="utf-8")

        bpa_out.to_csv(pasta / "bpa_padronizado.csv", index=False, encoding="utf-8", float_format='%.3f')
        bpp_out.to_csv(pasta / "bpp_padronizado.csv", index=False, encoding="utf-8", float_format='%.3f')        
        
        # 9. Mensagem de retorno
        fiscal_status = "MAR-FEV" if fiscal_info.is_mar_fev else ("PADRÃO" if fiscal_info.is_standard else "IRREGULAR")
        tipo = _get_tipo_empresa(ticker)
        pl_code = _detect_pl_code_from_data(bpp_tri) if _is_banco(ticker) else "2.03"
        
        n_periodos_bpa = len([c for c in bpa_out.columns if c not in ["cd_conta", "conta"]])
        n_periodos_bpp = len([c for c in bpp_out.columns if c not in ["cd_conta", "conta"]])
        
        pasta_usada = pasta.name
        pasta_info = f" (pasta: {pasta_usada})" if pasta_usada != ticker.upper() else ""
        
        # NOVO: Indicar se detectou mudança de estrutura
        struct_info = " | ESTRUTURA ADAPTATIVA" if structure_changed else ""
        
        msg_parts = [
            f"Fiscal: {fiscal_status}",
            f"Tipo: {tipo}",
            f"PL: {pl_code}" if _is_banco(ticker) else None,
            f"BPA: {n_periodos_bpa} períodos",
            f"BPP: {n_periodos_bpp} períodos",
        ]
        
        msg = f"bpa_padronizado.csv + bpp_padronizado.csv{pasta_info} | {' | '.join(m for m in msg_parts if m)}{struct_info}"
        
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
    ok_count, err_count, irregular_count, adaptive_count = 0, 0, 0, 0

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
            
            if "ESTRUTURA ADAPTATIVA" in msg:
                adaptive_count += 1
            
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
    if adaptive_count > 0:
        print(f"            Estrutura adaptativa (mudança de plano): {adaptive_count}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
