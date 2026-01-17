// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["MTRE3"] = {
  "ticker": "MTRE3",
  "ticker_preco": "MTRE3",
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
        "VALOR_MERCADO": 387135.84,
        "P_L": 23.7405,
        "P_VPA": 9.604,
        "EV_EBITDA": 22.9217,
        "EV_EBIT": 22.9217,
        "EV_RECEITA": 3.1904,
        "DY": 13.8194,
        "PAYOUT": 328.0784,
        "ROE": 40.454,
        "ROA": 6.0111,
        "ROIC": 10.4169,
        "MARGEM_EBITDA": 13.9187,
        "MARGEM_LIQUIDA": 10.8542,
        "DIV_LIQ_EBITDA": 4.4082,
        "DIV_LIQ_PL": 2.2868,
        "ICJ": 8.5212,
        "COMPOSICAO_DIVIDA": 9.7264,
        "LIQ_CORRENTE": 3.2858,
        "LIQ_SECA": 1.8547,
        "LIQ_GERAL": 1.1505,
        "GIRO_ATIVO": 0.5538,
        "PME": 383.0433,
        "CICLO_CAIXA": 619.9004,
        "NCG_RECEITA": 102.5367
      }
    },
    "2019": {
      "periodo_referencia": "2019T4",
      "multiplos": {
        "VALOR_MERCADO": 387135.84,
        "P_L": 12.0995,
        "P_VPA": 6.1135,
        "EV_EBITDA": 11.2749,
        "EV_EBIT": 11.2749,
        "EV_RECEITA": 1.5254,
        "DY": 13.8194,
        "PAYOUT": 167.2076,
        "ROE": 61.7475,
        "ROA": 9.5894,
        "ROIC": 18.3343,
        "MARGEM_EBITDA": 13.5289,
        "MARGEM_LIQUIDA": 10.26,
        "DIV_LIQ_EBITDA": 2.0989,
        "DIV_LIQ_PL": 1.3984,
        "ICJ": 6.1699,
        "COMPOSICAO_DIVIDA": 85.8216,
        "LIQ_CORRENTE": 1.3533,
        "LIQ_SECA": 1.0031,
        "LIQ_GERAL": 1.1387,
        "GIRO_ATIVO": 0.7874,
        "PME": 132.3864,
        "CICLO_CAIXA": 316.0477,
        "NCG_RECEITA": 48.1414
      }
    },
    "2020": {
      "periodo_referencia": "2020T4",
      "multiplos": {
        "VALOR_MERCADO": 1104289.12,
        "P_L": 22.4984,
        "P_VPA": 1.0961,
        "EV_EBITDA": 9.2322,
        "EV_EBIT": 10.0701,
        "EV_RECEITA": 0.9321,
        "DY": 4.8447,
        "PAYOUT": 108.9985,
        "ROE": 9.1679,
        "ROA": 5.7165,
        "ROIC": 8.7699,
        "MARGEM_EBITDA": 10.0965,
        "MARGEM_LIQUIDA": 11.935,
        "DIV_LIQ_EBITDA": -17.3631,
        "DIV_LIQ_PL": -0.7156,
        "ICJ": 9.7608,
        "COMPOSICAO_DIVIDA": 58.607,
        "LIQ_CORRENTE": 5.0946,
        "LIQ_SECA": 4.3771,
        "LIQ_GERAL": 4.1559,
        "GIRO_ATIVO": 0.3113,
        "PME": 202.2477,
        "CICLO_CAIXA": 317.3609,
        "NCG_RECEITA": 31.7773
      }
    },
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": 575415.02,
        "P_L": 21.0128,
        "P_VPA": 0.5783,
        "EV_EBITDA": 9.4189,
        "EV_EBIT": 10.5902,
        "EV_RECEITA": 0.7469,
        "DY": 9.2976,
        "PAYOUT": 195.3686,
        "ROE": 2.7352,
        "ROA": 1.8845,
        "ROIC": 3.1498,
        "MARGEM_EBITDA": 7.9293,
        "MARGEM_LIQUIDA": 4.7708,
        "DIV_LIQ_EBITDA": -3.2237,
        "DIV_LIQ_PL": -0.1475,
        "ICJ": 1.5823,
        "COMPOSICAO_DIVIDA": 84.4416,
        "LIQ_CORRENTE": 3.2699,
        "LIQ_SECA": 1.5495,
        "LIQ_GERAL": 2.6444,
        "GIRO_ATIVO": 0.3621,
        "PME": 608.3141,
        "CICLO_CAIXA": 763.3204,
        "NCG_RECEITA": 118.4771
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 267610.29,
        "P_L": 7.19,
        "P_VPA": 0.2665,
        "EV_EBITDA": 9.8575,
        "EV_EBIT": 10.9251,
        "EV_RECEITA": 0.7102,
        "DY": 19.9917,
        "PAYOUT": 143.7392,
        "ROE": 3.7239,
        "ROA": 2.0416,
        "ROIC": 2.5523,
        "MARGEM_EBITDA": 7.2042,
        "MARGEM_LIQUIDA": 4.9062,
        "DIV_LIQ_EBITDA": 4.9609,
        "DIV_LIQ_PL": 0.27,
        "ICJ": 1.8672,
        "COMPOSICAO_DIVIDA": 36.8279,
        "LIQ_CORRENTE": 2.8364,
        "LIQ_SECA": 1.2698,
        "LIQ_GERAL": 1.9085,
        "GIRO_ATIVO": 0.3681,
        "PME": 552.9044,
        "CICLO_CAIXA": 719.7606,
        "NCG_RECEITA": 121.6692
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 521469.86,
        "P_L": 5.4952,
        "P_VPA": 0.5082,
        "EV_EBITDA": 8.7187,
        "EV_EBIT": 9.3957,
        "EV_RECEITA": 1.0572,
        "DY": 10.2594,
        "PAYOUT": 56.3772,
        "ROE": 9.3482,
        "ROA": 4.4906,
        "ROIC": 4.6355,
        "MARGEM_EBITDA": 12.1253,
        "MARGEM_LIQUIDA": 10.2436,
        "DIV_LIQ_EBITDA": 4.0763,
        "DIV_LIQ_PL": 0.4462,
        "ICJ": 5.3325,
        "COMPOSICAO_DIVIDA": 46.4753,
        "LIQ_CORRENTE": 2.6267,
        "LIQ_SECA": 1.3276,
        "LIQ_GERAL": 1.8233,
        "GIRO_ATIVO": 0.4278,
        "PME": 397.7346,
        "CICLO_CAIXA": 600.2785,
        "NCG_RECEITA": 122.3322
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 266552.55,
        "P_L": 3.8285,
        "P_VPA": 0.2558,
        "EV_EBITDA": 6.9424,
        "EV_EBIT": 7.6638,
        "EV_RECEITA": 0.5565,
        "DY": 20.071,
        "PAYOUT": 76.8409,
        "ROE": 6.7328,
        "ROA": 3.1897,
        "ROIC": 3.9477,
        "MARGEM_EBITDA": 8.0156,
        "MARGEM_LIQUIDA": 5.9032,
        "DIV_LIQ_EBITDA": 4.1229,
        "DIV_LIQ_PL": 0.3741,
        "ICJ": 6.1883,
        "COMPOSICAO_DIVIDA": 59.2871,
        "LIQ_CORRENTE": 2.2651,
        "LIQ_SECA": 1.2292,
        "LIQ_GERAL": 1.8261,
        "GIRO_ATIVO": 0.536,
        "PME": 312.506,
        "CICLO_CAIXA": 466.5555,
        "NCG_RECEITA": 92.1776
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 396655.58,
        "P_L": 5.3632,
        "P_VPA": 0.3821,
        "EV_EBITDA": 8.7339,
        "EV_EBIT": 10.3515,
        "EV_RECEITA": 0.8275,
        "DY": 13.4877,
        "PAYOUT": 72.337,
        "ROE": 7.1273,
        "ROA": 3.3955,
        "ROIC": 3.7277,
        "MARGEM_EBITDA": 9.4746,
        "MARGEM_LIQUIDA": 6.7773,
        "DIV_LIQ_EBITDA": 4.8976,
        "DIV_LIQ_PL": 0.4878,
        "ICJ": 14.0978,
        "COMPOSICAO_DIVIDA": 53.7447,
        "LIQ_CORRENTE": 2.3192,
        "LIQ_SECA": 1.1926,
        "LIQ_GERAL": 1.7522,
        "GIRO_ATIVO": 0.4843,
        "PME": 370.9242,
        "CICLO_CAIXA": 585.2543,
        "NCG_RECEITA": 110.3145
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-17T10:32:19.557925",
    "preco_utilizado": 3.66,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 105774820,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 387135.84,
      "P_L": 5.2345,
      "P_VPA": 0.3729,
      "EV_EBITDA": 8.6418,
      "EV_EBIT": 10.2424,
      "EV_RECEITA": 0.8188,
      "DY": 13.8194,
      "PAYOUT": 72.337,
      "ROE": 7.1273,
      "ROA": 3.3955,
      "ROIC": 3.7277,
      "MARGEM_EBITDA": 9.4746,
      "MARGEM_LIQUIDA": 6.7773,
      "DIV_LIQ_EBITDA": 4.8976,
      "DIV_LIQ_PL": 0.4878,
      "ICJ": 14.0978,
      "COMPOSICAO_DIVIDA": 53.7447,
      "LIQ_CORRENTE": 2.3192,
      "LIQ_SECA": 1.1926,
      "LIQ_GERAL": 1.7522,
      "GIRO_ATIVO": 0.4843,
      "PME": 370.9242,
      "CICLO_CAIXA": 585.2543,
      "NCG_RECEITA": 110.3145
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
