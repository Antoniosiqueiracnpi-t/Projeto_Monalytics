import pandas as pd
import numpy as np

DRE_PADRAO = [
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


def padronizar_dre_trimestral_e_anual(
    dre_trimestral_csv: str,
    dre_anual_csv: str,
    *,
    unidade: str = "mil",
    preencher_derivadas: bool = True,
) -> pd.DataFrame:
    """
    Padrão de saída:
      cd_conta_padrao | ds_conta_padrao | YYYY-T1 | YYYY-T2 | YYYY-T3 | YYYY-T4 | ...

    Regras:
    - T1/T2/T3: usa exatamente o que vier no dre_consolidado.csv (SEM diferenciação/YTD)
    - T4: calcula isolado como:
         T4 = Anual(DFP) - (T1 + T2 + T3)
      para contas 3.01..3.11.
    - EPS (3.99): pega 1 valor por período (sem somar/duplicar) e NÃO subtrai.
    """

    tri = pd.read_csv(dre_trimestral_csv)
    anu = pd.read_csv(dre_anual_csv)

    cols = {"data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"}
    for name, df in [("trimestral", tri), ("anual", anu)]:
        missing = cols - set(df.columns)
        if missing:
            raise ValueError(f"Arquivo {name} sem colunas esperadas: {missing}")

    # normalização
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

    contas = [c for c, _ in DRE_PADRAO]
    nomes = {c: n for c, n in DRE_PADRAO}

    # períodos (T1..T3 do tri + T4 do anual)
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
    mat = pd.DataFrame(index=contas, columns=cols_mi, dtype="float64")

    def _valor_total_periodo(df_periodo: pd.DataFrame, codigo: str) -> float:
        exact = df_periodo[df_periodo["cd_conta"] == codigo]
        if not exact.empty:
            s = exact["valor"].dropna()
            return float(s.iloc[-1]) if not s.empty else np.nan

        desc = df_periodo[df_periodo["cd_conta"].str.startswith(codigo + ".")]
        if not desc.empty:
            return float(desc["valor"].sum(skipna=True))

        return np.nan

    def _valor_eps_periodo(df_periodo: pd.DataFrame) -> float:
        """
        EPS inteligente:
        prioriza ON quando existir (3.99.01.01 / 3.99.02.01),
        senão cai para 3.99.01 / 3.99.02 / 3.99,
        senão pega qualquer 3.99* não-zero.
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

    # preencher T1..T3 a partir do trimestral (sem mexer)
    for (ano, q) in periodos:
        if q in (1, 2, 3):
            dfp = tri[(tri["ano"] == ano) & (tri["q"] == q)]
        else:
            dfp = anu[(anu["ano"] == ano) & (anu["q"] == 4)]
        if dfp.empty:
            continue

        for cod in contas:
            if cod == "3.99":
                mat.at[cod, (ano, q)] = _valor_eps_periodo(dfp)
            else:
                mat.at[cod, (ano, q)] = _valor_total_periodo(dfp, cod)

    # opcional: preencher derivadas se faltarem
    if preencher_derivadas:
        def _fill(code, expr_codes):
            if code not in mat.index:
                return
            missing = mat.loc[code].isna()
            if not missing.any():
                return
            s = None
            for c in expr_codes:
                s = mat.loc[c].copy() if s is None else s.add(mat.loc[c], fill_value=np.nan)
            mat.loc[code, missing] = s[missing]

        _fill("3.03", ["3.01", "3.02"])
        _fill("3.05", ["3.03", "3.04"])
        _fill("3.07", ["3.05", "3.06"])
        _fill("3.09", ["3.07", "3.08"])
        _fill("3.11", ["3.09", "3.10"])

    # 🔥 T4 ISOLADO: anual - (T1+T2+T3), apenas para 3.01..3.11
    anos = sorted({a for (a, _) in periodos})
    for ano in anos:
        if (ano, 4) not in mat.columns:
            continue

        for cod in mat.index:
            if cod == "3.99":  # EPS não subtrai
                continue

            a = mat.at[cod, (ano, 4)]
            if pd.isna(a):
                continue

            s = 0.0
            ok = True
            for q in (1, 2, 3):
                v = mat.at[cod, (ano, q)] if (ano, q) in mat.columns else np.nan
                if pd.isna(v):
                    ok = False
                    break
                s += float(v)

            # só calcula T4 isolado se tiver T1,T2,T3 completos
            if ok:
                mat.at[cod, (ano, 4)] = float(a) - s

    # saída final
    out = pd.DataFrame(
        {
            "cd_conta_padrao": contas,
            "ds_conta_padrao": [nomes[c] for c in contas],
        }
    )

    for (ano, q) in periodos:
        out[f"{ano}-T{q}"] = mat[(ano, q)].values

    return out
