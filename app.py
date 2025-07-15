import streamlit as st
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

st.set_page_config(page_title="Radar RSI Cripto", layout="wide")
st.title("📊 Radar RSI com Tendência de Alta")
st.markdown("Análise das principais criptos com RSI, EMAs e CoinGecko como fonte de dados.")

# ===== CONFIGURAÇÕES =====
intervalo = st.selectbox("⏱️ Intervalo", ["1h", "4h", "1d"], index=0)
limite_velas = 100
limite_moedas = st.selectbox("🏆 Top moedas", [20, 50, 100], index=2)
atualizar = st.button("🔄 Atualizar agora")

# ===== API: COINGECKO (TOP COINS) =====
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

# ===== API: COINGECKO (MARKET CHART) =====
def get_coingecko_market_chart(cg_id, days):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{cg_id}/market_chart"
        res = requests.get(url, params={"vs_currency":"usd", "days":days}, timeout=10)
        res.raise_for_status()
        prices = res.json()["prices"]
        if not prices or len(prices) < 50:
            return None
        df = pd.DataFrame(prices, columns=["timestamp", "close"])
        df["close"] = df["close"].astype(float)
        return df
    except Exception as e:
        st.error(f"Erro no CoinGecko (market_chart) para {cg_id}: {e}")
        return None

# ===== CLASSIFICAÇÕES =====
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

# ===== ANÁLISE INDIVIDUAL =====
def analisar(cg_id, preco_atual, variacao_dia):
    dias_equivalentes = {"1h":1, "4h":7, "1d":14}
    df = get_coingecko_market_chart(cg_id, dias_equivalentes[intervalo])
    if df is None or len(df) < 50:
        return None

    try:
        rsi = RSIIndicator(df["close"]).rsi().iloc[-1]
        ema20 = EMAIndicator(df["close"], window=20).ema_indicator().iloc[-1]
        ema50 = EMAIndicator(df["close"], window=50).ema_indicator().iloc[-1]

        tendencia = classificar_tendencia(ema20, ema50)
        alerta = "🔔" if rsi <= 30 and tendencia == "Alta" else ""

        return {
            "Moeda": cg_id.upper(),
            "Preço US$": round(preco_atual, 4),
            "Variação (%)": round(variacao_dia or 0, 2),
            "RSI": round(rsi, 2),
            "Classificação RSI": classificar_rsi(rsi),
            "Tendência": tendencia,
            "Alerta": alerta
        }
    except Exception as e:
        st.error(f"Erro ao analisar {cg_id.upper()}: {e}")
        return None

# ===== EXECUÇÃO PRINCIPAL =====
if atualizar:
    with st.spinner("🔍 Analisando criptomoedas..."):
        coins = get_top_coins(limit=limite_moedas)
        tarefas = [
            (coin["id"], coin["current_price"], coin.get("price_change_percentage_24h", 0))
            for coin in coins
        ]

        resultados = []
        status = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_id = {executor.submit(analisar, *args): args[0] for args in tarefas}
            for future in future_to_id:
                cg_id = future_to_id[future]
                try:
                    res = future.result()
                    if res:
                        resultados.append(res)
                        status.append({"Moeda": cg_id.upper(), "Status": "✅ Sucesso"})
                    else:
                        status.append({"Moeda": cg_id.upper(), "Status": "❌ Erro na análise"})
                except Exception as e:
                    status.append({"Moeda": cg_id.upper(), "Status": f"❌ Exceção: {e}"})

    # ===== TABELA DE STATUS =====
    st.subheader("📦 Status da Análise")
    st.dataframe(pd.DataFrame(status), use_container_width=True)

    # ===== RESULTADOS =====
    if resultados:
        df = pd.DataFrame(resultados)

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
