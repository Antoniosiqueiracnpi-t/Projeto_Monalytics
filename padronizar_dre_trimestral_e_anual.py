"""
PADRONIZAÇÃO DRE - VERSÃO CORRIGIDA V3
=======================================
Correções implementadas:
1. Detecta padrão dos dados (YTD vs Isolado) automaticamente via teste de soma
2. NÃO cria trimestres fantasmas
3. Check-up rigoroso: receita NUNCA negativa, soma trimestres = anual
4. Suporta padrões alternativos (ex: AGRO3 com T1, T3, T4 isolados)
5. Independente - não chama outras funções de normalização

LÓGICA:
- Verifica quais trimestres existem nos ITRs
- Testa se soma dos ITRs + inferência de faltante ≈ anual
- YTD: T1,T2,T3 acumulados → isola cada um e calcula T4 = DFP - T3_ytd
- ISOLADO: Trimestres já vêm isolados → mantém e calcula faltante se necessário
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


def _valor_conta_raw(df_periodo: pd.DataFrame, codigo: str) -> float:
    """Extrai valor de uma conta do DataFrame"""
    exact = df_periodo[df_periodo["cd_conta"] == codigo]
    if not exact.empty:
        s = exact["valor"].dropna()
        return float(s.iloc[-1]) if not s.empty else np.nan
    desc = df_periodo[df_periodo["cd_conta"].str.startswith(codigo + ".")]
    if not desc.empty:
        return float(desc["valor"].sum(skipna=True))
    return np.nan


def _detectar_padrao_por_ano(
    tri: pd.DataFrame,
    anu: pd.DataFrame,
    ano: int,
    cod_teste: str = "3.01"
) -> Tuple[str, List[int], float]:
    """
    Detecta o padrão de um ano específico testando a soma contra o anual.
    
    Retorna: (padrão, trimestres_disponiveis, valor_anual)
    - padrão: "ytd", "isolado", ou "indeterminado"
    """
    # Filtrar ITRs do ano
    itrs_ano = tri[tri["ano"] == ano].copy()
    dfp_ano = anu[anu["ano"] == ano].copy()
    
    if itrs_ano.empty:
        return ("indeterminado", [], np.nan)
    
    # Identificar trimestres disponíveis
    trimestres = sorted(itrs_ano["q"].unique().tolist())
    
    # Obter valor anual (se disponível)
    v_anual = np.nan
    if not dfp_ano.empty:
        v_anual = _valor_conta_raw(dfp_ano, cod_teste)
    
    if pd.isna(v_anual) or v_anual == 0:
        # Sem anual para comparar - usar heurística
        # Se tem T1, T2, T3 → provavelmente YTD
        # Se tem combinação diferente → provavelmente isolado
        if trimestres == [1, 2, 3]:
            return ("ytd", trimestres, v_anual)
        else:
            return ("isolado", trimestres, v_anual)
    
    # Coletar valores por trimestre
    valores_tri = {}
    for q in trimestres:
        df_q = itrs_ano[itrs_ano["q"] == q]
        valores_tri[q] = _valor_conta_raw(df_q, cod_teste)
    
    # Remover NaN
    valores_validos = {k: v for k, v in valores_tri.items() if not pd.isna(v)}
    
    if not valores_validos:
        return ("indeterminado", trimestres, v_anual)
    
    # TESTE 1: Assumir ISOLADO - somar todos os trimestres disponíveis
    # Se soma ≈ anual, são isolados
    soma_isolado = sum(valores_validos.values())
    
    # Para isolado, precisamos inferir o trimestre faltante
    trimestres_faltantes = [q for q in [1, 2, 3, 4] if q not in trimestres]
    
    if len(trimestres_faltantes) == 1:
        # Calcular o faltante
        q_faltante = trimestres_faltantes[0]
        v_faltante_isolado = v_anual - soma_isolado
        soma_completa_isolado = soma_isolado + v_faltante_isolado
    elif len(trimestres_faltantes) == 0:
        soma_completa_isolado = soma_isolado
    else:
        # Mais de um faltante - difícil determinar
        soma_completa_isolado = soma_isolado
    
    diff_isolado = abs(soma_completa_isolado - v_anual)
    pct_isolado = (diff_isolado / abs(v_anual)) * 100 if v_anual != 0 else 0
    
    # TESTE 2: Assumir YTD - pegar o maior valor (último acumulado)
    # Se maior valor ≈ anual, são YTD
    if trimestres == [1, 2, 3]:
        # Padrão típico YTD
        v_t3 = valores_validos.get(3, np.nan)
        if not pd.isna(v_t3):
            diff_ytd = abs(v_t3 - v_anual)
            # Em YTD, T3 deveria ser ~75% do anual (9 meses)
            # Mas T4 isolado seria anual - T3
            # Então anual = T3 + T4_isolado
            # Não temos T4, então verificamos se T3 < anual
            if v_t3 < v_anual:
                # Poderia ser YTD
                pct_ytd = (diff_ytd / abs(v_anual)) * 100 if v_anual != 0 else 0
            else:
                pct_ytd = 999  # T3 >= anual não faz sentido para YTD
        else:
            pct_ytd = 999
    else:
        # Combinação atípica - provavelmente não é YTD padrão
        pct_ytd = 999
    
    # Decisão: escolher o padrão com menor erro
    if pct_isolado <= TOLERANCIA_CHECKUP_PCT:
        return ("isolado", trimestres, v_anual)
    elif pct_ytd <= 50:  # YTD permite mais variação pois T4 está embutido
        return ("ytd", trimestres, v_anual)
    elif pct_isolado < pct_ytd:
        return ("isolado", trimestres, v_anual)
    else:
        return ("ytd", trimestres, v_anual)


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
    1. Detecta padrão POR ANO: YTD (acumulado) ou Isolado
    2. YTD: isola T1,T2,T3 e calcula T4 = DFP - T3_ytd
    3. Isolado: mantém trimestres e calcula faltante = DFP - soma(existentes)
    4. Check-up rigoroso: receita NUNCA negativa, soma = anual
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
    
    if mes_encerramento != 12:
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

    def _valor_conta(df_periodo: pd.DataFrame, codigo: str) -> float:
        return _valor_conta_raw(df_periodo, codigo)

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

    # Identificar todos os anos disponíveis
    anos_tri = set(tri["ano"].dropna().unique())
    anos_anu = set(anu["ano"].dropna().unique())
    todos_anos = sorted(anos_tri | anos_anu)

    if not todos_anos:
        df_vazio = pd.DataFrame({"cd_conta_padrao": contas, "ds_conta_padrao": [nomes[c] for c in contas]})
        if retornar_resultado_completo:
            return PadronizacaoResult(df=df_vazio, aprovado_geral=True, alertas=["Sem períodos"], padrao_detectado="indeterminado")
        return df_vazio

    # Detectar padrão POR ANO
    padroes_por_ano = {}
    padrao_predominante = "ytd"
    
    for ano in todos_anos:
        padrao, trimestres, v_anual = _detectar_padrao_por_ano(tri, anu, ano, "3.01")
        padroes_por_ano[ano] = {
            "padrao": padrao,
            "trimestres": trimestres,
            "valor_anual": v_anual
        }
        alertas.append(f"Ano {ano}: padrão {padrao.upper()}, trimestres {trimestres}")
    
    # Determinar padrão predominante
    contagem = {"ytd": 0, "isolado": 0}
    for info in padroes_por_ano.values():
        if info["padrao"] in contagem:
            contagem[info["padrao"]] += 1
    
    padrao_predominante = "isolado" if contagem["isolado"] > contagem["ytd"] else "ytd"
    alertas.insert(0, f"Padrão predominante: {padrao_predominante.upper()}")

    # Coletar todos os períodos que realmente existem nos dados
    periodos_finais = set()
    
    for ano in todos_anos:
        info = padroes_por_ano.get(ano, {"trimestres": []})
        
        # Adicionar trimestres dos ITRs
        for q in info["trimestres"]:
            periodos_finais.add((ano, q))
        
        # Adicionar T4 do DFP se existir
        if ano in anos_anu:
            dfp_ano = anu[anu["ano"] == ano]
            if not dfp_ano.empty:
                q_dfp = dfp_ano["q"].iloc[0]
                periodos_finais.add((ano, q_dfp))

    todos_periodos = sorted(periodos_finais)

    # Criar matriz de resultados
    cols_mi = pd.MultiIndex.from_tuples(todos_periodos, names=["ano", "q"])
    mat = pd.DataFrame(index=contas, columns=cols_mi, dtype="float64")

    # PROCESSAR ANO POR ANO
    for ano in todos_anos:
        info = padroes_por_ano.get(ano, {"padrao": "ytd", "trimestres": []})
        padrao_ano = info["padrao"]
        trimestres_existentes = info["trimestres"]
        
        # Dados do ano
        itrs_ano = tri[tri["ano"] == ano].copy()
        dfp_ano = anu[anu["ano"] == ano].copy()
        
        tem_dfp = not dfp_ano.empty
        q_dfp = int(dfp_ano["q"].iloc[0]) if tem_dfp else 4
        
        if padrao_ano == "isolado":
            # ========== PADRÃO ISOLADO ==========
            # Manter trimestres como estão e calcular faltante
            
            for cod in contas:
                cod_mapeado = _map_codigo(cod)
                
                # 1. Preencher valores dos ITRs existentes
                for q in trimestres_existentes:
                    df_q = itrs_ano[itrs_ano["q"] == q]
                    if df_q.empty:
                        continue
                    
                    if cod.startswith("3.99"):
                        mat.at[cod, (ano, q)] = _valor_eps(df_q)
                    else:
                        mat.at[cod, (ano, q)] = _valor_conta(df_q, cod_mapeado)
                
                # 2. Calcular trimestre faltante (se tiver DFP)
                if tem_dfp and cod not in ["3.99", "3.99.01.01", "3.99.01.02"]:
                    v_anual = _valor_conta(dfp_ano, cod_mapeado)
                    
                    if not pd.isna(v_anual):
                        # Somar trimestres existentes
                        soma = 0.0
                        count = 0
                        for q in trimestres_existentes:
                            if (ano, q) in mat.columns:
                                v = mat.at[cod, (ano, q)]
                                if not pd.isna(v):
                                    soma += v
                                    count += 1
                        
                        # Identificar trimestre faltante
                        todos_q = [1, 2, 3, 4]
                        faltantes = [q for q in todos_q if q not in trimestres_existentes]
                        
                        if len(faltantes) == 1:
                            q_faltante = faltantes[0]
                            v_faltante = v_anual - soma
                            if (ano, q_faltante) in mat.columns:
                                mat.at[cod, (ano, q_faltante)] = v_faltante
                        elif len(faltantes) == 0:
                            # Todos trimestres já existem - não fazer nada
                            pass
                
                # LPA do DFP
                if tem_dfp and cod.startswith("3.99"):
                    if (ano, q_dfp) in mat.columns:
                        mat.at[cod, (ano, q_dfp)] = _valor_eps(dfp_ano)
        
        else:
            # ========== PADRÃO YTD (ACUMULADO) ==========
            # ITRs são acumulados, precisamos isolar cada trimestre
            
            for cod in contas:
                cod_mapeado = _map_codigo(cod)
                
                # 1. Preencher valores brutos dos ITRs (ainda YTD)
                valores_ytd = {}
                for q in trimestres_existentes:
                    df_q = itrs_ano[itrs_ano["q"] == q]
                    if df_q.empty:
                        continue
                    
                    if cod.startswith("3.99"):
                        valores_ytd[q] = _valor_eps(df_q)
                    else:
                        valores_ytd[q] = _valor_conta(df_q, cod_mapeado)
                
                # 2. Calcular T4 ANTES de isolar (usa T3 ainda acumulado)
                if tem_dfp and not cod.startswith("3.99"):
                    v_anual = _valor_conta(dfp_ano, cod_mapeado)
                    
                    if not pd.isna(v_anual):
                        # T4 = Anual - T3_ytd (ou último trimestre acumulado)
                        ultimo_q = max(trimestres_existentes) if trimestres_existentes else None
                        
                        if ultimo_q and ultimo_q in valores_ytd:
                            v_ultimo_ytd = valores_ytd[ultimo_q]
                            if not pd.isna(v_ultimo_ytd):
                                v_t4 = v_anual - v_ultimo_ytd
                                if (ano, q_dfp) in mat.columns:
                                    mat.at[cod, (ano, q_dfp)] = v_t4
                            else:
                                if (ano, q_dfp) in mat.columns:
                                    mat.at[cod, (ano, q_dfp)] = v_anual
                        else:
                            if (ano, q_dfp) in mat.columns:
                                mat.at[cod, (ano, q_dfp)] = v_anual
                
                # LPA do DFP
                if tem_dfp and cod.startswith("3.99"):
                    if (ano, q_dfp) in mat.columns:
                        mat.at[cod, (ano, q_dfp)] = _valor_eps(dfp_ano)
                
                # 3. Isolar trimestres (do maior para o menor)
                # T3_iso = T3_ytd - T2_ytd
                # T2_iso = T2_ytd - T1_ytd
                # T1_iso = T1_ytd (já isolado)
                
                if cod.startswith("3.99"):
                    # LPA já são valores por ação, não acumulam
                    for q in trimestres_existentes:
                        if (ano, q) in mat.columns:
                            mat.at[cod, (ano, q)] = valores_ytd.get(q, np.nan)
                else:
                    trimestres_ordenados = sorted(trimestres_existentes)
                    
                    for i in range(len(trimestres_ordenados) - 1, -1, -1):
                        q_atual = trimestres_ordenados[i]
                        v_atual = valores_ytd.get(q_atual, np.nan)
                        
                        if pd.isna(v_atual):
                            continue
                        
                        if i == 0:
                            # T1 já é isolado
                            if (ano, q_atual) in mat.columns:
                                mat.at[cod, (ano, q_atual)] = v_atual
                        else:
                            # Ti = Ti_ytd - Ti-1_ytd
                            q_anterior = trimestres_ordenados[i - 1]
                            v_anterior = valores_ytd.get(q_anterior, np.nan)
                            
                            if not pd.isna(v_anterior):
                                v_isolado = v_atual - v_anterior
                                if (ano, q_atual) in mat.columns:
                                    mat.at[cod, (ano, q_atual)] = v_isolado
                            else:
                                if (ano, q_atual) in mat.columns:
                                    mat.at[cod, (ano, q_atual)] = v_atual

    # Preencher derivadas (ex: Resultado Bruto = Receita + Custo)
    if preencher_derivadas:
        for (ano, q) in todos_periodos:
            if (ano, q) not in mat.columns:
                continue
            if "3.03" in contas and "3.01" in contas and "3.02" in contas:
                if pd.isna(mat.at["3.03", (ano, q)]):
                    v1 = mat.at["3.01", (ano, q)]
                    v2 = mat.at["3.02", (ano, q)]
                    if not (pd.isna(v1) or pd.isna(v2)):
                        mat.at["3.03", (ano, q)] = v1 + v2

    # ========== CHECK-UP RIGOROSO ==========
    checkup_results = []
    aprovado_geral = True
    
    if realizar_checkup:
        # VALIDAÇÃO 1: Receita (3.01) NUNCA pode ser negativa
        cod_receita = "3.01"
        for (ano, q) in todos_periodos:
            if (ano, q) not in mat.columns:
                continue
            v_receita = mat.at[cod_receita, (ano, q)]
            if not pd.isna(v_receita) and v_receita < 0:
                aprovado_geral = False
                alertas.append(f"❌ ERRO CRÍTICO: Receita NEGATIVA em {ano}-T{q}: {v_receita:,.0f}")
        
        # VALIDAÇÃO 2: Soma dos 4 trimestres deve bater com anual
        for ano in todos_anos:
            dfp_ano = anu[anu["ano"] == ano]
            if dfp_ano.empty:
                continue  # Sem anual, não tem como validar
            
            # Encontrar trimestres do ano na matriz
            trimestres_ano = [(a, q) for (a, q) in todos_periodos if a == ano]
            
            if len(trimestres_ano) < 4:
                # Ano incompleto - validação parcial
                alertas.append(f"Ano {ano}: {len(trimestres_ano)} trimestre(s) - validação parcial")
                continue
            
            for cod in contas:
                if cod.startswith("3.99"):
                    continue  # LPA não soma
                
                cod_mapeado = _map_codigo(cod)
                
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
                v_anual = _valor_conta(dfp_ano, cod_mapeado)
                
                if pd.isna(v_anual) or count == 0:
                    continue
                
                diff = abs(soma - v_anual)
                diff_pct = (diff / abs(v_anual)) * 100 if v_anual != 0 else 0
                ok = diff_pct <= TOLERANCIA_CHECKUP_PCT or diff <= TOLERANCIA_CHECKUP_ABS
                
                if not ok:
                    aprovado_geral = False
                    if cod == "3.01":
                        alertas.append(f"❌ Receita {ano}: Soma={soma:,.0f} vs Anual={v_anual:,.0f} (diff {diff_pct:.1f}%)")
                    elif cod == "3.11":
                        alertas.append(f"❌ Lucro {ano}: Soma={soma:,.0f} vs Anual={v_anual:,.0f} (diff {diff_pct:.1f}%)")
                
                checkup_results.append(CheckupResult(
                    ano=ano, trimestre=4, cd_conta=cod, ds_conta=nomes.get(cod, ""),
                    soma_trimestres=soma, valor_anual=v_anual,
                    diferenca=diff, diferenca_pct=diff_pct, aprovado=ok
                ))

    # Status final
    if aprovado_geral:
        alertas.append("✅ CHECK-UP APROVADO")
    else:
        alertas.append("❌ CHECK-UP REPROVADO - Verificar dados")

    # Montar saída
    out = pd.DataFrame({
        "cd_conta_padrao": contas,
        "ds_conta_padrao": [nomes[c] for c in contas]
    })
    
    for (ano, q) in todos_periodos:
        if (ano, q) in mat.columns:
            out[f"{ano}-T{q}"] = mat[(ano, q)].values

    if retornar_resultado_completo:
        return PadronizacaoResult(
            df=out,
            checkup_results=checkup_results,
            mes_encerramento_fiscal=mes_encerramento,
            aprovado_geral=aprovado_geral,
            alertas=alertas,
            padrao_detectado=padrao_predominante
        )

    return out


def gerar_relatorio_checkup(resultado: PadronizacaoResult) -> str:
    """Gera relatório de check-up formatado"""
    linhas = ["=" * 60, "RELATÓRIO DE CHECK-UP - DRE", "=" * 60, ""]
    linhas.append(f"Mês encerramento fiscal: {resultado.mes_encerramento_fiscal}")
    linhas.append(f"Padrão detectado: {resultado.padrao_detectado.upper()}")
    linhas.append(f"Status: {'✅ APROVADO' if resultado.aprovado_geral else '❌ REPROVADO'}")
    
    if resultado.alertas:
        linhas.append("\nALERTAS:")
        for a in resultado.alertas:
            linhas.append(f"  {a}")
    
    falhas = [r for r in resultado.checkup_results if not r.aprovado]
    if falhas:
        linhas.append(f"\nFALHAS DETALHADAS ({len(falhas)}):")
        for r in falhas[:20]:
            linhas.append(f"  {r.ano} | {r.cd_conta} {r.ds_conta[:30]}")
            linhas.append(f"       Soma={r.soma_trimestres:,.0f} vs Anual={r.valor_anual:,.0f} (diff {r.diferenca_pct:.2f}%)")
    
    return "\n".join(linhas)


def padronizar_dre(*args, **kwargs):
    """Alias para compatibilidade"""
    return padronizar_dre_trimestral_e_anual(*args, **kwargs)
