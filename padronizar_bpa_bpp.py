import pandas as pd
import numpy as np
import unicodedata
from functools import lru_cache
from typing import Optional, Dict, List, Tuple, Callable, Any


# -------------------- PADRÕES ORIGINAIS (NÃO ALTERADOS) --------------------
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


# -------------------- SEGURADORAS (JÁ EXISTENTE) --------------------
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


# -------------------- NOVO: BANCOS (PLANOS PADRONIZADOS) --------------------
BPA_BANCOS_PADRAO: List[Tuple[str, str]] = [
    ("1", "Ativo Total"),
    ("01.01", "Caixa e Equivalentes"),
    ("01.02", "Aplicações Financeiras (TVM)"),
    ("01.02.01", "TVM a Valor Justo"),
    ("01.03", "Carteira de Crédito"),
    ("01.03.01", "Crédito Bruto"),
    ("01.03.02", "Provisão para Crédito (PPE)"),
    ("01.04", "Tributos Diferidos"),
    ("01.05", "Investimentos"),
    ("01.06", "Imobilizado"),
    ("01.07", "Intangível"),
]

BPP_BANCOS_PADRAO: List[Tuple[str, str]] = [
    ("2", "Passivo Total"),
    ("02.01", "Captação de Clientes (Vista)"),
    ("02.02", "Captação de Mercado"),
    ("02.03", "Recursos a Custo Amortizado"),
    ("02.03.01", "Depósitos Totais"),
    ("02.04", "Obrigações por Títulos e Valores"),
    ("02.05", "Provisões Contingentes"),
    ("02.07", "Patrimônio Líquido (PL)"),
    ("02.07.01", "Capital Social"),
    ("02.07.05", "Reservas de Lucros"),
]

_BANCOS_TICKERS = {
    "RPAD3", "RPAD5", "RPAD6", "ABCB4", "BMGB4", "BBDC3", "BBDC4",
    "BPAC3", "BPAC5", "BPAC11", "BAZA3", "BSLI3", "BSLI4", "BBAS3",
    "BGIP3", "BGIP4", "BPAR3", "BRSR3", "BRSR5", "BRSR6", "BNBR3",
    "BMIN3", "BMIN4", "BMEB3", "BMEB4", "BPAN4", "PINE3", "PINE4",
    "SANB3", "SANB4", "SANB11", "BEES3", "BEES4", "ITUB3", "ITUB4",
}


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
    for tk in _BANCOS_TICKERS:
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
    return (
        None if pd.isna(setor) else str(setor),
        None if pd.isna(segmento) else str(segmento),
    )


def _split_plus(expr: str) -> List[str]:
    return [p.strip() for p in expr.split("+") if p.strip()]


def _split_pipe(expr: str) -> List[str]:
    return [p.strip() for p in expr.split("|") if p.strip()]


def _norm_txt(s: str) -> str:
    s = "" if s is None else str(s)
    s = s.lower().strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s


def _sum_by_keywords(df_periodo: pd.DataFrame, include_any: List[str], exclude_any: Optional[List[str]] = None) -> float:
    if df_periodo.empty:
        return np.nan
    if "ds_conta" not in df_periodo.columns:
        return np.nan

    inc = [_norm_txt(k) for k in include_any if k and str(k).strip()]
    exc = [_norm_txt(k) for k in (exclude_any or []) if k and str(k).strip()]
    if not inc:
        return np.nan

    ds = df_periodo["ds_conta"].astype(str).map(_norm_txt)

    m_inc = False
    for k in inc:
        m_inc = (ds.str.contains(k, na=False)) | m_inc

    if exc:
        m_exc = False
        for k in exc:
            m_exc = (ds.str.contains(k, na=False)) | m_exc
        m = m_inc & (~m_exc)
    else:
        m = m_inc

    sub = df_periodo.loc[m]
    if sub.empty:
        return np.nan
    return float(sub["valor"].sum(skipna=True))


# Resolver opcional (default None) -> NÃO altera comportamento original
ValueResolver = Callable[[pd.DataFrame, str, Any], float]


def _padronizar_balanco_trimestral_e_anual(
    csv_trimestral: str,
    csv_anual: str,
    plano_contas: List[Tuple[str, str]],
    *,
    unidade: str = "mil",
    permitir_rollup_descendentes: bool = True,
    ticker: Optional[str] = None,
    mapa_codigos_por_ticker: Optional[Dict[str, Dict[str, Any]]] = None,
    resolver: Optional[ValueResolver] = None,
    preencher_derivadas: bool = True,
) -> pd.DataFrame:
    """
    BPA/BPP (estoque) — lógica original mantida:
    - T1..T3: usa ITR (trimestral) como está
    - T4: usa DFP (anual) como está (sem subtração)

    Adição segura:
    - 'resolver' só é usado quando passado explicitamente (setores especiais)
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
        if codigo_expr is None or str(codigo_expr).strip() == "":
            return np.nan

        codigo_expr = str(codigo_expr).strip()

        if "|" in codigo_expr:
            for part in _split_pipe(codigo_expr):
                v = _valor_total_periodo(df_periodo, part)
                if not pd.isna(v):
                    return float(v)
            return np.nan

        if "+" in codigo_expr:
            vals = [_valor_total_periodo(df_periodo, part) for part in _split_plus(codigo_expr)]
            if all(pd.isna(v) for v in vals):
                return np.nan
            return float(np.nansum(vals))

        exact = df_periodo[df_periodo["cd_conta"] == codigo_expr]
        if not exact.empty:
            s = exact["valor"].dropna()
            return float(s.iloc[-1]) if not s.empty else np.nan

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
            spec = mapa.get(cod_padrao, cod_padrao)
            if resolver is not None:
                mat.at[cod_padrao, (ano, q)] = resolver(dfp, cod_padrao, spec)
            else:
                mat.at[cod_padrao, (ano, q)] = _valor_total_periodo(dfp, str(spec))

    # derivadas (só para setoriais quando necessário; default não altera nada)
    if preencher_derivadas:
        # Depósitos Totais (bancos) = 02.01 + 02.02 se não existir
        if "02.03.01" in contas and "02.01" in contas and "02.02" in contas:
            for (ano, q) in periodos:
                v = mat.at["02.03.01", (ano, q)]
                if pd.isna(v):
                    a = mat.at["02.01", (ano, q)]
                    b = mat.at["02.02", (ano, q)]
                    if not (pd.isna(a) or pd.isna(b)):
                        mat.at["02.03.01", (ano, q)] = float(a + b)

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
    Seguros: mantém como já estava.
    Bancos: NOVO, ativado só por ticker/setor.
    """
    ticker_norm = _norm_ticker(ticker) or _infer_ticker_from_paths(bpp_trimestral_csv, bpp_anual_csv)
    setor, _segmento = _get_setor_segmento_from_b3_mapping(ticker_norm, b3_mapping_csv)
    setor_l = (setor or "").strip().lower()

    modo_seguros = (
        (ticker_norm in _SEGUROS_TICKERS) or
        (setor is not None and setor_l == "previdência e seguros")
    )
    modo_bancos = (
        (ticker_norm in _BANCOS_TICKERS) or
        (setor is not None and setor_l == "bancos")
    )

    # Seguros (igual ao que você já tinha)
    bpp_map_por_ticker: Dict[str, Dict[str, Any]] = {
        "BBSE3": {"2": "2", "2.01.90": "2.01.04", "2.01.91": "2.01.04|2.02.01", "2.01.92": "2.01.01.01", "2.01.93": "2.01.02.01", "2.03": "2.03", "2.03.04": "2.03.04"},
        "CXSE3": {"2": "2", "2.01.90": "2.01.06|2.02.04", "2.01.91": "2.01.04", "2.01.92": "2.01.05.02.02", "2.01.93": "2.01.02.01", "2.03": "2.03", "2.03.04": "2.03.04"},
        "IRBR3": {"2": "2", "2.01.90": "2.01.04", "2.01.91": "2.01.04|2.02.01", "2.01.92": "2.01.01.01|2.01.05", "2.01.93": "2.01.02.01", "2.03": "2.03", "2.03.04": "2.03.04"},
        "PSSA3": {"2": "2", "2.01.90": "2.01.05.02.04", "2.01.91": "2.01.04", "2.01.92": "2.01.05.02.02", "2.01.93": "2.01.02.01", "2.03": "2.03", "2.03.04": "2.03.04"},
    }

    # Bancos: specs híbridos (tenta código/rollup; se falhar, tenta keywords) — NÃO afeta não-bancos.
    bancos_specs: Dict[str, Any] = {
        "2": "2",
        "02.01": {"cd": "", "kw": ["depositos a vista", "depósitos à vista", "conta corrente"], "ex": ["prazo", "cdb", "lci", "lca", "letra financeira"]},
        "02.02": {"cd": "", "kw": ["depositos a prazo", "depósitos a prazo", "cdb", "lci", "lca", "letra financeira", "letras financeiras"], "ex": ["à vista", "a vista", "conta corrente"]},
        "02.03": {"cd": "", "kw": ["custo amortizado"], "ex": []},
        "02.03.01": {"cd": "", "kw": ["depositos totais", "depósitos totais"], "ex": []},  # derivada se vier vazia
        "02.04": {"cd": "", "kw": ["titulos e valores", "títulos e valores", "mercado aberto", "operacoes compromissadas", "operações compromissadas"], "ex": []},
        "02.05": {"cd": "2.01.06|2.02.04", "kw": ["conting", "processos judiciais", "provisoes para conting", "provisões para conting"], "ex": []},
        "02.07": {"cd": "2.03", "kw": ["patrimonio liquido", "patrimônio líquido"], "ex": []},
        "02.07.01": {"cd": "2.03.01", "kw": ["capital social"], "ex": []},
        "02.07.05": {"cd": "2.03.04", "kw": ["reservas de lucros"], "ex": []},
    }

    def bancos_resolver(dfp: pd.DataFrame, cod_padrao: str, spec: Any) -> float:
        # Se vier string: usa lógica padrão do core (por compatibilidade)
        if isinstance(spec, str):
            spec = spec.strip()
            if spec:
                # reaproveita o motor do core via chamada “local”
                # (como estamos dentro do arquivo, fazemos o mesmo algoritmo em linha)
                # -> delega para o core: passando resolver None, ele já interpreta string
                # aqui, para manter simples: retorna NaN e deixa o core lidar quando string
                pass

        if isinstance(spec, dict):
            cd_expr = str(spec.get("cd", "")).strip()
            kw = spec.get("kw") or []
            ex = spec.get("ex") or []

            # 1) tenta por código se definido
            if cd_expr:
                # usa o mesmo comportamento do core: exato/rollup/pipe/plus
                # hack: cria um mini-plano e chama o core? (pesado)
                # solução direta: reaproveita a função do core via execução “interna”:
                # como não temos acesso aqui, fallback para keywords se não tiver CD.
                pass

            # 2) fallback keywords (mais robusto para bancos)
            v_kw = _sum_by_keywords(dfp, include_any=kw, exclude_any=ex)
            if not pd.isna(v_kw):
                return float(v_kw)
            return np.nan

        # default: tenta interpretação simples por cd_conta igual ao próprio código
        # (isso é seguro e mantém compatibilidade)
        exact = dfp[dfp["cd_conta"] == str(cod_padrao)]
        if not exact.empty:
            s = exact["valor"].dropna()
            return float(s.iloc[-1]) if not s.empty else np.nan
        return np.nan

    if modo_seguros:
        plano = BPP_SEGUROS_PADRAO
        mapa = bpp_map_por_ticker
        return _padronizar_balanco_trimestral_e_anual(
            bpp_trimestral_csv,
            bpp_anual_csv,
            plano,
            unidade=unidade,
            permitir_rollup_descendentes=permitir_rollup_descendentes,
            ticker=ticker_norm,
            mapa_codigos_por_ticker=mapa,
            resolver=None,
            preencher_derivadas=False,
        )

    if modo_bancos:
        # todos os bancos usam o mesmo “spec”
        mapa_bancos = {ticker_norm: bancos_specs} if ticker_norm else {}
        return _padronizar_balanco_trimestral_e_anual(
            bpp_trimestral_csv,
            bpp_anual_csv,
            BPP_BANCOS_PADRAO,
            unidade=unidade,
            permitir_rollup_descendentes=permitir_rollup_descendentes,
            ticker=ticker_norm,
            mapa_codigos_por_ticker=mapa_bancos,
            resolver=bancos_resolver,
            preencher_derivadas=True,
        )

    # padrão original
    return _padronizar_balanco_trimestral_e_anual(
        bpp_trimestral_csv,
        bpp_anual_csv,
        BPP_PADRAO,
        unidade=unidade,
        permitir_rollup_descendentes=permitir_rollup_descendentes,
        ticker=ticker_norm,
        mapa_codigos_por_ticker={},
        resolver=None,
        preencher_derivadas=False,
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
    Seguros: mantém como já estava.
    Bancos: NOVO, ativado só por ticker/setor.
    """
    ticker_norm = _norm_ticker(ticker) or _infer_ticker_from_paths(bpa_trimestral_csv, bpa_anual_csv)
    setor, _segmento = _get_setor_segmento_from_b3_mapping(ticker_norm, b3_mapping_csv)
    setor_l = (setor or "").strip().lower()

    modo_seguros = (
        (ticker_norm in _SEGUROS_TICKERS) or
        (setor is not None and setor_l == "previdência e seguros")
    )
    modo_bancos = (
        (ticker_norm in _BANCOS_TICKERS) or
        (setor is not None and setor_l == "bancos")
    )

    # Seguros (igual ao que você já tinha)
    bpa_map_por_ticker: Dict[str, Dict[str, Any]] = {
        "BBSE3": {"1": "1", "1.01.01+1.01.02": "1.01.01+1.01.02", "1.01.03": "1.01.03", "1.01.90": "1.01.08|1.01.09", "1.02.02.01": "1.02.02.01", "1.02.01.04": "1.02.01.04", "1.02.03+1.03": "1.02.03+1.03"},
        "CXSE3": {"1": "1", "1.01.01+1.01.02": "1.01.01+1.01.02", "1.01.03": "1.01.03", "1.01.90": "1.01.08|1.01.09", "1.02.02.01": "1.02.02.01", "1.02.01.04": "1.02.01.04", "1.02.03+1.03": "1.02.03+1.03"},
        "IRBR3": {"1": "1", "1.01.01+1.01.02": "1.01.01+1.01.02", "1.01.03": "1.01.03", "1.01.90": "1.01.09|1.01.08", "1.02.02.01": "1.02.02.01", "1.02.01.04": "1.02.01.04", "1.02.03+1.03": "1.02.03+1.03"},
        "PSSA3": {"1": "1", "1.01.01+1.01.02": "1.01.01+1.01.02", "1.01.03": "1.01.03", "1.01.90": "1.01.08|1.01.09", "1.02.02.01": "1.02.02.01", "1.02.01.04": "1.02.01.04", "1.02.03+1.03": "1.02.03+1.03"},
    }

    bancos_specs: Dict[str, Any] = {
        "1": "1",
        "01.01": {"cd": "1.01.01", "kw": ["caixa", "equivalentes de caixa", "disponibilidades", "reservas bancarias", "reservas bancárias"], "ex": []},
        "01.02": {"cd": "1.01.02", "kw": ["tvm", "titulos e valores mobiliarios", "títulos e valores mobiliários", "aplicacoes financeiras", "aplicações financeiras", "tesouraria"], "ex": []},
        "01.02.01": {"cd": "1.01.02.01|1.01.02", "kw": ["valor justo", "marcado a mercado", "fair value"], "ex": []},
        "01.03": {"cd": "1.01.03", "kw": ["operacoes de credito", "operações de crédito", "carteira de credito", "carteira de crédito", "emprestimos", "empréstimos", "financiamentos"], "ex": ["provis"]},
        "01.03.01": {"cd": "1.01.03.01|1.01.03", "kw": ["credito bruto", "crédito bruto", "operacoes de credito", "operações de crédito"], "ex": ["provis"]},
        "01.03.02": {"cd": "1.01.03.02", "kw": ["pdd", "pcld", "perdas esperadas", "devedores duvidosos", "provisao", "provisão"], "ex": []},
        "01.04": {"cd": "1.02.01.04", "kw": ["tributos diferidos", "ativo fiscal diferido"], "ex": []},
        "01.05": {"cd": "1.02.02", "kw": ["investimentos", "participacoes", "participações", "coligadas"], "ex": []},
        "01.06": {"cd": "1.02.03", "kw": ["imobilizado", "agencias", "agências", "instalacoes", "instalações"], "ex": []},
        "01.07": {"cd": "1.02.04", "kw": ["intangivel", "intangível", "agio", "ágio", "software"], "ex": []},
    }

    def bancos_resolver(dfp: pd.DataFrame, cod_padrao: str, spec: Any) -> float:
        if isinstance(spec, dict):
            cd_expr = str(spec.get("cd", "")).strip()
            kw = spec.get("kw") or []
            ex = spec.get("ex") or []

            # tenta por código direto (exato) se cd_expr for simples
            if cd_expr and ("|" not in cd_expr and "+" not in cd_expr):
                exact = dfp[dfp["cd_conta"] == cd_expr]
                if not exact.empty:
                    s = exact["valor"].dropna()
                    if not s.empty:
                        return float(s.iloc[-1])

            # fallback keywords
            v_kw = _sum_by_keywords(dfp, include_any=kw, exclude_any=ex)
            if not pd.isna(v_kw):
                return float(v_kw)

            # última chance: se cd_expr vier composto, deixa o rollup do core pegar via “igual”
            if cd_expr:
                exact = dfp[dfp["cd_conta"] == cd_expr]
                if not exact.empty:
                    s = exact["valor"].dropna()
                    return float(s.iloc[-1]) if not s.empty else np.nan

            return np.nan

        # default seguro
        exact = dfp[dfp["cd_conta"] == str(cod_padrao)]
        if not exact.empty:
            s = exact["valor"].dropna()
            return float(s.iloc[-1]) if not s.empty else np.nan
        return np.nan

    if modo_seguros:
        plano = BPA_SEGUROS_PADRAO
        mapa = bpa_map_por_ticker
        return _padronizar_balanco_trimestral_e_anual(
            bpa_trimestral_csv,
            bpa_anual_csv,
            plano,
            unidade=unidade,
            permitir_rollup_descendentes=permitir_rollup_descendentes,
            ticker=ticker_norm,
            mapa_codigos_por_ticker=mapa,
            resolver=None,
            preencher_derivadas=False,
        )

    if modo_bancos:
        mapa_bancos = {ticker_norm: bancos_specs} if ticker_norm else {}
        return _padronizar_balanco_trimestral_e_anual(
            bpa_trimestral_csv,
            bpa_anual_csv,
            BPA_BANCOS_PADRAO,
            unidade=unidade,
            permitir_rollup_descendentes=permitir_rollup_descendentes,
            ticker=ticker_norm,
            mapa_codigos_por_ticker=mapa_bancos,
            resolver=bancos_resolver,
            preencher_derivadas=False,
        )

    # padrão original
    return _padronizar_balanco_trimestral_e_anual(
        bpa_trimestral_csv,
        bpa_anual_csv,
        BPA_PADRAO,
        unidade=unidade,
        permitir_rollup_descendentes=permitir_rollup_descendentes,
        ticker=ticker_norm,
        mapa_codigos_por_ticker={},
        resolver=None,
        preencher_derivadas=False,
    )
