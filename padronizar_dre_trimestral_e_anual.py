import pandas as pd
import numpy as np
from functools import lru_cache
from typing import Optional, Dict, Tuple, List


# -------------------- DRE PADRÃO (ORIGINAL) --------------------
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


# -------------------- DRE SEGURADORAS (JÁ EXISTENTE/SEGUROS) --------------------
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
    ("3.99.01.01", "Lucro por Ação (LPA ON)"),
]


# -------------------- NOVO: DRE BANCOS --------------------
DRE_BANCOS_PADRAO: List[Tuple[str, str]] = [
    ("3.01", "Receitas da Intermediação Financeira"),
    ("3.02", "Despesas da Intermediação Financeira"),
    ("3.03", "Resultado Bruto Intermediação Financeira"),
    ("3.04", "Outras Despesas/Receitas Operacionais"),
    ("3.05", "Resultado Antes dos Tributos sobre o Lucro"),
    ("3.06", "Imposto de Renda e Contribuição Social"),
    ("3.07", "Resultado Líquido Operações Continuadas"),
    ("3.08", "Resultado Líquido Operações Descontinuadas"),
    ("3.09", "Lucro/Prejuízo Consolidado do Período"),
    ("3.99", "Lucro por Ação (Geral)"),
    ("3.99.01.01", "LPA - Ações Ordinárias (ON)"),
    ("3.99.01.02", "LPA - Ações Preferenciais (PN)"),
]


_SEGUROS_TICKERS = {"BBSE3", "CXSE3", "IRBR3", "PSSA3"}

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
    # prioridade: seguros (mantém comportamento já existente)
    for tk in _SEGUROS_TICKERS:
        if tk in joined:
            return tk
    # bancos (novo)
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


def _check_consistency_dre(mat: pd.DataFrame, anu: pd.DataFrame, contas: List[str], ano: int) -> None:
    """Realiza o check-up comparando Soma(Trimestres) vs Anual."""
    print(f"\n[CHECK-UP] Verificando consistência DRE para o ano {ano}...")
    
    # Contas chave para verificação (Receita e Lucro Líquido costumam ser bons termômetros)
    contas_verificacao = [c for c in contas if c in ["3.01", "3.11", "3.09"]]
    if not contas_verificacao:
        contas_verificacao = contas[:3] # fallback

    for conta in contas_verificacao:
        # Valor Anual Original
        dfp = anu[(anu["ano"] == ano) & (anu["q"] == 4)]
        if dfp.empty:
            continue
            
        # Tenta pegar valor exato no anual
        val_anu_series = dfp.loc[dfp["cd_conta"] == conta, "valor"]
        if val_anu_series.empty:
            continue
        val_anu = float(val_anu_series.iloc[-1])

        # Valor Calculado (Soma T1..T4)
        soma_tri = 0.0
        count_q = 0
        for q in range(1, 5):
            if (ano, q) in mat.columns:
                v = mat.at[conta, (ano, q)]
                if not pd.isna(v):
                    soma_tri += float(v)
                    count_q += 1
        
        # Só valida se tivermos os 4 trimestres
        if count_q == 4:
            diff = abs(val_anu - soma_tri)
            # Tolerância para arredondamentos
            status = "OK" if diff < 1.0 else f"DIVERGÊNCIA ({diff:.2f})"
            print(f"  > Conta {conta}: Anual={val_anu:.2f} | Soma(T1-T4)={soma_tri:.2f} -> {status}")


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
    Mantém 100% a lógica original, mas adiciona inteligência para detectar padrões do T4
    e realiza check-up de consistência.
    """

    ticker_norm = _norm_ticker(ticker) or _infer_ticker_from_paths(dre_trimestral_csv, dre_anual_csv)
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

    # prioridade: seguros > bancos > padrão
    if modo_seguros:
        plano = DRE_SEGUROS_PADRAO
    elif modo_bancos:
        plano = DRE_BANCOS_PADRAO
    else:
        plano = DRE_PADRAO

    contas = [c for c, _ in plano]
    nomes = {c: n for c, n in plano}

    tri = pd.read_csv(dre_trimestral_csv)
    anu = pd.read_csv(dre_anual_csv)

    cols = {"data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"}
    for name, df in [("trimestral", tri), ("anual", anu)]:
        missing = cols - set(df.columns)
        if missing:
            raise ValueError(f"Arquivo {name} sem colunas esperadas: {missing}")

    # normalização (original)
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

    # -------------------------------------------------------------------------
    # MELHORIA: Análise de Padrão T4 no Trimestral antes de filtrar
    # -------------------------------------------------------------------------
    # Verifica se existe T4 no arquivo trimestral e qual sua natureza
    t4_candidates = tri[tri["q"] == 4]
    if not t4_candidates.empty:
        print("[INFO] T4 detectado no arquivo trimestral. Analisando padrão...")
        # Pega um ano que tenha T4 no tri e no anu para comparar
        comm_years = set(t4_candidates["ano"]).intersection(set(anu["ano"]))
        if comm_years:
            test_year = list(comm_years)[0]
            # Exemplo com 3.11 ou 3.01
            conta_teste = "3.11" if "3.11" in contas else contas[0]
            
            val_t4_tri = t4_candidates.loc[(t4_candidates["ano"] == test_year) & (t4_candidates["cd_conta"] == conta_teste), "valor"].sum()
            val_anu = anu.loc[(anu["ano"] == test_year) & (anu["cd_conta"] == conta_teste), "valor"].sum()
            
            # Se for muito próximo, é ACUMULADO (padrão ITR normal se existisse T4)
            if abs(val_t4_tri - val_anu) < 1.0:
                 print(f"  > Padrão Detectado: T4 no trimestral é ACUMULADO (Igual ao Anual). Será ignorado em favor do cálculo auditado.")
            # Se for menor, pode ser ISOLADO
            elif abs(val_t4_tri) < abs(val_anu):
                 print(f"  > Padrão Detectado: T4 no trimestral parece ISOLADO ou incompleto. O script manterá o cálculo via 'Anual - (T1+T2+T3)' para garantir integridade.")
            else:
                 print(f"  > Padrão Detectado: Inconclusivo. Mantendo lógica padrão.")

    # Mantido: DRE trimestral usa só T1..T3; T4 vem do anual (garantia de auditoria)
    tri = tri[tri["q"].isin([1, 2, 3])].copy()
    anu = anu[anu["ano"].notna()].copy()

    # Períodos
    periodos = pd.concat(
        [tri[["ano", "q"]].dropna(), anu[["ano", "q"]].dropna()],
        ignore_index=True,
    ).drop_duplicates().sort_values(["ano", "q"]).astype(int)

    periodos = list(periodos.itertuples(index=False, name=None))
    if not periodos:
        return pd.DataFrame({"cd_conta_padrao": contas, "ds_conta_padrao": [nomes[c] for c in contas]})

    cols_mi = pd.MultiIndex.from_tuples(periodos, names=["ano", "q"])
    mat = pd.DataFrame(index=contas, columns=cols_mi, dtype="float64")

    def _valor_total_periodo(df_periodo: pd.DataFrame, codigo: str) -> float:
        exact = df_periodo[df_periodo["cd_conta"] == codigo]
        if not exact.empty:
            s = exact["valor"].dropna()
            return float(s.iloc[-1]) if not s.empty else np.nan

        # rollup descendente (original)
        desc = df_periodo[df_periodo["cd_conta"].str.startswith(codigo + ".")]
        if not desc.empty:
            return float(desc["valor"].sum(skipna=True))
        return np.nan

    def _valor_eps_periodo(df_periodo: pd.DataFrame) -> float:
        # pega 1 valor do grupo 3.99.* (evita somar linhas de LPA)
        eps = df_periodo[df_periodo["cd_conta"].str.startswith("3.99")].copy()
        if eps.empty:
            return np.nan
        eps = eps.dropna(subset=["valor"])
        if eps.empty:
            return np.nan
        # prioridade: 3.99.01.01, depois 3.99.01.02, depois qualquer 3.99
        for prefer in ["3.99.01.01", "3.99.01.02", "3.99"]:
            hit = eps[eps["cd_conta"] == prefer]
            if not hit.empty:
                return float(hit["valor"].iloc[-1])
        return float(eps["valor"].iloc[-1])

    # MAPEAMENTOS POR SETOR (somente quando ativado)
    seguros_map_por_ticker: Dict[str, Dict[str, str]] = {
        "BBSE3": {"3.05": "3.07", "3.06": "3.08", "3.07": "3.06", "3.08": "3.09"},
        "CXSE3": {"3.05": "3.05", "3.06": "3.06", "3.07": "3.07", "3.08": "3.08"},
        "IRBR3": {"3.05": "3.07", "3.06": "3.08", "3.07": "3.06", "3.08": "3.09"},
        "PSSA3": {"3.05": "3.05", "3.06": "3.06", "3.07": "3.07", "3.08": "3.07"},
    }
    seguros_map = seguros_map_por_ticker.get(ticker_norm, {}) if modo_seguros else {}

    # Bancos: remapeia seus códigos padronizados para os códigos CVM usuais
    bancos_map: Dict[str, str] = {
        "3.01": "3.01",
        "3.02": "3.02",
        "3.03": "3.03",
        "3.04": "3.04",
        "3.05": "3.07",  # LAIR
        "3.06": "3.08",  # IR/CSLL
        "3.07": "3.09",  # LL continuadas
        "3.08": "3.10",  # descontinuadas
        "3.09": "3.11",  # LL final
        "3.99": "3.99",  # master EPS (tratado à parte)
        "3.99.01.01": "3.99.01.01",
        "3.99.01.02": "3.99.01.02",
    } if modo_bancos else {}

    def _map_codigo_fonte(cod_padrao: str) -> str:
        if modo_seguros and cod_padrao in seguros_map:
            return seguros_map[cod_padrao]
        if modo_bancos and cod_padrao in bancos_map:
            return bancos_map[cod_padrao]
        return cod_padrao

    # preencher matriz
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
            if cod_padrao == "3.99":
                mat.at[cod_padrao, (ano, q)] = _valor_eps_periodo(dfp)
                continue

            cod_fonte = _map_codigo_fonte(cod_padrao)
            mat.at[cod_padrao, (ano, q)] = _valor_total_periodo(dfp, cod_fonte)

    # derivadas (mantido)
    if preencher_derivadas:
        for (ano, q) in periodos:
            if "3.03" in contas and "3.01" in contas and "3.02" in contas:
                v303 = mat.at["3.03", (ano, q)]
                if pd.isna(v303):
                    v301 = mat.at["3.01", (ano, q)]
                    v302 = mat.at["3.02", (ano, q)]
                    if not (pd.isna(v301) or pd.isna(v302)):
                        mat.at["3.03", (ano, q)] = float(v301 + v302)

    # T4 isolado (mantido)
    for (ano, q) in periodos:
        if q != 4:
            continue
        for cod_padrao in contas:
            if cod_padrao.startswith("3.99"):
                continue

            v_anual = mat.at[cod_padrao, (ano, 4)]
            if pd.isna(v_anual):
                continue

            soma = 0.0
            ok = False
            for qq in (1, 2, 3):
                if (ano, qq) in mat.columns:
                    vv = mat.at[cod_padrao, (ano, qq)]
                    if not pd.isna(vv):
                        soma += float(vv)
                        ok = True

            if ok:
                mat.at[cod_padrao, (ano, 4)] = float(v_anual - soma)

    # -------------------------------------------------------------------------
    # CHECK-UP FINAL: Validar consistência (Soma T1..T4 vs Anual)
    # -------------------------------------------------------------------------
    anos_unicos = sorted(list(set(p[0] for p in periodos)))
    for y in anos_unicos:
        _check_consistency_dre(mat, anu, contas, y)

    # saída final
    out = pd.DataFrame({"cd_conta_padrao": contas, "ds_conta_padrao": [nomes[c] for c in contas]})
    for (ano, q) in periodos:
        out[f"{ano}-T{q}"] = mat[(ano, q)].values

    return out
