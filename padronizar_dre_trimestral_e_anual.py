import pandas as pd
import numpy as np

# -----------------------------
# CONFIG: plano de contas padrão DRE
# -----------------------------
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
    itr_is_ytd: bool = True,
    unidade: str = "mil",
    preencher_derivadas: bool = True
) -> pd.DataFrame:
    """
    Retorna DataFrame no padrão:
      col1 cd_conta_padrao
      col2 ds_conta_padrao
      colunas seguintes: YYYY-T1, YYYY-T2, YYYY-T3, YYYY-T4 (isolados), do mais antigo ao mais novo

    - dre_trimestral_csv: arquivo ITR (ex: dre_consolidado.csv)
    - dre_anual_csv: arquivo DFP (ex: dre_anual.csv)
    - itr_is_ytd: True = calcula trimestre isolado por diferenças (recomendado p/ ITR/DFP)
    - unidade:
        "mil"     -> mantém como está (valor_mil)
        "unidade" -> multiplica por 1000
        "milhao"  -> divide por 1000
    - preencher_derivadas: se faltar 3.03/3.05/3.07/3.09/3.11, calcula pelas relações
    """

    # --------- carregar ----------
    tri = pd.read_csv(dre_trimestral_csv)
    anu = pd.read_csv(dre_anual_csv)

    # colunas esperadas
    cols = {"data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"}
    for name, df in [("trimestral", tri), ("anual", anu)]:
        missing = cols - set(df.columns)
        if missing:
            raise ValueError(f"Arquivo {name} sem colunas esperadas: {missing}")

    # --------- normalizações básicas ----------
    for df in (tri, anu):
        df["data_fim"] = pd.to_datetime(df["data_fim"], errors="coerce")
        df["trimestre"] = df["trimestre"].astype(str).str.upper().str.strip()
        df["cd_conta"] = df["cd_conta"].astype(str).str.strip()
        df["ds_conta"] = df["ds_conta"].astype(str)
        df["valor_mil"] = pd.to_numeric(df["valor_mil"], errors="coerce")

    # anual deve ser sempre T4
    anu["trimestre"] = "T4"

    # --------- unidade ----------
    fator = 1.0
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

    # --------- montar período (ano, q) ----------
    qmap = {"T1": 1, "T2": 2, "T3": 3, "T4": 4}
    tri["ano"] = tri["data_fim"].dt.year
    tri["q"] = tri["trimestre"].map(qmap)

    anu["ano"] = anu["data_fim"].dt.year
    anu["q"] = 4

    # mantém só trimestres válidos
    tri = tri[tri["q"].isin([1, 2, 3, 4])].copy()
    anu = anu[anu["ano"].notna()].copy()

    # --------- helper: pegar valor "padrão" de uma conta em um período ----------
    def _valor_total_periodo(df_periodo: pd.DataFrame, codigo: str) -> float:
        """
        Regra:
        - Se existe a conta exata (ex: 3.01), usa ela
        - Senão soma descendentes (ex: 3.01.01 + 3.01.02...)
        """
        exact = df_periodo[df_periodo["cd_conta"] == codigo]
        if not exact.empty:
            # se tiver mais de um, pega o último não-nulo
            s = exact["valor"].dropna()
            return float(s.iloc[-1]) if not s.empty else np.nan

        desc = df_periodo[df_periodo["cd_conta"].str.startswith(codigo + ".")]
        if not desc.empty:
            return float(desc["valor"].sum(skipna=True))

        return np.nan

    def _valor_eps_periodo(df_periodo: pd.DataFrame) -> float:
        """
        Inteligência EPS:
        - prioridade: 3.99 -> 3.99.01 -> 3.99.02 -> qualquer 3.99.*
        - retorna 1 valor só (não soma)
        """
        candidatos = ["3.99", "3.99.01", "3.99.02"]
        for c in candidatos:
            part = df_periodo[df_periodo["cd_conta"] == c]["valor"].dropna()
            if not part.empty:
                return float(part.iloc[-1])

        part = df_periodo[df_periodo["cd_conta"].str.startswith("3.99.")]["valor"].dropna()
        if not part.empty:
            return float(part.iloc[-1])

        return np.nan

    # --------- construir série YTD por período (ano,q) para cada conta padrão ----------
    # junta tri + anu para ter (1..4) onde existir
    base = pd.concat([
        tri[["ano", "q", "cd_conta", "ds_conta", "valor"]],
        anu[["ano", "q", "cd_conta", "ds_conta", "valor"]],
    ], ignore_index=True)

    # lista de períodos ordenados
    periodos = (
        base[["ano", "q"]]
        .dropna()
        .drop_duplicates()
        .sort_values(["ano", "q"])
        .astype(int)
        .itertuples(index=False, name=None)
    )
    periodos = list(periodos)

    # monta matriz (contas x períodos) em formato YTD (ou “como veio”)
    contas = [c for c, _ in DRE_PADRAO]
    nomes = {c: n for c, n in DRE_PADRAO}

    ytd = pd.DataFrame(index=contas, columns=periodos, dtype="float64")

    for (ano, q) in periodos:
        dfp = base[(base["ano"] == ano) & (base["q"] == q)]
        if dfp.empty:
            continue

        for cod in contas:
            if cod == "3.99":
                ytd.loc[cod, (ano, q)] = _valor_eps_periodo(dfp)
            else:
                ytd.loc[cod, (ano, q)] = _valor_total_periodo(dfp, cod)

    # --------- preencher derivadas (opcional) ----------
    # OBS: na CVM, custos/despesas geralmente vêm NEGATIVOS.
    # Por isso as relações são por soma:
    # 3.03 = 3.01 + 3.02
    # 3.05 = 3.03 + 3.04
    # 3.07 = 3.05 + 3.06
    # 3.09 = 3.07 + 3.08
    # 3.11 = 3.09 + 3.10
    if preencher_derivadas:
        def _fill(code, expr_codes):
            if code not in ytd.index:
                return
            missing_mask = ytd.loc[code].isna()
            if not missing_mask.any():
                return
            s = None
            for c in expr_codes:
                if s is None:
                    s = ytd.loc[c].copy()
                else:
                    s = s.add(ytd.loc[c], fill_value=np.nan)
            ytd.loc[code, missing_mask] = s[missing_mask]

        _fill("3.03", ["3.01", "3.02"])
        _fill("3.05", ["3.03", "3.04"])
        _fill("3.07", ["3.05", "3.06"])
        _fill("3.09", ["3.07", "3.08"])
        _fill("3.11", ["3.09", "3.10"])

    # --------- isolar trimestres (Q1..Q4) ----------
    # EPS (3.99) NÃO deve ser “diferenciado” (não faz sentido subtrair EPS anual)
    isolado = ytd.copy()

    if itr_is_ytd:
        for ano in sorted({a for (a, q) in periodos}):
            # pega colunas existentes para o ano
            cols_ano = [(a, q) for (a, q) in periodos if a == ano]
            if not cols_ano:
                continue
            cols_ano = sorted(cols_ano, key=lambda x: x[1])

            # para cada conta (exceto EPS): Q1=YTD1; Q2=YTD2-YTD1; Q3=YTD3-YTD2; Q4=YTD4-YTD3
            for cod in isolado.index:
                if cod == "3.99":
                    continue

                for i, (a, q) in enumerate(cols_ano):
                    if i == 0:
                        # Q1 permanece
                        continue
                    prev = cols_ano[i - 1]
                    isolado.loc[cod, (a, q)] = isolado.loc[cod, (a, q)] - ytd.loc[cod, prev]

    # --------- formatar colunas finais YYYY-Tn ----------
    col_labels = [f"{ano}-T{q}" for (ano, q) in periodos]
    out = pd.DataFrame({
        "cd_conta_padrao": contas,
        "ds_conta_padrao": [nomes[c] for c in contas],
    })

    # adiciona colunas (do mais antigo para o mais novo)
    for (ano, q), label in zip(periodos, col_labels):
        out[label] = isolado[(ano, q)].values

    return out
