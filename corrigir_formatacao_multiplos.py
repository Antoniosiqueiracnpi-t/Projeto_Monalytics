#!/usr/bin/env python3
"""
Script para corrigir a função formatMultiploValor() no script.js
Adiciona suporte para unidade "R$ mil" (valores em milhares de reais)
"""

import re
from pathlib import Path

# Caminho do arquivo
SCRIPT_JS = Path(__file__).parent / "site" / "js" / "script.js"

# Nova função corrigida
NOVA_FUNCAO = '''/**
 * Formata valores grandes em formato compacto (milhões, bilhões)
 * CORREÇÃO 2025-01-15: Adiciona suporte para "R$ mil"
 * @param {number} valor - Valor a ser formatado
 * @param {string} unidade - Unidade do múltiplo ('R$', 'R$ mil', '%', 'x', etc.)
 * @returns {string} - Valor formatado
 */
function formatMultiploValor(valor, unidade) {
    if (valor === null || valor === undefined) return 'N/D';
    
    // Para porcentagem e multiplicadores
    if (unidade === '%') {
        return `${valor.toFixed(2)}%`;
    }
    
    if (unidade === 'x') {
        return `${valor.toFixed(2)}x`;
    }
    
    // ✅ CORREÇÃO: Suporte para "R$ mil" (valores em milhares)
    if (unidade === 'R$ mil') {
        // Converte de milhares para reais (multiplica por 1.000)
        const valorEmReais = valor * 1_000;
        
        if (Math.abs(valorEmReais) >= 1_000_000_000) {
            // Bilhões
            return `R$ ${(valorEmReais / 1_000_000_000).toFixed(2)} bi`;
        } else if (Math.abs(valorEmReais) >= 1_000_000) {
            // Milhões
            return `R$ ${(valorEmReais / 1_000_000).toFixed(2)} mi`;
        } else if (Math.abs(valorEmReais) >= 1_000) {
            // Milhares
            return `R$ ${(valorEmReais / 1_000).toFixed(2)} mil`;
        } else {
            // Menor que mil
            return `R$ ${valorEmReais.toFixed(2)}`;
        }
    }
    
    // Para valores monetários padrão (R$)
    if (unidade === 'R$') {
        if (Math.abs(valor) >= 1_000_000_000) {
            // Bilhões
            return `R$ ${(valor / 1_000_000_000).toFixed(2)} bi`;
        } else if (Math.abs(valor) >= 1_000_000) {
            // Milhões
            return `R$ ${(valor / 1_000_000).toFixed(2)} mi`;
        } else if (Math.abs(valor) >= 1_000) {
            // Milhares
            return `R$ ${(valor / 1_000).toFixed(2)} mil`;
        } else {
            // Menor que mil
            return `R$ ${valor.toFixed(2)}`;
        }
    }
    
    // Padrão: sem unidade
    return valor.toFixed(2);
}'''

def corrigir_funcao():
    """Substitui a função formatMultiploValor no script.js"""
    
    print("🔧 Corrigindo formatMultiploValor()...")
    
    # Lê arquivo
    with open(SCRIPT_JS, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Padrão para localizar a função antiga
    # Captura desde "function formatMultiploValor" até a próxima função
    padrao = r'(function formatMultiploValor\(valor, unidade\).*?\n})\s*(?=\n\n/\*\*|\nfunction)'
    
    # Busca função
    match = re.search(padrao, conteudo, re.DOTALL)
    
    if not match:
        print("❌ Função formatMultiploValor() não encontrada!")
        return False
    
    funcao_antiga = match.group(1)
    print(f"✅ Função encontrada ({len(funcao_antiga)} caracteres)")
    
    # Substitui função
    novo_conteudo = conteudo.replace(funcao_antiga, NOVA_FUNCAO)
    
    # Salva arquivo
    with open(SCRIPT_JS, 'w', encoding='utf-8') as f:
        f.write(novo_conteudo)
    
    print(f"✅ Arquivo atualizado: {SCRIPT_JS}")
    print("\n🎯 Mudanças aplicadas:")
    print("   • Adicionado suporte para unidade 'R$ mil'")
    print("   • Valores em 'R$ mil' agora são multiplicados por 1.000")
    print("   • Formatação em bilhões/milhões funciona corretamente")
    
    return True

if __name__ == "__main__":
    if corrigir_funcao():
        print("\n✨ CORREÇÃO CONCLUÍDA COM SUCESSO!")
        print("\n📌 Teste:")
        print("   Valor: 166172757.07 com unidade 'R$ mil'")
        print("   ❌ ANTES: R$ 166.17 mi (ERRADO)")
        print("   ✅ DEPOIS: R$ 166.17 bi (CORRETO)")
    else:
        print("\n❌ Erro na correção")
