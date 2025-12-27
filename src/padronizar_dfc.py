# src/padronizar_dfc.py
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

# ADICIONAR NO TOPO DO ARQUIVO (após outros imports):
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from multi_ticker_utils import get_ticker_principal, get_pasta_balanco, load_mapeamento_consolidado

# ======================================================================================
# EMPRESAS COM ANO FISCAL ESPECIAL (MARÇO-FEVEREIRO)
# ======================================================================================

TICKERS_ANO_FISCAL_MAR_FEV: Set[str] = {
    "CAML3",  # Camil Alimentos - ano fiscal Março-Fevereiro
}


def _is_ano_fiscal_mar_fev(ticker: str) -> bool:
    """Verifica se empresa tem ano fiscal Março-Fevereiro."""
    return ticker.upper().strip() in TICKERS_ANO_FISCAL_MAR_FEV


def _map_fiscal_month_to_quarter(ticker: str, mes: int) -> Optional[str]:
    """
    Mapeia mês de encerramento para trimestre padrão.
    
    Para empresas com ano fiscal Março-Fevereiro (CAML3):
    - Maio (5) → T1
    - Agosto (8) → T2
    - Novembro (11) → T3
    - Fevereiro (2) → T4
    """
    if not _is_ano_fiscal_mar_fev(ticker):
        return None
    
    mapping = {5: "T1", 8: "T2", 11: "T3", 2: "T4"}
    return mapping.get(mes)


def _adjust_fiscal_year(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Ajusta o ano para ano fiscal (não calendário) para empresas com ano fiscal Março-Fevereiro.
    
    Para CAML3:
    - Meses Mar-Dez (3-12): ano_fiscal = ano_calendário + 1
    - Meses Jan-Fev (1-2): ano_fiscal = ano_calendário
    
    Exemplo:
    - Mai/2025 (mês 5) → ano fiscal 2026
    - Nov/2025 (mês 11) → ano fiscal 2026
    - Fev/2026 (mês 2) → ano fiscal 2026
    - Mai/2026 (mês 5) → ano fiscal 2027
    """
    if not _is_ano_fiscal_mar_fev(ticker):
        return df
    
    df = df.copy()
    # Para meses >= 3 (Mar-Dez): adiciona 1 ao ano
    mask = df["data_fim"].dt.month >= 3
    df.loc[mask, "ano"] = df.loc[mask, "ano"] + 1
    
    return df


# ======================================================================================
# CONTAS DFC PADRÃO (NÃO FINANCEIRAS)
# ======================================================================================

DFC_PADRAO: List[Tuple[str, str]] = [
    ("6.01", "Caixa Líquido Atividades Operacionais"),
    ("6.01.01", "Caixa Gerado nas Operações"),
    ("6.01.02", "Variações nos Ativos e Passivos"),
    ("6.02", "Caixa Líquido Atividades de Investimento"),
    ("6.03", "Caixa Líquido Atividades de Financiamento"),
    ("6.05", "Variação Cambial s/ Caixa e Equivalentes"),
    ("6.05.01", "Aumento (Redução) de Caixa e Equivalentes"),
    ("6.05.02", "Saldo Inicial de Caixa e Equivalentes"),
    ("6.05.03", "Saldo Final de Caixa e Equivalentes"),
]

# ======================================================================================
# CONTAS DFC BANCOS
# ======================================================================================

DFC_BANCOS: List[Tuple[str, str]] = [
    ("6.01", "Atividades Operacionais"),
    ("6.01.01", "Caixa Gerado nas Operações"),
    ("6.01.02", "Variações nos Ativos e Passivos"),
    ("6.02", "Atividades de Investimento"),
    ("6.03", "Atividades de Financiamento"),
    ("6.05", "Aumento (Redução) de Caixa e Equivalentes"),
    ("6.05.01", "Saldo Inicial de Caixa e Equivalentes"),
    ("6.05.02", "Saldo Final de Caixa e Equivalentes"),
]

# ======================================================================================
# CONTAS DFC HOLDINGS SEGUROS
# ======================================================================================

DFC_HOLDINGS_SEGUROS: List[Tuple[str, str]] = [
    ("6.01", "Caixa Líquido Atividades Operacionais"),
    ("6.01.01", "Caixa Gerado nas Operações"),
    ("6.01.02", "Variações nos Ativos e Passivos"),
    ("6.02", "Caixa Líquido Atividades de Investimento"),
    ("6.03", "Caixa Líquido Atividades de Financiamento"),
    ("6.05", "Aumento (Redução) de Caixa e Equivalentes"),
    ("6.05.01", "Saldo Inicial de Caixa e Equivalentes"),
    ("6.05.02", "Saldo Final de Caixa e Equivalentes"),
]

# ======================================================================================
# CONTAS DFC SEGURADORAS
# ======================================================================================

DFC_SEGURADORAS: List[Tuple[str, str]] = [
    ("6.01", "Das Atividades Operacionais"),
    ("6.01.01", "Lucro Líquido Ajustado"),
    ("6.01.02", "Variações nos Ativos e Passivos"),
    ("6.02", "Das Atividades de Investimento"),
    ("6.03", "Das Atividades de Financiamento"),
    ("6.05", "Aumento (Redução) de Caixa e Equivalentes de Caixa"),
    ("6.05.01", "Saldo Inicial de Caixa e Equivalentes de Caixa"),
    ("6.05.02", "Saldo Final de Caixa e Equivalentes de Caixa"),
]

# Listas de tickers
TICKERS_BANCOS: Set[str] = {
    "RPAD3", "RPAD5", "RPAD6", "ABCB4", "BMGB4", "BBDC3", "BBDC4",
    "BPAC3", "BPAC5", "BPAC11", "BSLI3", "BSLI4", "BBAS3", "BGIP3",
    "BGIP4", "BPAR3", "BRSR3", "BRSR5", "BRSR6", "BNBR3", "BMIN3",
    "BMIN4", "BMEB3", "BMEB4", "BPAN4", "PINE3", "PINE4", "SANB3",
    "SANB4", "SANB11", "BEES3", "BEES4", "ITUB3", "ITUB4",
}

TICKERS_HOLDINGS_SEGUROS: Set[str] = {"BBSE3", "CXSE3"}
TICKERS_SEGURADORAS: Set[str] = {"IRBR3", "PSSA3"}


def _is_banco(ticker: str) -> bool:
    return ticker.upper().strip() in TICKERS_BANCOS


def _is_holding_seguros(ticker: str) -> bool:
    return ticker.upper().strip() in TICKERS_HOLDINGS_SEGUROS


def _is_seguradora(ticker: str) -> bool:
    return ticker.upper().strip() in TICKERS_SEGURADORAS


def _get_dfc_schema(ticker: str) -> List[Tuple[str, str]]:
    ticker_upper = ticker.upper().strip()
    if _is_holding_seguros(ticker_upper):
        return DFC_HOLDINGS_SEGUROS
    elif _is_seguradora(ticker_upper):
        return DFC_SEGURADORAS
    elif _is_banco(ticker_upper):
        return DFC_BANCOS
    else:
        return DFC_PADRAO


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
    exact = group[group["cd_conta"] == base_code]
    if not exact.empty:
        v = _ensure_numeric(exact["valor_mil"]).sum()
        return float(v) if np.isfinite(v) else np.nan

    children = group[group["cd_conta"].astype(str).str.startswith(base_code + ".")]
    if children.empty:
        return np.nan
    v = _ensure_numeric(children["valor_mil"]).sum()
    return float(v) if np.isfinite(v) else np.nan


# ======================================================================================
# DETECTOR DE YTD (DADOS ACUMULADOS)
# ======================================================================================

def _detect_ytd_years(
    qtot: pd.DataFrame,
    anual: pd.DataFrame,
    base_code_for_detection: str = "6.01",
    ratio_threshold: float = 1.10,
) -> Dict[int, bool]:
    """
    Detecta se dados trimestrais estão em formato YTD (acumulado no ano).
    
    Compara soma dos trimestres vs valor anual:
    - Se soma >> anual (>10%): dados estão acumulados (YTD)
    - Se soma ≈ anual: dados estão isolados
    
    IMPORTANTE: Retorna dict vazio se não houver dados anuais.
    """
    anual_map = anual.set_index(["ano", "code"])["anual_val"].to_dict()
    out: Dict[int, bool] = {}

    for ano, g in qtot[qtot["code"] == base_code_for_detection].groupby("ano"):
        a = anual_map.get((int(ano), base_code_for_detection), np.nan)
        if not np.isfinite(a) or a == 0:
            continue
        s = float(np.nansum(g["valor"].values))
        
        # Se soma é muito maior que anual: YTD
        out[int(ano)] = bool(np.isfinite(s) and abs(s) > abs(a) * ratio_threshold)

    return out


def _to_isolated_quarters(qtot: pd.DataFrame, ytd_years: Dict[int, bool]) -> pd.DataFrame:
    """
    Converte dados YTD (acumulados) para trimestres isolados quando necessário.
    
    Para cada ano detectado como YTD:
    - T1 = T1_ytd
    - T2 = T2_ytd - T1_ytd
    - T3 = T3_ytd - T2_ytd
    - T4 = T4_ytd - T3_ytd
    """
    out_rows = []

    for (ano, code), g in qtot.groupby(["ano", "code"], sort=False):
        g = g.copy()
        g["qord"] = g["trimestre"].apply(_quarter_order)
        g = g.sort_values("qord")

        vals = g["valor"].values.astype(float)
        qs = g["trimestre"].tolist()

        # Converter apenas se ano foi detectado como YTD
        if ytd_years.get(int(ano), False):
            qords = g["qord"].values
            # Só converte se for sequência contínua
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


# ======================================================================================
# PADRONIZADOR DFC
# ======================================================================================

class PadronizadorDFC:
    def __init__(self, pasta_balancos: Path = Path("balancos")):
        self.pasta_balancos = pasta_balancos
        self._current_ticker: str = ""

    def _load_inputs(self, ticker: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        pasta = get_pasta_balanco(ticker)
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

        # MAPEAMENTO DE TRIMESTRES PARA ANO FISCAL ESPECIAL
        if _is_ano_fiscal_mar_fev(ticker):
            df_tri["trimestre"] = df_tri.apply(
                lambda row: _map_fiscal_month_to_quarter(ticker, row["data_fim"].month) 
                if pd.notna(row["data_fim"]) else row.get("trimestre"),
                axis=1
            )

        return df_tri, df_anu

    def _build_quarter_totals(self, df_tri: pd.DataFrame) -> pd.DataFrame:
        dfc_schema = _get_dfc_schema(self._current_ticker)
        target_codes = [c for c, _ in dfc_schema]
        wanted_prefixes = tuple([c + "." for c in target_codes])

        mask = (
            df_tri["cd_conta"].isin(target_codes)
            | df_tri["cd_conta"].astype(str).str.startswith(wanted_prefixes)
        )
        df = df_tri[mask].copy()
        
        # CRITICAL: Usar ano calendário primeiro, depois ajustar para fiscal se necessário
        df["ano"] = df["data_fim"].dt.year
        
        # AJUSTE DE ANO FISCAL para empresas Março-Fevereiro
        df = _adjust_fiscal_year(df, self._current_ticker)

        rows = []
        for (ano, trimestre), g in df.groupby(["ano", "trimestre"], sort=False):
            for code, _name in dfc_schema:
                v = _pick_value_for_base_code(g, code)
                rows.append((int(ano), str(trimestre), code, v))

        return pd.DataFrame(rows, columns=["ano", "trimestre", "code", "valor"])

    def _extract_annual_values(self, df_anu: pd.DataFrame) -> pd.DataFrame:
        dfc_schema = _get_dfc_schema(self._current_ticker)
        target_codes = [c for c, _ in dfc_schema]
        wanted_prefixes = tuple([c + "." for c in target_codes])

        mask = (
            df_anu["cd_conta"].isin(target_codes)
            | df_anu["cd_conta"].astype(str).str.startswith(wanted_prefixes)
        )
        df = df_anu[mask].copy()
        
        # CRITICAL: Usar ano calendário primeiro, depois ajustar para fiscal se necessário
        df["ano"] = df["data_fim"].dt.year
        
        # AJUSTE DE ANO FISCAL para empresas Março-Fevereiro
        df = _adjust_fiscal_year(df, self._current_ticker)

        rows = []
        for ano, g in df.groupby("ano", sort=False):
            for code, _name in dfc_schema:
                v = _pick_value_for_base_code(g, code)
                rows.append((int(ano), code, v))

        return pd.DataFrame(rows, columns=["ano", "code", "anual_val"])

    def _add_t4_from_annual_when_missing(self, qiso: pd.DataFrame, anual: pd.DataFrame) -> pd.DataFrame:
        """
        PARA DFC: T4 = Anual - (T1 + T2 + T3)
        DFC é fluxo de caixa, portanto acumulado.
        """
        dfc_schema = _get_dfc_schema(self._current_ticker)
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
            for code, _ in dfc_schema:
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
        dfc_schema = _get_dfc_schema(self._current_ticker)
        
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

        idx_codes = [c for c, _ in dfc_schema]
        pivot = pivot.reindex(idx_codes)
        pivot.columns = col_labels

        names = {c: n for c, n in dfc_schema}
        pivot.insert(0, "ds_conta", [names.get(c, '') for c in pivot.index])
        pivot.insert(0, "cd_conta", [str(c) for c in pivot.index])

        return pivot.reset_index(drop=True)

    def padronizar_e_salvar_ticker(self, ticker: str) -> Tuple[bool, str]:
        ticker = ticker.upper().strip()
        self._current_ticker = ticker
        pasta = get_pasta_balanco(ticker)

        df_tri, df_anu = self._load_inputs(ticker)

        qtot = self._build_quarter_totals(df_tri)
        anu = self._extract_annual_values(df_anu)

        ytd_years = _detect_ytd_years(qtot, anu)
        qiso = _to_isolated_quarters(qtot, ytd_years)

        qiso = self._add_t4_from_annual_when_missing(qiso, anu)

        qiso = qiso.assign(qord=qiso["trimestre"].apply(_quarter_order)).sort_values(["ano", "qord", "code"])
        qiso = qiso.drop(columns=["qord"])

        df_out = self._build_horizontal(qiso)

        pasta.mkdir(parents=True, exist_ok=True)
        out_path = pasta / "dfc_padronizado.csv"
        df_out.to_csv(out_path, index=False, encoding="utf-8")

        tipo_dfc = "BANCO" if _is_banco(ticker) else "HOLDING_SEG" if _is_holding_seguros(ticker) else "SEGURADORA" if _is_seguradora(ticker) else "PADRÃO"
        
        msg_parts = [f"tipo={tipo_dfc}"]
        if _is_ano_fiscal_mar_fev(ticker):
            msg_parts.append("(Mar-Fev)")
        
        msg = f"dfc_padronizado.csv | {' | '.join(msg_parts)}"
        
        return True, msg


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
    args = parser.parse_args()

    df = load_mapeamento_consolidado()
    df = df[df["cnpj"].notna()].reset_index(drop=True)

    if args.modo == "quantidade":
        limite = int(args.quantidade)
        df_sel = df.head(limite)
    elif args.modo == "ticker":
        ticker_upper = args.ticker.upper()
        df_sel = df[df["ticker"].str.upper().str.contains(ticker_upper, case=False, na=False, regex=False)]
    elif args.modo == "lista":
        tickers = [t.strip().upper() for t in args.lista.split(",") if t.strip()]
        mask = df["ticker"].str.upper().apply(
            lambda x: any(t in x for t in tickers) if pd.notna(x) else False
        )
        df_sel = df[mask]
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

    for _, row in df_sel.iterrows():
        ticker_str = str(row["ticker"]).upper().strip()
        ticker = ticker_str.split(';')[0] if ';' in ticker_str else ticker_str

        pasta = get_pasta_balanco(ticker)
        if not pasta.exists():
            err_count += 1
            print(f"❌ {ticker}: pasta {pasta} não existe (captura ausente)")
            continue

        try:
            ok, msg = pad.padronizar_e_salvar_ticker(ticker)
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
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
