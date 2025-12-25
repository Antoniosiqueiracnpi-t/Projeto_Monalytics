# src/capturar_precos.py
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import warnings

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
        Agora usa get_pasta_balanco() para garantir pasta correta.
        
        Prioridade: DRE > BP > DFC
        """
        pasta = get_pasta_balanco(ticker)
        
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

    def _build_horizontal(self, prices_data: pd.DataFrame) -> pd.DataFrame:
        """
        Constrói tabela horizontal (períodos como colunas).
        
        Formato: Preço_Fechamento | 2022T1 | 2022T2 | ...
        """
        if prices_data.empty:
            return pd.DataFrame(columns=["Preço_Fechamento"])
        
        # Adicionar coluna de ano
        prices_data["ano"] = prices_data["data_fim"].dt.year
        
        # Criar período (ex: 2022T1)
        prices_data["periodo"] = (
            prices_data["ano"].astype(str) + prices_data["trimestre"]
        )
        
        # Ordenar períodos cronologicamente
        def sort_key(p):
            try:
                return (int(p[:4]), _quarter_order(p[4:]))
            except:
                return (9999, 99)
        
        prices_data = prices_data.sort_values(
            by="periodo",
            key=lambda x: x.map(sort_key)
        )
        
        # Criar dict com período: preço
        price_dict = dict(zip(
            prices_data["periodo"],
            prices_data["preco_fechamento_ajustado"]
        ))
        
        # Construir linha horizontal
        result = {"Preço_Fechamento": "Preço de Fechamento Ajustado"}
        result.update(price_dict)
        
        return pd.DataFrame([result])

    def capturar_e_salvar_ticker(self, ticker: str) -> Tuple[bool, str]:
        """
        Pipeline completo de captura de preços para um ticker.
        Agora usa get_pasta_balanco() para garantir pasta correta.
        
        Returns:
            ok: True se capturou pelo menos um preço
            msg: Mensagem de status
        """
        ticker = ticker.upper().strip()
        pasta = get_pasta_balanco(ticker)
        
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
                    "data_fim": target_date,
                    "trimestre": trimestre,
                    "preco_fechamento_ajustado": round(price, 2)
                })
                precos_ok += 1
            else:
                results.append({
                    "data_fim": target_date,
                    "trimestre": trimestre,
                    "preco_fechamento_ajustado": np.nan
                })
                precos_fail += 1
        
        # 4. Construir tabela horizontal
        if results:
            df_temp = pd.DataFrame(results)
            df_out = self._build_horizontal(df_temp)
            
            # 5. Salvar resultado
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
    print("Saída: balancos/<TICKER>/precos_trimestrais.csv\n")

    capturador = CapturadorPrecos()

    ok_count = 0
    err_count = 0

    for _, row in df_sel.iterrows():
        ticker_str = str(row["ticker"]).upper().strip()
        ticker = ticker_str.split(';')[0] if ';' in ticker_str else ticker_str

        pasta = get_pasta_balanco(ticker)
        if not pasta.exists():
            err_count += 1
            print(f"❌ {ticker}: pasta {pasta} não existe")
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
