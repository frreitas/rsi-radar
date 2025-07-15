import streamlit as st
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

st.set_page_config(page_title="Radar RSI Cripto", layout="wide")
st.title("📊 Radar RSI com Tendência de Alta")
st.markdown("Análise das principais criptos com fallback da Binance para CoinGecko.")

# ===== Configurações =====
intervalo = st.selectbox("⏱️ Intervalo", ["1h", "4h", "1d"], index=0)
limite_velas = 100
limite_moedas = st.selectbox("🏆 Top moedas", [20, 50, 100], index=2)
atualizar = st.button("🔄 Atualizar agora")

# ===== APIs =====
@st.cache_data(ttl=600)
def get_top_coins(limit=100):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": limit, "page":1}
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"Erro ao obter moedas do CoinGecko: {e}")
        return []

def get_binance_klines(symbol):
    try:
        res = requests.get("https://api.binance.com/api/v3/klines",
                           params={"symbol":symbol,"interval":intervalo,"limit":limite_velas}, timeout=10)
        if res.status_code != 200:
            return None
        data = res.json()
        df = pd.DataFrame(data, columns=["timestamp","open","high","low","close","volume","close_time",
                                         "quote_asset_volume","number_of_trades","taker_buy_base","taker_buy_quote","ignore"])
        df["close"]=df["close"].astype(float)
        return df
    except:
        return None

def get_coingecko_ohlc(cg_id):
    days_map={"1h":1,"4h":7,"1d":14}
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{cg_id}/ohlc"
        params = {"vs_currency":"usd", "days": days_map[intervalo]}
        res = requests.get(url, params=params, timeout=10)
        if res.status_code != 200:
            return None
        df = pd.DataFrame(res.json(), columns=["timestamp","open","high","low","close"])
        df["close"]=df["close"].astype(float)
        return df
    except:
        return None

def classificar_rsi(rsi):
    if rsi <= 30:
        return "Sobrevendida"
    elif rsi >= 70:
        return "Sobrecomprada"
    else:
        return "Neutra"

def classificar_tendencia(ema20, ema50):
    if ema20 > ema50:
        return "Alta"
    elif ema20 < ema50:
        return "Baixa"
    else:
        return "Neutra"

def analisar(symbol, cg_id, current_price, price_change):
    try:
        df = get_binance_klines(symbol)
        if df is None:
            df = get_coingecko_ohlc(cg_id)
        if df is None or len(df) < 50:
            return None

        rsi = RSIIndicator(df["close"]).rsi().iloc[-1]
        ema20 = EMAIndicator(df["close"], window=20).ema_indicator().iloc[-1]
        ema50 = EMAIndicator(df["close"], window=50).ema_indicator().iloc[-1]

        tendencia = classificar_tendencia(ema20, ema50)
        alerta = "🔔" if rsi <= 30 and tendencia == "Alta" else ""

        return {
            "Moeda": cg_id.upper(),
            "Preço US$": round(current_price, 4),
            "Variação (%)": round(price_change or 0, 2),
            "RSI": round(rsi, 2),
            "Classificação RSI": classificar_rsi(rsi),
            "Tendência": tendencia,
            "Alerta": alerta
        }
    except Exception as e:
        print(f"Erro ao analisar {cg_id.upper()}: {e}")
        return None

# ===== Execução =====
if atualizar:
    with st.spinner("🔍 Analisando criptomoedas..."):
        coins = get_top_coins(limit=limite_moedas)
        symbols = [
            (coin["symbol"].upper() + "USDT", coin["id"], coin["current_price"], coin.get("price_change_percentage_24h", 0))
            for coin in coins
        ]

        results = []
        status = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_symbol = {
                executor.submit(analisar, *args): args[1] for args in symbols
            }
            for future in future_to_symbol:
                cg_id = future_to_symbol[future]
                try:
                    res = future.result()
                    if res:
                        results.append(res)
                        status.append({"Moeda": cg_id.upper(), "Status": "✅ Sucesso"})
                    else:
                        status.append({"Moeda": cg_id.upper(), "Status": "❌ Erro na análise"})
                except Exception as e:
                    status.append({"Moeda": cg_id.upper(), "Status": f"❌ Exceção: {e}"})

    st.subheader("📦 Status da Análise")
    st.dataframe(pd.DataFrame(status), use_container_width=True)

    if results:
        df = pd.DataFrame(results)

        filtro_rsi = st.multiselect(
            "📌 Filtrar por classificação RSI",
            options=["Sobrevendida", "Neutra", "Sobrecomprada"],
            default=["Sobrevendida", "Neutra", "Sobrecomprada"]
        )
        df_filtrado = df[df["Classificação RSI"].isin(filtro_rsi)]

        st.subheader("📋 Resultados da Análise")
        st.dataframe(df_filtrado, use_container_width=True)

        alertas = df_filtrado[df_filtrado["Alerta"] != ""]
        if not alertas.empty:
            st.subheader("🚨 Alertas de Oportunidade")
            st.dataframe(alertas, use_container_width=True)
        else:
            st.success("Nenhuma moeda com RSI ≤ 30 e tendência de alta.")
    else:
        st.warning("⚠️ Nenhum dado válido retornado.")
