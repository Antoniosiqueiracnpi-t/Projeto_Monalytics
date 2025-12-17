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
    
    def processar_empresa(self, ticker, cvm):
        """Processa uma empresa"""
        print(f"\n{'='*50}")
        print(f"📊 {ticker} (CVM: {cvm})")
        
        pasta = self.pasta_balancos / ticker
        pasta.mkdir(exist_ok=True)
        
        # Identificar se é financeira
        financeiras = [1, 1023, 17663, 1170, 18945, 21610]
        demos = ['DRE', 'BPA', 'BPP'] if cvm in financeiras else ['DRE', 'BPA', 'BPP', 'DFC_MD']
        
        for demo in demos:
            print(f"  {demo}:", end=' ')
            dados = []
            
            for ano in range(self.ano_inicio, self.ano_atual + 1):
                df = self.baixar_cvm(ano, demo)
                if df is None:
                    continue
                
                df = df[df['CD_CVM'] == cvm].copy()
                if len(df) == 0:
                    continue
                
                df = df[df['ORDEM_EXERC'] == 'ÚLTIMO']
                df['TRIMESTRE'] = df['DT_FIM_EXERC'].str[5:7].map({
                    '03': 'T1', '06': 'T2', '09': 'T3', '12': 'T4'
                })
                
                df['VL_CONTA'] = pd.to_numeric(df['VL_CONTA'], errors='coerce')
                df['VALOR_MIL'] = df['VL_CONTA'] / 1000
                
                df = df[['DT_FIM_EXERC', 'TRIMESTRE', 'CD_CONTA', 'DS_CONTA', 'VALOR_MIL']]
                df.columns = ['data_fim', 'trimestre', 'cd_conta', 'ds_conta', 'valor_mil']
                
                dados.append(df)
            
            if dados:
                consolidado = pd.concat(dados, ignore_index=True)
                consolidado = consolidado.sort_values(['data_fim', 'cd_conta'])
                arquivo = pasta / f"{demo.lower()}_consolidado.csv"
                consolidado.to_csv(arquivo, index=False, encoding='utf-8-sig')
                print(f"✅ {len(consolidado)} linhas")
            else:
                print("❌")
    
    def processar_lote(self, limite=10):
        """Processa múltiplas empresas"""
        
        # Carregar mapeamento (com encoding correto)
        df = pd.read_csv('mapeamento_final_b3_completo.csv', encoding='utf-8-sig')
        df = df[df['codigo_cvm'].notna()].head(limite)
        
        print(f"\n🚀 Processando {len(df)} empresas...\n")
        
        for _, row in df.iterrows():
            try:
                self.processar_empresa(row['ticker'], int(row['codigo_cvm']))
            except Exception as e:
                print(f"❌ Erro: {e}")
        
        print(f"\n✅ Concluído! Dados em: balancos/")

if __name__ == "__main__":
    import sys
    
    captura = CapturaBalancos()
    
    # Padrão: 10 empresas
    limite = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    
    captura.processar_lote(limite=limite)
