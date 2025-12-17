import pandas as pd
import numpy as np

BPP_PADRAO = [
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

BPA_PADRAO = [
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


def _padronizar_balanco_trimestral_e_anual(
    csv_trimestral: str,
    csv_anual: str,
    plano_contas: list[tuple[str, str]],
    *,
    unidade: str = "mil",
    permitir_rollup_descendentes: bool = True,
) -> pd.DataFrame:
    """
    BPA/BPP (estoque):
    - T1..T3: usa ITR como está (sem diferença)
    - T4: usa DFP (anual) como está (sem subtração)
    """

    tri = pd.read_csv(csv_trimestral)
    anu = pd.read_csv(csv_anual)

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

    tri = tri[tri["q"].isin([1, 2, 3, 4])].copy()
    anu = anu[anu["ano"].notna()].copy()

    # períodos (união) - mas T4 deve vir do anual quando existir
    periodos = pd.concat(
        [tri[["ano", "q"]].dropna(), anu[["ano", "q"]].dropna()],
        ignore_index=True,
    ).drop_duplicates().sort_values(["ano", "q"]).astype(int)

    periodos = list(periodos.itertuples(index=False, name=None))
    if not periodos:
        contas = [c for c, _ in plano_contas]
        nomes = {c: n for c, n in plano_contas}
        return pd.DataFrame(
            {"cd_conta_padrao": contas, "ds_conta_padrao": [nomes[c] for c in contas]}
        )

    cols_mi = pd.MultiIndex.from_tuples(periodos, names=["ano", "q"])

    contas = [c for c, _ in plano_contas]
    nomes = {c: n for c, n in plano_contas}

    mat = pd.DataFrame(index=contas, columns=cols_mi, dtype="float64")

    def _valor_total_periodo(df_periodo: pd.DataFrame, codigo: str) -> float:
        # 1) conta exata
        exact = df_periodo[df_periodo["cd_conta"] == codigo]
        if not exact.empty:
            s = exact["valor"].dropna()
            return float(s.iloc[-1]) if not s.empty else np.nan

        # 2) rollup de descendentes (dentro do mesmo período) — opcional
        if permitir_rollup_descendentes:
            desc = df_periodo[df_periodo["cd_conta"].str.startswith(codigo + ".")]
            if not desc.empty:
                return float(desc["valor"].sum(skipna=True))

        return np.nan

    # preencher matriz
    for (ano, q) in periodos:
        if q == 4:
            # prioridade: anual (DFP) para T4
            dfp = anu[(anu["ano"] == ano) & (anu["q"] == 4)]
            if dfp.empty:
                # fallback: se não houver anual, tenta T4 do trimestral (se existir)
                dfp = tri[(tri["ano"] == ano) & (tri["q"] == 4)]
        else:
            dfp = tri[(tri["ano"] == ano) & (tri["q"] == q)]

        if dfp.empty:
            continue

        for cod in contas:
            mat.at[cod, (ano, q)] = _valor_total_periodo(dfp, cod)

    # saída final
    out = pd.DataFrame(
        {"cd_conta_padrao": contas, "ds_conta_padrao": [nomes[c] for c in contas]}
    )

    for (ano, q) in periodos:
        out[f"{ano}-T{q}"] = mat[(ano, q)].values

    return out


def padronizar_bpp_trimestral_e_anual(
    bpp_trimestral_csv: str,
    bpp_anual_csv: str,
    *,
    unidade: str = "mil",
    permitir_rollup_descendentes: bool = True,
) -> pd.DataFrame:
    return _padronizar_balanco_trimestral_e_anual(
        bpp_trimestral_csv,
        bpp_anual_csv,
        BPP_PADRAO,
        unidade=unidade,
        permitir_rollup_descendentes=permitir_rollup_descendentes,
    )


def padronizar_bpa_trimestral_e_anual(
    bpa_trimestral_csv: str,
    bpa_anual_csv: str,
    *,
    unidade: str = "mil",
    permitir_rollup_descendentes: bool = True,
) -> pd.DataFrame:
    return _padronizar_balanco_trimestral_e_anual(
        bpa_trimestral_csv,
        bpa_anual_csv,
        BPA_PADRAO,
        unidade=unidade,
        permitir_rollup_descendentes=permitir_rollup_descendentes,
    )
