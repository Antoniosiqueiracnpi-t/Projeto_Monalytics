// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["CEAB3"] = {
  "ticker": "CEAB3",
  "ticker_preco": "CEAB3",
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
        "VALOR_MERCADO": 2934493.05,
        "P_L": 16.9003,
        "P_VPA": 2.6317,
        "EV_EBITDA": 3.1616,
        "EV_EBIT": 6.991,
        "EV_RECEITA": 0.482,
        "DY": 5.8758,
        "PAYOUT": 99.3029,
        "ROE": 15.5722,
        "ROA": 4.9919,
        "ROIC": 35.0443,
        "MARGEM_EBITDA": 15.2462,
        "MARGEM_LIQUIDA": 3.3609,
        "DIV_LIQ_EBITDA": -0.5639,
        "DIV_LIQ_PL": -0.3983,
        "ICJ": 1.1242,
        "COMPOSICAO_DIVIDA": 12.4459,
        "LIQ_CORRENTE": 1.2546,
        "LIQ_SECA": 0.9742,
        "LIQ_GERAL": 1.119,
        "GIRO_ATIVO": 1.4853,
        "PME": 67.4843,
        "CICLO_CAIXA": 53.7432,
        "NCG_RECEITA": -0.0053
      }
    },
    "2019": {
      "periodo_referencia": "2019T4",
      "multiplos": {
        "VALOR_MERCADO": 4996652.55,
        "P_L": 5.1406,
        "P_VPA": 1.8239,
        "EV_EBITDA": 2.9647,
        "EV_EBIT": 5.9407,
        "EV_RECEITA": 1.1612,
        "DY": 3.4508,
        "PAYOUT": 17.7394,
        "ROE": 50.4328,
        "ROA": 20.4298,
        "ROIC": 17.5724,
        "MARGEM_EBITDA": 39.1683,
        "MARGEM_LIQUIDA": 18.3909,
        "DIV_LIQ_EBITDA": 0.551,
        "DIV_LIQ_PL": 0.4163,
        "ICJ": 3.4271,
        "COMPOSICAO_DIVIDA": 22.5418,
        "LIQ_CORRENTE": 1.713,
        "LIQ_SECA": 1.4019,
        "LIQ_GERAL": 1.0992,
        "GIRO_ATIVO": 0.8755,
        "PME": 72.1728,
        "CICLO_CAIXA": 44.0778,
        "NCG_RECEITA": 21.9346
      }
    },
    "2020": {
      "periodo_referencia": "2020T4",
      "multiplos": {
        "VALOR_MERCADO": 3643456.7,
        "P_L": -21.9047,
        "P_VPA": 1.3724,
        "EV_EBITDA": 10.5781,
        "EV_EBIT": -20.3701,
        "EV_RECEITA": 0.8189,
        "DY": 4.7325,
        "PAYOUT": -103.6635,
        "ROE": -6.1669,
        "ROA": -2.4925,
        "ROIC": -4.5992,
        "MARGEM_EBITDA": 7.7414,
        "MARGEM_LIQUIDA": -4.0713,
        "DIV_LIQ_EBITDA": -0.9419,
        "DIV_LIQ_PL": -0.1122,
        "ICJ": -0.7274,
        "COMPOSICAO_DIVIDA": 32.2476,
        "LIQ_CORRENTE": 1.5632,
        "LIQ_SECA": 1.2786,
        "LIQ_GERAL": 1.0383,
        "GIRO_ATIVO": 0.5589,
        "PME": 105.4281,
        "CICLO_CAIXA": 8.5649,
        "NCG_RECEITA": 3.6644
      }
    },
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": 1738502.18,
        "P_L": 5.2841,
        "P_VPA": 0.5805,
        "EV_EBITDA": 6.0777,
        "EV_EBIT": 22.2319,
        "EV_RECEITA": 0.4003,
        "DY": 9.918,
        "PAYOUT": 52.4075,
        "ROE": 11.6467,
        "ROA": 4.1172,
        "ROIC": 1.845,
        "MARGEM_EBITDA": 6.5872,
        "MARGEM_LIQUIDA": 6.3846,
        "DIV_LIQ_EBITDA": 0.9562,
        "DIV_LIQ_PL": 0.1084,
        "ICJ": 0.3463,
        "COMPOSICAO_DIVIDA": 8.8141,
        "LIQ_CORRENTE": 1.627,
        "LIQ_SECA": 1.2754,
        "LIQ_GERAL": 0.9195,
        "GIRO_ATIVO": 0.5942,
        "PME": 110.9391,
        "CICLO_CAIXA": 7.9749,
        "NCG_RECEITA": 11.3574
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 647314.64,
        "P_L": 780.8379,
        "P_VPA": 0.2158,
        "EV_EBITDA": 1.1651,
        "EV_EBIT": 4.1589,
        "EV_RECEITA": 0.1804,
        "DY": 26.637,
        "PAYOUT": 20799.2171,
        "ROE": 0.0277,
        "ROA": 0.0091,
        "ROIC": 5.1035,
        "MARGEM_EBITDA": 15.4806,
        "MARGEM_LIQUIDA": 0.0134,
        "DIV_LIQ_EBITDA": 0.4889,
        "DIV_LIQ_PL": 0.156,
        "ICJ": 0.446,
        "COMPOSICAO_DIVIDA": 34.6849,
        "LIQ_CORRENTE": 1.2917,
        "LIQ_SECA": 1.0602,
        "LIQ_GERAL": 0.9318,
        "GIRO_ATIVO": 0.6421,
        "PME": 99.6711,
        "CICLO_CAIXA": -44.0407,
        "NCG_RECEITA": 2.2104
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 2213199.59,
        "P_L": 947.0259,
        "P_VPA": 0.7346,
        "EV_EBITDA": 2.3151,
        "EV_EBIT": 6.4746,
        "EV_RECEITA": 0.3801,
        "DY": 7.7908,
        "PAYOUT": 7378.0706,
        "ROE": 0.0777,
        "ROA": 0.0245,
        "ROIC": 7.7633,
        "MARGEM_EBITDA": 16.4172,
        "MARGEM_LIQUIDA": 0.0348,
        "DIV_LIQ_EBITDA": 0.3088,
        "DIV_LIQ_PL": 0.1131,
        "ICJ": 0.6197,
        "COMPOSICAO_DIVIDA": 30.3004,
        "LIQ_CORRENTE": 1.388,
        "LIQ_SECA": 1.1145,
        "LIQ_GERAL": 0.9721,
        "GIRO_ATIVO": 0.7135,
        "PME": 98.5458,
        "CICLO_CAIXA": 18.8491,
        "NCG_RECEITA": 6.0417
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 2274848.6,
        "P_L": 5.0275,
        "P_VPA": 0.6876,
        "EV_EBITDA": 1.4542,
        "EV_EBIT": 2.719,
        "EV_RECEITA": 0.2881,
        "DY": 7.5796,
        "PAYOUT": 38.1069,
        "ROE": 14.3162,
        "ROA": 4.6476,
        "ROIC": 16.5154,
        "MARGEM_EBITDA": 19.8139,
        "MARGEM_LIQUIDA": 5.9252,
        "DIV_LIQ_EBITDA": -0.0493,
        "DIV_LIQ_PL": -0.0225,
        "ICJ": 1.4239,
        "COMPOSICAO_DIVIDA": 30.4764,
        "LIQ_CORRENTE": 1.2969,
        "LIQ_SECA": 1.0288,
        "LIQ_GERAL": 1.0092,
        "GIRO_ATIVO": 0.7596,
        "PME": 107.4007,
        "CICLO_CAIXA": -37.7739,
        "NCG_RECEITA": 0.3552
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 4851777.37,
        "P_L": 9.1751,
        "P_VPA": 1.3718,
        "EV_EBITDA": 2.8997,
        "EV_EBIT": 4.8834,
        "EV_RECEITA": 0.6102,
        "DY": 3.5539,
        "PAYOUT": 32.6069,
        "ROE": 15.7437,
        "ROA": 5.9769,
        "ROIC": 18.4442,
        "MARGEM_EBITDA": 21.0434,
        "MARGEM_LIQUIDA": 6.5579,
        "DIV_LIQ_EBITDA": 0.0404,
        "DIV_LIQ_PL": 0.0194,
        "ICJ": 1.6944,
        "COMPOSICAO_DIVIDA": 36.299,
        "LIQ_CORRENTE": 1.4991,
        "LIQ_SECA": 1.0857,
        "LIQ_GERAL": 1.0587,
        "GIRO_ATIVO": 0.9042,
        "PME": 116.7012,
        "CICLO_CAIXA": 30.0094,
        "NCG_RECEITA": 8.5364
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-16T20:56:53.827025",
    "preco_utilizado": 9.52,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 308245068,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 2934493.05,
      "P_L": 5.5493,
      "P_VPA": 0.8297,
      "EV_EBITDA": 1.7698,
      "EV_EBIT": 2.9805,
      "EV_RECEITA": 0.3724,
      "DY": 5.8758,
      "PAYOUT": 32.6069,
      "ROE": 15.7437,
      "ROA": 5.9769,
      "ROIC": 18.4442,
      "MARGEM_EBITDA": 21.0434,
      "MARGEM_LIQUIDA": 6.5579,
      "DIV_LIQ_EBITDA": 0.0404,
      "DIV_LIQ_PL": 0.0194,
      "ICJ": 1.6944,
      "COMPOSICAO_DIVIDA": 36.299,
      "LIQ_CORRENTE": 1.4991,
      "LIQ_SECA": 1.0857,
      "LIQ_GERAL": 1.0587,
      "GIRO_ATIVO": 0.9042,
      "PME": 116.7012,
      "CICLO_CAIXA": 30.0094,
      "NCG_RECEITA": 8.5364
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
