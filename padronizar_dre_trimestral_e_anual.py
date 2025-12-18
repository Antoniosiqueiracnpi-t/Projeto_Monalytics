import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple


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

# --- NOVO: Plano padronizado para Seguros (setor segurador) ---
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
    t = t.replace(".SA", "").replace("SA", "") if t.endswith(".SA") else t
    return t


def _infer_ticker_from_paths(*paths: str) -> Optional[str]:
    joined = " ".join([str(p).upper() for p in paths if p is not None])
    for tk in _SEGUROS_TICKERS:
        if tk in joined:
            return tk
    return None


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
) -> pd.DataFrame:
    """
    Padrão de saída:
      cd_conta_padrao | ds_conta_padrao | YYYY-T1 | YYYY-T2 | YYYY-T3 | YYYY-T4 | ...

    Regras (mantidas):
    - T1/T2/T3: usa exatamente o que vier no trimestral (SEM YTD)
    - T4: calcula isolado como:
         T4 = Anual(DFP) - (T1 + T2 + T3)
      para contas de resultado (exceto EPS).
    - EPS (3.99): pega 1 valor por período e NÃO subtrai.

    NOVO (Seguros):
    - Se ticker ∈ {BBSE3, CXSE3, IRBR3, PSSA3}, troca o plano de contas e
      aplica mapeamentos específicos para EBIT/Financeiro/Equivalência/LAIR conforme instruções.
    """

    ticker_norm = _norm_ticker(ticker) or _infer_ticker_from_paths(dre_trimestral_csv, dre_anual_csv)
    modo_seguros = ticker_norm in _SEGUROS_TICKERS

    # Mapeamentos específicos (código-fonte por conta padronizada) — Seguros
    # Obs: para contas não listadas aqui, cai no "mesmo código".
    # - EBIT (pad 3.05): BBSE/IRBR -> 3.07 ; CXSE/PSSA -> 3.05
    # - Financeiro (pad 3.06): BBSE/IRBR -> 3.08 ; CXSE/PSSA -> 3.06
    # - Equivalência (pad 3.07): BBSE/IRBR -> 3.06 ; CXSE/PSSA -> 3.07
    # - LAIR (pad 3.08): BBSE -> 3.09 ; CXSE -> 3.08 ; IRBR -> 3.09 ; PSSA -> 3.07
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

    # normalização (mantida)
    for df in (tri, anu):
        df["data_fim"] = pd.to_datetime(df["data_fim"], errors="coerce")
        df["trimestre"] = df["trimestre"].astype(str).str.upper().str.strip()
        df["cd_conta"] = df["cd_conta"].astype(str).str.strip()
        df["ds_conta"] = df["ds_conta"].astype(str)
        df["valor_mil"] = pd.to_numeric(df["valor_mil"], errors="coerce")

    # anual sempre T4 (mantido)
    anu["trimestre"] = "T4"

    # unidade (mantido)
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

    # Mantém o comportamento original:
    # - DRE trimestral usa só T1..T3 (T4 virá do anual e depois será isolado)
    tri = tri[tri["q"].isin([1, 2, 3])].copy()
    anu = anu[anu["ano"].notna()].copy()

    # períodos (mantido)
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
        Mantém a regra original: tenta conta exata, senão soma descendentes.
        NOVO: aceita expressão com:
          - "+" para somar contas (ex.: "3.04.01+3.04.02")
          - "|" para fallback (primeiro não-NaN) (ex.: "3.07|3.05")
        """
        if codigo_expr is None or str(codigo_expr).strip() == "":
            return np.nan

        codigo_expr = str(codigo_expr).strip()

        # fallback pipe
        if "|" in codigo_expr:
            for part in _split_pipe(codigo_expr):
                v = _valor_total_periodo(df_periodo, part)
                if not pd.isna(v):
                    return float(v)
            return np.nan

        # soma plus
        if "+" in codigo_expr:
            vals = []
            for part in _split_plus(codigo_expr):
                vals.append(_valor_total_periodo(df_periodo, part))
            if all(pd.isna(v) for v in vals):
                return np.nan
            return float(np.nansum(vals))

        # 1) conta exata
        exact = df_periodo[df_periodo["cd_conta"] == codigo_expr]
        if not exact.empty:
            s = exact["valor"].dropna()
            return float(s.iloc[-1]) if not s.empty else np.nan

        # 2) soma descendentes
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

    # preencher T1..T3 (trimestral) e T4 (anual)
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

    # derivadas (mantido para o padrão; adaptado no modo seguros)
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
            # LAIR (3.08) costuma ser: EBIT (3.05) + Fin (3.06) + Equiv (3.07)
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

    out = pd.DataFrame(
        {"cd_conta_padrao": contas, "ds_conta_padrao": [nomes[c] for c in contas]}
    )
    for (ano, q) in periodos:
        out[f"{ano}-T{q}"] = mat[(ano, q)].values

    return out
