# src/padronizar_dre.py
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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


def _infer_fiscal_end_month(df_anual: pd.DataFrame) -> int:
    if df_anual is None or df_anual.empty:
        return 12
    dt = _to_datetime(df_anual, "data_fim").dropna()
    if dt.empty:
        return 12
    return int(dt.dt.month.value_counts().index[0])


def _quarter_end_months(fiscal_end_month: int) -> List[int]:
    m = fiscal_end_month

    def norm(x: int) -> int:
        x = x % 12
        return 12 if x == 0 else x

    return [norm(m - 9), norm(m - 6), norm(m - 3), norm(m)]  # Q1,Q2,Q3,Q4


def _map_trimestre_by_fiscal_month(month: int, fiscal_end_month: int) -> Optional[str]:
    qmonths = _quarter_end_months(fiscal_end_month)
    if month == qmonths[0]:
        return "T1"
    if month == qmonths[1]:
        return "T2"
    if month == qmonths[2]:
        return "T3"
    if month == qmonths[3]:
        return "T4"
    return None


def _fiscal_year(dt: pd.Timestamp, fiscal_end_month: int) -> int:
    if pd.isna(dt):
        return -1
    return int(dt.year if dt.month <= fiscal_end_month else dt.year + 1)


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
# PADRONIZADOR
# ======================================================================================

@dataclass
class PadronizadorDRE:
    pasta_balancos: Path = Path("balancos")

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

    def _add_fiscal_labels(self, df: pd.DataFrame, fiscal_end_month: int) -> pd.DataFrame:
        out = df.copy()
        dt = out["data_fim"]
        out["fiscal_year"] = dt.apply(lambda x: _fiscal_year(x, fiscal_end_month))
        out["trimestre_fiscal"] = dt.dt.month.apply(
            lambda m: _map_trimestre_by_fiscal_month(int(m), fiscal_end_month)
        )
        out = out.dropna(subset=["trimestre_fiscal"])
        out["trimestre_fiscal"] = out["trimestre_fiscal"].astype(str)
        return out

    def _build_quarter_totals(self, df_tri_fiscal: pd.DataFrame) -> pd.DataFrame:
        target_codes = [c for c, _ in DRE_PADRAO]
        wanted_prefixes = tuple([c + "." for c in target_codes] + [EPS_CODE + "."])

        mask = (
            df_tri_fiscal["cd_conta"].isin(target_codes + [EPS_CODE])
            | df_tri_fiscal["cd_conta"].astype(str).str.startswith(wanted_prefixes)
        )
        df = df_tri_fiscal[mask].copy()

        rows = []
        for (fy, tq), g in df.groupby(["fiscal_year", "trimestre_fiscal"], sort=False):
            for code, _name in DRE_PADRAO:
                v = _pick_value_for_base_code(g, code)
                rows.append((int(fy), tq, code, v))
            rows.append((int(fy), tq, EPS_CODE, _compute_eps_value(g)))

        return pd.DataFrame(rows, columns=["fiscal_year", "trimestre", "code", "valor"])

    def _extract_annual_values(self, df_anu_fiscal: pd.DataFrame) -> pd.DataFrame:
        target_codes = [c for c, _ in DRE_PADRAO]
        wanted_prefixes = tuple([c + "." for c in target_codes])

        mask = (
            df_anu_fiscal["cd_conta"].isin(target_codes)
            | df_anu_fiscal["cd_conta"].astype(str).str.startswith(wanted_prefixes)
        )
        df = df_anu_fiscal[mask].copy()

        rows = []
        # ✅ CORREÇÃO: groupby("fiscal_year") para não retornar (fy,) tuple
        for fy, g in df.groupby("fiscal_year", sort=False):
            for code, _name in DRE_PADRAO:
                v = _pick_value_for_base_code(g, code)
                rows.append((int(fy), code, v))

        return pd.DataFrame(rows, columns=["fiscal_year", "code", "anual_val"])

    def _detect_cumulative_years(
        self,
        qtot: pd.DataFrame,
        anual: pd.DataFrame,
        base_code_for_detection: str = "3.01",
        ratio_threshold: float = 1.10,
    ) -> Dict[int, bool]:
        """
        Detecta se o trimestral está acumulado (YTD) por ano fiscal usando 3.01:
          soma(trimestres) > anual * 1.10  => provavelmente acumulado
        """
        anual_map = anual.set_index(["fiscal_year", "code"])["anual_val"].to_dict()
        out: Dict[int, bool] = {}

        # ✅ CORREÇÃO: groupby("fiscal_year") para não retornar (fy,) tuple
        for fy, g in qtot[qtot["code"] == base_code_for_detection].groupby("fiscal_year"):
            a = anual_map.get((int(fy), base_code_for_detection), np.nan)
            if not np.isfinite(a) or a == 0:
                continue
            s = float(np.nansum(g["valor"].values))
            out[int(fy)] = bool(np.isfinite(s) and abs(s) > abs(a) * ratio_threshold)

        return out

    def _to_isolated_quarters(self, qtot: pd.DataFrame, cumulative_years: Dict[int, bool]) -> pd.DataFrame:
        out_rows = []

        for (fy, code), g in qtot.groupby(["fiscal_year", "code"], sort=False):
            g = g.copy()
            g["qord"] = g["trimestre"].apply(_quarter_order)
            g = g.sort_values("qord")

            vals = g["valor"].values.astype(float)
            qs = g["trimestre"].tolist()

            if cumulative_years.get(int(fy), False) and code != EPS_CODE:
                qords = g["qord"].values
                # só converte se for 1..k (sem gaps)
                if len(qords) >= 2 and np.array_equal(qords, np.arange(1, len(qords) + 1)):
                    iso = []
                    prev = None
                    for v in vals:
                        iso.append(v if prev is None else (v - prev))
                        prev = v
                    vals = np.array(iso, dtype=float)

            for tq, v in zip(qs, vals):
                out_rows.append((int(fy), tq, code, float(v) if np.isfinite(v) else np.nan))

        return pd.DataFrame(out_rows, columns=["fiscal_year", "trimestre", "code", "valor"])

    def _add_t4_from_annual_when_missing(self, qiso: pd.DataFrame, anual: pd.DataFrame) -> pd.DataFrame:
        anual_map = anual.set_index(["fiscal_year", "code"])["anual_val"].to_dict()
        out = qiso.copy()

        for fy in sorted(out["fiscal_year"].unique()):
            g = out[out["fiscal_year"] == fy]
            quarters = set(g["trimestre"].unique())

            if "T4" in quarters:
                continue
            if not {"T1", "T2", "T3"}.issubset(quarters):
                continue

            new_rows = []
            for code, _name in DRE_PADRAO:
                a = anual_map.get((int(fy), code), np.nan)
                if not np.isfinite(a):
                    continue
                s = g[(g["code"] == code) & (g["trimestre"].isin(["T1", "T2", "T3"]))]["valor"].sum(skipna=True)
                new_rows.append((int(fy), "T4", code, float(a - s)))

            if new_rows:
                out = pd.concat([out, pd.DataFrame(new_rows, columns=out.columns)], ignore_index=True)

        return out

    def _build_horizontal(self, qiso: pd.DataFrame) -> pd.DataFrame:
        periods = (
            qiso[["fiscal_year", "trimestre"]]
            .drop_duplicates()
            .assign(qord=lambda x: x["trimestre"].apply(_quarter_order))
            .sort_values(["fiscal_year", "qord"])
        )

        col_labels = [f"{int(r.fiscal_year)}{r.trimestre}" for r in periods.itertuples(index=False)]
        ordered_cols = [(int(r.fiscal_year), r.trimestre) for r in periods.itertuples(index=False)]

        pivot = qiso.pivot_table(
            index="code",
            columns=["fiscal_year", "trimestre"],
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

    def _checkup_vs_anual(self, qiso: pd.DataFrame, anual: pd.DataFrame) -> Tuple[int, int, int]:
        anual_map = anual.set_index(["fiscal_year", "code"])["anual_val"].to_dict()

        diverge = 0
        incompleto = 0
        sem_anual = 0

        for fy in sorted(qiso["fiscal_year"].unique()):
            for code, _name in DRE_PADRAO:
                a = anual_map.get((int(fy), code), np.nan)
                qs = qiso[(qiso["fiscal_year"] == fy) & (qiso["code"] == code)]
                have = set(qs["trimestre"].unique())

                if not np.isfinite(a):
                    sem_anual += 1
                    continue

                if not {"T1", "T2", "T3", "T4"}.issubset(have):
                    incompleto += 1
                    continue

                s = float(qs["valor"].sum(skipna=True))
                diff = float(s - a)
                tol = max(1e-6, abs(a) * 1e-3)  # 0,1% do anual

                if abs(diff) > tol:
                    diverge += 1

        return diverge, incompleto, sem_anual

    def padronizar_e_salvar_ticker(self, ticker: str) -> Tuple[bool, str]:
        ticker = ticker.upper().strip()
        pasta = self.pasta_balancos / ticker

        df_tri, df_anu = self._load_inputs(ticker)
        fiscal_end = _infer_fiscal_end_month(df_anu)

        tri_f = self._add_fiscal_labels(df_tri, fiscal_end)
        anu_f = self._add_fiscal_labels(df_anu, fiscal_end)

        qtot = self._build_quarter_totals(tri_f)
        anu = self._extract_annual_values(anu_f)

        cumulative_years = self._detect_cumulative_years(qtot, anu)
        qiso = self._to_isolated_quarters(qtot, cumulative_years)
        qiso = self._add_t4_from_annual_when_missing(qiso, anu)

        qiso = qiso.assign(qord=qiso["trimestre"].apply(_quarter_order)).sort_values(["fiscal_year", "qord", "code"])
        qiso = qiso.drop(columns=["qord"])

        df_out = self._build_horizontal(qiso)

        # check-up interno (sem salvar nada)
        diverge, incompleto, sem_anual = self._checkup_vs_anual(qiso, anu)

        # salva SOMENTE o arquivo final
        pasta.mkdir(parents=True, exist_ok=True)
        out_path = pasta / "dre_padronizado.csv"
        df_out.to_csv(out_path, index=False, encoding="utf-8")

        msg = f"salvo dre_padronizado.csv | check-up: DIVERGE={diverge} INCOMPLETO={incompleto} SEM_ANUAL={sem_anual}"
        ok = (diverge == 0)
        return ok, msg


# ======================================================================================
# CLI - idêntico ao captura_simples.py (modo/quantidade/ticker/lista/faixa)
# ======================================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modo", default="quantidade", choices=["quantidade", "ticker", "lista", "faixa"])
    parser.add_argument("--quantidade", default="10")
    parser.add_argument("--ticker", default="")
    parser.add_argument("--lista", default="")
    parser.add_argument("--faixa", default="1-50")
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
    print("Saída: balancos/<TICKER>/dre_padronizado.csv (apenas)\n")

    pad = PadronizadorDRE()

    ok_count = 0
    warn_count = 0
    err_count = 0

    for _, row in df_sel.iterrows():
        ticker = str(row["ticker"]).upper().strip()

        pasta = Path("balancos") / ticker
        if not pasta.exists():
            err_count += 1
            print(f"❌ {ticker}: pasta balancos/{ticker} não existe (captura ausente)")
            continue

        try:
            ok, msg = pad.padronizar_e_salvar_ticker(ticker)
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
            print(f"❌ {ticker}: erro ({type(e).__name__}: {e})")

    print("\n============================================================")
    print(f"Finalizado: OK={ok_count} | WARN(DIVERGE)>0={warn_count} | ERRO={err_count}")
    print("============================================================\n")


if __name__ == "__main__":
    main()
