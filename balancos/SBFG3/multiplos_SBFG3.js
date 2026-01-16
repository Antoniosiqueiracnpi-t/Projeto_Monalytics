// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["SBFG3"] = {
  "ticker": "SBFG3",
  "ticker_preco": "SBFG3",
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
        "VALOR_MERCADO": 2696775.27,
        "P_L": 18.1298,
        "P_VPA": 14.085,
        "EV_EBITDA": 15.6301,
        "EV_EBIT": 15.6301,
        "EV_RECEITA": 1.2363,
        "DY": 4.2908,
        "PAYOUT": 77.7917,
        "ROE": 77.6898,
        "ROA": 8.2716,
        "ROIC": 38.6516,
        "MARGEM_EBITDA": 7.9096,
        "MARGEM_LIQUIDA": 6.5382,
        "DIV_LIQ_EBITDA": 0.6436,
        "DIV_LIQ_PL": 0.6048,
        "ICJ": 1.1783,
        "COMPOSICAO_DIVIDA": 26.3947,
        "LIQ_CORRENTE": 0.8941,
        "LIQ_SECA": 0.5346,
        "LIQ_GERAL": 0.7753,
        "GIRO_ATIVO": 1.2651,
        "PME": 104.0127,
        "CICLO_CAIXA": -50.661,
        "NCG_RECEITA": -10.8501
      }
    },
    "2019": {
      "periodo_referencia": "2019T4",
      "multiplos": {
        "VALOR_MERCADO": 6796802.14,
        "P_L": 21.9445,
        "P_VPA": 5.8159,
        "EV_EBITDA": 16.804,
        "EV_EBIT": 16.804,
        "EV_RECEITA": 3.0941,
        "DY": 1.7025,
        "PAYOUT": 37.3599,
        "ROE": 45.5438,
        "ROA": 10.8069,
        "ROIC": 13.7619,
        "MARGEM_EBITDA": 18.4131,
        "MARGEM_LIQUIDA": 12.168,
        "DIV_LIQ_EBITDA": 2.3024,
        "DIV_LIQ_PL": 0.9234,
        "ICJ": 1.6788,
        "COMPOSICAO_DIVIDA": 10.2676,
        "LIQ_CORRENTE": 1.427,
        "LIQ_SECA": 1.0351,
        "LIQ_GERAL": 0.805,
        "GIRO_ATIVO": 0.6471,
        "PME": 119.8901,
        "CICLO_CAIXA": 17.9066,
        "NCG_RECEITA": 18.985
      }
    },
    "2020": {
      "periodo_referencia": "2020T4",
      "multiplos": {
        "VALOR_MERCADO": 6587272.3,
        "P_L": -58.3952,
        "P_VPA": 3.3769,
        "EV_EBITDA": 47.1088,
        "EV_EBIT": -108.1828,
        "EV_RECEITA": 3.2712,
        "DY": 2.0153,
        "PAYOUT": -117.6845,
        "ROE": -7.2326,
        "ROA": -2.2277,
        "ROIC": -1.484,
        "MARGEM_EBITDA": 6.944,
        "MARGEM_LIQUIDA": -4.6868,
        "DIV_LIQ_EBITDA": 7.6954,
        "DIV_LIQ_PL": 0.6593,
        "ICJ": -0.3144,
        "COMPOSICAO_DIVIDA": 11.8416,
        "LIQ_CORRENTE": 1.7757,
        "LIQ_SECA": 1.2948,
        "LIQ_GERAL": 0.994,
        "GIRO_ATIVO": 0.3886,
        "PME": 236.3567,
        "CICLO_CAIXA": 209.8633,
        "NCG_RECEITA": 47.1846
      }
    },
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": 5008189.23,
        "P_L": 10.06,
        "P_VPA": 2.2512,
        "EV_EBITDA": 6.483,
        "EV_EBIT": 16.3472,
        "EV_RECEITA": 1.2871,
        "DY": 2.6607,
        "PAYOUT": 26.7665,
        "ROE": 23.8464,
        "ROA": 7.4635,
        "ROIC": 6.9994,
        "MARGEM_EBITDA": 19.8535,
        "MARGEM_LIQUIDA": 9.7414,
        "DIV_LIQ_EBITDA": 1.5469,
        "DIV_LIQ_PL": 0.7055,
        "ICJ": 1.0669,
        "COMPOSICAO_DIVIDA": 9.7918,
        "LIQ_CORRENTE": 1.6738,
        "LIQ_SECA": 1.1915,
        "LIQ_GERAL": 1.0128,
        "GIRO_ATIVO": 0.7151,
        "PME": 136.0135,
        "CICLO_CAIXA": 110.4196,
        "NCG_RECEITA": 21.8035
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 2864690.58,
        "P_L": 14.0013,
        "P_VPA": 1.1887,
        "EV_EBITDA": 6.6648,
        "EV_EBIT": 12.2889,
        "EV_RECEITA": 0.7887,
        "DY": 4.663,
        "PAYOUT": 65.2877,
        "ROE": 8.8295,
        "ROA": 2.6203,
        "ROIC": 5.9156,
        "MARGEM_EBITDA": 11.8345,
        "MARGEM_LIQUIDA": 3.268,
        "DIV_LIQ_EBITDA": 2.7984,
        "DIV_LIQ_PL": 0.8604,
        "ICJ": 0.9173,
        "COMPOSICAO_DIVIDA": 11.1536,
        "LIQ_CORRENTE": 1.5353,
        "LIQ_SECA": 0.9461,
        "LIQ_GERAL": 0.9864,
        "GIRO_ATIVO": 0.7391,
        "PME": 188.3624,
        "CICLO_CAIXA": 117.6515,
        "NCG_RECEITA": 22.9648
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 2678671.43,
        "P_L": 15.8678,
        "P_VPA": 1.0539,
        "EV_EBITDA": 5.1583,
        "EV_EBIT": 9.4082,
        "EV_RECEITA": 0.7146,
        "DY": 4.9897,
        "PAYOUT": 79.1752,
        "ROE": 6.8187,
        "ROA": 1.9762,
        "ROIC": 7.2131,
        "MARGEM_EBITDA": 13.8534,
        "MARGEM_LIQUIDA": 2.4155,
        "DIV_LIQ_EBITDA": 2.3916,
        "DIV_LIQ_PL": 0.911,
        "ICJ": 0.8992,
        "COMPOSICAO_DIVIDA": 25.2844,
        "LIQ_CORRENTE": 1.65,
        "LIQ_SECA": 1.052,
        "LIQ_GERAL": 1.0097,
        "GIRO_ATIVO": 0.8113,
        "PME": 166.5112,
        "CICLO_CAIXA": 135.6943,
        "NCG_RECEITA": 25.442
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 2486492.27,
        "P_L": 4.6404,
        "P_VPA": 0.8254,
        "EV_EBITDA": 4.3179,
        "EV_EBIT": 7.2,
        "EV_RECEITA": 0.6162,
        "DY": 5.3814,
        "PAYOUT": 24.972,
        "ROE": 19.2957,
        "ROA": 6.1027,
        "ROIC": 8.1895,
        "MARGEM_EBITDA": 14.2714,
        "MARGEM_LIQUIDA": 7.4924,
        "DIV_LIQ_EBITDA": 1.8817,
        "DIV_LIQ_PL": 0.6376,
        "ICJ": 2.1435,
        "COMPOSICAO_DIVIDA": 24.1129,
        "LIQ_CORRENTE": 1.5128,
        "LIQ_SECA": 0.9958,
        "LIQ_GERAL": 1.0792,
        "GIRO_ATIVO": 0.7994,
        "PME": 164.8268,
        "CICLO_CAIXA": 140.4296,
        "NCG_RECEITA": 19.0032
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 3172168.74,
        "P_L": 9.4711,
        "P_VPA": 1.065,
        "EV_EBITDA": 5.4631,
        "EV_EBIT": 9.9402,
        "EV_RECEITA": 0.7258,
        "DY": 4.2182,
        "PAYOUT": 39.9508,
        "ROE": 11.2216,
        "ROA": 3.8255,
        "ROIC": 6.8851,
        "MARGEM_EBITDA": 13.2848,
        "MARGEM_LIQUIDA": 4.4772,
        "DIV_LIQ_EBITDA": 2.2711,
        "DIV_LIQ_PL": 0.7578,
        "ICJ": 1.0491,
        "COMPOSICAO_DIVIDA": 22.6659,
        "LIQ_CORRENTE": 1.4363,
        "LIQ_SECA": 0.8155,
        "LIQ_GERAL": 1.0818,
        "GIRO_ATIVO": 0.8248,
        "PME": 193.1869,
        "CICLO_CAIXA": 149.675,
        "NCG_RECEITA": 18.9508
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-16T20:56:56.916229",
    "preco_utilizado": 12.78,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 244012980,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 3118485.88,
      "P_L": 9.3108,
      "P_VPA": 1.0469,
      "EV_EBITDA": 5.409,
      "EV_EBIT": 9.8419,
      "EV_RECEITA": 0.7186,
      "DY": 4.2908,
      "PAYOUT": 39.9508,
      "ROE": 11.2216,
      "ROA": 3.8255,
      "ROIC": 6.8851,
      "MARGEM_EBITDA": 13.2848,
      "MARGEM_LIQUIDA": 4.4772,
      "DIV_LIQ_EBITDA": 2.2711,
      "DIV_LIQ_PL": 0.7578,
      "ICJ": 1.0491,
      "COMPOSICAO_DIVIDA": 22.6659,
      "LIQ_CORRENTE": 1.4363,
      "LIQ_SECA": 0.8155,
      "LIQ_GERAL": 1.0818,
      "GIRO_ATIVO": 0.8248,
      "PME": 193.1869,
      "CICLO_CAIXA": 149.675,
      "NCG_RECEITA": 18.9508
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
