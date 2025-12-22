def padronizar_dre_trimestral_e_anual(
    dre_trimestral_csv: str,
    dre_anual_csv: str,
    *,
    unidade: str = "mil",
    preencher_derivadas: bool = True,
    ticker: Optional[str] = None,
    b3_mapping_csv: Optional[str] = None,
    realizar_checkup: bool = True,
    retornar_resultado_completo: bool = False,
) -> pd.DataFrame:
    """
    Padroniza DRE trimestral e anual com detecção automática de padrão.
    
    LÓGICA:
    1. Detecta padrão: YTD (acumulado) ou Isolado
    2. YTD: isola T4 = DFP - soma(ITRs)  (na prática: T4 = Anual - T3_YTD, e T2/T3 via diferenças)
    3. Isolado: mantém trimestres como estão; usa DFP apenas para completar trimestre faltante quando necessário
    4. Check-up rigoroso com validação (inclui: Receita Líquida não pode ser negativa)
    """

    alertas = []

    # Tolerâncias (compatível com diferentes nomes de constantes no projeto)
    tol_pct = globals().get("TOLERANCIA_PCT", globals().get("TOLERANCIA_CHECKUP_PCT", 1.0))
    tol_abs = globals().get("TOLERANCIA_ABS", globals().get("TOLERANCIA_CHECKUP_ABS", 1.0))
    
    # Identificar ticker e setor
    ticker_norm = _norm_ticker(ticker) or _infer_ticker_from_paths(dre_trimestral_csv, dre_anual_csv)
    setor, _segmento = _get_setor_segmento_from_b3_mapping(ticker_norm, b3_mapping_csv)
    setor_l = (setor or "").strip().lower()

    modo_seguros = (ticker_norm in _SEGUROS_TICKERS) or (setor_l == "previdência e seguros")
    modo_bancos = (ticker_norm in _BANCOS_TICKERS) or (setor_l == "bancos")

    if modo_seguros:
        plano = DRE_SEGUROS_PADRAO
    elif modo_bancos:
        plano = DRE_BANCOS_PADRAO
    else:
        plano = DRE_PADRAO

    contas = [c for c, _ in plano]
    nomes = {c: n for c, n in plano}

    # Carregar dados
    tri = pd.read_csv(dre_trimestral_csv)
    anu = pd.read_csv(dre_anual_csv)

    cols = {"data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"}
    for name, df in [("trimestral", tri), ("anual", anu)]:
        missing = cols - set(df.columns)
        if missing:
            raise ValueError(f"Arquivo {name} sem colunas: {missing}")

    # Normalização
    for df in (tri, anu):
        df["data_fim"] = pd.to_datetime(df["data_fim"], errors="coerce")
        df["cd_conta"] = df["cd_conta"].astype(str).str.strip()
        df["ds_conta"] = df["ds_conta"].astype(str)
        df["valor_mil"] = pd.to_numeric(df["valor_mil"], errors="coerce")

    # Detectar mês de encerramento fiscal
    mes_encerramento = _detectar_mes_encerramento_fiscal(anu)
    ano_fiscal_normal = (mes_encerramento == 12)

    # Detectar padrão global (mantido para compatibilidade/telemetria)
    padrao = _detectar_padrao_trimestral(tri, anu, mes_encerramento)
    alertas.append(f"Padrão detectado: {padrao.upper()}")

    if not ano_fiscal_normal:
        alertas.append(f"Ano fiscal diferente: encerramento mês {mes_encerramento}")

    # Fator de unidade
    fator = {"mil": 1.0, "unidade": 1000.0, "milhao": 0.001}.get(unidade, 1.0)
    tri["valor"] = tri["valor_mil"] * fator
    anu["valor"] = anu["valor_mil"] * fator

    # Extrair ano e trimestre
    tri["ano"] = tri["data_fim"].dt.year
    tri["q"] = tri["trimestre"].str.replace("T", "").astype(int)

    anu["ano"] = anu["data_fim"].dt.year
    anu["q"] = anu["data_fim"].dt.month.apply(_mes_para_trimestre)

    # ---------------------------
    # DETECÇÃO DE PADRÃO POR ANO
    # ---------------------------
    padrao_por_ano: Dict[int, Dict[str, Any]] = {}

    def _soma_prefixo(df_ano: pd.DataFrame, q: int, prefixo: str) -> float:
        sub = df_ano[df_ano["q"] == q]
        if sub.empty:
            return np.nan
        hit = sub[sub["cd_conta"].astype(str).str.startswith(prefixo)]
        if hit.empty:
            return np.nan
        return float(pd.to_numeric(hit["valor"], errors="coerce").sum(skipna=True))

    anos_tri = set(tri["ano"].dropna().astype(int).unique().tolist())
    anos_anu = set(anu["ano"].dropna().astype(int).unique().tolist())
    for ano in sorted(anos_tri | anos_anu):
        itrs = tri[tri["ano"] == ano]
        qs = sorted(itrs["q"].dropna().astype(int).unique().tolist()) if not itrs.empty else []
        modo_ano = "isolado"
        evid = []

        if qs == [1, 2, 3]:
            # Teste de coerência para YTD usando Receita (3.01)
            v1 = _soma_prefixo(itrs, 1, "3.01")
            v2 = _soma_prefixo(itrs, 2, "3.01")
            v3 = _soma_prefixo(itrs, 3, "3.01")
            if (not pd.isna(v1)) and (not pd.isna(v2)) and (not pd.isna(v3)) and (v1 > 0) and (v2 > v1) and (v3 > v2):
                modo_ano = "ytd"
            else:
                evid.append("receita_não_crescente_no_ytd")
        else:
            evid.append(f"qs={qs}")

        padrao_por_ano[int(ano)] = {"padrao": modo_ano, "qs": qs, "evidencia": ", ".join(evid)}

    modos = sorted(set(v["padrao"] for v in padrao_por_ano.values())) if padrao_por_ano else []
    if len(modos) > 1:
        alertas.append("⚠️ Padrão misto por ano detectado (ex.: alguns anos YTD, outros isolados).")
        amostra = []
        for a in sorted(padrao_por_ano.keys())[-5:]:
            info = padrao_por_ano[a]
            amostra.append(f"{a}:{info['padrao']}({info.get('qs', [])})")
        alertas.append("Amostra (últimos anos): " + " | ".join(amostra))

    # Listar períodos únicos disponíveis (SEM CRIAR FANTASMAS)
    tri_periodos = list(tri[["ano", "q"]].drop_duplicates().itertuples(index=False, name=None))
    tri_periodos = [(int(a), int(q)) for a, q in tri_periodos if a > 0]

    anu_periodos = list(anu[["ano", "q"]].drop_duplicates().itertuples(index=False, name=None))
    anu_periodos = [(int(a), int(q)) for a, q in anu_periodos if a > 0]

    todos_periodos = sorted(set(tri_periodos) | set(anu_periodos))

    if not todos_periodos:
        df_vazio = pd.DataFrame({"cd_conta_padrao": contas, "ds_conta_padrao": [nomes[c] for c in contas]})
        if retornar_resultado_completo:
            return PadronizacaoResult(df=df_vazio, aprovado_geral=True, alertas=["Sem períodos"], padrao_detectado=padrao)
        return df_vazio

    cols_mi = pd.MultiIndex.from_tuples(todos_periodos, names=["ano", "q"])
    mat = pd.DataFrame(index=contas, columns=cols_mi, dtype="float64")

    def _valor_conta(df_periodo: pd.DataFrame, codigo: str) -> float:
        exact = df_periodo[df_periodo["cd_conta"] == codigo]
        if not exact.empty:
            s = exact["valor"].dropna()
            return float(s.iloc[-1]) if not s.empty else np.nan
        desc = df_periodo[df_periodo["cd_conta"].str.startswith(codigo + ".")]
        if not desc.empty:
            return float(desc["valor"].sum(skipna=True))
        return np.nan

    def _valor_eps(df_periodo: pd.DataFrame) -> float:
        eps = df_periodo[df_periodo["cd_conta"].str.startswith("3.99")].copy()
        if eps.empty:
            return np.nan
        eps = eps.dropna(subset=["valor"])
        if eps.empty:
            return np.nan

        for prefer in ["3.99.01.01", "3.99.01.02", "3.99"]:
            hit = eps[eps["cd_conta"] == prefer]
            if not hit.empty:
                val = float(hit["valor"].iloc[-1])
                if abs(val) <= 1000:
                    return val

        for _, row in eps.iterrows():
            val = row["valor"]
            if not pd.isna(val) and abs(val) <= 1000:
                return float(val)

        return np.nan

    seguros_map = {
        "BBSE3": {"3.05": "3.07", "3.06": "3.08", "3.07": "3.06", "3.08": "3.09"},
        "CXSE3": {"3.05": "3.05", "3.06": "3.06", "3.07": "3.07", "3.08": "3.08"},
        "IRBR3": {"3.05": "3.07", "3.06": "3.08", "3.07": "3.06", "3.08": "3.09"},
        "PSSA3": {"3.05": "3.05", "3.06": "3.06", "3.07": "3.07", "3.08": "3.07"},
    }.get(ticker_norm, {}) if modo_seguros else {}

    bancos_map = {
        "3.01": "3.01", "3.02": "3.02", "3.03": "3.03", "3.04": "3.04",
        "3.05": "3.07", "3.06": "3.08", "3.07": "3.09", "3.08": "3.10",
        "3.09": "3.11", "3.99": "3.99", "3.99.01.01": "3.99.01.01",
        "3.99.01.02": "3.99.01.02",
    } if modo_bancos else {}

    def _map_codigo(cod: str) -> str:
        if modo_seguros and cod in seguros_map:
            return seguros_map[cod]
        if modo_bancos and cod in bancos_map:
            return bancos_map[cod]
        return cod

    # PASSO 1: Preencher ITRs na matriz
    for (ano, q) in tri_periodos:
        df_periodo = tri[(tri["ano"] == ano) & (tri["q"] == q)]
        if df_periodo.empty:
            continue
        for cod in contas:
            if str(cod).startswith("3.99"):
                mat.at[cod, (ano, q)] = _valor_eps(df_periodo)
            else:
                mat.at[cod, (ano, q)] = _valor_conta(df_periodo, _map_codigo(cod))

    # PASSO 2: Processar DFP e isolar valores (ORDEM CORRETA)
    for (ano_dfp, q_dfp) in anu_periodos:
        df_dfp = anu[(anu["ano"] == ano_dfp) & (anu["q"] == q_dfp)]
        if df_dfp.empty:
            continue

        itrs_ano = sorted([(a, q) for (a, q) in tri_periodos if a == ano_dfp], key=lambda x: x[1])

        # Decisão por ANO (não global)
        padrao_ano = padrao_por_ano.get(int(ano_dfp), {}).get("padrao", padrao)

        if padrao_ano == "isolado":
            # Verificação solicitada: confirmar (com tolerância) se os trimestres já estão ISOLADOS
            # comparando a SOMA dos trimestres disponíveis vs o ANUAL, para TODAS as contas padronizadas
            # (exceto LPA 3.99*). Se bater para todas → manter como está e IGNORAR DFP.
            def _itrs_isolados_batem_com_anual_para_todas_contas() -> bool:
                contas_testaveis = [c for c in contas if not str(c).startswith("3.99")]
                total_comparadas = 0

                for cod_chk in contas_testaveis:
                    v_anual_chk = _valor_conta(df_dfp, _map_codigo(cod_chk))
                    if pd.isna(v_anual_chk):
                        continue

                    soma_itrs = 0.0
                    count_itrs = 0

                    for (a_itr, q_itr) in itrs_ano:
                        if (a_itr, q_itr) in mat.columns:
                            v = mat.at[cod_chk, (a_itr, q_itr)]
                            if pd.isna(v):
                                return False
                            soma_itrs += float(v)
                            count_itrs += 1

                    if count_itrs == 0:
                        return False

                    diff = abs(soma_itrs - float(v_anual_chk))
                    diff_pct = (diff / abs(v_anual_chk) * 100.0) if v_anual_chk != 0 else 0.0
                    ok = (diff_pct <= tol_pct) or (diff <= tol_abs)

                    if not ok:
                        return False

                    total_comparadas += 1

                return total_comparadas > 0

            if _itrs_isolados_batem_com_anual_para_todas_contas():
                alertas.append(f"Ano {ano_dfp}: ITRs isolados verificados em TODAS as contas, DFP ignorado")
                continue

            # Se não confirmou isolado para todas as contas, usar DFP apenas para completar trimestre faltante
            for cod in contas:
                if str(cod).startswith("3.99"):
                    mat.at[cod, (ano_dfp, q_dfp)] = _valor_eps(df_dfp)
                    continue

                v_anual = _valor_conta(df_dfp, _map_codigo(cod))
                if pd.isna(v_anual):
                    continue

                if (ano_dfp, q_dfp) in mat.columns and not pd.isna(mat.at[cod, (ano_dfp, q_dfp)]):
                    continue

                soma_outros = 0.0
                tem_outros = False
                for (a_itr, q_itr) in itrs_ano:
                    if (a_itr, q_itr) != (ano_dfp, q_dfp) and (a_itr, q_itr) in mat.columns:
                        v = mat.at[cod, (a_itr, q_itr)]
                        if not pd.isna(v):
                            soma_outros += v
                            tem_outros = True

                mat.at[cod, (ano_dfp, q_dfp)] = (v_anual - soma_outros) if tem_outros else v_anual

        else:
            # PADRÃO YTD: usa apenas T1,T2,T3 e calcula T4 = Anual - T3_YTD
            itrs_ytd = [(a, q) for (a, q) in itrs_ano if q in (1, 2, 3)]
            qs_ytd = sorted([q for (_a, q) in itrs_ytd])

            if qs_ytd != [1, 2, 3]:
                alertas.append(f"Ano {ano_dfp}: esperado T1,T2,T3 para YTD, mas veio {qs_ytd}. Tratando como ISOLADO.")
                for cod in contas:
                    if str(cod).startswith("3.99"):
                        mat.at[cod, (ano_dfp, q_dfp)] = _valor_eps(df_dfp)
                        continue

                    v_anual = _valor_conta(df_dfp, _map_codigo(cod))
                    if pd.isna(v_anual):
                        continue

                    if (ano_dfp, q_dfp) in mat.columns and not pd.isna(mat.at[cod, (ano_dfp, q_dfp)]):
                        continue

                    soma_outros = 0.0
                    tem_outros = False
                    for (a_itr, q_itr) in itrs_ano:
                        if (a_itr, q_itr) != (ano_dfp, q_dfp) and (a_itr, q_itr) in mat.columns:
                            v = mat.at[cod, (a_itr, q_itr)]
                            if not pd.isna(v):
                                soma_outros += v
                                tem_outros = True

                    mat.at[cod, (ano_dfp, q_dfp)] = (v_anual - soma_outros) if tem_outros else v_anual

            else:
                for cod in contas:
                    if str(cod).startswith("3.99"):
                        mat.at[cod, (ano_dfp, q_dfp)] = _valor_eps(df_dfp)
                        continue

                    v_anual = _valor_conta(df_dfp, _map_codigo(cod))
                    if pd.isna(v_anual):
                        continue

                    v_t3_ytd = mat.at[cod, (ano_dfp, 3)] if (ano_dfp, 3) in mat.columns else np.nan
                    mat.at[cod, (ano_dfp, q_dfp)] = (v_anual - v_t3_ytd) if not pd.isna(v_t3_ytd) else v_anual

                itrs_ordenados = [(ano_dfp, 1), (ano_dfp, 2), (ano_dfp, 3)]
                for i in range(len(itrs_ordenados) - 1, 0, -1):
                    (a_curr, q_curr) = itrs_ordenados[i]
                    (a_prev, q_prev) = itrs_ordenados[i - 1]
                    if (a_curr, q_curr) not in mat.columns or (a_prev, q_prev) not in mat.columns:
                        continue

                    for cod in contas:
                        if str(cod).startswith("3.99"):
                            continue
                        v_curr = mat.at[cod, (a_curr, q_curr)]
                        v_prev = mat.at[cod, (a_prev, q_prev)]
                        if not pd.isna(v_curr) and not pd.isna(v_prev):
                            mat.at[cod, (a_curr, q_curr)] = v_curr - v_prev

    # Preencher derivadas
    if preencher_derivadas:
        for (ano, q) in todos_periodos:
            if "3.03" in contas and "3.01" in contas and "3.02" in contas:
                if pd.isna(mat.at["3.03", (ano, q)]):
                    v1 = mat.at["3.01", (ano, q)]
                    v2 = mat.at["3.02", (ano, q)]
                    if not (pd.isna(v1) or pd.isna(v2)):
                        mat.at["3.03", (ano, q)] = v1 + v2

    # CHECK-UP
    checkup_results = []
    aprovado_geral = True

    if realizar_checkup:
        # Validação 1: Receita não pode ser negativa
        cod_receita = "3.01"
        for (ano, q) in todos_periodos:
            if (ano, q) in mat.columns:
                v_receita = mat.at[cod_receita, (ano, q)]
                if not pd.isna(v_receita) and v_receita < 0:
                    aprovado_geral = False
                    alertas.append(f"⚠️ RECEITA NEGATIVA em {ano}-T{q}: {v_receita:.0f}")

        # Validação 2 (corrigida): soma dos trimestres (T1..T4 disponíveis) deve bater com o anual (para todas as contas)
        for (ano_dfp, q_dfp) in anu_periodos:
            df_dfp = anu[(anu["ano"] == ano_dfp) & (anu["q"] == q_dfp)]
            if df_dfp.empty:
                continue

            # Encontrar os trimestres do ano (apenas T1..T4). NÃO incluir "anual" como período na soma.
            trimestres_ano = [(ano_dfp, q) for q in (1, 2, 3, 4) if (ano_dfp, q) in mat.columns]

            for cod in contas:
                if str(cod).startswith("3.99"):
                    continue

                soma = 0.0
                count = 0
                inconclusivo = False
                for (_a, q) in trimestres_ano:
                    v = mat.at[cod, (ano_dfp, q)]
                    if pd.isna(v):
                        inconclusivo = True
                        continue
                    soma += float(v)
                    count += 1

                v_anual = _valor_conta(df_dfp, _map_codigo(cod))
                if pd.isna(v_anual) or count == 0:
                    continue

                if inconclusivo:
                    aprovado_geral = False
                    checkup_results.append(CheckupResult(
                        ano=ano_dfp, trimestre=q_dfp, cd_conta=cod, ds_conta=nomes.get(cod, ""),
                        soma_trimestres=float(soma), valor_anual=float(v_anual),
                        diferenca=float("nan"), diferenca_pct=float("nan"),
                        aprovado=False,
                        observacao=f"Inconclusivo: conta ausente em algum trimestre do ano (T1..T4 disponíveis: {[q for (_a,q) in trimestres_ano]})"
                    ))
                    continue

                diff = abs(soma - v_anual)
                diff_pct = (diff / abs(v_anual) * 100) if v_anual != 0 else 0
                ok = diff_pct <= tol_pct or diff <= tol_abs

                if not ok:
                    aprovado_geral = False

                checkup_results.append(CheckupResult(
                    ano=ano_dfp, trimestre=q_dfp, cd_conta=cod, ds_conta=nomes.get(cod, ""),
                    soma_trimestres=float(soma), valor_anual=float(v_anual),
                    diferenca=float(diff), diferenca_pct=float(diff_pct), aprovado=bool(ok),
                    observacao=f"Trimestres usados na soma: {[q for (_a, q) in trimestres_ano if not pd.isna(mat.at[cod, (ano_dfp, q)])]}"
                ))

    # Montar saída
    out = pd.DataFrame({
        "cd_conta_padrao": contas,
        "ds_conta_padrao": [nomes[c] for c in contas]
    })

    for (ano, q) in todos_periodos:
        out[f"{ano}-T{q}"] = mat[(ano, q)].values

    if retornar_resultado_completo:
        return PadronizacaoResult(
            df=out,
            checkup_results=checkup_results,
            mes_encerramento_fiscal=mes_encerramento,
            aprovado_geral=aprovado_geral,
            alertas=alertas,
            padrao_detectado=padrao
        )

    return out
