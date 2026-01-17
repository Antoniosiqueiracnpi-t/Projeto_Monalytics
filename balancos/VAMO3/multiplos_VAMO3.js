// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["VAMO3"] = {
  "ticker": "VAMO3",
  "ticker_preco": "VAMO3",
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
    "2018": {
      "periodo_referencia": "2018T4",
      "multiplos": {
        "VALOR_MERCADO": 348544.19,
        "P_L": 3086.1825,
        "P_VPA": 0.5994,
        "EV_EBITDA": 13.7628,
        "EV_EBIT": 5347.2137,
        "EV_RECEITA": 1245.1581,
        "DY": 3.9084,
        "PAYOUT": 12062.0013,
        "ROE": 0.0194,
        "ROA": 0.0056,
        "ROIC": 0.0103,
        "MARGEM_EBITDA": 9047.2902,
        "MARGEM_LIQUIDA": 12.0281,
        "DIV_LIQ_EBITDA": 9.6598,
        "DIV_LIQ_PL": 1.4112,
        "ICJ": 2.6454,
        "COMPOSICAO_DIVIDA": 21.2331,
        "LIQ_CORRENTE": 0.8588,
        "LIQ_SECA": 0.6644,
        "LIQ_GERAL": 0.3529,
        "GIRO_ATIVO": 0.0005,
        "PME": 58744.577,
        "CICLO_CAIXA": 39637.0961,
        "NCG_RECEITA": 5150.9884
      }
    },
    "2019": {
      "periodo_referencia": "2019T4",
      "multiplos": {
        "VALOR_MERCADO": 348544.19,
        "P_L": 2.4583,
        "P_VPA": 0.7102,
        "EV_EBITDA": 3.6392,
        "EV_EBIT": 6.5611,
        "EV_RECEITA": 1.5849,
        "DY": 3.9084,
        "PAYOUT": 9.608,
        "ROE": 26.446,
        "ROA": 5.585,
        "ROIC": 9.3656,
        "MARGEM_EBITDA": 43.551,
        "MARGEM_LIQUIDA": 11.7029,
        "DIV_LIQ_EBITDA": 2.9786,
        "DIV_LIQ_PL": 3.2024,
        "ICJ": 2.6567,
        "COMPOSICAO_DIVIDA": 20.0376,
        "LIQ_CORRENTE": 1.4869,
        "LIQ_SECA": 1.281,
        "LIQ_GERAL": 0.4198,
        "GIRO_ATIVO": 0.3967,
        "PME": 63.2483,
        "CICLO_CAIXA": 49.4347,
        "NCG_RECEITA": 20.4236
      }
    },
    "2020": {
      "periodo_referencia": "2020T4",
      "multiplos": {
        "VALOR_MERCADO": 820263.56,
        "P_L": 4.5776,
        "P_VPA": 1.6203,
        "EV_EBITDA": 4.5487,
        "EV_EBIT": 7.8624,
        "EV_RECEITA": 1.9202,
        "DY": 3.9084,
        "PAYOUT": 17.8909,
        "ROE": 35.9465,
        "ROA": 4.9233,
        "ROIC": 9.4115,
        "MARGEM_EBITDA": 42.2138,
        "MARGEM_LIQUIDA": 11.842,
        "DIV_LIQ_EBITDA": 3.2646,
        "DIV_LIQ_PL": 4.1193,
        "ICJ": 2.773,
        "COMPOSICAO_DIVIDA": 11.2931,
        "LIQ_CORRENTE": 1.2917,
        "LIQ_SECA": 1.2028,
        "LIQ_GERAL": 0.3917,
        "GIRO_ATIVO": 0.3581,
        "PME": 32.1725,
        "CICLO_CAIXA": -101.5711,
        "NCG_RECEITA": -10.8404
      }
    },
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": 9975047.17,
        "P_L": 24.7904,
        "P_VPA": 3.7782,
        "EV_EBITDA": 8.9242,
        "EV_EBIT": 16.2389,
        "EV_RECEITA": 4.3344,
        "DY": 1.3781,
        "PAYOUT": 34.1632,
        "ROE": 25.5767,
        "ROA": 5.5843,
        "ROIC": 10.144,
        "MARGEM_EBITDA": 48.5691,
        "MARGEM_LIQUIDA": 14.251,
        "DIV_LIQ_EBITDA": 1.6503,
        "DIV_LIQ_PL": 0.8572,
        "ICJ": 2.661,
        "COMPOSICAO_DIVIDA": 3.5621,
        "LIQ_CORRENTE": 4.092,
        "LIQ_SECA": 3.8125,
        "LIQ_GERAL": 0.6616,
        "GIRO_ATIVO": 0.2772,
        "PME": 66.866,
        "CICLO_CAIXA": -20.5911,
        "NCG_RECEITA": 2.4993
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 11330647.57,
        "P_L": 16.9461,
        "P_VPA": 3.1138,
        "EV_EBITDA": 8.841,
        "EV_EBIT": 10.6076,
        "EV_RECEITA": 3.4784,
        "DY": 1.2733,
        "PAYOUT": 21.5778,
        "ROE": 21.2971,
        "ROA": 4.9784,
        "ROIC": 11.3137,
        "MARGEM_EBITDA": 39.3438,
        "MARGEM_LIQUIDA": 13.6081,
        "DIV_LIQ_EBITDA": 2.9797,
        "DIV_LIQ_PL": 1.5829,
        "ICJ": 1.3827,
        "COMPOSICAO_DIVIDA": 7.4825,
        "LIQ_CORRENTE": 0.9686,
        "LIQ_SECA": 0.7921,
        "LIQ_GERAL": 0.3394,
        "GIRO_ATIVO": 0.2947,
        "PME": 97.4422,
        "CICLO_CAIXA": -189.589,
        "NCG_RECEITA": -26.4331
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 10148742.79,
        "P_L": 17.2904,
        "P_VPA": 2.1432,
        "EV_EBITDA": 7.3354,
        "EV_EBIT": 9.3917,
        "EV_RECEITA": 3.2161,
        "DY": 1.531,
        "PAYOUT": 26.4722,
        "ROE": 14.0183,
        "ROA": 3.1318,
        "ROIC": 9.7145,
        "MARGEM_EBITDA": 43.8442,
        "MARGEM_LIQUIDA": 9.6452,
        "DIV_LIQ_EBITDA": 3.5317,
        "DIV_LIQ_PL": 1.9899,
        "ICJ": 1.1761,
        "COMPOSICAO_DIVIDA": 7.5243,
        "LIQ_CORRENTE": 1.7459,
        "LIQ_SECA": 1.2622,
        "LIQ_GERAL": 0.4306,
        "GIRO_ATIVO": 0.2924,
        "PME": 178.5052,
        "CICLO_CAIXA": 105.2549,
        "NCG_RECEITA": 18.618
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 4918698.04,
        "P_L": 12.9108,
        "P_VPA": 2.0139,
        "EV_EBITDA": 4.0642,
        "EV_EBIT": 6.4859,
        "EV_RECEITA": 3.5375,
        "DY": 3.0924,
        "PAYOUT": 39.9249,
        "ROE": 10.6155,
        "ROA": 1.8545,
        "ROIC": 11.9571,
        "MARGEM_EBITDA": 87.0396,
        "MARGEM_LIQUIDA": 8.107,
        "DIV_LIQ_EBITDA": 2.8617,
        "DIV_LIQ_PL": 4.7924,
        "ICJ": 1.3285,
        "COMPOSICAO_DIVIDA": 6.6052,
        "LIQ_CORRENTE": 1.5186,
        "LIQ_SECA": 1.4805,
        "LIQ_GERAL": 0.2483,
        "GIRO_ATIVO": 0.2318,
        "PME": 22.0797,
        "CICLO_CAIXA": -74.7361,
        "NCG_RECEITA": -8.8447
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 3567407.37,
        "P_L": 7.8068,
        "P_VPA": 1.3561,
        "EV_EBITDA": 2.7018,
        "EV_EBIT": 4.0497,
        "EV_RECEITA": 2.2121,
        "DY": 4.2637,
        "PAYOUT": 33.2859,
        "ROE": 11.6721,
        "ROA": 1.9074,
        "ROIC": 17.3473,
        "MARGEM_EBITDA": 81.8726,
        "MARGEM_LIQUIDA": 6.5311,
        "DIV_LIQ_EBITDA": 2.0791,
        "DIV_LIQ_PL": 4.5273,
        "ICJ": 1.1347,
        "COMPOSICAO_DIVIDA": 10.3876,
        "LIQ_CORRENTE": 1.9342,
        "LIQ_SECA": 1.8991,
        "LIQ_GERAL": 0.337,
        "GIRO_ATIVO": 0.3039,
        "PME": 16.5465,
        "CICLO_CAIXA": -39.193,
        "NCG_RECEITA": 4.5726
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-17T20:37:25.748155",
    "preco_utilizado": 3.6,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 1081032537,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 3891717.13,
      "P_L": 8.5165,
      "P_VPA": 1.4794,
      "EV_EBITDA": 2.7584,
      "EV_EBIT": 4.1346,
      "EV_RECEITA": 2.2584,
      "DY": 3.9084,
      "PAYOUT": 33.2859,
      "ROE": 11.6721,
      "ROA": 1.9074,
      "ROIC": 17.3473,
      "MARGEM_EBITDA": 81.8726,
      "MARGEM_LIQUIDA": 6.5311,
      "DIV_LIQ_EBITDA": 2.0791,
      "DIV_LIQ_PL": 4.5273,
      "ICJ": 1.1347,
      "COMPOSICAO_DIVIDA": 10.3876,
      "LIQ_CORRENTE": 1.9342,
      "LIQ_SECA": 1.8991,
      "LIQ_GERAL": 0.337,
      "GIRO_ATIVO": 0.3039,
      "PME": 16.5465,
      "CICLO_CAIXA": -39.193,
      "NCG_RECEITA": 4.5726
    }
  },
  "periodos_disponiveis": [
    "2018T1",
    "2018T2",
    "2018T3",
    "2018T4",
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
