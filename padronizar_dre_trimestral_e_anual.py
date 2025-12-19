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
    Mantém 100% a lógica original:
    - Trimestral (ITR): usa períodos como estão (sem assumir YTD).
    - Anual (DFP): representa o fechamento do exercício (trimestre fiscal 4).
    - T4 (trimestre fiscal isolado): Anual(DFP) - (T1 + T2 + T3) para contas de resultado (exceto EPS).
    - EPS (3.99*): pega 1 valor por período e NÃO subtrai.

    Melhorias (aditivas, sem quebrar o padrão existente):
    - Suporte a exercícios fiscais que NÃO fecham em 12/31 (ex.: 03/31, 06/30):
      * Reatribui 'ano' e 'q' por ANO FISCAL e TRIMESTRE FISCAL.
      * Permite que T1/T2/T3 do fiscal caiam no ano-calendário anterior (ex.: FY 2024 com Jun/Set/Dez 2023).
    - Check-up automático: compara (quando possível) soma dos trimestres isolados vs anual (DFP) por conta,
      e também imprime faltas (T1..T3) quando anual existe.
    """

    ticker_norm = _norm_ticker(ticker) or _infer_ticker_from_paths(dre_trimestral_csv, dre_anual_csv)

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

    # ---------------------------------------------
    # Exercício fiscal (NOVO - aditivo, sem quebrar padrão)
    # ---------------------------------------------
    def _infer_fy_end_month(df_anual: pd.DataFrame) -> int:
        d = pd.to_datetime(df_anual["data_fim"], errors="coerce")
        m = d.dt.month.dropna()
        if m.empty:
            return 12
        counts = m.value_counts()
        top = counts.index.tolist()
        for pref in [12, 3, 6, 9]:
            if pref in top:
                return int(pref)
        return int(top[0])

    fy_end_month = _infer_fy_end_month(anu)

    # delta = (mes - mes_fechamento) % 12
    # 0 => Q4 fiscal (fechamento); 3 => Q1; 6 => Q2; 9 => Q3
    _delta_to_q = {0: 4, 3: 1, 6: 2, 9: 3}

    def _apply_fiscal_index(df: pd.DataFrame, *, is_anual: bool) -> pd.DataFrame:
        df = df.copy()
        dt = pd.to_datetime(df["data_fim"], errors="coerce")
        m = dt.dt.month
        y = dt.dt.year

        delta = (m - fy_end_month) % 12
        q_fiscal = delta.map(_delta_to_q)

        q_cal = df["trimestre"].map(qmap)

        if is_anual:
            q_fiscal = pd.Series(4, index=df.index, dtype="float64")

        df["q"] = q_fiscal.fillna(q_cal).astype("Int64")

        # Ano fiscal = ano do fechamento (mês > mês_fechamento => FY do ano seguinte)
        df["ano"] = (y + (m > fy_end_month).astype("int")).astype("Int64")

        return df

    tri_all = _apply_fiscal_index(tri, is_anual=False)
    anu_all = _apply_fiscal_index(anu, is_anual=True)

    # anual sempre T4 (fiscal)
    anu_all["trimestre"] = "T4"

    # Mantido: DRE trimestral usa só T1..T3 (agora do FISCAL); T4 vem do anual
    tri = tri_all[tri_all["q"].isin([1, 2, 3])].copy()
    anu = anu_all[anu_all["ano"].notna()].copy()

    # Períodos (por ano fiscal + trimestre fiscal)
    periodos = pd.concat(
        [tri[["ano", "q"]].dropna(), anu[["ano", "q"]].dropna()],
        ignore_index=True,
    ).drop_duplicates().sort_values(["ano", "q"]).astype(int)

    periodos = list(periodos.itertuples(index=False, name=None))

    if not periodos:
        return pd.DataFrame({"cd_conta_padrao": [], "ds_conta_padrao": []})

    # ---------------------------------
    # Plano de contas padrão (original)
    # ---------------------------------
    contas = [
        "3.01",
        "3.02",
        "3.03",
        "3.04",
        "3.05",
        "3.06",
        "3.07",
        "3.08",
        "3.09",
        "3.10",
        "3.11",
        "3.99",
    ]

    nomes = {
        "3.01": "Receita Líquida de Vendas e/ou Serviços",
        "3.02": "Custo dos Produtos Vendidos e/ou Serviços Prestados",
        "3.03": "Resultado Bruto",
        "3.04": "Despesas/Receitas Operacionais",
        "3.05": "Resultado Antes do Resultado Financeiro e dos Tributos",
        "3.06": "Resultado Financeiro",
        "3.07": "Resultado Antes dos Tributos sobre o Lucro",
        "3.08": "Imposto de Renda e Contribuição Social sobre o Lucro",
        "3.09": "Resultado Líquido das Operações Continuadas",
        "3.10": "Resultado Líquido de Operações Descontinuadas",
        "3.11": "Lucro/Prejuízo Consolidado do Período",
        "3.99": "Lucro por Ação (EPS) - grupo 3.99.*",
    }

    # ----------------------------
    # Segmento por ticker (B3 map)
    # ----------------------------
    segmento = None
    if b3_mapping_csv:
        try:
            _, segmento = _get_setor_segmento_from_b3_mapping(ticker_norm or "", b3_mapping_csv=b3_mapping_csv)
        except Exception:
            segmento = None

    # ----------------------------
    # Mapas (original)
    # ----------------------------
    seguros_map_por_ticker = {
        # seguradoras tipicamente usam 3.01.01 para prêmios ganhos; mapeamos Receita -> 3.01.01
        "PSSA3": {"3.01": "3.01.01"},
        "BBSE3": {"3.01": "3.01.01"},
        "SULA11": {"3.01": "3.01.01"},
        "IRBR3": {"3.01": "3.01.01"},
    }

    bancos_map = {
        "3.01": "3.01.04",  # Receita Intermediação Financeira
        "3.02": "",         # CPV não faz sentido p/ banco
        "3.04": "3.03",     # Outras Receitas/Despesas Operacionais (varia bastante)
        "3.06": "3.05",     # Resultado Financeiro pode estar em 3.05/3.06
    }

    modo_bancos = bool(segmento and "BANCO" in str(segmento).upper())
    modo_seguros = bool(ticker_norm and ticker_norm in seguros_map_por_ticker)

    # se for seguro e tiver mapping específico
    mapa_custom = seguros_map_por_ticker.get(ticker_norm, {}) if modo_seguros else {}
    mapa_bancos = bancos_map if modo_bancos else {}

    def _map_codigo_fonte(cod_padrao: str) -> str:
        if modo_seguros and cod_padrao in mapa_custom:
            return mapa_custom[cod_padrao]
        if modo_bancos and cod_padrao in mapa_bancos and mapa_bancos[cod_padrao] is not None:
            return mapa_bancos[cod_padrao]
        return cod_padrao

    # ---------------------------------
    # Auxiliares (originais)
    # ---------------------------------
    cols_mi = pd.MultiIndex.from_tuples(periodos, names=["ano", "q"])
    mat = pd.DataFrame(index=contas, columns=cols_mi, dtype="float64")

    def _valor_total_periodo(df_periodo: pd.DataFrame, codigo: str) -> float:
        if codigo is None or str(codigo).strip() == "":
            return np.nan

        codigo = str(codigo).strip()

        exact = df_periodo[df_periodo["cd_conta"] == codigo]
        if not exact.empty:
            s = exact["valor"].dropna()
            return float(s.iloc[-1]) if not s.empty else np.nan

        desc = df_periodo[df_periodo["cd_conta"].str.startswith(codigo + ".")]
        if not desc.empty:
            return float(desc["valor"].sum(skipna=True))

        return np.nan

    def _valor_eps_periodo(df_periodo: pd.DataFrame) -> float:
        eps = df_periodo[df_periodo["cd_conta"].str.startswith("3.99")].copy()
        if eps.empty:
            return np.nan
        s = eps["valor"].dropna()
        return float(s.iloc[-1]) if not s.empty else np.nan

    # ---------------------------------
    # Preenche matriz (mantido: T4 prioriza anual/DFP quando existir)
    # ---------------------------------
    for (ano, q) in periodos:
        if q == 4:
            dfp = anu[(anu["ano"] == ano) & (anu["q"] == 4)]
            if dfp.empty:
                # fallback se, por alguma razão, vier T4 no trimestral
                dfp = tri_all[(tri_all["ano"] == ano) & (tri_all["q"] == 4)]
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

    # ---------------------------------
    # Derivadas (mantido)
    # ---------------------------------
    if preencher_derivadas:
        for (ano, q) in periodos:
            a = mat.at["3.01", (ano, q)] if (ano, q) in mat.columns else np.nan
            b = mat.at["3.02", (ano, q)] if (ano, q) in mat.columns else np.nan
            if not (pd.isna(a) and pd.isna(b)):
                mat.at["3.03", (ano, q)] = (0.0 if pd.isna(a) else float(a)) + (0.0 if pd.isna(b) else float(b))

        for (ano, q) in periodos:
            a = mat.at["3.03", (ano, q)] if (ano, q) in mat.columns else np.nan
            b = mat.at["3.04", (ano, q)] if (ano, q) in mat.columns else np.nan
            if not (pd.isna(a) and pd.isna(b)):
                mat.at["3.05", (ano, q)] = (0.0 if pd.isna(a) else float(a)) + (0.0 if pd.isna(b) else float(b))

        for (ano, q) in periodos:
            a = mat.at["3.05", (ano, q)] if (ano, q) in mat.columns else np.nan
            b = mat.at["3.06", (ano, q)] if (ano, q) in mat.columns else np.nan
            if not (pd.isna(a) and pd.isna(b)):
                mat.at["3.07", (ano, q)] = (0.0 if pd.isna(a) else float(a)) + (0.0 if pd.isna(b) else float(b))

        for (ano, q) in periodos:
            a = mat.at["3.07", (ano, q)] if (ano, q) in mat.columns else np.nan
            b = mat.at["3.08", (ano, q)] if (ano, q) in mat.columns else np.nan
            if not (pd.isna(a) and pd.isna(b)):
                mat.at["3.09", (ano, q)] = (0.0 if pd.isna(a) else float(a)) + (0.0 if pd.isna(b) else float(b))

        for (ano, q) in periodos:
            a = mat.at["3.09", (ano, q)] if (ano, q) in mat.columns else np.nan
            b = mat.at["3.10", (ano, q)] if (ano, q) in mat.columns else np.nan
            if not (pd.isna(a) and pd.isna(b)):
                mat.at["3.11", (ano, q)] = (0.0 if pd.isna(a) else float(a)) + (0.0 if pd.isna(b) else float(b))

    # ---------------------------------
    # T4 isolado (mantido) = anual - soma(T1..T3) por ANO FISCAL
    # ---------------------------------
    for ano in sorted({a for (a, _) in periodos}):
        if (ano, 4) not in mat.columns:
            continue

        dfp_anual = anu[(anu["ano"] == ano) & (anu["q"] == 4)]
        if dfp_anual.empty:
            continue

        for cod_padrao in contas:
            if cod_padrao == "3.99":
                continue
            v_anual = mat.at[cod_padrao, (ano, 4)]
            if pd.isna(v_anual):
                continue

            soma = 0.0
            ok = False
            for qq in [1, 2, 3]:
                if (ano, qq) in mat.columns:
                    vv = mat.at[cod_padrao, (ano, qq)]
                    if not pd.isna(vv):
                        soma += float(vv)
                        ok = True
            if ok:
                mat.at[cod_padrao, (ano, 4)] = float(v_anual - soma)

    # ---------------------------------
    # CHECK-UP (NOVO, não altera o output)
    # ---------------------------------
    try:
        tol_abs = 0.5  # tolerância simples contra arredondamentos (na unidade escolhida)
        tol_rel = 0.02

        anos_chk = sorted({a for (a, _) in periodos})
        for ano in anos_chk:
            df_anu = anu_all[(anu_all["ano"] == ano) & (anu_all["q"] == 4)]
            if df_anu.empty:
                continue

            # 1) faltas de T1..T3 (fiscal)
            faltas = []
            for cod_padrao in contas:
                if cod_padrao == "3.99":
                    continue
                miss = []
                for qq in [1, 2, 3]:
                    if (ano, qq) not in mat.columns or pd.isna(mat.at[cod_padrao, (ano, qq)]):
                        miss.append(qq)
                if miss:
                    faltas.append((cod_padrao, miss))

            if faltas:
                top = faltas[:10]
                print(f"[CHECKUP][DRE][{ticker_norm or ''}] FY{ano}: contas com T1..T3 faltando (top {len(top)})")
                for cod, miss in top:
                    print(f"  - {cod} {nomes.get(cod,'')}: faltando T{','.join(str(x) for x in miss)}")

            # 2) soma dos 4 trimestres isolados vs anual (DFP), quando possível
            diffs = []
            for cod_padrao in contas:
                if cod_padrao == "3.99":
                    continue

                cod_fonte = _map_codigo_fonte(cod_padrao)
                v_anual_raw = _valor_total_periodo(df_anu, cod_fonte)
                if pd.isna(v_anual_raw):
                    continue

                vals = []
                ok = True
                for qq in [1, 2, 3, 4]:
                    if (ano, qq) in mat.columns:
                        vv = mat.at[cod_padrao, (ano, qq)]
                        if pd.isna(vv):
                            ok = False
                            break
                        vals.append(float(vv))
                    else:
                        ok = False
                        break

                if not ok:
                    continue

                v_sum = float(np.nansum(vals))
                diff = float(v_sum - float(v_anual_raw))
                denom = max(1.0, abs(float(v_anual_raw)))
                if abs(diff) > tol_abs and abs(diff) / denom > tol_rel:
                    diffs.append((cod_padrao, diff, v_sum, float(v_anual_raw)))

            if diffs:
                diffs.sort(key=lambda x: abs(x[1]), reverse=True)
                top = diffs[:10]
                print(f"[CHECKUP][DRE][{ticker_norm or ''}] FY{ano}: divergências soma(trimestres isolados) vs anual (top {len(top)})")
                for cod, diff, v_sum, v_anual in top:
                    print(f"  - {cod} {nomes.get(cod,'')}: soma={v_sum:.3f} anual={v_anual:.3f} diff={diff:.3f}")

    except Exception as _e:
        print(f"[CHECKUP][DRE] aviso: falha no check-up ({type(_e).__name__}): {_e}")

    # saída final (mantida)
    out = pd.DataFrame({"cd_conta_padrao": contas, "ds_conta_padrao": [nomes[c] for c in contas]})
    for (ano, q) in periodos:
        out[f"{ano}-T{q}"] = mat[(ano, q)].values

    return out
