// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["LAND3"] = {
  "ticker": "LAND3",
  "ticker_preco": "LAND3",
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
    "2020": {
      "periodo_referencia": "2020T4",
      "multiplos": {
        "VALOR_MERCADO": 833325.49,
        "P_L": 15.4093,
        "P_VPA": 1.2847,
        "EV_EBITDA": 11.3226,
        "EV_EBIT": 11.3226,
        "EV_RECEITA": 10.7784,
        "DY": null,
        "PAYOUT": null,
        "ROE": 8.337,
        "ROA": 7.1856,
        "ROIC": 7.5807,
        "MARGEM_EBITDA": 95.1936,
        "MARGEM_LIQUIDA": 72.9409,
        "DIV_LIQ_EBITDA": -0.4845,
        "DIV_LIQ_PL": -0.0527,
        "ICJ": 37.1855,
        "COMPOSICAO_DIVIDA": null,
        "LIQ_CORRENTE": 4.5327,
        "LIQ_SECA": 4.3416,
        "LIQ_GERAL": 1.1882,
        "GIRO_ATIVO": 0.0985,
        "PME": 144.7817,
        "CICLO_CAIXA": 146.7385,
        "NCG_RECEITA": -0.8551
      }
    },
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": 2026539.82,
        "P_L": 85.3172,
        "P_VPA": 2.9114,
        "EV_EBITDA": 25.7157,
        "EV_EBIT": 27.5748,
        "EV_RECEITA": 19.9075,
        "DY": null,
        "PAYOUT": null,
        "ROE": 5.6552,
        "ROA": 4.313,
        "ROIC": 6.6667,
        "MARGEM_EBITDA": 77.4138,
        "MARGEM_LIQUIDA": 36.4679,
        "DIV_LIQ_EBITDA": 0.6089,
        "DIV_LIQ_PL": 0.0706,
        "ICJ": 4.2887,
        "COMPOSICAO_DIVIDA": 81.6491,
        "LIQ_CORRENTE": 1.1087,
        "LIQ_SECA": 1.1087,
        "LIQ_GERAL": 0.4718,
        "GIRO_ATIVO": 0.1032,
        "PME": 0.1008,
        "CICLO_CAIXA": 213.041,
        "NCG_RECEITA": 43.2534
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 2612562.02,
        "P_L": 19.0464,
        "P_VPA": 3.3241,
        "EV_EBITDA": 42.6479,
        "EV_EBIT": 47.0532,
        "EV_RECEITA": 27.7889,
        "DY": 0.7547,
        "PAYOUT": 14.3743,
        "ROE": 18.5112,
        "ROA": 13.8177,
        "ROIC": 4.5517,
        "MARGEM_EBITDA": 65.1588,
        "MARGEM_LIQUIDA": 144.3707,
        "DIV_LIQ_EBITDA": 0.4472,
        "DIV_LIQ_PL": 0.0352,
        "ICJ": 3.4539,
        "COMPOSICAO_DIVIDA": 100.0,
        "LIQ_CORRENTE": 0.513,
        "LIQ_SECA": 0.513,
        "LIQ_GERAL": 0.6419,
        "GIRO_ATIVO": 0.0975,
        "PME": 0.0,
        "CICLO_CAIXA": 183.8743,
        "NCG_RECEITA": -22.75
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 1626235.66,
        "P_L": 46.1815,
        "P_VPA": 2.2763,
        "EV_EBITDA": 27.3775,
        "EV_EBIT": 29.1885,
        "EV_RECEITA": 18.9105,
        "DY": 8.0148,
        "PAYOUT": 370.1352,
        "ROE": 4.6941,
        "ROA": 3.6736,
        "ROIC": 4.767,
        "MARGEM_EBITDA": 69.0731,
        "MARGEM_LIQUIDA": 38.3904,
        "DIV_LIQ_EBITDA": 1.7101,
        "DIV_LIQ_PL": 0.1517,
        "ICJ": 3.5997,
        "COMPOSICAO_DIVIDA": 41.3483,
        "LIQ_CORRENTE": 0.5345,
        "LIQ_SECA": 0.5345,
        "LIQ_GERAL": 0.4044,
        "GIRO_ATIVO": 0.0973,
        "PME": 0.0,
        "CICLO_CAIXA": 109.9828,
        "NCG_RECEITA": 14.3525
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 1346215.2,
        "P_L": 183.6082,
        "P_VPA": 2.0698,
        "EV_EBITDA": 60.2988,
        "EV_EBIT": 70.3358,
        "EV_RECEITA": 21.025,
        "DY": 0.6212,
        "PAYOUT": 114.0497,
        "ROE": 1.0744,
        "ROA": 0.8049,
        "ROIC": 1.8196,
        "MARGEM_EBITDA": 34.868,
        "MARGEM_LIQUIDA": 10.73,
        "DIV_LIQ_EBITDA": 3.7969,
        "DIV_LIQ_PL": 0.1391,
        "ICJ": 1.2697,
        "COMPOSICAO_DIVIDA": 57.2903,
        "LIQ_CORRENTE": 0.5576,
        "LIQ_SECA": 0.5576,
        "LIQ_GERAL": 0.4477,
        "GIRO_ATIVO": 0.0777,
        "PME": 0.0,
        "CICLO_CAIXA": 169.3578,
        "NCG_RECEITA": 17.4472
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 858344.5,
        "P_L": -79.6012,
        "P_VPA": 1.3158,
        "EV_EBITDA": -160.2449,
        "EV_EBIT": -99.9224,
        "EV_RECEITA": 10.0066,
        "DY": 0.8117,
        "PAYOUT": -64.6091,
        "ROE": 3.7529,
        "ROA": 2.9095,
        "ROIC": -0.8558,
        "MARGEM_EBITDA": -6.2446,
        "MARGEM_LIQUIDA": 28.7094,
        "DIV_LIQ_EBITDA": -7.84,
        "DIV_LIQ_PL": 0.0677,
        "ICJ": -0.4923,
        "COMPOSICAO_DIVIDA": 66.7988,
        "LIQ_CORRENTE": 0.8204,
        "LIQ_SECA": 0.8204,
        "LIQ_GERAL": 0.3859,
        "GIRO_ATIVO": 0.1057,
        "PME": 0.0,
        "CICLO_CAIXA": 67.3179,
        "NCG_RECEITA": 12.7309
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-15T19:04:37.891979",
    "preco_utilizado": 8.66,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 96226962,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 833325.49,
      "P_L": -77.281,
      "P_VPA": 1.2774,
      "EV_EBITDA": -155.8026,
      "EV_EBIT": -97.1524,
      "EV_RECEITA": 9.7292,
      "DY": 0.836,
      "PAYOUT": -64.6091,
      "ROE": 3.7529,
      "ROA": 2.9095,
      "ROIC": -0.8558,
      "MARGEM_EBITDA": -6.2446,
      "MARGEM_LIQUIDA": 28.7094,
      "DIV_LIQ_EBITDA": -7.84,
      "DIV_LIQ_PL": 0.0677,
      "ICJ": -0.4923,
      "COMPOSICAO_DIVIDA": 66.7988,
      "LIQ_CORRENTE": 0.8204,
      "LIQ_SECA": 0.8204,
      "LIQ_GERAL": 0.3859,
      "GIRO_ATIVO": 0.1057,
      "PME": 0.0,
      "CICLO_CAIXA": 67.3179,
      "NCG_RECEITA": 12.7309
    }
  },
  "periodos_disponiveis": [
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
