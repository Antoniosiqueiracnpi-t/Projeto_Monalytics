// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["PLPL3"] = {
  "ticker": "PLPL3",
  "ticker_preco": "PLPL3",
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
        "VALOR_MERCADO": 2804434.88,
        "P_L": 31.5385,
        "P_VPA": 29.236,
        "EV_EBITDA": 24.6239,
        "EV_EBIT": 28.6898,
        "EV_RECEITA": 4.2781,
        "DY": 10.9166,
        "PAYOUT": 344.2918,
        "ROE": 92.6994,
        "ROA": 12.8214,
        "ROIC": 37.4278,
        "MARGEM_EBITDA": 17.3739,
        "MARGEM_LIQUIDA": 13.182,
        "DIV_LIQ_EBITDA": 0.695,
        "DIV_LIQ_PL": 0.8492,
        "ICJ": 15.9438,
        "COMPOSICAO_DIVIDA": 13.2023,
        "LIQ_CORRENTE": 5.0487,
        "LIQ_SECA": 2.0128,
        "LIQ_GERAL": 1.1468,
        "GIRO_ATIVO": 0.9726,
        "PME": 322.8235,
        "CICLO_CAIXA": 357.4534,
        "NCG_RECEITA": 59.5253
      }
    },
    "2020": {
      "periodo_referencia": "2020T4",
      "multiplos": {
        "VALOR_MERCADO": 1158131.52,
        "P_L": 8.7602,
        "P_VPA": 5.0322,
        "EV_EBITDA": 7.1672,
        "EV_EBIT": 8.2693,
        "EV_RECEITA": 1.3814,
        "DY": 26.4346,
        "PAYOUT": 231.5722,
        "ROE": 81.0898,
        "ROA": 15.9775,
        "ROIC": 31.3749,
        "MARGEM_EBITDA": 19.2742,
        "MARGEM_LIQUIDA": 14.6738,
        "DIV_LIQ_EBITDA": 0.4979,
        "DIV_LIQ_PL": 0.3757,
        "ICJ": 32.0368,
        "COMPOSICAO_DIVIDA": 0.0409,
        "LIQ_CORRENTE": 5.9153,
        "LIQ_SECA": 5.9153,
        "LIQ_GERAL": 1.3072,
        "GIRO_ATIVO": 0.9372,
        "PME": 0.0,
        "CICLO_CAIXA": 28.1525,
        "NCG_RECEITA": 60.8526
      }
    },
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": 508597.44,
        "P_L": 3.765,
        "P_VPA": 1.6033,
        "EV_EBITDA": 3.7894,
        "EV_EBIT": 3.8055,
        "EV_RECEITA": 0.4902,
        "DY": 60.1945,
        "PAYOUT": 226.635,
        "ROE": 49.3577,
        "ROA": 12.1159,
        "ROIC": 25.0292,
        "MARGEM_EBITDA": 12.9365,
        "MARGEM_LIQUIDA": 10.626,
        "DIV_LIQ_EBITDA": 0.6968,
        "DIV_LIQ_PL": 0.3613,
        "ICJ": 17.6542,
        "COMPOSICAO_DIVIDA": 14.7284,
        "LIQ_CORRENTE": 4.7799,
        "LIQ_SECA": 4.7799,
        "LIQ_GERAL": 1.3197,
        "GIRO_ATIVO": 1.0022,
        "PME": 0.0,
        "CICLO_CAIXA": 14.3902,
        "NCG_RECEITA": 52.953
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 659746.88,
        "P_L": 4.9767,
        "P_VPA": 1.6131,
        "EV_EBITDA": 5.2234,
        "EV_EBIT": 5.2666,
        "EV_RECEITA": 0.5713,
        "DY": 46.4038,
        "PAYOUT": 230.9398,
        "ROE": 36.5093,
        "ROA": 9.1736,
        "ROIC": 17.754,
        "MARGEM_EBITDA": 10.9376,
        "MARGEM_LIQUIDA": 8.8839,
        "DIV_LIQ_EBITDA": 1.1811,
        "DIV_LIQ_PL": 0.4714,
        "ICJ": 6.6439,
        "COMPOSICAO_DIVIDA": 22.2362,
        "LIQ_CORRENTE": 3.437,
        "LIQ_SECA": 3.437,
        "LIQ_GERAL": 1.321,
        "GIRO_ATIVO": 0.9202,
        "PME": 0.0,
        "CICLO_CAIXA": 1.7064,
        "NCG_RECEITA": 54.3103
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 1989453.44,
        "P_L": 7.1843,
        "P_VPA": 3.0791,
        "EV_EBITDA": 6.0308,
        "EV_EBIT": 6.0885,
        "EV_RECEITA": 0.9419,
        "DY": 15.3885,
        "PAYOUT": 110.5566,
        "ROE": 52.491,
        "ROA": 15.1293,
        "ROIC": 34.781,
        "MARGEM_EBITDA": 15.6177,
        "MARGEM_LIQUIDA": 13.3645,
        "DIV_LIQ_EBITDA": -0.117,
        "DIV_LIQ_PL": -0.0586,
        "ICJ": 9.7474,
        "COMPOSICAO_DIVIDA": 34.7602,
        "LIQ_CORRENTE": 2.6338,
        "LIQ_SECA": 2.6338,
        "LIQ_GERAL": 1.4467,
        "GIRO_ATIVO": 1.0162,
        "PME": 0.0,
        "CICLO_CAIXA": 7.818,
        "NCG_RECEITA": 37.8145
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 1629168.99,
        "P_L": 4.1713,
        "P_VPA": 1.7793,
        "EV_EBITDA": 3.1355,
        "EV_EBIT": 3.1637,
        "EV_RECEITA": 0.547,
        "DY": 18.759,
        "PAYOUT": 78.2496,
        "ROE": 50.016,
        "ROA": 16.9068,
        "ROIC": 42.0366,
        "MARGEM_EBITDA": 17.4465,
        "MARGEM_LIQUIDA": 15.0832,
        "DIV_LIQ_EBITDA": -0.4708,
        "DIV_LIQ_PL": -0.2323,
        "ICJ": 5.714,
        "COMPOSICAO_DIVIDA": 5.1273,
        "LIQ_CORRENTE": 3.6987,
        "LIQ_SECA": 3.6987,
        "LIQ_GERAL": 1.5231,
        "GIRO_ATIVO": 1.0032,
        "PME": 0.0,
        "CICLO_CAIXA": 30.3711,
        "NCG_RECEITA": 32.0599
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 3356210.46,
        "P_L": 8.7777,
        "P_VPA": 3.1013,
        "EV_EBITDA": 7.123,
        "EV_EBIT": 7.4274,
        "EV_RECEITA": 1.1916,
        "DY": 9.106,
        "PAYOUT": 79.9296,
        "ROE": 38.3941,
        "ROA": 12.1433,
        "ROIC": 26.3592,
        "MARGEM_EBITDA": 16.7284,
        "MARGEM_LIQUIDA": 13.2811,
        "DIV_LIQ_EBITDA": 0.1542,
        "DIV_LIQ_PL": 0.0686,
        "ICJ": 3.8649,
        "COMPOSICAO_DIVIDA": 17.3257,
        "LIQ_CORRENTE": 3.7016,
        "LIQ_SECA": 3.7016,
        "LIQ_GERAL": 1.3748,
        "GIRO_ATIVO": 0.7521,
        "PME": 0.0,
        "CICLO_CAIXA": 42.2247,
        "NCG_RECEITA": 56.2921
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-17T10:32:20.200785",
    "preco_utilizado": 13.73,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 203901000,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 2799560.73,
      "P_L": 7.3219,
      "P_VPA": 2.5869,
      "EV_EBITDA": 5.9672,
      "EV_EBIT": 6.2222,
      "EV_RECEITA": 0.9982,
      "DY": 10.9166,
      "PAYOUT": 79.9296,
      "ROE": 38.3941,
      "ROA": 12.1433,
      "ROIC": 26.3592,
      "MARGEM_EBITDA": 16.7284,
      "MARGEM_LIQUIDA": 13.2811,
      "DIV_LIQ_EBITDA": 0.1542,
      "DIV_LIQ_PL": 0.0686,
      "ICJ": 3.8649,
      "COMPOSICAO_DIVIDA": 17.3257,
      "LIQ_CORRENTE": 3.7016,
      "LIQ_SECA": 3.7016,
      "LIQ_GERAL": 1.3748,
      "GIRO_ATIVO": 0.7521,
      "PME": 0.0,
      "CICLO_CAIXA": 42.2247,
      "NCG_RECEITA": 56.2921
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
