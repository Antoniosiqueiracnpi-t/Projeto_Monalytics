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
CODIGO_DOLAR_PTAX = 1  # Dólar americano (PTAX) - compra
CODIGO_IPCA_MENSAL = 433  # IPCA mensal


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


def capturar_dolar() -> Optional[Dict]:
    """
    Captura última cotação do Dólar PTAX (compra).
    
    Returns:
        {
            'cotacao': float,  # ex: 6.18
            'formato': str,  # ex: "R$ 6.18"
            'data_referencia': str  # ex: "2025-01-03"
        }
    """
    try:
        # Buscar série do dólar PTAX via SGS
        df = sgs.get(CODIGO_DOLAR_PTAX)
        
        if df is None or len(df) == 0:
            return None
        
        # Último valor disponível
        ultimo_valor = float(df.iloc[-1, 0])
        data_ref = df.index[-1].strftime('%Y-%m-%d')
        
        return {
            'cotacao': round(ultimo_valor, 2),
            'formato': f"R$ {ultimo_valor:.2f}",
            'data_referencia': data_ref
        }
    except Exception as e:
        print(f"⚠️  Erro ao capturar Dólar: {e}")
        return None


# ======================================================================================
# PROCESSAMENTO PRINCIPAL
# ======================================================================================

def processar_indicadores() -> Dict:
    """
    Captura todos os indicadores econômicos.
    
    Returns:
        Dicionário com todos os indicadores
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
    
    print("Capturando Dólar PTAX...", end=" ")
    dolar = capturar_dolar()
    if dolar:
        print(f"✅ {dolar['formato']}")
    else:
        print("⚠️  falha")
    
    print(f"\n{'='*70}\n")
    
    # Montar estrutura final
    return {
        'ultima_atualizacao': datetime.now().isoformat(),
        'indicadores': {
            'selic': selic if selic else {'erro': 'Dados não disponíveis'},
            'cdi': cdi if cdi else {'erro': 'Dados não disponíveis'},
            'ipca': ipca if ipca else {'erro': 'Dados não disponíveis'},
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
        print(f"Selic:        {selic['formato']}")
    else:
        print(f"Selic:        ⚠️  Não disponível")
    
    # CDI
    if 'erro' not in ind.get('cdi', {}):
        cdi = ind['cdi']
        print(f"CDI:          {cdi['formato']}")
    else:
        print(f"CDI:          ⚠️  Não disponível")
    
    # IPCA
    if 'erro' not in ind.get('ipca', {}):
        ipca = ind['ipca']
        print(f"IPCA (mês):   {ipca['formato_mensal']} ({ipca['mes_referencia']})")
        if ipca['formato_acumulado']:
            print(f"IPCA (12m):   {ipca['formato_acumulado']}")
    else:
        print(f"IPCA:         ⚠️  Não disponível")
    
    # Dólar
    if 'erro' not in ind.get('dolar', {}):
        dolar = ind['dolar']
        print(f"Dólar PTAX:   {dolar['formato']} ({dolar['data_referencia']})")
    else:
        print(f"Dólar:        ⚠️  Não disponível")
    
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
