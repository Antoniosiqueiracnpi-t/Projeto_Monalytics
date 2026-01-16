// Arquivo gerado automaticamente por calcular_multiplos.py
(function(){
  window.MONALYTICS = window.MONALYTICS || {};
  window.MONALYTICS.multiplos = window.MONALYTICS.multiplos || {};
  window.MONALYTICS.multiplos["TTEN3"] = {
  "ticker": "TTEN3",
  "ticker_preco": "TTEN3",
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
    "2021": {
      "periodo_referencia": "2021T4",
      "multiplos": {
        "VALOR_MERCADO": 4604899.76,
        "P_L": null,
        "P_VPA": 2.0592,
        "EV_EBITDA": null,
        "EV_EBIT": null,
        "EV_RECEITA": null,
        "DY": 4.0178,
        "PAYOUT": null,
        "ROE": null,
        "ROA": null,
        "ROIC": null,
        "MARGEM_EBITDA": null,
        "MARGEM_LIQUIDA": null,
        "DIV_LIQ_EBITDA": null,
        "DIV_LIQ_PL": -0.1301,
        "ICJ": null,
        "COMPOSICAO_DIVIDA": 61.1312,
        "LIQ_CORRENTE": 1.8317,
        "LIQ_SECA": 1.0527,
        "LIQ_GERAL": 1.6681,
        "GIRO_ATIVO": null,
        "PME": null,
        "CICLO_CAIXA": null,
        "NCG_RECEITA": null
      }
    },
    "2022": {
      "periodo_referencia": "2022T4",
      "multiplos": {
        "VALOR_MERCADO": 4434849.06,
        "P_L": 7.7644,
        "P_VPA": 1.5734,
        "EV_EBITDA": 8.1515,
        "EV_EBIT": 8.652,
        "EV_RECEITA": 0.6756,
        "DY": 4.1893,
        "PAYOUT": 32.5279,
        "ROE": 22.5993,
        "ROA": 10.9028,
        "ROIC": 11.6901,
        "MARGEM_EBITDA": 8.2875,
        "MARGEM_LIQUIDA": 8.2949,
        "DIV_LIQ_EBITDA": 0.3801,
        "DIV_LIQ_PL": 0.077,
        "ICJ": 1.6999,
        "COMPOSICAO_DIVIDA": 54.6629,
        "LIQ_CORRENTE": 1.5542,
        "LIQ_SECA": 0.8131,
        "LIQ_GERAL": 1.3967,
        "GIRO_ATIVO": 1.1322,
        "PME": 125.0845,
        "CICLO_CAIXA": 61.3079,
        "NCG_RECEITA": 17.9792
      }
    },
    "2023": {
      "periodo_referencia": "2023T4",
      "multiplos": {
        "VALOR_MERCADO": 5785235.68,
        "P_L": 10.0823,
        "P_VPA": 1.726,
        "EV_EBITDA": 11.0793,
        "EV_EBIT": 13.2034,
        "EV_RECEITA": 0.6481,
        "DY": 3.2115,
        "PAYOUT": 32.3789,
        "ROE": 18.5984,
        "ROA": 8.851,
        "ROIC": 8.5778,
        "MARGEM_EBITDA": 5.8492,
        "MARGEM_LIQUIDA": 6.3763,
        "DIV_LIQ_EBITDA": 0.0885,
        "DIV_LIQ_PL": 0.0139,
        "ICJ": 1.1167,
        "COMPOSICAO_DIVIDA": 44.1748,
        "LIQ_CORRENTE": 1.5879,
        "LIQ_SECA": 1.0435,
        "LIQ_GERAL": 1.387,
        "GIRO_ATIVO": 1.3073,
        "PME": 70.3942,
        "CICLO_CAIXA": 27.2987,
        "NCG_RECEITA": 10.8174
      }
    },
    "2024": {
      "periodo_referencia": "2024T4",
      "multiplos": {
        "VALOR_MERCADO": 6682171.45,
        "P_L": 8.8346,
        "P_VPA": 1.6517,
        "EV_EBITDA": 4.9391,
        "EV_EBIT": 5.6025,
        "EV_RECEITA": 0.544,
        "DY": 2.7804,
        "PAYOUT": 24.5636,
        "ROE": 20.4489,
        "ROA": 9.5905,
        "ROIC": 18.9362,
        "MARGEM_EBITDA": 11.0134,
        "MARGEM_LIQUIDA": 5.8972,
        "DIV_LIQ_EBITDA": 0.2086,
        "DIV_LIQ_PL": 0.0728,
        "ICJ": 1.2372,
        "COMPOSICAO_DIVIDA": 44.5632,
        "LIQ_CORRENTE": 1.5755,
        "LIQ_SECA": 1.0894,
        "LIQ_GERAL": 1.2735,
        "GIRO_ATIVO": 1.4428,
        "PME": 62.3332,
        "CICLO_CAIXA": 30.5022,
        "NCG_RECEITA": 9.815
      }
    },
    "2025": {
      "periodo_referencia": "2025T3",
      "multiplos": {
        "VALOR_MERCADO": 6891456.46,
        "P_L": 7.9927,
        "P_VPA": 1.4653,
        "EV_EBITDA": 8.9961,
        "EV_EBIT": 11.2876,
        "EV_RECEITA": 0.5542,
        "DY": 2.696,
        "PAYOUT": 21.548,
        "ROE": 19.9833,
        "ROA": 8.2429,
        "ROIC": 7.7774,
        "MARGEM_EBITDA": 6.1605,
        "MARGEM_LIQUIDA": 5.4192,
        "DIV_LIQ_EBITDA": 1.9651,
        "DIV_LIQ_PL": 0.4096,
        "ICJ": 0.9,
        "COMPOSICAO_DIVIDA": 46.9579,
        "LIQ_CORRENTE": 1.4627,
        "LIQ_SECA": 1.004,
        "LIQ_GERAL": 1.0731,
        "GIRO_ATIVO": 1.285,
        "PME": 66.938,
        "CICLO_CAIXA": 38.267,
        "NCG_RECEITA": 14.3036
      }
    }
  },
  "ltm": {
    "periodo_referencia": "2025T3",
    "data_calculo": "2026-01-16T17:17:53.808758",
    "preco_utilizado": 15.56,
    "periodo_preco": "2026T1",
    "acoes_utilizadas": 498297647,
    "periodo_acoes": "2024T4",
    "multiplos": {
      "VALOR_MERCADO": 7753511.39,
      "P_L": 8.9925,
      "P_VPA": 1.6486,
      "EV_EBITDA": 9.8756,
      "EV_EBIT": 12.3911,
      "EV_RECEITA": 0.6084,
      "DY": 2.3962,
      "PAYOUT": 21.548,
      "ROE": 19.9833,
      "ROA": 8.2429,
      "ROIC": 7.7774,
      "MARGEM_EBITDA": 6.1605,
      "MARGEM_LIQUIDA": 5.4192,
      "DIV_LIQ_EBITDA": 1.9651,
      "DIV_LIQ_PL": 0.4096,
      "ICJ": 0.9,
      "COMPOSICAO_DIVIDA": 46.9579,
      "LIQ_CORRENTE": 1.4627,
      "LIQ_SECA": 1.004,
      "LIQ_GERAL": 1.0731,
      "GIRO_ATIVO": 1.285,
      "PME": 66.938,
      "CICLO_CAIXA": 38.267,
      "NCG_RECEITA": 14.3036
    }
  },
  "periodos_disponiveis": [
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
