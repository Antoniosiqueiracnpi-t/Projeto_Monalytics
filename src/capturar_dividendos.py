# src/capturar_dividendos.py
from __future__ import annotations

import argparse
import base64
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import warnings

import pandas as pd
import numpy as np
import requests

# Suprimir warnings SSL
warnings.filterwarnings('ignore')
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
    Captura histórico de dividendos direto da API B3 oficial.
    
    Agrupa dividendos por trimestre baseado na data COM (ex-dividendo)
    e gera formato horizontal padronizado.
    """
    pasta_balancos: Path = Path("balancos")
    base_url: str = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall"
    
    def _get_trading_name(self, ticker: str) -> Optional[str]:
        """
        Busca o tradingName na B3 pelo ticker.
        
        O tradingName é necessário para consultar dividendos na API B3.
        """
        search_url = f"{self.base_url}/GetListedCompanies"
        
        try:
            response = requests.get(search_url, verify=False, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            ticker_clean = ticker.upper().strip()
            
            # Buscar empresa pelo código
            for company in data.get('results', []):
                codes = company.get('codes', [])
                if ticker_clean in codes:
                    trading_name = company.get('tradingName', '')
                    if trading_name:
                        return trading_name
            
            # Fallback: tentar usar o próprio ticker
            print(f"    ⚠️ TradingName não encontrado, usando ticker como fallback")
            return ticker_clean
            
        except Exception as e:
            print(f"    ⚠️ Erro ao buscar tradingName: {e}")
            return ticker.upper().strip()
    
    def _fetch_dividends_page(
        self, 
        trading_name: str, 
        page: int = 1
    ) -> dict:
        """
        Busca uma página de dividendos da B3.
        
        API retorna até 120 registros por página.
        """
        params = {
            "language": "pt-br",
            "pageNumber": page,
            "pageSize": 120,
            "tradingName": trading_name
        }
        
        # Codificar parâmetros em base64
        params_json = json.dumps(params)
        params_b64 = base64.b64encode(params_json.encode()).decode()
        
        url = f"{self.base_url}/GetListedCashDividends/{params_b64}"
        
        try:
            response = requests.get(url, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"    ⚠️ Erro na página {page}: {e}")
            return {}
    
    def _fetch_all_dividends(self, ticker: str) -> pd.DataFrame:
        """
        Busca todos os dividendos com paginação automática.
        """
        trading_name = self._get_trading_name(ticker)
        
        if not trading_name:
            return pd.DataFrame()
        
        all_dividends = []
        page = 1
        max_pages = 100  # Limite de segurança (100 páginas * 120 = 12.000 registros)
        
        while page <= max_pages:
            data = self._fetch_dividends_page(trading_name, page)
            
            cash_dividends = data.get('cashDividends', [])
            
            if not cash_dividends:
                break
            
            all_dividends.extend(cash_dividends)
            
            # Verificar se há mais páginas
            page_info = data.get('page', {})
            current_page = page_info.get('pageNumber', 0)
            total_pages = page_info.get('totalPages', 0)
            
            if current_page >= total_pages:
                break
            
            page += 1
        
        if not all_dividends:
            return pd.DataFrame()
        
        # Converter para DataFrame
        df = pd.DataFrame(all_dividends)
        
        return df
    
    def _process_dividends(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """
        Processa dividendos brutos da API B3.
        
        1. Extrai campos relevantes
        2. Converte datas
        3. Padroniza valores
        """
        if df.empty:
            return df
        
        # Mapear campos
        column_mapping = {
            'tradingName': 'ticker',
            'corporateActionPrice': 'valor',
            'approvedOn': 'data_aprovacao',
            'lastDatePrior': 'data_com',
            'paymentDate': 'data_pagamento',
            'corporateActionType': 'tipo_provento',
            'relatedTo': 'info'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Garantir que ticker está preenchido
        if 'ticker' not in df.columns or df['ticker'].isna().all():
            df['ticker'] = ticker.upper()
        
        # Selecionar colunas relevantes
        required_cols = ['ticker', 'data_com', 'data_pagamento', 'tipo_provento', 'valor']
        available_cols = [c for c in required_cols if c in df.columns]
        
        if 'info' in df.columns:
            available_cols.append('info')
        
        df = df[available_cols].copy()
        
        # Converter datas
        for date_col in ['data_com', 'data_pagamento', 'data_aprovacao']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Converter valores para numérico
        if 'valor' in df.columns:
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        
        # Remover linhas sem data COM ou valor
        df = df.dropna(subset=['data_com', 'valor'])
        
        return df
    
    def _group_by_quarter(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrupa dividendos por trimestre.
        
        Usa data COM (ex-dividendo) como referência.
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
        grouped['valor'] = grouped['valor'].round(2)
        
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
        
        # 1. Buscar dividendos brutos
        df_raw = self._fetch_all_dividends(ticker)
        
        if df_raw.empty:
            return False, "nenhum dividendo encontrado (API B3 retornou vazio)"
        
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
        description="Captura dividendos históricos da B3 agrupados por trimestre"
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
    print("Fonte: API B3 Oficial")
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
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"Finalizado: OK={ok_count} | ERRO={err_count}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
