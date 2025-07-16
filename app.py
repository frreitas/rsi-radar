import streamlit as st
import pandas as pd
import requests
import ta.momentum as ta_momentum
import ta.trend as ta_trend
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time

# Configuração da página
st.set_page_config(page_title="Análise Técnica de Criptomoedas", layout="wide")

# --- Estilo CSS ---
css = """
<style>
.main .block-container {
    max-width: 1200px;
    padding: 1rem 2rem;
}
h1 {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-weight: 700;
    color: #1e293b;
    text-align: center;
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
    max-width: 500px;
    margin: 30px auto;
    box-shadow: 0 5px 20px rgb(0 0 0 / 0.12);
    text-align: center;
    color: white;
}
.rec-compra { background-color: #28a745; }
.rec-acumular { background-color: #ffc107; color: #333; }
.rec-agardar { background-color: #fd7e14; }
.rec-venda { background-color: #dc3545; }
.rec-observar { background-color: #007bff; }
.rec-espera { background-color: #6c757d; }
.rec-vendaparcial { background-color: #6f42c1; }
.gauge-container {
    max-width: 500px;
    margin: 0 auto 35px auto;
}
.filter-section {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 25px;
}
.filter-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
}
@media (max-width: 768px) {
    .filter-grid {
        grid-template-columns: 1fr;
    }
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# --- Funções Auxiliares ---
@st.cache_data(ttl=3600)
def get_top_100_cryptos():
    """Busca as 100 principais criptomoedas"""
    url = "https://min-api.cryptocompare.com/data/top/mktcapfull?limit=100&tsym=USD"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()["Data"]
        return [f"{c['CoinInfo']['FullName']} ({c['CoinInfo']['Name']})" for c in data]
    except Exception as e:
        st.error(f"Erro ao buscar lista de criptomoedas: {e}")
        return ["Bitcoin (BTC)", "Ethereum (ETH)", "Binance Coin (BNB)"]

def extrair_simbolo(moeda_str):
    """Extrai o símbolo da criptomoeda"""
    return moeda_str.split("(")[-1].replace(")", "").strip()

@st.cache_data(ttl=600)
def get_timeframe_endpoint(timeframe):
    """Mapeia timeframe para endpoint da API"""
    if timeframe == "1h":
        return "histohour", 2000
    elif timeframe == "4h":
        return "histohour", 2000
    elif timeframe in ["1d", "1w", "1M"]:
        return "histoday", 730
    else:
        return "histoday", 730

@st.cache_data(ttl=600)
def get_crypto_data(symbol, endpoint="histoday", limit=200):
    """Busca dados históricos de criptomoedas"""
    url = f"https://min-api.cryptocompare.com/data/v2/{endpoint}?fsym={symbol}&tsym=USD&limit={limit}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()["Data"]["Data"]
        df = pd.DataFrame(data)
        df["time"] = pd.to_datetime(df["time"], unit='s')
        df = df.set_index("time")
        for col in ['open', 'high', 'low', 'close', 'volumefrom', 'volumeto']:
            if col in df.columns:
                df[col] = df[col].astype(float)
        df = df.rename(columns={'volumeto': 'volume'})
        return df
    except Exception as e:
        st.error(f"Erro ao buscar dados de {symbol}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=1800)
def get_fear_greed_index():
    """Obtém o índice de Medo e Ganância"""
    url = "https://api.alternative.me/fng/?limit=1"
    try:
        r = requests.get(url)
        r.raise_for_status()
        return int(r.json()["data"][0]["value"])
    except Exception as e:
        st.warning(f"Erro ao buscar índice: {e}")
        return None

def agrupar_4h_otimizado(df_horas):
    """Agrupa dados de 1h em 4h"""
    if df_horas.empty:
        return pd.DataFrame()
    return df_horas.resample('4H').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()

def classificar_rsi(rsi):
    """Classifica o valor do RSI"""
    if rsi < 30: return "Sobrevendido"
    elif rsi > 70: return "Sobrecomprado"
    else: return "Neutro"

def classificar_tendencia(ema_fast, ema_medium, ema_slow, ema_long):
    """Classifica a tendência com base nas EMAs"""
    if None in [ema_fast, ema_medium, ema_slow, ema_long]:
        return "Dados insuficientes"
    if ema_fast > ema_medium > ema_slow > ema_long:
        return "Alta consolidada"
    elif ema_fast < ema_medium < ema_slow < ema_long:
        return "Baixa consolidada"
    return "Neutra/Transição"

def classificar_volume(v_atual, v_medio):
    """Compara volume atual com médio"""
    return "Subindo" if v_atual >= v_medio else "Caindo"

def obter_recomendacao(tendencia, rsi_class, volume_class, macd_signal):
    """Gera recomendação com base nos indicadores"""
    if tendencia == "Alta consolidada":
        if rsi_class == "Sobrevendido" and volume_class == "Subindo" and macd_signal == "Compra":
            return "Compra Forte"
        elif rsi_class == "Sobrevendido" and macd_signal == "Compra":
            return "Compra"
        elif rsi_class == "Sobrecomprado":
            return "Venda Parcial"
    elif tendencia == "Baixa consolidada":
        if rsi_class == "Sobrecomprado" and macd_signal == "Venda":
            return "Venda"
    return "Aguardar"

def style_recomendacao_card(text):
    """Estiliza o card de recomendação"""
    styles = {
        "Compra Forte": ("Compra Forte", "rec-compra"),
        "Compra": ("Compra", "rec-compra"),
        "Venda": ("Venda", "rec-venda"),
        "Venda Parcial": ("Venda Parcial", "rec-vendaparcial"),
        "Aguardar": ("Aguardar", "rec-espera"),
    }
    return styles.get(text, (text, "rec-default"))

# --- Seção de Filtragem ---
def mostrar_filtros():
    """Exibe os controles de filtragem"""
    with st.expander("🔍 FILTRAR MOEDAS POR INDICADORES"):
        st.markdown('<div class="filter-section"><div class="filter-grid">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            timeframe_filter = st.selectbox("Timeframe", ["1h", "4h", "1d", "1w"], index=2, key="filter_timeframe")
            trend_filter = st.multiselect("Tendência", ["Alta consolidada", "Baixa consolidada", "Neutra/Transição"], key="filter_trend")
            
        with col2:
            rsi_filter = st.multiselect("RSI", ["Sobrevendido", "Neutro", "Sobrecomprado"], key="filter_rsi")
            price_min = st.number_input("Preço Mínimo (USD)", min_value=0.0, value=0.0, key="filter_pricemin")
            
        with col3:
            volume_filter = st.multiselect("Volume", ["Subindo", "Caindo"], key="filter_volume")
            price_max = st.number_input("Preço Máximo (USD)", min_value=0.0, value=100000.0, key="filter_pricemax")
        
        st.markdown('</div></div>', unsafe_allow_html=True)
        
        if st.button("🔎 APLICAR FILTROS", type="primary", use_container_width=True):
            return {
                'timeframe': timeframe_filter,
                'trend': trend_filter,
                'rsi': rsi_filter,
                'volume': volume_filter,
                'price_min': price_min,
                'price_max': price_max
            }
    return None

def filtrar_moedas(filters):
    """Filtra as moedas com base nos critérios"""
    with st.spinner(f"Processando {len(get_top_100_cryptos())} moedas..."):
        resultados = []
        progress_bar = st.progress(0)
        
        for i, moeda in enumerate(get_top_100_cryptos()):
            simbolo = extrair_simbolo(moeda)
            endpoint, limit = get_timeframe_endpoint(filters['timeframe'])
            df = get_crypto_data(simbolo, endpoint, limit)
            
            if df.empty:
                continue
                
            if filters['timeframe'] == "4h":
                df = agrupar_4h_otimizado(df)
                
            if len(df) < 50:  # Mínimo de dados
                continue
                
            # Calcular indicadores
            preco = df['close'].iloc[-1]
            variacao = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100 if len(df) > 1 else 0
            volume_atual = df['volume'].iloc[-1]
            volume_medio = df['volume'].mean()
            rsi = ta_momentum.RSIIndicator(df['close'], 14).rsi().iloc[-1]
            rsi_class = classificar_rsi(rsi)
            
            macd = ta_trend.MACD(df['close'])
            macd_signal = "Compra" if macd.macd().iloc[-1] > macd.macd_signal().iloc[-1] else "Venda"
            
            ema_fast = ta_trend.EMAIndicator(df['close'], 8).ema_indicator().iloc[-1]
            ema_medium = ta_trend.EMAIndicator(df['close'], 21).ema_indicator().iloc[-1]
            ema_long = ta_trend.EMAIndicator(df['close'], 200).ema_indicator().iloc[-1]
            tendencia = classificar_tendencia(ema_fast, ema_medium, ema_long, ema_long)
            
            volume_class = classificar_volume(volume_atual, volume_medio)
            
            # Aplicar filtros
            conditions = [
                not filters['price_min'] <= preco <= filters['price_max'],
                filters['trend'] and tendencia not in filters['trend'],
                filters['rsi'] and rsi_class not in filters['rsi'],
                filters['volume'] and volume_class not in filters['volume']
            ]
            
            if not any(conditions):  # Todos os critérios atendidos
                resultados.append({
                    'Moeda': moeda,
                    'Símbolo': simbolo,
                    'Preço': preco,
                    'Variação': variacao,
                    'RSI': rsi,
                    'Tendência': tendencia,
                    'Volume': volume_class,
                    'Data': df
                })
            
            progress_bar.progress((i + 1) / len(get_top_100_cryptos()))
        
        progress_bar.empty()
        return resultados

# --- Interface Principal ---
def main():
    st.title("📊 Análise Técnica de Criptomoedas")
    
    # Seção de Filtragem
    filtros = mostrar_filtros()
    resultados_filtro = None
    
    if filtros:
        resultados_filtro = filtrar_moedas(filtros)
        if resultados_filtro:
            st.success(f"✅ {len(resultados_filtro)} moedas atendem aos critérios")
            
            # Exibir resultados em uma tabela
            df_resultados = pd.DataFrame([{
                'Moeda': r['Moeda'],
                'Preço': f"${r['Preço']:,.2f}",
                'Variação': f"{r['Variação']:+.2f}%",
                'RSI': f"{r['RSI']:.1f}",
                'Tendência': r['Tendência'],
                'Volume': r['Volume']
            } for r in resultados_filtro])
            
            st.dataframe(df_resultados, height=300, use_container_width=True)
        else:
            st.warning("Nenhuma moeda atende aos critérios selecionados")

    # Seção de Análise Individual (original)
    st.divider()
    st.subheader("📈 Análise Individual")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        moeda_selecionada = st.selectbox(
            "Selecione a Moeda",
            get_top_100_cryptos(),
            key="main_coin_select",
            help="Escolha uma criptomoeda para análise detalhada"
        )
        simbolo = extrair_simbolo(moeda_selecionada)
    
    with col2:
        timeframe_analise = st.selectbox(
            "Timeframe Análise",
            ["1h", "4h", "1d", "1w"],
            index=2,
            key="main_timeframe"
        )
    
    with st.spinner("Carregando dados..."):
        endpoint_analise, limit_analise = get_timeframe_endpoint(timeframe_analise)
        df_analise_raw = get_crypto_data(simbolo, endpoint_analise, limit_analise)
        
        if df_analise_raw.empty:
            st.error("Dados insuficientes para análise")
            st.stop()
            
        if timeframe_analise == "4h":
            df_analise = agrupar_4h_otimizado(df_analise_raw)
        else:
            df_analise = df_analise_raw.copy()
            
        # Cálculo de indicadores (concatenei as funções para maior clareza)
        preco_atual = df_analise["close"].iloc[-1]
        variacao = ((df_analise["close"].iloc[-1] - df_analise["close"].iloc[-2]) / df_analise["close"].iloc[-2] * 100) if len(df_analise) > 1 else 0
        volume_atual = df_analise["volume"].iloc[-1]
        volume_medio = df_analise["volume"].mean()
        rsi = ta_momentum.RSIIndicator(df_analise["close"], 14).rsi().iloc[-1]
        rsi_class = classificar_rsi(rsi)
        
        macd = ta_trend.MACD(df_analise["close"])
        macd_line = macd.macd().iloc[-1]
        macd_signal_line = macd.macd_signal().iloc[-1]
        macd_diff = macd.macd_diff().iloc[-1]
        macd_signal = "Compra" if macd_line > macd_signal_line else "Venda"
        
        # Cálculo EMAs
        ema_periods = [8, 21, 50, 200]
        emas = {
            f"ema_{period}": ta_trend.EMAIndicator(df_analise["close"], period).ema_indicator().iloc[-1]
            for period in ema_periods
        } if len(df_analise) > max(ema_periods) else {f"ema_{period}": None for period in ema_periods}
        
        tendencia = classificar_tendencia(emas["ema_8"], emas["ema_21"], emas["ema_50"], emas["ema_200"])
        volume_class = classificar_volume(volume_atual, volume_medio)
        recomendacao = obter_recomendacao(tendencia, rsi_class, volume_class, macd_signal)
        texto_card, classe_card = style_recomendacao_card(recomendacao)

    # Exibição dos resultados
    col1, col2, col3 = st.columns(3)
    col1.metric("Preço Atual", f"${preco_atual:,.2f}", f"{variacao:+.2f}%")
    col2.metric("Volume 24h", f"${volume_atual:,.0f}", f"{'↑' if volume_class == 'Subindo' else '↓'} vs média")
    col3.metric("RSI (14)", f"{rsi:.1f}", rsi_class)

    st.markdown(f"""
    <div class="recommendation-card {classe_card}">
        {texto_card}
    </div>
    """, unsafe_allow_html=True)

    # Análise detalhada
    with st.expander("🔍 Detalhes da Análise", expanded=True):
        st.markdown(f"""
        <div class="analysis-container">
            <h4>Tendência: <strong>{tendencia}</strong></h4>
            <p>EMAs (8/21/50/200): {emas['ema_8']:.2f} / {emas['ema_21']:.2f} / {emas['ema_50']:.2f} / {emas['ema_200']:.2f}</p>
            
            <h4>Momentum:</h4>
            <p>RSI: {rsi:.1f} ({rsi_class}) | MACD: {macd_line:.2f} (Sinal: {macd_signal_line:.2f})</p>
            
            <h4>Volume:</h4>
            <p>Atual: ${volume_atual:,.0f} | Média: ${volume_medio:,.0f} | Status: {volume_class}</p>
        </div>
        """, unsafe_allow_html=True)

    # Gráficos
    tab1, tab2 = st.tabs(["Gráfico de Velas", "Indicadores Técnicos"])
    
    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df_analise.index,
            open=df_analise['open'],
            high=df_analise['high'],
            low=df_analise['low'],
            close=df_analise['close'],
            name='Preço'
        ))
        
        for period, color in zip([8, 21, 50, 200], ['orange', 'purple', 'blue', 'red']):
            if emas[f"ema_{period}"] is not None:
                fig.add_trace(go.Scatter(
                    x=df_analise.index,
                    y=ta_trend.EMAIndicator(df_analise["close"], period).ema_indicator(),
                    name=f'EMA {period}',
                    line=dict(color=color, width=1)
                ))
        
        fig.update_layout(
            title=f"{moeda_selecionada} - Gráfico de Velas ({timeframe_analise})",
            xaxis_rangeslider_visible=False,
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True)
        
        # RSI
        fig.add_trace(go.Scatter(
            x=df_analise.index,
            y=ta_momentum.RSIIndicator(df_analise["close"], 14).rsi(),
            name='RSI',
            line=dict(color='green')
        ), row=1, col=1)
        
        fig.add_hline(y=30, line_dash="dash", line_color="red", row=1, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=1, col=1)
        
        # MACD
        fig.add_trace(go.Scatter(
            x=df_analise.index,
            y=ta_trend.MACD(df_analise["close"]).macd(),
            name='MACD',
            line=dict(color='blue')
        ), row=2, col=1)
        
        fig.add_trace(go.Scatter(
            x=df_analise.index,
            y=ta_trend.MACD(df_analise["close"]).macd_signal(),
            name='Sinal',
            line=dict(color='orange')
        ), row=2, col=1)
        
        fig.update_layout(height=600, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    # Índice de Medo e Ganância
    st.divider()
    st.subheader("🌡️ Índice de Medo e Ganância do Mercado")
    
    fng = get_fear_greed_index()
    if fng is not None:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=fng,
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [0, 100]},
                'steps': [
                    {'range': [0, 25], 'color': "#FF0000"},
                    {'range': [25, 50], 'color': "#FFA500"},
                    {'range': [50, 75], 'color': "#90EE90"},
                    {'range': [75, 100], 'color': "#008000"}],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': fng}}))
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Não foi possível obter o índice no momento")

if __name__ == "__main__":
    main()
