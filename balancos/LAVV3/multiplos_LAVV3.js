// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["LAVV3"] = {
  "ticker": "LAVV3",
  "ticker_preco": "LAVV3",
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
        "VALOR_MERCADO": 3487715.6,
        "P_L": 70.1627,
        "P_VPA": 30.1909,
        "EV_EBITDA": 65.8329,
        "EV_EBIT": 65.8329,
        "EV_RECEITA": 17.943,
        "DY": 12.7064,
        "PAYOUT": 891.5152,
        "ROE": 43.0299,
        "ROA": 13.5864,
        "ROIC": 33.1289,
        "MARGEM_EBITDA": 27.2554,
        "MARGEM_LIQUIDA": 25.6491,
        "DIV_LIQ_EBITDA": -0.1948,
        "DIV_LIQ_PL": -0.0891,
        "ICJ": 50.6443,
        "COMPOSICAO_DIVIDA": 8.7732,
        "LIQ_CORRENTE": 2.5813,
        "LIQ_SECA": 1.2311,
        "LIQ_GERAL": 1.3703,
        "GIRO_ATIVO": 0.5297,
        "PME": 405.5769,
        "CICLO_CAIXA": 508.739,
        "NCG_RECEITA": 53.0758
      }
    },
    "2020": {
      "periodo_referencia": "2020T4",
      "multiplos": {
        "VALOR_MERCADO": 1152555.86,
        "P_L": 9.699,
        "P_VPA": 0.8863,
        "EV_EBITDA": 2.4369,
        "EV_EBIT": 2.4369,
        "EV_RECEITA": 0.8055,
        "DY": 38.4505,
        "PAYOUT": 372.9326,
        "ROE": 16.7858,
        "ROA": 11.539,
        "ROIC": 17.9324,
        "MARGEM_EBITDA": 33.0553,
        "MARGEM_LIQUIDA": 33.0542,
        "DIV_LIQ_EBITDA": -7.2618,
        "DIV_LIQ_PL": -0.6636,
        "ICJ": 44.6416,
        "COMPOSICAO_DIVIDA": 5.3867,
        "LIQ_CORRENTE": 4.7709,
        "LIQ_SECA": 3.8735,
        "LIQ_GERAL": 4.2713,
        "GIRO_ATIVO": 0.2122,
        "PME": 451.5243,
        "CICLO_CAIXA": 651.2865,
        "NCG_RECEITA": 51.9083
      }
    },
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": 695358.78,
        "P_L": 3.4036,
        "P_VPA": 0.5563,
        "EV_EBITDA": 1.3088,
        "EV_EBIT": 1.3088,
        "EV_RECEITA": 0.3793,
        "DY": 61.8201,
        "PAYOUT": 210.4108,
        "ROE": 16.0217,
        "ROA": 11.8613,
        "ROIC": 14.8317,
        "MARGEM_EBITDA": 28.9794,
        "MARGEM_LIQUIDA": 33.5321,
        "DIV_LIQ_EBITDA": -2.6295,
        "DIV_LIQ_PL": -0.3714,
        "ICJ": 57.3815,
        "COMPOSICAO_DIVIDA": 16.4656,
        "LIQ_CORRENTE": 3.1746,
        "LIQ_SECA": 2.0752,
        "LIQ_GERAL": 3.4547,
        "GIRO_ATIVO": 0.3479,
        "PME": 399.7423,
        "CICLO_CAIXA": 547.9521,
        "NCG_RECEITA": 51.5441
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 716177.91,
        "P_L": 5.4708,
        "P_VPA": 0.5702,
        "EV_EBITDA": 3.836,
        "EV_EBIT": 3.836,
        "EV_RECEITA": 0.5977,
        "DY": 60.023,
        "PAYOUT": 328.3767,
        "ROE": 10.4475,
        "ROA": 7.1151,
        "ROIC": 6.5504,
        "MARGEM_EBITDA": 15.5804,
        "MARGEM_LIQUIDA": 23.5731,
        "DIV_LIQ_EBITDA": -4.4414,
        "DIV_LIQ_PL": -0.3059,
        "ICJ": 25.9281,
        "COMPOSICAO_DIVIDA": 2.0238,
        "LIQ_CORRENTE": 4.5328,
        "LIQ_SECA": 2.1786,
        "LIQ_GERAL": 2.7868,
        "GIRO_ATIVO": 0.2879,
        "PME": 768.7821,
        "CICLO_CAIXA": 940.1723,
        "NCG_RECEITA": 135.8627
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 1394745.12,
        "P_L": 5.6555,
        "P_VPA": 0.986,
        "EV_EBITDA": 5.6181,
        "EV_EBIT": 5.6181,
        "EV_RECEITA": 1.369,
        "DY": 29.5392,
        "PAYOUT": 167.058,
        "ROE": 18.4693,
        "ROA": 11.894,
        "ROIC": 11.5628,
        "MARGEM_EBITDA": 24.3684,
        "MARGEM_LIQUIDA": 27.301,
        "DIV_LIQ_EBITDA": -0.7179,
        "DIV_LIQ_PL": -0.1117,
        "ICJ": 26.4768,
        "COMPOSICAO_DIVIDA": 11.4993,
        "LIQ_CORRENTE": 4.9256,
        "LIQ_SECA": 2.5488,
        "LIQ_GERAL": 2.6116,
        "GIRO_ATIVO": 0.4072,
        "PME": 499.8653,
        "CICLO_CAIXA": 692.1147,
        "NCG_RECEITA": 114.5814
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 1252734.2,
        "P_L": 3.192,
        "P_VPA": 0.7195,
        "EV_EBITDA": 2.8513,
        "EV_EBIT": 2.8513,
        "EV_RECEITA": 0.7306,
        "DY": 32.212,
        "PAYOUT": 102.822,
        "ROE": 24.8734,
        "ROA": 13.8282,
        "ROIC": 16.1703,
        "MARGEM_EBITDA": 25.6221,
        "MARGEM_LIQUIDA": 25.3312,
        "DIV_LIQ_EBITDA": -0.3045,
        "DIV_LIQ_PL": -0.0694,
        "ICJ": 14.3869,
        "COMPOSICAO_DIVIDA": 3.374,
        "LIQ_CORRENTE": 4.9257,
        "LIQ_SECA": 3.15,
        "LIQ_GERAL": 1.9204,
        "GIRO_ATIVO": 0.448,
        "PME": 333.3767,
        "CICLO_CAIXA": 513.0616,
        "NCG_RECEITA": 86.9241
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 2671587.59,
        "P_L": 5.3589,
        "P_VPA": 1.4751,
        "EV_EBITDA": 5.4344,
        "EV_EBIT": 5.4344,
        "EV_RECEITA": 1.5244,
        "DY": 15.1045,
        "PAYOUT": 80.9431,
        "ROE": 28.9677,
        "ROA": 14.7975,
        "ROIC": 17.6636,
        "MARGEM_EBITDA": 28.0516,
        "MARGEM_LIQUIDA": 27.5939,
        "DIV_LIQ_EBITDA": 0.163,
        "DIV_LIQ_PL": 0.0456,
        "ICJ": 7.2236,
        "COMPOSICAO_DIVIDA": 19.0746,
        "LIQ_CORRENTE": 3.5245,
        "LIQ_SECA": 2.2116,
        "LIQ_GERAL": 1.7606,
        "GIRO_ATIVO": 0.4499,
        "PME": 359.2818,
        "CICLO_CAIXA": 553.8443,
        "NCG_RECEITA": 88.2793
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-17T10:32:17.978170",
    "preco_utilizado": 16.25,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 195434352,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 3175808.22,
      "P_L": 6.3703,
      "P_VPA": 1.7535,
      "EV_EBITDA": 6.4293,
      "EV_EBIT": 6.4293,
      "EV_RECEITA": 1.8035,
      "DY": 12.7064,
      "PAYOUT": 80.9431,
      "ROE": 28.9677,
      "ROA": 14.7975,
      "ROIC": 17.6636,
      "MARGEM_EBITDA": 28.0516,
      "MARGEM_LIQUIDA": 27.5939,
      "DIV_LIQ_EBITDA": 0.163,
      "DIV_LIQ_PL": 0.0456,
      "ICJ": 7.2236,
      "COMPOSICAO_DIVIDA": 19.0746,
      "LIQ_CORRENTE": 3.5245,
      "LIQ_SECA": 2.2116,
      "LIQ_GERAL": 1.7606,
      "GIRO_ATIVO": 0.4499,
      "PME": 359.2818,
      "CICLO_CAIXA": 553.8443,
      "NCG_RECEITA": 88.2793
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
