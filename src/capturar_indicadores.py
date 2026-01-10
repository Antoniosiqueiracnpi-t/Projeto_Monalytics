"""
CAPTURADOR DE INDICADORES ECONÔMICOS
====================================
Janeiro 2025

Captura e atualiza indicadores econômicos brasileiros:
- Selic (taxa anualizada)
- CDI (taxa anualizada)
- IPCA (mensal e acumulado 12 meses)
- Dólar PTAX (última cotação)

SAÍDA: balancos/INDICADORES/indicadores_economicos.json

EXECUÇÃO:
python src/capturar_indicadores.py
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

try:
    import finbr
    from finbr import sgs
    HAS_FINBR = True
except ImportError:
    HAS_FINBR = False
    print("❌ finbr não instalado: pip install finbr")


# ======================================================================================
# CONFIGURAÇÃO
# ======================================================================================

OUTPUT_DIR = Path("balancos") / "INDICADORES"
OUTPUT_FILE = "indicadores_economicos.json"

# Códigos SGS do Banco Central
CODIGO_DOLAR_PTAX_COMPRA = 1      # Dólar PTAX - compra (BCB-Ptax)
CODIGO_DOLAR_PTAX_VENDA = 10813   # Dólar PTAX - venda
CODIGO_EURO_PTAX = 21619          # Euro PTAX - compra (opcional)
CODIGO_IPCA_MENSAL = 433          # IPCA mensal
CODIGO_IGPM_MENSAL = 189          # IGP-M mensal (FGV)
CODIGO_IGPM_ACUM_12M = 190        # IGP-M acumulado 12 meses


# ======================================================================================
# CAPTURA DE INDICADORES
# ======================================================================================

def capturar_selic() -> Optional[Dict]:
    """
    Captura taxa Selic anualizada.
    
    Returns:
        {
            'taxa_anual': float,  # ex: 14.25
            'taxa_decimal': float,  # ex: 0.1425
            'formato': str  # ex: "14.25%"
        }
    """
    try:
        taxa_decimal = finbr.selic()  # Retorna ex: 0.1425
        
        if taxa_decimal is None:
            return None
        
        taxa_pct = taxa_decimal * 100
        
        return {
            'taxa_anual': round(taxa_pct, 2),
            'taxa_decimal': round(taxa_decimal, 4),
            'formato': f"{taxa_pct:.2f}%"
        }
    except Exception as e:
        print(f"⚠️  Erro ao capturar Selic: {e}")
        return None


def capturar_cdi() -> Optional[Dict]:
    """
    Captura taxa CDI anualizada.
    
    Returns:
        {
            'taxa_anual': float,  # ex: 14.15
            'taxa_decimal': float,  # ex: 0.1415
            'formato': str  # ex: "14.15%"
        }
    """
    try:
        taxa_decimal = finbr.cdi()  # Retorna ex: 0.1415
        
        if taxa_decimal is None:
            return None
        
        taxa_pct = taxa_decimal * 100
        
        return {
            'taxa_anual': round(taxa_pct, 2),
            'taxa_decimal': round(taxa_decimal, 4),
            'formato': f"{taxa_pct:.2f}%"
        }
    except Exception as e:
        print(f"⚠️  Erro ao capturar CDI: {e}")
        return None


def capturar_ipca() -> Optional[Dict]:
    """
    Captura IPCA mensal e acumulado 12 meses.
    
    Returns:
        {
            'taxa_mensal': float,  # ex: 0.52 (0.52%)
            'taxa_acumulada_12m': float,  # ex: 4.83 (4.83%)
            'mes_referencia': str,  # ex: "2024-12"
            'formato_mensal': str,  # ex: "0.52%"
            'formato_acumulado': str  # ex: "4.83%"
        }
    """
    try:
        # finbr.ipca() retorna DataFrame com coluna 'ipca' e índice de datas
        df = finbr.ipca()
        
        if df is None or len(df) == 0:
            return None
        
        # Última taxa mensal disponível
        ultimo_valor = df['ipca'].iloc[-1]
        taxa_mensal_pct = ultimo_valor * 100
        
        # Data de referência do último dado
        data_ref = df.index[-1].strftime('%Y-%m')
        
        # Calcular acumulado 12 meses
        if len(df) >= 12:
            ultimos_12 = df['ipca'].iloc[-12:]
            # Fórmula do acumulado: produto de (1 + taxa) - 1
            acumulado = 1
            for taxa in ultimos_12:
                acumulado *= (1 + taxa)
            taxa_acum_12m_pct = (acumulado - 1) * 100
        else:
            taxa_acum_12m_pct = None
        
        return {
            'taxa_mensal': round(taxa_mensal_pct, 2),
            'taxa_acumulada_12m': round(taxa_acum_12m_pct, 2) if taxa_acum_12m_pct else None,
            'mes_referencia': data_ref,
            'formato_mensal': f"{taxa_mensal_pct:.2f}%",
            'formato_acumulado': f"{taxa_acum_12m_pct:.2f}%" if taxa_acum_12m_pct else None
        }
    except Exception as e:
        print(f"⚠️  Erro ao capturar IPCA: {e}")
        return None


def capturar_igpm() -> Optional[Dict]:
    """
    Captura IGP-M mensal e acumulado 12 meses.
    
    IGP-M = Índice Geral de Preços do Mercado (FGV)
    Usado em contratos de aluguel, energia, etc.
    
    Returns:
        {
            'taxa_mensal': float,
            'taxa_acumulada_12m': float,
            'mes_referencia': str,
            'formato_mensal': str,
            'formato_acumulado': str
        }
    """
    try:
        # Capturar IGP-M mensal
        df_mensal = sgs.get(CODIGO_IGPM_MENSAL)
        
        if df_mensal is None or len(df_mensal) == 0:
            return None
        
        # Última taxa mensal disponível
        ultimo_valor_mensal = float(df_mensal.iloc[-1, 0])
        data_ref = df_mensal.index[-1].strftime('%Y-%m')
        
        # Capturar IGP-M acumulado 12 meses (se disponível)
        taxa_acum_12m = None
        try:
            df_acum = sgs.get(CODIGO_IGPM_ACUM_12M)
            if df_acum is not None and len(df_acum) > 0:
                taxa_acum_12m = float(df_acum.iloc[-1, 0])
        except:
            # Se falhar, calcular manualmente
            if len(df_mensal) >= 12:
                ultimos_12 = df_mensal.iloc[-12:, 0]
                acumulado = 1
                for taxa in ultimos_12:
                    acumulado *= (1 + taxa / 100)
                taxa_acum_12m = (acumulado - 1) * 100
        
        return {
            'taxa_mensal': round(ultimo_valor_mensal, 2),
            'taxa_acumulada_12m': round(taxa_acum_12m, 2) if taxa_acum_12m else None,
            'mes_referencia': data_ref,
            'formato_mensal': f"{ultimo_valor_mensal:.2f}%",
            'formato_acumulado': f"{taxa_acum_12m:.2f}%" if taxa_acum_12m else None
        }
    except Exception as e:
        print(f"⚠️  Erro ao capturar IGP-M: {e}")
        return None


def capturar_dolar() -> Optional[Dict]:
    """
    Captura cotações do Dólar PTAX (compra e venda).
    
    FALLBACK: Se SGS falhar, tenta scraping alternativo
    
    Returns:
        {
            'cotacao_compra': float,
            'cotacao_venda': float,
            'spread': float,
            'formato_compra': str,
            'formato_venda': str,
            'data_referencia': str,
            'fonte': str  # 'BCB-SGS' ou 'BCB-Alternativo'
        }
    """
    try:
        # ========== TENTATIVA 1: SGS Compra ==========
        df_compra = None
        cotacao_compra = None
        data_ref = None
        
        try:
            df_compra = sgs.get(CODIGO_DOLAR_PTAX_COMPRA)
            if df_compra is not None and len(df_compra) > 0:
                cotacao_compra = float(df_compra.iloc[-1, 0])
                data_ref = df_compra.index[-1].strftime('%Y-%m-%d')
        except Exception as e:
            print(f"    ⚠️  SGS compra falhou: {e}")
        
        # ========== FALLBACK: Se SGS falhar, usar finbr direto ==========
        if cotacao_compra is None:
            try:
                # finbr tem função específica para dólar
                import finbr
                df_dolar = finbr.get_series('USDBRL')  # Bloomberg ticker
                if df_dolar is not None and len(df_dolar) > 0:
                    cotacao_compra = float(df_dolar.iloc[-1])
                    data_ref = df_dolar.index[-1].strftime('%Y-%m-%d')
                    print(f"    ✅ Usando fonte alternativa finbr")
            except:
                pass
        
        # ========== Se ainda falhou, tentar API do BCB direto ==========
        if cotacao_compra is None:
            try:
                import requests
                url = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao='01-09-2026'&$format=json"
                # Ajustar data dinamicamente
                from datetime import datetime, timedelta
                hoje = datetime.now()
                for i in range(7):  # Tentar últimos 7 dias
                    data_teste = (hoje - timedelta(days=i)).strftime('%m-%d-%Y')
                    url_teste = f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao='{data_teste}'&$format=json"
                    resp = requests.get(url_teste, timeout=5)
                    if resp.status_code == 200:
                        dados = resp.json()
                        if 'value' in dados and len(dados['value']) > 0:
                            cotacao_compra = float(dados['value'][0]['cotacaoCompra'])
                            data_ref = dados['value'][0]['dataHoraCotacao'][:10]
                            print(f"    ✅ Usando API BCB direto")
                            break
            except:
                pass
        
        if cotacao_compra is None:
            return None
        
        # ========== TENTATIVA 2: SGS Venda ==========
        cotacao_venda = None
        try:
            df_venda = sgs.get(CODIGO_DOLAR_PTAX_VENDA)
            if df_venda is not None and len(df_venda) > 0:
                cotacao_venda = float(df_venda.iloc[-1, 0])
        except:
            pass
        
        # ========== Montar resultado ==========
        resultado = {
            'cotacao_compra': round(cotacao_compra, 4),
            'formato_compra': f"R$ {cotacao_compra:.4f}",
            'data_referencia': data_ref,
            'fonte': 'BCB-SGS' if df_compra is not None else 'BCB-Alternativo'
        }
        
        if cotacao_venda:
            spread = cotacao_venda - cotacao_compra
            resultado.update({
                'cotacao_venda': round(cotacao_venda, 4),
                'formato_venda': f"R$ {cotacao_venda:.4f}",
                'spread': round(spread, 4),
                'spread_pct': round((spread / cotacao_compra) * 100, 2),
                'formato_spread': f"R$ {spread:.4f} ({(spread/cotacao_compra)*100:.2f}%)"
            })
        
        return resultado
        
    except Exception as e:
        print(f"⚠️  Erro ao capturar Dólar: {e}")
        import traceback
        traceback.print_exc()
        return None


# ======================================================================================
# PROCESSAMENTO PRINCIPAL
# ======================================================================================

def processar_indicadores() -> Dict:
    """
    Captura todos os indicadores econômicos.
    """
    print(f"\n{'='*70}")
    print(f"📊 CAPTURANDO INDICADORES ECONÔMICOS")
    print(f"{'='*70}\n")
    
    # Capturar cada indicador
    print("Capturando Selic...", end=" ")
    selic = capturar_selic()
    if selic:
        print(f"✅ {selic['formato']}")
    else:
        print("⚠️  falha")
    
    print("Capturando CDI...", end=" ")
    cdi = capturar_cdi()
    if cdi:
        print(f"✅ {cdi['formato']}")
    else:
        print("⚠️  falha")
    
    print("Capturando IPCA...", end=" ")
    ipca = capturar_ipca()
    if ipca:
        print(f"✅ {ipca['formato_mensal']} (mês) | {ipca['formato_acumulado']} (12m)")
    else:
        print("⚠️  falha")
    
    # ✅ NOVO: IGP-M
    print("Capturando IGP-M...", end=" ")
    igpm = capturar_igpm()
    if igpm:
        print(f"✅ {igpm['formato_mensal']} (mês) | {igpm['formato_acumulado']} (12m)")
    else:
        print("⚠️  falha")
    
    print("Capturando Dólar PTAX...", end=" ")
    dolar = capturar_dolar()
    if dolar:
        venda_info = f" | {dolar.get('formato_venda', 'N/A')} (venda)" if 'cotacao_venda' in dolar else ""
        print(f"✅ {dolar['formato_compra']} (compra){venda_info}")
    else:
        print("⚠️  falha")
    
    print(f"\n{'='*70}\n")
    
    # Montar estrutura final
    from datetime import datetime, timezone
    
    return {
        'ultima_atualizacao': datetime.now(timezone.utc).isoformat(),  # ✅ Com timezone
        'indicadores': {
            'selic': selic if selic else {'erro': 'Dados não disponíveis'},
            'cdi': cdi if cdi else {'erro': 'Dados não disponíveis'},
            'ipca': ipca if ipca else {'erro': 'Dados não disponíveis'},
            'igpm': igpm if igpm else {'erro': 'Dados não disponíveis'},  # ✅ NOVO
            'dolar': dolar if dolar else {'erro': 'Dados não disponíveis'}
        }
    }


# ======================================================================================
# SALVAMENTO
# ======================================================================================

def salvar_resultado(dados: Dict) -> bool:
    """Salva resultado em JSON."""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        arquivo = OUTPUT_DIR / OUTPUT_FILE
        
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Arquivo salvo: {arquivo}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")
        return False


# ======================================================================================
# EXIBIÇÃO DE RESULTADOS
# ======================================================================================

def exibir_resumo(dados: Dict):
    """Exibe resumo dos indicadores."""
    ind = dados.get('indicadores', {})
    
    print(f"\n{'='*70}")
    print(f"📈 RESUMO DOS INDICADORES ECONÔMICOS")
    print(f"{'='*70}")
    
    # Selic
    if 'erro' not in ind.get('selic', {}):
        selic = ind['selic']
        print(f"Selic:         {selic['formato']}")
    else:
        print(f"Selic:         ⚠️  Não disponível")
    
    # CDI
    if 'erro' not in ind.get('cdi', {}):
        cdi = ind['cdi']
        print(f"CDI:           {cdi['formato']}")
    else:
        print(f"CDI:           ⚠️  Não disponível")
    
    # IPCA
    if 'erro' not in ind.get('ipca', {}):
        ipca = ind['ipca']
        print(f"IPCA (mês):    {ipca['formato_mensal']} ({ipca['mes_referencia']})")
        if ipca['formato_acumulado']:
            print(f"IPCA (12m):    {ipca['formato_acumulado']}")
    else:
        print(f"IPCA:          ⚠️  Não disponível")
    
    # ✅ NOVO: IGP-M
    if 'erro' not in ind.get('igpm', {}):
        igpm = ind['igpm']
        print(f"IGP-M (mês):   {igpm['formato_mensal']} ({igpm['mes_referencia']})")
        if igpm['formato_acumulado']:
            print(f"IGP-M (12m):   {igpm['formato_acumulado']}")
    else:
        print(f"IGP-M:         ⚠️  Não disponível")
    
    # Dólar
    if 'erro' not in ind.get('dolar', {}):
        dolar = ind['dolar']
        print(f"Dólar PTAX:    {dolar['formato_compra']} (compra)")
        if 'formato_venda' in dolar:
            print(f"               {dolar['formato_venda']} (venda)")
            if 'formato_spread' in dolar:
                print(f"               Spread: {dolar['formato_spread']}")
        print(f"               Data: {dolar['data_referencia']} | Fonte: {dolar.get('fonte', 'N/A')}")
    else:
        print(f"Dólar:         ⚠️  Não disponível")
    
    print(f"{'='*70}\n")


# ======================================================================================
# MAIN
# ======================================================================================

def main():
    if not HAS_FINBR:
        print("❌ Instale finbr: pip install finbr")
        return
    
    # Processar
    resultado = processar_indicadores()
    
    # Exibir
    exibir_resumo(resultado)
    
    # Salvar
    salvar_resultado(resultado)


if __name__ == "__main__":
    main()
