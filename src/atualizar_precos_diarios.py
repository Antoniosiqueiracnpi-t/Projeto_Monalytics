# src/atualizar_precos_diarios.py
"""
Atualização Diária de Preços e Múltiplos de Valuation
=====================================================
Este script:
1. Baixa preços de fechamento do dia anterior para todas as empresas
2. Atualiza os arquivos precos_trimestrais.csv
3. Recalcula APENAS os múltiplos de valuation (que dependem de preço):
   - P/L, P/VPA, EV/EBITDA, EV/EBIT, EV/Receita, DY
4. Mantém intactos os múltiplos fundamentalistas (ROE, ROA, etc)

Fonte de dados: yfinance (Yahoo Finance)
Periodicidade: Execução diária (após fechamento do mercado)
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

# Importar utilitários do projeto
sys.path.insert(0, str(Path(__file__).parent))
from multi_ticker_utils import get_ticker_principal, get_pasta_balanco, load_mapeamento_consolidado

# Tentar importar yfinance
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    print("⚠️  yfinance não instalado. Execute: pip install yfinance")


# ======================================================================================
# CONFIGURAÇÕES
# ======================================================================================

# Empresas financeiras (excluídas)
TICKERS_FINANCEIROS = {
    "RPAD3", "RPAD5", "RPAD6", "ABCB4", "BMGB4", "BBDC3", "BBDC4",
    "BPAC3", "BPAC5", "BPAC11", "BSLI3", "BSLI4", "BBAS3", "BGIP3",
    "BGIP4", "BPAR3", "BRSR3", "BRSR5", "BRSR6", "BNBR3", "BMIN3",
    "BMIN4", "BMEB3", "BMEB4", "BPAN4", "PINE3", "PINE4", "SANB3",
    "SANB4", "SANB11", "BEES3", "BEES4", "ITUB3", "ITUB4",
    "BBSE3", "CXSE3", "IRBR3", "PSSA3",
}

# Mapeamento de códigos B3 para Yahoo Finance
# Exemplos: PETR4 → PETR4.SA, VALE3 → VALE3.SA
SUFIXO_YAHOO = ".SA"


# ======================================================================================
# FUNÇÕES DE DOWNLOAD DE PREÇOS
# ======================================================================================

def _ticker_para_yahoo(ticker: str) -> str:
    """Converte ticker B3 para formato Yahoo Finance."""
    ticker_clean = ticker.upper().strip()
    if not ticker_clean.endswith(SUFIXO_YAHOO):
        return f"{ticker_clean}{SUFIXO_YAHOO}"
    return ticker_clean


def baixar_preco_ultimo_dia(ticker: str, max_dias_atras: int = 10) -> Optional[Dict[str, float]]:
    """
    Baixa o preço de fechamento ajustado do último dia disponível.
    
    Args:
        ticker: Ticker B3 (ex: PETR4, VALE3)
        max_dias_atras: Máximo de dias para buscar retroativamente
    
    Returns:
        {
            'data': 'YYYY-MM-DD',
            'preco_fechamento': float,
            'preco_ajustado': float,
            'volume': float
        }
    """
    if not HAS_YFINANCE:
        return None
    
    ticker_yahoo = _ticker_para_yahoo(ticker)
    
    try:
        # Baixar últimos N dias
        end_date = datetime.now()
        start_date = end_date - timedelta(days=max_dias_atras)
        
        stock = yf.Ticker(ticker_yahoo)
        hist = stock.history(start=start_date, end=end_date)
        
        if hist.empty:
            return None
        
        # Pegar último dia disponível
        last_row = hist.iloc[-1]
        last_date = hist.index[-1]
        
        return {
            'data': last_date.strftime('%Y-%m-%d'),
            'preco_fechamento': float(last_row['Close']),
            'preco_ajustado': float(last_row['Close']),  # yfinance já retorna ajustado
            'volume': float(last_row['Volume']) if 'Volume' in last_row else 0.0
        }
        
    except Exception as e:
        print(f"⚠️  Erro ao baixar {ticker}: {e}")
        return None


def baixar_precos_lote(tickers: List[str], max_workers: int = 10) -> Dict[str, Optional[Dict]]:
    """
    Baixa preços para múltiplos tickers em paralelo.
    
    Returns:
        {ticker: dados_preco}
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    resultados = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(baixar_preco_ultimo_dia, ticker): ticker 
            for ticker in tickers
        }
        
        for future in as_completed(futures):
            ticker = futures[future]
            try:
                dados = future.result()
                resultados[ticker] = dados
            except Exception as e:
                print(f"❌ Erro em {ticker}: {e}")
                resultados[ticker] = None
    
    return resultados


# ======================================================================================
# ATUALIZAÇÃO DE ARQUIVOS PRECOS_TRIMESTRAIS.CSV
# ======================================================================================

def atualizar_arquivo_precos(ticker: str, preco_novo: Dict[str, float]) -> bool:
    """
    Atualiza o arquivo precos_trimestrais.csv com novo preço.
    
    Estratégia:
    - Se já existe coluna para o trimestre atual, atualiza
    - Se não existe, cria nova coluna
    """
    pasta = get_pasta_balanco(ticker)
    arquivo_precos = pasta / "precos_trimestrais.csv"
    
    if not arquivo_precos.exists():
        print(f"⚠️  {ticker}: arquivo precos_trimestrais.csv não existe")
        return False
    
    try:
        df = pd.read_csv(arquivo_precos)
        
        # Determinar trimestre atual
        data_preco = datetime.strptime(preco_novo['data'], '%Y-%m-%d')
        ano = data_preco.year
        mes = data_preco.month
        
        # Calcular trimestre: T1=jan-mar, T2=abr-jun, T3=jul-set, T4=out-dez
        trimestre = (mes - 1) // 3 + 1
        periodo = f"{ano}T{trimestre}"
        
        # Verificar se coluna já existe
        if periodo in df.columns:
            # Atualizar valor existente
            if 'preco_fechamento' in df.columns or len(df) > 0:
                df.loc[0, periodo] = preco_novo['preco_ajustado']
            else:
                df[periodo] = [preco_novo['preco_ajustado']]
        else:
            # Adicionar nova coluna
            df[periodo] = [preco_novo['preco_ajustado']]
        
        # Salvar
        df.to_csv(arquivo_precos, index=False)
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar {ticker}: {e}")
        return False


# ======================================================================================
# RECÁLCULO DE MÚLTIPLOS DE VALUATION
# ======================================================================================

def recalcular_multiplos_valuation(ticker: str) -> bool:
    """
    Recalcula APENAS os múltiplos de valuation que dependem de preço:
    - P/L, P/VPA, EV/EBITDA, EV/EBIT, EV/Receita, DY
    
    Estratégia:
    1. Carregar multiplos.json existente
    2. Recalcular Market Cap com novo preço
    3. Recalcular EV
    4. Recalcular múltiplos de valuation
    5. Manter todos os outros múltiplos intactos
    6. Salvar multiplos.json atualizado
    """
    pasta = get_pasta_balanco(ticker)
    arquivo_multiplos = pasta / "multiplos.json"
    
    if not arquivo_multiplos.exists():
        print(f"⚠️  {ticker}: arquivo multiplos.json não existe")
        return False
    
    try:
        # Carregar JSON existente
        with open(arquivo_multiplos, 'r', encoding='utf-8') as f:
            dados_multiplos = json.load(f)
        
        # Importar função de cálculo do script original
        from calcular_multiplos import (
            carregar_dados_empresa,
            _calcular_market_cap,
            _calcular_ev,
            _calcular_ltm,
            _obter_valor_pontual,
            _safe_divide,
            _normalizar_valor,
            CONTAS_DRE,
            CONTAS_BPP
        )
        
        # Carregar dados da empresa
        dados = carregar_dados_empresa(ticker)
        
        if not dados.periodos:
            print(f"⚠️  {ticker}: sem períodos disponíveis")
            return False
        
        # Determinar período atual (último trimestre com balanço)
        ultimo_periodo = dados.periodos[-1]
        
        # Recalcular Market Cap e EV
        market_cap = _calcular_market_cap(dados, ultimo_periodo)
        ev = _calcular_ev(dados, ultimo_periodo)
        
        if not np.isfinite(market_cap):
            print(f"⚠️  {ticker}: Market Cap inválido (falta preço/ações)")
            return False
        
        # Obter componentes para cálculo
        ll_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["lucro_liquido"], ultimo_periodo)
        pl = _obter_valor_pontual(dados.bpp, CONTAS_BPP["patrimonio_liquido"], ultimo_periodo)
        
        from calcular_multiplos import _calcular_ebitda_ltm
        ebitda_ltm = _calcular_ebitda_ltm(dados, ultimo_periodo)
        ebit_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["ebit"], ultimo_periodo)
        receita_ltm = _calcular_ltm(dados, dados.dre, CONTAS_DRE["receita"], ultimo_periodo)
        
        # Atualizar múltiplos de valuation no LTM
        ltm_multiplos = dados_multiplos.get("ltm", {}).get("multiplos", {})
        
        ltm_multiplos["P_L"] = _normalizar_valor(_safe_divide(market_cap, ll_ltm))
        ltm_multiplos["P_VPA"] = _normalizar_valor(_safe_divide(market_cap, pl))
        ltm_multiplos["EV_EBITDA"] = _normalizar_valor(_safe_divide(ev, ebitda_ltm))
        ltm_multiplos["EV_EBIT"] = _normalizar_valor(_safe_divide(ev, ebit_ltm))
        ltm_multiplos["EV_RECEITA"] = _normalizar_valor(_safe_divide(ev, receita_ltm))
        
        # Atualizar data de cálculo
        dados_multiplos["ltm"]["data_calculo"] = datetime.now().isoformat()
        dados_multiplos["ltm"]["multiplos"] = ltm_multiplos
        
        # Atualizar último ano do histórico anual se for o mesmo período
        historico_anual = dados_multiplos.get("historico_anual", {})
        
        ano_atual = int(ultimo_periodo[:4])
        if str(ano_atual) in historico_anual:
            periodo_ref_ano = historico_anual[str(ano_atual)].get("periodo_referencia", "")
            
            if periodo_ref_ano == ultimo_periodo:
                historico_anual[str(ano_atual)]["multiplos"].update({
                    "P_L": ltm_multiplos["P_L"],
                    "P_VPA": ltm_multiplos["P_VPA"],
                    "EV_EBITDA": ltm_multiplos["EV_EBITDA"],
                    "EV_EBIT": ltm_multiplos["EV_EBIT"],
                    "EV_RECEITA": ltm_multiplos["EV_RECEITA"],
                })
        
        # Salvar JSON atualizado
        with open(arquivo_multiplos, 'w', encoding='utf-8') as f:
            json.dump(dados_multiplos, f, ensure_ascii=False, indent=2, default=str)
        
        # Atualizar CSV também
        from calcular_multiplos import _salvar_csv_historico
        csv_path = pasta / "multiplos.csv"
        _salvar_csv_historico(dados_multiplos, csv_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao recalcular {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return False


# ======================================================================================
# PROCESSADOR PRINCIPAL
# ======================================================================================

def processar_atualizacao_diaria(
    modo: str = "quantidade",
    quantidade: int = 10,
    ticker: str = "",
    lista: str = "",
    faixa: str = "1-50"
) -> Tuple[int, int, int]:
    """
    Processa atualização diária de preços e múltiplos.
    
    Returns:
        (sucesso, sem_preco, erro)
    """
    if not HAS_YFINANCE:
        print("❌ yfinance não está instalado!")
        print("Execute: pip install yfinance")
        return 0, 0, 0
    
    # Carregar mapeamento
    df = load_mapeamento_consolidado()
    df = df[df["cnpj"].notna()].reset_index(drop=True)
    
    # Selecionar empresas
    if modo == "quantidade":
        df_sel = df.head(quantidade)
    elif modo == "ticker":
        ticker_upper = ticker.upper()
        df_sel = df[df["ticker"].str.upper().str.contains(ticker_upper, case=False, na=False)]
    elif modo == "lista":
        tickers = [t.strip().upper() for t in lista.split(",") if t.strip()]
        mask = df["ticker"].str.upper().apply(
            lambda x: any(t in x for t in tickers) if pd.notna(x) else False
        )
        df_sel = df[mask]
    elif modo == "faixa":
        inicio, fim = map(int, faixa.split("-"))
        df_sel = df.iloc[inicio - 1 : fim]
    else:
        df_sel = df.head(10)
    
    print(f"\n{'='*70}")
    print(f">>> ATUALIZAÇÃO DIÁRIA DE PREÇOS E MÚLTIPLOS DE VALUATION <<<")
    print(f"{'='*70}")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Modo: {modo} | Selecionadas: {len(df_sel)}")
    print(f"{'='*70}\n")
    
    # Filtrar tickers não-financeiros
    tickers_processar = []
    for _, row in df_sel.iterrows():
        ticker_str = str(row["ticker"]).upper().strip()
        ticker_clean = ticker_str.split(';')[0] if ';' in ticker_str else ticker_str
        
        if ticker_clean not in TICKERS_FINANCEIROS:
            tickers_processar.append(ticker_clean)
    
    print(f"Tickers não-financeiros: {len(tickers_processar)}")
    print(f"Baixando preços...\n")
    
    # Baixar preços em lote
    precos = baixar_precos_lote(tickers_processar, max_workers=10)
    
    # Processar cada ticker
    ok_count = 0
    sem_preco_count = 0
    err_count = 0
    
    for ticker_clean in tickers_processar:
        preco_dados = precos.get(ticker_clean)
        
        if preco_dados is None:
            sem_preco_count += 1
            print(f"⏭️  {ticker_clean}: sem dados de preço")
            continue
        
        try:
            # 1. Atualizar arquivo de preços
            if not atualizar_arquivo_precos(ticker_clean, preco_dados):
                err_count += 1
                continue
            
            # 2. Recalcular múltiplos de valuation
            if recalcular_multiplos_valuation(ticker_clean):
                ok_count += 1
                print(f"✅ {ticker_clean}: preço={preco_dados['preco_ajustado']:.2f} | data={preco_dados['data']}")
            else:
                err_count += 1
                
        except Exception as e:
            err_count += 1
            print(f"❌ {ticker_clean}: ERRO - {type(e).__name__}: {e}")
    
    print(f"\n{'='*70}")
    print(f"RESUMO: OK={ok_count} | SEM_PREÇO={sem_preco_count} | ERRO={err_count}")
    print(f"{'='*70}\n")
    
    return ok_count, sem_preco_count, err_count


# ======================================================================================
# CLI
# ======================================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Atualização Diária de Preços e Múltiplos de Valuation"
    )
    parser.add_argument("--modo", default="quantidade", 
                       choices=["quantidade", "ticker", "lista", "faixa"])
    parser.add_argument("--quantidade", default="10", type=int)
    parser.add_argument("--ticker", default="")
    parser.add_argument("--lista", default="")
    parser.add_argument("--faixa", default="1-50")
    args = parser.parse_args()
    
    processar_atualizacao_diaria(
        modo=args.modo,
        quantidade=args.quantidade,
        ticker=args.ticker,
        lista=args.lista,
        faixa=args.faixa
    )


if __name__ == "__main__":
    main()
