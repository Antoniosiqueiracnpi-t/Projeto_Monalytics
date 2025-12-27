# src/padronizar_bp.py
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
# CONTAS BP ATIVO (NÃO FINANCEIRAS)
# ======================================================================================

BPA_PADRAO: List[Tuple[str, str]] = [
    ("1.01", "Ativo Circulante"),
    ("1.01.01", "Caixa e Equivalentes de Caixa"),
    ("1.01.02", "Aplicações Financeiras"),
    ("1.01.03", "Contas a Receber"),
    ("1.01.04", "Estoques"),
    ("1.01.06", "Tributos a Recuperar"),
    ("1.01.08", "Outros Ativos Circulantes"),
    ("1.02", "Ativo Não Circulante"),
    ("1.02.01", "Ativo Realizável a Longo Prazo"),
    ("1.02.02", "Investimentos"),
    ("1.02.03", "Imobilizado"),
    ("1.02.04", "Intangível"),
]

# ======================================================================================
# CONTAS BP PASSIVO (NÃO FINANCEIRAS)
# ======================================================================================

BPP_PADRAO: List[Tuple[str, str]] = [
    ("2.01", "Passivo Circulante"),
    ("2.01.01", "Obrigações Sociais e Trabalhistas"),
    ("2.01.02", "Fornecedores"),
    ("2.01.03", "Obrigações Fiscais"),
    ("2.01.04", "Empréstimos e Financiamentos"),
    ("2.01.05", "Outras Obrigações"),
    ("2.02", "Passivo Não Circulante"),
    ("2.02.01", "Empréstimos e Financiamentos"),
    ("2.02.02", "Outras Obrigações"),
    ("2.03", "Patrimônio Líquido"),
    ("2.03.01", "Capital Social Realizado"),
    ("2.03.02", "Reservas de Capital"),
    ("2.03.04", "Reservas de Lucros"),
    ("2.03.09", "Participação dos Acionistas Não Controladores"),
]

# ======================================================================================
# CONTAS BP ATIVO (BANCOS)
# ======================================================================================

BPA_BANCOS: List[Tuple[str, str]] = [
    ("1.01", "Ativo Circulante"),
    ("1.01.01", "Disponibilidades"),
    ("1.01.02", "Aplicações Interfinanceiras de Liquidez"),
    ("1.01.03", "Títulos e Valores Mobiliários e Instrumentos Derivativos"),
    ("1.01.04", "Relações Interfinanceiras e Interdependências"),
    ("1.01.06", "Operações de Crédito, Arrendamento Mercantil e Outros Créditos"),
    ("1.01.08", "Outros Ativos"),
    ("1.02", "Ativo Não Circulante"),
    ("1.02.01", "Ativo Realizável a Longo Prazo"),
    ("1.02.02", "Investimentos"),
    ("1.02.03", "Imobilizado"),
    ("1.02.04", "Intangível"),
]

# ======================================================================================
# CONTAS BP PASSIVO (BANCOS)
# ======================================================================================

BPP_BANCOS: List[Tuple[str, str]] = [
    ("2.01", "Passivo Circulante"),
    ("2.01.01", "Depósitos"),
    ("2.01.02", "Captação no Mercado Aberto"),
    ("2.01.03", "Recursos de Aceites e Emissão de Títulos"),
    ("2.01.04", "Relações Interfinanceiras e Interdependências"),
    ("2.01.06", "Obrigações por Empréstimos e Repasses"),
    ("2.01.07", "Instrumentos Financeiros Derivativos"),
    ("2.01.09", "Outras Obrigações"),
    ("2.02", "Passivo Não Circulante"),
    ("2.02.01", "Depósitos"),
    ("2.02.03", "Recursos de Aceites e Emissão de Títulos"),
    ("2.02.05", "Relações Interfinanceiras e Interdependências"),
    ("2.02.06", "Obrigações por Empréstimos e Repasses"),
    ("2.02.07", "Instrumentos Financeiros Derivativos"),
    ("2.02.09", "Outras Obrigações"),
    ("2.03", "Patrimônio Líquido"),
    ("2.03.01", "Capital Social Realizado"),
    ("2.03.02", "Reservas de Capital, Opções Outorgadas e Ações em Tesouraria"),
    ("2.03.04", "Reservas de Lucros"),
    ("2.03.05", "Lucros ou Prejuízos Acumulados"),
    ("2.03.08", "Outros Resultados Abrangentes"),
    ("2.03.09", "Participação dos Acionistas Não Controladores"),
]

# ======================================================================================
# CONTAS BP ATIVO (HOLDINGS SEGUROS)
# ======================================================================================

BPA_HOLDINGS_SEGUROS: List[Tuple[str, str]] = [
    ("1.01", "Ativo Circulante"),
    ("1.01.01", "Caixa e Equivalentes de Caixa"),
    ("1.01.02", "Aplicações Financeiras"),
    ("1.01.03", "Contas a Receber"),
    ("1.01.06", "Tributos Correntes e Diferidos a Recuperar"),
    ("1.01.08", "Outros Ativos Circulantes"),
    ("1.02", "Ativo Não Circulante"),
    ("1.02.01", "Ativo Realizável a Longo Prazo"),
    ("1.02.02", "Investimentos"),
    ("1.02.03", "Imobilizado"),
    ("1.02.04", "Intangível"),
]

# ======================================================================================
# CONTAS BP PASSIVO (HOLDINGS SEGUROS)
# ======================================================================================

BPP_HOLDINGS_SEGUROS: List[Tuple[str, str]] = [
    ("2.01", "Passivo Circulante"),
    ("2.01.01", "Contas a Pagar"),
    ("2.01.02", "Obrigações Fiscais Correntes"),
    ("2.01.03", "Empréstimos e Financiamentos"),
    ("2.01.05", "Outras Obrigações"),
    ("2.02", "Passivo Não Circulante"),
    ("2.02.01", "Empréstimos e Financiamentos"),
    ("2.02.02", "Tributos Diferidos"),
    ("2.02.04", "Provisões"),
    ("2.02.05", "Outras Obrigações"),
    ("2.03", "Patrimônio Líquido Consolidado"),
    ("2.03.01", "Capital Social Realizado"),
    ("2.03.02", "Reservas de Capital"),
    ("2.03.04", "Reservas de Lucros"),
    ("2.03.05", "Lucros/Prejuízos Acumulados"),
    ("2.03.08", "Outros Resultados Abrangentes"),
    ("2.03.09", "Participação dos Acionistas Não Controladores"),
]

# ======================================================================================
# CONTAS BP ATIVO (SEGURADORAS)
# ======================================================================================

BPA_SEGURADORAS: List[Tuple[str, str]] = [
    ("1.01", "Ativo Circulante"),
    ("1.01.01", "Disponível"),
    ("1.01.02", "Aplicações"),
    ("1.01.03", "Créditos das Operações com Seguros e Resseguros"),
    ("1.01.04", "Ativos de Resseguro e Retrocessão - Provisões Técnicas"),
    ("1.01.05", "Títulos e Créditos a Receber"),
    ("1.01.08", "Outros Créditos Operacionais"),
    ("1.01.09", "Despesas Antecipadas"),
    ("1.02", "Ativo Não Circulante"),
    ("1.02.01", "Ativo Realizável a Longo Prazo"),
    ("1.02.02", "Investimentos"),
    ("1.02.03", "Imobilizado"),
    ("1.02.04", "Intangível"),
]

# ======================================================================================
# CONTAS BP PASSIVO (SEGURADORAS)
# ======================================================================================

BPP_SEGURADORAS: List[Tuple[str, str]] = [
    ("2.01", "Passivo Circulante"),
    ("2.01.01", "Contas a Pagar"),
    ("2.01.02", "Débitos de Operações com Seguros e Resseguros"),
    ("2.01.03", "Depósitos de Terceiros"),
    ("2.01.04", "Provisões Técnicas - Seguros e Resseguros"),
    ("2.02", "Passivo Não Circulante"),
    ("2.02.01", "Contas a Pagar"),
    ("2.02.02", "Débitos de Operações com Seguros e Resseguros"),
    ("2.02.03", "Depósitos de Terceiros"),
    ("2.02.04", "Provisões Técnicas - Seguros e Resseguros"),
    ("2.03", "Patrimônio Líquido"),
    ("2.03.01", "Capital Social"),
    ("2.03.02", "Reservas de Capital"),
    ("2.03.04", "Reservas de Lucros"),
    ("2.03.05", "Ajustes de Avaliação Patrimonial"),
    ("2.03.09", "Participação de Acionistas Não Controladores"),
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


def _get_bpa_schema(ticker: str) -> List[Tuple[str, str]]:
    ticker_upper = ticker.upper().strip()
    if _is_holding_seguros(ticker_upper):
        return BPA_HOLDINGS_SEGUROS
    elif _is_seguradora(ticker_upper):
        return BPA_SEGURADORAS
    elif _is_banco(ticker_upper):
        return BPA_BANCOS
    else:
        return BPA_PADRAO


def _get_bpp_schema(ticker: str) -> List[Tuple[str, str]]:
    ticker_upper = ticker.upper().strip()
    if _is_holding_seguros(ticker_upper):
        return BPP_HOLDINGS_SEGUROS
    elif _is_seguradora(ticker_upper):
        return BPP_SEGURADORAS
    elif _is_banco(ticker_upper):
        return BPP_BANCOS
    else:
        return BPP_PADRAO


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
# PADRONIZADOR BP
# ======================================================================================

class PadronizadorBP:
    def __init__(self, pasta_balancos: Path = Path("balancos")):
        self.pasta_balancos = pasta_balancos
        self._current_ticker: str = ""

    def _load_inputs(self, ticker: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        pasta = get_pasta_balanco(ticker)
        
        tri_ativo = pasta / "bpa_consolidado.csv"
        tri_passivo = pasta / "bpp_consolidado.csv"
        anu_ativo = pasta / "bpa_anual.csv"
        anu_passivo = pasta / "bpp_anual.csv"

        for p in [tri_ativo, tri_passivo, anu_ativo, anu_passivo]:
            if not p.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {p}")

        dfs = []
        for p in [tri_ativo, tri_passivo, anu_ativo, anu_passivo]:
            df = pd.read_csv(p)
            df["cd_conta"] = df["cd_conta"].astype(str).str.strip()
            df["ds_conta"] = df["ds_conta"].astype(str).str.strip()
            df["valor_mil"] = _ensure_numeric(df["valor_mil"])
            df["data_fim"] = _to_datetime(df, "data_fim")
            df = df.dropna(subset=["data_fim"])
            dfs.append(df)

        # MAPEAMENTO DE TRIMESTRES PARA ANO FISCAL ESPECIAL
        if _is_ano_fiscal_mar_fev(ticker):
            for df in [dfs[0], dfs[1]]:  # apenas trimestrais
                df["trimestre"] = df.apply(
                    lambda row: _map_fiscal_month_to_quarter(ticker, row["data_fim"].month) 
                    if pd.notna(row["data_fim"]) else row.get("trimestre"),
                    axis=1
                )

        return dfs[0], dfs[1], dfs[2], dfs[3]

    def _build_quarter_totals(self, df_tri: pd.DataFrame, schema: List[Tuple[str, str]]) -> pd.DataFrame:
        target_codes = [c for c, _ in schema]
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
            for code, _name in schema:
                v = _pick_value_for_base_code(g, code)
                rows.append((int(ano), str(trimestre), code, v))

        return pd.DataFrame(rows, columns=["ano", "trimestre", "code", "valor"])

    def _extract_annual_values(self, df_anu: pd.DataFrame, schema: List[Tuple[str, str]]) -> pd.DataFrame:
        target_codes = [c for c, _ in schema]
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
            for code, _name in schema:
                v = _pick_value_for_base_code(g, code)
                rows.append((int(ano), code, v))

        return pd.DataFrame(rows, columns=["ano", "code", "anual_val"])

    def _add_t4_from_annual_when_missing(
        self, qiso: pd.DataFrame, anual: pd.DataFrame, schema: List[Tuple[str, str]]
    ) -> pd.DataFrame:
        """
        PARA BP: T4 = valor anual DIRETO (não subtrai trimestres).
        BP é posição patrimonial, não fluxo acumulado.
        """
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
            for code, _ in schema:
                a = anual_map.get((int(ano), code), np.nan)
                if not np.isfinite(a):
                    continue
                # T4 = valor anual (posição, não fluxo)
                new_rows.append((int(ano), "T4", code, float(a)))

            if new_rows:
                out = pd.concat([out, pd.DataFrame(new_rows, columns=out.columns)], ignore_index=True)

        return out

    def _build_horizontal(self, qiso: pd.DataFrame, schema: List[Tuple[str, str]]) -> pd.DataFrame:
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

        idx_codes = [c for c, _ in schema]
        pivot = pivot.reindex(idx_codes)
        pivot.columns = col_labels

        names = {c: n for c, n in schema}
        pivot.insert(0, "ds_conta", [names.get(c, '') for c in pivot.index])
        pivot.insert(0, "cd_conta", [str(c) for c in pivot.index])

        return pivot.reset_index(drop=True)

    def padronizar_e_salvar_ticker(self, ticker: str) -> Tuple[bool, str]:
        ticker = ticker.upper().strip()
        self._current_ticker = ticker
        pasta = get_pasta_balanco(ticker)

        tri_a, tri_p, anu_a, anu_p = self._load_inputs(ticker)

        schema_ativo = _get_bpa_schema(ticker)
        schema_passivo = _get_bpp_schema(ticker)

        qtot_a = self._build_quarter_totals(tri_a, schema_ativo)
        qtot_p = self._build_quarter_totals(tri_p, schema_passivo)

        anu_a_vals = self._extract_annual_values(anu_a, schema_ativo)
        anu_p_vals = self._extract_annual_values(anu_p, schema_passivo)

        qiso_a = qtot_a.assign(qord=qtot_a["trimestre"].apply(_quarter_order)).sort_values(["ano", "qord", "code"]).drop(columns=["qord"])
        qiso_p = qtot_p.assign(qord=qtot_p["trimestre"].apply(_quarter_order)).sort_values(["ano", "qord", "code"]).drop(columns=["qord"])

        qiso_a = self._add_t4_from_annual_when_missing(qiso_a, anu_a_vals, schema_ativo)
        qiso_p = self._add_t4_from_annual_when_missing(qiso_p, anu_p_vals, schema_passivo)

        df_ativo = self._build_horizontal(qiso_a, schema_ativo)
        df_passivo = self._build_horizontal(qiso_p, schema_passivo)

        pasta.mkdir(parents=True, exist_ok=True)

        out_ativo = pasta / "bpa_padronizado.csv"
        out_passivo = pasta / "bpp_padronizado.csv"

        df_ativo.to_csv(out_ativo, index=False, encoding="utf-8")
        df_passivo.to_csv(out_passivo, index=False, encoding="utf-8")

        tipo_bp = "BANCO" if _is_banco(ticker) else "HOLDING_SEG" if _is_holding_seguros(ticker) else "SEGURADORA" if _is_seguradora(ticker) else "PADRÃO"
        
        msg_parts = [f"tipo={tipo_bp}"]
        if _is_ano_fiscal_mar_fev(ticker):
            msg_parts.append("(Mar-Fev)")
        
        msg = f"bpa_padronizado.csv + bpp_padronizado.csv | {' | '.join(msg_parts)}"
        
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

    print(f"\n>>> JOB: PADRONIZAR BP <<<")
    print(f"Modo: {args.modo} | Selecionadas: {len(df_sel)}")
    print("Saída: balancos/<TICKER>/bpa_padronizado.csv + bpp_padronizado.csv\n")

    pad = PadronizadorBP()

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
