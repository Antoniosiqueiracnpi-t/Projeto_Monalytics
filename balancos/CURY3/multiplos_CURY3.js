// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["CURY3"] = {
  "ticker": "CURY3",
  "ticker_preco": "CURY3",
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
        "VALOR_MERCADO": 9243684.04,
        "P_L": 45.2997,
        "P_VPA": 25.409,
        "EV_EBITDA": 37.6709,
        "EV_EBIT": 38.804,
        "EV_RECEITA": 9.042,
        "DY": 13.4883,
        "PAYOUT": 611.0177,
        "ROE": 56.0908,
        "ROA": 15.8429,
        "ROIC": 46.5954,
        "MARGEM_EBITDA": 24.0026,
        "MARGEM_LIQUIDA": 20.0197,
        "DIV_LIQ_EBITDA": -0.1119,
        "DIV_LIQ_PL": -0.0753,
        "ICJ": 8.8991,
        "COMPOSICAO_DIVIDA": 43.1041,
        "LIQ_CORRENTE": 1.6711,
        "LIQ_SECA": 1.3897,
        "LIQ_GERAL": 1.3627,
        "GIRO_ATIVO": 0.7914,
        "PME": 98.4205,
        "CICLO_CAIXA": 265.9116,
        "NCG_RECEITA": 23.725
      }
    },
    "2020": {
      "periodo_referencia": "2020T4",
      "multiplos": {
        "VALOR_MERCADO": 1961400.59,
        "P_L": 10.3233,
        "P_VPA": 3.0533,
        "EV_EBITDA": 7.5272,
        "EV_EBIT": 8.0312,
        "EV_RECEITA": 1.5788,
        "DY": 63.5678,
        "PAYOUT": 656.2271,
        "ROE": 37.7661,
        "ROA": 12.9572,
        "ROIC": 30.4213,
        "MARGEM_EBITDA": 20.9745,
        "MARGEM_LIQUIDA": 16.5983,
        "DIV_LIQ_EBITDA": -0.6422,
        "DIV_LIQ_PL": -0.24,
        "ICJ": 9.5823,
        "COMPOSICAO_DIVIDA": 33.1417,
        "LIQ_CORRENTE": 2.2466,
        "LIQ_SECA": 1.7976,
        "LIQ_GERAL": 1.5994,
        "GIRO_ATIVO": 0.696,
        "PME": 135.8381,
        "CICLO_CAIXA": 311.036,
        "NCG_RECEITA": 35.9298
      }
    },
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": 1409756.68,
        "P_L": 4.471,
        "P_VPA": 1.9094,
        "EV_EBITDA": 2.9247,
        "EV_EBIT": 3.2056,
        "EV_RECEITA": 0.6941,
        "DY": 88.4421,
        "PAYOUT": 395.4274,
        "ROE": 45.6733,
        "ROA": 14.8638,
        "ROIC": 46.4245,
        "MARGEM_EBITDA": 23.7317,
        "MARGEM_LIQUIDA": 18.139,
        "DIV_LIQ_EBITDA": -0.4927,
        "DIV_LIQ_PL": -0.2753,
        "ICJ": 7.5707,
        "COMPOSICAO_DIVIDA": 17.3863,
        "LIQ_CORRENTE": 1.6559,
        "LIQ_SECA": 1.2196,
        "LIQ_GERAL": 1.3334,
        "GIRO_ATIVO": 0.6691,
        "PME": 160.2011,
        "CICLO_CAIXA": 282.8637,
        "NCG_RECEITA": 11.7991
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 2740707.08,
        "P_L": 7.8656,
        "P_VPA": 3.1224,
        "EV_EBITDA": 5.146,
        "EV_EBIT": 5.6638,
        "EV_RECEITA": 1.0775,
        "DY": 45.4926,
        "PAYOUT": 357.8287,
        "ROE": 43.1217,
        "ROA": 12.9139,
        "ROIC": 49.785,
        "MARGEM_EBITDA": 20.9387,
        "MARGEM_LIQUIDA": 15.4362,
        "DIV_LIQ_EBITDA": -0.6526,
        "DIV_LIQ_PL": -0.3514,
        "ICJ": 4.8542,
        "COMPOSICAO_DIVIDA": 25.137,
        "LIQ_CORRENTE": 1.9331,
        "LIQ_SECA": 1.4319,
        "LIQ_GERAL": 1.3916,
        "GIRO_ATIVO": 0.8066,
        "PME": 135.5936,
        "CICLO_CAIXA": 215.244,
        "NCG_RECEITA": 14.5092
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 4191326.26,
        "P_L": 8.4569,
        "P_VPA": 4.204,
        "EV_EBITDA": 6.0371,
        "EV_EBIT": 6.5512,
        "EV_RECEITA": 1.3209,
        "DY": 29.7476,
        "PAYOUT": 251.572,
        "ROE": 52.8728,
        "ROA": 16.8276,
        "ROIC": 62.1426,
        "MARGEM_EBITDA": 21.8801,
        "MARGEM_LIQUIDA": 17.1719,
        "DIV_LIQ_EBITDA": -0.6,
        "DIV_LIQ_PL": -0.3801,
        "ICJ": 5.812,
        "COMPOSICAO_DIVIDA": 20.261,
        "LIQ_CORRENTE": 2.0336,
        "LIQ_SECA": 1.444,
        "LIQ_GERAL": 1.4075,
        "GIRO_ATIVO": 0.9334,
        "PME": 128.967,
        "CICLO_CAIXA": 154.4336,
        "NCG_RECEITA": 8.8932
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 4413151.33,
        "P_L": 6.3152,
        "P_VPA": 3.37,
        "EV_EBITDA": 4.6818,
        "EV_EBIT": 4.8596,
        "EV_RECEITA": 1.0145,
        "DY": 28.2523,
        "PAYOUT": 178.4197,
        "ROE": 60.5945,
        "ROA": 18.8072,
        "ROIC": 61.498,
        "MARGEM_EBITDA": 21.6694,
        "MARGEM_LIQUIDA": 17.7982,
        "DIV_LIQ_EBITDA": -0.5052,
        "DIV_LIQ_PL": -0.3282,
        "ICJ": 5.9759,
        "COMPOSICAO_DIVIDA": 21.1753,
        "LIQ_CORRENTE": 2.181,
        "LIQ_SECA": 1.5344,
        "LIQ_GERAL": 1.4046,
        "GIRO_ATIVO": 0.9048,
        "PME": 120.5588,
        "CICLO_CAIXA": 124.3215,
        "NCG_RECEITA": 6.8463
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 9153202.76,
        "P_L": 9.4081,
        "P_VPA": 5.574,
        "EV_EBITDA": 7.1929,
        "EV_EBIT": 7.5711,
        "EV_RECEITA": 1.7355,
        "DY": 13.6217,
        "PAYOUT": 128.1544,
        "ROE": 67.6696,
        "ROA": 20.2915,
        "ROIC": 63.6517,
        "MARGEM_EBITDA": 24.128,
        "MARGEM_LIQUIDA": 19.4011,
        "DIV_LIQ_EBITDA": -0.3721,
        "DIV_LIQ_PL": -0.2742,
        "ICJ": 5.7525,
        "COMPOSICAO_DIVIDA": 11.3907,
        "LIQ_CORRENTE": 1.9968,
        "LIQ_SECA": 1.4337,
        "LIQ_GERAL": 1.3911,
        "GIRO_ATIVO": 0.8904,
        "PME": 113.9164,
        "CICLO_CAIXA": 114.4339,
        "NCG_RECEITA": 1.5599
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-17T10:32:12.716647",
    "preco_utilizado": 31.67,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 291875088,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 9243684.04,
      "P_L": 9.5011,
      "P_VPA": 5.6291,
      "EV_EBITDA": 7.2677,
      "EV_EBIT": 7.6498,
      "EV_RECEITA": 1.7535,
      "DY": 13.4883,
      "PAYOUT": 128.1544,
      "ROE": 67.6696,
      "ROA": 20.2915,
      "ROIC": 63.6517,
      "MARGEM_EBITDA": 24.128,
      "MARGEM_LIQUIDA": 19.4011,
      "DIV_LIQ_EBITDA": -0.3721,
      "DIV_LIQ_PL": -0.2742,
      "ICJ": 5.7525,
      "COMPOSICAO_DIVIDA": 11.3907,
      "LIQ_CORRENTE": 1.9968,
      "LIQ_SECA": 1.4337,
      "LIQ_GERAL": 1.3911,
      "GIRO_ATIVO": 0.8904,
      "PME": 113.9164,
      "CICLO_CAIXA": 114.4339,
      "NCG_RECEITA": 1.5599
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
    "2021T3",
    "2021T4",
    "2022T1",
    "2022T2",
    "2022T3",
    "2022T4",
    "2023T1",
    "2023T2",
    "2023T3",
    "2023T4",
    "2024T1",
    "2024T2",
    "2024T3",
    "2024T4",
    "2025T1",
    "2025T2",
    "2025T3"
  ],
  "erros": []
};
})();
