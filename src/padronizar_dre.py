"""
PADRONIZAÇÃO DE DRE - Demonstração do Resultado do Exercício
- Padroniza contas segundo estrutura padrão para empresas não financeiras
- Isola trimestres (calcula T4 se necessário)
- Tratamento especial para Lucro por Ação (3.99)
- Validação linha a linha com DRE anual
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class PadronizadorDRE:
    
    def __init__(self):
        self.pasta_balancos = Path("balancos")
        
        # Contas padrão DRE (não financeiras)
        self.contas_padrao = {
            "3.01": "Receita de Venda de Bens e/ou Serviços",
            "3.02": "Custo dos Bens e/ou Serviços Vendidos",
            "3.03": "Resultado Bruto",
            "3.04": "Despesas/Receitas Operacionais",
            "3.05": "Resultado Antes do Resultado Financeiro e dos Tributos",
            "3.06": "Resultado Financeiro",
            "3.07": "Resultado Antes dos Tributos sobre o Lucro",
            "3.08": "Imposto de Renda e Contribuição Social sobre o Lucro",
            "3.09": "Resultado Líquido das Operações Continuadas",
            "3.10": "Resultado Líquido de Operações Descontinuadas",
            "3.11": "Lucro/Prejuízo Consolidado do Período",
            "3.99": "Lucro por Ação (Reais/Ação)"
        }
    
    # ------------------------- HELPERS -------------------------
    
    def _extrair_lucro_por_acao(self, df: pd.DataFrame, data_fim: str, trimestre: str) -> float:
        """
        Extrai o valor correto de Lucro por Ação (3.99.x.x)
        Regras:
        - Se ON e PN têm valores diferentes, soma ambos
        - Se ON e PN têm valores iguais, pega apenas um
        - Ignora os níveis superiores (3.99, 3.99.01, 3.99.02)
        """
        mask = (
            (df['data_fim'] == data_fim) & 
            (df['trimestre'] == trimestre) & 
            (df['cd_conta'].str.startswith('3.99'))
        )
        subset = df[mask].copy()
        
        if subset.empty:
            return np.nan
        
        # Filtra apenas as contas terminais (3.99.01.01, 3.99.02.01, etc)
        subset = subset[subset['cd_conta'].str.count(r'\.') >= 3]
        
        if subset.empty:
            return np.nan
        
        # Identifica ON e PN
        on_mask = subset['ds_conta'].str.upper().str.contains('ON', na=False)
        pn_mask = subset['ds_conta'].str.upper().str.contains('PN', na=False)
        
        valor_on = subset[on_mask]['valor_mil'].sum()
        valor_pn = subset[pn_mask]['valor_mil'].sum()
        
        # Se ambos existem e são diferentes, soma
        if valor_on != 0 and valor_pn != 0 and abs(valor_on - valor_pn) > 0.0001:
            return valor_on + valor_pn
        
        # Caso contrário, retorna o maior valor encontrado (evita duplicação)
        valores = subset['valor_mil'].dropna()
        return valores.max() if not valores.empty else np.nan
    
    def _extrair_conta_padrao(self, df: pd.DataFrame, codigo: str, data_fim: str, trimestre: str) -> float:
        """
        Extrai o valor de uma conta padrão para data_fim e trimestre específicos
        """
        if codigo == "3.99":
            return self._extrair_lucro_por_acao(df, data_fim, trimestre)
        
        mask = (
            (df['data_fim'] == data_fim) & 
            (df['trimestre'] == trimestre) & 
            (df['cd_conta'] == codigo)
        )
        valores = df[mask]['valor_mil']
        
        return valores.iloc[0] if not valores.empty else np.nan
    
    def _calcular_t4_isolado(self, df_tri: pd.DataFrame, df_anual: pd.DataFrame, ano: int) -> pd.DataFrame:
        """
        Calcula T4 isolado: T4 = Anual - (T1 + T2 + T3)
        Retorna DataFrame com as linhas do T4 calculado
        """
        data_fim_anual = f"{ano}-12-31"
        
        # Verifica se existe anual para este ano
        if data_fim_anual not in df_anual['data_fim'].values:
            return pd.DataFrame()
        
        # Verifica quais trimestres existem
        trimestres_disponiveis = df_tri[df_tri['data_fim'].str.startswith(str(ano))]['trimestre'].unique()
        
        if 'T4' in trimestres_disponiveis:
            # Já tem T4, não precisa calcular
            return pd.DataFrame()
        
        if not all(t in trimestres_disponiveis for t in ['T1', 'T2', 'T3']):
            # Não tem T1, T2 e T3 completos
            return pd.DataFrame()
        
        linhas_t4 = []
        
        for codigo, descricao in self.contas_padrao.items():
            # Valor anual
            valor_anual = self._extrair_conta_padrao(df_anual, codigo, data_fim_anual, 'T4')
            
            if pd.isna(valor_anual):
                continue
            
            # Soma T1 + T2 + T3
            soma_tri = 0
            for tri in ['T1', 'T2', 'T3']:
                data_tri = f"{ano}-{(int(tri[1])*3):02d}-31"
                if data_tri.endswith('31-31'):
                    data_tri = data_tri.replace('-31-31', '-30')
                if tri == 'T1':
                    data_tri = f"{ano}-03-31"
                elif tri == 'T2':
                    data_tri = f"{ano}-06-30"
                elif tri == 'T3':
                    data_tri = f"{ano}-09-30"
                
                valor_tri = self._extrair_conta_padrao(df_tri, codigo, data_tri, tri)
                if not pd.isna(valor_tri):
                    soma_tri += valor_tri
            
            # T4 = Anual - (T1+T2+T3)
            valor_t4 = valor_anual - soma_tri
            
            linhas_t4.append({
                'data_fim': data_fim_anual,
                'trimestre': 'T4',
                'cd_conta': codigo,
                'ds_conta': descricao,
                'valor_mil': valor_t4
            })
        
        return pd.DataFrame(linhas_t4)
    
    def _montar_dataframe_horizontal(self, df_tri: pd.DataFrame, df_anual: pd.DataFrame, anos: list) -> pd.DataFrame:
        """
        Monta DataFrame horizontal com trimestres isolados
        Formato: cd_conta | ds_conta | YYYY-T1 | YYYY-T2 | ... (do mais antigo para o mais recente)
        """
        # Combina trimestral com T4 calculados quando necessário
        frames = [df_tri]
        
        for ano in anos:
            df_t4 = self._calcular_t4_isolado(df_tri, df_anual, ano)
            if not df_t4.empty:
                frames.append(df_t4)
        
        df_completo = pd.concat(frames, ignore_index=True)
        
        # Cria coluna período (YYYY-TX)
        df_completo['periodo'] = df_completo['data_fim'].str[:4] + '-' + df_completo['trimestre']
        
        # Agrupa contas padrão
        resultado = []
        
        for codigo, descricao in self.contas_padrao.items():
            linha = {
                'cd_conta': codigo,
                'ds_conta': descricao
            }
            
            # Para cada período único
            periodos = sorted(df_completo['periodo'].unique())
            
            for periodo in periodos:
                ano = periodo[:4]
                tri = periodo[-2:]
                
                # Encontra a data_fim correta
                if tri == 'T1':
                    data_fim = f"{ano}-03-31"
                elif tri == 'T2':
                    data_fim = f"{ano}-06-30"
                elif tri == 'T3':
                    data_fim = f"{ano}-09-30"
                else:  # T4
                    data_fim = f"{ano}-12-31"
                
                valor = self._extrair_conta_padrao(df_completo, codigo, data_fim, tri)
                linha[periodo] = valor
            
            resultado.append(linha)
        
        return pd.DataFrame(resultado)
    
    def _validar_com_anual(self, df_horizontal: pd.DataFrame, df_anual: pd.DataFrame) -> dict:
        """
        Valida se a soma dos trimestres bate com o anual
        Retorna dicionário com resultados da validação
        """
        validacao = {
            'total_linhas': len(df_horizontal),
            'linhas_validas': 0,
            'linhas_invalidas': 0,
            'erros': []
        }
        
        # Identifica colunas de períodos
        colunas_periodos = [col for col in df_horizontal.columns if '-T' in col]
        
        # Agrupa por ano
        anos = set(col[:4] for col in colunas_periodos)
        
        for idx, row in df_horizontal.iterrows():
            codigo = row['cd_conta']
            descricao = row['ds_conta']
            
            linha_valida = True
            
            for ano in anos:
                # Colunas deste ano
                cols_ano = [col for col in colunas_periodos if col.startswith(ano)]
                
                if not cols_ano:
                    continue
                
                # Verifica se tem os 4 trimestres
                trimestres = [col for col in cols_ano if col[-2:] in ['T1', 'T2', 'T3', 'T4']]
                
                if len(trimestres) == 4:
                    # Soma dos trimestres
                    soma_tri = sum(row[t] for t in trimestres if pd.notna(row[t]))
                    
                    # Valor anual esperado
                    data_fim_anual = f"{ano}-12-31"
                    valor_anual = self._extrair_conta_padrao(df_anual, codigo, data_fim_anual, 'T4')
                    
                    if not pd.isna(valor_anual):
                        diferenca = abs(soma_tri - valor_anual)
                        tolerancia = abs(valor_anual) * 0.01  # 1% de tolerância
                        
                        if diferenca > max(tolerancia, 0.01):  # Mínimo 0.01 mil
                            linha_valida = False
                            validacao['erros'].append({
                                'conta': f"{codigo} - {descricao}",
                                'ano': ano,
                                'soma_trimestres': round(soma_tri, 2),
                                'valor_anual': round(valor_anual, 2),
                                'diferenca': round(diferenca, 2)
                            })
            
            if linha_valida:
                validacao['linhas_validas'] += 1
            else:
                validacao['linhas_invalidas'] += 1
        
        return validacao
    
    # ------------------------- PROCESSAMENTO -------------------------
    
    def padronizar_dre_empresa(self, ticker: str, validar: bool = True):
        """
        Padroniza DRE de uma empresa específica
        """
        print(f"\n{'='*60}")
        print(f"📋 Padronizando DRE: {ticker}")
        
        pasta_ticker = self.pasta_balancos / ticker
        
        if not pasta_ticker.exists():
            print(f"❌ Pasta não encontrada: {pasta_ticker}")
            return
        
        arquivo_tri = pasta_ticker / "dre_consolidado.csv"
        arquivo_anual = pasta_ticker / "dre_anual.csv"
        
        if not arquivo_tri.exists():
            print(f"❌ Arquivo não encontrado: {arquivo_tri}")
            return
        
        if not arquivo_anual.exists():
            print(f"❌ Arquivo não encontrado: {arquivo_anual}")
            return
        
        # Carrega dados
        df_tri = pd.read_csv(arquivo_tri)
        df_anual = pd.read_csv(arquivo_anual)
        
        # Identifica anos disponíveis
        anos = sorted(set(df_tri['data_fim'].str[:4].unique()) | set(df_anual['data_fim'].str[:4].unique()))
        anos = [int(a) for a in anos if a.isdigit()]
        
        print(f"📅 Anos encontrados: {anos}")
        
        # Monta DataFrame horizontal
        df_padronizado = self._montar_dataframe_horizontal(df_tri, df_anual, anos)
        
        # Salva arquivo padronizado
        arquivo_saida = pasta_ticker / "dre_padronizado.csv"
        df_padronizado.to_csv(arquivo_saida, index=False, encoding="utf-8-sig")
        
        print(f"✅ DRE padronizado salvo: {arquivo_saida}")
        print(f"   {len(df_padronizado)} contas × {len(df_padronizado.columns)-2} períodos")
        
        # Validação
        if validar:
            print(f"\n🔍 Validando com DRE anual...")
            validacao = self._validar_com_anual(df_padronizado, df_anual)
            
            print(f"   Total de linhas: {validacao['total_linhas']}")
            print(f"   ✅ Linhas válidas: {validacao['linhas_validas']}")
            print(f"   ❌ Linhas inválidas: {validacao['linhas_invalidas']}")
            
            if validacao['erros']:
                print(f"\n⚠️  Erros encontrados ({len(validacao['erros'])}):")
                for erro in validacao['erros'][:5]:  # Mostra apenas os 5 primeiros
                    print(f"   • {erro['conta']} ({erro['ano']})")
                    print(f"     Soma trimestres: {erro['soma_trimestres']:,.2f}")
                    print(f"     Valor anual: {erro['valor_anual']:,.2f}")
                    print(f"     Diferença: {erro['diferenca']:,.2f}")
                
                if len(validacao['erros']) > 5:
                    print(f"   ... e mais {len(validacao['erros'])-5} erros")
    
    def padronizar_dre_lote(self, tickers: list = None, validar: bool = True):
        """
        Padroniza DRE de múltiplas empresas
        Se tickers=None, processa todas as pastas em balancos/
        """
        if tickers is None:
            # Processa todas as empresas
            tickers = [p.name for p in self.pasta_balancos.iterdir() if p.is_dir()]
        
        print(f"\n🚀 Padronizando DRE de {len(tickers)} empresas...\n")
        
        sucesso = 0
        erro = 0
        
        for ticker in tickers:
            try:
                self.padronizar_dre_empresa(ticker, validar=validar)
                sucesso += 1
            except Exception as e:
                print(f"❌ Erro em {ticker}: {e}")
                erro += 1
        
        print(f"\n{'='*60}")
        print(f"✅ Concluído: {sucesso} sucessos, {erro} erros")
    
    def padronizar_dre_por_csv(self, arquivo_csv: str = "mapeamento_final_b3_completo.csv", 
                               limite: int = None, validar: bool = True):
        """
        Padroniza DRE usando lista de tickers do CSV de mapeamento
        """
        try:
            df = pd.read_csv(arquivo_csv, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(arquivo_csv, sep=";", encoding="ISO-8859-1")
        
        tickers = df['ticker'].dropna().tolist()
        
        if limite:
            tickers = tickers[:limite]
        
        self.padronizar_dre_lote(tickers=tickers, validar=validar)


if __name__ == "__main__":
    import sys
    
    padronizador = PadronizadorDRE()
    
    # Exemplos de uso:
    # python padronizar_dre.py                    -> padroniza todas as empresas
    # python padronizar_dre.py PETR4              -> padroniza apenas PETR4
    # python padronizar_dre.py csv 10             -> padroniza 10 primeiras do CSV
    # python padronizar_dre.py csv                -> padroniza todas do CSV
    
    if len(sys.argv) == 1:
        # Sem argumentos: processa todas
        padronizador.padronizar_dre_lote()
    
    elif len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg.lower() == 'csv':
            # Processa todas do CSV
            padronizador.padronizar_dre_por_csv()
        else:
            # Processa ticker específico
            padronizador.padronizar_dre_empresa(arg)
    
    elif len(sys.argv) == 3 and sys.argv[1].lower() == 'csv':
        # Processa N primeiras do CSV
        limite = int(sys.argv[2])
        padronizador.padronizar_dre_por_csv(limite=limite)
    
    else:
        print("Uso:")
        print("  python padronizar_dre.py              # todas as empresas")
        print("  python padronizar_dre.py PETR4        # empresa específica")
        print("  python padronizar_dre.py csv          # todas do CSV")
        print("  python padronizar_dre.py csv 10       # 10 primeiras do CSV")
