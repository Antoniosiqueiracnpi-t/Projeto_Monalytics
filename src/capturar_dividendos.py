# src/capturar_dividendos.py
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import warnings

import pandas as pd
import numpy as np
import requests

# Suprimir warnings
warnings.filterwarnings('ignore')

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False


def _quarter_order(q: str) -> int:
    """Retorna ordem numérica do trimestre para ordenação."""
    return {"T1": 1, "T2": 2, "T3": 3, "T4": 4}.get(q, 99)


def _date_to_quarter(date: pd.Timestamp) -> str:
    """Converte data para trimestre (T1, T2, T3, T4)."""
    if pd.isna(date):
        return None
    month = date.month
    if month <= 3:
        return "T1"
    elif month <= 6:
        return "T2"
    elif month <= 9:
        return "T3"
    else:
        return "T4"


@dataclass
class CapturadorDividendos:
    """
    Captura histórico de dividendos usando múltiplas fontes.
    
    Prioridade:
    1. OkaneBox API (gratuita, simples, dados B3)
    2. yfinance (fallback, dados Yahoo Finance)
    
    Agrupa dividendos por trimestre baseado na data de pagamento
    e gera formato horizontal padronizado.
    """
    pasta_balancos: Path = Path("balancos")
    timeout: int = 30
    
    def _fetch_okanebox(self, ticker: str) -> pd.DataFrame:
        """
        Busca dividendos da OkaneBox API.
        
        Endpoint: https://okanebox.com.br/api/acoes/proventos/{ticker}/
        Retorna: JSON com histórico completo de proventos
        """
        ticker_clean = ticker.upper().replace('.SA', '')
        url = f"https://okanebox.com.br/api/acoes/proventos/{ticker_clean}/"
        
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return pd.DataFrame()
            
            # Converter para DataFrame
            df = pd.DataFrame(data)
            
            # Padronizar colunas
            # OkaneBox retorna: ticker, tipo, datacom, datapagamento, valor
            if 'datacom' in df.columns:
                df = df.rename(columns={
                    'datacom': 'data_com',
                    'datapagamento': 'data_pagamento'
                })
            
            return df
            
        except Exception as e:
            print(f"    [OkaneBox] Erro: {e}")
            return pd.DataFrame()
    
    def _fetch_yfinance(self, ticker: str) -> pd.DataFrame:
        """
        Busca dividendos via yfinance (Yahoo Finance).
        
        Fallback quando OkaneBox não funciona.
        """
        if not HAS_YFINANCE:
            return pd.DataFrame()
        
        try:
            # Garantir que ticker tenha .SA
            ticker_yf = ticker.upper()
            if not ticker_yf.endswith('.SA'):
                ticker_yf = f"{ticker_yf}.SA"
            
            stock = yf.Ticker(ticker_yf)
            divs = stock.dividends
            
            if divs.empty:
                return pd.DataFrame()
            
            # Converter Series para DataFrame
            df = divs.reset_index()
            df.columns = ['data_pagamento', 'valor']
            
            # yfinance não diferencia tipo, considerar tudo como "Dividendo"
            df['tipo'] = 'Dividendo'
            df['data_com'] = df['data_pagamento']  # Aproximação
            
            return df
            
        except Exception as e:
            print(f"    [yfinance] Erro: {e}")
            return pd.DataFrame()
    
    def _fetch_local_csv(self, ticker: str) -> pd.DataFrame:
        """
        Busca dividendos de arquivo CSV local (se disponível).
        
        Formato esperado: balancos/{ticker}/dividendos_raw.csv
        Colunas: data_com, data_pagamento, valor, tipo
        
        Terceiro fallback para ambientes sem acesso a APIs externas.
        """
        csv_path = self.pasta_balancos / ticker / "dividendos_raw.csv"
        
        if not csv_path.exists():
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(csv_path)
            return df
        except Exception as e:
            print(f"    [CSV Local] Erro: {e}")
            return pd.DataFrame()
    
    def _fetch_all_dividends(self, ticker: str) -> pd.DataFrame:
        """
        Busca dividendos tentando múltiplas fontes em ordem de prioridade.
        
        1. OkaneBox API (gratuita, dados B3 oficiais)
        2. yfinance (Yahoo Finance, dados internacionais)
        3. CSV local (se arquivo dividendos_raw.csv existe)
        """
        # 1. Tentar OkaneBox (fonte primária - dados B3)
        df = self._fetch_okanebox(ticker)
        
        if not df.empty:
            print(f"    ✓ Fonte: OkaneBox ({len(df)} registros)")
            return df
        
        # 2. Tentar yfinance (fallback)
        df = self._fetch_yfinance(ticker)
        
        if not df.empty:
            print(f"    ✓ Fonte: yfinance ({len(df)} registros)")
            return df
        
        # 3. Tentar CSV local (último fallback)
        df = self._fetch_local_csv(ticker)
        
        if not df.empty:
            print(f"    ✓ Fonte: CSV Local ({len(df)} registros)")
            return df
        
        return pd.DataFrame()
    
    def _process_dividends(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """
        Processa dividendos brutos.
        
        1. Padroniza colunas
        2. Converte datas
        3. Padroniza valores
        4. Remove dados inválidos
        """
        if df.empty:
            return df
        
        # Garantir colunas essenciais
        if 'ticker' not in df.columns:
            df['ticker'] = ticker.upper()
        
        # Usar data_com se disponível, senão data_pagamento
        if 'data_com' in df.columns:
            date_ref = 'data_com'
        elif 'data_pagamento' in df.columns:
            date_ref = 'data_pagamento'
            df['data_com'] = df['data_pagamento']
        else:
            return pd.DataFrame()
        
        # Converter datas
        for date_col in ['data_com', 'data_pagamento']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Converter valores
        if 'valor' in df.columns:
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        
        # Remover linhas sem data ou valor
        df = df.dropna(subset=['data_com', 'valor'])
        
        # Remover valores zero ou negativos
        df = df[df['valor'] > 0]
        
        return df
    
    def _group_by_quarter(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrupa dividendos por trimestre.
        
        Usa data_com (ex-dividendo) como referência.
        Soma todos os proventos do mesmo trimestre.
        """
        if df.empty:
            return df
        
        # Extrair ano e trimestre
        df['ano'] = df['data_com'].dt.year
        df['trimestre'] = df['data_com'].apply(_date_to_quarter)
        
        # Remover registros sem trimestre
        df = df.dropna(subset=['trimestre'])
        
        # Agrupar e somar por ano/trimestre
        grouped = df.groupby(['ano', 'trimestre'], as_index=False).agg({
            'valor': 'sum'
        })
        
        # Arredondar valores
        grouped['valor'] = grouped['valor'].round(4)
        
        return grouped
    
    def _build_horizontal(self, df_grouped: pd.DataFrame) -> pd.DataFrame:
        """
        Constrói tabela horizontal (períodos como colunas).
        
        Formato: Dividendos_Pagos | 2022T1 | 2022T2 | ...
        """
        if df_grouped.empty:
            return pd.DataFrame(columns=["Dividendos_Pagos"])
        
        # Criar período (ex: 2022T1)
        df_grouped['periodo'] = (
            df_grouped['ano'].astype(str) + df_grouped['trimestre']
        )
        
        # Ordenar períodos cronologicamente
        def sort_key(p):
            try:
                return (int(p[:4]), _quarter_order(p[4:]))
            except:
                return (9999, 99)
        
        df_grouped = df_grouped.sort_values(
            by='periodo',
            key=lambda x: x.map(sort_key)
        )
        
        # Criar dict com período: valor
        value_dict = dict(zip(
            df_grouped['periodo'],
            df_grouped['valor']
        ))
        
        # Construir linha horizontal
        result = {"Dividendos_Pagos": "Dividendos + JCP Pagos no Trimestre"}
        result.update(value_dict)
        
        return pd.DataFrame([result])
    
    def capturar_e_salvar_ticker(self, ticker: str) -> Tuple[bool, str]:
        """
        Pipeline completo de captura de dividendos.
        
        Returns:
            ok: True se capturou pelo menos um dividendo
            msg: Mensagem de status
        """
        ticker = ticker.upper().strip()
        pasta = self.pasta_balancos / ticker
        
        # 1. Buscar dividendos brutos (multi-fonte)
        df_raw = self._fetch_all_dividends(ticker)
        
        if df_raw.empty:
            return False, "nenhum dividendo encontrado (todas as fontes falharam)"
        
        # 2. Processar dados
        df_processed = self._process_dividends(df_raw, ticker)
        
        if df_processed.empty:
            return False, "nenhum dividendo válido após processamento"
        
        # 3. Agrupar por trimestre
        df_grouped = self._group_by_quarter(df_processed)
        
        if df_grouped.empty:
            return False, "nenhum dividendo após agrupamento trimestral"
        
        # 4. Construir formato horizontal
        df_out = self._build_horizontal(df_grouped)
        
        # 5. Salvar
        out_path = pasta / "dividendos_trimestrais.csv"
        df_out.to_csv(out_path, index=False, encoding="utf-8")
        
        # 6. Estatísticas
        n_periodos = len([c for c in df_out.columns if c != "Dividendos_Pagos"])
        total_dividendos = df_grouped['valor'].sum()
        
        if not df_processed.empty and 'data_com' in df_processed.columns:
            periodo_inicio = df_processed['data_com'].min().year
            periodo_fim = df_processed['data_com'].max().year
        else:
            periodo_inicio = periodo_fim = "?"
        
        msg_parts = [
            f"periodos={n_periodos}",
            f"total=R${total_dividendos:.2f}",
            f"range={periodo_inicio}-{periodo_fim}"
        ]
        
        msg = f"dividendos_trimestrais.csv | {' | '.join(msg_parts)}"
        
        return True, msg


def main():
    parser = argparse.ArgumentParser(
        description="Captura dividendos históricos agrupados por trimestre"
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

    print(f"\n>>> JOB: CAPTURAR DIVIDENDOS TRIMESTRAIS <<<")
    print(f"Modo: {args.modo} | Selecionadas: {len(df_sel)}")
    print("Fontes: OkaneBox API (primária) + yfinance (fallback)")
    print("Saída: balancos/<TICKER>/dividendos_trimestrais.csv\n")

    capturador = CapturadorDividendos()

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
            # traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"Finalizado: OK={ok_count} | ERRO={err_count}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
