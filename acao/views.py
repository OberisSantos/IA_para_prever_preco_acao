from django.shortcuts import render
import pandas as pd
import numpy as np

import yfinance as yf
import pandas_datareader as pdr

from scipy import stats

from sklearn.metrics import  mean_absolute_error

from datetime import date

# Create your views here.

def home(request):
    return render(request, 'acao/home.html', {})


def buscar_acao(request):
    yf.pdr_override()

    busca = request.GET['busca']

    #acao = pdr.get_data_yahoo(busca, start = '2015-01-01')['Close']
    
    acao = pd.read_csv("F:/preco_acao/acao/media/acao.csv")
    
    #converter para DateFrame
    acao = pd.DataFrame(acao)

    #apagar valores nulos
    acao.dropna(inplace=True) #remover
    acao = acao.rename(columns={'PETR3.SA': 'Close'}) #remover
    acao.set_index('Date', inplace=True)
    
    #resetar o index
    #acaodf.reset_index('Date', inplace=True)
    
    monte_carlo = previsao_monte_carlo(acao)
    
    return render(request, 'acao/home.html', {'monte_carlo': monte_carlo})


def previsao_monte_carlo(dataset):
    dataset = (dataset['Close'])
    #dataset = dataset.to_list() #converter para lista
    #dataset = pd.DataFrame(dataset)
    dias_a_frente = 90
    simulacoes = 50  

    dataset_normalizado = dataset.copy()
    #print(dataset.iloc[0][1])
   
    tamanho_dataset = len(dataset)
    
    for i in range(tamanho_dataset):        
        dataset_normalizado[i] = dataset[i] / dataset[0]

    
    dataset_normalizado = dataset_normalizado
    

    dataset_taxa_retorno = np.log(1 + dataset_normalizado.pct_change())
    dataset_taxa_retorno.fillna(0, inplace=True)
    media = dataset_taxa_retorno.mean()
    variancia = dataset_taxa_retorno.var()

    drift = media - (0.5 * variancia)
    desvio_padrao = dataset_taxa_retorno.std()

    Z = stats.norm.ppf(np.random.rand(dias_a_frente, simulacoes)) #numeros aleatorios com multiplicador do desvio padrão
    retorno_diarios = np.exp(drift + desvio_padrao * Z)

    previsoes = np.zeros_like(retorno_diarios) #criar uma matriz com zeros

    previsao_teste = previsoes.copy()
    
    previsoes[0] = dataset[-1] #iniciar a previsao com u último valor 

   
    #calculo das previsoes
    for dia in range(1, dias_a_frente): #a previsao será com base no dia anterior multiplicado pelo retorno de cada dia.
        previsoes[dia] = previsoes[dia - 1] * retorno_diarios[dia]
    previsao = previsoes.T.tolist()

    #testar para escolher a melhor previsão
    previsao_teste[0] = dataset[-dias_a_frente]
    

    for dia in range(1, dias_a_frente): #a previsao será com base no dia anterior multiplicado pelo retorno de cada dia.
        previsao_teste[dia] = previsao_teste[dia - 1] * retorno_diarios[dia]
    #p_teste = previsao_teste.T.tolist()
    #melhor = melhor_simulacao_monte_carlo(previsao_teste.T, dataset)
    previsao_teste = pd.DataFrame(previsao_teste)
    #previsao para teste
   
    #dataset_teste = dataset.reset_index(level=None, drop=True).copy()
    dataset_teste = dataset.copy()
    dataset_teste = dataset_teste.iloc[-len(previsao_teste):]
    #inicio = dataset_teste.index[-len(previsao_teste)] 
  
    erros = [ ]

    for i in range(len(previsao_teste.T)):
        simulacao = previsao_teste[i][0:len(dataset_teste)]
        erros.append(mean_absolute_error(dataset_teste, simulacao))

    erro_menor = min(erros)
    erro_menor_index = erros.index(erro_menor)

    previsao_teste = previsao_teste[erro_menor_index].to_list()
   

    data_futura = pd.date_range(start = date.today(), periods = dias_a_frente, freq ='B') 
    previsao_futura = pd.DataFrame(data_futura)
    #previsao_futura['Previsao'] = pd.DataFrame(previsao[erro_menor_index])
    previsao_futura.columns = ['Date']
    previsao_futura['Previsao'] = pd.DataFrame(previsao[erro_menor_index])
    #previsao_futura.set_index('Date', inplace=True)
    

    dados = {
        'erro': erro_menor,
        'previsao_futura': previsao_futura['Previsao'].to_list(),
        'previsao_teste': previsao_teste,
        'valor_real': dataset_teste.to_list()
    }
    
    return dados
