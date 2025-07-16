import streamlit as st
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.trend import MACD # MACD agora está em ta.trend
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Análise Técnica de Criptomoedas", layout="wide")

# --- Estilo CSS para visual limpo e profissional ---
st.markdown("""
<style>
.main .block-container {
    max-width: 1100px;
    padding: 1rem 2rem;
}
h1 {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-weight: 700;
    color: #1e293b;
}
.stMetric {
    border-radius: 10px;
    box-shadow: 0 2px 6px rgb(0 0 0 / 0.1);
    background: #f9fafb;
    padding: 15px 20px;
    margin-bottom: 15px;
}
.analysis-container {
    background: #f3f4f6;
    padding: 20px 25px;
    border-radius: 12px;
    box-shadow: 0 3px 8px rgb(0 0 0 / 0.08);
    margin-top: 15px;
}
.recommendation-card {
    border-radius: 14px;
    padding: 25px 30px;
    font-weight: 700;
    font-size: 28px;
    max-width: 400px;
    margin: 20px auto;
    box-shadow: 0 5px 20px rgb(0 0 0 / 0.12);
    text-align: center;
    color: white;
}
.rec-compra { background-color: #2d7a2d; }
.rec-acumular { background-color: #d1a939; }
.rec-agardar { background-color: #d96f18; }
.rec-venda { background-color: #b02a2a; }
.rec-observar { background-color: #2b5bb1; }
.rec-espera { background-color: #6b7280; }
.rec-vendaparcial { background-color: #db8f91; }
.rec-default { background-color: #6b7280; }
.gauge-container {
    max-width: 500px;
    margin: 0 auto 35px auto;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Análise Técnica de Criptomoedas")

# --- Funções auxiliares ---

@st.cache_data(ttl=3600)
def get_top_100_cryptos():
    """
    Busca as 100 principais criptomoedas por capitalização de mercado da API CryptoCompare.
    Os resultados são armazenados em cache por 1 hora.
    """
    url = "https://min-api.cryptocompare.com/data/top/mktcapfull?limit=100&tsym=USD"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()["Data"]
        return [f"{c['CoinInfo']['FullName']} ({c['CoinInfo']['Name']})" for c in data]
    except Exception as e:
        st.error(f"Erro ao buscar lista de criptomoedas: {e}. Usando lista padrão.")
        return ["Bitcoin (BTC)", "Ethereum (ETH)", "Solana (SOL)"]

def extrair_simbolo(moeda_str):
    """Extrai o símbolo da criptomoeda de uma string formatada."""
    return moeda_str.split("(")[-1].replace(")", "").strip()

@st.cache_data(ttl=600)
def get_timeframe_endpoint(timeframe):
    """
    Retorna o endpoint da API CryptoCompare e o limite de dados
    com base no timeframe selecionado.
    """
    if timeframe == "1h":
        return "histohour", 2000 # Aumentado para ter dados suficientes para 4h e gráficos
    elif timeframe == "4h":
        return "histohour", 2000 # Pegar dados de 1h e agrupar para 4h
    elif timeframe in ["1d", "1w", "1M"]:
        return "histoday", 730 # Aproximadamente 2 anos de dados diários
    else:
        return "histoday", 730

@st.cache_data(ttl=600)
def get_crypto_data(symbol, endpoint="histoday", limit=200):
    """
    Busca dados históricos de criptomoedas da API CryptoCompare.
    Os resultados são armazenados em cache por 10 minutos.
    """
    url = f"https://min-api.cryptocompare.com/data/v2/{endpoint}?fsym={symbol}&tsym=USD&limit={limit}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()["Data"]["Data"]
        df = pd.DataFrame(data)
        # Converter timestamp para datetime e definir como índice
        df["time"] = pd.to_datetime(df["time"], unit='s')
        df = df.set_index("time")
        # Converter colunas numéricas para float
        for col in ['open', 'high', 'low', 'close', 'volumefrom', 'volumeto']:
            if col in df.columns:
                df[col] = df[col].astype(float)
        df = df.rename(columns={'volumeto': 'volume'}) # Padronizar nome da coluna de volume
        return df
    except Exception as e:
        st.error(f"Erro ao buscar dados de {symbol} ({endpoint}, limit={limit}): {e}")
        return pd.DataFrame()

@st.cache_data(ttl=1800)
def get_fear_greed_index():
    """
    Busca o valor atual do Índice de Medo e Ganância da API alternative.me.
    Os resultados são armazenados em cache por 30 minutos.
    """
    url = "https://api.alternative.me/fng/?limit=1"
    try:
        r = requests.get(url)
        r.raise_for_status()
        valor = int(r.json()["data"][0]["value"])
        return valor
    except Exception as e:
        st.warning(f"Não foi possível obter o índice de Medo e Ganância: {e}")
        return None

def agrupar_4h_otimizado(df_horas):
    """
    Agrupa dados de 1h para 4h, alinhando os blocos de 4 horas
    com base em um offset (ex: 00:00, 04:00, 08:00, etc.).
    """
    if df_horas.empty:
        return pd.DataFrame()

    # Certificar-se de que o índice é datetime e está em ordem crescente
    df_horas = df_horas.sort_index()

    # Definir o offset para o agrupamento de 4h (ex: começar em 00:00, 04:00, etc.)
    # O 'origin' garante que o agrupamento seja alinhado a esses horários
    grouped = df_horas.resample('4H', origin='start_day').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna() # Remover períodos sem dados

    return grouped

def classificar_rsi(rsi):
    """Classifica o valor do RSI em Sobrevendido, Sobrecomprado ou Neutro."""
    if rsi < 30: return "Sobrevendido"
    elif rsi > 70: return "Sobrecomprado"
    else: return "Neutro"

def classificar_tendencia(ema_fast, ema_medium, ema_slow, ema_long):
    """
    Classifica a tendência com base na ordem das EMAs.
    Considera 4 EMAs para uma análise mais robusta.
    """
    if ema_fast > ema_medium > ema_slow > ema_long:
        return "Alta consolidada"
    elif ema_fast < ema_medium < ema_slow < ema_long:
        return "Baixa consolidada"
    return "Neutra/Transição"

def classificar_volume(v_atual, v_medio):
    """Compara o volume atual com o volume médio."""
    return "Subindo" if v_atual >= v_medio else "Caindo"

def obter_recomendacao(tendencia, rsi_class, volume_class, macd_signal, bb_signal):
    """
    Gera uma recomendação de negociação com base em múltiplos indicadores.
    Adicionado MACD e Bandas de Bollinger na lógica.
    """
    # Inicializa a recomendação padrão
    recomendacao = "Aguardar"

    # Lógica baseada na tendência principal
    if tendencia == "Alta consolidada":
        if rsi_class == "Sobrevendido" and volume_class == "Subindo" and macd_signal == "Compra":
            recomendacao = "Compra"
        elif rsi_class == "Neutro" and volume_class == "Subindo":
            recomendacao = "Acumular / Espera"
        elif rsi_class == "Sobrecomprado" and volume_class == "Subindo":
            recomendacao = "Aguardar correção"
        elif bb_signal == "Preço abaixo da banda inferior":
            recomendacao = "Observar reversão potencial (compra de risco)"
        elif bb_signal == "Preço acima da banda superior":
            recomendacao = "Aguardar correção (venda de risco)"

    elif tendencia == "Baixa consolidada":
        if rsi_class == "Sobrevendido" and volume_class == "Subindo" and macd_signal == "Compra":
            recomendacao = "Observar reversão potencial com stop curto"
        elif volume_class == "Caindo" or macd_signal == "Venda":
            recomendacao = "Venda / Evitar"
        elif rsi_class == "Neutro" and volume_class == "Subindo":
            recomendacao = "Observar cautelosamente"
        elif bb_signal == "Preço acima da banda superior":
            recomendacao = "Venda (oportunidade de short)"

    elif tendencia == "Neutra/Transição":
        if rsi_class == "Sobrevendido" and volume_class == "Subindo" and macd_signal == "Compra":
            recomendacao = "Observar"
        elif rsi_class == "Neutro" and volume_class == "Caindo":
            recomendacao = "Espera"
        elif rsi_class == "Sobrecomprado":
            if volume_class == "Subindo":
                recomendacao = "Venda parcial para quem já está comprado; observar topo para quem não está dentro"
            else:
                recomendacao = "Esperar topo confirmado"
        elif bb_signal == "Preço abaixo da banda inferior":
            recomendacao = "Observar (potencial compra em fundo)"
        elif bb_signal == "Preço acima da banda superior":
            recomendacao = "Observar (potencial venda em topo)"

    # Ajustes finos com base em MACD e BB se a recomendação ainda for "Aguardar" ou genérica
    if recomendacao == "Aguardar":
        if macd_signal == "Compra":
            recomendacao = "Aguardar confirmação (MACD compra)"
        elif macd_signal == "Venda":
            recomendacao = "Aguardar confirmação (MACD venda)"
        elif bb_signal == "Preço abaixo da banda inferior":
            recomendacao = "Aguardar (preço em zona de compra BB)"
        elif bb_signal == "Preço acima da banda superior":
            recomendacao = "Aguardar (preço em zona de venda BB)"

    return recomendacao

def style_recomendacao_card(text):
    """Mapeia o texto da recomendação para um estilo de cartão CSS."""
    styles = {
        "Compra": ("Compra Forte", "rec-compra"),
        "Acumular / Espera": ("Atenção", "rec-acumular"),
        "Aguardar correção": ("Aguardar", "rec-agardar"),
        "Venda / Evitar": ("Venda Forte", "rec-venda"),
        "Observar": ("Observar", "rec-observar"),
        "Espera": ("Espera", "rec-espera"),
        "Venda parcial para quem já está comprado; observar topo para quem não está dentro": ("Venda Parcial", "rec-vendaparcial"),
        "Observar reversão potencial com stop curto": ("Observar Reversão", "rec-observar"),
        "Observar cautelosamente": ("Observar Cautelosamente", "rec-observar"),
        "Esperar topo confirmado": ("Esperar Topo Confirmado", "rec-espera"),
        "Aguardar": ("Aguardar", "rec-default"),
        "Observar reversão potencial (compra de risco)": ("Compra de Risco", "rec-acumular"),
        "Aguardar correção (venda de risco)": ("Venda de Risco", "rec-agardar"),
        "Venda (oportunidade de short)": ("Venda Forte", "rec-venda"),
        "Aguardar confirmação (MACD compra)": ("Aguardar Compra", "rec-acumular"),
        "Aguardar confirmação (MACD venda)": ("Aguardar Venda", "rec-agardar"),
        "Aguardar (preço em zona de compra BB)": ("Aguardar Compra BB", "rec-acumular"),
        "Aguardar (preço em zona de venda BB)": ("Aguardar Venda BB", "rec-agardar"),
    }
    return styles.get(text, ("Desconhecido", "rec-default"))

# --- Interface ---

top_moedas = get_top_100_cryptos()
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    moeda_selecionada = st.selectbox("Selecione a Moeda", top_moedas)
    simbolo = extrair_simbolo(moeda_selecionada)
with col2:
    timeframe_analise = st.selectbox("Timeframe Análise (RSI, Gráfico)", ["1h", "4h", "1d", "1w"], index=2)
with col3:
    # Permitir que o usuário personalize os períodos das EMAs
    st.subheader("Configurações EMAs")
    ema_fast_period = st.number_input("EMA Rápida (períodos)", min_value=5, max_value=20, value=8, step=1)
    ema_medium_period = st.number_input("EMA Média (períodos)", min_value=15, max_value=30, value=21, step=1)
    ema_slow_period = st.number_input("EMA Lenta (períodos)", min_value=40, max_value=70, value=56, step=1)
    ema_long_period = st.number_input("EMA Longa (períodos)", min_value=150, max_value=250, value=200, step=1)


st.divider()
st.subheader("📈 Análise Técnica")

with st.spinner("Carregando dados e calculando indicadores..."):

    # Obter dados brutos para o timeframe de análise (RSI, Gráfico)
    endpoint_analise, limit_analise = get_timeframe_endpoint(timeframe_analise)
    df_analise_raw = get_crypto_data(simbolo, endpoint_analise, limit_analise)

    if df_analise_raw.empty:
        st.error("Dados insuficientes para análise. Tente novamente mais tarde ou selecione outro timeframe/moeda.")
        st.stop()

    # Ajuste para 4h - agrupar dados de 1h em blocos de 4 horas
    if timeframe_analise == "4h":
        df_analise = agrupar_4h_otimizado(df_analise_raw)
    elif timeframe_analise == "1w":
        # Agrupar dados diários em semanais para análise
        df_analise = df_analise_raw.resample('W-MON').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
    else: # 1h, 1d
        df_analise = df_analise_raw.copy()

    if df_analise.empty or len(df_analise) < max(ema_long_period, 200): # Garantir dados suficientes para EMAs longas
        st.error(f"Dados insuficientes para o timeframe '{timeframe_analise}' ou para calcular todas as EMAs. Tente um timeframe maior ou outra moeda.")
        st.stop()

    # --- Cálculo de Indicadores ---

    # Preço atual e variação do dia (sempre baseado no último dado disponível, que pode ser do timeframe de análise)
    preco_atual = df_analise["close"].iloc[-1]
    # Para variação diária, idealmente precisaríamos do preço de 24h atrás, mas usaremos o penúltimo do timeframe atual
    # Se o timeframe for 1h, será a variação da última hora. Se for 1d, será a variação do dia anterior.
    if len(df_analise) > 1:
        preco_anterior = df_analise["close"].iloc[-2]
        variacao_periodo = (preco_atual - preco_anterior) / preco_anterior * 100
    else:
        variacao_periodo = 0.0

    # Volume atual e médio (do timeframe de análise)
    volume_atual = df_analise["volume"].iloc[-1]
    volume_medio = df_analise["volume"].mean()

    # RSI no timeframe selecionado
    rsi_valor = RSIIndicator(close=df_analise["close"], window=14).rsi().iloc[-1]
    rsi_class = classificar_rsi(rsi_valor)

    # MACD no timeframe selecionado
    macd_indicator = MACD(close=df_analise["close"])
    macd_line = macd_indicator.macd().iloc[-1]
    macd_signal_line = macd_indicator.macd_signal().iloc[-1]
    macd_diff = macd_indicator.macd_diff().iloc[-1] # Histograma
    macd_signal = "Neutro"
    if macd_line > macd_signal_line and macd_diff > 0:
        macd_signal = "Compra"
    elif macd_line < macd_signal_line and macd_diff < 0:
        macd_signal = "Venda"

    # Bandas de Bollinger no timeframe selecionado
    bb_indicator = BollingerBands(close=df_analise["close"])
    bb_upper = bb_indicator.bollinger_hband().iloc[-1]
    bb_lower = bb_indicator.bollinger_lband().iloc[-1]
    bb_signal = "Neutro"
    if preco_atual > bb_upper:
        bb_signal = "Preço acima da banda superior"
    elif preco_atual < bb_lower:
        bb_signal = "Preço abaixo da banda inferior"

    # EMAs no timeframe de análise (usando os períodos configurados pelo usuário)
    # Garantir que há dados suficientes para o cálculo da EMA mais longa
    if len(df_analise) < ema_long_period:
        st.warning(f"Dados insuficientes para calcular EMA de {ema_long_period} períodos. A análise de tendência pode não ser precisa.")
        ema_fast, ema_medium, ema_slow, ema_long = [None]*4
        tendencia = "Dados insuficientes para EMAs"
    else:
        ema_fast = EMAIndicator(close=df_analise["close"], window=ema_fast_period).ema_indicator().iloc[-1]
        ema_medium = EMAIndicator(close=df_analise["close"], window=ema_medium_period).ema_indicator().iloc[-1]
        ema_slow = EMAIndicator(close=df_analise["close"], window=ema_slow_period).ema_indicator().iloc[-1]
        ema_long = EMAIndicator(close=df_analise["close"], window=ema_long_period).ema_indicator().iloc[-1]
        tendencia = classificar_tendencia(ema_fast, ema_medium, ema_slow, ema_long)

    volume_class = classificar_volume(volume_atual, volume_medio)
    recomendacao = obter_recomendacao(tendencia, rsi_class, volume_class, macd_signal, bb_signal)
    texto_card, classe_card = style_recomendacao_card(recomendacao)

# --- Exibição de Métricas e Análise ---

col_preco, col_volume_atual, col_volume_medio = st.columns(3)
col_preco.metric("💵 Preço Atual (USD)", f"${preco_atual:,.2f}", f"{variacao_periodo:.2f}% ({timeframe_analise})")
col_volume_atual.metric("📊 Volume Atual", f"${volume_atual:,.2f}")
col_volume_medio.metric("📉 Volume Médio", f"${volume_medio:,.2f}")

st.divider()

with st.container():
    st.markdown(f"""
    <div class="analysis-container">
        <h4 style="color:#334155;">Tendência (EMAs {ema_fast_period}/{ema_medium_period}/{ema_slow_period}/{ema_long_period} {timeframe_analise}): <strong>{tendencia}</strong></h4>
        <h4 style="color:#334155;">RSI ({timeframe_analise}): <strong>{rsi_valor:.2f} – {rsi_class}</strong></h4>
        <h4 style="color:#334155;">MACD ({timeframe_analise}): <strong>Linha: {macd_line:.2f}, Sinal: {macd_signal_line:.2f}, Histograma: {macd_diff:.2f} – {macd_signal}</strong></h4>
        <h4 style="color:#334155;">Bandas de Bollinger ({timeframe_analise}): <strong>Superior: {bb_upper:.2f}, Inferior: {bb_lower:.2f} – {bb_signal}</strong></h4>
        <h4 style="color:#334155;">Volume Atual vs. Médio: <strong>{volume_class}</strong></h4>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div class="recommendation-card {classe_card}">
    {texto_card}
</div>
""", unsafe_allow_html=True)

# --- Gráfico de Velas com Indicadores ---
st.subheader(f"Gráfico de Velas ({timeframe_analise})")

# Certificar-se de que o DataFrame tem dados suficientes para o gráfico
if not df_analise.empty and len(df_analise) > 1:
    fig_chart = go.Figure(data=[go.Candlestick(
        x=df_analise.index,
        open=df_analise['open'],
        high=df_analise['high'],
        low=df_analise['low'],
        close=df_analise['close'],
        name='Preço'
    )])

    # Adicionar EMAs ao gráfico principal
    if ema_fast is not None: # Verifica se as EMAs foram calculadas
        fig_chart.add_trace(go.Scatter(x=df_analise.index, y=EMAIndicator(close=df_analise["close"], window=ema_fast_period).ema_indicator(),
                                   mode='lines', name=f'EMA {ema_fast_period}', line=dict(color='orange', width=1)))
        fig_chart.add_trace(go.Scatter(x=df_analise.index, y=EMAIndicator(close=df_analise["close"], window=ema_medium_period).ema_indicator(),
                                   mode='lines', name=f'EMA {ema_medium_period}', line=dict(color='purple', width=1)))
        fig_chart.add_trace(go.Scatter(x=df_analise.index, y=EMAIndicator(close=df_analise["close"], window=ema_slow_period).ema_indicator(),
                                   mode='lines', name=f'EMA {ema_slow_period}', line=dict(color='brown', width=1)))
        fig_chart.add_trace(go.Scatter(x=df_analise.index, y=EMAIndicator(close=df_analise["close"], window=ema_long_period).ema_indicator(),
                                   mode='lines', name=f'EMA {ema_long_period}', line=dict(color='blue', width=1)))

    # Adicionar Bandas de Bollinger ao gráfico principal
    fig_chart.add_trace(go.Scatter(x=df_analise.index, y=bb_indicator.bollinger_hband(),
                                   mode='lines', name='BB Superior', line=dict(color='gray', width=1, dash='dash')))
    fig_chart.add_trace(go.Scatter(x=df_analise.index, y=bb_indicator.bollinger_lband(),
                                   mode='lines', name='BB Inferior', line=dict(color='gray', width=1, dash='dash')))

    fig_chart.update_layout(
        xaxis_rangeslider_visible=False,
        title=f'{moeda_selecionada} - Gráfico de Velas',
        height=500,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    # Criar subplots para RSI e MACD
    fig_subplots = go.Figure()

    # Subplot RSI
    fig_subplots.add_trace(go.Scatter(x=df_analise.index, y=RSIIndicator(close=df_analise["close"], window=14).rsi(),
                                      mode='lines', name='RSI', line=dict(color='green')), row=1, col=1)
    fig_subplots.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Sobrecomprado", annotation_position="top right", row=1, col=1)
    fig_subplots.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Sobrevendido", annotation_position="bottom right", row=1, col=1)
    fig_subplots.update_yaxes(range=[0, 100], title_text="RSI", row=1, col=1)

    # Subplot MACD
    fig_subplots.add_trace(go.Scatter(x=df_analise.index, y=macd_indicator.macd(),
                                      mode='lines', name='MACD Linha', line=dict(color='blue')), row=2, col=1)
    fig_subplots.add_trace(go.Scatter(x=df_analise.index, y=macd_indicator.macd_signal(),
                                      mode='lines', name='MACD Sinal', line=dict(color='red')), row=2, col=1)
    fig_subplots.add_trace(go.Bar(x=df_analise.index, y=macd_indicator.macd_diff(),
                                   name='MACD Histograma', marker_color='gray'), row=2, col=1)
    fig_subplots.update_yaxes(title_text="MACD", row=2, col=1)

    # Layout dos subplots
    fig_subplots.update_layout(
        height=400,
        showlegend=True,
        margin=dict(l=20, r=20, t=20, b=20),
        grid=dict(rows=2, columns=1, pattern="independent", row_heights=[0.5, 0.5])
    )

    st.plotly_chart(fig_chart, use_container_width=True)
    st.plotly_chart(fig_subplots, use_container_width=True)
else:
    st.info("Não há dados suficientes para exibir o gráfico de velas.")


# --- Gráfico Gauge Fear & Greed Index (abaixo da análise) ---

fng_valor = get_fear_greed_index()

if fng_valor is not None:
    fig_fng = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = fng_valor,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Índice de Medo e Ganância"},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "#1f77b4"},
            'steps' : [
                {'range': [0, 25], 'color': "#d62728"}, # Extreme Fear
                {'range': [25, 50], 'color': "#ff7f0e"}, # Fear
                {'range': [50, 75], 'color': "#bcbd22"}, # Greed
                {'range': [75, 100], 'color': "#2ca02c"}], # Extreme Greed
            'threshold' : {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': fng_valor}}))

    st.markdown('<div class="gauge-container">', unsafe_allow_html=True)
    st.plotly_chart(fig_fng, use_container_width=True)
    st.markdown("""
    <div style="text-align:center; font-size: 14px; color: #64748b; margin-bottom: 35px;">
        0-25: Medo Extremo | 25-50: Medo | 50-75: Ganância | 75-100: Ganância Extrema
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("Não foi possível obter o índice de Medo e Ganância no momento.")

