# src/padronizar_dfc.py
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd


# ======================================================================================
# CONTAS DFC - PADRÃO PARA TODAS AS EMPRESAS
# ======================================================================================

DFC_CONTAS: List[Tuple[str, str]] = [
    ("6.01", "Caixa Líquido das Atividades Operacionais"),
    ("6.02", "Caixa Líquido Atividades de Investimento"),
    ("6.03", "Caixa Líquido Atividades de Financiamento"),
    ("6.04", "Variação Cambial s/ Caixa e Equivalentes"),
    ("6.05", "Aumento (Redução) de Caixa e Equivalentes"),
]

# Código especial para Depreciação e Amortização (subconta de 6.01)
DEPREC_CODE = "6.01.DA"
DEPREC_LABEL = "Depreciação e Amortização"


# ======================================================================================
# TICKERS DE BANCOS E SEGURADORAS (NÃO incluem D&A)
# ======================================================================================

TICKERS_BANCOS: Set[str] = {
    "RPAD3", "RPAD5", "RPAD6",
    "ABCB4",
    "BMGB4",
    "BBDC3", "BBDC4",
    "BPAC3", "BPAC5", "BPAC11",
    "BSLI3", "BSLI4",
    "BBAS3",
    "BGIP3", "BGIP4",
    "BPAR3",
    "BRSR3", "BRSR5", "BRSR6",
    "BNBR3",
    "BMIN3", "BMIN4",
    "BMEB3", "BMEB4",
    "BPAN4",
    "PINE3", "PINE4",
    "SANB3", "SANB4", "SANB11",
    "BEES3", "BEES4",
    "ITUB3", "ITUB4",
}

TICKERS_HOLDINGS_SEGUROS: Set[str] = {
    "BBSE3",
    "CXSE3",
}

TICKERS_SEGURADORAS: Set[str] = {
    "IRBR3",
    "PSSA3",
}


def _is_financeira_ou_seguradora(ticker: str) -> bool:
    """
    Verifica se o ticker é banco, holding de seguros ou seguradora.
    Essas empresas NÃO incluem Depreciação e Amortização no DFC padronizado.
    """
    t = ticker.upper().strip()
    return t in TICKERS_BANCOS or t in TICKERS_HOLDINGS_SEGUROS or t in TICKERS_SEGURADORAS


# ======================================================================================
# UTILITÁRIOS
# ======================================================================================

def _to_datetime(df: pd.DataFrame, col: str = "data_fim") -> pd.Series:
    return pd.to_datetime(df[col], errors="coerce")


def _ensure_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype(float)


def _quarter_order(q: str) -> int:
    return {"T1": 1, "T2": 2, "T3": 3, "T4": 4}.get(q, 99)


def _normalize_value(v: float, decimals: int = 3) -> float:
    """Normaliza valor numérico para evitar erros de ponto flutuante."""
    if not np.isfinite(v):
        return np.nan
    return round(float(v), decimals)


def _pick_value_for_code(group: pd.DataFrame, code: str) -> float:
    """Extrai valor para um código, buscando conta exata ou somando filhas."""
    exact = group[group["cd_conta"] == code]
    if not exact.empty:
        v = _ensure_numeric(exact["valor_mil"]).sum()
        return float(v) if np.isfinite(v) else np.nan

    children = group[group["cd_conta"].astype(str).str.startswith(code + ".")]
    if children.empty:
        return np.nan
    v = _ensure_numeric(children["valor_mil"]).sum()
    return float(v) if np.isfinite(v) else np.nan


# ======================================================================================
# EXTRAÇÃO DE DEPRECIAÇÃO E AMORTIZAÇÃO
# ======================================================================================

# Padrões para identificar contas de Depreciação e/ou Amortização
# Considera variações de escrita e acentuação
DEPREC_PATTERNS = [
    r"deprecia[çc][aã]o\s*(e|ou)?\s*amortiza[çc][aã]o",  # Depreciação e Amortização
    r"amortiza[çc][aã]o\s*(e|ou)?\s*deprecia[çc][aã]o",  # Amortização e Depreciação
    r"^deprecia[çc][oõ]es?\s*$",                          # Depreciação / Depreciações
    r"^amortiza[çc][oõ]es?\s*$",                          # Amortização / Amortizações
    r"^deprecia[çc][aã]o\s*$",                            # Depreciação
    r"^amortiza[çc][aã]o\s*$",                            # Amortização
    r"deprec\.\s*(e|ou)?\s*amort\.",                      # Deprec. e Amort.
    r"d&a",                                                # D&A
    r"deprec\s*/\s*amort",                                # Deprec / Amort
]

# Compilar regex com flag IGNORECASE
DEPREC_REGEX = [re.compile(p, re.IGNORECASE) for p in DEPREC_PATTERNS]


def _is_deprec_amort_account(ds_conta: str) -> bool:
    """
    Verifica se o nome da conta corresponde a Depreciação e/ou Amortização.
    """
    ds_clean = ds_conta.strip()
    for regex in DEPREC_REGEX:
        if regex.search(ds_clean):
            return True
    return False


def _compute_deprec_amort_value(group: pd.DataFrame) -> float:
    """
    Calcula o valor de Depreciação e Amortização para um período.
    
    Regras:
    1. Busca dentro de 6.01 (subcontas de Caixa Operacional)
    2. Identifica contas pelo nome usando padrões inteligentes
    3. Soma todos os valores encontrados (quando separadas)
    4. Retorna NaN se nenhuma conta encontrada
    """
    # Filtrar apenas subcontas de 6.01
    subcontas_601 = group[group["cd_conta"].astype(str).str.startswith("6.01.")]
    
    if subcontas_601.empty:
        return np.nan
    
    # Identificar contas de D&A pelo nome
    mask = subcontas_601["ds_conta"].apply(_is_deprec_amort_account)
    deprec_rows = subcontas_601[mask]
    
    if deprec_rows.empty:
        return np.nan
    
    # Somar todos os valores encontrados
    total = _ensure_numeric(deprec_rows["valor_mil"]).sum()
    
    return float(total) if np.isfinite(total) else np.nan


# ======================================================================================
# DETECTOR DE ANO FISCAL IRREGULAR
# ======================================================================================

@dataclass
class FiscalYearInfo:
    """Informações sobre o padrão de ano fiscal da empresa."""
    is_standard: bool
    fiscal_end_month: int
    quarters_pattern: Set[str]
    has_all_quarters: bool
    description: str


def _detect_fiscal_year_pattern(df_tri: pd.DataFrame, df_anu: pd.DataFrame) -> FiscalYearInfo:
    """
    Detecta o padrão de ano fiscal da empresa.
    """
    quarters_found = set(df_tri["trimestre"].dropna().unique())
    
    # Verificar meses de encerramento dos dados anuais
    if "data_fim" in df_anu.columns and not df_anu.empty:
        end_months = df_anu["data_fim"].dropna().dt.month.unique()
        
        # Se todos os encerramentos anuais são em dezembro = ano fiscal padrão
        if len(end_months) == 1 and end_months[0] == 12:
            fiscal_end = 12
            is_standard = True
        elif len(end_months) >= 1:
            # Pegar o mês mais comum
            fiscal_end = int(df_anu["data_fim"].dt.month.mode().iloc[0]) if not df_anu["data_fim"].dt.month.mode().empty else 12
            is_standard = (fiscal_end == 12)
        else:
            fiscal_end = 12
            is_standard = True
    else:
        fiscal_end = 12
        is_standard = True
    
    has_all = {"T1", "T2", "T3", "T4"}.issubset(quarters_found)
    
    if is_standard:
        desc = "Ano fiscal padrão (jan-dez)"
    else:
        desc = f"Ano fiscal irregular (encerra em mês {fiscal_end})"
    
    return FiscalYearInfo(
        is_standard=is_standard,
        fiscal_end_month=fiscal_end,
        quarters_pattern=quarters_found,
        has_all_quarters=has_all,
        description=desc
    )


# ======================================================================================
# CLASSE PRINCIPAL - PADRONIZADOR DFC
# ======================================================================================

@dataclass
class PadronizadorDFC:
    pasta_balancos: Path = Path("balancos")
    _current_ticker: str = field(default="", repr=False)
    
    def _include_deprec_amort(self) -> bool:
        """Retorna True se deve incluir D&A (empresas não-financeiras)."""
        return not _is_financeira_ou_seguradora(self._current_ticker)
    
    def _get_dfc_schema(self) -> List[Tuple[str, str]]:
        """Retorna o esquema DFC para o ticker atual."""
        schema = list(DFC_CONTAS)
        if self._include_deprec_amort():
            # Inserir D&A logo após 6.01
            schema.insert(1, (DEPREC_CODE, DEPREC_LABEL))
        return schema

    def _load_inputs(self, ticker: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Carrega arquivos DFC trimestral e anual."""
        pasta = self.pasta_balancos / ticker.upper().strip()
        tri_path = pasta / "dfc_consolidado.csv"
        anu_path = pasta / "dfc_anual.csv"

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
        """
        target_codes = [c for c, _ in DFC_CONTAS]
        wanted_prefixes = tuple([c + "." for c in target_codes])

        mask = (
            df_tri["cd_conta"].isin(target_codes)
            | df_tri["cd_conta"].astype(str).str.startswith(wanted_prefixes)
        )
        df = df_tri[mask].copy()
        df["ano"] = df["data_fim"].dt.year
        
        rows = []
        for (ano, trimestre), g in df.groupby(["ano", "trimestre"], sort=False):
            # Contas padrão DFC
            for code, _name in DFC_CONTAS:
                v = _pick_value_for_code(g, code)
                rows.append((int(ano), str(trimestre), code, v))
            
            # Depreciação e Amortização (se aplicável)
            if self._include_deprec_amort():
                deprec_val = _compute_deprec_amort_value(g)
                rows.append((int(ano), str(trimestre), DEPREC_CODE, deprec_val))

        return pd.DataFrame(rows, columns=["ano", "trimestre", "code", "valor"])

    def _extract_annual_values(self, df_anu: pd.DataFrame) -> pd.DataFrame:
        """Extrai valores anuais para cálculo do T4."""
        target_codes = [c for c, _ in DFC_CONTAS]
        wanted_prefixes = tuple([c + "." for c in target_codes])

        mask = (
            df_anu["cd_conta"].isin(target_codes)
            | df_anu["cd_conta"].astype(str).str.startswith(wanted_prefixes)
        )
        df = df_anu[mask].copy()
        df["ano"] = df["data_fim"].dt.year

        rows = []
        for ano, g in df.groupby("ano", sort=False):
            for code, _name in DFC_CONTAS:
                v = _pick_value_for_code(g, code)
                rows.append((int(ano), code, v))
            
            if self._include_deprec_amort():
                deprec_val = _compute_deprec_amort_value(g)
                rows.append((int(ano), DEPREC_CODE, deprec_val))

        return pd.DataFrame(rows, columns=["ano", "code", "anual_val"])

    def _detect_cumulative_years(
        self,
        qtot: pd.DataFrame,
        anual: pd.DataFrame,
        fiscal_info: FiscalYearInfo,
        base_code_for_detection: str = "6.01",
        ratio_threshold: float = 1.10,
    ) -> Dict[int, bool]:
        """
        Detecta se o trimestral está acumulado (YTD) por ano.
        """
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
        """
        out_rows = []

        for (ano, code), g in qtot.groupby(["ano", "code"], sort=False):
            g = g.copy()
            g["qord"] = g["trimestre"].apply(_quarter_order)
            g = g.sort_values("qord")

            vals = g["valor"].values.astype(float)
            qs = g["trimestre"].tolist()

            # Converter se ano acumulado e empresa padrão
            if (cumulative_years.get(int(ano), False) and fiscal_info.is_standard):
                qords = g["qord"].values
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
        Adiciona T4 calculado quando faltante.
        T4 = Anual - (T1 + T2 + T3)
        """
        if not fiscal_info.is_standard:
            return qiso
        
        anual_map = anual.set_index(["ano", "code"])["anual_val"].to_dict()
        out = qiso.copy()

        # Lista de códigos a processar
        all_codes = [c for c, _ in DFC_CONTAS]
        if self._include_deprec_amort():
            all_codes.append(DEPREC_CODE)

        for ano in sorted(out["ano"].unique()):
            g = out[out["ano"] == ano]
            quarters = set(g["trimestre"].unique())

            if "T4" in quarters:
                continue
            if not {"T1", "T2", "T3"}.issubset(quarters):
                continue

            new_rows = []
            for code in all_codes:
                a = anual_map.get((int(ano), code), np.nan)
                if not np.isfinite(a):
                    continue
                s = g[(g["code"] == code) & (g["trimestre"].isin(["T1", "T2", "T3"]))]["valor"].sum(skipna=True)
                t4_val = float(a - s)
                new_rows.append((int(ano), "T4", code, t4_val))

            if new_rows:
                out = pd.concat([out, pd.DataFrame(new_rows, columns=out.columns)], ignore_index=True)

        return out

    def _build_horizontal(self, qiso: pd.DataFrame) -> pd.DataFrame:
        """
        Constrói tabela horizontal (períodos como colunas).
        """
        dfc_schema = self._get_dfc_schema()
        
        qiso = qiso.copy()
        qiso["periodo"] = qiso["ano"].astype(str) + qiso["trimestre"]
        qiso["valor"] = qiso["valor"].apply(lambda x: _normalize_value(x, 3))

        piv = qiso.pivot_table(
            index="code", columns="periodo", values="valor", aggfunc="first"
        )

        # Ordenar colunas cronologicamente
        def sort_key(p):
            try:
                return (int(p[:4]), _quarter_order(p[4:]))
            except:
                return (9999, 99)

        cols = sorted(piv.columns, key=sort_key)
        piv = piv[cols]

        # Ordenar linhas pelo esquema
        code_order = {c: i for i, (c, _) in enumerate(dfc_schema)}
        piv = piv.reindex(sorted(piv.index, key=lambda x: code_order.get(x, 999)))

        # Adicionar nomes das contas
        code_to_name = {c: n for c, n in dfc_schema}
        piv.insert(0, "conta", piv.index.map(lambda x: code_to_name.get(x, x)))
        piv = piv.reset_index().rename(columns={"code": "cd_conta"})

        return piv

    def padronizar_e_salvar_ticker(self, ticker: str) -> Tuple[bool, str]:
        """
        Pipeline completo de padronização do DFC.
        """
        self._current_ticker = ticker.upper().strip()
        
        # 1. Carregar dados
        df_tri, df_anu = self._load_inputs(ticker)
        
        # 2. Detectar padrão fiscal
        fiscal_info = _detect_fiscal_year_pattern(df_tri, df_anu)
        
        # 3. Construir totais trimestrais
        qtot = self._build_quarter_totals(df_tri)
        
        # 4. Extrair valores anuais
        anual = self._extract_annual_values(df_anu)
        
        # 5. Detectar anos acumulados
        cumulative_years = self._detect_cumulative_years(qtot, anual, fiscal_info)
        
        # 6. Converter para trimestres isolados
        qiso = self._to_isolated_quarters(qtot, cumulative_years, fiscal_info)
        
        # 7. Adicionar T4 quando faltante
        qiso = self._add_t4_from_annual_when_missing(qiso, anual, fiscal_info)
        
        # 8. Construir tabela horizontal
        df_out = self._build_horizontal(qiso)
        
        # 9. Salvar
        pasta = self.pasta_balancos / ticker.upper().strip()
        out_path = pasta / "dfc_padronizado.csv"
        df_out.to_csv(out_path, index=False, encoding="utf-8")
        
        # 10. Mensagem de retorno
        fiscal_status = "PADRÃO" if fiscal_info.is_standard else "IRREGULAR"
        tipo = "FINANCEIRA" if _is_financeira_ou_seguradora(ticker) else "GERAL"
        
        n_periodos = len([c for c in df_out.columns if c not in ["cd_conta", "conta"]])
        
        msg_parts = [
            f"Fiscal: {fiscal_status}",
            f"Tipo: {tipo}",
            f"Períodos: {n_periodos}",
        ]
        
        if self._include_deprec_amort():
            # Verificar se encontrou D&A
            has_deprec = not df_out[df_out["cd_conta"] == DEPREC_CODE].empty
            if has_deprec:
                deprec_row = df_out[df_out["cd_conta"] == DEPREC_CODE].iloc[0]
                non_null = sum(1 for c in df_out.columns if c not in ["cd_conta", "conta"] and pd.notna(deprec_row[c]))
                msg_parts.append(f"D&A: {non_null} períodos")
            else:
                msg_parts.append("D&A: não encontrada")
        
        msg = f"dfc_padronizado.csv | {' | '.join(msg_parts)}"
        
        return True, msg


# ======================================================================================
# CLI - MAIN
# ======================================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Padroniza DFC das empresas (trimestres isolados + T4)"
    )
    parser.add_argument(
        "--modo",
        choices=["quantidade", "ticker", "lista", "faixa"],
        default="quantidade",
        help="Modo de seleção: quantidade, ticker, lista, faixa",
    )
    parser.add_argument("--quantidade", default="10", help="Quantidade de empresas")
    parser.add_argument("--ticker", default="", help="Ticker específico")
    parser.add_argument("--lista", default="", help="Lista de tickers separados por vírgula")
    parser.add_argument("--faixa", default="", help="Faixa de linhas: inicio-fim (ex: 1-50)")
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

    print(f"\n>>> JOB: PADRONIZAR DFC <<<")
    print(f"Modo: {args.modo} | Selecionadas: {len(df_sel)}")
    print("Saída: balancos/<TICKER>/dfc_padronizado.csv\n")

    pad = PadronizadorDFC()

    ok_count = 0
    err_count = 0
    irregular_count = 0

    for _, row in df_sel.iterrows():
        ticker = str(row["ticker"]).upper().strip()

        pasta = Path("balancos") / ticker
        if not pasta.exists():
            err_count += 1
            print(f"❌ {ticker}: pasta balancos/{ticker} não existe")
            continue

        try:
            ok, msg = pad.padronizar_e_salvar_ticker(ticker)
            
            if "IRREGULAR" in msg:
                irregular_count += 1
            
            if ok:
                ok_count += 1
                print(f"✅ {ticker}: {msg}")
            else:
                err_count += 1
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
    print(f"Finalizado: OK={ok_count} | ERRO={err_count}")
    if irregular_count > 0:
        print(f"            Anos fiscais irregulares: {irregular_count}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
