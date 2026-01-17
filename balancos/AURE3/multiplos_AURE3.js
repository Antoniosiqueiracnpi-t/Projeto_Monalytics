// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["AURE3"] = {
  "ticker": "AURE3",
  "ticker_preco": "AURE3",
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
        "VALOR_MERCADO": 11540000.0,
        "P_L": 68.2146,
        "P_VPA": 1.3982,
        "EV_EBITDA": 13.9861,
        "EV_EBIT": 13.9861,
        "EV_RECEITA": 6.1532,
        "DY": 0.4942,
        "PAYOUT": 33.713,
        "ROE": 2.0497,
        "ROA": 0.9248,
        "ROIC": 6.1408,
        "MARGEM_EBITDA": 43.9951,
        "MARGEM_LIQUIDA": 7.3339,
        "DIV_LIQ_EBITDA": 2.6148,
        "DIV_LIQ_PL": 0.3215,
        "ICJ": 1.4223,
        "COMPOSICAO_DIVIDA": 3.4812,
        "LIQ_CORRENTE": 1.2211,
        "LIQ_SECA": 1.2211,
        "LIQ_GERAL": 0.766,
        "GIRO_ATIVO": 0.1261,
        "PME": 0.0,
        "CICLO_CAIXA": 23.0922,
        "NCG_RECEITA": -29.2524
      }
    },
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": 11540000.0,
        "P_L": 37.0292,
        "P_VPA": 1.2756,
        "EV_EBITDA": 7.1678,
        "EV_EBIT": 10.7189,
        "EV_RECEITA": 5.5549,
        "DY": 0.4942,
        "PAYOUT": 18.3006,
        "ROE": 3.6028,
        "ROA": 1.6465,
        "ROIC": 7.428,
        "MARGEM_EBITDA": 77.4978,
        "MARGEM_LIQUIDA": 11.8762,
        "DIV_LIQ_EBITDA": 1.4932,
        "DIV_LIQ_PL": 0.3357,
        "ICJ": 1.5774,
        "COMPOSICAO_DIVIDA": 4.4692,
        "LIQ_CORRENTE": 1.4682,
        "LIQ_SECA": 1.4682,
        "LIQ_GERAL": 0.7808,
        "GIRO_ATIVO": 0.1341,
        "PME": 0.0,
        "CICLO_CAIXA": -20.9685,
        "NCG_RECEITA": -27.3957
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 11540000.0,
        "P_L": 4.3082,
        "P_VPA": 0.7566,
        "EV_EBITDA": 7.1954,
        "EV_EBIT": 10.1959,
        "EV_RECEITA": 2.5714,
        "DY": 0.4942,
        "PAYOUT": 2.1292,
        "ROE": 22.0466,
        "ROA": 10.3331,
        "ROIC": 5.1301,
        "MARGEM_EBITDA": 35.7372,
        "MARGEM_LIQUIDA": 48.5634,
        "DIV_LIQ_EBITDA": 1.3409,
        "DIV_LIQ_PL": 0.1733,
        "ICJ": 1.1822,
        "COMPOSICAO_DIVIDA": 4.7413,
        "LIQ_CORRENTE": 1.4929,
        "LIQ_SECA": 1.4929,
        "LIQ_GERAL": 1.0037,
        "GIRO_ATIVO": 0.1709,
        "PME": 0.0,
        "CICLO_CAIXA": -4.8744,
        "NCG_RECEITA": -16.0141
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 12810000.0,
        "P_L": -40.3225,
        "P_VPA": 1.0357,
        "EV_EBITDA": 9.3198,
        "EV_EBIT": 14.8896,
        "EV_RECEITA": 2.5866,
        "DY": 0.4452,
        "PAYOUT": -17.9525,
        "ROE": -2.3003,
        "ROA": -1.0369,
        "ROIC": 4.5583,
        "MARGEM_EBITDA": 27.754,
        "MARGEM_LIQUIDA": -5.139,
        "DIV_LIQ_EBITDA": 1.8535,
        "DIV_LIQ_PL": 0.2571,
        "ICJ": 0.9074,
        "COMPOSICAO_DIVIDA": 13.3654,
        "LIQ_CORRENTE": 1.542,
        "LIQ_SECA": 1.542,
        "LIQ_GERAL": 0.7557,
        "GIRO_ATIVO": 0.2132,
        "PME": 0.0,
        "CICLO_CAIXA": -2.9218,
        "NCG_RECEITA": -4.7464
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 9148792.15,
        "P_L": 33.6515,
        "P_VPA": 0.6317,
        "EV_EBITDA": 15.1169,
        "EV_EBIT": 22.5762,
        "EV_RECEITA": 3.618,
        "DY": 0.6548,
        "PAYOUT": 22.035,
        "ROE": 2.0249,
        "ROA": 0.6651,
        "ROIC": 2.4713,
        "MARGEM_EBITDA": 23.9335,
        "MARGEM_LIQUIDA": 3.3731,
        "DIV_LIQ_EBITDA": 10.3742,
        "DIV_LIQ_PL": 1.3817,
        "ICJ": 0.875,
        "COMPOSICAO_DIVIDA": 9.9562,
        "LIQ_CORRENTE": 1.5575,
        "LIQ_SECA": 1.5575,
        "LIQ_GERAL": 0.4391,
        "GIRO_ATIVO": 0.1528,
        "PME": 0.0,
        "CICLO_CAIXA": -4.3993,
        "NCG_RECEITA": -6.3108
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 10787381.79,
        "P_L": -8.5872,
        "P_VPA": 0.7953,
        "EV_EBITDA": 8.2669,
        "EV_EBIT": 24.2845,
        "EV_RECEITA": 2.4485,
        "DY": 0.5553,
        "PAYOUT": -4.7688,
        "ROE": -9.6072,
        "ROA": -3.1278,
        "ROIC": 2.4924,
        "MARGEM_EBITDA": 29.6177,
        "MARGEM_LIQUIDA": -10.0168,
        "DIV_LIQ_EBITDA": 5.3627,
        "DIV_LIQ_PL": 1.4685,
        "ICJ": 0.3638,
        "COMPOSICAO_DIVIDA": 8.986,
        "LIQ_CORRENTE": 1.3006,
        "LIQ_SECA": 1.3006,
        "LIQ_GERAL": 0.3891,
        "GIRO_ATIVO": 0.2568,
        "PME": 0.0,
        "CICLO_CAIXA": -2.6426,
        "NCG_RECEITA": -6.3085
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-17T21:43:02.696892",
    "preco_utilizado": 11.54,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 1050377974,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 12121361.82,
      "P_L": -9.6491,
      "P_VPA": 0.8936,
      "EV_EBITDA": 8.6261,
      "EV_EBIT": 25.3395,
      "EV_RECEITA": 2.5548,
      "DY": 0.4942,
      "PAYOUT": -4.7688,
      "ROE": -9.6072,
      "ROA": -3.1278,
      "ROIC": 2.4924,
      "MARGEM_EBITDA": 29.6177,
      "MARGEM_LIQUIDA": -10.0168,
      "DIV_LIQ_EBITDA": 5.3627,
      "DIV_LIQ_PL": 1.4685,
      "ICJ": 0.3638,
      "COMPOSICAO_DIVIDA": 8.986,
      "LIQ_CORRENTE": 1.3006,
      "LIQ_SECA": 1.3006,
      "LIQ_GERAL": 0.3891,
      "GIRO_ATIVO": 0.2568,
      "PME": 0.0,
      "CICLO_CAIXA": -2.6426,
      "NCG_RECEITA": -6.3085
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
