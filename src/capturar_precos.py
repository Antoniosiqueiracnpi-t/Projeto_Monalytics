# src/capturar_precos.py
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import warnings

import pandas as pd
import numpy as np

# yfinance pode gerar warnings, vamos suprimir
warnings.filterwarnings('ignore')

try:
    import yfinance as yf
except ImportError:
    raise ImportError("Instale yfinance: pip install yfinance")


@dataclass
class CapturadorPrecos:
    """
    Captura preços de fechamento ajustados para cada trimestre.
    
    Usa as datas de fechamento dos trimestres já capturados (DRE, BP, DFC)
    e busca o preço de fechamento ajustado mais próximo.
    """
    pasta_balancos: Path = Path("balancos")
    max_days_lookback: int = 10  # Busca até 10 dias úteis antes se não houver dados

    def _get_ticker_symbol(self, ticker: str) -> str:
        """Converte ticker brasileiro para formato yfinance (.SA)."""
        ticker_clean = ticker.upper().strip()
        if not ticker_clean.endswith(".SA"):
            ticker_clean = f"{ticker_clean}.SA"
        return ticker_clean

    def _extract_quarter_dates(self, ticker: str) -> pd.DataFrame:
        """
        Extrai datas de fechamento de trimestre dos arquivos já capturados.
        
        Prioridade: DRE > BP > DFC
        """
        pasta = self.pasta_balancos / ticker.upper().strip()
        
        # Tentar DRE primeiro
        dre_tri = pasta / "dre_consolidado.csv"
        if dre_tri.exists():
            df = pd.read_csv(dre_tri)
            if "data_fim" in df.columns and "trimestre" in df.columns:
                dates = df[["data_fim", "trimestre"]].drop_duplicates()
                dates["data_fim"] = pd.to_datetime(dates["data_fim"], errors="coerce")
                return dates.dropna().sort_values("data_fim").reset_index(drop=True)
        
        # Tentar BPA
        bpa_tri = pasta / "bpa_consolidado.csv"
        if bpa_tri.exists():
            df = pd.read_csv(bpa_tri)
            if "data_fim" in df.columns and "trimestre" in df.columns:
                dates = df[["data_fim", "trimestre"]].drop_duplicates()
                dates["data_fim"] = pd.to_datetime(dates["data_fim"], errors="coerce")
                return dates.dropna().sort_values("data_fim").reset_index(drop=True)
        
        # Tentar DFC
        dfc_tri = pasta / "dfc_mi_consolidado.csv"
        if dfc_tri.exists():
            df = pd.read_csv(dfc_tri)
            if "data_fim" in df.columns and "trimestre" in df.columns:
                dates = df[["data_fim", "trimestre"]].drop_duplicates()
                dates["data_fim"] = pd.to_datetime(dates["data_fim"], errors="coerce")
                return dates.dropna().sort_values("data_fim").reset_index(drop=True)
        
        return pd.DataFrame(columns=["data_fim", "trimestre"])

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

    def capturar_e_salvar_ticker(self, ticker: str) -> Tuple[bool, str]:
        """
        Pipeline completo de captura de preços para um ticker.
        
        Returns:
            ok: True se capturou pelo menos um preço
            msg: Mensagem de status
        """
        ticker = ticker.upper().strip()
        pasta = self.pasta_balancos / ticker
        
        # 1. Extrair datas dos trimestres
        dates_df = self._extract_quarter_dates(ticker)
        
        if dates_df.empty:
            return False, "nenhum trimestre encontrado (capture balanços primeiro)"
        
        # 2. Converter ticker para formato yfinance
        ticker_symbol = self._get_ticker_symbol(ticker)
        
        # 3. Buscar preços para cada trimestre
        results = []
        precos_ok = 0
        precos_fail = 0
        
        for _, row in dates_df.iterrows():
            target_date = row["data_fim"]
            trimestre = row["trimestre"]
            
            price = self._fetch_price_for_date(ticker_symbol, target_date)
            
            if price is not None:
                results.append({
                    "data_fim": target_date.strftime("%Y-%m-%d"),
                    "trimestre": trimestre,
                    "preco_fechamento_ajustado": round(price, 2)
                })
                precos_ok += 1
            else:
                results.append({
                    "data_fim": target_date.strftime("%Y-%m-%d"),
                    "trimestre": trimestre,
                    "preco_fechamento_ajustado": np.nan
                })
                precos_fail += 1
        
        # 4. Salvar resultado
        if results:
            df_out = pd.DataFrame(results)
            out_path = pasta / "precos_trimestrais.csv"
            df_out.to_csv(out_path, index=False, encoding="utf-8")
            
            msg_parts = [
                f"periodos={len(results)}",
                f"OK={precos_ok}",
                f"FAIL={precos_fail}"
            ]
            
            msg = f"precos_trimestrais.csv | {' | '.join(msg_parts)}"
            ok = precos_ok > 0
            
            return ok, msg
        else:
            return False, "nenhum resultado gerado"


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
        df_sel = df.iloc[inicio - 1: fim]

    else:
        df_sel = df.head(10)

    print(f"\n>>> JOB: CAPTURAR PREÇOS TRIMESTRAIS <<<")
    print(f"Modo: {args.modo} | Selecionadas: {len(df_sel)}")
    print("Saída: balancos/<TICKER>/precos_trimestrais.csv\n")

    capturador = CapturadorPrecos()

    ok_count = 0
    err_count = 0

    for _, row in df_sel.iterrows():
        ticker = str(row["ticker"]).upper().strip()

        pasta = Path("balancos") / ticker
        if not pasta.exists():
            err_count += 1
            print(f"❌ {ticker}: pasta balancos/{ticker} não existe")
            continue

        try:
            ok, msg = capturador.capturar_e_salvar_ticker(ticker)

            if ok:
                ok_count += 1
                print(f"✅ {ticker}: {msg}")
            else:
                err_count += 1
                print(f"⚠️ {ticker}: {msg}")

        except Exception as e:
            err_count += 1
            import traceback
            print(f"❌ {ticker}: erro ({type(e).__name__}: {e})")
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"Finalizado: OK={ok_count} | ERRO={err_count}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
