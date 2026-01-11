# src/capturar_precos.py
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import warnings
import re

import pandas as pd
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from multi_ticker_utils import get_ticker_principal, get_pasta_balanco, load_mapeamento_consolidado

# yfinance pode gerar warnings, vamos suprimir
warnings.filterwarnings('ignore')

try:
    import yfinance as yf
except ImportError:
    raise ImportError("Instale yfinance: pip install yfinance")


def _quarter_order(q: str) -> int:
    """Retorna ordem numérica do trimestre para ordenação."""
    return {"T1": 1, "T2": 2, "T3": 3, "T4": 4}.get(q, 99)


def _inferir_data_fim(ano: int, trimestre: str) -> pd.Timestamp:
    """
    Infere a data de fim do trimestre baseado no padrão brasileiro.
    
    T1 -> 31/03
    T2 -> 30/06
    T3 -> 30/09
    T4 -> 31/12
    """
    mapa_datas = {
        "T1": f"{ano}-03-31",
        "T2": f"{ano}-06-30",
        "T3": f"{ano}-09-30",
        "T4": f"{ano}-12-31"
    }
    return pd.Timestamp(mapa_datas.get(trimestre, f"{ano}-12-31"))


@dataclass
class CapturadorPrecos:
    """
    Captura preços de fechamento ajustados para cada trimestre.
    
    Usa os arquivos padronizados (dre_padronizado.csv, bpa_padronizado.csv, etc.)
    para extrair os períodos e mapear para datas de fechamento.
    """
    pasta_balancos: Path = Path("balancos")
    max_days_lookback: int = 10  # Busca até 10 dias úteis antes se não houver dados

    def _get_ticker_symbol(self, ticker: str) -> str:
        """Converte ticker brasileiro para formato yfinance (.SA)."""
        ticker_clean = ticker.upper().strip()
        if not ticker_clean.endswith(".SA"):
            ticker_clean = f"{ticker_clean}.SA"
        return ticker_clean

    def _ticker_to_yahoo_symbol(self, ticker: str) -> str:
        """Alias (compatibilidade): converte ticker B3 para símbolo do Yahoo Finance (.SA)."""
        return self._get_ticker_symbol(ticker)

    def _extract_quarter_dates_from_padronizado(self, ticker: str, pasta_base: Optional[Path] = None) -> pd.DataFrame:
        """
        Extrai períodos dos arquivos padronizados e mapeia para datas de fechamento.
        
        Prioridade: dre_padronizado > bpa_padronizado > bpp_padronizado > dfc_padronizado
        """
        pasta = pasta_base if pasta_base is not None else get_pasta_balanco(ticker)
        
        # Arquivos padronizados em ordem de prioridade
        arquivos_padronizados = [
            "dre_padronizado.csv",
            "bpa_padronizado.csv",
            "bpp_padronizado.csv",
            "dfc_padronizado.csv"
        ]
        
        for arquivo in arquivos_padronizados:
            arquivo_path = pasta / arquivo
            if arquivo_path.exists():
                try:
                    df = pd.read_csv(arquivo_path)
                    
                    # Extrair colunas que são períodos (formato: 2015T1, 2015T2, etc.)
                    pattern = re.compile(r'^(\d{4})(T[1-4])$')
                    periodos = []
                    
                    for col in df.columns:
                        match = pattern.match(str(col))
                        if match:
                            ano = int(match.group(1))
                            trimestre = match.group(2)
                            data_fim = _inferir_data_fim(ano, trimestre)
                            periodos.append({
                                'periodo': col,
                                'ano': ano,
                                'trimestre': trimestre,
                                'data_fim': data_fim
                            })
                    
                    if periodos:
                        df_periodos = pd.DataFrame(periodos)
                        # Ordenar por data
                        df_periodos = df_periodos.sort_values('data_fim').reset_index(drop=True)
                        return df_periodos
                    
                except Exception as e:
                    continue
        
        # Se não encontrou nada nos padronizados, tentar consolidados (fallback)
        return self._extract_quarter_dates_from_consolidado(ticker)

    def _extract_quarter_dates_from_consolidado(self, ticker: str) -> pd.DataFrame:
        """
        Fallback: extrai datas dos arquivos consolidados (método antigo).
        """
        pasta = get_pasta_balanco(ticker)
        
        def process_file(filepath):
            if filepath.exists():
                df = pd.read_csv(filepath)
                if "data_fim" in df.columns and "trimestre" in df.columns:
                    dates = df[["data_fim", "trimestre"]].drop_duplicates()
                    dates["data_fim"] = pd.to_datetime(dates["data_fim"], errors="coerce")
                    dates = dates.dropna()
                    if not dates.empty:
                        # Extrair ano e criar período
                        dates["ano"] = dates["data_fim"].dt.year
                        dates["periodo"] = dates["ano"].astype(str) + dates["trimestre"]
                        return dates[["periodo", "ano", "trimestre", "data_fim"]]
            return pd.DataFrame()
        
        # Tentar DRE, BPA, DFC consolidados
        for arquivo in ["dre_consolidado.csv", "bpa_consolidado.csv", "dfc_mi_consolidado.csv"]:
            df = process_file(pasta / arquivo)
            if not df.empty:
                return df.sort_values("data_fim").reset_index(drop=True)
        
        return pd.DataFrame(columns=["periodo", "ano", "trimestre", "data_fim"])

    def _fetch_price_for_date(
        self, 
        ticker_symbol: str, 
        target_date: pd.Timestamp
    ) -> Optional[float]:
        """
        Busca preço de fechamento ajustado para uma data específica.
        
        Se não houver negociação na data exata, busca o último preço disponível
        nos últimos max_days_lookback dias.
        """
        try:
            # Período de busca: target_date - lookback até target_date + 1 dia
            start_date = target_date - pd.Timedelta(days=self.max_days_lookback)
            end_date = target_date + pd.Timedelta(days=1)
            
            # Download dados
            data = yf.download(
                ticker_symbol,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                progress=False,
                auto_adjust=True  # Retorna preços ajustados
            )
            
            if data.empty:
                return None
            
            # yfinance retorna Close como preço ajustado quando auto_adjust=True
            if "Close" not in data.columns:
                return None
            
            # Buscar preço na data exata
            if target_date in data.index:
                price = float(data.loc[target_date, "Close"])
                if np.isfinite(price) and price > 0:
                    return price
            
            # Se não encontrou na data exata, buscar o último disponível antes
            data = data[data.index <= target_date]
            if data.empty:
                return None
            
            price = float(data["Close"].iloc[-1])
            if np.isfinite(price) and price > 0:
                return price
            
            return None
            
        except Exception as e:
            print(f"    ⚠️ Erro ao buscar preço: {e}")
            return None

    def _build_horizontal(self, prices_data: pd.DataFrame) -> pd.DataFrame:
        """
        Constrói tabela horizontal (períodos como colunas).
        
        Formato: Preço_Fechamento | 2015T1 | 2015T2 | ... | 2015T4 | 2016T1 | ...
        """
        if prices_data.empty:
            return pd.DataFrame(columns=["Preço_Fechamento"])
        
        # Ordenar períodos cronologicamente usando ano e trimestre
        def sort_key(row):
            return (row["ano"], _quarter_order(row["trimestre"]))
        
        prices_data = prices_data.copy()
        prices_data["sort_key"] = prices_data.apply(sort_key, axis=1)
        prices_data = prices_data.sort_values("sort_key").drop("sort_key", axis=1)
        
        # Criar dict com período: preço
        price_dict = dict(zip(
            prices_data["periodo"],
            prices_data["preco_fechamento_ajustado"]
        ))
        
        # Construir linha horizontal
        result = {"Preço_Fechamento": "Preço de Fechamento Ajustado"}
        result.update(price_dict)
        
        return pd.DataFrame([result])

    def capturar_e_salvar_ticker(self, ticker: str, merge_multiclasses: bool = True, pasta_base: Optional[Path] = None) -> Tuple[bool, str]:
        """
        Pipeline completo de captura de preços para um ticker.

        IMPORTANTE (multi-classes no mesmo arquivo/pasta):
          - Quando merge_multiclasses=True, o arquivo balancos/<PASTA>/precos_trimestrais.csv passa a ter várias linhas,
            uma por ticker (classe), com a coluna 'Ticker' identificando a linha.
          - Se existir um arquivo legado (sem coluna 'Ticker'), ele será migrado automaticamente para o novo formato.

        Returns:
            ok: True se capturou pelo menos um preço
            msg: Mensagem de status
        """
        ticker = ticker.upper().strip()
        pasta = pasta_base if pasta_base is not None else get_pasta_balanco(ticker)

        # 1) Extrair períodos e datas (prioriza padronizados) - usa a pasta "base" encontrada pelo get_pasta_balanco()
        dates_df = self._extract_quarter_dates_from_padronizado(ticker, pasta_base=pasta)

        if dates_df.empty:
            return False, "nenhum período encontrado (capture balanços primeiro)"

        # 2) Determinar símbolo para o Yahoo (ex.: BBDC3.SA)
        ticker_symbol = self._ticker_to_yahoo_symbol(ticker)

        # 3) Buscar preço para cada data (fim de trimestre)
        results = []
        precos_ok = 0
        precos_fail = 0
        tem_t4 = False

        for _, row in dates_df.iterrows():
            target_date = row["data_fim"]
            trimestre = row["trimestre"]
            periodo = row["periodo"]
            ano = row["ano"]

            if trimestre == "T4":
                tem_t4 = True

            price = self._fetch_price_for_date(ticker_symbol, target_date)

            if price is not None:
                results.append({
                    "periodo": periodo,
                    "ano": ano,
                    "trimestre": trimestre,
                    "data_fim": target_date,
                    "preco_fechamento_ajustado": round(float(price), 2),
                })
                precos_ok += 1
            else:
                results.append({
                    "periodo": periodo,
                    "ano": ano,
                    "trimestre": trimestre,
                    "data_fim": target_date,
                    "preco_fechamento_ajustado": np.nan,
                })
                precos_fail += 1

        if not results:
            return False, "nenhum resultado gerado"

        # 4) Construir tabela horizontal (1 linha)
        df_temp = pd.DataFrame(results)
        df_out = self._build_horizontal(df_temp)

        # 5) Salvar/mesclar no arquivo (multi-linhas por ticker)
        out_path = pasta / "precos_trimestrais.csv"

        # Enriquecer com coluna 'Ticker'
        df_out = df_out.copy()
        df_out.insert(0, "Ticker", ticker)

        if merge_multiclasses and out_path.exists():
            try:
                df_old = pd.read_csv(out_path)

                # Migração automática do formato legado (sem coluna Ticker)
                if "Ticker" not in df_old.columns:
                    try:
                        principal = get_ticker_principal(ticker)
                    except Exception:
                        principal = pasta.name.upper()
                    df_old = df_old.copy()
                    df_old.insert(0, "Ticker", principal)

                # União de colunas
                all_cols = list(dict.fromkeys(list(df_old.columns) + list(df_out.columns)))

                def _ensure_cols(df: pd.DataFrame) -> pd.DataFrame:
                    df2 = df.copy()
                    for c in all_cols:
                        if c not in df2.columns:
                            df2[c] = np.nan
                    return df2[all_cols]

                df_old = _ensure_cols(df_old)
                df_out2 = _ensure_cols(df_out)

                # Upsert da linha do ticker
                mask = df_old["Ticker"].astype(str).str.upper().str.strip() == ticker
                if mask.any():
                    df_old.loc[mask, :] = df_out2.iloc[0].values
                else:
                    df_old = pd.concat([df_old, df_out2], ignore_index=True)

                # Reordenar colunas: Ticker, Preço_Fechamento, períodos ordenados
                base_cols = [c for c in ["Ticker", "Preço_Fechamento"] if c in df_old.columns]
                period_cols = [c for c in df_old.columns if re.fullmatch(r"\d{4}T[1-4]", str(c))]
                other_cols = [c for c in df_old.columns if c not in base_cols + period_cols]
                period_cols = sorted(period_cols)
                df_final = df_old[base_cols + period_cols + other_cols]

                df_final.to_csv(out_path, index=False, encoding="utf-8")
            except Exception:
                # Em caso de erro na mesclagem, sobrescreve (mantém no mínimo o ticker atual)
                df_out.to_csv(out_path, index=False, encoding="utf-8")
        else:
            # Novo arquivo no formato multi-linhas
            df_out.to_csv(out_path, index=False, encoding="utf-8")

        msg_parts = [f"periodos={len(results)}", f"OK={precos_ok}", f"FAIL={precos_fail}"]
        if tem_t4:
            msg_parts.append("inclui_T4")
        return True, " | ".join(msg_parts)


def main():
    parser = argparse.ArgumentParser(
        description="Captura preços de fechamento ajustados para cada trimestre"
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

    # Tentar carregar mapeamento consolidado, fallback para original
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
        df_sel = df.iloc[inicio - 1: fim]

    else:
        df_sel = df.head(10)

    print(f"\n>>> JOB: CAPTURAR PREÇOS TRIMESTRAIS <<<")
    print(f"Modo: {args.modo} | Selecionadas: {len(df_sel)}")
    print("Fonte: arquivos *_padronizado.csv (prioridade)")
    print("Saída: balancos/<TICKER>/precos_trimestrais.csv\n")

    capturador = CapturadorPrecos()

    ok_count = 0
    err_count = 0

    for _, row in df_sel.iterrows():
        ticker_str = str(row["ticker"]).upper().strip()

        # Capturar TODAS as classes no mesmo arquivo/pasta (evita criar BBDC3/BBDC4/...)
        tickers = [t.strip().upper() for t in re.split(r"[;,]", ticker_str) if t.strip()]
        if not tickers:
            err_count += 1
            print(f"❌ linha sem ticker válido: {ticker_str}")
            continue

        ticker_base = tickers[0]  # ticker principal da pasta (ex.: BBDC3)
        # A pasta base é resolvida pelo get_pasta_balanco (reutiliza pasta existente)
        pasta = get_pasta_balanco(ticker_base)
        if not pasta.exists():
            err_count += 1
            print(f"❌ {ticker_base}: pasta {pasta} não existe")
            continue

        try:
            # Captura trimestral: salva TODAS as classes no mesmo precos_trimestrais.csv (uma linha por ticker/classe)
            ok_all = True
            msgs = []
            for t in tickers:
                ok_t, msg_t = capturador.capturar_e_salvar_ticker(t, merge_multiclasses=True, pasta_base=pasta)
                ok_all = ok_all and ok_t
                msgs.append(f"{t}: {msg_t}")
            ok, msg = ok_all, " ; ".join(msgs)


            if ok:
                ok_count += 1
                print(f"✅ {ticker_base}: {msg}")
            else:
                err_count += 1
                print(f"⚠️ {ticker_base}: {msg}")

        except Exception as e:
            err_count += 1
            import traceback
            print(f"❌ {ticker_base}: erro ({type(e).__name__}: {e})")
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"Finalizado: OK={ok_count} | ERRO={err_count}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
