"""
PADRONIZAÇÃO DRE - VERSÃO V4 DEFINITIVA
========================================
APENAS DRE - NÃO PROCESSA BPA/BPP/DFC

Regras:
1. PADRÃO CVM: ITRs com T1, T2, T3 acumulados (YTD) → T4 = DFP - T3_ytd
2. PADRÃO ALTERNATIVO (ex: AGRO3): ITRs isolados → soma deve bater com anual
3. DETECÇÃO AUTOMÁTICA: Testa soma dos ITRs contra o anual para decidir
4. CHECK-UP RIGOROSO: Receita NUNCA negativa, soma trimestres = anual
5. INDEPENDENTE: Não chama nenhuma outra função de normalização
"""

import pandas as pd
import numpy as np
from functools import lru_cache
from typing import Optional, Tuple, List
from dataclasses import dataclass, field


# ==================== ESTRUTURAS DE DADOS ====================

@dataclass
class CheckupResult:
    """Resultado do check-up de uma conta"""
    ano: int
    cd_conta: str
    ds_conta: str
    soma_trimestres: float
    valor_anual: float
    diferenca: float
    diferenca_pct: float
    aprovado: bool
    observacao: str = ""


@dataclass
class PadronizacaoResult:
    """Resultado completo da padronização"""
    df: pd.DataFrame
    checkup_results: List[CheckupResult] = field(default_factory=list)
    mes_encerramento_fiscal: int = 12
    aprovado_geral: bool = True
    alertas: List[str] = field(default_factory=list)
    padrao_detectado: str = "ytd"


# ==================== PLANOS DE CONTAS DRE ====================

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

TOLERANCIA_PCT = 1.0
TOLERANCIA_ABS = 1.0


# ==================== FUNÇÕES AUXILIARES ====================

def _norm_ticker(t: Optional[str]) -> Optional[str]:
    if t is None:
        return None
    return str(t).upper().strip().replace(".SA", "")


@lru_cache(maxsize=8)
def _load_b3_mapping(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, sep=";", encoding="utf-8")
    df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()
    return df


def _get_setor(ticker: Optional[str], b3_csv: Optional[str]) -> Optional[str]:
    if not ticker or not b3_csv:
        return None
    try:
        df = _load_b3_mapping(b3_csv)
        hit = df.loc[df["ticker"] == ticker, "setor"]
        return str(hit.iloc[0]) if not hit.empty else None
    except Exception:
        return None


def _valor_conta(df: pd.DataFrame, cod: str) -> float:
    """Extrai valor de uma conta - exato ou soma de descendentes"""
    exact = df[df["cd_conta"] == cod]
    if not exact.empty:
        v = exact["valor"].dropna()
        return float(v.iloc[-1]) if not v.empty else np.nan
    
    # Tenta soma de descendentes
    desc = df[df["cd_conta"].str.startswith(cod + ".")]
    if not desc.empty:
        return float(desc["valor"].sum(skipna=True))
    
    return np.nan


def _valor_lpa(df: pd.DataFrame) -> float:
    """Extrai LPA com validação"""
    eps = df[df["cd_conta"].str.startswith("3.99")].copy()
    if eps.empty:
        return np.nan
    
    eps = eps.dropna(subset=["valor"])
    for pref in ["3.99.01.01", "3.99.01.02", "3.99"]:
        hit = eps[eps["cd_conta"] == pref]
        if not hit.empty:
            val = float(hit["valor"].iloc[-1])
            if abs(val) <= 1000:
                return val
    return np.nan


# ==================== FUNÇÃO PRINCIPAL ====================

def padronizar_dre_trimestral_e_anual(
    dre_trimestral_csv: str,
    dre_anual_csv: str,
    *,
    unidade: str = "mil",
    ticker: Optional[str] = None,
    b3_mapping_csv: Optional[str] = None,
    realizar_checkup: bool = True,
    retornar_resultado_completo: bool = False,
) -> pd.DataFrame:
    """
    Padroniza DRE trimestral e anual.
    
    APENAS DRE - NÃO PROCESSA BPA/BPP/DFC
    
    Args:
        dre_trimestral_csv: Caminho do CSV trimestral (ITR)
        dre_anual_csv: Caminho do CSV anual (DFP)
        unidade: 'mil', 'unidade' ou 'milhao'
        ticker: Código do ativo (ex: 'PETR4')
        b3_mapping_csv: Mapeamento de setores B3
        realizar_checkup: Validar soma dos trimestres
        retornar_resultado_completo: Retorna PadronizacaoResult com detalhes
    
    Returns:
        DataFrame padronizado ou PadronizacaoResult
    """
    alertas = []
    
    # === IDENTIFICAR SETOR ===
    ticker_norm = _norm_ticker(ticker)
    setor = _get_setor(ticker_norm, b3_mapping_csv)
    setor_l = (setor or "").lower()
    
    modo_seguros = ticker_norm in _SEGUROS_TICKERS or "seguros" in setor_l
    modo_bancos = ticker_norm in _BANCOS_TICKERS or setor_l == "bancos"
    
    if modo_seguros:
        plano = DRE_SEGUROS_PADRAO
    elif modo_bancos:
        plano = DRE_BANCOS_PADRAO
    else:
        plano = DRE_PADRAO
    
    contas = [c for c, _ in plano]
    nomes = {c: n for c, n in plano}
    
    # === CARREGAR DADOS ===
    tri = pd.read_csv(dre_trimestral_csv)
    anu = pd.read_csv(dre_anual_csv)
    
    cols_req = {"data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"}
    for nome, df in [("trimestral", tri), ("anual", anu)]:
        if not cols_req.issubset(df.columns):
            raise ValueError(f"Arquivo {nome} sem colunas: {cols_req - set(df.columns)}")
    
    # === NORMALIZAR ===
    for df in (tri, anu):
        df["data_fim"] = pd.to_datetime(df["data_fim"], errors="coerce")
        df["cd_conta"] = df["cd_conta"].astype(str).str.strip()
        df["ds_conta"] = df["ds_conta"].astype(str)
        df["valor_mil"] = pd.to_numeric(df["valor_mil"], errors="coerce")
    
    fator = {"mil": 1.0, "unidade": 1000.0, "milhao": 0.001}.get(unidade, 1.0)
    tri["valor"] = tri["valor_mil"] * fator
    anu["valor"] = anu["valor_mil"] * fator
    
    tri["ano"] = tri["data_fim"].dt.year.astype("Int64")
    tri["q"] = tri["trimestre"].str.replace("T", "").astype(int)
    
    anu["ano"] = anu["data_fim"].dt.year.astype("Int64")
    anu["q"] = 4  # DFP sempre é T4
    
    # === MAPEAMENTO DE CÓDIGOS POR SETOR ===
    mapa_cod = {}
    if modo_seguros:
        mapa_cod = {
            "BBSE3": {"3.05": "3.07", "3.06": "3.08", "3.07": "3.06", "3.08": "3.09"},
            "CXSE3": {},
            "IRBR3": {"3.05": "3.07", "3.06": "3.08", "3.07": "3.06", "3.08": "3.09"},
            "PSSA3": {},
        }.get(ticker_norm, {})
    elif modo_bancos:
        mapa_cod = {
            "3.05": "3.07", "3.06": "3.08", "3.07": "3.09", "3.08": "3.10", "3.09": "3.11"
        }
    
    def map_cod(cod: str) -> str:
        return mapa_cod.get(cod, cod)
    
    # === IDENTIFICAR ANOS E TRIMESTRES DISPONÍVEIS ===
    anos = sorted(set(tri["ano"].dropna().unique()) | set(anu["ano"].dropna().unique()))
    
    if not anos:
        df_vazio = pd.DataFrame({"cd_conta_padrao": contas, "ds_conta_padrao": [nomes[c] for c in contas]})
        if retornar_resultado_completo:
            return PadronizacaoResult(df=df_vazio, alertas=["Sem dados"])
        return df_vazio
    
    # === DETECTAR PADRÃO POR ANO (YTD vs ISOLADO) ===
    padroes = {}
    
    for ano in anos:
        itrs = tri[tri["ano"] == ano]
        dfp = anu[anu["ano"] == ano]
        
        if itrs.empty:
            padroes[ano] = {"padrao": "sem_itr", "trimestres": [], "v_anual": np.nan}
            continue
        
        trimestres = sorted(itrs["q"].unique().tolist())
        
        # Obter valor anual da receita (3.01) para teste
        v_anual = _valor_conta(dfp, map_cod("3.01")) if not dfp.empty else np.nan
        
        if pd.isna(v_anual) or v_anual == 0:
            # Sem anual - heurística por trimestres
            padrao = "ytd" if trimestres == [1, 2, 3] else "isolado"
            padroes[ano] = {"padrao": padrao, "trimestres": trimestres, "v_anual": v_anual}
            continue
        
        # Coletar valores de receita por trimestre
        vals = {}
        for q in trimestres:
            df_q = itrs[itrs["q"] == q]
            vals[q] = _valor_conta(df_q, map_cod("3.01"))
        
        vals_ok = {k: v for k, v in vals.items() if not pd.isna(v)}
        
        if not vals_ok:
            padroes[ano] = {"padrao": "indeterminado", "trimestres": trimestres, "v_anual": v_anual}
            continue
        
        # TESTE: Soma dos ITRs disponíveis
        soma = sum(vals_ok.values())
        
        # Se soma ≈ anual (com 1 trimestre inferido) → ISOLADO
        faltantes = [q for q in [1, 2, 3, 4] if q not in trimestres]
        
        if len(faltantes) == 1:
            # Calcula o faltante
            v_faltante = v_anual - soma
            soma_total = v_anual  # soma + faltante = anual
        else:
            soma_total = soma
        
        diff_pct = abs(soma_total - v_anual) / abs(v_anual) * 100 if v_anual != 0 else 999
        
        # Se trimestres são [1,2,3] e T3 < anual → provavelmente YTD
        # Se soma ≈ anual → ISOLADO
        
        if diff_pct <= TOLERANCIA_PCT:
            padrao = "isolado"
        elif trimestres == [1, 2, 3]:
            v_t3 = vals_ok.get(3, np.nan)
            if not pd.isna(v_t3) and v_t3 < v_anual * 0.99:
                padrao = "ytd"
            else:
                padrao = "isolado"
        else:
            padrao = "isolado"
        
        padroes[ano] = {"padrao": padrao, "trimestres": trimestres, "v_anual": v_anual}
        alertas.append(f"Ano {ano}: {padrao.upper()}, trimestres {trimestres}")
    
    # Padrão predominante
    cnt = {"ytd": 0, "isolado": 0}
    for info in padroes.values():
        if info["padrao"] in cnt:
            cnt[info["padrao"]] += 1
    
    padrao_geral = "isolado" if cnt["isolado"] > cnt["ytd"] else "ytd"
    alertas.insert(0, f"Padrão predominante: {padrao_geral.upper()}")
    
    # === COLETAR PERÍODOS FINAIS ===
    periodos = set()
    
    for ano in anos:
        info = padroes.get(ano, {"trimestres": []})
        
        # Trimestres dos ITRs
        for q in info["trimestres"]:
            periodos.add((int(ano), q))
        
        # T4 do DFP
        if ano in anu["ano"].values:
            periodos.add((int(ano), 4))
    
    periodos = sorted(periodos)
    
    # === CRIAR MATRIZ DE RESULTADOS ===
    mat = pd.DataFrame(
        index=contas,
        columns=pd.MultiIndex.from_tuples(periodos, names=["ano", "q"]),
        dtype="float64"
    )
    
    # === PROCESSAR ANO POR ANO ===
    for ano in anos:
        info = padroes.get(ano, {"padrao": "ytd", "trimestres": []})
        padrao = info["padrao"]
        tris_exist = info["trimestres"]
        
        itrs = tri[tri["ano"] == ano]
        dfp = anu[anu["ano"] == ano]
        
        tem_dfp = not dfp.empty
        
        if padrao == "isolado" or padrao == "sem_itr":
            # ========== PADRÃO ISOLADO ==========
            # Manter valores como estão, calcular faltante
            
            for cod in contas:
                cod_map = map_cod(cod)
                is_lpa = cod.startswith("3.99")
                
                # Preencher ITRs existentes
                for q in tris_exist:
                    df_q = itrs[itrs["q"] == q]
                    if df_q.empty:
                        continue
                    
                    if (ano, q) in mat.columns:
                        mat.at[cod, (ano, q)] = _valor_lpa(df_q) if is_lpa else _valor_conta(df_q, cod_map)
                
                # Calcular trimestre faltante
                if tem_dfp and not is_lpa:
                    v_anual = _valor_conta(dfp, cod_map)
                    
                    if not pd.isna(v_anual):
                        # Somar existentes
                        soma = 0.0
                        for q in tris_exist:
                            if (ano, q) in mat.columns:
                                v = mat.at[cod, (ano, q)]
                                if not pd.isna(v):
                                    soma += v
                        
                        # Faltantes
                        faltantes = [q for q in [1, 2, 3, 4] if q not in tris_exist]
                        
                        if len(faltantes) == 1:
                            q_falt = faltantes[0]
                            if (ano, q_falt) in mat.columns:
                                mat.at[cod, (ano, q_falt)] = v_anual - soma
                
                # LPA do DFP
                if tem_dfp and is_lpa and (ano, 4) in mat.columns:
                    mat.at[cod, (ano, 4)] = _valor_lpa(dfp)
        
        else:
            # ========== PADRÃO YTD (ACUMULADO) ==========
            # ITRs são acumulados, isolar cada trimestre
            
            for cod in contas:
                cod_map = map_cod(cod)
                is_lpa = cod.startswith("3.99")
                
                # Coletar valores YTD brutos
                ytd_vals = {}
                for q in tris_exist:
                    df_q = itrs[itrs["q"] == q]
                    if df_q.empty:
                        continue
                    ytd_vals[q] = _valor_lpa(df_q) if is_lpa else _valor_conta(df_q, cod_map)
                
                # Calcular T4 ANTES de isolar (usa último YTD)
                if tem_dfp and not is_lpa:
                    v_anual = _valor_conta(dfp, cod_map)
                    
                    if not pd.isna(v_anual):
                        ultimo_q = max(tris_exist) if tris_exist else None
                        
                        if ultimo_q and ultimo_q in ytd_vals and not pd.isna(ytd_vals[ultimo_q]):
                            v_t4 = v_anual - ytd_vals[ultimo_q]
                            if (ano, 4) in mat.columns:
                                mat.at[cod, (ano, 4)] = v_t4
                        elif (ano, 4) in mat.columns:
                            mat.at[cod, (ano, 4)] = v_anual
                
                # LPA do DFP
                if tem_dfp and is_lpa and (ano, 4) in mat.columns:
                    mat.at[cod, (ano, 4)] = _valor_lpa(dfp)
                
                # Isolar trimestres (do maior para menor)
                if is_lpa:
                    # LPA não acumula
                    for q in tris_exist:
                        if (ano, q) in mat.columns:
                            mat.at[cod, (ano, q)] = ytd_vals.get(q, np.nan)
                else:
                    tris_ord = sorted(tris_exist)
                    
                    for i in range(len(tris_ord) - 1, -1, -1):
                        q_at = tris_ord[i]
                        v_at = ytd_vals.get(q_at, np.nan)
                        
                        if pd.isna(v_at):
                            continue
                        
                        if i == 0:
                            # T1 já é isolado
                            if (ano, q_at) in mat.columns:
                                mat.at[cod, (ano, q_at)] = v_at
                        else:
                            q_ant = tris_ord[i - 1]
                            v_ant = ytd_vals.get(q_ant, np.nan)
                            
                            if not pd.isna(v_ant):
                                if (ano, q_at) in mat.columns:
                                    mat.at[cod, (ano, q_at)] = v_at - v_ant
                            else:
                                if (ano, q_at) in mat.columns:
                                    mat.at[cod, (ano, q_at)] = v_at
    
    # === CHECK-UP RIGOROSO ===
    checkup_results = []
    aprovado_geral = True
    
    if realizar_checkup:
        # 1. Receita NUNCA negativa
        for (ano, q) in periodos:
            if (ano, q) not in mat.columns:
                continue
            v_rec = mat.at["3.01", (ano, q)]
            if not pd.isna(v_rec) and v_rec < 0:
                aprovado_geral = False
                alertas.append(f"❌ ERRO: Receita NEGATIVA {ano}-T{q}: {v_rec:,.0f}")
        
        # 2. Soma trimestres = anual (anos completos)
        for ano in anos:
            dfp = anu[anu["ano"] == ano]
            if dfp.empty:
                continue
            
            tris_ano = [(a, q) for (a, q) in periodos if a == ano]
            
            if len(tris_ano) < 4:
                alertas.append(f"Ano {ano}: {len(tris_ano)} trimestre(s) - validação parcial")
                continue
            
            for cod in contas:
                if cod.startswith("3.99"):
                    continue
                
                cod_map = map_cod(cod)
                
                soma = 0.0
                cnt = 0
                for (a, q) in tris_ano:
                    if (a, q) in mat.columns:
                        v = mat.at[cod, (a, q)]
                        if not pd.isna(v):
                            soma += v
                            cnt += 1
                
                v_anual = _valor_conta(dfp, cod_map)
                
                if pd.isna(v_anual) or cnt == 0:
                    continue
                
                diff = abs(soma - v_anual)
                diff_pct = diff / abs(v_anual) * 100 if v_anual != 0 else 0
                ok = diff_pct <= TOLERANCIA_PCT or diff <= TOLERANCIA_ABS
                
                if not ok:
                    aprovado_geral = False
                    if cod == "3.01":
                        alertas.append(f"❌ Receita {ano}: Soma={soma:,.0f} vs Anual={v_anual:,.0f} ({diff_pct:.1f}%)")
                    elif cod == "3.11":
                        alertas.append(f"❌ Lucro {ano}: Soma={soma:,.0f} vs Anual={v_anual:,.0f} ({diff_pct:.1f}%)")
                
                checkup_results.append(CheckupResult(
                    ano=ano, cd_conta=cod, ds_conta=nomes.get(cod, ""),
                    soma_trimestres=soma, valor_anual=v_anual,
                    diferenca=diff, diferenca_pct=diff_pct, aprovado=ok
                ))
    
    if aprovado_geral:
        alertas.append("✅ CHECK-UP APROVADO")
    else:
        alertas.append("❌ CHECK-UP REPROVADO")
    
    # === MONTAR SAÍDA ===
    out = pd.DataFrame({
        "cd_conta_padrao": contas,
        "ds_conta_padrao": [nomes[c] for c in contas]
    })
    
    for (ano, q) in periodos:
        if (ano, q) in mat.columns:
            out[f"{ano}-T{q}"] = mat[(ano, q)].values
    
    if retornar_resultado_completo:
        return PadronizacaoResult(
            df=out,
            checkup_results=checkup_results,
            aprovado_geral=aprovado_geral,
            alertas=alertas,
            padrao_detectado=padrao_geral
        )
    
    return out


def gerar_relatorio_checkup(resultado: PadronizacaoResult) -> str:
    """Gera relatório de check-up"""
    linhas = ["=" * 60, "RELATÓRIO CHECK-UP DRE", "=" * 60]
    linhas.append(f"Padrão: {resultado.padrao_detectado.upper()}")
    linhas.append(f"Status: {'✅ APROVADO' if resultado.aprovado_geral else '❌ REPROVADO'}")
    
    if resultado.alertas:
        linhas.append("\nALERTAS:")
        for a in resultado.alertas:
            linhas.append(f"  {a}")
    
    falhas = [r for r in resultado.checkup_results if not r.aprovado]
    if falhas:
        linhas.append(f"\nFALHAS ({len(falhas)}):")
        for r in falhas[:10]:
            linhas.append(f"  {r.ano} {r.cd_conta}: Soma={r.soma_trimestres:,.0f} vs Anual={r.valor_anual:,.0f}")
    
    return "\n".join(linhas)


# Alias para compatibilidade
def padronizar_dre(*args, **kwargs):
    return padronizar_dre_trimestral_e_anual(*args, **kwargs)
