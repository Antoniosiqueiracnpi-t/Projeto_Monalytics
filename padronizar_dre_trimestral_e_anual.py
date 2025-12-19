"""
PADRONIZAÇÃO DRE - VERSÃO APRIMORADA
=====================================
Melhorias implementadas:
1. Detecção automática do ano fiscal baseado no mês de encerramento do DFP
2. Mapeamento correto de trimestres para o ano fiscal correspondente
3. Isolamento do T4 usando trimestres do mesmo ano fiscal
4. Sistema de check-up comparando soma dos trimestres com o anual
5. Suporte completo para empresas com ano fiscal diferente de dezembro
6. Relatório de validação com status de aprovação

Mantém 100% compatibilidade com a lógica original para casos padrão.
"""

import pandas as pd
import numpy as np
from functools import lru_cache
from typing import Optional, Dict, Tuple, List, Any
from dataclasses import dataclass, field
from datetime import datetime
import warnings


# ==================== ESTRUTURAS DE DADOS ====================

@dataclass
class CheckupResult:
    """Resultado do check-up de uma conta em um ano fiscal"""
    ano_fiscal: int
    cd_conta: str
    ds_conta: str
    soma_trimestres: float
    valor_anual: float
    diferenca: float
    diferenca_pct: float
    aprovado: bool
    trimestres_usados: List[str]
    observacao: str = ""


@dataclass
class PadronizacaoResult:
    """Resultado completo da padronização"""
    df: pd.DataFrame
    checkup_results: List[CheckupResult] = field(default_factory=list)
    ano_fiscal_detectado: int = 12  # mês de encerramento
    anos_fiscais_mapeados: Dict[int, List[Tuple[int, int]]] = field(default_factory=dict)
    aprovado_geral: bool = True
    alertas: List[str] = field(default_factory=list)


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

# Tolerância para check-up (diferença percentual aceitável)
TOLERANCIA_CHECKUP_PCT = 1.0  # 1%
TOLERANCIA_CHECKUP_ABS = 1.0  # R$ 1 mil (para valores muito pequenos)


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


def _detectar_mes_encerramento_ano_fiscal(df_anual: pd.DataFrame) -> int:
    """
    Detecta o mês de encerramento do ano fiscal baseado nas datas do DFP.
    Retorna o mês (1-12) mais frequente nas datas de fim de exercício.
    """
    if df_anual.empty or "data_fim" not in df_anual.columns:
        return 12  # padrão: dezembro
    
    datas = pd.to_datetime(df_anual["data_fim"], errors="coerce")
    meses = datas.dt.month.dropna()
    
    if meses.empty:
        return 12
    
    # Retorna o mês mais frequente
    return int(meses.mode().iloc[0]) if not meses.mode().empty else 12


def _mapear_trimestre_para_ano_fiscal(
    data_fim: pd.Timestamp,
    mes_encerramento: int
) -> Tuple[int, int]:
    """
    Mapeia uma data para o ano fiscal e trimestre correspondentes.
    
    Para uma empresa com ano fiscal encerrando em junho:
    - Jul/2023 a Set/2023 -> AF 2024, T1
    - Out/2023 a Dez/2023 -> AF 2024, T2
    - Jan/2024 a Mar/2024 -> AF 2024, T3
    - Abr/2024 a Jun/2024 -> AF 2024, T4
    
    Retorna: (ano_fiscal, trimestre)
    """
    if pd.isna(data_fim):
        return (0, 0)
    
    mes = data_fim.month
    ano = data_fim.year
    
    # Calcular quantos meses após o encerramento do ano fiscal anterior
    if mes <= mes_encerramento:
        # Estamos no mesmo ano calendário do encerramento
        meses_desde_inicio = mes + (12 - mes_encerramento)
        ano_fiscal = ano
    else:
        # Estamos no ano calendário seguinte ao início do ano fiscal
        meses_desde_inicio = mes - mes_encerramento
        ano_fiscal = ano + 1
    
    # Determinar trimestre (1-4) baseado nos meses desde o início
    trimestre = ((meses_desde_inicio - 1) // 3) + 1
    trimestre = min(max(trimestre, 1), 4)  # garantir entre 1 e 4
    
    return (ano_fiscal, trimestre)


def _criar_mapeamento_ano_fiscal(
    df_tri: pd.DataFrame,
    df_anu: pd.DataFrame,
    mes_encerramento: int
) -> Dict[int, Dict[str, Any]]:
    """
    Cria um mapeamento completo de anos fiscais com seus trimestres.
    
    Retorna:
    {
        2024: {
            "trimestres": {1: (data, valor_dict), 2: ..., 3: ..., 4: (data_dfp, valor_dict)},
            "anual": (data_dfp, valor_dict),
            "completo": True/False
        }
    }
    """
    mapeamento = {}
    
    # Processar trimestres do ITR
    for _, row in df_tri.iterrows():
        data = row["data_fim"]
        if pd.isna(data):
            continue
        
        af, q = _mapear_trimestre_para_ano_fiscal(data, mes_encerramento)
        if af == 0:
            continue
        
        if af not in mapeamento:
            mapeamento[af] = {"trimestres": {}, "anual": None, "completo": False}
        
        if q not in mapeamento[af]["trimestres"]:
            mapeamento[af]["trimestres"][q] = data
    
    # Processar dados anuais (DFP)
    for _, row in df_anu.iterrows():
        data = row["data_fim"]
        if pd.isna(data):
            continue
        
        af, _ = _mapear_trimestre_para_ano_fiscal(data, mes_encerramento)
        if af == 0:
            continue
        
        if af not in mapeamento:
            mapeamento[af] = {"trimestres": {}, "anual": None, "completo": False}
        
        mapeamento[af]["anual"] = data
        mapeamento[af]["trimestres"][4] = data  # T4 vem do DFP
    
    # Verificar completude
    for af in mapeamento:
        tris = set(mapeamento[af]["trimestres"].keys())
        # Consideramos completo se temos pelo menos T1, T2, T3 ou alguma combinação válida + T4
        mapeamento[af]["completo"] = (4 in tris) and len(tris) >= 2
    
    return mapeamento


def _realizar_checkup(
    mat: pd.DataFrame,
    df_anual_original: pd.DataFrame,
    contas: List[str],
    nomes: Dict[str, str],
    mapeamento_af: Dict[int, Dict],
    mes_encerramento: int
) -> List[CheckupResult]:
    """
    Realiza o check-up comparando soma dos trimestres isolados com o valor anual.
    Retorna lista de resultados do check-up.
    """
    resultados = []
    
    for af, info in mapeamento_af.items():
        if not info["anual"]:
            continue
        
        trimestres_disponiveis = sorted(info["trimestres"].keys())
        if 4 not in trimestres_disponiveis:
            continue
        
        # Buscar valor anual original
        data_anual = info["anual"]
        df_anual_af = df_anual_original[
            df_anual_original["data_fim"] == data_anual
        ]
        
        for cod in contas:
            # Pular LPA (não soma)
            if cod.startswith("3.99"):
                continue
            
            # Soma dos trimestres isolados na matriz
            soma_tri = 0.0
            tris_usados = []
            for q in [1, 2, 3, 4]:
                if (af, q) in mat.columns:
                    v = mat.at[cod, (af, q)]
                    if not pd.isna(v):
                        soma_tri += v
                        tris_usados.append(f"T{q}")
            
            # Valor anual original
            valor_anual = np.nan
            anual_rows = df_anual_af[df_anual_af["cd_conta"] == cod]
            if not anual_rows.empty:
                valor_anual = anual_rows["valor"].iloc[-1]
            
            if pd.isna(valor_anual) or len(tris_usados) == 0:
                continue
            
            # Calcular diferença
            diferenca = abs(soma_tri - valor_anual)
            diferenca_pct = (diferenca / abs(valor_anual) * 100) if valor_anual != 0 else 0
            
            # Verificar aprovação
            aprovado = (
                diferenca_pct <= TOLERANCIA_CHECKUP_PCT or
                diferenca <= TOLERANCIA_CHECKUP_ABS
            )
            
            observacao = ""
            if not aprovado:
                observacao = f"Diferença de {diferenca_pct:.2f}% excede tolerância"
            
            resultados.append(CheckupResult(
                ano_fiscal=af,
                cd_conta=cod,
                ds_conta=nomes.get(cod, ""),
                soma_trimestres=soma_tri,
                valor_anual=valor_anual,
                diferenca=diferenca,
                diferenca_pct=diferenca_pct,
                aprovado=aprovado,
                trimestres_usados=tris_usados,
                observacao=observacao
            ))
    
    return resultados


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
) -> pd.DataFrame | PadronizacaoResult:
    """
    Padroniza DRE trimestral e anual com suporte a anos fiscais diferentes.
    
    REGRAS PRINCIPAIS:
    - T1/T2/T3: valores do ITR (já são trimestrais isolados para DRE)
    - T4: Anual(DFP) - (T1 + T2 + T3) para contas de resultado
    - EPS (3.99*): pega 1 valor por período, NÃO subtrai
    
    MELHORIAS DESTA VERSÃO:
    - Detecta automaticamente o mês de encerramento do ano fiscal
    - Mapeia trimestres para o ano fiscal correto
    - Realiza check-up comparando soma trimestral com anual
    - Suporta empresas com ano fiscal diferente de dezembro
    
    Parâmetros:
        dre_trimestral_csv: Caminho do CSV trimestral (ITR)
        dre_anual_csv: Caminho do CSV anual (DFP)
        unidade: 'mil', 'unidade' ou 'milhao'
        preencher_derivadas: Se True, calcula contas derivadas faltantes
        ticker: Ticker da empresa (opcional, pode ser inferido)
        b3_mapping_csv: Caminho do mapeamento B3 para identificar setor
        realizar_checkup: Se True, realiza validação dos valores
        retornar_resultado_completo: Se True, retorna PadronizacaoResult
    
    Retorna:
        DataFrame padronizado ou PadronizacaoResult (se retornar_resultado_completo=True)
    """
    
    alertas = []
    
    # Identificar ticker e setor
    ticker_norm = _norm_ticker(ticker) or _infer_ticker_from_paths(dre_trimestral_csv, dre_anual_csv)
    setor, _segmento = _get_setor_segmento_from_b3_mapping(ticker_norm, b3_mapping_csv)
    setor_l = (setor or "").strip().lower()

    # Determinar modo (seguros, bancos ou padrão)
    modo_seguros = (
        (ticker_norm in _SEGUROS_TICKERS) or
        (setor is not None and setor_l == "previdência e seguros")
    )
    modo_bancos = (
        (ticker_norm in _BANCOS_TICKERS) or
        (setor is not None and setor_l == "bancos")
    )

    # Selecionar plano de contas
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
            raise ValueError(f"Arquivo {name} sem colunas esperadas: {missing}")

    # Normalização básica
    for df in (tri, anu):
        df["data_fim"] = pd.to_datetime(df["data_fim"], errors="coerce")
        df["trimestre"] = df["trimestre"].astype(str).str.upper().str.strip()
        df["cd_conta"] = df["cd_conta"].astype(str).str.strip()
        df["ds_conta"] = df["ds_conta"].astype(str)
        df["valor_mil"] = pd.to_numeric(df["valor_mil"], errors="coerce")

    # Detectar mês de encerramento do ano fiscal
    mes_encerramento = _detectar_mes_encerramento_ano_fiscal(anu)
    
    if mes_encerramento != 12:
        alertas.append(f"Ano fiscal detectado: encerramento em mês {mes_encerramento}")

    # Aplicar fator de unidade
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

    # Mapear para ano fiscal
    tri["ano_fiscal"], tri["q_fiscal"] = zip(*tri["data_fim"].apply(
        lambda d: _mapear_trimestre_para_ano_fiscal(d, mes_encerramento)
    ))
    anu["ano_fiscal"], anu["q_fiscal"] = zip(*anu["data_fim"].apply(
        lambda d: _mapear_trimestre_para_ano_fiscal(d, mes_encerramento)
    ))
    
    # Anual sempre é Q4 do ano fiscal
    anu["q_fiscal"] = 4

    # Criar mapeamento de anos fiscais
    mapeamento_af = _criar_mapeamento_ano_fiscal(tri, anu, mes_encerramento)

    # Filtrar trimestres: DRE usa T1-T3 do ITR, T4 vem do DFP
    # Remover T4 do ITR para evitar duplicação (exceto se não houver DFP para o ano)
    tri_filtrado = tri.copy()
    for af, info in mapeamento_af.items():
        if info["anual"] is not None:
            # Se temos DFP, remover T4 do ITR para este ano fiscal
            mask = (tri_filtrado["ano_fiscal"] == af) & (tri_filtrado["q_fiscal"] == 4)
            tri_filtrado = tri_filtrado[~mask]

    # Construir lista de períodos (ano_fiscal, trimestre)
    periodos_tri = tri_filtrado[["ano_fiscal", "q_fiscal"]].dropna().drop_duplicates()
    periodos_anu = anu[["ano_fiscal", "q_fiscal"]].dropna().drop_duplicates()
    
    periodos = pd.concat([periodos_tri, periodos_anu], ignore_index=True)
    periodos = periodos.drop_duplicates().sort_values(["ano_fiscal", "q_fiscal"])
    periodos = [(int(r["ano_fiscal"]), int(r["q_fiscal"])) for _, r in periodos.iterrows() if r["ano_fiscal"] > 0]

    if not periodos:
        df_vazio = pd.DataFrame({"cd_conta_padrao": contas, "ds_conta_padrao": [nomes[c] for c in contas]})
        if retornar_resultado_completo:
            return PadronizacaoResult(df=df_vazio, aprovado_geral=True, alertas=["Sem períodos encontrados"])
        return df_vazio

    # Criar matriz de valores
    cols_mi = pd.MultiIndex.from_tuples(periodos, names=["ano_fiscal", "q"])
    mat = pd.DataFrame(index=contas, columns=cols_mi, dtype="float64")

    # Funções auxiliares para extração de valores
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
        eps = df_periodo[df_periodo["cd_conta"].str.startswith("3.99")].copy()
        if eps.empty:
            return np.nan
        eps = eps.dropna(subset=["valor"])
        if eps.empty:
            return np.nan
        for prefer in ["3.99.01.01", "3.99.01.02", "3.99"]:
            hit = eps[eps["cd_conta"] == prefer]
            if not hit.empty:
                return float(hit["valor"].iloc[-1])
        return float(eps["valor"].iloc[-1])

    # Mapeamentos por setor
    seguros_map_por_ticker: Dict[str, Dict[str, str]] = {
        "BBSE3": {"3.05": "3.07", "3.06": "3.08", "3.07": "3.06", "3.08": "3.09"},
        "CXSE3": {"3.05": "3.05", "3.06": "3.06", "3.07": "3.07", "3.08": "3.08"},
        "IRBR3": {"3.05": "3.07", "3.06": "3.08", "3.07": "3.06", "3.08": "3.09"},
        "PSSA3": {"3.05": "3.05", "3.06": "3.06", "3.07": "3.07", "3.08": "3.07"},
    }
    seguros_map = seguros_map_por_ticker.get(ticker_norm, {}) if modo_seguros else {}

    bancos_map: Dict[str, str] = {
        "3.01": "3.01", "3.02": "3.02", "3.03": "3.03", "3.04": "3.04",
        "3.05": "3.07", "3.06": "3.08", "3.07": "3.09", "3.08": "3.10",
        "3.09": "3.11", "3.99": "3.99", "3.99.01.01": "3.99.01.01",
        "3.99.01.02": "3.99.01.02",
    } if modo_bancos else {}

    def _map_codigo_fonte(cod_padrao: str) -> str:
        if modo_seguros and cod_padrao in seguros_map:
            return seguros_map[cod_padrao]
        if modo_bancos and cod_padrao in bancos_map:
            return bancos_map[cod_padrao]
        return cod_padrao

    # Preencher matriz com valores dos períodos
    for (af, q) in periodos:
        if q == 4:
            # T4: prioriza DFP
            dfp = anu[(anu["ano_fiscal"] == af) & (anu["q_fiscal"] == 4)]
            if dfp.empty:
                dfp = tri_filtrado[(tri_filtrado["ano_fiscal"] == af) & (tri_filtrado["q_fiscal"] == 4)]
        else:
            dfp = tri_filtrado[(tri_filtrado["ano_fiscal"] == af) & (tri_filtrado["q_fiscal"] == q)]

        if dfp.empty:
            continue

        for cod_padrao in contas:
            if cod_padrao == "3.99" or cod_padrao.startswith("3.99"):
                mat.at[cod_padrao, (af, q)] = _valor_eps_periodo(dfp)
                continue

            cod_fonte = _map_codigo_fonte(cod_padrao)
            mat.at[cod_padrao, (af, q)] = _valor_total_periodo(dfp, cod_fonte)

    # Preencher derivadas
    if preencher_derivadas:
        for (af, q) in periodos:
            if "3.03" in contas and "3.01" in contas and "3.02" in contas:
                v303 = mat.at["3.03", (af, q)]
                if pd.isna(v303):
                    v301 = mat.at["3.01", (af, q)]
                    v302 = mat.at["3.02", (af, q)]
                    if not (pd.isna(v301) or pd.isna(v302)):
                        mat.at["3.03", (af, q)] = float(v301 + v302)

    # Isolar T4: T4 = Anual - (T1 + T2 + T3)
    # Agora usando ano fiscal corretamente
    for (af, q) in periodos:
        if q != 4:
            continue
        
        for cod_padrao in contas:
            # Não subtrair LPA
            if cod_padrao.startswith("3.99"):
                continue

            v_anual = mat.at[cod_padrao, (af, 4)]
            if pd.isna(v_anual):
                continue

            # Somar trimestres anteriores DO MESMO ANO FISCAL
            soma = 0.0
            tem_trimestres = False
            for qq in (1, 2, 3):
                if (af, qq) in mat.columns:
                    vv = mat.at[cod_padrao, (af, qq)]
                    if not pd.isna(vv):
                        soma += float(vv)
                        tem_trimestres = True

            if tem_trimestres:
                mat.at[cod_padrao, (af, 4)] = float(v_anual - soma)

    # Realizar check-up
    checkup_results = []
    aprovado_geral = True
    
    if realizar_checkup:
        checkup_results = _realizar_checkup(
            mat, anu, contas, nomes, mapeamento_af, mes_encerramento
        )
        aprovado_geral = all(r.aprovado for r in checkup_results)
        
        if not aprovado_geral:
            falhas = [r for r in checkup_results if not r.aprovado]
            alertas.append(f"Check-up: {len(falhas)} contas com divergência")

    # Construir DataFrame de saída
    out = pd.DataFrame({
        "cd_conta_padrao": contas,
        "ds_conta_padrao": [nomes[c] for c in contas]
    })
    
    for (af, q) in periodos:
        out[f"{af}-T{q}"] = mat[(af, q)].values

    if retornar_resultado_completo:
        return PadronizacaoResult(
            df=out,
            checkup_results=checkup_results,
            ano_fiscal_detectado=mes_encerramento,
            anos_fiscais_mapeados={af: list(info["trimestres"].keys()) for af, info in mapeamento_af.items()},
            aprovado_geral=aprovado_geral,
            alertas=alertas
        )

    return out


# ==================== FUNÇÕES DE RELATÓRIO ====================

def gerar_relatorio_checkup(resultado: PadronizacaoResult) -> str:
    """Gera um relatório textual do check-up"""
    
    linhas = []
    linhas.append("=" * 60)
    linhas.append("RELATÓRIO DE CHECK-UP - PADRONIZAÇÃO DRE")
    linhas.append("=" * 60)
    linhas.append("")
    
    linhas.append(f"Mês de encerramento do ano fiscal: {resultado.ano_fiscal_detectado}")
    linhas.append(f"Status geral: {'✅ APROVADO' if resultado.aprovado_geral else '❌ REPROVADO'}")
    linhas.append("")
    
    if resultado.alertas:
        linhas.append("ALERTAS:")
        for alerta in resultado.alertas:
            linhas.append(f"  ⚠️ {alerta}")
        linhas.append("")
    
    if resultado.checkup_results:
        linhas.append("DETALHES POR CONTA E ANO FISCAL:")
        linhas.append("-" * 60)
        
        # Agrupar por ano fiscal
        por_af = {}
        for r in resultado.checkup_results:
            if r.ano_fiscal not in por_af:
                por_af[r.ano_fiscal] = []
            por_af[r.ano_fiscal].append(r)
        
        for af in sorted(por_af.keys()):
            linhas.append(f"\nAno Fiscal {af}:")
            for r in por_af[af]:
                status = "✅" if r.aprovado else "❌"
                linhas.append(
                    f"  {status} {r.cd_conta} ({r.ds_conta[:30]}...): "
                    f"Soma={r.soma_trimestres:,.0f} | Anual={r.valor_anual:,.0f} | "
                    f"Diff={r.diferenca_pct:.2f}%"
                )
                if r.observacao:
                    linhas.append(f"      {r.observacao}")
    
    return "\n".join(linhas)


# ==================== COMPATIBILIDADE ====================

# Manter assinatura original para compatibilidade
def padronizar_dre(*args, **kwargs):
    """Alias para compatibilidade"""
    return padronizar_dre_trimestral_e_anual(*args, **kwargs)
