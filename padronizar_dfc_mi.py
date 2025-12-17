import pandas as pd
import numpy as np

# Plano padrão (coarse) para manter padronização entre empresas.
# Se quiser mais granularidade depois, ampliamos esse plano.
DFC_MI_PADRAO = [
    ("6", "Demonstração do Fluxo de Caixa (Método Indireto)"),
    ("6.01", "Fluxo de Caixa das Atividades Operacionais"),
    ("6.02", "Fluxo de Caixa das Atividades de Investimento"),
    ("6.03", "Fluxo de Caixa das Atividades de Financiamento"),
    ("6.04", "Variação Cambial sobre Caixa e Equivalentes"),
    ("6.05", "Aumento/Redução de Caixa e Equivalentes"),
    ("6.06", "Caixa e Equivalentes no Início do Período"),
    ("6.07", "Caixa e Equivalentes no Final do Período"),
]


def padronizar_dfc_mi_trimestral_e_anual(
    dfc_trimestral_csv: str,
    dfc_anual_csv: str,
    *,
    unidade: str = "mil",
    permitir_rollup_descendentes: bool = True,
    plano_contas: list[tuple[str, str]] | None = None,
) -> pd.DataFrame:
    """
    Saída:
      cd_conta_padrao | ds_conta_padrao | YYYY-T1 | YYYY-T2 | YYYY-T3 | YYYY-T4 | ...

    Regras (DFC = fluxo, ITR vem YTD):
      - T1 isolado = YTD(T1)
      - T2 isolado = YTD(T2) - YTD(T1)
      - T3 isolado = YTD(T3) - YTD(T2)
      - T4 isolado = Anual(DFP) - YTD(T3)

    Observação:
      - Aqui NÃO fazemos "anual - (T1+T2+T3)" porque T2/T3 já são acumulados.
    """

    if plano_contas is None:
        plano_contas = DFC_MI_PADRAO

    tri = pd.read_csv(dfc_trimestral_csv)
    anu = pd.read_csv(dfc_anual_csv)

    cols = {"data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"}
    for name, df in [("trimestral", tri), ("anual", anu)]:
        missing = cols - set(df.columns)
        if missing:
            raise ValueError(f"Arquivo {name} sem colunas esperadas: {missing}")

    # normalizações
    for df in (tri, anu):
        df["data_fim"] = pd.to_datetime(df["data_fim"], errors="coerce")
        df["trimestre"] = df["trimestre"].astype(str).str.upper().str.strip()
        df["cd_conta"] = df["cd_conta"].astype(str).str.strip()
        df["ds_conta"] = df["ds_conta"].astype(str)
        df["valor_mil"] = pd.to_numeric(df["valor_mil"], errors="coerce")

    # anual sempre T4 (representa 12M)
    anu["trimestre"] = "T4"

    # unidade
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

    # ITR normalmente só T1..T3; mas deixamos robusto
    tri = tri[tri["q"].isin([1, 2, 3])].copy()
    anu = anu[anu["ano"].notna()].copy()

    contas = [c for c, _ in plano_contas]
    nomes = {c: n for c, n in plano_contas}

    # períodos existentes
    periodos = pd.concat(
        [
            tri[["ano", "q"]].dropna(),
            anu[["ano", "q"]].dropna(),
        ],
        ignore_index=True,
    ).drop_duplicates().sort_values(["ano", "q"]).astype(int)

    periodos = list(periodos.itertuples(index=False, name=None))
    if not periodos:
        return pd.DataFrame(
            {"cd_conta_padrao": contas, "ds_conta_padrao": [nomes[c] for c in contas]}
        )

    cols_mi = pd.MultiIndex.from_tuples(periodos, names=["ano", "q"])

    # matriz YTD (T1,T2,T3 do ITR + T4 do anual)
    ytd = pd.DataFrame(index=contas, columns=cols_mi, dtype="float64")

    def _valor_total_periodo(df_periodo: pd.DataFrame, codigo: str) -> float:
        # conta exata
        exact = df_periodo[df_periodo["cd_conta"] == codigo]
        if not exact.empty:
            s = exact["valor"].dropna()
            return float(s.iloc[-1]) if not s.empty else np.nan

        # rollup descendente (opcional)
        if permitir_rollup_descendentes:
            desc = df_periodo[df_periodo["cd_conta"].str.startswith(codigo + ".")]
            if not desc.empty:
                return float(desc["valor"].sum(skipna=True))

        return np.nan

    for (ano, q) in periodos:
        if q in (1, 2, 3):
            dfp = tri[(tri["ano"] == ano) & (tri["q"] == q)]
        else:
            dfp = anu[(anu["ano"] == ano) & (anu["q"] == 4)]
        if dfp.empty:
            continue

        for cod in contas:
            ytd.at[cod, (ano, q)] = _valor_total_periodo(dfp, cod)

    # converter para trimestres isolados (quarter)
    qt = ytd.copy()

    anos = sorted({a for (a, _) in periodos})
    for ano in anos:
        # precisa de T1..T4 no mínimo para Q4, mas calcula o que der.
        has = {(a, q) for (a, q) in periodos if a == ano}

        # Q2 = YTD2 - YTD1
        if (ano, 2) in has and (ano, 1) in has:
            qt[(ano, 2)] = ytd[(ano, 2)] - ytd[(ano, 1)]

        # Q3 = YTD3 - YTD2
        if (ano, 3) in has and (ano, 2) in has:
            qt[(ano, 3)] = ytd[(ano, 3)] - ytd[(ano, 2)]

        # Q4 = YTD4(Anual) - YTD3
        if (ano, 4) in has and (ano, 3) in has:
            qt[(ano, 4)] = ytd[(ano, 4)] - ytd[(ano, 3)]

    # saída final
    out = pd.DataFrame(
        {"cd_conta_padrao": contas, "ds_conta_padrao": [nomes[c] for c in contas]}
    )

    for (ano, q) in periodos:
        out[f"{ano}-T{q}"] = qt[(ano, q)].values

    return out
