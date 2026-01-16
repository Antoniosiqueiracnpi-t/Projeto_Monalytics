// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["ASAI3"] = {
  "ticker": "ASAI3",
  "ticker_preco": "ASAI3",
  "padrao_fiscal": {
    "tipo": "PADRAO",
    "descricao": "Ano fiscal padrão (jan-dez) com T1-T4",
    "trimestres_ltm": 4
  },
  "metadata": {
    "VALOR_MERCADO": {
      "nome": "Valor de Mercado",
      "categoria": "Valuation",
      "formula": "Preço × Ações (3+4)",
      "unidade": "R$ mil",
      "usa_preco": true
    },
    "P_L": {
      "nome": "P/L",
      "categoria": "Valuation",
      "formula": "Preço / Lucro por Ação LTM",
      "unidade": "x",
      "usa_preco": true
    },
    "P_VPA": {
      "nome": "P/VPA",
      "categoria": "Valuation",
      "formula": "Preço / Valor Patrimonial por Ação",
      "unidade": "x",
      "usa_preco": true
    },
    "EV_EBITDA": {
      "nome": "EV/EBITDA",
      "categoria": "Valuation",
      "formula": "Enterprise Value / EBITDA LTM",
      "unidade": "x",
      "usa_preco": true
    },
    "EV_EBIT": {
      "nome": "EV/EBIT",
      "categoria": "Valuation",
      "formula": "Enterprise Value / EBIT LTM",
      "unidade": "x",
      "usa_preco": true
    },
    "EV_RECEITA": {
      "nome": "EV/Receita",
      "categoria": "Valuation",
      "formula": "Enterprise Value / Receita LTM",
      "unidade": "x",
      "usa_preco": true
    },
    "DY": {
      "nome": "Dividend Yield",
      "categoria": "Valuation",
      "formula": "Dividendos LTM / Market Cap",
      "unidade": "%",
      "usa_preco": true
    },
    "PAYOUT": {
      "nome": "Payout",
      "categoria": "Valuation",
      "formula": "Dividendos LTM / Lucro Líquido LTM",
      "unidade": "%",
      "usa_preco": false
    },
    "ROE": {
      "nome": "ROE",
      "categoria": "Rentabilidade",
      "formula": "Lucro Líquido LTM / PL Médio",
      "unidade": "%",
      "usa_preco": false
    },
    "ROA": {
      "nome": "ROA",
      "categoria": "Rentabilidade",
      "formula": "Lucro Líquido LTM / Ativo Total Médio",
      "unidade": "%",
      "usa_preco": false
    },
    "ROIC": {
      "nome": "ROIC",
      "categoria": "Rentabilidade",
      "formula": "NOPAT / Capital Investido",
      "unidade": "%",
      "usa_preco": false
    },
    "MARGEM_EBITDA": {
      "nome": "Margem EBITDA",
      "categoria": "Rentabilidade",
      "formula": "EBITDA / Receita",
      "unidade": "%",
      "usa_preco": false
    },
    "MARGEM_LIQUIDA": {
      "nome": "Margem Líquida",
      "categoria": "Rentabilidade",
      "formula": "Lucro Líquido / Receita",
      "unidade": "%",
      "usa_preco": false
    },
    "DIV_LIQ_EBITDA": {
      "nome": "Dív.Líq/EBITDA",
      "categoria": "Endividamento",
      "formula": "(Emp CP + LP - Caixa) / EBITDA",
      "unidade": "x",
      "usa_preco": false
    },
    "DIV_LIQ_PL": {
      "nome": "Dív.Líq/PL",
      "categoria": "Endividamento",
      "formula": "Dívida Líquida / Patrimônio Líquido",
      "unidade": "x",
      "usa_preco": false
    },
    "ICJ": {
      "nome": "ICJ",
      "categoria": "Endividamento",
      "formula": "EBIT / Despesas Financeiras",
      "unidade": "x",
      "usa_preco": false
    },
    "COMPOSICAO_DIVIDA": {
      "nome": "Composição Dívida",
      "categoria": "Endividamento",
      "formula": "Emp CP / (Emp CP + LP)",
      "unidade": "%",
      "usa_preco": false
    },
    "LIQ_CORRENTE": {
      "nome": "Liquidez Corrente",
      "categoria": "Liquidez",
      "formula": "Ativo Circulante / Passivo Circulante",
      "unidade": "x",
      "usa_preco": false
    },
    "LIQ_SECA": {
      "nome": "Liquidez Seca",
      "categoria": "Liquidez",
      "formula": "(AC - Estoques) / PC",
      "unidade": "x",
      "usa_preco": false
    },
    "LIQ_GERAL": {
      "nome": "Liquidez Geral",
      "categoria": "Liquidez",
      "formula": "(AC + RLP) / (PC + PNC)",
      "unidade": "x",
      "usa_preco": false
    },
    "GIRO_ATIVO": {
      "nome": "Giro do Ativo",
      "categoria": "Eficiência",
      "formula": "Receita LTM / Ativo Total",
      "unidade": "x",
      "usa_preco": false
    },
    "CICLO_CAIXA": {
      "nome": "Ciclo de Caixa",
      "categoria": "Eficiência",
      "formula": "PMR + PME - PMP",
      "unidade": "dias",
      "usa_preco": false
    },
    "PME": {
      "nome": "PME",
      "categoria": "Eficiência",
      "formula": "(Estoques + AtBio) × 360 / CPV",
      "unidade": "dias",
      "usa_preco": false
    },
    "NCG_RECEITA": {
      "nome": "NCG/Receita",
      "categoria": "Eficiência",
      "formula": "NCG / Receita LTM",
      "unidade": "%",
      "usa_preco": false
    }
  },
  "historico_anual": {
    "2019": {
      "periodo_referencia": "2019T4",
      "multiplos": {
        "VALOR_MERCADO": 2007269.72,
        "P_L": 1.8937,
        "P_VPA": 0.2069,
        "EV_EBITDA": 2.3741,
        "EV_EBIT": 3.3578,
        "EV_RECEITA": 0.1919,
        "DY": 0.1945,
        "PAYOUT": 0.3682,
        "ROE": 10.9267,
        "ROA": 2.9522,
        "ROIC": 8.4505,
        "MARGEM_EBITDA": 8.0841,
        "MARGEM_LIQUIDA": 3.5062,
        "DIV_LIQ_EBITDA": 1.5528,
        "DIV_LIQ_PL": 0.3912,
        "ICJ": null,
        "COMPOSICAO_DIVIDA": 16.6875,
        "LIQ_CORRENTE": 0.8817,
        "LIQ_SECA": 0.5091,
        "LIQ_GERAL": 0.5188,
        "GIRO_ATIVO": 0.842,
        "PME": 75.0633,
        "CICLO_CAIXA": -57.941,
        "NCG_RECEITA": -17.2069
      }
    },
    "2020": {
      "periodo_referencia": "2020T4",
      "multiplos": {
        "VALOR_MERCADO": 2007269.72,
        "P_L": 1.29,
        "P_VPA": 1.4902,
        "EV_EBITDA": 1.365,
        "EV_EBIT": 3.0495,
        "EV_RECEITA": 0.175,
        "DY": 0.1945,
        "PAYOUT": 0.2509,
        "ROE": 28.168,
        "ROA": 5.6865,
        "ROIC": 24.1743,
        "MARGEM_EBITDA": 12.818,
        "MARGEM_LIQUIDA": 4.3171,
        "DIV_LIQ_EBITDA": 0.9305,
        "DIV_LIQ_PL": 3.1915,
        "ICJ": null,
        "COMPOSICAO_DIVIDA": 27.0719,
        "LIQ_CORRENTE": 0.9503,
        "LIQ_SECA": 0.5247,
        "LIQ_GERAL": 0.5459,
        "GIRO_ATIVO": 1.915,
        "PME": 44.6759,
        "CICLO_CAIXA": -13.6028,
        "NCG_RECEITA": -5.13
      }
    },
    "2021": {
      "periodo_referencia": "2021T3",
      "multiplos": {
        "VALOR_MERCADO": 4870580.94,
        "P_L": 2.257,
        "P_VPA": 2.0277,
        "EV_EBITDA": 2.1298,
        "EV_EBIT": 3.1757,
        "EV_RECEITA": 0.1959,
        "DY": 0.0801,
        "PAYOUT": 0.1809,
        "ROE": 28.5828,
        "ROA": 7.1055,
        "ROIC": 27.4599,
        "MARGEM_EBITDA": 9.2004,
        "MARGEM_LIQUIDA": 4.165,
        "DIV_LIQ_EBITDA": 1.108,
        "DIV_LIQ_PL": 2.199,
        "ICJ": 7.4005,
        "COMPOSICAO_DIVIDA": 29.1437,
        "LIQ_CORRENTE": 0.9688,
        "LIQ_SECA": 0.4823,
        "LIQ_GERAL": 0.5446,
        "GIRO_ATIVO": 2.4947,
        "PME": 36.8392,
        "CICLO_CAIXA": -4.5057,
        "NCG_RECEITA": -1.5209
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2021T3",
    "data_calculo": "2026-01-16T21:22:27.326361",
    "preco_utilizado": 7.48,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 1352245185,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 10114793.98,
      "P_L": 0.9302,
      "P_VPA": 0.8357,
      "EV_EBITDA": 3.2299,
      "EV_EBIT": 4.816,
      "EV_RECEITA": 0.2972,
      "DY": 0.1945,
      "PAYOUT": 0.1809,
      "ROE": 28.5828,
      "ROA": 7.1055,
      "ROIC": 27.4599,
      "MARGEM_EBITDA": 9.2004,
      "MARGEM_LIQUIDA": 4.165,
      "DIV_LIQ_EBITDA": 1.108,
      "DIV_LIQ_PL": 2.199,
      "ICJ": 7.4005,
      "COMPOSICAO_DIVIDA": 29.1437,
      "LIQ_CORRENTE": 0.9688,
      "LIQ_SECA": 0.4823,
      "LIQ_GERAL": 0.5446,
      "GIRO_ATIVO": 2.4947,
      "PME": 36.8392,
      "CICLO_CAIXA": -4.5057,
      "NCG_RECEITA": -1.5209
    }
  },
  "periodos_disponiveis": [
    "2019T1",
    "2019T2",
    "2019T3",
    "2019T4",
    "2020T1",
    "2020T2",
    "2020T3",
    "2020T4",
    "2021T1",
    "2021T2",
    "2021T3"
  ],
  "erros": []
};
})();
