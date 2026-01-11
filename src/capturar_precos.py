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

    def _extract_quarter_dates_from_padronizado(self, ticker: str) -> pd.DataFrame:
        """
        Extrai períodos dos arquivos padronizados e mapeia para datas de fechamento.
        
        Prioridade: dre_padronizado > bpa_padronizado > bpp_padronizado > dfc_padronizado
        """
        pasta = get_pasta_balanco(ticker)
        
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

    def capturar_e_salvar_ticker(self, ticker: str) -> Tuple[bool, str]:
        """
        Pipeline completo de captura de preços para um ticker.
        
        Returns:
            ok: True se capturou pelo menos um preço
            msg: Mensagem de status
        """
        ticker = ticker.upper().strip()
        pasta = get_pasta_balanco(ticker)
        
        # 1. Extrair períodos e datas (prioriza padronizados)
        dates_df = self._extract_quarter_dates_from_padronizado(ticker)
        
        if dates_df.empty:
            return False, "nenhum período encontrado (capture balanços primeiro)"
        
        # 2. Converter ticker para formato yfinance
        ticker_symbol = self._get_ticker_symbol(ticker)
        
        # 3. Buscar preços para cada período
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
                    "preco_fechamento_ajustado": round(price, 2)
                })
                precos_ok += 1
            else:
                results.append({
                    "periodo": periodo,
                    "ano": ano,
                    "trimestre": trimestre,
                    "data_fim": target_date,
                    "preco_fechamento_ajustado": np.nan
                })
                precos_fail += 1
        
        # 4. Construir tabela horizontal
        if results:
            df_temp = pd.DataFrame(results)
            df_out = self._build_horizontal(df_temp)
            
            # 5. Salvar resultado (SOBRESCREVE o arquivo anterior)
            out_path = pasta / "precos_trimestrais.csv"
            df_out.to_csv(out_path, index=False, encoding="utf-8")
            
            msg_parts = [
                f"periodos={len(results)}",
                f"OK={precos_ok}",
                f"FAIL={precos_fail}"
            ]
            
            if tem_t4:
                msg_parts.append("T4=✓")
            
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
    print("Fonte: arquivos *_padronizado.csv (prioridade)")
    print("Saída: balancos/<TICKER>/precos_trimestrais.csv\n")

    capturador = CapturadorPrecos()

    ok_count = 0
    err_count = 0
    tickers_processados = set()

    for _, row in df_sel.iterrows():
        ticker_str = str(row["ticker"]).upper().strip()
    
        # Para múltiplos/valuation: IGNORAR classe 11 (UNIT).
        # Ex.: "ITUB3;ITUB4;ITUB11" -> ["ITUB3", "ITUB4"]
        tickers_raw = [t.strip() for t in ticker_str.split(";") if t.strip()] if ";" in ticker_str else [ticker_str]
        tickers_filtrados = [t for t in tickers_raw if not t.endswith("11")]
    
        if not tickers_filtrados:
            # Só existe UNIT (ou nada válido) -> não capturamos preços trimestrais (múltiplos ignoram 11)
            print(f"⏭️ {ticker_str}: ignorado (somente classe 11/UNIT ou vazio)")
            continue
    
        # Evitar capturar o mesmo ticker duas vezes no mesmo job
        for ticker in tickers_filtrados:
            if ticker in tickers_processados:
                continue
            tickers_processados.add(ticker)
    
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



if __name__ == "__main__":
    main()
