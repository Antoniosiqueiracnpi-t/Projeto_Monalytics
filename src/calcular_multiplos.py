"""
CALCULADORA DE MÚLTIPLOS FINANCEIROS - v1.2.0

CORREÇÕES NESTA VERSÃO:
========================
✅ ESCALA DE BALANÇO: Multiplicação por 1.000 (arquivos estão em R$ MIL)
✅ DIVIDEND YIELD: Implementação completa e funcional
✅ VALIDAÇÃO: Detecção de anomalias em Market Cap
✅ COMPATIBILIDADE: Mantém suporte total para empresas sem dividendos

PARTICULARIDADES IDENTIFICADAS:
===============================
1. Balanços: valores em R$ MIL (multiplicar por 1.000)
2. Ações: número absoluto de ações (não dividir)
3. Preços: em REAIS por ação (não converter)
4. Dividendos: em REAIS por ação (somar para LTM)

FONTE DE DADOS:
- Balanços: arquivos *_padronizado.csv (BPA, BPP, DRE, DFC)
- Ações: acoes_historico.csv (FRE - Formulário de Referência)
- Preços: precos_trimestrais.csv (yfinance - ajustados)
- Dividendos: dividendos_trimestrais.csv (B3 API / OkaneBox)

MÚLTIPLOS CALCULADOS:
====================
VALUATION:
- P/L (Price/Earnings)
- P/VP (Price/Book Value)  
- EV/EBITDA
- EV/EBIT
- P/EBITDA
- P/EBIT
- PSR (Price/Sales Ratio)

RENTABILIDADE:
- ROE (Return on Equity)
- ROIC (Return on Invested Capital) - usando alíquota efetiva
- Margem Bruta
- Margem EBIT
- Margem EBITDA
- Margem Líquida

DIVIDENDOS:
- Dividend Yield (DY)
- Payout Ratio

ENDIVIDAMENTO:
- Dívida Líquida / PL
- Dívida Líquida / EBITDA

LIQUIDEZ:
- Liquidez Corrente
- VPA (Valor Patrimonial por Ação)
- LPA (Lucro por Ação)

PERÍODOS CALCULADOS:
===================
- LTM (Last Twelve Months) - 4 últimos trimestres disponíveis
- Trimestral - todos os trimestres com dados completos
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import argparse
import json


# ======================================================================================
# CLASSE PRINCIPAL
# ======================================================================================

class CalculadoraMultiplos:
    """
    Calcula múltiplos financeiros a partir de arquivos padronizados.
    
    VERSÃO: 1.2.0
    DATA: 2024-12-28
    
    CORREÇÕES v1.2.0:
    ----------------
    1. Multiplicação por 1.000 nos valores de balanço (escala correta)
    2. Implementação completa de Dividend Yield
    3. Validação de Market Cap (detecta anomalias)
    4. Compatibilidade total com empresas sem dividendos
    """
    
    def __init__(self, ticker: str, pasta_balancos: Path = Path("balancos")):
        """
        Inicializa calculadora para um ticker específico.
        
        Args:
            ticker: Código do ativo (ex: PETR4, VALE3)
            pasta_balancos: Pasta raiz dos balanços
        """
        self.ticker = ticker.upper().strip()
        self.pasta = pasta_balancos / self.ticker
        
        # Validar pasta
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
        
        # Warnings acumulados
        self.warnings: List[str] = []
    
    # ==================================================================================
    # UTILITÁRIOS - CARREGAMENTO
    # ==================================================================================
    
    def _carregar_csv(self, nome_arquivo: str, required: bool = True) -> Optional[pd.DataFrame]:
        """
        Carrega arquivo CSV da pasta do ticker.
        
        Args:
            nome_arquivo: Nome do arquivo CSV
            required: Se True, lança exceção se arquivo não existir
        
        Returns:
            DataFrame ou None (se required=False e arquivo não existe)
        """
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
    
    # ==================================================================================
    # UTILITÁRIOS - EXTRAÇÃO DE VALORES
    # ==================================================================================
    
    def get_valor(self, df: pd.DataFrame, periodo: str, codigo: str) -> Optional[float]:
        """
        Retorna valor de uma conta contábil para um período.
        
        CORREÇÃO v1.2.0: Multiplica por 1.000 pois arquivos estão em R$ MIL
        
        Args:
            df: DataFrame com dados padronizados (BPA, BPP, DRE, DFC)
            periodo: Período no formato AAAATX (ex: 2024T4)
            codigo: Código da conta (ex: 1, 1.01, 3.11)
        
        Returns:
            Valor em REAIS (após conversão) ou None se não encontrado
        """
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
        
        # CORREÇÃO v1.2.0: Multiplicar por 1.000 (arquivos em R$ mil)
        return float(valor) * 1000.0
    
    def get_preco(self, periodo: str) -> Optional[float]:
        """
        Retorna preço de fechamento ajustado para um período.
        
        Args:
            periodo: Período no formato AAAATX (ex: 2024T4)
        
        Returns:
            Preço em REAIS por ação ou None se não encontrado
        """
        if self.precos is None or self.precos.empty:
            return None
        
        if periodo not in self.precos.columns:
            return None
        
        valor = self.precos[periodo].iloc[0]
        
        if pd.isna(valor):
            return None
        
        # Preços já estão em REAIS (não precisa conversão)
        return float(valor)
    
    def get_num_acoes_total(self, periodo: str) -> Optional[float]:
        """
        Retorna número total de ações para um período.
        
        Args:
            periodo: Período no formato AAAATX (ex: 2024T4)
        
        Returns:
            Número de ações ou None se não encontrado
        """
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
        
        # Ações já estão em unidades absolutas (não precisa conversão)
        return float(valor)
    
    def get_dividendos_trimestre(self, periodo: str) -> Optional[float]:
        """
        Retorna dividendos pagos em um trimestre específico.
        
        Args:
            periodo: Período no formato AAAATX (ex: 2024T4)
        
        Returns:
            Dividendos em REAIS por ação ou None
        """
        if self.dividendos is None or self.dividendos.empty:
            return None
        
        if periodo not in self.dividendos.columns:
            return None
        
        valor = self.dividendos[periodo].iloc[0]
        
        if pd.isna(valor):
            return None
        
        # Dividendos já estão em REAIS por ação (não precisa conversão)
        return float(valor)
    
    # ==================================================================================
    # PERÍODOS E LTM
    # ==================================================================================
    
    def get_periodos_disponiveis(self) -> List[str]:
        """
        Retorna lista de períodos disponíveis em ordem cronológica.
        
        Returns:
            Lista de períodos (ex: ['2023T1', '2023T2', ..., '2024T4'])
        """
        # Coletar colunas de todos os DataFrames
        colunas_set = set()
        
        for df in [self.bpa, self.bpp, self.dre, self.dfc, self.precos, self.acoes]:
            if df is not None and not df.empty:
                # Filtrar apenas colunas no formato AAAATX
                colunas_periodo = [c for c in df.columns if self._is_periodo_valido(c)]
                colunas_set.update(colunas_periodo)
        
        # Ordenar cronologicamente
        periodos = sorted(list(colunas_set), key=self._periodo_sort_key)
        return periodos
    
    def _is_periodo_valido(self, coluna: str) -> bool:
        """Verifica se coluna é um período válido (formato AAAATX)."""
        import re
        return bool(re.match(r'^\d{4}T[1-4]$', str(coluna)))
    
    def _periodo_sort_key(self, periodo: str) -> tuple:
        """Chave de ordenação para períodos."""
        if not self._is_periodo_valido(periodo):
            return (9999, 9)
        ano = int(periodo[:4])
        trimestre = int(periodo[5])
        return (ano, trimestre)
    
    def get_ultimos_4_trimestres(self, periodo_referencia: Optional[str] = None) -> List[str]:
        """
        Retorna os últimos 4 trimestres disponíveis (para cálculo LTM).
        
        Args:
            periodo_referencia: Período de referência (None = último disponível)
        
        Returns:
            Lista com 4 períodos ou lista vazia se não houver dados suficientes
        """
        periodos = self.get_periodos_disponiveis()
        
        if not periodos:
            return []
        
        # Se não especificou referência, usar o mais recente
        if periodo_referencia is None:
            periodo_referencia = periodos[-1]
        
        # Encontrar índice do período de referência
        try:
            idx = periodos.index(periodo_referencia)
        except ValueError:
            return []
        
        # Pegar 4 trimestres até o período de referência (inclusive)
        if idx < 3:
            return []  # Não tem 4 trimestres completos
        
        return periodos[idx-3:idx+1]
    
    # ==================================================================================
    # CÁLCULOS INTERMEDIÁRIOS
    # ==================================================================================
    
    def calcular_ebitda(self, periodo: str) -> Optional[float]:
        """
        EBITDA = EBIT + Depreciação e Amortização
        
        Onde:
        - EBIT = conta 3.05 (Resultado Antes do Resultado Financeiro e dos Tributos)
        - D&A = conta 6.01.DA (Depreciação e Amortização do DFC)
        """
        ebit = self.get_valor(self.dre, periodo, "3.05")
        deprec = self.get_valor(self.dfc, periodo, "6.01.DA")
        
        if ebit is None:
            return None
        
        if deprec is None:
            # Se não tem D&A, EBITDA = EBIT (empresas financeiras)
            return ebit
        
        return ebit + deprec
    
    def calcular_ebitda_ltm(self, periodo: str) -> Optional[float]:
        """EBITDA dos últimos 12 meses (soma dos últimos 4 trimestres)."""
        trimestres = self.get_ultimos_4_trimestres(periodo)
        if len(trimestres) < 4:
            return None
        
        ebitdas = [self.calcular_ebitda(t) for t in trimestres]
        
        if None in ebitdas:
            return None
        
        return sum(ebitdas)
    
    def calcular_ebit_ltm(self, periodo: str) -> Optional[float]:
        """EBIT dos últimos 12 meses (soma dos últimos 4 trimestres)."""
        trimestres = self.get_ultimos_4_trimestres(periodo)
        if len(trimestres) < 4:
            return None
        
        ebits = [self.get_valor(self.dre, t, "3.05") for t in trimestres]
        
        if None in ebits:
            return None
        
        return sum(ebits)
    
    def calcular_receita_ltm(self, periodo: str) -> Optional[float]:
        """Receita dos últimos 12 meses."""
        trimestres = self.get_ultimos_4_trimestres(periodo)
        if len(trimestres) < 4:
            return None
        
        receitas = [self.get_valor(self.dre, t, "3.01") for t in trimestres]
        
        if None in receitas:
            return None
        
        return sum(receitas)
    
    def calcular_lucro_liquido_ltm(self, periodo: str) -> Optional[float]:
        """Lucro Líquido dos últimos 12 meses."""
        trimestres = self.get_ultimos_4_trimestres(periodo)
        if len(trimestres) < 4:
            return None
        
        lucros = [self.get_valor(self.dre, t, "3.11") for t in trimestres]
        
        if None in lucros:
            return None
        
        return sum(lucros)
    
    def calcular_dividendos_ltm(self, periodo: str) -> Optional[float]:
        """
        Dividendos dos últimos 12 meses (soma dos últimos 4 trimestres).
        
        Returns:
            Dividendos em REAIS por ação ou None
        """
        trimestres = self.get_ultimos_4_trimestres(periodo)
        if len(trimestres) < 4:
            return None
        
        divs = [self.get_dividendos_trimestre(t) for t in trimestres]
        
        # Se não tem dados de dividendos, retorna None (não erro)
        if all(d is None for d in divs):
            return None
        
        # Substituir None por 0 (trimestres sem pagamento)
        divs_clean = [d if d is not None else 0.0 for d in divs]
        
        total = sum(divs_clean)
        return total if total > 0 else None
    
    def calcular_market_cap(self, periodo: str) -> Optional[float]:
        """
        Market Cap = Número de Ações × Preço
        
        Returns:
            Market Cap em REAIS ou None
        """
        preco = self.get_preco(periodo)
        num_acoes = self.get_num_acoes_total(periodo)
        
        if not preco or not num_acoes:
            return None
        
        market_cap = num_acoes * preco
        
        # VALIDAÇÃO v1.2.0: Detectar valores suspeitos
        if market_cap > 500_000_000_000:  # > R$ 500 bilhões
            self.warnings.append(
                f"Market Cap muito alto em {periodo}: R$ {market_cap/1e9:.1f} bi "
                f"(ações={num_acoes:,.0f}, preço=R${preco:.2f})"
            )
        
        return market_cap
    
    def calcular_enterprise_value(self, periodo: str) -> Optional[float]:
        """
        Enterprise Value = Market Cap + Dívida Líquida
        
        Onde:
        - Dívida Líquida = (Dívida CP + Dívida LP) - Caixa
        """
        market_cap = self.calcular_market_cap(periodo)
        
        # Dívida de Curto Prazo (2.01.04)
        divida_cp = self.get_valor(self.bpp, periodo, "2.01.04")
        
        # Dívida de Longo Prazo (2.02.01)
        divida_lp = self.get_valor(self.bpp, periodo, "2.02.01")
        
        # Caixa e Equivalentes (1.01.01)
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
        """
        Capital Investido = PL + Dívida Líquida
        
        Usado no cálculo do ROIC.
        """
        pl = self.get_valor(self.bpp, periodo, "2.03")
        
        # Dívida Líquida
        divida_cp = self.get_valor(self.bpp, periodo, "2.01.04") or 0.0
        divida_lp = self.get_valor(self.bpp, periodo, "2.02.01") or 0.0
        caixa = self.get_valor(self.bpa, periodo, "1.01.01") or 0.0
        
        divida_liquida = (divida_cp + divida_lp) - caixa
        
        if pl is None:
            return None
        
        return pl + divida_liquida
    
    # ==================================================================================
    # MÚLTIPLOS - VALUATION
    # ==================================================================================
    
    def calcular_pl(self, periodo: str) -> Optional[float]:
        """
        P/L = Market Cap / Lucro Líquido LTM
        
        Indica quantos anos levaria para recuperar o investimento.
        """
        market_cap = self.calcular_market_cap(periodo)
        lucro_ltm = self.calcular_lucro_liquido_ltm(periodo)
        
        if not market_cap or not lucro_ltm or lucro_ltm <= 0:
            return None
        
        return market_cap / lucro_ltm
    
    def calcular_pvp(self, periodo: str) -> Optional[float]:
        """
        P/VP = Market Cap / Patrimônio Líquido
        
        Indica quanto o mercado paga por cada real de patrimônio.
        """
        market_cap = self.calcular_market_cap(periodo)
        pl = self.get_valor(self.bpp, periodo, "2.03")
        
        if not market_cap or not pl or pl <= 0:
            return None
        
        return market_cap / pl
    
    def calcular_ev_ebitda(self, periodo: str) -> Optional[float]:
        """
        EV/EBITDA = Enterprise Value / EBITDA LTM
        
        Múltiplo mais usado em M&A.
        """
        ev = self.calcular_enterprise_value(periodo)
        ebitda_ltm = self.calcular_ebitda_ltm(periodo)
        
        if not ev or not ebitda_ltm or ebitda_ltm <= 0:
            return None
        
        return ev / ebitda_ltm
    
    def calcular_ev_ebit(self, periodo: str) -> Optional[float]:
        """EV/EBIT = Enterprise Value / EBIT LTM"""
        ev = self.calcular_enterprise_value(periodo)
        ebit_ltm = self.calcular_ebit_ltm(periodo)
        
        if not ev or not ebit_ltm or ebit_ltm <= 0:
            return None
        
        return ev / ebit_ltm
    
    def calcular_p_ebitda(self, periodo: str) -> Optional[float]:
        """P/EBITDA = Market Cap / EBITDA LTM"""
        market_cap = self.calcular_market_cap(periodo)
        ebitda_ltm = self.calcular_ebitda_ltm(periodo)
        
        if not market_cap or not ebitda_ltm or ebitda_ltm <= 0:
            return None
        
        return market_cap / ebitda_ltm
    
    def calcular_p_ebit(self, periodo: str) -> Optional[float]:
        """P/EBIT = Market Cap / EBIT LTM"""
        market_cap = self.calcular_market_cap(periodo)
        ebit_ltm = self.calcular_ebit_ltm(periodo)
        
        if not market_cap or not ebit_ltm or ebit_ltm <= 0:
            return None
        
        return market_cap / ebit_ltm
    
    def calcular_psr(self, periodo: str) -> Optional[float]:
        """
        PSR = Market Cap / Receita LTM
        
        Price to Sales Ratio.
        """
        market_cap = self.calcular_market_cap(periodo)
        receita_ltm = self.calcular_receita_ltm(periodo)
        
        if not market_cap or not receita_ltm or receita_ltm <= 0:
            return None
        
        return market_cap / receita_ltm
    
    # ==================================================================================
    # MÚLTIPLOS - RENTABILIDADE
    # ==================================================================================
    
    def calcular_roe(self, periodo: str) -> Optional[float]:
        """
        ROE = (Lucro Líquido LTM / PL) × 100
        
        Return on Equity - retorno sobre patrimônio líquido.
        """
        lucro_ltm = self.calcular_lucro_liquido_ltm(periodo)
        pl = self.get_valor(self.bpp, periodo, "2.03")
        
        if not lucro_ltm or not pl or pl <= 0:
            return None
        
        return (lucro_ltm / pl) * 100
    
    def calcular_roic(self, periodo: str) -> Optional[float]:
        """
        ROIC = (NOPAT / Capital Investido) × 100
        
        Onde:
        - NOPAT = EBIT × (1 - Alíquota Efetiva)
        - Alíquota Efetiva = |IR e CSLL| / |Resultado Antes dos Tributos|
        - Capital Investido = PL + Dívida Líquida
        
        CORREÇÃO v1.1.0: Usa alíquota efetiva (não fixa de 34%)
        """
        trimestres = self.get_ultimos_4_trimestres(periodo)
        if len(trimestres) < 4:
            return None
        
        # Calcular EBIT LTM
        ebit_ltm = self.calcular_ebit_ltm(periodo)
        if not ebit_ltm:
            return None
        
        # Calcular Alíquota Efetiva LTM
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
            aliquota_efetiva = 0.34  # Fallback para 34%
        
        # Calcular NOPAT
        nopat = ebit_ltm * (1 - aliquota_efetiva)
        
        # Capital Investido
        capital_investido = self.calcular_capital_investido(periodo)
        if not capital_investido or capital_investido <= 0:
            return None
        
        return (nopat / capital_investido) * 100
    
    def calcular_margem_bruta(self, periodo: str) -> Optional[float]:
        """
        Margem Bruta = (Resultado Bruto / Receita) × 100
        """
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
        """Margem EBIT = (EBIT / Receita) × 100"""
        ebit_ltm = self.calcular_ebit_ltm(periodo)
        receita_ltm = self.calcular_receita_ltm(periodo)
        
        if not ebit_ltm or not receita_ltm or receita_ltm <= 0:
            return None
        
        return (ebit_ltm / receita_ltm) * 100
    
    def calcular_margem_ebitda(self, periodo: str) -> Optional[float]:
        """Margem EBITDA = (EBITDA / Receita) × 100"""
        ebitda_ltm = self.calcular_ebitda_ltm(periodo)
        receita_ltm = self.calcular_receita_ltm(periodo)
        
        if not ebitda_ltm or not receita_ltm or receita_ltm <= 0:
            return None
        
        return (ebitda_ltm / receita_ltm) * 100
    
    def calcular_margem_liquida(self, periodo: str) -> Optional[float]:
        """Margem Líquida = (Lucro Líquido / Receita) × 100"""
        lucro_ltm = self.calcular_lucro_liquido_ltm(periodo)
        receita_ltm = self.calcular_receita_ltm(periodo)
        
        if not lucro_ltm or not receita_ltm or receita_ltm <= 0:
            return None
        
        return (lucro_ltm / receita_ltm) * 100
    
    # ==================================================================================
    # MÚLTIPLOS - DIVIDENDOS
    # ==================================================================================
    
    def calcular_dy(self, periodo: str) -> Optional[float]:
        """
        Dividend Yield = (Dividendos LTM / Preço) × 100
        
        CORREÇÃO v1.2.0: Implementação completa e funcional.
        
        Cálculo:
        - dividendos_ltm: soma dos últimos 4 trimestres (R$/ação)
        - preco: preço por ação (R$)
        - DY = (dividendos_ltm / preco) × 100
        
        Returns:
            Dividend Yield em % ou None se não houver dados
        """
        dividendos_ltm = self.calcular_dividendos_ltm(periodo)
        preco = self.get_preco(periodo)
        
        if not dividendos_ltm or not preco or preco <= 0:
            return None
        
        dy = (dividendos_ltm / preco) * 100
        return round(dy, 2)
    
    def calcular_payout(self, periodo: str) -> Optional[float]:
        """
        Payout = (Dividendos LTM / Lucro Líquido LTM) × 100
        
        Percentual do lucro distribuído como dividendos.
        
        CORREÇÃO v1.2.0: Ajuste para usar dividendos totais.
        """
        dividendos_ltm = self.calcular_dividendos_ltm(periodo)
        lucro_ltm = self.calcular_lucro_liquido_ltm(periodo)
        num_acoes = self.get_num_acoes_total(periodo)
        
        if not dividendos_ltm or not lucro_ltm or not num_acoes:
            return None
        
        if lucro_ltm <= 0:
            return None
        
        # Converter dividendos por ação em dividendos totais
        dividendos_totais = dividendos_ltm * num_acoes
        
        payout = (dividendos_totais / lucro_ltm) * 100
        
        # Limitar payout a 100% (pode ultrapassar se empresa distribui reservas)
        # Mas não limitar - deixar o valor real
        return round(payout, 2)
    
    # ==================================================================================
    # MÚLTIPLOS - ENDIVIDAMENTO
    # ==================================================================================
    
    def calcular_divida_liquida_pl(self, periodo: str) -> Optional[float]:
        """
        Dívida Líquida / PL
        
        Indica alavancagem financeira.
        """
        divida_cp = self.get_valor(self.bpp, periodo, "2.01.04") or 0.0
        divida_lp = self.get_valor(self.bpp, periodo, "2.02.01") or 0.0
        caixa = self.get_valor(self.bpa, periodo, "1.01.01") or 0.0
        pl = self.get_valor(self.bpp, periodo, "2.03")
        
        if not pl or pl <= 0:
            return None
        
        divida_liquida = (divida_cp + divida_lp) - caixa
        
        return divida_liquida / pl
    
    def calcular_divida_liquida_ebitda(self, periodo: str) -> Optional[float]:
        """
        Dívida Líquida / EBITDA LTM
        
        Indica quantos anos de EBITDA seriam necessários para pagar a dívida.
        """
        divida_cp = self.get_valor(self.bpp, periodo, "2.01.04") or 0.0
        divida_lp = self.get_valor(self.bpp, periodo, "2.02.01") or 0.0
        caixa = self.get_valor(self.bpa, periodo, "1.01.01") or 0.0
        ebitda_ltm = self.calcular_ebitda_ltm(periodo)
        
        if not ebitda_ltm or ebitda_ltm <= 0:
            return None
        
        divida_liquida = (divida_cp + divida_lp) - caixa
        
        return divida_liquida / ebitda_ltm
    
    # ==================================================================================
    # MÚLTIPLOS - LIQUIDEZ
    # ==================================================================================
    
    def calcular_liquidez_corrente(self, periodo: str) -> Optional[float]:
        """
        Liquidez Corrente = Ativo Circulante / Passivo Circulante
        
        Indica capacidade de pagar dívidas de curto prazo.
        """
        ativo_circulante = self.get_valor(self.bpa, periodo, "1.01")
        passivo_circulante = self.get_valor(self.bpp, periodo, "2.01")
        
        if not ativo_circulante or not passivo_circulante or passivo_circulante <= 0:
            return None
        
        return ativo_circulante / passivo_circulante
    
    def calcular_vpa(self, periodo: str) -> Optional[float]:
        """
        VPA = Patrimônio Líquido / Número de Ações
        
        Valor Patrimonial por Ação.
        """
        pl = self.get_valor(self.bpp, periodo, "2.03")
        num_acoes = self.get_num_acoes_total(periodo)
        
        if not pl or not num_acoes or num_acoes <= 0:
            return None
        
        return pl / num_acoes
    
    def calcular_lpa(self, periodo: str) -> Optional[float]:
        """
        LPA = Lucro Líquido LTM / Número de Ações
        
        Lucro por Ação.
        """
        lucro_ltm = self.calcular_lucro_liquido_ltm(periodo)
        num_acoes = self.get_num_acoes_total(periodo)
        
        if not lucro_ltm or not num_acoes or num_acoes <= 0:
            return None
        
        return lucro_ltm / num_acoes
    
    # ==================================================================================
    # PROCESSAMENTO COMPLETO
    # ==================================================================================
    
    def calcular_todos_multiplos(self, periodo: str) -> Dict[str, Any]:
        """
        Calcula todos os múltiplos para um período específico.
        
        Args:
            periodo: Período no formato AAAATX (ex: 2024T4)
        
        Returns:
            Dicionário com todos os múltiplos calculados
        """
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
    
    def calcular_multiplos_historico(self, limite_periodos: Optional[int] = None) -> pd.DataFrame:
        """
        Calcula múltiplos para todos os períodos disponíveis.
        
        Args:
            limite_periodos: Número máximo de períodos (None = todos)
        
        Returns:
            DataFrame com múltiplos de todos os períodos
        """
        periodos = self.get_periodos_disponiveis()
        
        if limite_periodos:
            periodos = periodos[-limite_periodos:]
        
        resultados = []
        for periodo in periodos:
            try:
                multiplos = self.calcular_todos_multiplos(periodo)
                resultados.append(multiplos)
            except Exception as e:
                print(f"⚠️ Erro ao calcular {periodo}: {e}")
                continue
        
        if not resultados:
            return pd.DataFrame()
        
        df = pd.DataFrame(resultados)
        
        # Reordenar colunas
        cols_order = ['ticker', 'periodo', 'data_calculo']
        outras_cols = [c for c in df.columns if c not in cols_order]
        df = df[cols_order + outras_cols]
        
        return df
    
    def gerar_relatorio_ltm(self) -> Dict[str, Any]:
        """
        Gera relatório completo com múltiplos LTM (último período disponível).
        
        Returns:
            Dicionário com relatório completo incluindo warnings
        """
        periodos = self.get_periodos_disponiveis()
        if not periodos:
            raise ValueError("Nenhum período disponível para cálculo")
        
        ultimo_periodo = periodos[-1]
        multiplos = self.calcular_todos_multiplos(ultimo_periodo)
        
        # Adicionar warnings ao relatório
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
# CLI - INTERFACE DE LINHA DE COMANDO
# ======================================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Calculadora de Múltiplos Financeiros v1.2.0'
    )
    parser.add_argument(
        'ticker',
        type=str,
        help='Ticker do ativo (ex: PETR4, VALE3)'
    )
    parser.add_argument(
        '--pasta',
        type=str,
        default='balancos',
        help='Pasta raiz dos balanços (padrão: balancos)'
    )
    parser.add_argument(
        '--periodo',
        type=str,
        help='Período específico (ex: 2024T4). Se omitido, usa LTM'
    )
    parser.add_argument(
        '--historico',
        action='store_true',
        help='Calcular múltiplos para todos os períodos'
    )
    parser.add_argument(
        '--limite',
        type=int,
        help='Limitar número de períodos no histórico'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Saída em formato JSON'
    )
    parser.add_argument(
        '--csv',
        type=str,
        help='Salvar resultado em arquivo CSV'
    )
    
    args = parser.parse_args()
    
    try:
        # Inicializar calculadora
        calc = CalculadoraMultiplos(
            ticker=args.ticker,
            pasta_balancos=Path(args.pasta)
        )
        
        # Modo histórico
        if args.historico:
            df = calc.calcular_multiplos_historico(limite_periodos=args.limite)
            
            if args.csv:
                df.to_csv(args.csv, index=False, encoding='utf-8-sig')
                print(f"✅ Arquivo salvo: {args.csv}")
            
            if args.json:
                print(df.to_json(orient='records', indent=2))
            else:
                print(df.to_string(index=False))
        
        # Modo período único
        else:
            if args.periodo:
                multiplos = calc.calcular_todos_multiplos(args.periodo)
            else:
                relatorio = calc.gerar_relatorio_ltm()
                multiplos = relatorio['multiplos']
                
                # Mostrar warnings se houver
                if relatorio['warnings']:
                    print("\n⚠️ AVISOS:")
                    for w in relatorio['warnings']:
                        print(f"  • {w}")
                    print()
            
            if args.json:
                print(json.dumps(multiplos, indent=2, ensure_ascii=False))
            else:
                print(f"\n{'='*70}")
                print(f"MÚLTIPLOS FINANCEIROS - {args.ticker}")
                print(f"{'='*70}")
                print(f"Período: {multiplos['periodo']}")
                print(f"{'='*70}\n")
                
                categorias = {
                    'VALUATION': ['P/L', 'P/VP', 'EV/EBITDA', 'EV/EBIT', 'P/EBITDA', 'P/EBIT', 'PSR'],
                    'RENTABILIDADE': ['ROE', 'ROIC', 'Margem_Bruta', 'Margem_EBIT', 'Margem_EBITDA', 'Margem_Liquida'],
                    'DIVIDENDOS': ['Dividend_Yield', 'Payout'],
                    'ENDIVIDAMENTO': ['Divida_Liquida_PL', 'Divida_Liquida_EBITDA'],
                    'LIQUIDEZ': ['Liquidez_Corrente', 'VPA', 'LPA'],
                }
                
                for categoria, metricas in categorias.items():
                    print(f"{categoria}:")
                    for metrica in metricas:
                        valor = multiplos.get(metrica)
                        if valor is not None:
                            if metrica in ['VPA', 'LPA', 'Preco']:
                                print(f"  {metrica:25s}: R$ {valor:,.2f}")
                            elif metrica.startswith('Margem') or metrica in ['ROE', 'ROIC', 'Dividend_Yield', 'Payout']:
                                print(f"  {metrica:25s}: {valor:.2f}%")
                            else:
                                print(f"  {metrica:25s}: {valor:.2f}")
                        else:
                            print(f"  {metrica:25s}: N/A")
                    print()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
