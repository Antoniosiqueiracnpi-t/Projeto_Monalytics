// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["GMAT3"] = {
  "ticker": "GMAT3",
  "ticker_preco": "GMAT3",
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
        "VALOR_MERCADO": 10074618.12,
        "P_L": 29.8335,
        "P_VPA": 5.1684,
        "EV_EBITDA": 23.7673,
        "EV_EBIT": 23.7673,
        "EV_RECEITA": 1.3648,
        "DY": 5.4676,
        "PAYOUT": 163.1185,
        "ROE": 17.324,
        "ROA": 8.1938,
        "ROIC": 10.7176,
        "MARGEM_EBITDA": 5.7423,
        "MARGEM_LIQUIDA": 4.2025,
        "DIV_LIQ_EBITDA": 1.9336,
        "DIV_LIQ_PL": 0.4577,
        "ICJ": 2.5193,
        "COMPOSICAO_DIVIDA": 19.7335,
        "LIQ_CORRENTE": 2.7523,
        "LIQ_SECA": 1.27,
        "LIQ_GERAL": 1.3392,
        "GIRO_ATIVO": 1.9497,
        "PME": 90.5518,
        "CICLO_CAIXA": 93.9231,
        "NCG_RECEITA": 20.2413
      }
    },
    "2020": {
      "periodo_referencia": "2020T4",
      "multiplos": {
        "VALOR_MERCADO": 17343366.72,
        "P_L": 23.8801,
        "P_VPA": 3.0387,
        "EV_EBITDA": 18.7962,
        "EV_EBIT": 18.7962,
        "EV_RECEITA": 1.3186,
        "DY": 3.1761,
        "PAYOUT": 75.8456,
        "ROE": 18.9705,
        "ROA": 11.79,
        "ROIC": 12.1842,
        "MARGEM_EBITDA": 7.0153,
        "MARGEM_LIQUIDA": 5.8584,
        "DIV_LIQ_EBITDA": -1.1459,
        "DIV_LIQ_PL": -0.1746,
        "ICJ": 3.804,
        "COMPOSICAO_DIVIDA": 5.4821,
        "LIQ_CORRENTE": 4.4559,
        "LIQ_SECA": 2.5332,
        "LIQ_GERAL": 2.5128,
        "GIRO_ATIVO": 1.5121,
        "PME": 100.1647,
        "CICLO_CAIXA": 101.9272,
        "NCG_RECEITA": 21.4041
      }
    },
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": 12504898.81,
        "P_L": 16.2657,
        "P_VPA": 1.9308,
        "EV_EBITDA": 11.5328,
        "EV_EBIT": 14.8681,
        "EV_RECEITA": 0.858,
        "DY": 4.405,
        "PAYOUT": 71.6506,
        "ROE": 12.6196,
        "ROA": 8.4698,
        "ROIC": 7.9631,
        "MARGEM_EBITDA": 7.4393,
        "MARGEM_LIQUIDA": 4.8422,
        "DIV_LIQ_EBITDA": 0.9455,
        "DIV_LIQ_PL": 0.1724,
        "ICJ": 3.3947,
        "COMPOSICAO_DIVIDA": 11.7334,
        "LIQ_CORRENTE": 3.8005,
        "LIQ_SECA": 1.6806,
        "LIQ_GERAL": 1.858,
        "GIRO_ATIVO": 1.5949,
        "PME": 103.4552,
        "CICLO_CAIXA": 113.3947,
        "NCG_RECEITA": 25.0587
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 13123515.71,
        "P_L": 12.3249,
        "P_VPA": 1.7401,
        "EV_EBITDA": 7.3486,
        "EV_EBIT": 10.6178,
        "EV_RECEITA": 0.6659,
        "DY": 4.1974,
        "PAYOUT": 51.7323,
        "ROE": 15.1912,
        "ROA": 9.1718,
        "ROIC": 10.1079,
        "MARGEM_EBITDA": 9.0619,
        "MARGEM_LIQUIDA": 4.8915,
        "DIV_LIQ_EBITDA": 0.6959,
        "DIV_LIQ_PL": 0.182,
        "ICJ": 2.9639,
        "COMPOSICAO_DIVIDA": 8.6197,
        "LIQ_CORRENTE": 3.1962,
        "LIQ_SECA": 1.7487,
        "LIQ_GERAL": 1.5796,
        "GIRO_ATIVO": 1.6412,
        "PME": 84.5482,
        "CICLO_CAIXA": 84.0793,
        "NCG_RECEITA": 20.7841
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 14890992.57,
        "P_L": 12.061,
        "P_VPA": 1.6973,
        "EV_EBITDA": 6.9857,
        "EV_EBIT": 10.308,
        "EV_RECEITA": 0.6478,
        "DY": 3.6992,
        "PAYOUT": 44.6157,
        "ROE": 15.1345,
        "ROA": 8.3362,
        "ROIC": 9.8916,
        "MARGEM_EBITDA": 9.2735,
        "MARGEM_LIQUIDA": 4.6114,
        "DIV_LIQ_EBITDA": 0.9881,
        "DIV_LIQ_PL": 0.2796,
        "ICJ": 2.5993,
        "COMPOSICAO_DIVIDA": 13.3873,
        "LIQ_CORRENTE": 2.4483,
        "LIQ_SECA": 1.2472,
        "LIQ_GERAL": 1.4139,
        "GIRO_ATIVO": 1.6368,
        "PME": 87.3806,
        "CICLO_CAIXA": 81.6737,
        "NCG_RECEITA": 19.97
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 13850574.18,
        "P_L": 10.3758,
        "P_VPA": 1.5002,
        "EV_EBITDA": 5.8601,
        "EV_EBIT": 6.9161,
        "EV_RECEITA": 0.4507,
        "DY": 4.0475,
        "PAYOUT": 41.9957,
        "ROE": 14.8274,
        "ROA": 7.7194,
        "ROIC": 14.0209,
        "MARGEM_EBITDA": 7.6906,
        "MARGEM_LIQUIDA": 4.1604,
        "DIV_LIQ_EBITDA": 0.2471,
        "DIV_LIQ_PL": 0.066,
        "ICJ": 2.4913,
        "COMPOSICAO_DIVIDA": 18.5142,
        "LIQ_CORRENTE": 2.3242,
        "LIQ_SECA": 1.2672,
        "LIQ_GERAL": 1.3012,
        "GIRO_ATIVO": 1.7602,
        "PME": 71.6294,
        "CICLO_CAIXA": 65.1245,
        "NCG_RECEITA": 15.4121
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 15469472.46,
        "P_L": 8.1318,
        "P_VPA": 1.3749,
        "EV_EBITDA": 5.2151,
        "EV_EBIT": 6.9111,
        "EV_RECEITA": 0.4619,
        "DY": 3.6239,
        "PAYOUT": 29.4688,
        "ROE": 18.4263,
        "ROA": 9.1466,
        "ROIC": 12.7242,
        "MARGEM_EBITDA": 8.8579,
        "MARGEM_LIQUIDA": 5.1975,
        "DIV_LIQ_EBITDA": 0.4437,
        "DIV_LIQ_PL": 0.1279,
        "ICJ": 2.2886,
        "COMPOSICAO_DIVIDA": 20.4175,
        "LIQ_CORRENTE": 1.9309,
        "LIQ_SECA": 1.0377,
        "LIQ_GERAL": 1.1155,
        "GIRO_ATIVO": 1.5446,
        "PME": 72.727,
        "CICLO_CAIXA": 59.2598,
        "NCG_RECEITA": 14.548
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-16T21:22:28.030512",
    "preco_utilizado": 4.56,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 2248469834,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 10253022.44,
      "P_L": 5.3897,
      "P_VPA": 0.9113,
      "EV_EBITDA": 3.6061,
      "EV_EBIT": 4.7789,
      "EV_RECEITA": 0.3194,
      "DY": 5.4676,
      "PAYOUT": 29.4688,
      "ROE": 18.4263,
      "ROA": 9.1466,
      "ROIC": 12.7242,
      "MARGEM_EBITDA": 8.8579,
      "MARGEM_LIQUIDA": 5.1975,
      "DIV_LIQ_EBITDA": 0.4437,
      "DIV_LIQ_PL": 0.1279,
      "ICJ": 2.2886,
      "COMPOSICAO_DIVIDA": 20.4175,
      "LIQ_CORRENTE": 1.9309,
      "LIQ_SECA": 1.0377,
      "LIQ_GERAL": 1.1155,
      "GIRO_ATIVO": 1.5446,
      "PME": 72.727,
      "CICLO_CAIXA": 59.2598,
      "NCG_RECEITA": 14.548
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
