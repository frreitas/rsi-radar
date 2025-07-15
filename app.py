import streamlit as st
import pandas as pd
import requests
import time
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

st.set_page_config(page_title="Radar Técnico Cripto - Diário", layout="wide")
st.title("📊 Radar Técnico Cripto - Análise Diária (RSI + EMA20 + EMA50)")
st.markdown("""
Dados via CoinGecko API (candles diários).  
Intervalos intraday não disponíveis na versão gratuita e estável.  
""")

@st.cache_data(ttl=900)
def get_top_coins(n=100):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": n,
        "page": 1,
        "sparkline": False,
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    return df

def validar_id_coin(coin_id):
    if not isinstance(coin_id, str):
        return False
    coin_id = coin_id.strip()
    if coin_id == "":
        return False
    import re
    if not re.fullmatch(r"[a-z0-9-]+", coin_id):
        return False
    return True

@st.cache_data(ttl=900)
def get_coin_ohlc(coin_id, days=60):
    if not validar_id_coin(coin_id):
        st.warning(f"ID inválido da moeda ignorado: '{coin_id}'")
        return pd.DataFrame()
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        df = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        return df
    except requests.exceptions.HTTPError as e:
        st.warning(f"Erro HTTP ao obter candles para {coin_id}: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.warning(f"Erro inesperado ao obter candles para {coin_id}: {e}")
        return pd.DataFrame()

def calcular_indicadores(df):
    close = df["price"]
    if len(close) < 50:
        return None

    rsi = RSIIndicator(close=close, window=14).rsi()
    ema20 = EMAIndicator(close=close, window=20).ema_indicator()
    ema50 = EMAIndicator(close=close, window=50).ema_indicator()

    rsi_ult = rsi.iloc[-1]
    ema20_ult = ema20.iloc[-1]
    ema50_ult = ema50.iloc[-1]

    if rsi_ult <= 30:
        rsi_class = "Sobrevendida"
    elif rsi_ult >= 70:
        rsi_class = "Sobrecomprada"
    else:
        rsi_class = "Neutra"

    if ema20_ult > ema50_ult:
        tendencia = "Alta"
    elif ema20_ult < ema50_ult:
        tendencia = "Baixa"
    else:
        tendencia = "Neutra"

    return {
        "RSI": round(rsi_ult, 2),
        "Classificação RSI": rsi_class,
        "EMA20": round(ema20_ult, 2),
        "EMA50": round(ema50_ult, 2),
        "Tendência": tendencia
    }

# UI Inputs
top_n = st.slider("Número de moedas a analisar (top N)", 5, 100, 20)
filtro_rsi = st.multiselect("Filtrar por classificação RSI", ["Sobrevendida", "Neutra", "Sobrecomprada"], default=["Sobrevendida", "Neutra", "Sobrecomprada"])
input_moeda = st.text_input("Buscar moeda por símbolo (ex: btc). Deixe vazio para usar top N.")

botao = st.button("Analisar")

if botao:
    with st.spinner("Carregando dados e calculando indicadores..."):
        try:
            df_coins = get_top_coins(top_n)
        except Exception as e:
            st.error(f"Erro ao obter lista de moedas: {e}")
            st.stop()

        if input_moeda.strip():
            df_coins = df_coins[df_coins["symbol"].str.lower() == input_moeda.strip().lower()]
            if df_coins.empty:
                st.warning("Moeda não encontrada.")
                st.stop()

        df_coins["id_valido"] = df_coins["id"].apply(validar_id_coin)
        df_coins_validas = df_coins[df_coins["id_valido"]]

        if df_coins_validas.empty:
            st.warning("Nenhuma moeda válida para análise após filtragem dos IDs.")
            st.stop()

        resultados = []
        for _, coin in df_coins_validas.iterrows():
            st.write(f"Analisando: {coin['id']} ({coin['symbol'].upper()})")
            df_ohlc = get_coin_ohlc(coin["id"], days=60)
            if df_ohlc.empty:
                st.warning(f"Sem dados suficientes para {coin['symbol'].upper()}")
                continue

            indicadores = calcular_indicadores(df_ohlc)
            if indicadores is None:
                st.warning(f"Indicadores insuficientes para {coin['symbol'].upper()}")
                continue

            preco_atual = df_ohlc["price"].iloc[-1]
            preco_ontem = df_ohlc["price"].iloc[-2]
            variacao = ((preco_atual - preco_ontem) / preco_ontem) * 100

            resultados.append({
                "Moeda": coin["symbol"].upper(),
                "Nome": coin["name"],
                "Preço Atual (USD)": round(preco_atual, 4),
                "Variação 24h (%)": round(variacao, 2),
                **indicadores
            })

            time.sleep(1.5)  # pausa para evitar rate limit CoinGecko

        if resultados:
            df_res = pd.DataFrame(resultados)
            df_filtrado = df_res[df_res["Classificação RSI"].isin(filtro_rsi)]

            def alerta(row):
                if row["RSI"] <= 30 and row["Tendência"] == "Alta":
                    return "🔔"
                return ""

            df_filtrado["Alerta"] = df_filtrado.apply(alerta, axis=1)

            st.subheader("Resultados da Análise Técnica")
            st.dataframe(df_filtrado.style.applymap(lambda v: "background-color: lightgreen" if v == "🔔" else "", subset=["Alerta"]), use_container_width=True)

            if df_filtrado["Alerta"].str.contains("🔔").any():
                st.success("Moedas com RSI ≤ 30 e Tendência de Alta destacadas!")
            else:
                st.info("Nenhuma moeda com alerta no momento.")
        else:
            st.warning("Nenhum resultado disponível com os filtros aplicados.")
