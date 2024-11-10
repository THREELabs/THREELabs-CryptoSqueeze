import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from coinbase_analyzer import CoinbaseAnalyzer

# Configure Streamlit page settings
st.set_page_config(
    page_title="Crypto Analysis Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
    <style>
    .stProgress .st-bo {
        background-color: #2ea043;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.4rem;
    }
    .market-up {
        color: #2ea043;
    }
    .market-down {
        color: #cf222e;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state if not already done
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = CoinbaseAnalyzer()

# Page Header
st.title("Cryptocurrency Market Analysis")
st.markdown("""
    This dashboard provides real-time analysis of cryptocurrency markets using Coinbase data.
    Monitor key metrics, identify opportunities, and track market movements.
""")

# Sidebar Configuration
st.sidebar.title("Analysis Settings")

# Volume filter in sidebar
min_volume = st.sidebar.number_input(
    "Minimum 24h Volume (USD)",
    min_value=10000,
    max_value=10000000,
    value=100000,
    step=10000,
    help="Filter out trading pairs with 24h volume below this threshold"
)

# Trading pair selection
available_pairs = st.session_state.analyzer.recommended_pairs
selected_pairs = st.sidebar.multiselect(
    "Select Trading Pairs",
    options=available_pairs,
    default=available_pairs[:2],
    help="Choose which trading pairs to analyze in detail"
)

# Add time range selector
time_ranges = {
    "24 Hours": 1,
    "7 Days": 7,
    "30 Days": 30
}
selected_range = st.sidebar.selectbox(
    "Time Range",
    options=list(time_ranges.keys()),
    index=1
)

# Add refresh button in sidebar
if st.sidebar.button("🔄 Refresh Data"):
    st.experimental_rerun()

# Add last update time in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Error handling wrapper
def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            return None
    return wrapper

# Market Overview Section
def create_market_metrics_card(title, value, change=None, prefix="$", suffix=""):
    col1, col2 = st.columns([2, 1])
    with col1:
        st.metric(
            title,
            f"{prefix}{value:,.2f}{suffix}",
            f"{change:+.2f}%" if change is not None else None,
            delta_color="normal" if change is None else ("inverse" if title == "Volatility" else "normal")
        )

@handle_errors
def display_market_overview():
    st.header("Market Overview")
    
    with st.expander("📊 Market Overview", expanded=True):
        # Create three columns for key metrics
        col1, col2, col3 = st.columns(3)
        
        try:
            # Get BTC stats as market indicator
            btc_stats = st.session_state.analyzer.get_product_stats("BTC-USD")
            if btc_stats:
                with col1:
                    create_market_metrics_card(
                        "BTC Price",
                        float(btc_stats.get('last', 0)),
                        float(btc_stats.get('price_change_24h', 0))
                    )
                
                with col2:
                    create_market_metrics_card(
                        "24h Volume",
                        float(btc_stats.get('volume', 0))
                    )
                
                with col3:
                    create_market_metrics_card(
                        "24h Range",
                        float(btc_stats.get('high', 0)) - float(btc_stats.get('low', 0))
                    )
            else:
                st.warning("Unable to fetch market overview data")
        except Exception as e:
            st.error(f"Error loading market overview: {str(e)}")

@handle_errors
def scan_opportunities():
    st.header("Market Opportunities")
    
    with st.expander("🎯 Opportunity Scanner", expanded=True):
        # Add scan button
        if st.button("🔍 Scan for Opportunities"):
            with st.spinner("Scanning market for opportunities..."):
                opportunities = st.session_state.analyzer.scan_for_opportunities(min_volume=min_volume)
                
                if opportunities:
                    # Create a DataFrame for better display
                    opp_data = []
                    for opp in opportunities:
                        indicators = [k for k, v in opp['indicators'].items() if v]
                        opp_data.append({
                            'Trading Pair': opp['product_id'],
                            'Current Price': f"${opp['price']:,.2f}",
                            '24h Volume': f"${opp['volume']:,.2f}",
                            'Signals': ', '.join(indicators)
                        })
                    
                    df = pd.DataFrame(opp_data)
                    
                    # Display opportunities in a clean table
                    st.dataframe(
                        df,
                        column_config={
                            'Trading Pair': st.column_config.TextColumn('Trading Pair', width=150),
                            'Current Price': st.column_config.TextColumn('Current Price', width=150),
                            '24h Volume': st.column_config.TextColumn('24h Volume', width=150),
                            'Signals': st.column_config.TextColumn('Signals', width=300)
                        },
                        hide_index=True
                    )
                    
                    # Add detailed cards for each opportunity
                    st.subheader("Detailed Analysis")
                    for opp in opportunities:
                        with st.expander(f"{opp['product_id']} Analysis"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.metric("Current Price", f"${opp['price']:,.2f}")
                                st.metric("24h Volume", f"${opp['volume']:,.2f}")
                            
                            with col2:
                                st.write("**Active Signals:**")
                                for indicator, active in opp['indicators'].items():
                                    if active:
                                        st.markdown(f"- {indicator.replace('_', ' ').title()}")
                else:
                    st.info("No opportunities found matching the current criteria. Try adjusting the minimum volume filter.")

def plot_price_chart(product_id, df):
    """Create an interactive price chart using Plotly"""
    fig = go.Figure()
    
    # Add candlestick chart
    fig.add_trace(go.Candlestick(
        x=df['time'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name=product_id
    ))
    
    # Add volume bars
    fig.add_trace(go.Bar(
        x=df['time'],
        y=df['volume'],
        name='Volume',
        yaxis='y2',
        opacity=0.3
    ))
    
    # Update layout
    fig.update_layout(
        title=f'{product_id} Price Chart',
        yaxis_title='Price (USD)',
        yaxis2=dict(
            title='Volume',
            overlaying='y',
            side='right'
        ),
        xaxis_title='Date',
        height=500,
        yaxis=dict(side='left'),
        xaxis=dict(type='date'),
        showlegend=True
    )
    
    return fig

# Execute main page sections
try:
    display_market_overview()
    st.markdown("---")
    scan_opportunities()
except Exception as e:
    st.error(f"An error occurred while loading the market overview: {str(e)}")
    st.warning("Please try refreshing the page or adjust the analysis settings.")

@handle_errors
def display_detailed_analysis():
    if not selected_pairs:
        st.info("Please select one or more trading pairs from the sidebar to view detailed analysis.")
        return

    st.header("Detailed Pair Analysis")

    for pair in selected_pairs:
        with st.spinner(f"Analyzing {pair}..."):
            analysis = st.session_state.analyzer.detailed_pair_analysis(pair)
            
            if not analysis:
                st.error(f"Unable to analyze {pair}. Please try again later.")
                continue
            
            with st.expander(f"📊 {pair} Analysis", expanded=True):
                # Price and Volume Overview
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(
                        "Current Price",
                        f"${analysis['current_price']:,.2f}"
                    )
                with col2:
                    st.metric(
                        "24h Volume",
                        f"${analysis['volume_24h']:,.2f}"
                    )
                with col3:
                    momentum = analysis['analysis']['price_momentum']
                    st.metric(
                        "Momentum",
                        momentum['ema_trend'].title(),
                        f"{momentum['strength']:,.2f}%"
                    )
                with col4:
                    trend = analysis['analysis']['trend_strength']
                    st.metric(
                        "Trend Strength",
                        trend['direction'].title(),
                        f"{trend['strength']:,.2f}"
                    )

                # Technical Analysis Metrics
                st.subheader("Technical Analysis")
                
                # Create tabs for different timeframes
                timeframe_tabs = st.tabs(["Short Term (24h)", "Medium Term (7d)", "Long Term (30d)"])
                
                for tab, (timeframe, metrics) in zip(timeframe_tabs, analysis['metrics'].items()):
                    with tab:
                        m_col1, m_col2, m_col3 = st.columns(3)
                        
                        with m_col1:
                            st.metric(
                                "RSI",
                                f"{metrics['rsi']:.2f}",
                                delta_color="inverse"
                            )
                            
                        with m_col2:
                            st.metric(
                                "Volume Trend",
                                f"{metrics['volume_trend']:.2f}x"
                            )
                            
                        with m_col3:
                            st.metric(
                                "Volatility",
                                f"{metrics['volatility']:.2f}",
                                delta_color="inverse"
                            )

                # Support and Resistance Levels
                st.subheader("Price Levels")
                levels_col1, levels_col2 = st.columns(2)
                
                with levels_col1:
                    st.metric(
                        "Support Level",
                        f"${analysis['analysis']['support_level']:,.2f}"
                    )
                
                with levels_col2:
                    st.metric(
                        "Resistance Level",
                        f"${analysis['analysis']['resistance_level']:,.2f}"
                    )

                # Get historical data for charting
                end = datetime.now()
                start = end - timedelta(days=time_ranges[selected_range])
                historical_data = st.session_state.analyzer.get_historical_data(
                    pair, start, end,
                    granularity=3600 if time_ranges[selected_range] <= 7 else 86400
                )
                
                if historical_data:
                    df = pd.DataFrame(
                        historical_data,
                        columns=['time', 'open', 'high', 'low', 'close', 'volume']
                    )
                    df['time'] = pd.to_datetime(df['time'], unit='s')
                    df = df.sort_values('time')
                    
                    # Plot interactive chart
                    st.plotly_chart(
                        plot_price_chart(pair, df),
                        use_container_width=True
                    )
                else:
                    st.warning("Unable to load historical data for charting.")

                # Market Signals
                st.subheader("Market Signals")
                signals = []
                
                # RSI signals
                rsi = analysis['metrics']['short_term']['rsi']
                if rsi < 30:
                    signals.append(("Oversold (RSI)", "⚠️", "Assets may be undervalued"))
                elif rsi > 70:
                    signals.append(("Overbought (RSI)", "⚠️", "Assets may be overvalued"))
                
                # Volume signals
                vol_trend = analysis['metrics']['short_term']['volume_trend']
                if vol_trend > 2:
                    signals.append(("High Volume", "📈", "Volume is significantly above average"))
                elif vol_trend < 0.5:
                    signals.append(("Low Volume", "📉", "Volume is significantly below average"))
                
                # Trend signals
                trend_str = analysis['analysis']['trend_strength']['strength']
                if trend_str > 25:
                    signals.append(("Strong Trend", "➡️", f"Current {analysis['analysis']['trend_strength']['direction']} trend is strong"))
                
                # Display signals
                if signals:
                    for signal, icon, desc in signals:
                        st.markdown(f"{icon} **{signal}**: {desc}")
                else:
                    st.info("No significant market signals detected")

# Main execution
try:
    # Only run detailed analysis if pairs are selected
    if selected_pairs:
        display_detailed_analysis()
        
        # Add data disclaimer
        st.markdown("---")
        st.caption("""
            **Disclaimer**: This analysis is for informational purposes only and should not be considered as financial advice. 
            Cryptocurrency markets are highly volatile and past performance is not indicative of future results.
            Always conduct your own research before making investment decisions.
        """)
except Exception as e:
    st.error("An error occurred while running the analysis. Please try again.")
    st.exception(e)

# Add footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p style='color: #666; font-size: 14px;'>
            Built with Streamlit • Last updated: {}</p>
    </div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
