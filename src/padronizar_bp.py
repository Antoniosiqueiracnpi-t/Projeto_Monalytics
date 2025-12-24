# src/padronizar_bp.py
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd


# ======================================================================================
# CONTAS BPA - BALANÇO PATRIMONIAL ATIVO
# ======================================================================================

BPA_PADRAO: List[Tuple[str, str]] = [
    ("1", "Ativo Total"),
    ("1.01", "Ativo Circulante"),
    ("1.01.01", "Caixa e Equivalentes de Caixa"),
    ("1.01.02", "Aplicações Financeiras"),
    ("1.01.03", "Contas a Receber"),
    ("1.01.04", "Estoques"),
    ("1.01.05", "Ativos Biológicos"),
    ("1.01.06", "Tributos a Recuperar"),
    ("1.01.07", "Despesas Antecipadas"),
    ("1.01.08", "Outros Ativos Circulantes"),
    ("1.02", "Ativo Não Circulante"),
    ("1.02.01", "Ativo Realizável a Longo Prazo"),
    ("1.02.02", "Investimentos"),
    ("1.02.03", "Imobilizado"),
    ("1.02.04", "Intangível"),
]

# ======================================================================================
# CONTAS BPP - BALANÇO PATRIMONIAL PASSIVO
# ======================================================================================

BPP_PADRAO: List[Tuple[str, str]] = [
    ("2", "Passivo Total"),
    ("2.01", "Passivo Circulante"),
    ("2.01.01", "Obrigações Sociais e Trabalhistas"),
    ("2.01.02", "Fornecedores"),
    ("2.01.03", "Obrigações Fiscais"),
    ("2.01.04", "Empréstimos e Financiamentos"),
    ("2.01.05", "Outras Obrigações"),
    ("2.01.06", "Provisões"),
    ("2.01.07", "Passivos sobre Ativos Não-Correntes a Venda e Descontinuados"),
    ("2.02", "Passivo Não Circulante"),
    ("2.02.01", "Empréstimos e Financiamentos"),
    ("2.02.02", "Outras Obrigações"),
    ("2.02.03", "Tributos Diferidos"),
    ("2.02.04", "Provisões"),
    ("2.02.05", "Passivos sobre Ativos Não-Correntes a Venda e Descontinuados"),
    ("2.02.06", "Lucros e Receitas a Apropriar"),
    ("2.03", "Patrimônio Líquido Consolidado"),
    ("2.03.01", "Capital Social Realizado"),
    ("2.03.02", "Reservas de Capital"),
    ("2.03.03", "Reservas de Reavaliação"),
    ("2.03.04", "Reservas de Lucros"),
    ("2.03.05", "Lucros/Prejuízos Acumulados"),
    ("2.03.06", "Ajustes de Avaliação Patrimonial"),
    ("2.03.07", "Ajustes Acumulados de Conversão"),
    ("2.03.08", "Outros Resultados Abrangentes"),
    ("2.03.09", "Participação dos Acionistas Não Controladores"),
]


# ======================================================================================
# CONTAS BPA - BANCOS (placeholder - usar mesmo esquema por enquanto)
# ======================================================================================

BPA_BANCOS: List[Tuple[str, str]] = BPA_PADRAO  # TODO: Adicionar esquema específico


# ======================================================================================
# CONTAS BPP - BANCOS (placeholder - usar mesmo esquema por enquanto)
# ======================================================================================

BPP_BANCOS: List[Tuple[str, str]] = BPP_PADRAO  # TODO: Adicionar esquema específico


# ======================================================================================
# CONTAS BPA - SEGURADORAS (placeholder - usar mesmo esquema por enquanto)
# ======================================================================================

BPA_SEGURADORAS: List[Tuple[str, str]] = BPA_PADRAO  # TODO: Adicionar esquema específico


# ======================================================================================
# CONTAS BPP - SEGURADORAS (placeholder - usar mesmo esquema por enquanto)
# ======================================================================================

BPP_SEGURADORAS: List[Tuple[str, str]] = BPP_PADRAO  # TODO: Adicionar esquema específico


# ======================================================================================
# TICKERS DE BANCOS E SEGURADORAS
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


def _is_banco(ticker: str) -> bool:
    return ticker.upper().strip() in TICKERS_BANCOS


def _is_seguradora(ticker: str) -> bool:
    t = ticker.upper().strip()
    return t in TICKERS_HOLDINGS_SEGUROS or t in TICKERS_SEGURADORAS


def _get_bpa_schema(ticker: str) -> List[Tuple[str, str]]:
    """Retorna o esquema BPA apropriado para o ticker."""
    if _is_banco(ticker):
        return BPA_BANCOS
    elif _is_seguradora(ticker):
        return BPA_SEGURADORAS
    else:
        return BPA_PADRAO


def _get_bpp_schema(ticker: str) -> List[Tuple[str, str]]:
    """Retorna o esquema BPP apropriado para o ticker."""
    if _is_banco(ticker):
        return BPP_BANCOS
    elif _is_seguradora(ticker):
        return BPP_SEGURADORAS
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


def _normalize_value(v: float, decimals: int = 3) -> float:
    """Normaliza valor numérico para evitar erros de ponto flutuante."""
    if not np.isfinite(v):
        return np.nan
    return round(float(v), decimals)


def _pick_value_for_code(group: pd.DataFrame, code: str) -> float:
    """Extrai valor para um código específico."""
    exact = group[group["cd_conta"] == code]
    if not exact.empty:
        v = _ensure_numeric(exact["valor_mil"]).iloc[0]
        return float(v) if np.isfinite(v) else np.nan
    return np.nan


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
    """Detecta o padrão de ano fiscal da empresa."""
    quarters_found = set(df_tri["trimestre"].dropna().unique())
    
    if "data_fim" in df_anu.columns and not df_anu.empty:
        end_months = df_anu["data_fim"].dropna().dt.month.unique()
        
        if len(end_months) == 1 and end_months[0] == 12:
            fiscal_end = 12
            is_standard = True
        elif len(end_months) >= 1:
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
# CLASSE PRINCIPAL - PADRONIZADOR BP (BPA + BPP)
# ======================================================================================

@dataclass
class PadronizadorBP:
    pasta_balancos: Path = Path("balancos")
    _current_ticker: str = field(default="", repr=False)

    def _load_inputs(self, ticker: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Carrega os 4 arquivos de entrada:
        - bpa_consolidado.csv (trimestral)
        - bpa_anual.csv
        - bpp_consolidado.csv (trimestral)
        - bpp_anual.csv
        """
        pasta = self.pasta_balancos / ticker.upper().strip()
        
        bpa_tri_path = pasta / "bpa_consolidado.csv"
        bpa_anu_path = pasta / "bpa_anual.csv"
        bpp_tri_path = pasta / "bpp_consolidado.csv"
        bpp_anu_path = pasta / "bpp_anual.csv"

        if not bpa_tri_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {bpa_tri_path}")
        if not bpa_anu_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {bpa_anu_path}")
        if not bpp_tri_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {bpp_tri_path}")
        if not bpp_anu_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {bpp_anu_path}")

        bpa_tri = pd.read_csv(bpa_tri_path)
        bpa_anu = pd.read_csv(bpa_anu_path)
        bpp_tri = pd.read_csv(bpp_tri_path)
        bpp_anu = pd.read_csv(bpp_anu_path)

        for df in (bpa_tri, bpa_anu, bpp_tri, bpp_anu):
            df["cd_conta"] = df["cd_conta"].astype(str).str.strip()
            df["ds_conta"] = df["ds_conta"].astype(str).str.strip()
            df["valor_mil"] = _ensure_numeric(df["valor_mil"])
            df["data_fim"] = _to_datetime(df, "data_fim")

        bpa_tri = bpa_tri.dropna(subset=["data_fim"])
        bpa_anu = bpa_anu.dropna(subset=["data_fim"])
        bpp_tri = bpp_tri.dropna(subset=["data_fim"])
        bpp_anu = bpp_anu.dropna(subset=["data_fim"])

        return bpa_tri, bpa_anu, bpp_tri, bpp_anu

    def _build_quarter_values(
        self, 
        df_tri: pd.DataFrame, 
        schema: List[Tuple[str, str]]
    ) -> pd.DataFrame:
        """
        Extrai valores trimestrais para as contas do esquema.
        
        IMPORTANTE: Balanço Patrimonial é POSIÇÃO, não fluxo.
        Não soma trimestres - cada trimestre é uma fotografia independente.
        """
        target_codes = [c for c, _ in schema]
        
        df = df_tri[df_tri["cd_conta"].isin(target_codes)].copy()
        df["ano"] = df["data_fim"].dt.year
        
        rows = []
        for (ano, trimestre), g in df.groupby(["ano", "trimestre"], sort=False):
            for code, _name in schema:
                v = _pick_value_for_code(g, code)
                rows.append((int(ano), str(trimestre), code, v))

        return pd.DataFrame(rows, columns=["ano", "trimestre", "code", "valor"])

    def _extract_annual_values(
        self, 
        df_anu: pd.DataFrame, 
        schema: List[Tuple[str, str]]
    ) -> pd.DataFrame:
        """Extrai valores anuais para inclusão como T4."""
        target_codes = [c for c, _ in schema]
        
        df = df_anu[df_anu["cd_conta"].isin(target_codes)].copy()
        df["ano"] = df["data_fim"].dt.year

        rows = []
        for ano, g in df.groupby("ano", sort=False):
            for code, _name in schema:
                v = _pick_value_for_code(g, code)
                rows.append((int(ano), code, v))

        return pd.DataFrame(rows, columns=["ano", "code", "anual_val"])

    def _add_t4_from_annual(
        self, 
        qtot: pd.DataFrame, 
        anual: pd.DataFrame,
        fiscal_info: FiscalYearInfo,
        schema: List[Tuple[str, str]]
    ) -> pd.DataFrame:
        """
        Adiciona T4 usando valor anual diretamente (não subtrai).
        
        IMPORTANTE: Para Balanço Patrimonial, T4 = valor do anual (posição em 31/12).
        Diferente do DRE/DFC onde T4 = Anual - (T1+T2+T3).
        """
        if not fiscal_info.is_standard:
            return qtot
        
        anual_map = anual.set_index(["ano", "code"])["anual_val"].to_dict()
        out = qtot.copy()

        all_codes = [c for c, _ in schema]

        for ano in sorted(out["ano"].unique()):
            g = out[out["ano"] == ano]
            quarters = set(g["trimestre"].unique())

            # Se já tem T4, pular
            if "T4" in quarters:
                continue

            new_rows = []
            for code in all_codes:
                a = anual_map.get((int(ano), code), np.nan)
                if np.isfinite(a):
                    # T4 = valor anual diretamente (posição, não fluxo)
                    new_rows.append((int(ano), "T4", code, float(a)))

            if new_rows:
                out = pd.concat([out, pd.DataFrame(new_rows, columns=out.columns)], ignore_index=True)

        return out

    def _build_horizontal(
        self, 
        qdata: pd.DataFrame, 
        schema: List[Tuple[str, str]]
    ) -> pd.DataFrame:
        """Constrói tabela horizontal (períodos como colunas)."""
        qdata = qdata.copy()
        qdata["periodo"] = qdata["ano"].astype(str) + qdata["trimestre"]
        qdata["valor"] = qdata["valor"].apply(lambda x: _normalize_value(x, 3))

        piv = qdata.pivot_table(
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
        code_order = {c: i for i, (c, _) in enumerate(schema)}
        piv = piv.reindex(sorted(piv.index, key=lambda x: code_order.get(x, 999)))

        # Adicionar nomes das contas
        code_to_name = {c: n for c, n in schema}
        piv.insert(0, "conta", piv.index.map(lambda x: code_to_name.get(x, x)))
        piv = piv.reset_index().rename(columns={"code": "cd_conta"})

        return piv

    def padronizar_e_salvar_ticker(self, ticker: str) -> Tuple[bool, str]:
        """
        Pipeline completo de padronização do BP (BPA + BPP).
        
        Gera 2 arquivos:
        - bpa_padronizado.csv
        - bpp_padronizado.csv
        """
        self._current_ticker = ticker.upper().strip()
        
        # 1. Carregar dados (4 arquivos)
        bpa_tri, bpa_anu, bpp_tri, bpp_anu = self._load_inputs(ticker)
        
        # 2. Detectar padrão fiscal (usar BPA trimestral + anual como referência)
        fiscal_info = _detect_fiscal_year_pattern(bpa_tri, bpa_anu)
        
        # 3. Obter esquemas
        bpa_schema = _get_bpa_schema(ticker)
        bpp_schema = _get_bpp_schema(ticker)
        
        # ========== PROCESSAR BPA ==========
        # 4a. Extrair valores trimestrais
        bpa_qtot = self._build_quarter_values(bpa_tri, bpa_schema)
        
        # 5a. Extrair valores anuais
        bpa_anual = self._extract_annual_values(bpa_anu, bpa_schema)
        
        # 6a. Adicionar T4 do anual
        bpa_qtot = self._add_t4_from_annual(bpa_qtot, bpa_anual, fiscal_info, bpa_schema)
        
        # 7a. Construir tabela horizontal
        bpa_out = self._build_horizontal(bpa_qtot, bpa_schema)
        
        # ========== PROCESSAR BPP ==========
        # 4b. Extrair valores trimestrais
        bpp_qtot = self._build_quarter_values(bpp_tri, bpp_schema)
        
        # 5b. Extrair valores anuais
        bpp_anual = self._extract_annual_values(bpp_anu, bpp_schema)
        
        # 6b. Adicionar T4 do anual
        bpp_qtot = self._add_t4_from_annual(bpp_qtot, bpp_anual, fiscal_info, bpp_schema)
        
        # 7b. Construir tabela horizontal
        bpp_out = self._build_horizontal(bpp_qtot, bpp_schema)
        
        # 8. Salvar arquivos
        pasta = self.pasta_balancos / ticker.upper().strip()
        
        bpa_path = pasta / "bpa_padronizado.csv"
        bpp_path = pasta / "bpp_padronizado.csv"
        
        bpa_out.to_csv(bpa_path, index=False, encoding="utf-8")
        bpp_out.to_csv(bpp_path, index=False, encoding="utf-8")
        
        # 9. Mensagem de retorno
        fiscal_status = "PADRÃO" if fiscal_info.is_standard else "IRREGULAR"
        
        if _is_banco(ticker):
            tipo = "BANCO"
        elif _is_seguradora(ticker):
            tipo = "SEGURADORA"
        else:
            tipo = "GERAL"
        
        n_periodos_bpa = len([c for c in bpa_out.columns if c not in ["cd_conta", "conta"]])
        n_periodos_bpp = len([c for c in bpp_out.columns if c not in ["cd_conta", "conta"]])
        
        msg_parts = [
            f"Fiscal: {fiscal_status}",
            f"Tipo: {tipo}",
            f"BPA: {n_periodos_bpa} períodos",
            f"BPP: {n_periodos_bpp} períodos",
        ]
        
        msg = f"bpa_padronizado.csv + bpp_padronizado.csv | {' | '.join(msg_parts)}"
        
        return True, msg


# ======================================================================================
# CLI - MAIN
# ======================================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Padroniza BPA e BPP das empresas (inclui T4 do anual)"
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

    print(f"\n>>> JOB: PADRONIZAR BP (BPA + BPP) <<<")
    print(f"Modo: {args.modo} | Selecionadas: {len(df_sel)}")
    print("Saída: balancos/<TICKER>/bpa_padronizado.csv + bpp_padronizado.csv\n")

    pad = PadronizadorBP()

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
