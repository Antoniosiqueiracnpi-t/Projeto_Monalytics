import pandas as pd
import numpy as np
from functools import lru_cache
from typing import Optional, Dict, List, Tuple


# -------------------- PADRÕES ORIGINAIS --------------------
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


# -------------------- NOVO: PADRÕES SEGURADORAS (BPA/BPP) --------------------
BPA_SEGUROS_PADRAO: List[Tuple[str, str]] = [
    ("1", "Ativo Total"),
    ("1.01.01+1.01.02", "Disponibilidades e Aplicações"),
    ("1.01.03", "Créditos Operacionais"),
    ("1.01.90", "Ativos de Resseguro"),
    ("1.02.02.01", "Participações em Coligadas"),
    ("1.02.01.04", "Tributos Diferidos"),
    ("1.02.03+1.03", "Imobilizado e Intangível"),
]

BPP_SEGUROS_PADRAO: List[Tuple[str, str]] = [
    ("2", "Passivo Total"),
    ("2.01.90", "Provisões Técnicas (CP)"),
    ("2.01.91", "Empréstimos e Financ."),
    ("2.01.92", "Dividendos a Pagar"),
    ("2.01.93", "Passivos de Resseguro"),
    ("2.03", "Patrimônio Líquido"),
    ("2.03.04", "Reservas de Lucros"),
]

_SEGUROS_TICKERS = {"BBSE3", "CXSE3", "IRBR3", "PSSA3"}


def _norm_ticker(t: Optional[str]) -> Optional[str]:
    if t is None:
        return None
    t = str(t).upper().strip()
    return t.replace(".SA", "")


def _infer_ticker_from_paths(*paths: str) -> Optional[str]:
    joined = " ".join([str(p).upper() for p in paths if p is not None])
    for tk in _SEGUROS_TICKERS:
        if tk in joined:
            return tk
    return None


@lru_cache(maxsize=8)
def _load_b3_mapping(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, sep=";", encoding="utf-8")
    df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()
    df["setor"] = df["setor"].astype(str)
    df["segmento"] = df["segmento"].astype(str)
    return df


def _get_setor_segmento_from_b3_mapping(
    ticker: Optional[str],
    b3_mapping_csv: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    if not ticker or not b3_mapping_csv:
        return (None, None)

    t = _norm_ticker(ticker)
    df = _load_b3_mapping(b3_mapping_csv)

    hit = df.loc[df["ticker"] == t, ["setor", "segmento"]]
    if hit.empty:
        return (None, None)

    setor = hit.iloc[0]["setor"]
    segmento = hit.iloc[0]["segmento"]
    return (None if pd.isna(setor) else str(setor),
            None if pd.isna(segmento) else str(segmento))


def _split_plus(expr: str) -> List[str]:
    return [p.strip() for p in expr.split("+") if p.strip()]


def _split_pipe(expr: str) -> List[str]:
    return [p.strip() for p in expr.split("|") if p.strip()]


def _padronizar_balanco_trimestral_e_anual(
    csv_trimestral: str,
    csv_anual: str,
    plano_contas: List[Tuple[str, str]],
    *,
    unidade: str = "mil",
    permitir_rollup_descendentes: bool = True,
    ticker: Optional[str] = None,
    mapa_codigos_por_ticker: Optional[Dict[str, Dict[str, str]]] = None,
) -> pd.DataFrame:
    """
    BPA/BPP (estoque) — lógica original mantida:
    - T1..T3: usa ITR (trimestral) como está
    - T4: usa DFP (anual) como está (sem subtração)
    """

    ticker_norm = _norm_ticker(ticker) or _infer_ticker_from_paths(csv_trimestral, csv_anual)
    mapa = (mapa_codigos_por_ticker or {}).get(ticker_norm, {}) if ticker_norm else {}

    tri = pd.read_csv(csv_trimestral)
    anu = pd.read_csv(csv_anual)

    cols = {"data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"}
    for name, df in [("trimestral", tri), ("anual", anu)]:
        missing = cols - set(df.columns)
        if missing:
            raise ValueError(f"Arquivo {name} sem colunas esperadas: {missing}")

    # Normalização (mantida)
    for df in (tri, anu):
        df["data_fim"] = pd.to_datetime(df["data_fim"], errors="coerce")
        df["trimestre"] = df["trimestre"].astype(str).str.upper().str.strip()
        df["cd_conta"] = df["cd_conta"].astype(str).str.strip()
        df["ds_conta"] = df["ds_conta"].astype(str)
        df["valor_mil"] = pd.to_numeric(df["valor_mil"], errors="coerce")

    # Anual sempre T4 (mantido)
    anu["trimestre"] = "T4"

    # Unidade (mantida)
    if unidade == "mil":
        fator = 1.0
    elif unidade == "unidade":
        fator = 1000.0
    elif unidade == "milhao":
        fator = 1.0 / 1000.0
    else:
        raise ValueError("unidade deve ser: 'mil', 'unidade' ou 'milhao'")

    tri["valor"] = tri["valor_mil"] * fator
    anu["valor"] = anu["valor_mil"] * fator

    qmap = {"T1": 1, "T2": 2, "T3": 3, "T4": 4}
    tri["ano"] = tri["data_fim"].dt.year
    tri["q"] = tri["trimestre"].map(qmap)

    anu["ano"] = anu["data_fim"].dt.year
    anu["q"] = 4

    tri = tri[tri["q"].isin([1, 2, 3, 4])].copy()
    anu = anu[anu["ano"].notna()].copy()

    # Períodos (mantido)
    periodos = pd.concat(
        [tri[["ano", "q"]].dropna(), anu[["ano", "q"]].dropna()],
        ignore_index=True,
    ).drop_duplicates().sort_values(["ano", "q"]).astype(int)

    periodos = list(periodos.itertuples(index=False, name=None))
    contas = [c for c, _ in plano_contas]
    nomes = {c: n for c, n in plano_contas}

    if not periodos:
        return pd.DataFrame({"cd_conta_padrao": contas, "ds_conta_padrao": [nomes[c] for c in contas]})

    cols_mi = pd.MultiIndex.from_tuples(periodos, names=["ano", "q"])
    mat = pd.DataFrame(index=contas, columns=cols_mi, dtype="float64")

    def _valor_total_periodo(df_periodo: pd.DataFrame, codigo_expr: str) -> float:
        # expressão vazia
        if codigo_expr is None or str(codigo_expr).strip() == "":
            return np.nan

        codigo_expr = str(codigo_expr).strip()

        # fallback pipe (primeiro não-NaN)
        if "|" in codigo_expr:
            for part in _split_pipe(codigo_expr):
                v = _valor_total_periodo(df_periodo, part)
                if not pd.isna(v):
                    return float(v)
            return np.nan

        # soma plus
        if "+" in codigo_expr:
            vals = [_valor_total_periodo(df_periodo, part) for part in _split_plus(codigo_expr)]
            if all(pd.isna(v) for v in vals):
                return np.nan
            return float(np.nansum(vals))

        # 1) conta exata
        exact = df_periodo[df_periodo["cd_conta"] == codigo_expr]
        if not exact.empty:
            s = exact["valor"].dropna()
            return float(s.iloc[-1]) if not s.empty else np.nan

        # 2) rollup de descendentes (opcional, como no original)
        if permitir_rollup_descendentes:
            desc = df_periodo[df_periodo["cd_conta"].str.startswith(codigo_expr + ".")]
            if not desc.empty:
                return float(desc["valor"].sum(skipna=True))

        return np.nan

    # Preenche matriz (mantido: T4 prioriza anual/DFP quando existir)
    for (ano, q) in periodos:
        if q == 4:
            dfp = anu[(anu["ano"] == ano) & (anu["q"] == 4)]
            if dfp.empty:
                dfp = tri[(tri["ano"] == ano) & (tri["q"] == 4)]
        else:
            dfp = tri[(tri["ano"] == ano) & (tri["q"] == q)]

        if dfp.empty:
            continue

        for cod_padrao in contas:
            cod_fonte = mapa.get(cod_padrao, cod_padrao)
            mat.at[cod_padrao, (ano, q)] = _valor_total_periodo(dfp, cod_fonte)

    out = pd.DataFrame({"cd_conta_padrao": contas, "ds_conta_padrao": [nomes[c] for c in contas]})
    for (ano, q) in periodos:
        out[f"{ano}-T{q}"] = mat[(ano, q)].values

    return out


def padronizar_bpp_trimestral_e_anual(
    bpp_trimestral_csv: str,
    bpp_anual_csv: str,
    *,
    unidade: str = "mil",
    permitir_rollup_descendentes: bool = True,
    ticker: Optional[str] = None,
    b3_mapping_csv: Optional[str] = None,
) -> pd.DataFrame:
    """
    BPP — lógica original mantida.
    NOVO: ativa plano segurador quando:
      - ticker em BBSE3/CXSE3/IRBR3/PSSA3, OU
      - setor no b3_mapping_csv == "Previdência e Seguros"
    """
    ticker_norm = _norm_ticker(ticker) or _infer_ticker_from_paths(bpp_trimestral_csv, bpp_anual_csv)
    setor, _segmento = _get_setor_segmento_from_b3_mapping(ticker_norm, b3_mapping_csv)

    modo_seguros = (
        (ticker_norm in _SEGUROS_TICKERS) or
        (setor is not None and setor.strip().lower() == "previdência e seguros")
    )

    # Mapeamento seguradoras (conforme suas regras)
    bpp_map_por_ticker: Dict[str, Dict[str, str]] = {
        "BBSE3": {
            "2": "2",
            "2.01.90": "2.01.04",
            "2.01.91": "2.01.04|2.02.01",
            "2.01.92": "2.01.01.01",
            "2.01.93": "2.01.02.01",
            "2.03": "2.03",
            "2.03.04": "2.03.04",
        },
        "CXSE3": {
            "2": "2",
            "2.01.90": "2.01.06|2.02.04",
            "2.01.91": "2.01.04",
            "2.01.92": "2.01.05.02.02",
            "2.01.93": "2.01.02.01",
            "2.03": "2.03",
            "2.03.04": "2.03.04",
        },
        "IRBR3": {
            "2": "2",
            "2.01.90": "2.01.04",
            "2.01.91": "2.01.04|2.02.01",
            "2.01.92": "2.01.01.01|2.01.05",
            "2.01.93": "2.01.02.01",
            "2.03": "2.03",
            "2.03.04": "2.03.04",
        },
        "PSSA3": {
            "2": "2",
            "2.01.90": "2.01.05.02.04",
            "2.01.91": "2.01.04",
            "2.01.92": "2.01.05.02.02",
            "2.01.93": "2.01.02.01",
            "2.03": "2.03",
            "2.03.04": "2.03.04",
        },
    }

    plano = BPP_SEGUROS_PADRAO if modo_seguros else BPP_PADRAO
    mapa = bpp_map_por_ticker if modo_seguros else {}

    return _padronizar_balanco_trimestral_e_anual(
        bpp_trimestral_csv,
        bpp_anual_csv,
        plano,
        unidade=unidade,
        permitir_rollup_descendentes=permitir_rollup_descendentes,
        ticker=ticker_norm,
        mapa_codigos_por_ticker=mapa,
    )


def padronizar_bpa_trimestral_e_anual(
    bpa_trimestral_csv: str,
    bpa_anual_csv: str,
    *,
    unidade: str = "mil",
    permitir_rollup_descendentes: bool = True,
    ticker: Optional[str] = None,
    b3_mapping_csv: Optional[str] = None,
) -> pd.DataFrame:
    """
    BPA — lógica original mantida.
    NOVO: ativa plano segurador quando:
      - ticker em BBSE3/CXSE3/IRBR3/PSSA3, OU
      - setor no b3_mapping_csv == "Previdência e Seguros"
    """
    ticker_norm = _norm_ticker(ticker) or _infer_ticker_from_paths(bpa_trimestral_csv, bpa_anual_csv)
    setor, _segmento = _get_setor_segmento_from_b3_mapping(ticker_norm, b3_mapping_csv)

    modo_seguros = (
        (ticker_norm in _SEGUROS_TICKERS) or
        (setor is not None and setor.strip().lower() == "previdência e seguros")
    )

    # Mapeamento seguradoras (inclui Ativo de Resseguro específico por empresa)
    bpa_map_por_ticker: Dict[str, Dict[str, str]] = {
        "BBSE3": {
            "1": "1",
            "1.01.01+1.01.02": "1.01.01+1.01.02",
            "1.01.03": "1.01.03",
            "1.01.90": "1.01.08|1.01.09",
            "1.02.02.01": "1.02.02.01",
            "1.02.01.04": "1.02.01.04",
            "1.02.03+1.03": "1.02.03+1.03",
        },
        "CXSE3": {
            "1": "1",
            "1.01.01+1.01.02": "1.01.01+1.01.02",
            "1.01.03": "1.01.03",
            "1.01.90": "1.01.08|1.01.09",
            "1.02.02.01": "1.02.02.01",
            "1.02.01.04": "1.02.01.04",
            "1.02.03+1.03": "1.02.03+1.03",
        },
        "IRBR3": {
            "1": "1",
            "1.01.01+1.01.02": "1.01.01+1.01.02",
            "1.01.03": "1.01.03",
            "1.01.90": "1.01.09|1.01.08",  # IRB prioriza 1.01.09
            "1.02.02.01": "1.02.02.01",
            "1.02.01.04": "1.02.01.04",
            "1.02.03+1.03": "1.02.03+1.03",
        },
        "PSSA3": {
            "1": "1",
            "1.01.01+1.01.02": "1.01.01+1.01.02",
            "1.01.03": "1.01.03",
            "1.01.90": "1.01.08|1.01.09",  # PSSA prioriza 1.01.08
            "1.02.02.01": "1.02.02.01",
            "1.02.01.04": "1.02.01.04",
            "1.02.03+1.03": "1.02.03+1.03",
        },
    }

    plano = BPA_SEGUROS_PADRAO if modo_seguros else BPA_PADRAO
    mapa = bpa_map_por_ticker if modo_seguros else {}

    return _padronizar_balanco_trimestral_e_anual(
        bpa_trimestral_csv,
        bpa_anual_csv,
        plano,
        unidade=unidade,
        permitir_rollup_descendentes=permitir_rollup_descendentes,
        ticker=ticker_norm,
        mapa_codigos_por_ticker=mapa,
    )
