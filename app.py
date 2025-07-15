import streamlit as st
import pandas as pd
import requests
import ta  # Para cálculos de indicadores

# Função para obter dados da API
def get_candles(coin, timeframe):
    # Exemplo usando Yahoo Finance
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{coin}-USD?range=1mo&interval={timeframe}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['chart']['result'][0]['indicators']['quote'][0]
    else:
        st.error("Não foi possível carregar dados automaticamente. Insira os valores manualmente.")
        return None

# Função para calcular RSI e EMAs
def calculate_indicators(data):
    df = pd.DataFrame(data)
    df['EMA_8'] = ta.trend.ema_indicator(df['close'], window=8)
    df['EMA_21'] = ta.trend.ema_indicator(df['close'], window=21)
    df['EMA_56'] = ta.trend.ema_indicator(df['close'], window=56)
    df['EMA_200'] = ta.trend.ema_indicator(df['close'], window=200)
    df['RSI'] = ta.momentum.rsi(df['close'], window=14)
    return df

# Interface do Streamlit
st.title("Análise Técnica de Criptomoedas")

# Seleção de moeda e timeframe
coin = st.selectbox("Selecione a moeda:", ["BTC", "ETH", "SOL"])
timeframe = st.selectbox("Selecione o timeframe:", ["1h", "4h", "1d", "1w"])

# Obter dados
data = get_candles(coin, timeframe)

if data:
    indicators_df = calculate_indicators(data)
    st.write(indicators_df)

    # Classificação do RSI
    rsi_value = indicators_df['RSI'].iloc[-1]
    if rsi_value < 30:
        rsi_classification = "Sobrevendida"
    elif rsi_value > 70:
        rsi_classification = "Sobrecomprada"
    else:
        rsi_classification = "Neutra"

    st.write(f"Classificação do RSI: {rsi_classification}")

    # Exibir EMAs
    st.write(f"EMA 8: {indicators_df['EMA_8'].iloc[-1]}")
    st.write(f"EMA 21: {indicators_df['EMA_21'].iloc[-1]}")
    st.write(f"EMA 56: {indicators_df['EMA_56'].iloc[-1]}")
    st.write(f"EMA 200: {indicators_df['EMA_200'].iloc[-1]}")

    # Exportar para CSV
    if st.button("Exportar Análise"):
        indicators_df.to_csv(f"{coin}_analysis.csv")
        st.success("Análise exportada com sucesso!")

# Botão para limpar/resetar
if st.button("Limpar"):
    st.experimental_rerun()
