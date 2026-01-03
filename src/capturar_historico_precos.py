"""
CAPTURADOR DE HISTÓRICO DE PREÇOS - 5 ANOS + MÉDIAS MÓVEIS
==========================================================
Janeiro 2025

Captura histórico de preços ajustados dos últimos 5 anos e calcula:
- Médias móveis: 20, 50, 200 períodos
- Estatísticas: máxima, mínima, variação

CLASSES SUPORTADAS: 3, 4, 11 + IBOVESPA (^BVSP)
SAÍDA: balancos/{TICKER}/historico_precos.json

EXECUÇÃO:
python src/capturar_historico_precos.py --modo lista --lista "PETR4,VALE3,BBDC4"
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import re

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    print("❌ yfinance não instalado: pip install yfinance")


# ======================================================================================
# UTILITÁRIOS DE MAPEAMENTO
# ======================================================================================

def load_mapeamento_b3() -> pd.DataFrame:
    """Carrega mapeamento de tickers B3 do CSV."""
    csv_path = Path("mapeamento_b3_consolidado.csv")
    
    if not csv_path.exists():
        print(f"❌ Arquivo não encontrado: {csv_path}")
        return pd.DataFrame()
    
    try:
        # CSV usa ; como separador e pode ter BOM UTF-8
        df = pd.read_csv(
            csv_path, 
            encoding='utf-8-sig',  # Remove BOM se existir
            sep=';',                # Separador é ponto e vírgula
            on_bad_lines='warn'     # Avisar sobre linhas problemáticas
        )
        return df
    except Exception as e:
        print(f"❌ Erro ao ler CSV: {e}")
        return pd.DataFrame()


import re  # <-- adicione este import

def get_pasta_balanco(ticker: str) -> Path:
    """
    Define a pasta balancos/{TICKER_CANONICO}/ para salvar os dados.

    Regras:
      - Se já existir uma pasta para a empresa (qualquer classe 3/4/11), reutiliza essa pasta (não cria outra).
      - Se existir apenas a pasta "base" sem classe (ex.: PETR) e o ticker solicitado tem classe (ex.: PETR4),
        cria/usa a pasta com classe (PETR4) para não perpetuar o padrão antigo.
      - Se não existir nenhuma pasta, usa o ticker exatamente como informado.
    """
    ticker = str(ticker).upper().strip()

    # IBOVESPA é sempre fixo
    if ticker == "IBOV":
        return Path("balancos") / "IBOV"

    root = Path("balancos")
    base = re.sub(r"\d+$", "", ticker)  # remove apenas sufixo numérico final
    has_suffix = bool(re.search(r"\d+$", ticker))
    if not base:
        base = ticker
        has_suffix = False

    # 1) Se já existe pasta exatamente com o ticker solicitado (ex.: ABEV3), usar ela
    exact = root / ticker
    if exact.exists() and exact.is_dir():
        return exact

    # 2) Se existe alguma pasta de classe para a mesma empresa (ex.: ABEV3/ABEV4/ABEV11), reutilizar (não criar outra)
    class_candidates = []
    if root.exists():
        for p in root.iterdir():
            if not p.is_dir():
                continue
            name = p.name.upper()
            if re.fullmatch(re.escape(base) + r"\d+", name):
                class_candidates.append(p)

    if class_candidates:
        # Preferência determinística (11 > 4 > 3; senão, ordem alfabética)
        def _prio(path: Path):
            n = path.name.upper()
            suf = n[len(base):]
            if suf == "11":
                return (0, n)
            if suf == "4":
                return (1, n)
            if suf == "3":
                return (2, n)
            return (9, n)

        return sorted(class_candidates, key=_prio)[0]

    # 3) Se existe somente a pasta base (legado), só reutiliza quando o ticker NÃO tem sufixo numérico
    base_path = root / base
    if base_path.exists() and base_path.is_dir() and (not has_suffix):
        return base_path

    # 4) Caso contrário, criar/usar a pasta do ticker informado (mantém a classe)
    return exact



# ======================================================================================
# CONFIGURAÇÕES
# ======================================================================================

ANOS_HISTORICO = 5
PERIODOS_MM = [20, 50, 200]  # Médias móveis


# ======================================================================================
# CAPTURA DE DADOS
# ======================================================================================

def capturar_historico_ticker(ticker: str, anos: int = ANOS_HISTORICO) -> Optional[pd.DataFrame]:
    """
    Captura histórico de preços ajustados via yfinance.

    Args:
        ticker: Código B3 (ex: PETR4) ou ^BVSP para Ibovespa
        anos: Anos de histórico (padrão: 5)

    Returns:
        DataFrame com OHLCV ou None
    """
    if not HAS_YFINANCE:
        return None

    # Converter para formato Yahoo
    if ticker == "IBOV":
        ticker_yahoo = "^BVSP"
    else:
        ticker_yahoo = f"{ticker}.SA" if not ticker.endswith(".SA") else ticker

    # Período
    end_date = datetime.now()
    start_date = end_date - timedelta(days=anos * 365 + 30)  # +30 dias de margem

    try:
        hist = yf.download(
            ticker_yahoo,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            progress=False,
            auto_adjust=True  # Preços ajustados
        )

        # Verificações robustas
        if hist is None:
            return None

        if not isinstance(hist, pd.DataFrame):
            return None

        if len(hist) == 0:
            return None

        # ------------------------------------------------------------------
        # yfinance pode retornar colunas MultiIndex (dependendo da versão/ambiente).
        # Isso pode fazer com que df['Close'].iloc[0] vire Series e estoure:
        # "The truth value of a Series is ambiguous".
        # Normalizamos para um DataFrame com colunas simples (Open/High/Low/Close/Volume).
        # ------------------------------------------------------------------
        if isinstance(hist.columns, pd.MultiIndex):
            # 1) Se existir um nível contendo o ticker solicitado, seleciona apenas ele
            for lvl in range(hist.columns.nlevels):
                lvl_vals = hist.columns.get_level_values(lvl)
                if ticker_yahoo in set(lvl_vals):
                    hist = hist.xs(ticker_yahoo, level=lvl, axis=1)
                    break

            # 2) Se ainda for MultiIndex, achata para o nível que contém OHLCV
            if isinstance(hist.columns, pd.MultiIndex):
                ohlcv = {"Open", "High", "Low", "Close", "Adj Close", "Volume"}
                lv0 = hist.columns.get_level_values(0)
                lv1 = hist.columns.get_level_values(1)

                if any(c in ohlcv for c in lv0):
                    hist.columns = lv0
                elif any(c in ohlcv for c in lv1):
                    hist.columns = lv1
                else:
                    # fallback: concatena os níveis em string
                    hist.columns = ["_".join(map(str, c)).strip() for c in hist.columns.to_list()]

        # Renomear colunas para padrão
        hist = hist.rename(columns={
            'Open': 'abertura',
            'High': 'maxima',
            'Low': 'minima',
            'Close': 'fechamento',
            'Volume': 'volume'
        })

        # Garantir que índice é datetime
        hist.index = pd.to_datetime(hist.index)

        # Verificar se tem as colunas necessárias
        colunas_necessarias = ['abertura', 'maxima', 'minima', 'fechamento', 'volume']
        colunas_disponiveis = [col for col in colunas_necessarias if col in hist.columns]

        if len(colunas_disponiveis) < 4:  # Precisa de pelo menos 4 colunas (menos volume)
            return None

        # Garantir que 'fechamento' seja Series (evita ambiguidade em operações futuras)
        if 'fechamento' in hist.columns and isinstance(hist['fechamento'], pd.DataFrame):
            hist['fechamento'] = hist['fechamento'].iloc[:, 0]

        return hist[colunas_disponiveis]

    except Exception as e:
        print(f"  ⚠️  Erro ao baixar {ticker}: {e}")
        return None

# ======================================================================================
# CÁLCULO DE MÉDIAS MÓVEIS
# ======================================================================================

def calcular_medias_moveis(df: pd.DataFrame, periodos: List[int] = PERIODOS_MM) -> pd.DataFrame:
    """
    Calcula médias móveis do fechamento.

    Args:
        df: DataFrame com coluna 'fechamento'
        periodos: Lista de períodos (ex: [20, 50, 200])

    Returns:
        DataFrame com colunas mm20, mm50, mm200 adicionadas
    """
    df = df.copy()

    # Garantir que fechamento é Series (pode vir como DataFrame se houver colunas duplicadas)
    fechamento = df.get('fechamento')
    if isinstance(fechamento, pd.DataFrame):
        if fechamento.shape[1] == 0:
            return df
        fechamento = fechamento.iloc[:, 0]
        df['fechamento'] = fechamento

    for periodo in periodos:
        col_name = f"mm{periodo}"
        df[col_name] = df['fechamento'].rolling(window=periodo, min_periods=periodo).mean()

    return df


# ======================================================================================
# ANÁLISE DE TENDÊNCIA
# ======================================================================================

def calcular_tendencia(preco: float, mm20: float, mm50: float, mm200: float) -> str:
    """
    Determina tendência baseada em preço e médias móveis.
    
    Args:
        preco: Preço de fechamento atual
        mm20, mm50, mm200: Valores das médias móveis
    
    Returns:
        "alta" | "baixa" | "indefinida"
    """
    # Verificar se todos os valores são válidos
    if any(pd.isna(v) or v is None for v in [preco, mm20, mm50, mm200]):
        return "indefinida"
    
    # Tendência de ALTA: Preço > MM20 > MM50 > MM200
    if preco > mm20 > mm50 > mm200:
        return "alta"
    
    # Tendência de BAIXA: Preço < MM20 < MM50 < MM200
    if preco < mm20 < mm50 < mm200:
        return "baixa"
    
    # Qualquer outra configuração
    return "indefinida"


# ======================================================================================
# ESTATÍSTICAS
# ======================================================================================

def calcular_estatisticas(df: pd.DataFrame) -> Dict:
    """Calcula estatísticas do período."""
    if len(df) == 0:
        return {}

    if 'fechamento' not in df.columns:
        return {}

    fechamento = df['fechamento']

    # Se por algum motivo 'fechamento' vier como DataFrame (colunas duplicadas / MultiIndex)
    if isinstance(fechamento, pd.DataFrame):
        if fechamento.shape[1] == 0:
            return {}
        fechamento = fechamento.iloc[:, 0]

    # Converter para float com segurança
    primeiro_preco_raw = fechamento.iloc[0]
    ultimo_preco_raw = fechamento.iloc[-1]

    try:
        primeiro_preco = float(primeiro_preco_raw)
    except Exception:
        return {}

    try:
        ultimo_preco = float(ultimo_preco_raw)
    except Exception:
        return {}

    if primeiro_preco <= 0:
        variacao_pct = 0.0
    else:
        variacao_pct = (ultimo_preco - primeiro_preco) / primeiro_preco * 100.0

    # Volume (opcional)
    volume_medio = 0
    if 'volume' in df.columns:
        vol = df['volume']
        if isinstance(vol, pd.DataFrame):
            if vol.shape[1] > 0:
                vol = vol.iloc[:, 0]
            else:
                vol = None
        if vol is not None:
            try:
                volume_medio = int(float(vol.mean()))
            except Exception:
                volume_medio = 0

    # ANÁLISE DE TENDÊNCIA (último dia com médias válidas)
    tendencia = "indefinida"
    try:
        # Pegar último registro com todas as médias válidas
        ultimos_validos = df[
            df['mm20'].notna() & 
            df['mm50'].notna() & 
            df['mm200'].notna()
        ]
        
        if len(ultimos_validos) > 0:
            ultimo = ultimos_validos.iloc[-1]
            
            # Extrair valores (garantindo que são float)
            preco = float(ultimo['fechamento']) if isinstance(ultimo['fechamento'], (int, float, np.number)) else float(ultimo['fechamento'].iloc[0])
            mm20 = float(ultimo['mm20']) if isinstance(ultimo['mm20'], (int, float, np.number)) else float(ultimo['mm20'].iloc[0])
            mm50 = float(ultimo['mm50']) if isinstance(ultimo['mm50'], (int, float, np.number)) else float(ultimo['mm50'].iloc[0])
            mm200 = float(ultimo['mm200']) if isinstance(ultimo['mm200'], (int, float, np.number)) else float(ultimo['mm200'].iloc[0])
            
            tendencia = calcular_tendencia(preco, mm20, mm50, mm200)
    except Exception:
        tendencia = "indefinida"

    return {
        "total_dias": int(len(df)),
        "preco_inicial": round(primeiro_preco, 2),
        "preco_atual": round(ultimo_preco, 2),
        "variacao_periodo": round(float(variacao_pct), 2),
        "maxima_periodo": round(float(fechamento.max()), 2),
        "minima_periodo": round(float(fechamento.min()), 2),
        "volume_medio": volume_medio,
        "tendencia": tendencia
    }


# ======================================================================================
# CONVERSÃO PARA JSON
# ======================================================================================

def df_para_json(df: pd.DataFrame, ticker: str) -> Dict:
    """
    Converte DataFrame em estrutura JSON otimizada para gráficos.
    
    Returns:
        {
            "ticker": "PETR4",
            "ultima_atualizacao": "2025-01-02T10:00:00",
            "periodo": {"inicio": "2020-01-02", "fim": "2025-01-02"},
            "dados": [...],
            "estatisticas": {...}
        }
    """
    if len(df) == 0:
        return {}
    
    # Resetar índice para ter 'data' como coluna
    df = df.reset_index()
    
    # Tentar diferentes nomes de coluna de data
    if 'Date' in df.columns:
        df['data'] = df['Date'].dt.strftime('%Y-%m-%d')
    elif df.index.name == 'Date' or isinstance(df.index, pd.DatetimeIndex):
        df['data'] = df.index.strftime('%Y-%m-%d')
    else:
        # Se não encontrar coluna de data, usar o índice resetado
        df['data'] = pd.to_datetime(df.index).strftime('%Y-%m-%d')
    
    # Converter para lista de dicts
    dados = []
    for _, row in df.iterrows():
        ponto = {
            "data": row['data'],
            "abertura": round(float(row['abertura']), 2) if 'abertura' in row and pd.notna(row['abertura']) else None,
            "maxima": round(float(row['maxima']), 2) if 'maxima' in row and pd.notna(row['maxima']) else None,
            "minima": round(float(row['minima']), 2) if 'minima' in row and pd.notna(row['minima']) else None,
            "fechamento": round(float(row['fechamento']), 2) if 'fechamento' in row and pd.notna(row['fechamento']) else None,
            "volume": int(row['volume']) if 'volume' in row and pd.notna(row['volume']) else 0,
            "mm20": round(float(row['mm20']), 2) if 'mm20' in row and pd.notna(row['mm20']) else None,
            "mm50": round(float(row['mm50']), 2) if 'mm50' in row and pd.notna(row['mm50']) else None,
            "mm200": round(float(row['mm200']), 2) if 'mm200' in row and pd.notna(row['mm200']) else None
        }
        dados.append(ponto)
    
    # Estrutura final
    return {
        "ticker": ticker,
        "ultima_atualizacao": datetime.now().isoformat(),
        "periodo": {
            "inicio": dados[0]['data'] if dados else None,
            "fim": dados[-1]['data'] if dados else None
        },
        "dados": dados,
        "estatisticas": calcular_estatisticas(df)
    }


# ======================================================================================
# PROCESSADOR PRINCIPAL
# ======================================================================================

def processar_ticker(ticker: str, anos: int = ANOS_HISTORICO) -> Tuple[bool, str]:
    """
    Processa um ticker: baixa histórico, calcula médias, salva JSON.
    
    Returns:
        (sucesso, mensagem)
    """
    try:
        # Determinar pasta
        if ticker == "IBOV":
            pasta = Path("balancos") / "IBOV"
        else:
            pasta = get_pasta_balanco(ticker)
        
        pasta.mkdir(parents=True, exist_ok=True)
        
        # Baixar histórico
        df = capturar_historico_ticker(ticker, anos)
        
        # Verificação corrigida para evitar erro de ambiguidade
        if df is None:
            return False, "sem dados disponíveis"
        
        if not isinstance(df, pd.DataFrame):
            return False, "formato de dados inválido"
        
        if len(df) == 0:
            return False, "sem dados disponíveis"
        
        # Calcular médias móveis
        df = calcular_medias_moveis(df, PERIODOS_MM)
        
        # Converter para JSON
        dados_json = df_para_json(df, ticker)
        
        # Salvar
        arquivo = pasta / "historico_precos_diarios.json"
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados_json, f, ensure_ascii=False, indent=2)
        
        # Estatísticas para log
        stats = dados_json.get('estatisticas', {})
        total_dias = stats.get('total_dias', 0)
        preco_atual = stats.get('preco_atual', 0)
        variacao = stats.get('variacao_periodo', 0)
        
        msg = f"{total_dias} dias | R$ {preco_atual} | Δ {variacao:+.1f}%"
        
        return True, msg
        
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:50]}"


# ======================================================================================
# PROCESSADOR EM LOTE
# ======================================================================================

def processar_lote(tickers: List[str], anos: int = ANOS_HISTORICO) -> Tuple[int, int]:
    """
    Processa múltiplos tickers em sequência.
    
    Returns:
        (sucessos, erros)
    """
    print(f"\n{'='*70}")
    print(f"📈 CAPTURANDO HISTÓRICO DE PREÇOS ({anos} ANOS)")
    print(f"{'='*70}")
    print(f"Total de tickers: {len(tickers)}")
    print(f"Médias móveis: {', '.join(f'MM{p}' for p in PERIODOS_MM)}")
    print(f"{'='*70}\n")
    
    ok_count = 0
    err_count = 0
    
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] {ticker}...", end=" ")
        
        try:
            ok, msg = processar_ticker(ticker, anos)
            
            if ok:
                ok_count += 1
                print(f"✅ {msg}")
            else:
                err_count += 1
                print(f"⚠️  {msg}")
                
        except Exception as e:
            err_count += 1
            print(f"❌ {type(e).__name__}: {e}")
    
    print(f"\n{'='*70}")
    print(f"RESUMO: ✅ {ok_count} | ❌ {err_count}")
    print(f"{'='*70}\n")
    
    return ok_count, err_count


# ======================================================================================
# CLI
# ======================================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Captura histórico de preços (5 anos) + médias móveis"
    )
    parser.add_argument("--modo", default="quantidade", 
                       choices=["quantidade", "ticker", "lista", "faixa", "todos"])
    parser.add_argument("--quantidade", default="10", type=int)
    parser.add_argument("--ticker", default="")
    parser.add_argument("--lista", default="")
    parser.add_argument("--faixa", default="1-50")
    parser.add_argument("--anos", default=ANOS_HISTORICO, type=int,
                       help="Anos de histórico (padrão: 5)")
    parser.add_argument("--incluir-ibov", action="store_true",
                       help="Incluir IBOVESPA no processamento")
    args = parser.parse_args()
    
    if not HAS_YFINANCE:
        print("❌ Instale yfinance: pip install yfinance")
        return
    
    # Carregar mapeamento
    df = load_mapeamento_b3()
    
    if df is None or len(df) == 0:
        print("❌ Não foi possível carregar mapeamento")
        return
    
    # Filtrar linhas válidas
    if 'cnpj' in df.columns:
        df = df[df["cnpj"].notna()].reset_index(drop=True)
    elif 'CNPJ' in df.columns:
        df = df[df["CNPJ"].notna()].reset_index(drop=True)
    else:
        print("⚠️  Coluna CNPJ não encontrada, usando todos os registros")
    
    # Selecionar tickers
    if args.modo == "quantidade":
        df_sel = df.head(args.quantidade)
    elif args.modo == "ticker":
        ticker_upper = args.ticker.upper()
        df_sel = df[df["ticker"].str.upper().str.contains(ticker_upper, case=False, na=False)]
    elif args.modo == "lista":
        tickers_lista = [t.strip().upper() for t in args.lista.split(",") if t.strip()]
        mask = df["ticker"].str.upper().apply(
            lambda x: any(t in x for t in tickers_lista) if pd.notna(x) else False
        )
        df_sel = df[mask]
    elif args.modo == "faixa":
        inicio, fim = map(int, args.faixa.split("-"))
        df_sel = df.iloc[inicio - 1 : fim]
    elif args.modo == "todos":
        df_sel = df
    else:
        df_sel = df.head(10)
    
    # Extrair TODOS os tickers (incluindo classes separadas)
    tickers = []
    for _, row in df_sel.iterrows():
        ticker_str = str(row["ticker"]).upper().strip()
        tickers.extend([t.strip() for t in ticker_str.split(';') if t.strip()])
    
    # Remover duplicatas preservando ordem
    tickers = list(dict.fromkeys(tickers))
    
    # Adicionar IBOVESPA se solicitado
    if args.incluir_ibov and "IBOV" not in tickers:
        tickers.insert(0, "IBOV")
    
    # Processar
    processar_lote(tickers, args.anos)


if __name__ == "__main__":
    main()
