import pandas as pd
import numpy as np
from functools import lru_cache
from typing import Optional, Dict, List, Tuple


# -------------------- DRE PADRÃO (original) --------------------
DRE_PADRAO: List[Tuple[str, str]] = [
    ("3.01", "Receita de Venda de Bens e/ou Serviços"),
    ("3.02", "Custo dos Bens e/ou Serviços Vendidos"),
    ("3.03", "Resultado Bruto"),
    ("3.04", "Despesas/Receitas Operacionais"),
    ("3.05", "Resultado Antes do Resultado Financeiro e dos Tributos"),
    ("3.06", "Resultado Financeiro"),
    ("3.07", "Resultado Antes dos Tributos sobre o Lucro"),
    ("3.08", "Imposto de Renda e Contribuição Social sobre o Lucro"),
    ("3.09", "Resultado Líquido das Operações Continuadas"),
    ("3.10", "Resultado Líquido de Operações Descontinuadas"),
    ("3.11", "Lucro/Prejuízo Consolidado do Período"),
    ("3.99", "Lucro por Ação - (Reais / Ação)"),
]

# -------------------- NOVO: DRE Seguros --------------------
DRE_SEGUROS_PADRAO: List[Tuple[str, str]] = [
    ("3.01", "Receita de Prêmios Retidos"),
    ("3.02", "Sinistros Ocorridos"),
    ("3.03", "Resultado Bruto (Margem)"),
    ("3.04.01", "Custos de Aquisição (Vendas)"),
    ("3.04.02", "Despesas Administrativas"),
    ("3.05", "Resultado Operacional (EBIT)"),
    ("3.06", "Resultado Financeiro"),
    ("3.07", "Equivalência Patrimonial"),
    ("3.08", "Lucro Antes Impostos (LAIR)"),
    ("3.11", "Lucro Líquido"),
    ("3.99", "Lucro por Ação (LPA ON)"),
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
    # Arquivo do usuário é separado por ';'
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


def padronizar_dre_trimestral_e_anual(
    dre_trimestral_csv: str,
    dre_anual_csv: str,
    *,
    unidade: str = "mil",
    preencher_derivadas: bool = True,
    ticker: Optional[str] = None,
    b3_mapping_csv: Optional[str] = None,
) -> pd.DataFrame:
    """
    Saída:
      cd_conta_padrao | ds_conta_padrao | YYYY-T1 | YYYY-T2 | YYYY-T3 | YYYY-T4 | ...

    Lógica original mantida:
    - T1/T2/T3: vem do trimestral (ITR)
    - T4: vem do anual (DFP), mas para DRE é isolado:
         T4_isolado = Anual - (T1 + T2 + T3)
      (exceto EPS 3.99, que não é subtraído)
    - EPS (3.99): pega 1 valor por período e NÃO subtrai

    NOVO:
    - Detecção de Seguros por:
        (a) ticker em {_SEGUROS_TICKERS} OU
        (b) b3_mapping_csv com setor == "Previdência e Seguros"
    - Mapeamentos específicos de Seguros para EBIT/Financeiro/Equivalência/LAIR
    """

    ticker_norm = _norm_ticker(ticker) or _infer_ticker_from_paths(dre_trimestral_csv, dre_anual_csv)
    setor, _segmento = _get_setor_segmento_from_b3_mapping(ticker_norm, b3_mapping_csv)

    modo_seguros = (
        (ticker_norm in _SEGUROS_TICKERS) or
        (setor is not None and setor.strip().lower() == "previdência e seguros")
    )

    # Seguros: remapeamento por ticker (conforme sua tabela)
    seguros_map_por_ticker: Dict[str, Dict[str, str]] = {
        "BBSE3": {"3.05": "3.07", "3.06": "3.08", "3.07": "3.06", "3.08": "3.09"},
        "CXSE3": {"3.05": "3.05", "3.06": "3.06", "3.07": "3.07", "3.08": "3.08"},
        "IRBR3": {"3.05": "3.07", "3.06": "3.08", "3.07": "3.06", "3.08": "3.09"},
        "PSSA3": {"3.05": "3.05", "3.06": "3.06", "3.07": "3.07", "3.08": "3.07"},
    }
    seguros_map = seguros_map_por_ticker.get(ticker_norm, {}) if modo_seguros else {}

    plano = DRE_SEGUROS_PADRAO if modo_seguros else DRE_PADRAO
    contas = [c for c, _ in plano]
    nomes = {c: n for c, n in plano}

    tri = pd.read_csv(dre_trimestral_csv)
    anu = pd.read_csv(dre_anual_csv)

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

    # Mantido: DRE trimestral usa só T1..T3; T4 vem do anual
    tri = tri[tri["q"].isin([1, 2, 3])].copy()
    anu = anu[anu["ano"].notna()].copy()

    # Períodos (mantido)
    periodos = pd.concat(
        [tri[["ano", "q"]].dropna(), anu[["ano", "q"]].dropna()],
        ignore_index=True,
    ).drop_duplicates().sort_values(["ano", "q"]).astype(int)

    periodos = list(periodos.itertuples(index=False, name=None))
    if not periodos:
        return pd.DataFrame({"cd_conta_padrao": contas, "ds_conta_padrao": [nomes[c] for c in contas]})

    cols_mi = pd.MultiIndex.from_tuples(periodos, names=["ano", "q"])
    mat = pd.DataFrame(index=contas, columns=cols_mi, dtype="float64")

    def _valor_total_periodo(df_periodo: pd.DataFrame, codigo_expr: str) -> float:
        """
        Regra original: tenta conta exata, senão soma descendentes.
        Extensão compatível:
          - "+" soma contas (ex.: "3.04.01+3.04.02")
          - "|" fallback (primeiro não-NaN) (ex.: "3.07|3.05")
        """
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

        desc = df_periodo[df_periodo["cd_conta"].str.startswith(codigo_expr + ".")]
        if not desc.empty:
            return float(desc["valor"].sum(skipna=True))

        return np.nan

    def _valor_eps_periodo(df_periodo: pd.DataFrame) -> float:
        """
        EPS inteligente (mantido): prioriza ON, depois cai para níveis mais agregados.
        """
        df_eps = df_periodo[df_periodo["cd_conta"].astype(str).str.startswith("3.99")].copy()
        if df_eps.empty:
            return np.nan

        df_eps["valor"] = pd.to_numeric(df_eps["valor"], errors="coerce")
        df_eps = df_eps.dropna(subset=["valor"])
        if df_eps.empty:
            return np.nan

        prioridade = ["3.99.01.01", "3.99.02.01", "3.99.01", "3.99.02", "3.99"]
        for c in prioridade:
            s = df_eps.loc[df_eps["cd_conta"] == c, "valor"]
            s = s[s != 0]
            if not s.empty:
                return float(s.iloc[-1])

        nz = df_eps[df_eps["valor"] != 0]
        if not nz.empty:
            r = nz.iloc[int(nz["valor"].abs().argmax())]
            return float(r["valor"])

        return 0.0

    # Preenche T1..T3 (tri) e T4 (anual)
    for (ano, q) in periodos:
        if q in (1, 2, 3):
            dfp = tri[(tri["ano"] == ano) & (tri["q"] == q)]
        else:
            dfp = anu[(anu["ano"] == ano) & (anu["q"] == 4)]
        if dfp.empty:
            continue

        for cod_padrao in contas:
            if cod_padrao == "3.99":
                mat.at[cod_padrao, (ano, q)] = _valor_eps_periodo(dfp)
                continue

            cod_fonte = seguros_map.get(cod_padrao, cod_padrao) if modo_seguros else cod_padrao
            mat.at[cod_padrao, (ano, q)] = _valor_total_periodo(dfp, cod_fonte)

    # Derivadas (mantidas; adaptadas no modo Seguros)
    if preencher_derivadas:
        def _fill(code: str, expr_codes: List[str]):
            if code not in mat.index:
                return
            missing = mat.loc[code].isna()
            if not missing.any():
                return
            s = None
            for c in expr_codes:
                if c not in mat.index:
                    return
                s = mat.loc[c].copy() if s is None else s.add(mat.loc[c], fill_value=np.nan)
            mat.loc[code, missing] = s[missing]

        if not modo_seguros:
            _fill("3.03", ["3.01", "3.02"])
            _fill("3.05", ["3.03", "3.04"])
            _fill("3.07", ["3.05", "3.06"])
            _fill("3.09", ["3.07", "3.08"])
            _fill("3.11", ["3.09", "3.10"])
        else:
            # Seguros: 3.03 = 3.01 + 3.02
            _fill("3.03", ["3.01", "3.02"])
            # LAIR (3.08) normalmente = EBIT (3.05) + Fin (3.06) + Equiv (3.07)
            _fill("3.08", ["3.05", "3.06", "3.07"])

    # T4 isolado (mantido): anual - (T1+T2+T3), exceto EPS
    anos = sorted({a for (a, _) in periodos})
    for ano in anos:
        if (ano, 4) not in mat.columns:
            continue

        for cod_padrao in mat.index:
            if cod_padrao == "3.99":
                continue

            a = mat.at[cod_padrao, (ano, 4)]
            if pd.isna(a):
                continue

            s = 0.0
            ok = True
            for q in (1, 2, 3):
                v = mat.at[cod_padrao, (ano, q)] if (ano, q) in mat.columns else np.nan
                if pd.isna(v):
                    ok = False
                    break
                s += float(v)

            if ok:
                mat.at[cod_padrao, (ano, 4)] = float(a) - s

    # Saída final
    out = pd.DataFrame({"cd_conta_padrao": contas, "ds_conta_padrao": [nomes[c] for c in contas]})
    for (ano, q) in periodos:
        out[f"{ano}-T{q}"] = mat[(ano, q)].values

    return out
