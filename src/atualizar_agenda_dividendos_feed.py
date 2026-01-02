"""
ATUALIZADOR DE AGENDA DE DIVIDENDOS A PARTIR DO FEED DE NOTÍCIAS
=================================================================
Janeiro 2025

MISSÃO:
1. Ler feed_noticias.json (pasta balancos)
2. Identificar notícias sobre proventos/dividendos
3. Extrair informações (tipo, valor, datas)
4. Atualizar agenda_dividendos_acoes_investidor10.json SEM apagar dados existentes
5. Adicionar apenas proventos FUTUROS (data_pagamento >= hoje)

ESTRUTURA DO JSON DE AGENDA:
[
  {
    "ticker": "BBDC3",
    "empresa": null,
    "tipo": "JSCP",
    "tipo_raw": "JSCP",
    "valor": 0.02,
    "valor_unidade": "R$",
    "data_com": "2020-01-02",
    "data_pagamento": "2020-02-03",
    "data_com_raw": "02/01/20",
    "data_pagamento_raw": "03/02/20",
    "valor_raw": "0,02",
    "source_url": "https://...",
    "ano_ref": 2020,
    "mes_ref": 1
  }
]

EXECUÇÃO:
python src/atualizar_agenda_dividendos_feed.py
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse


class AtualizadorAgendaDividendos:
    """
    Atualiza agenda de dividendos com informações do feed de notícias B3.
    """
    
    def __init__(
        self, 
        arquivo_feed: str = "balancos/feed_noticias.json",
        arquivo_agenda: str = "agenda_dividendos_acoes_investidor10.json"
    ):
        self.arquivo_feed = Path(arquivo_feed)
        self.arquivo_agenda = Path(arquivo_agenda)
        self.proventos_novos = []
        self.proventos_ignorados = []
        self.data_hoje = datetime.now().strftime('%Y-%m-%d')
    
    # ==================================================================================
    # CARREGAR DADOS
    # ==================================================================================
    
    def carregar_feed(self) -> Optional[Dict]:
        """Carrega feed de notícias."""
        if not self.arquivo_feed.exists():
            print(f"❌ Arquivo não encontrado: {self.arquivo_feed}")
            return None
        
        try:
            with open(self.arquivo_feed, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erro ao carregar feed: {e}")
            return None
    
    def carregar_agenda_existente(self) -> List[Dict]:
        """Carrega agenda existente ou retorna lista vazia."""
        if not self.arquivo_agenda.exists():
            print(f"⚠️  Arquivo agenda não encontrado. Será criado novo.")
            return []
        
        try:
            with open(self.arquivo_agenda, 'r', encoding='utf-8') as f:
                agenda = json.load(f)
                print(f"✅ Agenda existente carregada: {len(agenda)} proventos")
                return agenda
        except Exception as e:
            print(f"❌ Erro ao carregar agenda: {e}")
            return []
    
    # ==================================================================================
    # IDENTIFICAÇÃO DE NOTÍCIAS DE PROVENTOS
    # ==================================================================================
    
    def _identificar_tipo_provento(self, texto: str) -> Optional[str]:
        """
        Identifica tipo de provento baseado em palavras-chave.
        
        Returns:
            "Dividendos", "JSCP", "JCP", ou None
        """
        texto_upper = texto.upper()
        
        # Ordem de prioridade (mais específico primeiro)
        if any(palavra in texto_upper for palavra in [
            "JUROS SOBRE CAPITAL PROPRIO",
            "JUROS SOBRE O CAPITAL PROPRIO",
            "JUROS S/ CAPITAL PROPRIO",
            "JCP",
            "JSCP"
        ]):
            return "JSCP"
        
        if any(palavra in texto_upper for palavra in [
            "DIVIDENDO",
            "DIVIDEND",
            "DIV.",
            "PROVENT"
        ]):
            return "Dividendos"
        
        return None
    
    def _e_noticia_provento(self, noticia: Dict) -> bool:
        """Verifica se notícia é sobre proventos."""
        titulo = noticia.get('titulo', '').upper()
        headline = noticia.get('headline', '').upper()
        categoria = noticia.get('categoria', '').upper()
        
        texto = f"{titulo} {headline} {categoria}"
        
        # Palavras-chave de proventos
        keywords_provento = [
            "DIVIDENDO", "DIVIDEND", "JCP", "JSCP",
            "JUROS SOBRE CAPITAL", "PROVENTO", "RENDIMENTO"
        ]
        
        # Palavras de exclusão (evitar falsos positivos)
        keywords_exclusao = [
            "CALENDARIO", "ASSEMBLEIA", "ATA", "POLITICA"
        ]
        
        tem_provento = any(kw in texto for kw in keywords_provento)
        tem_exclusao = any(kw in texto for kw in keywords_exclusao)
        
        return tem_provento and not tem_exclusao
    
    # ==================================================================================
    # EXTRAÇÃO DE INFORMAÇÕES
    # ==================================================================================
    
    def _extrair_valor(self, texto: str) -> Optional[float]:
        """
        Extrai valor monetário de texto.
        
        Formatos suportados:
        - R$ 0,15
        - R$ 1,23
        - R$ 12,34
        - R$ 0.15
        - 0,15 por ação
        """
        # Padrões de regex (ordem de especificidade)
        padroes = [
            r'R\$\s*(\d+[.,]\d{2})',           # R$ 1,23 ou R$ 1.23
            r'(\d+[.,]\d{2})\s*(?:por|reais)', # 1,23 por ação
            r'valor\s+de\s+R\$\s*(\d+[.,]\d{2})', # valor de R$ 1,23
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                valor_str = match.group(1).replace(',', '.')
                try:
                    return float(valor_str)
                except ValueError:
                    continue
        
        return None
    
    def _extrair_datas(self, texto: str) -> Dict[str, Optional[str]]:
        """
        Extrai datas da notícia.
        
        Retorna:
            {
                'data_com': 'YYYY-MM-DD' ou None,
                'data_pagamento': 'YYYY-MM-DD' ou None
            }
        """
        # Padrões de data
        # DD/MM/YYYY ou DD/MM/YY
        padrao_data = r'\b(\d{2})/(\d{2})/(\d{2,4})\b'
        
        datas_encontradas = []
        for match in re.finditer(padrao_data, texto):
            dia, mes, ano = match.groups()
            
            # Normalizar ano (2 dígitos → 4 dígitos)
            if len(ano) == 2:
                ano_int = int(ano)
                # Se ano < 50, assume 2000+, senão 1900+
                ano = f"20{ano}" if ano_int < 50 else f"19{ano}"
            
            try:
                data_iso = f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"
                # Validar data
                datetime.strptime(data_iso, '%Y-%m-%d')
                datas_encontradas.append(data_iso)
            except ValueError:
                continue
        
        # Heurística: primeira data = data com, última data = data pagamento
        resultado = {
            'data_com': None,
            'data_pagamento': None
        }
        
        if len(datas_encontradas) >= 2:
            resultado['data_com'] = datas_encontradas[0]
            resultado['data_pagamento'] = datas_encontradas[-1]
        elif len(datas_encontradas) == 1:
            # Se só tem uma data, assume que é data de pagamento
            resultado['data_pagamento'] = datas_encontradas[0]
        
        return resultado
    
    def _extrair_ticker_base(self, ticker: str) -> str:
        """Remove número de classe do ticker (BBDC4 → BBDC)."""
        return re.sub(r'\d+$', '', ticker.upper().strip())
    
    # ==================================================================================
    # PROCESSAMENTO DE NOTÍCIAS
    # ==================================================================================
    
    def processar_noticia(self, item_feed: Dict) -> Optional[Dict]:
        """
        Processa uma notícia do feed e extrai provento.
        
        Returns:
            Dict com estrutura da agenda ou None
        """
        # Validar estrutura
        if 'empresa' not in item_feed or 'noticia' not in item_feed:
            return None
        
        empresa = item_feed['empresa']
        noticia = item_feed['noticia']
        
        # Verificar se é notícia de provento
        if not self._e_noticia_provento(noticia):
            return None
        
        # Extrair informações
        ticker = empresa.get('ticker', '')
        if not ticker:
            return None
        
        texto_completo = f"{noticia.get('titulo', '')} {noticia.get('headline', '')}"
        
        tipo = self._identificar_tipo_provento(texto_completo)
        if not tipo:
            return None
        
        valor = self._extrair_valor(texto_completo)
        if not valor or valor <= 0:
            return None
        
        datas = self._extrair_datas(texto_completo)
        data_pagamento = datas.get('data_pagamento')
        
        # CRÍTICO: Só adicionar se data de pagamento for FUTURA
        if not data_pagamento or data_pagamento < self.data_hoje:
            return None
        
        # Construir objeto no formato da agenda
        provento = {
            "ticker": ticker,
            "empresa": empresa.get('nome'),
            "tipo": tipo,
            "tipo_raw": tipo,
            "valor": valor,
            "valor_unidade": "R$",
            "data_com": datas.get('data_com'),
            "data_pagamento": data_pagamento,
            "data_com_raw": self._formatar_data_br(datas.get('data_com')),
            "data_pagamento_raw": self._formatar_data_br(data_pagamento),
            "valor_raw": f"{valor:.2f}".replace('.', ','),
            "source_url": noticia.get('url', ''),
            "ano_ref": int(data_pagamento.split('-')[0]),
            "mes_ref": int(data_pagamento.split('-')[1])
        }
        
        return provento
    
    def _formatar_data_br(self, data_iso: Optional[str]) -> Optional[str]:
        """Converte YYYY-MM-DD para DD/MM/YY."""
        if not data_iso:
            return None
        
        try:
            dt = datetime.strptime(data_iso, '%Y-%m-%d')
            return dt.strftime('%d/%m/%y')
        except ValueError:
            return None
    
    # ==================================================================================
    # DEDUPLICAÇÃO
    # ==================================================================================
    
    def _criar_chave_duplicacao(self, provento: Dict) -> Tuple:
        """
        Cria chave única para detectar duplicatas.
        
        Considera: ticker + data_com + valor
        """
        ticker = provento.get('ticker', '').upper()
        data_com = provento.get('data_com') or provento.get('data_pagamento', '')
        valor = round(provento.get('valor', 0), 2)
        
        return (ticker, data_com, valor)
    
    def remover_duplicatas(
        self, 
        agenda_existente: List[Dict], 
        proventos_novos: List[Dict]
    ) -> List[Dict]:
        """
        Remove duplicatas entre agenda existente e novos proventos.
        
        Returns:
            Lista de proventos únicos para adicionar
        """
        # Criar set de chaves existentes
        chaves_existentes = {
            self._criar_chave_duplicacao(p) 
            for p in agenda_existente
        }
        
        # Filtrar novos proventos
        unicos = []
        duplicados = []
        
        for provento in proventos_novos:
            chave = self._criar_chave_duplicacao(provento)
            
            if chave not in chaves_existentes:
                unicos.append(provento)
                chaves_existentes.add(chave)  # Adicionar ao set para evitar duplicatas dentro dos novos
            else:
                duplicados.append(provento)
        
        if duplicados:
            print(f"  ⏭️  {len(duplicados)} proventos duplicados ignorados")
        
        return unicos
    
    # ==================================================================================
    # EXECUÇÃO PRINCIPAL
    # ==================================================================================
    
    def executar(self) -> Tuple[int, int]:
        """
        Executa atualização completa da agenda.
        
        Returns:
            (total_novos, total_existentes)
        """
        print(f"\n{'='*70}")
        print(f"📊 ATUALIZADOR DE AGENDA DE DIVIDENDOS (FEED)")
        print(f"{'='*70}")
        print(f"Data de referência: {self.data_hoje}")
        print(f"Feed: {self.arquivo_feed}")
        print(f"Agenda: {self.arquivo_agenda}")
        print(f"{'='*70}\n")
        
        # 1. Carregar dados
        print("1️⃣ Carregando dados...")
        
        feed = self.carregar_feed()
        if not feed:
            return 0, 0
        
        agenda_existente = self.carregar_agenda_existente()
        total_existentes = len(agenda_existente)
        
        # 2. Processar feed
        print(f"\n2️⃣ Processando feed ({len(feed.get('feed', []))} notícias)...")
        
        proventos_candidatos = []
        noticias_provento = 0
        
        for item in feed.get('feed', []):
            if self._e_noticia_provento(item.get('noticia', {})):
                noticias_provento += 1
                provento = self.processar_noticia(item)
                if provento:
                    proventos_candidatos.append(provento)
        
        print(f"  ✅ {noticias_provento} notícias sobre proventos identificadas")
        print(f"  ✅ {len(proventos_candidatos)} proventos futuros extraídos")
        
        # 3. Remover duplicatas
        print(f"\n3️⃣ Removendo duplicatas...")
        
        proventos_unicos = self.remover_duplicatas(agenda_existente, proventos_candidatos)
        print(f"  ✅ {len(proventos_unicos)} proventos novos para adicionar")
        
        # 4. Consolidar e salvar
        print(f"\n4️⃣ Salvando agenda atualizada...")
        
        agenda_atualizada = agenda_existente + proventos_unicos
        
        # Ordenar por data de pagamento (mais antigo primeiro)
        agenda_atualizada.sort(
            key=lambda x: (
                x.get('data_pagamento', '9999-99-99'),
                x.get('ticker', ''),
                x.get('valor', 0)
            )
        )
        
        # Salvar
        try:
            with open(self.arquivo_agenda, 'w', encoding='utf-8') as f:
                json.dump(agenda_atualizada, f, ensure_ascii=False, indent=2)
            
            print(f"  ✅ Agenda salva: {self.arquivo_agenda}")
            print(f"  📊 Total de proventos: {len(agenda_atualizada)}")
            print(f"     - Existentes: {total_existentes}")
            print(f"     - Novos: {len(proventos_unicos)}")
            
        except Exception as e:
            print(f"  ❌ Erro ao salvar: {e}")
            return 0, total_existentes
        
        # 5. Resumo dos novos
        if proventos_unicos:
            print(f"\n5️⃣ Resumo dos proventos adicionados:\n")
            
            for p in proventos_unicos[:10]:  # Mostrar primeiros 10
                print(f"  • {p['ticker']} - {p['tipo']}: R$ {p['valor']:.2f} em {p['data_pagamento']}")
            
            if len(proventos_unicos) > 10:
                print(f"  ... e mais {len(proventos_unicos) - 10} proventos")
        
        print(f"\n{'='*70}")
        print(f"✅ ATUALIZAÇÃO CONCLUÍDA")
        print(f"{'='*70}\n")
        
        return len(proventos_unicos), total_existentes


# ======================================================================================
# CLI
# ======================================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Atualiza agenda de dividendos com informações do feed de notícias"
    )
    parser.add_argument(
        "--feed",
        default="balancos/feed_noticias.json",
        help="Caminho do arquivo feed_noticias.json"
    )
    parser.add_argument(
        "--agenda",
        default="agenda_dividendos_acoes_investidor10.json",
        help="Caminho do arquivo agenda_dividendos_acoes_investidor10.json"
    )
    args = parser.parse_args()
    
    atualizador = AtualizadorAgendaDividendos(
        arquivo_feed=args.feed,
        arquivo_agenda=args.agenda
    )
    
    novos, existentes = atualizador.executar()
    
    if novos == 0 and existentes == 0:
        print("❌ Nenhum provento processado")
        exit(1)
    
    exit(0)


if __name__ == "__main__":
    main()
