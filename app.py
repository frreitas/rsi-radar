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
st.set_page_config(
    page_title="Crypto Analyst Pro",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# --- Estilos CSS ---
st.markdown("""
<style>
:root {
    --primary: #4f46e5;
    --secondary: #06b6d4;
    --dark: #1e293b;
    --light: #f8fafc;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
}

/* Layout Principal */
.main {
    max-width: 1400px;
    padding: 2rem 3rem;
}

/* Cabeçalhos */
h1 {
    color: var(--dark);
    font-weight: 800;
    text-align: center;
    margin-bottom: 0.5rem;
}
h2 {
    color: var(--primary);
    border-bottom: 2px solid var(--primary);
    padding-bottom: 0.5rem;
    margin-top: 1.5rem;
}
h3 {
    color: var(--dark);
    font-weight: 600;
}

/* Cards e Contêineres */
.card {
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    background: white;
    transition: transform 0.2s, box-shadow 0.2s;
}
.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.12);
}

/* Botões */
.stButton>button {
    border-radius: 8px !important;
    padding: 0.5rem 1.25rem !important;
    font-weight: 500 !important;
}
.stButton>button.primary {
    background-color: var(--primary) !important;
}

/* Filtros */
.filter-section {
    background-color: #f1f5f9;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
}

/* Tabelas */
.stDataFrame {
    border-radius: 8px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
}

/* Abas */
.stTabs [role="tablist"] {
    gap: 0.5rem !important;
}
.stTabs [role="tab"] {
    border-radius: 8px !important;
    padding: 0.75rem 1.5rem !important;
    font-weight: 500 !important;
    background: #f1f5f9 !important;
}
.stTabs [aria-selected="true"] {
    background: var(--primary) !important;
    color: white !important;
}

/* Responsividade */
@media (max-width: 768px) {
    .main {
        padding: 1rem;
    }
    .stTabs [role="tab"] {
        padding: 0.5rem 1rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

# --- Cache de Dados ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_top_cryptos(limit=100):
    """Obtém as principais criptomoedas por capitalização de mercado"""
    url = f"https://min-api.cryptocompare.com/data/top/mktcapfull?limit={limit}&tsym=USD"
    try:
        response = requests.get(url)
        data = response.json().get("Data", [])
        return sorted([
            f"{coin['CoinInfo']['FullName']} ({coin['CoinInfo']['Name']})" 
            for coin in data
            if coin['CoinInfo'].get('Name')
        ])
    except Exception as e:
        st.error(f"Erro ao buscar criptomoedas: {str(e)}")
        return []

@st.cache_data(ttl=600, show_spinner=False)
def get_crypto_data(symbol, endpoint="histoday", limit=200):
    """Obtém dados históricos de uma criptomoeda"""
    url = f"https://min-api.cryptocompare.com/data/v2/{endpoint}?fsym={symbol}&tsym=USD&limit={limit}"
    try:
        response = requests.get(url)
        data = response.json().get("Data", {}).get("Data", [])
        
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        df["time"] = pd.to_datetime(df["time"], unit='s')
        df = df.set_index("time")
        
        # Padronizar colunas numéricas
        numeric_cols = ['open', 'high', 'low', 'close', 'volumefrom', 'volumeto']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        df = df.rename(columns={'volumeto': 'volume'}).dropna()
        return df
        
    except Exception as e:
        st.error(f"Erro ao buscar dados de {symbol}: {str(e)}")
        return pd.DataFrame()

# --- Funções de Análise ---
def calculate_indicators(df, ema_periods=(8, 21, 50)):
    """Calcula todos os indicadores técnicos para um DataFrame de preços"""
    if df.empty or len(df) < max(ema_periods):
        return None
    
    close = df['close']
    volume = df['volume']
    
    # Médias Móveis
    ema_fast = ta_trend.EMAIndicator(close, window=ema_periods[0]).ema_indicator().iloc[-1]
    ema_medium = ta_trend.EMAIndicator(close, window=ema_periods[1]).ema_indicator().iloc[-1]
    ema_slow = ta_trend.EMAIndicator(close, window=ema_periods[2]).ema_indicator().iloc[-1]
    
    # Momentum
    rsi = ta_momentum.RSIIndicator(close, window=14).rsi().iloc[-1]
    rsi_status = "Sobrevendido" if rsi < 30 else "Sobrecomprado" if rsi > 70 else "Neutro"
    
    # Volume
    volume_status = "Alto" if volume.iloc[-1] > volume.quantile(0.75) else "Normal"
    
    # Tendência
    trend = "Alta" if ema_fast > ema_medium > ema_slow else "Baixa" if ema_fast < ema_medium < ema_slow else "Lateral"
    
    return {
        'Preço': close.iloc[-1],
        'Variação': ((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100) if len(df) > 1 else 0,
        'Volume': volume.iloc[-1],
        'Volume Médio': volume.mean(),
        'RSI': rsi,
        'Status RSI': rsi_status,
        'EMA Rápida': ema_fast,
        'EMA Média': ema_medium,
        'EMA Lenta': ema_slow,
        'Tendência': trend,
        'Status Volume': volume_status
    }

# --- Funções de Visualização ---
def create_candlestick_chart(df, title):
    """Cria um gráfico de candlestick com EMAs"""
    fig = go.Figure()
    
    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Preço',
        increasing_line_color='#10b981',
        decreasing_line_color='#ef4444'
    ))
    
    # EMAs
    for period, color in zip([8, 21, 50], ['#FFA500', '#636EFA', '#00B5B8']):
        ema = ta_trend.EMAIndicator(df['close'], window=period).ema_indicator()
        fig.add_trace(go.Scatter(
            x=df.index,
            y=ema,
            name=f'EMA {period}',
            line=dict(color=color, width=1.5),
            opacity=0.8
        ))
    
    fig.update_layout(
        title=title,
        xaxis_rangeslider_visible=False,
        height=500,
        hovermode="x unified",
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    return fig

def create_technical_indicators(df):
    """Cria gráficos de indicadores técnicos"""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                       vertical_spacing=0.1,
                       row_heights=[0.6, 0.4])
    
    # RSI
    rsi = ta_momentum.RSIIndicator(df['close'], window=14).rsi()
    fig.add_trace(go.Scatter(
        x=df.index, y=rsi,
        name='RSI', line=dict(color='#7C4DFF')
    ), row=1, col=1)
    
    fig.add_hline(y=30, line_dash="dash", line_color="#10b981",
                  annotation_text="Sobrevendido", row=1, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#ef4444",
                  annotation_text="Sobrecomprado", row=1, col=1)
    
    # MACD
    macd = ta_trend.MACD(df['close'])
    fig.add_trace(go.Scatter(
        x=df.index, y=macd.macd(),
        name='MACD', line=dict(color='#4f46e5')
    ), row=2, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=macd.macd_signal(),
        name='Sinal', line=dict(color='#f59e0b')
    ), row=2, col=1)
    fig.add_trace(go.Bar(
        x=df.index, y=macd.macd_diff(),
        name='Histograma', marker_color='#d1d5db'
    ), row=2, col=1)
    
    fig.update_layout(
        height=600,
        showlegend=True,
        hovermode="x unified",
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

# --- Interface Principal ---
def main():
    st.title("🚀 Crypto Analyst Pro")
    st.markdown("""
    <p style='text-align: center; color: #64748b; margin-bottom: 2rem;'>
    Ferramenta completa de análise técnica e filtragem de criptomoedas
    </p>
    """, unsafe_allow_html=True)
    
    # Inicializar sessão
    if 'analyzed_coins' not in st.session_state:
        st.session_state.analyzed_coins = {}
    
    # --- Seção de Filtragem ---
    with st.expander("🔍 FILTRAR MOEDAS", expanded=True):
        with st.container():
            col1, col2, col3 = st.columns(3)
            
            with col1:
                timeframe = st.selectbox(
                    "Período",
                    ["1h", "4h", "1d", "1w"],
                    index=2,
                    help="Selecione o intervalo temporal para análise"
                )
                
                price_range = st.slider(
                    "Faixa de Preço (USD)",
                    0.0, 100000.0, (0.0, 100000.0),
                    step=0.1,
                    format="%.2f"
                )
                
            with col2:
                trend_options = st.multiselect(
                    "Tendência",
                    ["Alta", "Baixa", "Lateral"],
                    default=["Alta"],
                    help="Filtrar por direção da tendência"
                )
                
                volume_options = st.multiselect(
                    "Volume",
                    ["Alto", "Normal"],
                    default=["Alto"],
                    help="Filtrar por nível de volume"
                )
                
            with col3:
                rsi_options = st.multiselect(
                    "Situação RSI",
                    ["Sobrevendido", "Neutro", "Sobrecomprado"],
                    help="Filtrar por condição do RSI"
                )
                
                min_volume = st.number_input(
                    "Volume Mínimo (USD)",
                    min_value=0.0,
                    value=0.0,
                    step=1000.0
                )
        
        analyze_button = st.button(
            "🔍 ANALISAR MOEDAS",
            type="primary",
            use_container_width=True
        )
    
    # --- Processamento ---
    if analyze_button:
        with st.spinner("Analisando criptomoedas (isso pode levar alguns minutos)..."):
            start_time = time.time()
            all_coins = get_top_cryptos()
            
            # Barra de progresso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            filtered_coins = []
            
            for i, coin in enumerate(all_coins):
                try:
                    symbol = coin.split('(')[1][:-1]
                    
                    # Obter dados
                    endpoint, limit = ("histohour", 500) if timeframe in ['1h', '4h'] else ("histoday", 200)
                    df = get_crypto_data(symbol, endpoint, limit)
                    
                    if df.empty:
                        continue
                        
                    # Processar timeframe 4h
                    if timeframe == '4h':
                        df = df.resample('4H').agg({
                            'open': 'first',
                            'high': 'max',
                            'low': 'min',
                            'close': 'last',
                            'volume': 'sum'
                        }).dropna()
                    
                    # Calcular indicadores
                    indicators = calculate_indicators(df)
                    if not indicators:
                        continue
                        
                    # Aplicar filtros
                    meets_criteria = all([
                        (not trend_options or indicators['Tendência'] in trend_options),
                        (not rsi_options or indicators['Status RSI'] in rsi_options),
                        (not volume_options or indicators['Status Volume'] in volume_options),
                        (price_range[0] <= indicators['Preço'] <= price_range[1]),
                        (indicators['Volume'] >= min_volume)
                    ])
                    
                    if meets_criteria:
                        filtered_coins.append({
                            'Moeda': coin,
                            'Símbolo': symbol,
                            **indicators,
                            'Dados': df
                        })
                    
                    # Atualizar progresso
                    progress = (i + 1) / len(all_coins)
                    progress_bar.progress(progress)
                    status_text.text(f"Processando... {i+1}/{len(all_coins)} moedas")
                    
                    # Pequena pausa para evitar sobrecarregar a API
                    time.sleep(0.1)
                    
                except Exception as e:
                    st.warning(f"Erro ao processar {coin}: {str(e)}")
                    continue
            
            st.session_state.analyzed_coins = {
                'timeframe': timeframe,
                'filtered_coins': filtered_coins,
                'analysis_time': time.time() - start_time
            }
            
            progress_bar.empty()
            status_text.empty()
    
    # --- Exibição de Resultados ---
    if st.session_state.analyzed_coins and st.session_state.analyzed_coins['filtered_coins']:
        results = st.session_state.analyzed_coins
        timeframe = results['timeframe']
        filtered_coins = results['filtered_coins']
        
        st.success(f"""
        ✅ **{len(filtered_coins)} moedas** encontradas com os critérios selecionados 
        (Tempo de análise: {results['analysis_time']:.2f} segundos)
        """)
        
        # Tabs para diferentes visualizações
        tab1, tab2, tab3 = st.tabs(["📊 Lista de Moedas", "📈 Análise Detalhada", "🎯 Top Oportunidades"])
        
        with tab1:
            # Tabela de resultados
            summary_df = pd.DataFrame([{
                'Moeda': coin['Moeda'],
                'Preço (USD)': f"${coin['Preço']:,.2f}",
                'Variação (%)': f"{coin['Variação']:+.2f}%",
                'RSI': f"{coin['RSI']:.1f}",
                'Status RSI': coin['Status RSI'],
                'Tendência': coin['Tendência'],
                'Volume (USD)': f"${coin['Volume']:,.0f}"
            } for coin in filtered_coins])
            
            st.dataframe(
                summary_df,
                height=min(600, 45 * len(filtered_coins) + 45),
                use_container_width=True,
                column_config={
                    "Preço (USD)": st.column_config.NumberColumn(format="$%.2f"),
                    "Variação (%)": st.column_config.NumberColumn(format="%+.2f%%"),
                    "RSI": st.column_config.NumberColumn(format="%.1f"),
                    "Volume (USD)": st.column_config.NumberColumn(format="$%.0f")
                }
            )
            
            # Opção para exportar dados
            st.download_button(
                "⬇️ Exportar para CSV",
                summary_df.to_csv(index=False).encode('utf-8'),
                "moedas_filtradas.csv",
                "text/csv",
                use_container_width=True
            )
        
        with tab2:
            if filtered_coins:
                selected_coin = st.selectbox(
                    "Selecione uma moeda para análise detalhada",
                    [coin['Moeda'] for coin in filtered_coins],
                    index=0
                )
                
                coin_data = next((c for c in filtered_coins if c['Moeda'] == selected_coin), None)
                
                if coin_data:
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.plotly_chart(
                            create_candlestick_chart(
                                coin_data['Dados'],
                                f"{selected_coin} - Gráfico de Velas ({timeframe})"
                            ),
                            use_container_width=True
                        )
                    
                    with col2:
                        st.plotly_chart(
                            create_technical_indicators(coin_data['Dados']),
                            use_container_width=True
                        )
                    
                    # Métricas detalhadas
                    with st.expander("📌 Métricas Detalhadas"):
                        cols = st.columns(4)
                        cols[0].metric("Preço Atual", f"${coin_data['Preço']:,.2f}")
                        cols[1].metric("Variação 24h", f"{coin_data['Variação']:+.2f}%")
                        cols[2].metric("RSI", f"{coin_data['RSI']:.1f}", coin_data['Status RSI'])
                        cols[3].metric("Volume", f"${coin_data['Volume']:,.0f}")
                        
                        cols = st.columns(3)
                        cols[0].metric("EMA Rápida (8)", f"${coin_data['EMA Rápida']:,.2f}")
                        cols[1].metric("EMA Média (21)", f"${coin_data['EMA Média']:,.2f}")
                        cols[2].metric("EMA Lenta (50)", f"${coin_data['EMA Lenta']:,.2f}")
        
        with tab3:
            st.subheader("🔥 Melhores Oportunidades")
            
            opportunities = sorted(
                filtered_coins,
                key=lambda x: (
                    -1 if x['Status RSI'] == "Sobrevendido" else 1,
                    -1 if x['Tendência'] == "Alta" else 1,
                    -x['RSI'] if x['Status RSI'] == "Sobrevendido" else x['RSI'],
                    -x['Volume']
                )
            )[:10]  # Top 10 oportunidades
            
            for i, coin in enumerate(opportunities, 1):
                with st.container():
                    cols = st.columns([1, 3, 2, 2, 2, 2])
                    
                    # Ranking
                    cols[0].markdown(f"<h3>{i}</h3>", unsafe_allow_html=True)
                    
                    # Moeda
                    cols[1].markdown(f"""
                    <h4>{coin['Moeda']}</h4>
                    <small>{coin['Tendência']} | Volume: ${coin['Volume']:,.0f}</small>
                    """, unsafe_allow_html=True)
                    
                    # Preço e variação
                    cols[2].metric("Preço", f"${coin['Preço']:,.2f}", f"{coin['Variação']:+.2f}%")
                    
                    # RSI
                    rsi_color = "#10b981" if coin['Status RSI'] == "Sobrevendido" else "#ef4444" if coin['Status RSI'] == "Sobrecomprado" else "#64748b"
                    cols[3].markdown(f"""
                    <div style="background-color:{rsi_color}20; border-radius:8px; padding:0.5rem;">
                        <small>RSI</small><br>
                        <strong style="color:{rsi_color}">{coin['RSI']:.1f}</strong>
                        <small style="color:{rsi_color}">({coin['Status RSI']})</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # EMAs
                    ema_trend = "up" if coin['EMA Rápida'] > coin['EMA Média'] > coin['EMA Lenta'] else "down"
                    cols[4].markdown(f"""
                    <div>
                        <small>EMAs (8/21/50)</small><br>
                        <strong>${coin['EMA Rápida']:,.2f}</strong> → 
                        <strong>${coin['EMA Média']:,.2f}</strong> → 
                        <strong>${coin['EMA Lenta']:,.2f}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Botão de análise
                    cols[5].button(
                        "Analisar",
                        key=f"analyze_{coin['Símbolo']}_{i}",
                        on_click=lambda c=coin: st.session_state.update({'selected_coin': c}),
                        use_container_width=True
                    )
                    
                    st.divider()
    
    elif st.session_state.analyzed_coins:
        st.warning("Nenhuma moeda encontrada com os critérios selecionados.")
    
    # --- Rodapé ---
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #64748b; margin-top: 2rem;">
        <small>Crypto Analyst Pro v1.0 - Ferramenta de análise técnica para criptomoedas</small><br>
        <small>© 2023 - Dados fornecidos por CryptoCompare API</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
