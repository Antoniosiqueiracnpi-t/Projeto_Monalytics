"""
PADRONIZAÇÃO DRE - VERSÃO CORRIGIDA V2
=======================================
Correções implementadas:
1. Detecta padrão dos dados (YTD vs Isolado) automaticamente
2. NÃO cria trimestres fantasmas
3. Check-up rigoroso com validação de receitas negativas
4. Suporta anos fiscais diferentes de dezembro

LÓGICA:
- YTD (padrão): ITR com T1,T2,T3 acumulados → isola T4 = DFP - soma(ITRs)
- ISOLADO: Trimestres já vêm isolados → mantém como estão
"""

import pandas as pd
import numpy as np
from functools import lru_cache
from typing import Optional, Dict, Tuple, List, Any
from dataclasses import dataclass, field


# ==================== ESTRUTURAS DE DADOS ====================

@dataclass
class CheckupResult:
    """Resultado do check-up de uma conta"""
    ano: int
    trimestre: int
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
    padrao_detectado: str = "ytd"  # "ytd" ou "isolado"


# ==================== DRE PADRÕES POR SETOR ====================

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

TOLERANCIA_CHECKUP_PCT = 1.0
TOLERANCIA_CHECKUP_ABS = 1.0


# ==================== FUNÇÕES AUXILIARES ====================

def _norm_ticker(t: Optional[str]) -> Optional[str]:
    if t is None:
        return None
    t = str(t).upper().strip()
    return t.replace(".SA", "")


def _infer_ticker_from_paths(*paths: str) -> Optional[str]:
    joined = " ".join([str(p).upper() for p in paths if p is not None])
    for tk in _SEGUROS_TICKERS:
        if tk in joined:
            return tk
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


def _mes_para_trimestre(mes: int) -> int:
    """Converte mês (1-12) para trimestre (1-4)"""
    return ((mes - 1) // 3) + 1


def _detectar_mes_encerramento_fiscal(df_anual: pd.DataFrame) -> int:
    """Detecta mês de encerramento do ano fiscal pelo DFP"""
    if df_anual.empty or "data_fim" not in df_anual.columns:
        return 12
    datas = pd.to_datetime(df_anual["data_fim"], errors="coerce")
    meses = datas.dt.month.dropna()
    if meses.empty:
        return 12
    return int(meses.mode().iloc[0]) if not meses.mode().empty else 12


def _detectar_padrao_trimestral(
    tri: pd.DataFrame, 
    anu: pd.DataFrame,
    mes_encerramento: int
) -> str:
    """
    Detecta se os dados estão em formato YTD (acumulado) ou Isolado (trimestral).
    
    Padrão YTD: T1, T2, T3 acumulados → precisa isolar T4
    Padrão Isolado: Trimestres já vêm isolados → mantém como está
    
    Retorna: "ytd" ou "isolado"
    """
    if tri.empty and anu.empty:
        return "ytd"  # default seguro
    
    # Preparar dados para análise
    for df in (tri, anu):
        if not df.empty and "ano" not in df.columns:
            df["ano"] = pd.to_datetime(df["data_fim"], errors="coerce").dt.year
            df["mes"] = pd.to_datetime(df["data_fim"], errors="coerce").dt.month
    
    if tri.empty:
        return "isolado"  # sem ITR, assume que anual virá isolado
    
    # Agrupar ITRs por ano
    anos = sorted(tri["ano"].dropna().unique())
    
    evidencias_ytd = 0
    evidencias_isolado = 0
    
    for ano in anos[-3:]:  # analisa últimos 3 anos disponíveis
        itrs_ano = tri[tri["ano"] == ano].copy()
        
        if itrs_ano.empty:
            continue
        
        # Contar quantos trimestres únicos existem
        trimestres = sorted(itrs_ano["trimestre"].str.replace("T", "").astype(int).unique())
        
        # Se não tem exatamente [1,2,3] → forte evidência de isolado
        if trimestres != [1, 2, 3]:
            evidencias_isolado += 2  # peso maior
        else:
            evidencias_ytd += 1
        
        # Teste quantitativo: valores devem ser crescentes em YTD
        try:
            # Pegar conta de Receita (3.01) para teste
            rec = itrs_ano[itrs_ano["cd_conta"].str.startswith("3.01")].copy()
            if not rec.empty:
                rec["q"] = rec["trimestre"].str.replace("T", "").astype(int)
                rec["valor_mil"] = pd.to_numeric(rec["valor_mil"], errors="coerce")
                
                # Agrupar por trimestre e pegar valor médio (caso tenha múltiplas linhas)
                valores = rec.groupby("q")["valor_mil"].sum().to_dict()
                
                # YTD: T2 > T1 e T3 > T2 (crescente)
                if 1 in valores and 2 in valores and 3 in valores:
                    v1, v2, v3 = valores[1], valores[2], valores[3]
                    # Se valores são positivos e crescentes → YTD
                    if v1 > 0 and v2 > v1 and v3 > v2:
                        evidencias_ytd += 2  # peso maior
                    # Se T2 < T1 ou T3 < T2 → provavelmente isolado
                    elif v2 < v1 or v3 < v2:
                        evidencias_isolado += 2
        except Exception:
            pass
    
    # Decisão final
    if evidencias_isolado > evidencias_ytd:
        return "isolado"
    else:
        return "ytd"


# ==================== FUNÇÃO PRINCIPAL ====================

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
    2. YTD: isola T4 = DFP - soma(ITRs)
    3. Isolado: mantém trimestres como estão
    4. Check-up rigoroso com validação
    """
    
    alertas = []
    
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
    
    # **NOVIDADE:** Detectar padrão dos dados
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

    # Listar períodos únicos disponíveis (SEM CRIAR FANTASMAS)
    tri_periodos = list(tri[["ano", "q"]].drop_duplicates().itertuples(index=False, name=None))
    tri_periodos = [(int(a), int(q)) for a, q in tri_periodos if a > 0]
    
    anu_periodos = list(anu[["ano", "q"]].drop_duplicates().itertuples(index=False, name=None))
    anu_periodos = [(int(a), int(q)) for a, q in anu_periodos if a > 0]

    # Todos os períodos disponíveis
    todos_periodos = sorted(set(tri_periodos) | set(anu_periodos))

    if not todos_periodos:
        df_vazio = pd.DataFrame({"cd_conta_padrao": contas, "ds_conta_padrao": [nomes[c] for c in contas]})
        if retornar_resultado_completo:
            return PadronizacaoResult(df=df_vazio, aprovado_geral=True, alertas=["Sem períodos"], padrao_detectado=padrao)
        return df_vazio

    # Criar matriz
    cols_mi = pd.MultiIndex.from_tuples(todos_periodos, names=["ano", "q"])
    mat = pd.DataFrame(index=contas, columns=cols_mi, dtype="float64")

    # Funções auxiliares
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
        """Extrai LPA validando valores razoáveis"""
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

    # Mapeamentos por setor
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

    # **PASSO 1:** Preencher matriz com valores dos ITRs (YTD ou isolados, como vieram)
    for (ano, q) in tri_periodos:
        df_periodo = tri[(tri["ano"] == ano) & (tri["q"] == q)]
        if df_periodo.empty:
            continue
        for cod in contas:
            if cod.startswith("3.99"):
                mat.at[cod, (ano, q)] = _valor_eps(df_periodo)
            else:
                mat.at[cod, (ano, q)] = _valor_conta(df_periodo, _map_codigo(cod))

    # **PASSO 2:** Processar DFP e isolar valores (ORDEM CORRETA)
    for (ano_dfp, q_dfp) in anu_periodos:
        df_dfp = anu[(anu["ano"] == ano_dfp) & (anu["q"] == q_dfp)]
        if df_dfp.empty:
            continue
        
        # Encontrar ITRs do mesmo ano
        itrs_ano = sorted([(a, q) for (a, q) in tri_periodos if a == ano_dfp], key=lambda x: x[1])
        
        if padrao == "isolado":
            # **PADRÃO ISOLADO:** Verificar se ITRs já somam para o anual
            # Se sim: ITRs já estão corretos, IGNORAR DFP
            
            # Testar com Receita (3.01) - conta independente
            cod_teste = "3.01"
            v_anual_teste = _valor_conta(df_dfp, _map_codigo(cod_teste))
            
            if not pd.isna(v_anual_teste):
                # Somar ITRs do ano para esta conta
                soma_itrs_teste = 0.0
                count_itrs = 0
                for (a_itr, q_itr) in itrs_ano:
                    if (a_itr, q_itr) in mat.columns:
                        v = mat.at[cod_teste, (a_itr, q_itr)]
                        if not pd.isna(v):
                            soma_itrs_teste += v
                            count_itrs += 1
                
                # Verificar se ITRs já somam para o anual (tolerância)
                if count_itrs > 0:
                    diff = abs(soma_itrs_teste - v_anual_teste)
                    diff_pct = (diff / abs(v_anual_teste) * 100) if v_anual_teste != 0 else 0
                    
                    if diff_pct <= TOLERANCIA_CHECKUP_PCT or diff <= TOLERANCIA_CHECKUP_ABS:
                        # ITRs já isolados e corretos → IGNORAR DFP
                        alertas.append(f"Ano {ano_dfp}: ITRs isolados verificados, DFP ignorado")
                        continue
            
            # ITRs não batem: processar DFP para calcular trimestre faltante
            # CADA CONTA É INDEPENDENTE
            for cod in contas:
                if cod.startswith("3.99"):
                    mat.at[cod, (ano_dfp, q_dfp)] = _valor_eps(df_dfp)
                    continue
                
                v_anual = _valor_conta(df_dfp, _map_codigo(cod))
                if pd.isna(v_anual):
                    continue
                
                # Se já tem valor de ITR, não sobrescrever
                if (ano_dfp, q_dfp) in mat.columns and not pd.isna(mat.at[cod, (ano_dfp, q_dfp)]):
                    continue
                
                # Calcular trimestre faltante desta conta
                soma_outros = 0.0
                tem_outros = False
                for (a_itr, q_itr) in itrs_ano:
                    if (a_itr, q_itr) != (ano_dfp, q_dfp) and (a_itr, q_itr) in mat.columns:
                        v = mat.at[cod, (a_itr, q_itr)]
                        if not pd.isna(v):
                            soma_outros += v
                            tem_outros = True
                
                if tem_outros:
                    mat.at[cod, (ano_dfp, q_dfp)] = v_anual - soma_outros
                else:
                    mat.at[cod, (ano_dfp, q_dfp)] = v_anual
        
        else:
            # **PADRÃO YTD:** Processar CADA CONTA independentemente
            # ORDEM: 1) Calcular T4, 2) Isolar T1,T2,T3
            
            for cod in contas:
                if cod.startswith("3.99"):
                    mat.at[cod, (ano_dfp, q_dfp)] = _valor_eps(df_dfp)
                    continue
                
                # PASSO 2.1: Calcular T4 = Anual - T3_ytd (valor ORIGINAL)
                v_anual = _valor_conta(df_dfp, _map_codigo(cod))
                if pd.isna(v_anual):
                    continue
                
                # Encontrar último ITR (T3) - ainda tem valor YTD original
                ultimo_itr = max(itrs_ano, key=lambda x: x[1]) if itrs_ano else None
                
                if ultimo_itr and ultimo_itr in mat.columns:
                    v_ultimo_ytd = mat.at[cod, ultimo_itr]
                    if not pd.isna(v_ultimo_ytd):
                        # T4_isolado = Anual - T3_ytd
                        mat.at[cod, (ano_dfp, q_dfp)] = v_anual - v_ultimo_ytd
                    else:
                        mat.at[cod, (ano_dfp, q_dfp)] = v_anual
                else:
                    mat.at[cod, (ano_dfp, q_dfp)] = v_anual
                
                # PASSO 2.2: Agora isolar T1, T2, T3 retroativamente
                # T3 = T3_ytd - T2_ytd, T2 = T2_ytd - T1_ytd
                itrs_ordenados = sorted(itrs_ano, key=lambda x: x[1])
                
                for i in range(len(itrs_ordenados) - 1, 0, -1):
                    (a_curr, q_curr) = itrs_ordenados[i]
                    (a_prev, q_prev) = itrs_ordenados[i-1]
                    
                    if (a_curr, q_curr) not in mat.columns or (a_prev, q_prev) not in mat.columns:
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

    # **CHECK-UP RIGOROSO**
    checkup_results = []
    aprovado_geral = True
    
    if realizar_checkup:
        # **VALIDAÇÃO 1: Receita não pode ser negativa em nenhum trimestre**
        cod_receita = "3.01"
        for (ano, q) in todos_periodos:
            if (ano, q) in mat.columns:
                v_receita = mat.at[cod_receita, (ano, q)]
                if not pd.isna(v_receita) and v_receita < 0:
                    aprovado_geral = False
                    alertas.append(f"⚠️ RECEITA NEGATIVA em {ano}-T{q}: {v_receita:.0f}")
        
        # **VALIDAÇÃO 2: Soma dos trimestres deve bater com anual**
        for (ano_dfp, q_dfp) in anu_periodos:
            df_dfp = anu[(anu["ano"] == ano_dfp) & (anu["q"] == q_dfp)]
            if df_dfp.empty:
                continue
            
            # Encontrar todos os trimestres deste ano (incluindo DFP)
            trimestres_ano = [(a, q) for (a, q) in todos_periodos if a == ano_dfp]
            
            for cod in contas:
                if cod.startswith("3.99"):
                    continue
                
                # Soma dos trimestres isolados
                soma = 0.0
                count = 0
                for (a, q) in trimestres_ano:
                    if (a, q) in mat.columns:
                        v = mat.at[cod, (a, q)]
                        if not pd.isna(v):
                            soma += v
                            count += 1
                
                # Valor anual original
                v_anual = _valor_conta(df_dfp, _map_codigo(cod))
                if pd.isna(v_anual) or count == 0:
                    continue
                
                diff = abs(soma - v_anual)
                diff_pct = (diff / abs(v_anual) * 100) if v_anual != 0 else 0
                ok = diff_pct <= TOLERANCIA_CHECKUP_PCT or diff <= TOLERANCIA_CHECKUP_ABS
                
                if not ok:
                    aprovado_geral = False
                
                checkup_results.append(CheckupResult(
                    ano=ano_dfp, trimestre=q_dfp, cd_conta=cod, ds_conta=nomes.get(cod, ""),
                    soma_trimestres=soma, valor_anual=v_anual,
                    diferenca=diff, diferenca_pct=diff_pct, aprovado=ok
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


def gerar_relatorio_checkup(resultado: PadronizacaoResult) -> str:
    """Gera relatório de check-up"""
    linhas = ["=" * 60, "RELATÓRIO DE CHECK-UP - DRE", "=" * 60, ""]
    linhas.append(f"Mês encerramento fiscal: {resultado.mes_encerramento_fiscal}")
    linhas.append(f"Padrão detectado: {resultado.padrao_detectado.upper()}")
    linhas.append(f"Status: {'✅ APROVADO' if resultado.aprovado_geral else '❌ REPROVADO'}")
    
    if resultado.alertas:
        linhas.append("\nALERTAS:")
        for a in resultado.alertas:
            linhas.append(f"  ⚠️ {a}")
    
    falhas = [r for r in resultado.checkup_results if not r.aprovado]
    if falhas:
        linhas.append(f"\nFALHAS ({len(falhas)}):")
        for r in falhas[:10]:
            linhas.append(f"  {r.ano}-T{r.trimestre} {r.cd_conta}: Soma={r.soma_trimestres:,.0f} vs Anual={r.valor_anual:,.0f} ({r.diferenca_pct:.1f}%)")
    
    return "\n".join(linhas)


def padronizar_dre(*args, **kwargs):
    """Alias para compatibilidade"""
    return padronizar_dre_trimestral_e_anual(*args, **kwargs)
