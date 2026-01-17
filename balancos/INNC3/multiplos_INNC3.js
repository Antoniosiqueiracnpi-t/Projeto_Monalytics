// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["INNC3"] = {
  "ticker": "INNC3",
  "ticker_preco": "INNC3",
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
    "2017": {
      "periodo_referencia": "2017T4",
      "multiplos": {
        "VALOR_MERCADO": null,
        "P_L": null,
        "P_VPA": null,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": null,
        "ROA": null,
        "ROIC": null,
        "MARGEM_EBITDA": null,
        "MARGEM_LIQUIDA": null,
        "DIV_LIQ_EBITDA": null,
        "DIV_LIQ_PL": 1.1865,
        "ICJ": null,
        "COMPOSICAO_DIVIDA": 5.4547,
        "LIQ_CORRENTE": 2.6517,
        "LIQ_SECA": 1.7529,
        "LIQ_GERAL": 0.8268,
        "GIRO_ATIVO": null,
        "PME": null,
        "CICLO_CAIXA": null,
        "NCG_RECEITA": null
      }
    },
    "2018": {
      "periodo_referencia": "2018T4",
      "multiplos": {
        "VALOR_MERCADO": null,
        "P_L": null,
        "P_VPA": null,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 309.571,
        "ROA": 20.1265,
        "ROIC": 84.1302,
        "MARGEM_EBITDA": 28.1166,
        "MARGEM_LIQUIDA": 24.3831,
        "DIV_LIQ_EBITDA": 0.3257,
        "DIV_LIQ_PL": 0.7588,
        "ICJ": 4.2603,
        "COMPOSICAO_DIVIDA": 10.8495,
        "LIQ_CORRENTE": 1.747,
        "LIQ_SECA": 1.1193,
        "LIQ_GERAL": 1.0062,
        "GIRO_ATIVO": 0.4909,
        "PME": 204.5012,
        "CICLO_CAIXA": 184.1527,
        "NCG_RECEITA": 5.302
      }
    },
    "2019": {
      "periodo_referencia": "2019T4",
      "multiplos": {
        "VALOR_MERCADO": null,
        "P_L": null,
        "P_VPA": null,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 123.8517,
        "ROA": 8.6989,
        "ROIC": 20.5445,
        "MARGEM_EBITDA": 18.9289,
        "MARGEM_LIQUIDA": 16.5704,
        "DIV_LIQ_EBITDA": 2.087,
        "DIV_LIQ_PL": 2.1439,
        "ICJ": 3.786,
        "COMPOSICAO_DIVIDA": 42.4977,
        "LIQ_CORRENTE": 2.1765,
        "LIQ_SECA": 0.868,
        "LIQ_GERAL": 1.0386,
        "GIRO_ATIVO": 0.4161,
        "PME": 392.8912,
        "CICLO_CAIXA": 412.9245,
        "NCG_RECEITA": 64.7997
      }
    },
    "2020": {
      "periodo_referencia": "2020T4",
      "multiplos": {
        "VALOR_MERCADO": null,
        "P_L": null,
        "P_VPA": null,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": -80.2948,
        "ROA": -5.3542,
        "ROIC": -8.926,
        "MARGEM_EBITDA": -10.4453,
        "MARGEM_LIQUIDA": -17.8755,
        "DIV_LIQ_EBITDA": -6.0028,
        "DIV_LIQ_PL": 2.9294,
        "ICJ": -2.0338,
        "COMPOSICAO_DIVIDA": 81.69,
        "LIQ_CORRENTE": 1.2522,
        "LIQ_SECA": 0.4806,
        "LIQ_GERAL": 0.9429,
        "GIRO_ATIVO": 0.2731,
        "PME": 491.0726,
        "CICLO_CAIXA": 510.023,
        "NCG_RECEITA": 80.2149
      }
    },
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": null,
        "P_L": null,
        "P_VPA": null,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 24.5349,
        "ROA": 1.8975,
        "ROIC": 9.3149,
        "MARGEM_EBITDA": 8.1511,
        "MARGEM_LIQUIDA": 3.4985,
        "DIV_LIQ_EBITDA": 4.5339,
        "DIV_LIQ_PL": 2.0977,
        "ICJ": 1.7601,
        "COMPOSICAO_DIVIDA": 55.0285,
        "LIQ_CORRENTE": 1.3553,
        "LIQ_SECA": 0.4378,
        "LIQ_GERAL": 0.9129,
        "GIRO_ATIVO": 0.5486,
        "PME": 251.3759,
        "CICLO_CAIXA": 258.253,
        "NCG_RECEITA": 36.7908
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": null,
        "P_L": null,
        "P_VPA": null,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 59.1045,
        "ROA": 6.778,
        "ROIC": 14.8123,
        "MARGEM_EBITDA": 16.6823,
        "MARGEM_LIQUIDA": 13.8203,
        "DIV_LIQ_EBITDA": 2.5411,
        "DIV_LIQ_PL": 1.4139,
        "ICJ": 3.8153,
        "COMPOSICAO_DIVIDA": 60.8364,
        "LIQ_CORRENTE": 0.8782,
        "LIQ_SECA": 0.3633,
        "LIQ_GERAL": 0.9481,
        "GIRO_ATIVO": 0.4271,
        "PME": 223.7971,
        "CICLO_CAIXA": 209.4655,
        "NCG_RECEITA": 10.7958
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": null,
        "P_L": null,
        "P_VPA": null,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 29.5352,
        "ROA": 4.4198,
        "ROIC": 10.738,
        "MARGEM_EBITDA": 15.4939,
        "MARGEM_LIQUIDA": 9.4655,
        "DIV_LIQ_EBITDA": 3.4791,
        "DIV_LIQ_PL": 1.5133,
        "ICJ": 2.3914,
        "COMPOSICAO_DIVIDA": 52.3246,
        "LIQ_CORRENTE": 0.8843,
        "LIQ_SECA": 0.3811,
        "LIQ_GERAL": 1.0747,
        "GIRO_ATIVO": 0.4856,
        "PME": 269.8949,
        "CICLO_CAIXA": 306.6027,
        "NCG_RECEITA": 13.763
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": null,
        "P_L": null,
        "P_VPA": null,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 29.9644,
        "ROA": 5.0996,
        "ROIC": 9.6929,
        "MARGEM_EBITDA": 16.8322,
        "MARGEM_LIQUIDA": 12.6552,
        "DIV_LIQ_EBITDA": 3.8604,
        "DIV_LIQ_PL": 1.3823,
        "ICJ": 2.447,
        "COMPOSICAO_DIVIDA": 58.244,
        "LIQ_CORRENTE": 0.6899,
        "LIQ_SECA": 0.2151,
        "LIQ_GERAL": 1.1106,
        "GIRO_ATIVO": 0.3575,
        "PME": 408.0039,
        "CICLO_CAIXA": 417.3895,
        "NCG_RECEITA": -19.1661
      }
    },
    "2025": {
      "periodo_referencia": "2025T2",
      "multiplos": {
        "VALOR_MERCADO": null,
        "P_L": null,
        "P_VPA": null,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 0.0,
        "PAYOUT": 0.0,
        "ROE": 29.2846,
        "ROA": 4.9843,
        "ROIC": 11.0051,
        "MARGEM_EBITDA": 18.4696,
        "MARGEM_LIQUIDA": 11.7864,
        "DIV_LIQ_EBITDA": 3.405,
        "DIV_LIQ_PL": 1.3704,
        "ICJ": 1.9153,
        "COMPOSICAO_DIVIDA": 44.8922,
        "LIQ_CORRENTE": 1.389,
        "LIQ_SECA": 0.5094,
        "LIQ_GERAL": 1.1208,
        "GIRO_ATIVO": 0.3691,
        "PME": 416.484,
        "CICLO_CAIXA": 479.7289,
        "NCG_RECEITA": 60.4946
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T2",
    "data_calculo": "2026-01-17T10:32:16.554269",
    "preco_utilizado": null,
    "periodo_preco": "",
    "acoes_utilizadas": 86885350,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": null,
      "P_L": null,
      "P_VPA": null,
      "EV_EBITDA": null,
      "EV_EBIT": null,
      "EV_RECEITA": null,
      "DY": 0.0,
      "PAYOUT": 0.0,
      "ROE": 29.2846,
      "ROA": 4.9843,
      "ROIC": 11.0051,
      "MARGEM_EBITDA": 18.4696,
      "MARGEM_LIQUIDA": 11.7864,
      "DIV_LIQ_EBITDA": 3.405,
      "DIV_LIQ_PL": 1.3704,
      "ICJ": 1.9153,
      "COMPOSICAO_DIVIDA": 44.8922,
      "LIQ_CORRENTE": 1.389,
      "LIQ_SECA": 0.5094,
      "LIQ_GERAL": 1.1208,
      "GIRO_ATIVO": 0.3691,
      "PME": 416.484,
      "CICLO_CAIXA": 479.7289,
      "NCG_RECEITA": 60.4946
    }
  },
  "periodos_disponiveis": [
    "2017T3",
    "2017T4",
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
    "2025T2"
  ],
  "erros": []
};
})();
