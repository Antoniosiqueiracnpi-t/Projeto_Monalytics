#!/usr/bin/env python3
"""
Script para corrigir unidades monetárias nos arquivos multiplos*.js
Garante que múltiplos de valor monetário tenham unidade: "R$"
"""

import os
import re
import json
from pathlib import Path

# Múltiplos que devem ter unidade monetária "R$"
MULTIPLOS_MONETARIOS = {
    "VALORMERCADO",
    "PATRIMONIOLIQUIDO", 
    "ATIVOTOTAL",
    "DIVIDA",
    "DIVIDABRUTA",
    "DIVIDALIQUIDA",
    "RECEITALIQUIDA",
    "LUCROLIQUIDO",
    "EBIT",
    "EBITDA",
    "CAIXALIQUIDO"
}

def extrair_metadata_js(conteudo):
    """Extrai o bloco metadata de um arquivo .js"""
    padrao = r'metadata\s*:\s*({[^}]+(?:{[^}]*}[^}]*)*})'
    match = re.search(padrao, conteudo, re.DOTALL)
    if match:
        return match.group(1), match.start(1), match.end(1)
    return None, None, None

def corrigir_metadata(metadata_str):
    """Adiciona unidade "R$" aos múltiplos monetários"""
    linhas = metadata_str.split('\n')
    corrigido = []
    multiplo_atual = None
    
    for linha in linhas:
        # Detecta início de novo múltiplo
        match = re.match(r'\s*"([A-Z]+)"\s*:\s*{', linha)
        if match:
            multiplo_atual = match.group(1)
        
        # Se é um múltiplo monetário e não tem unidade, adiciona
        if multiplo_atual in MULTIPLOS_MONETARIOS:
            # Verifica se já existe linha de unidade
            if 'unidade:' not in linha and 'unidade :' not in linha:
                # Se é a linha do nome, adiciona unidade logo após
                if 'nome:' in linha:
                    corrigido.append(linha)
                    # Extrai indentação
                    indent = re.match(r'(\s*)', linha).group(1)
                    corrigido.append(f'{indent}unidade: "R$",')
                    continue
        
        corrigido.append(linha)
    
    return '\n'.join(corrigido)

def processar_arquivo(caminho):
    """Processa um arquivo multiplos*.js"""
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        metadata_str, inicio, fim = extrair_metadata_js(conteudo)
        
        if metadata_str is None:
            print(f"  ⚠️ Não foi possível extrair metadata de {caminho.name}")
            return False
        
        # Corrige metadata
        metadata_corrigida = corrigir_metadata(metadata_str)
        
        # Substitui no conteúdo original
        if metadata_str != metadata_corrigida:
            novo_conteudo = conteudo[:inicio] + metadata_corrigida + conteudo[fim:]
            
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(novo_conteudo)
            
            print(f"  ✅ {caminho.name} corrigido")
            return True
        else:
            print(f"  ✓ {caminho.name} já estava correto")
            return False
            
    except Exception as e:
        print(f"  ❌ Erro ao processar {caminho.name}: {e}")
        return False

def main():
    # Localiza diretório balancos/
    repo_root = Path(__file__).parent
    balancos_dir = repo_root / 'balancos'
    
    if not balancos_dir.exists():
        print("❌ Diretório 'balancos/' não encontrado")
        return
    
    print("🔍 Buscando arquivos multiplos*.js...\n")
    
    # Busca recursiva por multiplos*.js
    arquivos = list(balancos_dir.rglob('multiplos*.js'))
    
    if not arquivos:
        print("⚠️ Nenhum arquivo multiplos*.js encontrado")
        return
    
    print(f"📁 {len(arquivos)} arquivo(s) encontrado(s)\n")
    
    corrigidos = 0
    for arquivo in sorted(arquivos):
        if processar_arquivo(arquivo):
            corrigidos += 1
    
    print(f"\n{'='*60}")
    print(f"✨ Processamento concluído!")
    print(f"   • Total de arquivos: {len(arquivos)}")
    print(f"   • Corrigidos: {corrigidos}")
    print(f"   • Já corretos: {len(arquivos) - corrigidos}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
