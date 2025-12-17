"""
CAPTURA DE BALANÇOS - VERSÃO GITHUB ACTIONS
Roda 100% na nuvem do GitHub
"""

import pandas as pd
import requests
from io import BytesIO
import zipfile
from pathlib import Path
from datetime import datetime

class CapturaBalancos:
    
    def __init__(self):
        self.pasta_balancos = Path('balancos')
        self.pasta_balancos.mkdir(exist_ok=True)
        self.ano_inicio = 2015
        self.ano_atual = datetime.now().year
    
    def baixar_cvm(self, ano, tipo):
        """Baixa dados da CVM"""
        url = f'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_{tipo}_con_{ano}.zip'
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                with zipfile.ZipFile(BytesIO(r.content)) as z:
                    nome = f'itr_cia_aberta_{tipo}_con_{ano}.csv'
                    with z.open(nome) as f:
                        return pd.read_csv(f, sep=';', encoding='ISO-8859-1', decimal=',')
        except:
            pass
        return None
    
    def processar_empresa(self, ticker, cnpj):
        """Processa uma empresa"""
        print(f"\n{'='*50}")
        print(f"📊 {ticker} (CNPJ: {cnpj})")
        
        pasta = self.pasta_balancos / ticker
        pasta.mkdir(exist_ok=True)
        
        # Processar todas as demonstrações
        demos = ['DRE', 'BPA', 'BPP', 'DFC_MD']
        
        for demo in demos:
            print(f"  {demo}:", end=' ')
            dados = []
            
            for ano in range(self.ano_inicio, self.ano_atual + 1):
                df = self.baixar_cvm(ano, demo)
                if df is None:
                    continue
                
                # CORREÇÃO CRÍTICA: Usar CNPJ COM formatação (não limpar)
                df = df[df['CNPJ_CIA'] == cnpj].copy()
                
                if len(df) == 0:
                    continue
                
                # Filtrar apenas consolidado e último exercício
                df = df[df['ORDEM_EXERC'] == 'ÚLTIMO']
                
                if len(df) == 0:
                    continue
                
                # Extrair trimestre
                df['TRIMESTRE'] = df['DT_FIM_EXERC'].str[5:7].map({
                    '03': 'T1', '06': 'T2', '09': 'T3', '12': 'T4'
                })
                
                # Converter valores
                df['VL_CONTA'] = pd.to_numeric(df['VL_CONTA'], errors='coerce')
                df['VALOR_MIL'] = df['VL_CONTA'] / 1000
                
                # Selecionar colunas
                df = df[['DT_FIM_EXERC', 'TRIMESTRE', 'CD_CONTA', 'DS_CONTA', 'VALOR_MIL']]
                df.columns = ['data_fim', 'trimestre', 'cd_conta', 'ds_conta', 'valor_mil']
                
                dados.append(df)
            
            if dados:
                consolidado = pd.concat(dados, ignore_index=True)
                consolidado = consolidado.sort_values(['data_fim', 'cd_conta'])
                consolidado = consolidado.drop_duplicates(subset=['data_fim', 'trimestre', 'cd_conta'], keep='last')
                arquivo = pasta / f"{demo.lower()}_consolidado.csv"
                consolidado.to_csv(arquivo, index=False, encoding='utf-8-sig')
                print(f"✅ {len(consolidado)} linhas")
            else:
                print("❌")
    
    def processar_lote(self, limite=10):
        """Processa múltiplas empresas"""
        
        # Tentar carregar com diferentes encodings
        try:
            # Tentar UTF-8 primeiro (padrão)
            df = pd.read_csv('mapeamento_final_b3_completo.csv', encoding='utf-8')
        except UnicodeDecodeError:
            # Se falhar, tentar ISO-8859-1 com separador ;
            df = pd.read_csv('mapeamento_final_b3_completo.csv', sep=';', encoding='ISO-8859-1')
        
        # Filtrar apenas empresas com CNPJ
        df = df[df['cnpj'].notna()].head(limite)
        
        print(f"\n🚀 Processando {len(df)} empresas...\n")
        
        for _, row in df.iterrows():
            try:
                self.processar_empresa(row['ticker'], row['cnpj'])
            except Exception as e:
                print(f"❌ Erro: {e}")
        
        print(f"\n✅ Concluído! Dados em: balancos/")

if __name__ == "__main__":
    import sys
    
    captura = CapturaBalancos()
    
    # Padrão: 10 empresas
    limite = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    
    captura.processar_lote(limite=limite)
