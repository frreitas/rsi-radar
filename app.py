import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Análise Técnica Manual", layout="wide")
st.title("📊 Análise Técnica Manual - Criptomoedas")

# Inicializar estado
if "historico" not in st.session_state:
    st.session_state["historico"] = []

# Lista de moedas
moedas_disponiveis = {
    "Bitcoin (BTC)": "bitcoin",
    "Ethereum (ETH)": "ethereum",
    "Solana (SOL)": "solana",
    "XRP (XRP)": "ripple",
    "Cardano (ADA)": "cardano",
}

# Função para pegar o preço
def get_price(moeda_id):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": moeda_id, "vs_currencies": "usd"}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()[moeda_id]["usd"]
    except Exception as e:
        st.warning(f"Erro ao obter preço: {e}")
        return None

# Resetar app
if st.button("🧹 Limpar / Resetar tudo"):
    st.session_state["historico"] = []
    st.experimental_rerun()

# Seleção de moeda
st.subheader("🪙 Selecione a moeda")
col1, col2 = st.columns([1, 1])
with col1:
    moeda_nome = st.selectbox("Escolha uma moeda", list(moedas_disponiveis.keys()))
with col2:
    timeframe_rsi = st.selectbox("⏱️ Timeframe do RSI", ["1h", "4h", "1d", "1w", "1M"])

moeda_id = moedas_disponiveis[moeda_nome]
preco = get_price(moeda_id)

if preco:
    st.markdown(f"💰 **Preço atual de {moeda_nome}:** ${preco:,.2f}")
else:
    st.warning("Não foi possível obter o preço da moeda.")

# Dados técnicos manuais
st.subheader("✍️ Dados técnicos - Curto Prazo")

rsi = st.number_input("RSI atual", min_value=0.0, max_value=100.0, step=0.1)
num_emas = st.selectbox("Quantas EMAs do timeframe deseja usar?", [1, 2, 3])
ema_vals = []
for i in range(num_emas):
    val = st.number_input(f"Valor da EMA {i+1}", min_value=0.0, step=0.1)
    ema_vals.append(val)

# Dados técnicos - SEMANAL
st.subheader("📐 EMAs Semanais (8 / 21 / 56 / 200)")

col1, col2, col3, col4 = st.columns(4)
ema8 = col1.number_input("EMA 8 (semanal)", min_value=0.0, step=0.1)
ema21 = col2.number_input("EMA 21 (semanal)", min_value=0.0, step=0.1)
ema56 = col3.number_input("EMA 56 (semanal)", min_value=0.0, step=0.1)
ema200 = col4.number_input("EMA 200 (semanal)", min_value=0.0, step=0.1)

# Classificação RSI
if rsi <= 30:
    rsi_class = "Sobrevendida"
elif rsi >= 70:
    rsi_class = "Sobrecomprada"
else:
    rsi_class = "Neutra"

# Tendência curto prazo
tendencia = "Indefinida"
if len(ema_vals) >= 2:
    if ema_vals[0] > ema_vals[1]:
        tendencia = "Alta"
    elif ema_vals[0] < ema_vals[1]:
        tendencia = "Baixa"
    else:
        tendencia = "Neutra"
elif len(ema_vals) == 1:
    tendencia = "Indefinida (só 1 EMA)"

# Análise da estrutura semanal (EMAs)
estrutura_semanal = "Desalinhada"
if ema8 > ema21 > ema56 > ema200:
    estrutura_semanal = "Alta consolidada"
elif ema8 < ema21 < ema56 < ema200:
    estrutura_semanal = "Baixa consolidada"
else:
    estrutura_semanal = "Estrutura neutra / transição"

# Recomendação
if rsi <= 30 and tendencia == "Alta":
    recomendacao = "🟢 Bom sinal de entrada"
elif tendencia == "Alta" and rsi_class == "Neutra":
    recomendacao = "🟡 Tendência de alta, mas RSI neutro"
elif tendencia == "Baixa":
    recomendacao = "🔴 Tendência de baixa - cautela"
else:
    recomendacao = "⚪ Sem sinal claro no momento"

# Resultado
resultado = {
    "Moeda": moeda_nome,
    "Timeframe RSI": timeframe_rsi,
    "Preço Atual (USD)": round(preco, 2) if preco else "N/A",
    "RSI": rsi,
    "Classificação RSI": rsi_class,
    "Tendência Curto Prazo": tendencia,
    "Estrutura Semanal": estrutura_semanal,
    "EMA 8w": ema8,
    "EMA 21w": ema21,
    "EMA 56w": ema56,
    "EMA 200w": ema200,
    "Recomendação": recomendacao
}
for i, ema in enumerate(ema_vals):
    resultado[f"EMA Curto {i+1}"] = ema

# Salvar no histórico
if st.button("📌 Adicionar Análise ao Histórico"):
    st.session_state["historico"].append(resultado)
    st.success("Análise adicionada ao histórico!")

# Resultado atual
st.subheader("📋 Resultado da Análise Atual")
df_result = pd.DataFrame([resultado])
st.dataframe(df_result, use_container_width=True, hide_index=True)

# Download do CSV atual
csv = df_result.to_csv(index=False).encode("utf-8")
st.download_button("📥 Baixar Resultado como CSV", data=csv, file_name="analise_atual.csv", mime="text/csv")

# Histórico completo
if st.session_state["historico"]:
    st.subheader("📚 Histórico de Análises")
    df_hist = pd.DataFrame(st.session_state["historico"])
    st.dataframe(df_hist, use_container_width=True)

    csv_hist = df_hist.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Baixar Histórico como CSV", data=csv_hist, file_name="historico_analises.csv", mime="text/csv")
