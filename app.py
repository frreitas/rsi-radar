import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Análise Técnica Manual", layout="wide")
st.title("📊 Análise Técnica Manual - Criptomoedas")

# Inicializar histórico
if "historico" not in st.session_state:
    st.session_state["historico"] = []

# Lista de moedas pré-definidas
moedas_disponiveis = {
    "Bitcoin (BTC)": "bitcoin",
    "Ethereum (ETH)": "ethereum",
    "Solana (SOL)": "solana",
    "XRP (XRP)": "ripple",
    "Cardano (ADA)": "cardano",
}

# Cache com TTL para evitar rate limit da CoinGecko
@st.cache_data(ttl=600)
def get_precos_coin_gecko():
    ids = ",".join(moedas_disponiveis.values())
    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": ids, "vs_currencies": "usd"}
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.warning(f"Erro ao obter preços da CoinGecko: {e}")
        return {}

# Botão de reset
if st.button("🧹 Limpar / Resetar tudo"):
    st.session_state["historico"] = []
    st.experimental_rerun()

# ===== Seleção de moeda =====
st.subheader("🪙 Selecione a moeda para análise")

col1, col2 = st.columns([1, 1])
with col1:
    moeda_nome = st.selectbox("Escolha uma moeda", list(moedas_disponiveis.keys()))
with col2:
    timeframe_rsi = st.selectbox("⏱️ Timeframe do RSI", ["1h", "4h", "1d", "1w", "1M"])

moeda_id = moedas_disponiveis[moeda_nome]
precos = get_precos_coin_gecko()
preco = precos.get(moeda_id, {}).get("usd")

if preco:
    st.markdown(f"💰 **Preço atual de {moeda_nome}:** ${preco:,.2f}")
else:
    preco = st.number_input(f"Preço atual de {moeda_nome} (inserir manualmente)", min_value=0.0, step=0.01)

# ===== RSI manual =====
st.subheader("📈 RSI atual")
rsi = st.number_input("Valor do RSI", min_value=0.0, max_value=100.0, step=0.1)

# Classificação RSI
if rsi <= 30:
    rsi_class = "Sobrevendida"
elif rsi >= 70:
    rsi_class = "Sobrecomprada"
else:
    rsi_class = "Neutra"

# ===== EMAs Semanais =====
st.subheader("📐 EMAs SEMANAIS (usadas sempre no gráfico semanal)")

col1, col2, col3, col4 = st.columns(4)
ema8 = col1.number_input("EMA 8", min_value=0.0, step=0.1)
ema21 = col2.number_input("EMA 21", min_value=0.0, step=0.1)
ema56 = col3.number_input("EMA 56", min_value=0.0, step=0.1)
ema200 = col4.number_input("EMA 200", min_value=0.0, step=0.1)

# Análise da estrutura semanal (EMAs)
if ema8 > ema21 > ema56 > ema200:
    estrutura = "Alta consolidada"
elif ema8 < ema21 < ema56 < ema200:
    estrutura = "Baixa consolidada"
else:
    estrutura = "Estrutura neutra / transição"

# Recomendação com base em RSI e estrutura
if rsi <= 30 and estrutura == "Alta consolidada":
    recomendacao = "🟢 Bom sinal de entrada"
elif estrutura == "Alta consolidada" and rsi_class == "Neutra":
    recomendacao = "🟡 Tendência forte, mas RSI neutro"
elif estrutura == "Baixa consolidada":
    recomendacao = "🔴 Tendência de baixa - Cautela"
else:
    recomendacao = "⚪ Sem sinal claro no momento"

# Monta resultado da análise
resultado = {
    "Moeda": moeda_nome,
    "Timeframe RSI": timeframe_rsi,
    "Preço Atual (USD)": round(preco, 2),
    "RSI": rsi,
    "Classificação RSI": rsi_class,
    "EMA 8w": ema8,
    "EMA 21w": ema21,
    "EMA 56w": ema56,
    "EMA 200w": ema200,
    "Estrutura Semanal": estrutura,
    "Recomendação": recomendacao
}

# Botão para adicionar ao histórico
if st.button("📌 Adicionar Análise ao Histórico"):
    st.session_state["historico"].append(resultado)
    st.success("Análise adicionada ao histórico!")

# Resultado atual
st.subheader("📋 Resultado da Análise Atual")
df_result = pd.DataFrame([resultado])
st.dataframe(df_result, use_container_width=True, hide_index=True)

# Download do CSV atual
csv_atual = df_result.to_csv(index=False).encode("utf-8")
st.download_button("📥 Baixar Resultado como CSV", data=csv_atual, file_name="analise_atual.csv", mime="text/csv")

# Histórico completo
if st.session_state["historico"]:
    st.subheader("📚 Histórico de Análises")
    df_hist = pd.DataFrame(st.session_state["historico"])
    st.dataframe(df_hist, use_container_width=True, hide_index=True)

    csv_hist = df_hist.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Baixar Histórico como CSV", data=csv_hist, file_name="historico_analises.csv", mime="text/csv")
