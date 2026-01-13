"""
CAPTURA DE BALANÇOS - VERSÃO GITHUB ACTIONS
- TRIMESTRAL: ITR (T1..T4 quando existir)  -> *_consolidado.csv
- ANUAL:     DFP (fechamento do exercício) -> *_anual.csv
- DFC pelo método indireto: DFC_MI
- Cache local de ZIP por ano
- Inteligência de seleção: prioriza ticker ON (3) > PN (4) > outros
"""

import pandas as pd
import requests
from pathlib import Path
from datetime import datetime
import zipfile
import re
import argparse
import sys


# ============================================================================
# UTILITÁRIOS MULTI-TICKER (INLINE COM INTELIGÊNCIA)
# ============================================================================

def load_mapeamento_consolidado() -> pd.DataFrame:
    """Carrega CSV de mapeamento (tenta consolidado, fallback para original)."""
    csv_consolidado = "mapeamento_b3_consolidado.csv"
    csv_original = "mapeamento_final_b3_completo_utf8.csv"

    # Tentar CSV consolidado primeiro
    if Path(csv_consolidado).exists():
        try:
            return pd.read_csv(csv_consolidado, sep=";", encoding="utf-8-sig")
        except Exception:
            pass

    # Fallback para CSV original
    if Path(csv_original).exists():
        try:
            return pd.read_csv(csv_original, sep=";", encoding="utf-8-sig")
        except Exception:
            pass

    # Último fallback
    try:
        return pd.read_csv(csv_original, sep=";")
    except Exception as e:
        raise FileNotFoundError(
            f"Nenhum arquivo de mapeamento encontrado"
        ) from e


def extrair_ticker_inteligente(tickers_str):
    """
    Extrai o ticker mais adequado para busca na CVM.
    Prioriza: ON (código 3) > PN (código 4) > UNIT (código 11)

    Args:
        tickers_str: String com tickers separados por ';' (ex: "SAPR11;SAPR3;SAPR4")

    Returns:
        str: Ticker selecionado segundo a prioridade
    """
    # Remove aspas e espaços, depois faz split por ponto-e-vírgula
    tickers = [t.strip().strip('"') for t in tickers_str.split(';')]

    # Prioridade 1: Busca ticker ON (termina com 3)
    for ticker in tickers:
        if ticker.endswith('3') and not ticker.endswith('11'):  # Evita confusão com UNIT11
            return ticker

    # Prioridade 2: Busca ticker PN (termina com 4)
    for ticker in tickers:
        if ticker.endswith('4'):
            return ticker

    # Prioridade 3: Busca ticker UNIT (termina com 11)
    for ticker in tickers:
        if ticker.endswith('11'):
            return ticker

    # Fallback: retorna o primeiro ticker disponível
    return tickers[0] if tickers else tickers_str


def get_pasta_balanco(ticker: str) -> Path:
    """
    Retorna Path da pasta de balanços usando ticker inteligente.

    Args:
        ticker: Qualquer ticker

    Returns:
        Path para pasta de balanços
    """
    ticker_clean = extrair_ticker_inteligente(ticker)
    return Path("balancos") / ticker_clean


# ============================================================================
# FIM DOS UTILITÁRIOS
# ============================================================================


class CapturaBalancos:

    def __init__(self):
        self.pasta_balancos = Path("balancos")
        self.pasta_balancos.mkdir(exist_ok=True)

        self.cache_dir = Path(".cvm_cache")
        self.cache_dir.mkdir(exist_ok=True)

        self.ano_inicio = 2010
        self.ano_atual = datetime.now().year

        # Consolidado (con). Se quiser individual: False
        self.consolidado = True

        # Demos (inclui DFC_MI)
        self.demos = ["DRE", "BPA", "BPP", "DFC_MI"]

    # ------------------------- DOWNLOAD / LEITURA -------------------------

    def _download_zip(self, doc: str, ano: int) -> Path:
        """
        doc: 'ITR' ou 'DFP'
        Cache robusto: se ZIP estiver corrompido/incompleto, rebaixa automaticamente.
        """
        doc = doc.upper().strip()
        if doc not in ("ITR", "DFP"):
            raise ValueError("doc deve ser 'ITR' ou 'DFP'")

        # Respeita o que existe no Dados Abertos:
        # DFP começa em 2010; ITR começa em 2011
        if doc == "DFP" and ano < 2010:
            raise FileNotFoundError("DFP estruturado (ZIP) indisponível antes de 2010 (Dados Abertos CVM).")
        if doc == "ITR" and ano < 2011:
            raise FileNotFoundError("ITR estruturado (ZIP) indisponível antes de 2011 (Dados Abertos CVM).")

        prefix = "itr_cia_aberta" if doc == "ITR" else "dfp_cia_aberta"
        url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/{doc}/DADOS/{prefix}_{ano}.zip"
        dest = self.cache_dir / f"{prefix}_{ano}.zip"

        def _zip_valido(p: Path) -> bool:
            try:
                if not p.exists() or p.stat().st_size < 1024:
                    return False
                with zipfile.ZipFile(p) as z:
                    return z.testzip() is None
            except Exception:
                return False

        # Se já existe e é válido, usa cache
        if _zip_valido(dest):
            return dest

        # Se existe mas está inválido, apaga e baixa de novo
        if dest.exists():
            try:
                dest.unlink()
            except Exception:
                pass

        r = requests.get(url, timeout=180)
        r.raise_for_status()

        # grava atômico (evita zip “meio baixado”)
        tmp = dest.with_suffix(".zip.tmp")
        tmp.write_bytes(r.content)

        if not _zip_valido(tmp):
            try:
                tmp.unlink()
            except Exception:
                pass
            raise zipfile.BadZipFile(f"ZIP inválido baixado da CVM: {url}")

        tmp.replace(dest)
        return dest

    def _ler_csv_do_zip(self, zip_path: Path, alvo_csv: str) -> pd.DataFrame | None:
        try:
            with zipfile.ZipFile(zip_path) as z:
                name_map = {n.lower(): n for n in z.namelist()}
                real_name = name_map.get(alvo_csv.lower())
                if not real_name:
                    return None
                with z.open(real_name) as f:
                    return pd.read_csv(
                        f,
                        sep=";",
                        encoding="ISO-8859-1",
                        decimal=",",
                        dtype=str,
                        low_memory=False
                    )
        except Exception:
            return None

    def baixar_doc(self, doc: str, ano: int, demo: str, consolidado: bool = True) -> pd.DataFrame | None:
        """
        doc: 'ITR' ou 'DFP'
        demo: 'DRE', 'BPA', 'BPP', 'DFC_MI', ...
        """
        doc = doc.upper().strip()
        demo = demo.upper().strip()

        prefix = "itr_cia_aberta" if doc == "ITR" else "dfp_cia_aberta"
        sufixo = "con" if consolidado else "ind"
        alvo = f"{prefix}_{demo}_{sufixo}_{ano}.csv"

        try:
            zip_path = self._download_zip(doc, ano)
        except Exception as e:
            print(f"[AVISO] Falha ao baixar ZIP {doc} {ano}: {e}")
            return None

        df = self._ler_csv_do_zip(zip_path, alvo)
        return df

    # ------------------------- HELPERS -------------------------

    def _cnpj_digits(self, cnpj: str) -> str:
        # Normaliza para 14 dígitos (corrige casos onde o mapeamento vem como número e perde zeros)
        dig = re.sub(r"\D", "", str(cnpj))
        return dig.zfill(14)

    def _filtrar_empresa_ultimo(self, df: pd.DataFrame, cnpj_digits: str) -> pd.DataFrame:
        if df is None or df.empty:
            return df.iloc[0:0]

        if "CNPJ_CIA" not in df.columns:
            return df.iloc[0:0]

        # CNPJ sempre com 14 dígitos (evita perder anos por zeros à esquerda)
        cnpj_col = (
            df["CNPJ_CIA"]
            .astype(str)
            .str.replace(r"\D", "", regex=True)
            .str.zfill(14)
        )

        df = df[cnpj_col == cnpj_digits].copy()
        if df.empty:
            return df

        if "ORDEM_EXERC" in df.columns:
            ordv = df["ORDEM_EXERC"].astype(str).str.upper()
            df = df[ordv.isin(["ÚLTIMO", "ULTIMO"])].copy()
            if df.empty:
                return df

        if "DT_FIM_EXERC" not in df.columns:
            return df.iloc[0:0]

        df["DT_FIM_EXERC"] = df["DT_FIM_EXERC"].astype(str)
        return df

    def _add_trimestre_itr(self, df: pd.DataFrame) -> pd.DataFrame:
        # ITR: trimestre pelo mês (formato esperado YYYY-MM-DD)
        mes = df["DT_FIM_EXERC"].str[5:7]
        df["TRIMESTRE"] = mes.map({"03": "T1", "06": "T2", "09": "T3", "12": "T4"})
        return df

    def _valor_em_mil(self, df: pd.DataFrame) -> pd.DataFrame:
        if "VL_CONTA" not in df.columns:
            df["VALOR_MIL"] = pd.NA
            return df

        # Normaliza número pt-BR (ex: "1.234.567,89" -> "1234567.89")
        s = df["VL_CONTA"].astype(str)
        s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
        df["VL_CONTA"] = pd.to_numeric(s, errors="coerce")

        # respeita ESCALA_MOEDA quando existir (UNIDADE/MIL)
        if "ESCALA_MOEDA" in df.columns:
            escala = df["ESCALA_MOEDA"].astype(str).str.upper()
            fator = escala.map({"UNIDADE": 1/1000, "MIL": 1}).fillna(1)
            df["VALOR_MIL"] = df["VL_CONTA"] * fator
        else:
            df["VALOR_MIL"] = df["VL_CONTA"] / 1000

        return df

    def _padronizar(self, df: pd.DataFrame, trimestral: bool) -> pd.DataFrame:
        # garante TRIMESTRE na saída
        if trimestral:
            req = ["DT_FIM_EXERC", "TRIMESTRE", "CD_CONTA", "DS_CONTA", "VALOR_MIL"]
            if not all(c in df.columns for c in req):
                return df.iloc[0:0]
            out = df[req].copy()
            out.columns = ["data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"]
            return out

        # anual (DFP): não tem trimestre -> fixamos como T4 para padronizar seu pipeline
        req = ["DT_FIM_EXERC", "CD_CONTA", "DS_CONTA", "VALOR_MIL"]
        if not all(c in df.columns for c in req):
            return df.iloc[0:0]
        out = df[req].copy()
        out["TRIMESTRE"] = "T4"
        out = out[["DT_FIM_EXERC", "TRIMESTRE", "CD_CONTA", "DS_CONTA", "VALOR_MIL"]]
        out.columns = ["data_fim", "trimestre", "cd_conta", "ds_conta", "valor_mil"]
        return out

    def _consolidar(self, frames: list[pd.DataFrame]) -> pd.DataFrame:
        consolidado = pd.concat(frames, ignore_index=True)
        consolidado = consolidado.sort_values(["data_fim", "cd_conta"])
        consolidado = consolidado.drop_duplicates(
            subset=["data_fim", "trimestre", "cd_conta"],
            keep="last"
        )
        return consolidado

    # ------------------------- PROCESSAMENTO -------------------------

    def processar_empresa(self, ticker: str, cnpj: str):
        print(f"\n{'='*50}")
        print(f"📊 {ticker} (CNPJ: {cnpj})")

        # Usar get_pasta_balanco para garantir pasta correta
        pasta = get_pasta_balanco(ticker)
        pasta.mkdir(exist_ok=True)

        cnpj_digits = self._cnpj_digits(cnpj)

        # Ajustes mínimos para evitar warnings e respeitar disponibilidade dos zips
        inicio_dfp = max(self.ano_inicio, 2010)
        inicio_itr = max(self.ano_inicio, 2011)

        for demo in self.demos:
            # -------- TRIMESTRAL (ITR) --------
            dados_tri = []
            for ano in range(inicio_itr, self.ano_atual + 1):
                df = self.baixar_doc("ITR", ano, demo, consolidado=self.consolidado)
                if df is None or df.empty:
                    continue

                df = self._filtrar_empresa_ultimo(df, cnpj_digits)
                if df.empty:
                    continue

                df = self._add_trimestre_itr(df)
                df = self._valor_em_mil(df)
                out = self._padronizar(df, trimestral=True)
                if out.empty:
                    continue

                dados_tri.append(out)

            if dados_tri:
                tri = self._consolidar(dados_tri)
                arq_tri = pasta / f"{demo.lower()}_consolidado.csv"
                tri.to_csv(arq_tri, index=False, encoding="utf-8-sig")
                tri_info = f"✅ {len(tri)} linhas"
            else:
                tri_info = "❌"

            # -------- ANUAL (DFP) --------
            dados_anual = []
            for ano in range(inicio_dfp, self.ano_atual + 1):
                df = self.baixar_doc("DFP", ano, demo, consolidado=self.consolidado)
                if df is None or df.empty:
                    continue

                df = self._filtrar_empresa_ultimo(df, cnpj_digits)
                if df.empty:
                    continue

                df = self._valor_em_mil(df)
                out = self._padronizar(df, trimestral=False)
                if out.empty:
                    continue

                dados_anual.append(out)

            if dados_anual:
                anual = self._consolidar(dados_anual)
                arq_anual = pasta / f"{demo.lower()}_anual.csv"
                anual.to_csv(arq_anual, index=False, encoding="utf-8-sig")
                anual_info = f"✅ {len(anual)} linhas"
            else:
                anual_info = "❌"

            print(f"  {demo}: trimestral(ITR) {tri_info} | anual(DFP) {anual_info}")

    def processar_lote(self, df_sel: pd.DataFrame):
        """
        Processa um lote de empresas selecionadas.
        INTELIGÊNCIA: Sempre usa ticker ON (3) ou PN (4) para buscar na CVM.

        Args:
            df_sel: DataFrame com empresas selecionadas (colunas: ticker, cnpj)
        """
        print(f"\n🚀 Processando {len(df_sel)} empresas...\n")

        ok_count = 0
        err_count = 0

        for _, row in df_sel.iterrows():
            try:
                # Aplicar inteligência de seleção de ticker
                ticker_str = str(row["ticker"]).strip().upper()
                ticker_cvm = extrair_ticker_inteligente(ticker_str)

                self.processar_empresa(ticker_cvm, row["cnpj"])
                ok_count += 1
            except Exception as e:
                err_count += 1
                ticker_str = str(row.get("ticker", "UNKNOWN")).strip().upper()
                ticker_display = extrair_ticker_inteligente(ticker_str)
                print(f"❌ {ticker_display}: erro ({type(e).__name__}: {e})")

        print(f"\n{'='*70}")
        print(f"Finalizado: OK={ok_count} | ERRO={err_count}")
        print(f"{'='*70}\n")


def main():
    """
    Função principal com suporte a argumentos CLI.
    """
    parser = argparse.ArgumentParser(
        description="Captura balanços das empresas B3 (ITR e DFP)"
    )
    parser.add_argument(
        "--modo",
        choices=["quantidade", "ticker", "lista", "faixa"],
        default="quantidade",
        help="Modo de seleção: quantidade, ticker, lista, faixa",
    )
    parser.add_argument(
        "--quantidade",
        default="10",
        help="Quantidade de empresas (modo quantidade)"
    )
    parser.add_argument(
        "--ticker",
        default="",
        help="Ticker específico (modo ticker): ex: PETR4"
    )
    parser.add_argument(
        "--lista",
        default="",
        help="Lista de tickers (modo lista): ex: PETR4,VALE3,ITUB4"
    )
    parser.add_argument(
        "--faixa",
        default="1-50",
        help="Faixa de linhas (modo faixa): ex: 1-50, 51-150"
    )
    args = parser.parse_args()

    # Carregar mapeamento (tenta consolidado, fallback para original)
    df = load_mapeamento_consolidado()
    df = df[df["cnpj"].notna()].reset_index(drop=True)

    # Seleção baseada no modo
    if args.modo == "quantidade":
        limite = int(args.quantidade)
        df_sel = df.head(limite)

    elif args.modo == "ticker":
        ticker_upper = args.ticker.upper()
        # Buscar ticker em qualquer posição da string de tickers
        df_sel = df[df["ticker"].str.upper().str.contains(
            ticker_upper,
            case=False,
            na=False,
            regex=False
        )]

        if df_sel.empty:
            print(f"❌ Ticker '{args.ticker}' não encontrado no mapeamento.")
            sys.exit(1)

    elif args.modo == "lista":
        tickers = [t.strip().upper() for t in args.lista.split(",") if t.strip()]

        if not tickers:
            print("❌ Lista de tickers vazia.")
            sys.exit(1)

        # Buscar cada ticker em qualquer posição
        mask = df["ticker"].str.upper().apply(
            lambda x: any(t in x for t in tickers) if pd.notna(x) else False
        )
        df_sel = df[mask]

        if df_sel.empty:
            print(f"❌ Nenhum ticker da lista encontrado: {', '.join(tickers)}")
            sys.exit(1)

    elif args.modo == "faixa":
        try:
            inicio, fim = map(int, args.faixa.split("-"))
            df_sel = df.iloc[inicio - 1: fim]

            if df_sel.empty:
                print(f"❌ Faixa {args.faixa} está fora do range disponível (1-{len(df)}).")
                sys.exit(1)
        except ValueError:
            print(f"❌ Formato de faixa inválido: '{args.faixa}'. Use formato: inicio-fim (ex: 1-50)")
            sys.exit(1)

    else:
        df_sel = df.head(10)

    # Exibir informações do job
    print(f"\n{'='*70}")
    print(f">>> JOB: CAPTURAR BALANÇOS (ITR + DFP) <<<")
    print(f"{'='*70}")
    print(f"Modo: {args.modo}")
    print(f"Empresas selecionadas: {len(df_sel)}")
    print(f"Demonstrações: DRE, BPA, BPP, DFC_MI")
    print(f"Período: {datetime.now().year - 10} - {datetime.now().year}")
    print(f"Saída: balancos/<TICKER>/*_consolidado.csv + *_anual.csv")
    print(f"Inteligência: Prioriza ON (3) > PN (4) > outros")
    print(f"{'='*70}\n")

    # Processar
    captura = CapturaBalancos()
    captura.processar_lote(df_sel)


if __name__ == "__main__":
    main()
