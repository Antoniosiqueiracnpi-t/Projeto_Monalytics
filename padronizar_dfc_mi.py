import pandas as pd
import numpy as np
import unicodedata

# Plano mínimo correto (compatível com os CSVs do DFC_MI)
# Inclui conta sintética 6.01.DA (Depreciação e Amortização) para padronização
DFC_MI_PADRAO = [
    ("6.01", "Fluxo de Caixa das Atividades Operacionais"),
    ("6.01.DA", "Depreciação e Amortização"),  # <- conta sintética (inteligente via DS_CONTA)
    ("6.02", "Fluxo de Caixa das Atividades de Investimento"),
    ("6.03", "Fluxo de Caixa das Atividades de Financiamento"),
    ("6.04", "Variação Cambial s/ Caixa e Equivalentes"),
    ("6.05", "Aumento (Redução) de Caixa e Equivalentes"),
    ("6.05.01", "Saldo Inicial de Caixa e Equivalentes"),
    ("6.05.02", "Saldo Final de Caixa e Equivalentes"),
]

# Contas "de saldo" (nível/estoque) — NÃO diferenciar como YTD
SALDO_ACCOUNTS = {"6.05.01", "6.05.02"}

# Conta sintética de D&A
DA_CODE = "6.01.DA"


def _norm_text(s: str) -> str:
    """normaliza texto: lowercase, sem acento, espaços comprimidos"""
    s = "" if s is None else str(s)
    s = s.strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = " ".join(s.split())
    return s


def _capturar_depreciacao_amortizacao(df_periodo: pd.DataFrame) -> float:
    """
    Inteligência para capturar D&A (apenas dentro do bloco operacional: CD_CONTA startswith 6.01):
      1) Se existir linha com deprecia* e amortiza* ao mesmo tempo -> usa só ela(s)
      2) Senão soma linhas com deprecia* OU amortiza*
    """
    if df_periodo.empty:
        return np.nan

    # restringir ao bloco operacional
    dfx = df_periodo[df_periodo["cd_conta"].astype(str).str.startswith("6.01")].copy()
    if dfx.empty:
        return np.nan

    dfx["ds_norm"] = dfx["ds_conta"].map(_norm_text)
    dfx["valor"] = pd.to_numeric(dfx["valor"], errors="coerce")

    # termos (aceita variações e abreviações comuns)
    def has_depr(txt: str) -> bool:
        return ("depreci" in txt) or ("deprec" in txt)

    def has_amort(txt: str) -> bool:
        return ("amortiz" in txt) or ("amort" in txt)

    mask_both = dfx["ds_norm"].apply(lambda t: has_depr(t) and has_amort(t))
    both = dfx.loc[mask_both, "valor"].dropna()

    if not both.empty:
        # se existir combinado, NÃO soma com as separadas
        return float(both.sum())

    mask_any = dfx["ds_norm"].apply(lambda t: has_depr(t) or has_amort(t))
    any_ = dfx.loc[mask_any, "valor"].dropna()

    if any_.empty:
        return np.nan

    return float(any_.sum())


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

    Regras (DFC ITR em YTD):
      Fluxos (ex.: 6.01..6.05 e 6.01.DA):
        - Q1 = YTD(T1)
        - Q2 = YTD(T2) - YTD(T1)
        - Q3 = YTD(T3) - YTD(T2)
        - Q4 = Anual(DFP) - YTD(T3)

      Saldos (6.05.01 / 6.05.02):
        - 6.05.02 (saldo final): Q1=final T1, Q2=final T2, Q3=final T3, Q4=final anual
        - 6.05.01 (saldo inicial): Q1=inicial do ano; Q2=final T1; Q3=final T2; Q4=final T3
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

    # anual sempre T4
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

    tri = tri[tri["q"].isin([1, 2, 3])].copy()
    anu = anu[anu["ano"].notna()].copy()

    contas = [c for c, _ in plano_contas]
    nomes = {c: n for c, n in plano_contas}

    periodos = pd.concat(
        [tri[["ano", "q"]].dropna(), anu[["ano", "q"]].dropna()],
        ignore_index=True,
    ).drop_duplicates().sort_values(["ano", "q"]).astype(int)

    periodos = list(periodos.itertuples(index=False, name=None))
    if not periodos:
        return pd.DataFrame(
            {"cd_conta_padrao": contas, "ds_conta_padrao": [nomes[c] for c in contas]}
        )

    ytd = pd.DataFrame(
        index=contas,
        columns=pd.MultiIndex.from_tuples(periodos, names=["ano", "q"]),
        dtype="float64",
    )

    def _valor_total_periodo(df_periodo: pd.DataFrame, codigo: str) -> float:
        exact = df_periodo[df_periodo["cd_conta"] == codigo]
        if not exact.empty:
            s = exact["valor"].dropna()
            return float(s.iloc[-1]) if not s.empty else np.nan

        if permitir_rollup_descendentes:
            desc = df_periodo[df_periodo["cd_conta"].str.startswith(codigo + ".")]
            if not desc.empty:
                return float(desc["valor"].sum(skipna=True))

        return np.nan

    # preencher YTD (T1..T3 do tri + T4 anual)
    for (ano, q) in periodos:
        if q in (1, 2, 3):
            dfp = tri[(tri["ano"] == ano) & (tri["q"] == q)]
        else:
            dfp = anu[(anu["ano"] == ano) & (anu["q"] == 4)]

        if dfp.empty:
            continue

        for cod in contas:
            if cod == DA_CODE:
                ytd.at[cod, (ano, q)] = _capturar_depreciacao_amortizacao(dfp)
            else:
                ytd.at[cod, (ano, q)] = _valor_total_periodo(dfp, cod)

    # converter para trimestre isolado
    qt = ytd.copy()
    anos = sorted({a for (a, _) in periodos})

    for ano in anos:
        has = {(a, q) for (a, q) in periodos if a == ano}

        # Fluxos (inclui 6.01.DA)
        for cod in contas:
            if cod in SALDO_ACCOUNTS:
                continue

            if (ano, 1) in has:
                qt.loc[cod, (ano, 1)] = ytd.loc[cod, (ano, 1)]
            if (ano, 2) in has and (ano, 1) in has:
                qt.loc[cod, (ano, 2)] = ytd.loc[cod, (ano, 2)] - ytd.loc[cod, (ano, 1)]
            if (ano, 3) in has and (ano, 2) in has:
                qt.loc[cod, (ano, 3)] = ytd.loc[cod, (ano, 3)] - ytd.loc[cod, (ano, 2)]
            if (ano, 4) in has and (ano, 3) in has:
                qt.loc[cod, (ano, 4)] = ytd.loc[cod, (ano, 4)] - ytd.loc[cod, (ano, 3)]

        # Saldos:
        # 6.05.02 (final): usa o valor do próprio período (não diferenciar)
        if "6.05.02" in contas:
            if (ano, 1) in has:
                qt.loc["6.05.02", (ano, 1)] = ytd.loc["6.05.02", (ano, 1)]
            if (ano, 2) in has:
                qt.loc["6.05.02", (ano, 2)] = ytd.loc["6.05.02", (ano, 2)]
            if (ano, 3) in has:
                qt.loc["6.05.02", (ano, 3)] = ytd.loc["6.05.02", (ano, 3)]
            if (ano, 4) in has:
                qt.loc["6.05.02", (ano, 4)] = ytd.loc["6.05.02", (ano, 4)]

        # 6.05.01 (inicial): Q1 = inicial do ano; Q2 = final T1; Q3 = final T2; Q4 = final T3
        if "6.05.01" in contas and "6.05.02" in contas:
            if (ano, 1) in has:
                qt.loc["6.05.01", (ano, 1)] = ytd.loc["6.05.01", (ano, 1)]
            if (ano, 2) in has and (ano, 1) in has:
                qt.loc["6.05.01", (ano, 2)] = ytd.loc["6.05.02", (ano, 1)]
            if (ano, 3) in has and (ano, 2) in has:
                qt.loc["6.05.01", (ano, 3)] = ytd.loc["6.05.02", (ano, 2)]
            if (ano, 4) in has and (ano, 3) in has:
                qt.loc["6.05.01", (ano, 4)] = ytd.loc["6.05.02", (ano, 3)]

    # saída
    out = pd.DataFrame(
        {"cd_conta_padrao": contas, "ds_conta_padrao": [nomes[c] for c in contas]}
    )

    for (ano, q) in periodos:
        out[f"{ano}-T{q}"] = qt[(ano, q)].values

    return out
