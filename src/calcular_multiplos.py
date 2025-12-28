#!/usr/bin/env python3
"""
CALCULADORA DE MÚLTIPLOS - PROCESSAMENTO EM LOTE

Calcula múltiplos financeiros para empresas da B3.
Compatível com GitHub Actions workflow.

ARGUMENTOS CLI:
- --modo: quantidade, ticker, lista, faixa
- --quantidade: número de empresas (modo quantidade)
- --ticker: ticker específico (modo ticker)
- --lista: lista de tickers separados por vírgula (modo lista)
- --faixa: faixa de linhas (modo faixa)

SAÍDA:
- balancos/<TICKER>/multiplos.json (LTM)
- balancos/<TICKER>/multiplos.csv (histórico completo)

VERSÃO: 1.2.0
DATA: 2024-12-28
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime
import sys

# Adicionar diretório src ao path
sys.path.insert(0, str(Path(__file__).parent))

# Importar utilitários multi-ticker
try:
    from multi_ticker_utils import (
        get_ticker_principal, 
        get_pasta_balanco, 
        load_mapeamento_consolidado
    )
except ImportError:
    print("⚠️ multi_ticker_utils.py não encontrado, usando implementação básica")
    
    def get_ticker_principal(ticker: str) -> str:
        return ticker.split(';')[0].strip().upper()
    
    def get_pasta_balanco(ticker: str) -> Path:
        ticker_clean = get_ticker_principal(ticker)
        return Path("balancos") / ticker_clean
    
    def load_mapeamento_consolidado() -> pd.DataFrame:
        path_consolidado = Path("mapeamento_b3_consolidado.csv")
        path_original = Path("mapeamento_final_b3_completo_utf8.csv")
        
        if path_consolidado.exists():
            return pd.read_csv(path_consolidado, sep=";", encoding="utf-8-sig")
        elif path_original.exists():
            return pd.read_csv(path_original, sep=";", encoding="utf-8-sig")
        else:
            raise FileNotFoundError("Nenhum arquivo de mapeamento encontrado")


# ======================================================================================
# CLASSE CALCULADORA DE MÚLTIPLOS
# ======================================================================================

class CalculadoraMultiplos:
    """
    Calcula múltiplos financeiros a partir de arquivos padronizados.
    
    VERSÃO: 1.2.0
    CORREÇÕES:
    - Multiplicação por 1.000 nos valores de balanço (escala correta)
    - Implementação completa de Dividend Yield
    - Validação de Market Cap (detecta anomalias)
    """
    
    def __init__(self, ticker: str, pasta_balancos: Path = Path("balancos")):
        self.ticker = ticker.upper().strip()
        self.pasta = pasta_balancos / self.ticker
        
        if not self.pasta.exists():
            raise FileNotFoundError(f"Pasta não encontrada: {self.pasta}")
        
        # Carregar dados
        self.bpa = self._carregar_csv("bpa_padronizado.csv")
        self.bpp = self._carregar_csv("bpp_padronizado.csv")
        self.dre = self._carregar_csv("dre_padronizado.csv")
        self.dfc = self._carregar_csv("dfc_padronizado.csv")
        self.acoes = self._carregar_csv("acoes_historico.csv")
        self.precos = self._carregar_csv("precos_trimestrais.csv")
        self.dividendos = self._carregar_csv("dividendos_trimestrais.csv", required=False)
        
        self.warnings: List[str] = []
    
    def _carregar_csv(self, nome_arquivo: str, required: bool = True) -> Optional[pd.DataFrame]:
        caminho = self.pasta / nome_arquivo
        
        if not caminho.exists():
            if required:
                raise FileNotFoundError(f"Arquivo obrigatório não encontrado: {caminho}")
            return None
        
        try:
            df = pd.read_csv(caminho)
            return df
        except Exception as e:
            if required:
                raise ValueError(f"Erro ao ler {caminho}: {e}")
            return None
    
    def get_valor(self, df: pd.DataFrame, periodo: str, codigo: str) -> Optional[float]:
        """CORREÇÃO v1.2.0: Multiplica por 1.000 (arquivos em R$ MIL)"""
        if df is None or df.empty:
            return None
        
        if periodo not in df.columns:
            return None
        
        linha = df[df['cd_conta'] == codigo]
        if linha.empty:
            return None
        
        valor = linha[periodo].iloc[0]
        
        if pd.isna(valor):
            return None
        
        return float(valor) * 1000.0
    
    def get_preco(self, periodo: str) -> Optional[float]:
        if self.precos is None or self.precos.empty:
            return None
        
        if periodo not in self.precos.columns:
            return None
        
        valor = self.precos[periodo].iloc[0]
        
        if pd.isna(valor):
            return None
        
        return float(valor)
    
    def get_num_acoes_total(self, periodo: str) -> Optional[float]:
        if self.acoes is None or self.acoes.empty:
            return None
        
        if periodo not in self.acoes.columns:
            return None
        
        linha_total = self.acoes[self.acoes['Espécie_Acao'] == 'TOTAL']
        if linha_total.empty:
            return None
        
        valor = linha_total[periodo].iloc[0]
        
        if pd.isna(valor):
            return None
        
        return float(valor)
    
    def get_dividendos_trimestre(self, periodo: str) -> Optional[float]:
        if self.dividendos is None or self.dividendos.empty:
            return None
        
        if periodo not in self.dividendos.columns:
            return None
        
        valor = self.dividendos[periodo].iloc[0]
        
        if pd.isna(valor):
            return None
        
        return float(valor)
    
    def get_periodos_disponiveis(self) -> List[str]:
        import re
        colunas_set = set()
        
        for df in [self.bpa, self.bpp, self.dre, self.dfc, self.precos, self.acoes]:
            if df is not None and not df.empty:
                colunas_periodo = [c for c in df.columns if bool(re.match(r'^\d{4}T[1-4]$', str(c)))]
                colunas_set.update(colunas_periodo)
        
        periodos = sorted(list(colunas_set), key=lambda p: (int(p[:4]), int(p[5])))
        return periodos
    
    def get_ultimos_4_trimestres(self, periodo_referencia: Optional[str] = None) -> List[str]:
        periodos = self.get_periodos_disponiveis()
        
        if not periodos:
            return []
        
        if periodo_referencia is None:
            periodo_referencia = periodos[-1]
        
        try:
            idx = periodos.index(periodo_referencia)
        except ValueError:
            return []
        
        if idx < 3:
            return []
        
        return periodos[idx-3:idx+1]
    
    def calcular_ebitda(self, periodo: str) -> Optional[float]:
        ebit = self.get_valor(self.dre, periodo, "3.05")
        deprec = self.get_valor(self.dfc, periodo, "6.01.DA")
        
        if ebit is None:
            return None
        
        if deprec is None:
            return ebit
        
        return ebit + deprec
    
    def calcular_ebitda_ltm(self, periodo: str) -> Optional[float]:
        trimestres = self.get_ultimos_4_trimestres(periodo)
        if len(trimestres) < 4:
            return None
        
        ebitdas = [self.calcular_ebitda(t) for t in trimestres]
        
        if None in ebitdas:
            return None
        
        return sum(ebitdas)
    
    def calcular_ebit_ltm(self, periodo: str) -> Optional[float]:
        trimestres = self.get_ultimos_4_trimestres(periodo)
        if len(trimestres) < 4:
            return None
        
        ebits = [self.get_valor(self.dre, t, "3.05") for t in trimestres]
        
        if None in ebits:
            return None
        
        return sum(ebits)
    
    def calcular_receita_ltm(self, periodo: str) -> Optional[float]:
        trimestres = self.get_ultimos_4_trimestres(periodo)
        if len(trimestres) < 4:
            return None
        
        receitas = [self.get_valor(self.dre, t, "3.01") for t in trimestres]
        
        if None in receitas:
            return None
        
        return sum(receitas)
    
    def calcular_lucro_liquido_ltm(self, periodo: str) -> Optional[float]:
        trimestres = self.get_ultimos_4_trimestres(periodo)
        if len(trimestres) < 4:
            return None
        
        lucros = [self.get_valor(self.dre, t, "3.11") for t in trimestres]
        
        if None in lucros:
            return None
        
        return sum(lucros)
    
    def calcular_dividendos_ltm(self, periodo: str) -> Optional[float]:
        trimestres = self.get_ultimos_4_trimestres(periodo)
        if len(trimestres) < 4:
            return None
        
        divs = [self.get_dividendos_trimestre(t) for t in trimestres]
        
        if all(d is None for d in divs):
            return None
        
        divs_clean = [d if d is not None else 0.0 for d in divs]
        
        total = sum(divs_clean)
        return total if total > 0 else None
    
    def calcular_market_cap(self, periodo: str) -> Optional[float]:
        preco = self.get_preco(periodo)
        num_acoes = self.get_num_acoes_total(periodo)
        
        if not preco or not num_acoes:
            return None
        
        market_cap = num_acoes * preco
        
        if market_cap > 500_000_000_000:
            self.warnings.append(
                f"Market Cap muito alto em {periodo}: R$ {market_cap/1e9:.1f} bi "
                f"(ações={num_acoes:,.0f}, preço=R${preco:.2f})"
            )
        
        return market_cap
    
    def calcular_enterprise_value(self, periodo: str) -> Optional[float]:
        market_cap = self.calcular_market_cap(periodo)
        
        divida_cp = self.get_valor(self.bpp, periodo, "2.01.04")
        divida_lp = self.get_valor(self.bpp, periodo, "2.02.01")
        caixa = self.get_valor(self.bpa, periodo, "1.01.01")
        
        if market_cap is None:
            return None
        
        divida_total = 0.0
        if divida_cp:
            divida_total += divida_cp
        if divida_lp:
            divida_total += divida_lp
        
        caixa_val = caixa if caixa else 0.0
        
        divida_liquida = divida_total - caixa_val
        
        return market_cap + divida_liquida
    
    def calcular_capital_investido(self, periodo: str) -> Optional[float]:
        pl = self.get_valor(self.bpp, periodo, "2.03")
        
        divida_cp = self.get_valor(self.bpp, periodo, "2.01.04") or 0.0
        divida_lp = self.get_valor(self.bpp, periodo, "2.02.01") or 0.0
        caixa = self.get_valor(self.bpa, periodo, "1.01.01") or 0.0
        
        divida_liquida = (divida_cp + divida_lp) - caixa
        
        if pl is None:
            return None
        
        return pl + divida_liquida
    
    def calcular_pl(self, periodo: str) -> Optional[float]:
        market_cap = self.calcular_market_cap(periodo)
        lucro_ltm = self.calcular_lucro_liquido_ltm(periodo)
        
        if not market_cap or not lucro_ltm or lucro_ltm <= 0:
            return None
        
        return market_cap / lucro_ltm
    
    def calcular_pvp(self, periodo: str) -> Optional[float]:
        market_cap = self.calcular_market_cap(periodo)
        pl = self.get_valor(self.bpp, periodo, "2.03")
        
        if not market_cap or not pl or pl <= 0:
            return None
        
        return market_cap / pl
    
    def calcular_ev_ebitda(self, periodo: str) -> Optional[float]:
        ev = self.calcular_enterprise_value(periodo)
        ebitda_ltm = self.calcular_ebitda_ltm(periodo)
        
        if not ev or not ebitda_ltm or ebitda_ltm <= 0:
            return None
        
        return ev / ebitda_ltm
    
    def calcular_ev_ebit(self, periodo: str) -> Optional[float]:
        ev = self.calcular_enterprise_value(periodo)
        ebit_ltm = self.calcular_ebit_ltm(periodo)
        
        if not ev or not ebit_ltm or ebit_ltm <= 0:
            return None
        
        return ev / ebit_ltm
    
    def calcular_p_ebitda(self, periodo: str) -> Optional[float]:
        market_cap = self.calcular_market_cap(periodo)
        ebitda_ltm = self.calcular_ebitda_ltm(periodo)
        
        if not market_cap or not ebitda_ltm or ebitda_ltm <= 0:
            return None
        
        return market_cap / ebitda_ltm
    
    def calcular_p_ebit(self, periodo: str) -> Optional[float]:
        market_cap = self.calcular_market_cap(periodo)
        ebit_ltm = self.calcular_ebit_ltm(periodo)
        
        if not market_cap or not ebit_ltm or ebit_ltm <= 0:
            return None
        
        return market_cap / ebit_ltm
    
    def calcular_psr(self, periodo: str) -> Optional[float]:
        market_cap = self.calcular_market_cap(periodo)
        receita_ltm = self.calcular_receita_ltm(periodo)
        
        if not market_cap or not receita_ltm or receita_ltm <= 0:
            return None
        
        return market_cap / receita_ltm
    
    def calcular_roe(self, periodo: str) -> Optional[float]:
        lucro_ltm = self.calcular_lucro_liquido_ltm(periodo)
        pl = self.get_valor(self.bpp, periodo, "2.03")
        
        if not lucro_ltm or not pl or pl <= 0:
            return None
        
        return (lucro_ltm / pl) * 100
    
    def calcular_roic(self, periodo: str) -> Optional[float]:
        trimestres = self.get_ultimos_4_trimestres(periodo)
        if len(trimestres) < 4:
            return None
        
        ebit_ltm = self.calcular_ebit_ltm(periodo)
        if not ebit_ltm:
            return None
        
        ir_csll_ltm = sum([
            self.get_valor(self.dre, t, "3.08") or 0.0 
            for t in trimestres
        ])
        
        resultado_antes_tributos_ltm = sum([
            self.get_valor(self.dre, t, "3.07") or 0.0
            for t in trimestres
        ])
        
        if resultado_antes_tributos_ltm and resultado_antes_tributos_ltm != 0:
            aliquota_efetiva = abs(ir_csll_ltm) / abs(resultado_antes_tributos_ltm)
        else:
            aliquota_efetiva = 0.34
        
        nopat = ebit_ltm * (1 - aliquota_efetiva)
        
        capital_investido = self.calcular_capital_investido(periodo)
        if not capital_investido or capital_investido <= 0:
            return None
        
        return (nopat / capital_investido) * 100
    
    def calcular_margem_bruta(self, periodo: str) -> Optional[float]:
        trimestres = self.get_ultimos_4_trimestres(periodo)
        if len(trimestres) < 4:
            return None
        
        resultado_bruto_ltm = sum([
            self.get_valor(self.dre, t, "3.03") or 0.0
            for t in trimestres
        ])
        
        receita_ltm = self.calcular_receita_ltm(periodo)
        
        if not receita_ltm or receita_ltm <= 0:
            return None
        
        return (resultado_bruto_ltm / receita_ltm) * 100
    
    def calcular_margem_ebit(self, periodo: str) -> Optional[float]:
        ebit_ltm = self.calcular_ebit_ltm(periodo)
        receita_ltm = self.calcular_receita_ltm(periodo)
        
        if not ebit_ltm or not receita_ltm or receita_ltm <= 0:
            return None
        
        return (ebit_ltm / receita_ltm) * 100
    
    def calcular_margem_ebitda(self, periodo: str) -> Optional[float]:
        ebitda_ltm = self.calcular_ebitda_ltm(periodo)
        receita_ltm = self.calcular_receita_ltm(periodo)
        
        if not ebitda_ltm or not receita_ltm or receita_ltm <= 0:
            return None
        
        return (ebitda_ltm / receita_ltm) * 100
    
    def calcular_margem_liquida(self, periodo: str) -> Optional[float]:
        lucro_ltm = self.calcular_lucro_liquido_ltm(periodo)
        receita_ltm = self.calcular_receita_ltm(periodo)
        
        if not lucro_ltm or not receita_ltm or receita_ltm <= 0:
            return None
        
        return (lucro_ltm / receita_ltm) * 100
    
    def calcular_dy(self, periodo: str) -> Optional[float]:
        """CORREÇÃO v1.2.0: Implementação completa"""
        dividendos_ltm = self.calcular_dividendos_ltm(periodo)
        preco = self.get_preco(periodo)
        
        if not dividendos_ltm or not preco or preco <= 0:
            return None
        
        dy = (dividendos_ltm / preco) * 100
        return round(dy, 2)
    
    def calcular_payout(self, periodo: str) -> Optional[float]:
        dividendos_ltm = self.calcular_dividendos_ltm(periodo)
        lucro_ltm = self.calcular_lucro_liquido_ltm(periodo)
        num_acoes = self.get_num_acoes_total(periodo)
        
        if not dividendos_ltm or not lucro_ltm or not num_acoes:
            return None
        
        if lucro_ltm <= 0:
            return None
        
        dividendos_totais = dividendos_ltm * num_acoes
        
        payout = (dividendos_totais / lucro_ltm) * 100
        
        return round(payout, 2)
    
    def calcular_divida_liquida_pl(self, periodo: str) -> Optional[float]:
        divida_cp = self.get_valor(self.bpp, periodo, "2.01.04") or 0.0
        divida_lp = self.get_valor(self.bpp, periodo, "2.02.01") or 0.0
        caixa = self.get_valor(self.bpa, periodo, "1.01.01") or 0.0
        pl = self.get_valor(self.bpp, periodo, "2.03")
        
        if not pl or pl <= 0:
            return None
        
        divida_liquida = (divida_cp + divida_lp) - caixa
        
        return divida_liquida / pl
    
    def calcular_divida_liquida_ebitda(self, periodo: str) -> Optional[float]:
        divida_cp = self.get_valor(self.bpp, periodo, "2.01.04") or 0.0
        divida_lp = self.get_valor(self.bpp, periodo, "2.02.01") or 0.0
        caixa = self.get_valor(self.bpa, periodo, "1.01.01") or 0.0
        ebitda_ltm = self.calcular_ebitda_ltm(periodo)
        
        if not ebitda_ltm or ebitda_ltm <= 0:
            return None
        
        divida_liquida = (divida_cp + divida_lp) - caixa
        
        return divida_liquida / ebitda_ltm
    
    def calcular_liquidez_corrente(self, periodo: str) -> Optional[float]:
        ativo_circulante = self.get_valor(self.bpa, periodo, "1.01")
        passivo_circulante = self.get_valor(self.bpp, periodo, "2.01")
        
        if not ativo_circulante or not passivo_circulante or passivo_circulante <= 0:
            return None
        
        return ativo_circulante / passivo_circulante
    
    def calcular_vpa(self, periodo: str) -> Optional[float]:
        pl = self.get_valor(self.bpp, periodo, "2.03")
        num_acoes = self.get_num_acoes_total(periodo)
        
        if not pl or not num_acoes or num_acoes <= 0:
            return None
        
        return pl / num_acoes
    
    def calcular_lpa(self, periodo: str) -> Optional[float]:
        lucro_ltm = self.calcular_lucro_liquido_ltm(periodo)
        num_acoes = self.get_num_acoes_total(periodo)
        
        if not lucro_ltm or not num_acoes or num_acoes <= 0:
            return None
        
        return lucro_ltm / num_acoes
    
    def calcular_todos_multiplos(self, periodo: str) -> Dict[str, Any]:
        """Calcula todos os múltiplos para um período específico."""
        resultado = {
            'ticker': self.ticker,
            'periodo': periodo,
            'data_calculo': datetime.now().isoformat(),
            
            # VALUATION
            'P/L': self.calcular_pl(periodo),
            'P/VP': self.calcular_pvp(periodo),
            'EV/EBITDA': self.calcular_ev_ebitda(periodo),
            'EV/EBIT': self.calcular_ev_ebit(periodo),
            'P/EBITDA': self.calcular_p_ebitda(periodo),
            'P/EBIT': self.calcular_p_ebit(periodo),
            'PSR': self.calcular_psr(periodo),
            
            # RENTABILIDADE
            'ROE': self.calcular_roe(periodo),
            'ROIC': self.calcular_roic(periodo),
            'Margem_Bruta': self.calcular_margem_bruta(periodo),
            'Margem_EBIT': self.calcular_margem_ebit(periodo),
            'Margem_EBITDA': self.calcular_margem_ebitda(periodo),
            'Margem_Liquida': self.calcular_margem_liquida(periodo),
            
            # DIVIDENDOS
            'Dividend_Yield': self.calcular_dy(periodo),
            'Payout': self.calcular_payout(periodo),
            
            # ENDIVIDAMENTO
            'Divida_Liquida_PL': self.calcular_divida_liquida_pl(periodo),
            'Divida_Liquida_EBITDA': self.calcular_divida_liquida_ebitda(periodo),
            
            # LIQUIDEZ
            'Liquidez_Corrente': self.calcular_liquidez_corrente(periodo),
            'VPA': self.calcular_vpa(periodo),
            'LPA': self.calcular_lpa(periodo),
            
            # DADOS BASE
            'Preco': self.get_preco(periodo),
            'Num_Acoes': self.get_num_acoes_total(periodo),
            'Market_Cap': self.calcular_market_cap(periodo),
            'Patrimonio_Liquido': self.get_valor(self.bpp, periodo, "2.03"),
            'Lucro_Liquido_LTM': self.calcular_lucro_liquido_ltm(periodo),
            'Receita_LTM': self.calcular_receita_ltm(periodo),
            'EBITDA_LTM': self.calcular_ebitda_ltm(periodo),
            'EBIT_LTM': self.calcular_ebit_ltm(periodo),
        }
        
        return resultado
    
    def calcular_multiplos_historico(self) -> pd.DataFrame:
        """Calcula múltiplos para todos os períodos disponíveis."""
        periodos = self.get_periodos_disponiveis()
        
        resultados = []
        for periodo in periodos:
            try:
                multiplos = self.calcular_todos_multiplos(periodo)
                resultados.append(multiplos)
            except Exception:
                continue
        
        if not resultados:
            return pd.DataFrame()
        
        df = pd.DataFrame(resultados)
        
        cols_order = ['ticker', 'periodo', 'data_calculo']
        outras_cols = [c for c in df.columns if c not in cols_order]
        df = df[cols_order + outras_cols]
        
        return df
    
    def gerar_relatorio_ltm(self) -> Dict[str, Any]:
        """Gera relatório completo com múltiplos LTM."""
        periodos = self.get_periodos_disponiveis()
        if not periodos:
            raise ValueError("Nenhum período disponível para cálculo")
        
        ultimo_periodo = periodos[-1]
        multiplos = self.calcular_todos_multiplos(ultimo_periodo)
        
        relatorio = {
            'multiplos': multiplos,
            'warnings': self.warnings,
            'info': {
                'total_periodos_disponiveis': len(periodos),
                'periodo_mais_antigo': periodos[0],
                'periodo_mais_recente': periodos[-1],
                'tem_dividendos': self.dividendos is not None
            }
        }
        
        return relatorio


# ======================================================================================
# PROCESSAMENTO EM LOTE
# ======================================================================================

def processar_ticker(ticker: str, pasta_balancos: Path = Path("balancos")) -> tuple[bool, str]:
    """
    Processa um ticker e salva multiplos.json e multiplos.csv.
    
    Returns:
        (sucesso, mensagem)
    """
    try:
        calc = CalculadoraMultiplos(ticker, pasta_balancos)
        
        # Gerar relatório LTM (JSON)
        relatorio = calc.gerar_relatorio_ltm()
        
        # Salvar JSON
        json_path = calc.pasta / "multiplos.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False, default=str)
        
        # Gerar histórico completo (CSV)
        df_historico = calc.calcular_multiplos_historico()
        
        # Salvar CSV
        csv_path = calc.pasta / "multiplos.csv"
        df_historico.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        # Estatísticas
        periodo_ltm = relatorio['multiplos']['periodo']
        n_periodos = len(df_historico)
        
        msg = f"JSON+CSV | LTM={periodo_ltm} | períodos={n_periodos}"
        
        if relatorio['warnings']:
            msg += f" | AVISOS={len(relatorio['warnings'])}"
        
        return True, msg
        
    except FileNotFoundError as e:
        return False, f"arquivos ausentes ({e})"
    except Exception as e:
        return False, f"erro ({type(e).__name__}: {e})"


def main():
    parser = argparse.ArgumentParser(
        description='Calculadora de Múltiplos - Processamento em Lote v1.2.0'
    )
    parser.add_argument(
        '--modo',
        choices=['quantidade', 'ticker', 'lista', 'faixa'],
        default='quantidade',
        help='Modo de seleção'
    )
    parser.add_argument(
        '--quantidade',
        default='10',
        help='Quantidade de empresas (modo quantidade)'
    )
    parser.add_argument(
        '--ticker',
        default='',
        help='Ticker único (modo ticker)'
    )
    parser.add_argument(
        '--lista',
        default='',
        help='Lista de tickers separados por vírgula (modo lista)'
    )
    parser.add_argument(
        '--faixa',
        default='1-50',
        help='Faixa de linhas (modo faixa)'
    )
    
    args = parser.parse_args()
    
    # Carregar mapeamento
    try:
        df = load_mapeamento_consolidado()
        df = df[df["cnpj"].notna()].reset_index(drop=True)
    except Exception as e:
        print(f"❌ Erro ao carregar mapeamento: {e}")
        return 1
    
    # Seleção de tickers
    if args.modo == 'quantidade':
        limite = int(args.quantidade)
        df_sel = df.head(limite)
    
    elif args.modo == 'ticker':
        ticker_upper = args.ticker.upper()
        df_sel = df[df['ticker'].str.upper().str.contains(
            ticker_upper, case=False, na=False, regex=False
        )]
    
    elif args.modo == 'lista':
        tickers = [t.strip().upper() for t in args.lista.split(',') if t.strip()]
        mask = df['ticker'].str.upper().apply(
            lambda x: any(t in x for t in tickers) if pd.notna(x) else False
        )
        df_sel = df[mask]
    
    elif args.modo == 'faixa':
        inicio, fim = map(int, args.faixa.split('-'))
        df_sel = df.iloc[inicio - 1: fim]
    
    else:
        df_sel = df.head(10)
    
    # Exibir info
    print(f"\n{'='*70}")
    print(f">>> CALCULAR MÚLTIPLOS FINANCEIROS v1.2.0 <<<")
    print(f"{'='*70}")
    print(f"Modo: {args.modo}")
    print(f"Empresas: {len(df_sel)}")
    print(f"Saída: balancos/<TICKER>/multiplos.json + multiplos.csv")
    print(f"{'='*70}\n")
    
    # Processar
    ok_count = 0
    err_count = 0
    
    for _, row in df_sel.iterrows():
        ticker_str = str(row['ticker']).upper().strip()
        ticker = ticker_str.split(';')[0] if ';' in ticker_str else ticker_str
        
        ok, msg = processar_ticker(ticker)
        
        if ok:
            ok_count += 1
            print(f"✅ {ticker}: {msg}")
        else:
            err_count += 1
            print(f"❌ {ticker}: {msg}")
    
    print(f"\n{'='*70}")
    print(f"Finalizado: OK={ok_count} | ERRO={err_count}")
    print(f"{'='*70}\n")
    
    return 0


if __name__ == '__main__':
    exit(main())
