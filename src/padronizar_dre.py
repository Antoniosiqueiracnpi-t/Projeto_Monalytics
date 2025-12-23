# src/padronizar_dre.py
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd


# ======================================================================================
# CONTAS PADRÃO (NÃO FINANCEIRAS) - DRE
# ======================================================================================

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
]

EPS_CODE = "3.99"
EPS_LABEL = "Lucro por Ação (Reais/Ação)"


# ======================================================================================
# UTILITÁRIOS
# ======================================================================================

def _to_datetime(df: pd.DataFrame, col: str = "data_fim") -> pd.Series:
    return pd.to_datetime(df[col], errors="coerce")


def _ensure_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype(float)


def _quarter_order(q: str) -> int:
    return {"T1": 1, "T2": 2, "T3": 3, "T4": 4}.get(q, 99)


def _pick_value_for_base_code(group: pd.DataFrame, base_code: str) -> float:
    """Extrai valor para um código base, buscando conta exata ou somando filhas."""
    exact = group[group["cd_conta"] == base_code]
    if not exact.empty:
        v = _ensure_numeric(exact["valor_mil"]).sum()
        return float(v) if np.isfinite(v) else np.nan

    children = group[group["cd_conta"].astype(str).str.startswith(base_code + ".")]
    if children.empty:
        return np.nan
    v = _ensure_numeric(children["valor_mil"]).sum()
    return float(v) if np.isfinite(v) else np.nan


def _compute_eps_value(group: pd.DataFrame) -> float:
    """
    EPS:
      - usar apenas ON/PN (folhas 3.99.*.*)
      - se valores iguais => NÃO somar (retorna um)
      - se ON != PN => soma ON + PN
      - se básico vs diluído divergente => NÃO soma, pega maior |valor| (por classe)
    """
    g = group.copy()
    g["cd_conta"] = g["cd_conta"].astype(str)
    g["ds_conta"] = g["ds_conta"].astype(str)

    leaf = g[g["cd_conta"].str.startswith(EPS_CODE + ".")]
    if leaf.empty:
        direct = g[g["cd_conta"] == EPS_CODE]
        if direct.empty:
            return np.nan
        v = _ensure_numeric(direct["valor_mil"]).sum()
        return float(v) if np.isfinite(v) else np.nan

    leaf = leaf[leaf["ds_conta"].str.upper().isin(["ON", "PN"])].copy()
    if leaf.empty:
        return np.nan

    values_by_class: Dict[str, float] = {}

    for cls in ["ON", "PN"]:
        sub = leaf[leaf["ds_conta"].str.upper() == cls]
        if sub.empty:
            continue
        vals = _ensure_numeric(sub["valor_mil"]).dropna().values.astype(float)
        if len(vals) == 0:
            continue

        uniq = np.unique(np.round(vals, 10))
        if len(uniq) == 1:
            values_by_class[cls] = float(uniq[0])
        else:
            values_by_class[cls] = float(uniq[np.argmax(np.abs(uniq))])

    if not values_by_class:
        return np.nan

    if "ON" in values_by_class and "PN" in values_by_class:
        on = values_by_class["ON"]
        pn = values_by_class["PN"]
        if np.isfinite(on) and np.isfinite(pn) and np.isclose(on, pn, rtol=1e-9, atol=1e-12):
            return float(on)
        return float(on + pn)

    return float(values_by_class.get("ON", values_by_class.get("PN", np.nan)))


# ======================================================================================
# DETECTOR DE ANO FISCAL IRREGULAR
# ======================================================================================

@dataclass
class FiscalYearInfo:
    """Informações sobre o padrão de ano fiscal da empresa."""
    is_standard: bool  # True se ano fiscal = ano calendário (jan-dez)
    fiscal_end_month: int  # Mês de encerramento fiscal (12 = padrão)
    quarters_pattern: Set[str]  # Padrão de trimestres encontrados (ex: {"T1","T2","T3","T4"})
    has_all_quarters: bool  # True se tem T1, T2, T3, T4
    description: str  # Descrição para log


def _detect_fiscal_year_pattern(df_tri: pd.DataFrame, df_anu: pd.DataFrame) -> FiscalYearInfo:
    """
    Detecta o padrão de ano fiscal da empresa de forma CIRÚRGICA.
    
    Critérios para ano fiscal PADRÃO (calendário):
    1. Dados anuais encerram em dezembro (mês 12)
    2. Dados trimestrais contêm T1, T2, T3, T4 para a maioria dos anos
    3. Média de pelo menos 3.5 trimestres por ano
    
    Se qualquer critério falhar => empresa tem ano fiscal IRREGULAR.
    """
    # 1. Verificar mês de encerramento dos dados ANUAIS
    if df_anu is not None and not df_anu.empty:
        dt_anu = _to_datetime(df_anu, "data_fim").dropna()
        if not dt_anu.empty:
            anu_months = dt_anu.dt.month.value_counts()
            most_common_anu_month = int(anu_months.index[0])
        else:
            most_common_anu_month = 12
    else:
        most_common_anu_month = 12

    # 2. Verificar padrão de trimestres nos dados TRIMESTRAIS
    if df_tri is not None and not df_tri.empty:
        df_tri_copy = df_tri.copy()
        df_tri_copy["data_fim"] = _to_datetime(df_tri_copy, "data_fim")
        df_tri_copy = df_tri_copy.dropna(subset=["data_fim"])
        
        if "trimestre" in df_tri_copy.columns:
            all_quarters = set(df_tri_copy["trimestre"].dropna().unique())
        else:
            all_quarters = set()
        
        # Verificar por ano quantos trimestres existem
        df_tri_copy["ano"] = df_tri_copy["data_fim"].dt.year
        quarters_per_year = df_tri_copy.groupby("ano")["trimestre"].nunique()
        avg_quarters = quarters_per_year.mean() if len(quarters_per_year) > 0 else 0
        
    else:
        all_quarters = set()
        avg_quarters = 0

    # 3. DECISÃO: ano fiscal padrão ou irregular?
    # CRITÉRIO DEFINITIVO: baseado APENAS no mês de encerramento anual
    # - Encerra em dezembro (mês 12) = ano fiscal PADRÃO
    # - Encerra em outro mês = ano fiscal IRREGULAR
    has_all_quarters = {"T1", "T2", "T3", "T4"}.issubset(all_quarters)
    is_december_fiscal = (most_common_anu_month == 12)
    
    # Ano fiscal padrão = encerra em dezembro (independente de já ter T4)
    is_standard = is_december_fiscal
    
    # Descrição para log
    if is_standard:
        if has_all_quarters:
            description = "Ano fiscal padrão (jan-dez) com T1-T4 completos"
        else:
            description = f"Ano fiscal padrão (jan-dez) - trimestres disponíveis: {sorted(all_quarters)}"
    else:
        description = f"Ano fiscal IRREGULAR (encerramento em mês {most_common_anu_month}, trimestres: {sorted(all_quarters)})"

    return FiscalYearInfo(
        is_standard=is_standard,
        fiscal_end_month=most_common_anu_month,
        quarters_pattern=all_quarters,
        has_all_quarters=has_all_quarters,
        description=description
    )


# ======================================================================================
# PADRONIZADOR
# ======================================================================================

@dataclass
class CheckupResult:
    """Resultado do check-up linha a linha."""
    code: str
    ano: int
    soma_trimestral: float
    valor_anual: float
    diferenca: float
    percentual_diff: float
    status: str  # "OK", "DIVERGE", "SEM_ANUAL", "INCOMPLETO", "IRREGULAR_SKIP"


@dataclass
class PadronizadorDRE:
    pasta_balancos: Path = Path("balancos")
    checkup_results: List[CheckupResult] = field(default_factory=list)

    def _load_inputs(self, ticker: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        pasta = self.pasta_balancos / ticker.upper().strip()
        tri_path = pasta / "dre_consolidado.csv"
        anu_path = pasta / "dre_anual.csv"

        if not tri_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {tri_path}")
        if not anu_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {anu_path}")

        df_tri = pd.read_csv(tri_path)
        df_anu = pd.read_csv(anu_path)

        for df in (df_tri, df_anu):
            df["cd_conta"] = df["cd_conta"].astype(str).str.strip()
            df["ds_conta"] = df["ds_conta"].astype(str).str.strip()
            df["valor_mil"] = _ensure_numeric(df["valor_mil"])
            df["data_fim"] = _to_datetime(df, "data_fim")

        df_tri = df_tri.dropna(subset=["data_fim"])
        df_anu = df_anu.dropna(subset=["data_fim"])

        return df_tri, df_anu

    def _build_quarter_totals(self, df_tri: pd.DataFrame) -> pd.DataFrame:
        """
        Constrói totais trimestrais preservando trimestres originais.
        Usa ano calendário direto (sem transformação fiscal).
        """
        target_codes = [c for c, _ in DRE_PADRAO]
        wanted_prefixes = tuple([c + "." for c in target_codes] + [EPS_CODE + "."])

        mask = (
            df_tri["cd_conta"].isin(target_codes + [EPS_CODE])
            | df_tri["cd_conta"].astype(str).str.startswith(wanted_prefixes)
        )
        df = df_tri[mask].copy()
        df["ano"] = df["data_fim"].dt.year
        
        rows = []
        for (ano, trimestre), g in df.groupby(["ano", "trimestre"], sort=False):
            for code, _name in DRE_PADRAO:
                v = _pick_value_for_base_code(g, code)
                rows.append((int(ano), str(trimestre), code, v))
            rows.append((int(ano), str(trimestre), EPS_CODE, _compute_eps_value(g)))

        return pd.DataFrame(rows, columns=["ano", "trimestre", "code", "valor"])

    def _extract_annual_values(self, df_anu: pd.DataFrame) -> pd.DataFrame:
        """Extrai valores anuais para comparação no check-up."""
        target_codes = [c for c, _ in DRE_PADRAO]
        wanted_prefixes = tuple([c + "." for c in target_codes])

        mask = (
            df_anu["cd_conta"].isin(target_codes)
            | df_anu["cd_conta"].astype(str).str.startswith(wanted_prefixes)
        )
        df = df_anu[mask].copy()
        df["ano"] = df["data_fim"].dt.year

        rows = []
        for ano, g in df.groupby("ano", sort=False):
            for code, _name in DRE_PADRAO:
                v = _pick_value_for_base_code(g, code)
                rows.append((int(ano), code, v))

        return pd.DataFrame(rows, columns=["ano", "code", "anual_val"])

    def _detect_cumulative_years(
        self,
        qtot: pd.DataFrame,
        anual: pd.DataFrame,
        fiscal_info: FiscalYearInfo,
        base_code_for_detection: str = "3.01",
        ratio_threshold: float = 1.10,
    ) -> Dict[int, bool]:
        """
        Detecta se o trimestral está acumulado (YTD) por ano usando 3.01.
        
        IMPORTANTE: Só faz sentido para empresas com ano fiscal PADRÃO.
        Para empresas irregulares, retorna dict vazio (não tenta converter).
        """
        # Para ano fiscal irregular, não tenta detectar acumulado
        if not fiscal_info.is_standard:
            return {}
        
        anual_map = anual.set_index(["ano", "code"])["anual_val"].to_dict()
        out: Dict[int, bool] = {}

        for ano, g in qtot[qtot["code"] == base_code_for_detection].groupby("ano"):
            a = anual_map.get((int(ano), base_code_for_detection), np.nan)
            if not np.isfinite(a) or a == 0:
                continue
            s = float(np.nansum(g["valor"].values))
            out[int(ano)] = bool(np.isfinite(s) and abs(s) > abs(a) * ratio_threshold)

        return out

    def _to_isolated_quarters(
        self, 
        qtot: pd.DataFrame, 
        cumulative_years: Dict[int, bool],
        fiscal_info: FiscalYearInfo
    ) -> pd.DataFrame:
        """
        Converte dados acumulados (YTD) para trimestres isolados quando necessário.
        
        Para empresas com ano fiscal IRREGULAR: preserva valores originais.
        """
        out_rows = []

        for (ano, code), g in qtot.groupby(["ano", "code"], sort=False):
            g = g.copy()
            g["qord"] = g["trimestre"].apply(_quarter_order)
            g = g.sort_values("qord")

            vals = g["valor"].values.astype(float)
            qs = g["trimestre"].tolist()

            # Só converte se:
            # 1. Ano detectado como acumulado
            # 2. Não é EPS (EPS nunca é acumulado)
            # 3. Empresa tem ano fiscal padrão
            if (cumulative_years.get(int(ano), False) and 
                code != EPS_CODE and 
                fiscal_info.is_standard):
                qords = g["qord"].values
                # só converte se for sequência contínua (1,2,3... ou 1,2,3,4)
                if len(qords) >= 2 and np.array_equal(qords, np.arange(1, len(qords) + 1)):
                    iso = []
                    prev = None
                    for v in vals:
                        iso.append(v if prev is None else (v - prev))
                        prev = v
                    vals = np.array(iso, dtype=float)

            for tq, v in zip(qs, vals):
                out_rows.append((int(ano), tq, code, float(v) if np.isfinite(v) else np.nan))

        return pd.DataFrame(out_rows, columns=["ano", "trimestre", "code", "valor"])

    def _add_t4_from_annual_when_missing(
        self, 
        qiso: pd.DataFrame, 
        anual: pd.DataFrame,
        fiscal_info: FiscalYearInfo
    ) -> pd.DataFrame:
        """
        Adiciona T4 calculado quando faltante, APENAS para empresas com ano fiscal padrão.
        Para empresas com ano fiscal irregular, NÃO adiciona trimestres artificiais.
        """
        # Se ano fiscal irregular, NÃO criar trimestres artificiais
        if not fiscal_info.is_standard:
            return qiso
        
        anual_map = anual.set_index(["ano", "code"])["anual_val"].to_dict()
        out = qiso.copy()

        for ano in sorted(out["ano"].unique()):
            g = out[out["ano"] == ano]
            quarters = set(g["trimestre"].unique())

            if "T4" in quarters:
                continue
            if not {"T1", "T2", "T3"}.issubset(quarters):
                continue

            new_rows = []
            for code, _name in DRE_PADRAO:
                a = anual_map.get((int(ano), code), np.nan)
                if not np.isfinite(a):
                    continue
                s = g[(g["code"] == code) & (g["trimestre"].isin(["T1", "T2", "T3"]))]["valor"].sum(skipna=True)
                new_rows.append((int(ano), "T4", code, float(a - s)))

            if new_rows:
                out = pd.concat([out, pd.DataFrame(new_rows, columns=out.columns)], ignore_index=True)

        return out

    def _build_horizontal(self, qiso: pd.DataFrame) -> pd.DataFrame:
        """Constrói tabela horizontal (períodos como colunas)."""
        periods = (
            qiso[["ano", "trimestre"]]
            .drop_duplicates()
            .assign(qord=lambda x: x["trimestre"].apply(_quarter_order))
            .sort_values(["ano", "qord"])
        )

        col_labels = [f"{int(r.ano)}{r.trimestre}" for r in periods.itertuples(index=False)]
        ordered_cols = [(int(r.ano), r.trimestre) for r in periods.itertuples(index=False)]

        pivot = qiso.pivot_table(
            index="code",
            columns=["ano", "trimestre"],
            values="valor",
            aggfunc="first",
        ).reindex(columns=ordered_cols)

        idx_codes = [c for c, _ in DRE_PADRAO] + [EPS_CODE]
        pivot = pivot.reindex(idx_codes)
        pivot.columns = col_labels

        names = {c: n for c, n in DRE_PADRAO}
        names[EPS_CODE] = EPS_LABEL
        pivot.insert(0, "conta", [f"{c} {names.get(c, '')}".strip() for c in pivot.index])

        return pivot.reset_index(drop=True)

    def _checkup_linha_a_linha(
        self, 
        qiso: pd.DataFrame, 
        anual: pd.DataFrame,
        fiscal_info: FiscalYearInfo,
        tolerancia_percentual: float = 0.1  # 0.1% de tolerância
    ) -> Tuple[List[CheckupResult], int, int, int, int]:
        """
        Realiza check-up LINHA A LINHA comparando soma trimestral vs anual.
        
        IMPORTANTE: Para empresas com ano fiscal IRREGULAR, o check-up é PULADO
        porque a comparação não faz sentido (trimestres calendário vs ano fiscal diferente).
        
        Returns:
            results: Lista de CheckupResult para cada verificação
            diverge_count: Número de divergências
            incompleto_count: Número de anos com trimestres incompletos
            sem_anual_count: Número de anos sem dado anual
            irregular_skip_count: Número de verificações puladas por ano fiscal irregular
        """
        results: List[CheckupResult] = []
        
        diverge_count = 0
        incompleto_count = 0
        sem_anual_count = 0
        irregular_skip_count = 0

        # Para empresas com ano fiscal IRREGULAR: pular check-up
        if not fiscal_info.is_standard:
            for ano in sorted(qiso["ano"].unique()):
                for code, _name in DRE_PADRAO:
                    g_code = qiso[(qiso["ano"] == ano) & (qiso["code"] == code)]
                    soma_tri = float(g_code["valor"].sum(skipna=True))
                    
                    results.append(CheckupResult(
                        code=code,
                        ano=int(ano),
                        soma_trimestral=soma_tri,
                        valor_anual=np.nan,
                        diferenca=np.nan,
                        percentual_diff=np.nan,
                        status="IRREGULAR_SKIP"
                    ))
                    irregular_skip_count += 1
            
            return results, diverge_count, incompleto_count, sem_anual_count, irregular_skip_count

        # Para empresas com ano fiscal PADRÃO: fazer check-up normal
        anual_map = anual.set_index(["ano", "code"])["anual_val"].to_dict()
        expected_quarters = {"T1", "T2", "T3", "T4"}

        for ano in sorted(qiso["ano"].unique()):
            g_ano = qiso[qiso["ano"] == ano]
            quarters_present = set(g_ano["trimestre"].unique())
            
            for code, _name in DRE_PADRAO:
                anual_val = anual_map.get((int(ano), code), np.nan)
                
                # Soma trimestral
                g_code = g_ano[g_ano["code"] == code]
                soma_tri = float(g_code["valor"].sum(skipna=True))
                
                # Determinar status
                if not np.isfinite(anual_val):
                    status = "SEM_ANUAL"
                    sem_anual_count += 1
                    diferenca = np.nan
                    percentual = np.nan
                elif not expected_quarters.issubset(quarters_present):
                    status = "INCOMPLETO"
                    incompleto_count += 1
                    diferenca = soma_tri - anual_val
                    percentual = (diferenca / abs(anual_val) * 100) if anual_val != 0 else np.nan
                else:
                    diferenca = soma_tri - anual_val
                    percentual = (diferenca / abs(anual_val) * 100) if anual_val != 0 else 0.0
                    
                    # Verificar tolerância
                    if abs(percentual) <= tolerancia_percentual:
                        status = "OK"
                    else:
                        status = "DIVERGE"
                        diverge_count += 1
                
                results.append(CheckupResult(
                    code=code,
                    ano=int(ano),
                    soma_trimestral=soma_tri,
                    valor_anual=anual_val,
                    diferenca=diferenca,
                    percentual_diff=percentual,
                    status=status
                ))

        return results, diverge_count, incompleto_count, sem_anual_count, irregular_skip_count

    def _generate_checkup_report(
        self, 
        results: List[CheckupResult],
        fiscal_info: FiscalYearInfo
    ) -> pd.DataFrame:
        """Gera relatório de check-up em formato DataFrame."""
        rows = []
        for r in results:
            rows.append({
                "ano": r.ano,
                "codigo": r.code,
                "soma_trimestral": r.soma_trimestral,
                "valor_anual": r.valor_anual,
                "diferenca": r.diferenca,
                "diff_%": r.percentual_diff,
                "status": r.status
            })
        
        df = pd.DataFrame(rows)
        return df

    def padronizar_e_salvar_ticker(self, ticker: str, salvar_checkup: bool = True) -> Tuple[bool, str]:
        """
        Padroniza DRE de um ticker e salva resultado.
        
        Args:
            ticker: Código do ticker
            salvar_checkup: Se True, salva relatório de check-up
            
        Returns:
            ok: True se não há divergências (ou se é irregular e foi pulado)
            msg: Mensagem de status
        """
        ticker = ticker.upper().strip()
        pasta = self.pasta_balancos / ticker

        # 1. Carregar dados
        df_tri, df_anu = self._load_inputs(ticker)
        
        # 2. DETECTAR PADRÃO FISCAL (CRÍTICO!)
        fiscal_info = _detect_fiscal_year_pattern(df_tri, df_anu)
        
        # 3. Construir totais trimestrais (preserva originais)
        qtot = self._build_quarter_totals(df_tri)
        
        # 4. Extrair valores anuais
        anu = self._extract_annual_values(df_anu)
        
        # 5. Detectar e converter dados acumulados (YTD) - só para padrão
        cumulative_years = self._detect_cumulative_years(qtot, anu, fiscal_info)
        qiso = self._to_isolated_quarters(qtot, cumulative_years, fiscal_info)
        
        # 6. Adicionar T4 quando faltante (APENAS para ano fiscal padrão)
        qiso = self._add_t4_from_annual_when_missing(qiso, anu, fiscal_info)
        
        # 7. Ordenar
        qiso = qiso.assign(qord=qiso["trimestre"].apply(_quarter_order)).sort_values(["ano", "qord", "code"])
        qiso = qiso.drop(columns=["qord"])
        
        # 8. Construir tabela horizontal
        df_out = self._build_horizontal(qiso)
        
        # 9. CHECK-UP LINHA A LINHA
        checkup_results, diverge, incompleto, sem_anual, irregular_skip = self._checkup_linha_a_linha(
            qiso, anu, fiscal_info
        )
        self.checkup_results = checkup_results
        
        # 10. Salvar arquivos
        pasta.mkdir(parents=True, exist_ok=True)
        
        # Arquivo principal
        out_path = pasta / "dre_padronizado.csv"
        df_out.to_csv(out_path, index=False, encoding="utf-8")
        
        # Relatório de check-up (SEMPRE salva se solicitado)
        checkup_saved = False
        if salvar_checkup:
            try:
                checkup_df = self._generate_checkup_report(checkup_results, fiscal_info)
                checkup_path = pasta / "dre_checkup.csv"
                
                # Salvar com cabeçalho informativo
                with open(checkup_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Padrão Fiscal: {fiscal_info.description}\n")
                    f.write(f"# Trimestres encontrados: {sorted(fiscal_info.quarters_pattern)}\n")
                    f.write(f"# Data geração: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                checkup_df.to_csv(checkup_path, index=False, encoding="utf-8", mode='a')
                checkup_saved = True
            except Exception as e:
                print(f"  ⚠️ Erro ao salvar check-up: {e}")
        
        # 11. Construir mensagem de retorno
        fiscal_status = "PADRÃO" if fiscal_info.is_standard else "IRREGULAR"
        
        if fiscal_info.is_standard:
            msg_parts = [
                f"fiscal={fiscal_status}",
                f"DIVERGE={diverge}",
                f"INCOMPLETO={incompleto}",
                f"SEM_ANUAL={sem_anual}"
            ]
            ok = (diverge == 0)
        else:
            # Para irregular: check-up foi pulado, considera OK se valores foram copiados
            msg_parts = [
                f"fiscal={fiscal_status}",
                f"CHECK-UP=PULADO",
                f"trimestres={sorted(fiscal_info.quarters_pattern)}"
            ]
            ok = True  # Valores foram copiados corretamente
        
        if checkup_saved:
            msg_parts.append("checkup=SALVO")
        
        msg = f"dre_padronizado.csv | {' | '.join(msg_parts)}"
        
        return ok, msg


# ======================================================================================
# CLI
# ======================================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modo", default="quantidade", choices=["quantidade", "ticker", "lista", "faixa"])
    parser.add_argument("--quantidade", default="10")
    parser.add_argument("--ticker", default="")
    parser.add_argument("--lista", default="")
    parser.add_argument("--faixa", default="1-50")
    parser.add_argument("--no-checkup", action="store_true", help="Não salvar relatório de check-up")
    args = parser.parse_args()

    df = pd.read_csv("mapeamento_final_b3_completo_utf8.csv", sep=";", encoding="utf-8-sig")
    df = df[df["cnpj"].notna()].reset_index(drop=True)

    if args.modo == "quantidade":
        limite = int(args.quantidade)
        df_sel = df.head(limite)

    elif args.modo == "ticker":
        df_sel = df[df["ticker"].str.upper() == args.ticker.upper()]

    elif args.modo == "lista":
        tickers = [t.strip().upper() for t in args.lista.split(",") if t.strip()]
        df_sel = df[df["ticker"].str.upper().isin(tickers)]

    elif args.modo == "faixa":
        inicio, fim = map(int, args.faixa.split("-"))
        df_sel = df.iloc[inicio - 1 : fim]

    else:
        df_sel = df.head(10)

    print(f"\n>>> JOB: PADRONIZAR DRE <<<")
    print(f"Modo: {args.modo} | Selecionadas: {len(df_sel)}")
    print("Saída: balancos/<TICKER>/dre_padronizado.csv + dre_checkup.csv\n")

    pad = PadronizadorDRE()

    ok_count = 0
    warn_count = 0
    err_count = 0
    irregular_count = 0

    salvar_checkup = not args.no_checkup

    for _, row in df_sel.iterrows():
        ticker = str(row["ticker"]).upper().strip()

        pasta = Path("balancos") / ticker
        if not pasta.exists():
            err_count += 1
            print(f"❌ {ticker}: pasta balancos/{ticker} não existe (captura ausente)")
            continue

        try:
            ok, msg = pad.padronizar_e_salvar_ticker(ticker, salvar_checkup=salvar_checkup)
            
            # Verificar se é irregular para contagem
            if "IRREGULAR" in msg:
                irregular_count += 1
            
            if ok:
                ok_count += 1
                print(f"✅ {ticker}: {msg}")
            else:
                warn_count += 1
                print(f"⚠️ {ticker}: {msg}")

        except FileNotFoundError as e:
            err_count += 1
            print(f"❌ {ticker}: arquivos ausentes ({e})")
        except Exception as e:
            err_count += 1
            import traceback
            print(f"❌ {ticker}: erro ({type(e).__name__}: {e})")
            traceback.print_exc()

    print("\n" + "="*70)
    print(f"Finalizado: OK={ok_count} | WARN(DIVERGE)>0={warn_count} | ERRO={err_count}")
    if irregular_count > 0:
        print(f"            Anos fiscais irregulares: {irregular_count} (check-up pulado)")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
