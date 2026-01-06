"""
ANÁLISE INTELIGENTE DE BALANÇOS - RESUMO 5 ANOS
===============================================
Janeiro 2025

Analisa demonstrações financeiras padronizadas e gera resumo crítico:
- Empresas não financeiras: BPA, BPP, DFC, DRE
- Bancos/Seguradoras: BPA, BPP, DRE (sem DFC)

SAÍDA: balancos/{TICKER}/analise_balancos.json

EXECUÇÃO:
python src/analisar_balancos.py --modo lista --lista "ABEV3,PETR4,ITUB4"
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np


# ======================================================================================
# IDENTIFICAÇÃO DE TIPO DE EMPRESA
# ======================================================================================

SETORES_FINANCEIROS = {
    "intermediários financeiros",
    "bancos",
    "previdência e seguros",
    "seguros",
    "intermediação financeira",
    "banco",
    "seguradora"
}


def load_mapeamento() -> pd.DataFrame:
    """Carrega mapeamento B3 para identificar setor."""
    csv_path = Path("mapeamento_b3_consolidado.csv")
    if not csv_path.exists():
        return pd.DataFrame()
    
    try:
        return pd.read_csv(csv_path, encoding='utf-8-sig', sep=';', on_bad_lines='warn')
    except Exception:
        return pd.DataFrame()


def get_pasta_balanco(ticker: str) -> Path:
    """Retorna pasta do ticker (reutiliza lógica existente)."""
    import re
    
    ticker = str(ticker).upper().strip()
    if ticker == "IBOV":
        return Path("balancos") / "IBOV"
    
    root = Path("balancos")
    base = re.sub(r"\d+$", "", ticker)
    has_suffix = bool(re.search(r"\d+$", ticker))
    if not base:
        base = ticker
        has_suffix = False
    
    exact = root / ticker
    if exact.exists() and exact.is_dir():
        return exact
    
    class_candidates = []
    if root.exists():
        for p in root.iterdir():
            if not p.is_dir():
                continue
            name = p.name.upper()
            if re.fullmatch(re.escape(base) + r"\d+", name):
                class_candidates.append(p)
    
    if class_candidates:
        def _prio(path: Path):
            n = path.name.upper()
            suf = n[len(base):]
            if suf == "11": return (0, n)
            if suf == "4": return (1, n)
            if suf == "3": return (2, n)
            return (9, n)
        return sorted(class_candidates, key=_prio)[0]
    
    base_path = root / base
    if base_path.exists() and base_path.is_dir() and (not has_suffix):
        return base_path
    
    return exact


def identificar_tipo_empresa(ticker: str) -> str:
    """
    Identifica se é empresa financeira ou não.
    
    Returns:
        'financeira' | 'nao_financeira'
    """
    df_map = load_mapeamento()
    
    if not df_map.empty and 'ticker' in df_map.columns and 'setor' in df_map.columns:
        ticker_base = ticker.rstrip('0123456789')
        mask = df_map['ticker'].astype(str).str.upper().str.contains(ticker_base, case=False, na=False)
        empresas = df_map[mask]
        
        if not empresas.empty:
            setor = str(empresas.iloc[0]['setor']).lower().strip()
            if any(s in setor for s in SETORES_FINANCEIROS):
                return 'financeira'
    
    return 'nao_financeira'


# ======================================================================================
# CARREGAMENTO DE DADOS
# ======================================================================================

def carregar_demonstracao(pasta: Path, nome: str) -> Optional[pd.DataFrame]:
    """Carrega demonstração padronizada (CSV)."""
    arquivo = pasta / f"{nome}.csv"
    if not arquivo.exists():
        return None
    
    try:
        df = pd.read_csv(arquivo, encoding='utf-8')
        if len(df) == 0:
            return None
        return df
    except Exception:
        return None


# ======================================================================================
# EXTRAÇÃO DE MÉTRICAS
# ======================================================================================

def extrair_series_temporal(df: pd.DataFrame, conta: str) -> pd.Series:
    """
    Extrai série temporal de uma conta específica.
    
    Args:
        df: DataFrame com colunas cd_conta/conta + períodos (2015T1, 2015T2, ...)
        conta: Nome da conta a buscar
    
    Returns:
        Series com valores ao longo do tempo
    """
    if df is None or len(df) == 0:
        return pd.Series(dtype=float)
    
    # Buscar linha da conta
    if 'ds_conta' in df.columns:
        mask = df['ds_conta'].astype(str).str.lower().str.contains(conta.lower(), case=False, na=False)
    elif 'conta' in df.columns:
        mask = df['conta'].astype(str).str.lower().str.contains(conta.lower(), case=False, na=False)
    else:
        return pd.Series(dtype=float)
    
    linhas = df[mask]
    if len(linhas) == 0:
        return pd.Series(dtype=float)
    
    # Pegar primeira linha encontrada
    linha = linhas.iloc[0]
    
    # Extrair colunas de período (formato: YYYYTQ)
    colunas_periodo = [c for c in df.columns if c not in ['cd_conta', 'conta', 'ds_conta']]
    
    valores = {}
    for col in colunas_periodo:
        try:
            val = float(linha[col])
            if pd.notna(val):
                valores[col] = val
        except (ValueError, TypeError):
            continue
    
    return pd.Series(valores).sort_index()


def obter_valor_valido(valores: pd.Series, direcao: str = 'primeiro') -> Tuple[Optional[float], Optional[int]]:
    """
    Busca primeiro ou último valor válido (não-zero, não-nan) em uma série.
    
    Args:
        valores: Série temporal de valores
        direcao: 'primeiro' ou 'ultimo'
    
    Returns:
        (valor, índice) - valor válido e sua posição na série
    
    Exemplo:
        Series: [0.0, 0.0, 249.11, 260.34, ...]
        obter_valor_valido(series, 'primeiro') → (249.11, 2)
    """
    if len(valores) == 0:
        return None, None
    
    # Filtrar valores válidos (não-nan, não-zero)
    mask = (valores.notna()) & (valores != 0) & (valores.abs() > 0.01)
    valores_validos = valores[mask]
    
    if len(valores_validos) == 0:
        return None, None
    
    if direcao == 'primeiro':
        idx = valores_validos.index[0]
        return valores_validos.iloc[0], list(valores.index).index(idx)
    else:  # 'ultimo'
        idx = valores_validos.index[-1]
        return valores_validos.iloc[-1], list(valores.index).index(idx)


def calcular_cagr(valores: pd.Series, anos: int = 5) -> Optional[float]:
    """
    Calcula CAGR (Compound Annual Growth Rate) usando valores válidos.
    
    CORREÇÃO: Busca automaticamente primeiro e último valor NÃO-ZERO.
    
    Exemplo:
        Series: [0.0, 0.0, 249.11, ..., 786.38]
        CAGR = crescimento de 249.11 → 786.38 (ignora zeros iniciais)
    """
    if len(valores) < 2:
        return None
    
    # Buscar primeiro e último valor válidos
    val_inicio, idx_inicio = obter_valor_valido(valores, 'primeiro')
    val_fim, idx_fim = obter_valor_valido(valores, 'ultimo')
    
    if val_inicio is None or val_fim is None:
        return None
    
    if idx_inicio >= idx_fim:  # Precisa de pelo menos 2 períodos
        return None
    
    if val_inicio <= 0:
        return None
    
    # Calcular número de anos entre primeiro e último valor válido
    num_periodos = idx_fim - idx_inicio
    periodos_anos = num_periodos / 4  # Trimestres para anos
    
    if periodos_anos <= 0:
        return None
    
    try:
        cagr = ((val_fim / val_inicio) ** (1 / periodos_anos) - 1) * 100
        return round(cagr, 2)
    except (ValueError, ZeroDivisionError):
        return None


def calcular_variacao_periodo(valores: pd.Series) -> Optional[float]:
    """
    Calcula variação percentual total usando valores válidos.
    
    CORREÇÃO: Ignora zeros e NaNs no início/fim da série.
    
    Exemplo:
        Series: [0.0, 249.11, ..., 786.38, 0.0]
        Variação = (786.38 - 249.11) / 249.11 × 100
    """
    if len(valores) < 2:
        return None
    
    # Buscar primeiro e último valor válidos
    val_inicio, _ = obter_valor_valido(valores, 'primeiro')
    val_fim, _ = obter_valor_valido(valores, 'ultimo')
    
    if val_inicio is None or val_fim is None:
        return None
    
    if val_inicio == 0:
        return None
    
    try:
        variacao = ((val_fim - val_inicio) / abs(val_inicio)) * 100
        return round(variacao, 2)
    except ZeroDivisionError:
        return None



# ======================================================================================
# ANÁLISE COMPLETA
# ======================================================================================

def analisar_empresa(ticker: str, tipo: str, pasta: Path) -> Dict:
    """
    Realiza análise completa dos balanços.
    
    Args:
        ticker: Código do ticker
        tipo: 'financeira' | 'nao_financeira'
        pasta: Path da pasta do ticker
    
    Returns:
        Dicionário com análise completa
    """
    # Carregar demonstrações
    dre = carregar_demonstracao(pasta, "dre_padronizado")
    bpa = carregar_demonstracao(pasta, "bpa_padronizado")
    bpp = carregar_demonstracao(pasta, "bpp_padronizado")
    dfc = carregar_demonstracao(pasta, "dfc_padronizado") if tipo == 'nao_financeira' else None
    
    if dre is None:
        return {"erro": "DRE não encontrada"}
    
    # Extrair períodos disponíveis
    colunas_periodo = [c for c in dre.columns if c not in ['cd_conta', 'conta', 'ds_conta']]
    if len(colunas_periodo) == 0:
        return {"erro": "Sem dados de períodos"}
    
    periodo_inicio = colunas_periodo[0]
    periodo_fim = colunas_periodo[-1]
    total_trimestres = len(colunas_periodo)
    
    # === MÉTRICAS DE RECEITA ===
    receita = extrair_series_temporal(dre, "Receita de Venda")
    receita_cagr = calcular_cagr(receita) if len(receita) > 0 else None
    receita_var = calcular_variacao_periodo(receita) if len(receita) > 0 else None
    
    # === MÉTRICAS DE RENTABILIDADE ===
    lucro_bruto = extrair_series_temporal(dre, "Resultado Bruto")
    lucro_operacional = extrair_series_temporal(dre, "Resultado Antes do Resultado Financeiro")
    lucro_liquido = extrair_series_temporal(dre, "Lucro/Prejuízo Consolidado")
    
    # Margens médias do período
    margem_bruta = None
    margem_operacional = None
    margem_liquida = None
    
    if len(receita) > 0 and len(lucro_bruto) > 0:
        margens_brutas = (lucro_bruto / receita.loc[lucro_bruto.index]) * 100
        margem_bruta = round(margens_brutas.mean(), 2)
    
    if len(receita) > 0 and len(lucro_operacional) > 0:
        margens_op = (lucro_operacional / receita.loc[lucro_operacional.index]) * 100
        margem_operacional = round(margens_op.mean(), 2)
    
    if len(receita) > 0 and len(lucro_liquido) > 0:
        margens_liq = (lucro_liquido / receita.loc[lucro_liquido.index]) * 100
        margem_liquida = round(margens_liq.mean(), 2)
    
    # === MÉTRICAS DE CAIXA (apenas não financeiras) ===
    caixa_operacional = None
    caixa_livre = None
    
    if dfc is not None:
        fcx_op = extrair_series_temporal(dfc, "Caixa Líquido das Atividades Operacionais")
        fcx_inv = extrair_series_temporal(dfc, "Atividades de Investimento")
        
        if len(fcx_op) > 0:
            caixa_operacional = {
                "media": round(fcx_op.mean() / 1000, 2),  # Em milhões
                "ultimo": round(fcx_op.iloc[-1] / 1000, 2)
            }
        
        if len(fcx_op) > 0 and len(fcx_inv) > 0:
            fcl = fcx_op + fcx_inv
            caixa_livre = {
                "media": round(fcl.mean() / 1000, 2),
                "ultimo": round(fcl.iloc[-1] / 1000, 2)
            }
    
    # === MÉTRICAS DE BALANÇO ===
    ativo_total = extrair_series_temporal(bpa, "Ativo Total") if bpa is not None else pd.Series()
    passivo_total = extrair_series_temporal(bpp, "Passivo Total") if bpp is not None else pd.Series()
    patrimonio = extrair_series_temporal(bpp, "Patrimônio Líquido") if bpp is not None else pd.Series()
    
    # ROE médio
    roe = None
    if len(lucro_liquido) > 0 and len(patrimonio) > 0:
        # Usar patrimônio médio (início + fim) / 2 para cada trimestre
        roes = []
        for periodo in lucro_liquido.index:
            if periodo in patrimonio.index:
                ll = lucro_liquido[periodo]
                pl = patrimonio[periodo]
                if pl > 0:
                    # Anualizar (multiplicar por 4 para ter base anual)
                    roe_trim = (ll * 4 / pl) * 100
                    roes.append(roe_trim)
        
        if len(roes) > 0:
            roe = round(np.mean(roes), 2)
    
    # === ANÁLISE CRÍTICA TEXTUAL ===
    analise_critica = gerar_analise_critica(
        ticker, tipo, receita, lucro_liquido,
        margem_bruta, margem_operacional, margem_liquida,
        roe, caixa_operacional
    )
    
    pontos_fortes, pontos_atencao = identificar_pontos_destaque(
        receita_cagr, margem_liquida, roe, caixa_operacional
    )
    
    # === ESTRUTURA FINAL ===
    return {
        "ticker": ticker,
        "tipo_empresa": tipo,
        "ultima_atualizacao": datetime.now().isoformat(),
        "periodo_analisado": {
            "inicio": periodo_inicio,
            "fim": periodo_fim,
            "total_trimestres": total_trimestres,
            "anos": round(total_trimestres / 4, 1)
        },
        "metricas": {
            "receita": {
                "cagr": receita_cagr,
                "variacao_total": receita_var,
                "ultimo_valor": round(receita.iloc[-1] / 1000, 2) if len(receita) > 0 else None
            },
            "margens": {
                "bruta": margem_bruta,
                "operacional": margem_operacional,
                "liquida": margem_liquida
            },
            "rentabilidade": {
                "roe_medio": roe
            },
            "caixa": caixa_operacional if caixa_operacional else {},
            "balanco": {
                "ativo_total": round(ativo_total.iloc[-1] / 1000, 2) if len(ativo_total) > 0 else None,
                "patrimonio": round(patrimonio.iloc[-1] / 1000, 2) if len(patrimonio) > 0 else None
            }
        },
        "analise_critica": analise_critica,
        "pontos_fortes": pontos_fortes,
        "pontos_atencao": pontos_atencao
    }


def gerar_analise_critica(
    ticker: str, tipo: str,
    receita: pd.Series, lucro: pd.Series,
    mg_bruta: Optional[float], mg_op: Optional[float], mg_liq: Optional[float],
    roe: Optional[float], caixa: Optional[Dict]
) -> str:
    """Gera análise crítica em texto."""
    
    partes = []
    
    # Tendência de receita
    if len(receita) >= 8:  # Pelo menos 2 anos
        rec_ini = receita.iloc[:4].mean()
        rec_fim = receita.iloc[-4:].mean()
        
        if rec_fim > rec_ini * 1.1:
            partes.append(f"{ticker} apresenta trajetória consistente de crescimento de receita no período analisado.")
        elif rec_fim < rec_ini * 0.9:
            partes.append(f"{ticker} enfrenta desafios no crescimento, com receita em tendência de queda.")
        else:
            partes.append(f"{ticker} mantém receita relativamente estável no período.")
    
    # Margens
    if mg_liq is not None:
        if mg_liq > 20:
            partes.append(f"Destaca-se pela alta rentabilidade, com margem líquida média de {mg_liq}%.")
        elif mg_liq > 10:
            partes.append(f"Apresenta rentabilidade saudável com margem líquida de {mg_liq}%.")
        elif mg_liq > 0:
            partes.append(f"Opera com margens comprimidas (margem líquida de {mg_liq}%).")
        else:
            partes.append(f"Enfrenta dificuldades de rentabilidade, apresentando prejuízos recorrentes.")
    
    # ROE
    if roe is not None:
        if roe > 15:
            partes.append(f"Gera excelente retorno sobre o patrimônio (ROE médio de {roe}%).")
        elif roe > 10:
            partes.append(f"Retorno sobre patrimônio adequado (ROE de {roe}%).")
        elif roe > 0:
            partes.append(f"Retorno sobre patrimônio abaixo do esperado (ROE de {roe}%).")
    
    # Caixa (apenas não financeiras)
    if caixa and 'ultimo' in caixa:
        if caixa['ultimo'] > 0:
            partes.append(f"Geração de caixa operacional positiva.")
        else:
            partes.append(f"Apresenta queima de caixa operacional, requerendo atenção.")
    
    return " ".join(partes) if partes else "Dados insuficientes para análise detalhada."


def identificar_pontos_destaque(
    receita_cagr: Optional[float],
    margem_liq: Optional[float],
    roe: Optional[float],
    caixa: Optional[Dict]
) -> Tuple[List[str], List[str]]:
    """Identifica pontos fortes e de atenção."""
    
    fortes = []
    atencao = []
    
    # Receita
    if receita_cagr is not None:
        if receita_cagr > 10:
            fortes.append(f"Forte crescimento de receita (CAGR: {receita_cagr}%)")
        elif receita_cagr < 0:
            atencao.append(f"Receita em queda (CAGR: {receita_cagr}%)")
    
    # Margem
    if margem_liq is not None:
        if margem_liq > 15:
            fortes.append(f"Alta margem de lucro líquido ({margem_liq}%)")
        elif margem_liq < 5:
            atencao.append(f"Margem líquida comprimida ({margem_liq}%)")
    
    # ROE
    if roe is not None:
        if roe > 15:
            fortes.append(f"Excelente retorno sobre patrimônio (ROE: {roe}%)")
        elif roe < 8:
            atencao.append(f"Retorno sobre patrimônio baixo (ROE: {roe}%)")
    
    # Caixa
    if caixa and 'ultimo' in caixa:
        if caixa['ultimo'] > 1000:
            fortes.append("Forte geração de caixa operacional")
        elif caixa['ultimo'] < 0:
            atencao.append("Queima de caixa operacional")
    
    return fortes, atencao


# ======================================================================================
# PROCESSAMENTO
# ======================================================================================

def processar_ticker(ticker: str) -> Tuple[bool, str]:
    """Processa análise de um ticker."""
    try:
        pasta = get_pasta_balanco(ticker)
        
        if not pasta.exists():
            return False, "pasta não encontrada"
        
        tipo = identificar_tipo_empresa(ticker)
        analise = analisar_empresa(ticker, tipo, pasta)
        
        if "erro" in analise:
            return False, analise["erro"]
        
        # Salvar JSON
        arquivo = pasta / "analise_balancos.json"
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(analise, f, ensure_ascii=False, indent=2)
        
        # Resumo para log
        periodo = analise['periodo_analisado']
        anos = periodo['anos']
        tipo_txt = "FINANCEIRA" if tipo == 'financeira' else "NÃO-FINANCEIRA"
        
        return True, f"{tipo_txt} | {anos} anos | Análise completa"
        
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:50]}"


def processar_lote(tickers: List[str]) -> Tuple[int, int]:
    """Processa múltiplos tickers."""
    print(f"\n{'='*70}")
    print(f"📊 ANÁLISE INTELIGENTE DE BALANÇOS")
    print(f"{'='*70}")
    print(f"Total de tickers: {len(tickers)}")
    print(f"{'='*70}\n")
    
    ok_count = 0
    err_count = 0
    
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] {ticker}...", end=" ")
        
        ok, msg = processar_ticker(ticker)
        
        if ok:
            ok_count += 1
            print(f"✅ {msg}")
        else:
            err_count += 1
            print(f"⚠️  {msg}")
    
    print(f"\n{'='*70}")
    print(f"RESUMO: ✅ {ok_count} | ❌ {err_count}")
    print(f"{'='*70}\n")
    
    return ok_count, err_count


# ======================================================================================
# CLI
# ======================================================================================

def main():
    parser = argparse.ArgumentParser(description="Análise inteligente de balanços")
    parser.add_argument("--modo", default="quantidade", 
                       choices=["quantidade", "ticker", "lista", "faixa", "todos"])
    parser.add_argument("--quantidade", default="10", type=int)
    parser.add_argument("--ticker", default="")
    parser.add_argument("--lista", default="")
    parser.add_argument("--faixa", default="1-50")
    args = parser.parse_args()
    
    # Carregar mapeamento
    df = load_mapeamento()
    
    if df is None or len(df) == 0:
        print("❌ Não foi possível carregar mapeamento")
        return
    
    # Filtrar linhas válidas
    if 'cnpj' in df.columns:
        df = df[df["cnpj"].notna()].reset_index(drop=True)
    elif 'CNPJ' in df.columns:
        df = df[df["CNPJ"].notna()].reset_index(drop=True)
    
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
    
    # Extrair tickers
    tickers = []
    for _, row in df_sel.iterrows():
        ticker_str = str(row["ticker"]).upper().strip()
        tickers.extend([t.strip() for t in ticker_str.split(';') if t.strip()])
    
    tickers = list(dict.fromkeys(tickers))
    
    # Processar
    processar_lote(tickers)


if __name__ == "__main__":
    main()
