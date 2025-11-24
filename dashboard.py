import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime
import requests

# Set page config
st.set_page_config(page_title="Stock G2G Screener", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .score-high {
        color: #00aa00;
        font-weight: bold;
    }
    .score-medium {
        color: #ffaa00;
        font-weight: bold;
    }
    .score-low {
        color: #dd0000;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'stocks_list' not in st.session_state:
    st.session_state.stocks_list = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFC.NS", "BAJAJFINSV.NS"]

# Helper functions
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        data = {
            "ticker": ticker,
            "price": info.get("currentPrice"),
            "pe": info.get("trailingPE"),
            "eps": info.get("trailingEps"),
            "marketCap": info.get("marketCap"),
            "pb": info.get("priceToBook"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh")
        }
        return data
    except:
        return None

def get_screener_eps(stock_id):
    try:
        url = f"https://www.screener.in/company/{stock_id}/consolidated/"
        df = pd.read_html(url)
        eps_table = df[2]
        eps_values = eps_table.iloc[0].tolist()[1:]
        return eps_values
    except:
        return None

def g2g_model(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        price = info.get("currentPrice")
        pe = info.get("trailingPE")
        eps_y = info.get("trailingEps")
        low52 = info.get("fiftyTwoWeekLow")
        pb = info.get("priceToBook")

        eps_screener = None
        try:
            eps_screener = get_screener_eps(ticker.split(".")[0])
        except:
            eps_screener = None

        eps_nse = None
        
        if eps_nse:
            eps_final = eps_nse
        elif eps_y:
            eps_final = eps_y
        else:
            eps_final = price / pe if pe and pe > 0 else None

        pe_val = 1 if pe and pe < 15 else 0
        underval = 1 if price and low52 and price < low52 * 1.2 else 0
        peg = pe / (eps_final * 5) if eps_final and eps_final > 0 and pe and pe > 0 else None
        peg_val = 1 if peg and peg < 1 else 0

        g2g = (pe_val*30) + (peg_val*30) + (underval*40)

        return {
            "Ticker": ticker,
            "Price": price,
            "PE": pe,
            "EPS": eps_final,
            "PEG": peg,
            "PE_Score": pe_val * 30,
            "PEG_Score": peg_val * 30,
            "Underval_Score": underval * 40,
            "G2G_Score": g2g
        }
    except:
        return None

def get_score_rating(score):
    if score >= 80:
        return "🟢 Strong Buy", "#00aa00"
    elif score >= 60:
        return "🟡 Watchlist", "#ffaa00"
    elif score >= 40:
        return "🔴 Hold/Avoid", "#dd0000"
    elif score >= 20:
        return "⚫ Keep Watching", "#666666"
    else:
        return "❌ Avoid", "#990000"

# Main UI
st.title("📊 Stock G2G Screener Dashboard")
st.markdown("**Growth-to-Growth Valuation Model** - Find Undervalued Stocks")

# Sidebar for adding stocks
st.sidebar.header("⚙️ Stock Selection")
st.sidebar.markdown("---")

# Input for new stock
new_stock = st.sidebar.text_input(
    "Add Stock Ticker (e.g., INFY.NS, TCS.NS)",
    placeholder="Enter ticker symbol"
).upper()

if st.sidebar.button("➕ Add Stock", use_container_width=True):
    if new_stock and new_stock not in st.session_state.stocks_list:
        st.session_state.stocks_list.append(new_stock)
        st.sidebar.success(f"✅ Added {new_stock}")
    elif new_stock in st.session_state.stocks_list:
        st.sidebar.warning(f"⚠️ {new_stock} already in list")
    else:
        st.sidebar.error("❌ Please enter a valid ticker")

st.sidebar.markdown("---")
st.sidebar.subheader("📋 Current Stocks")

# Display and manage stocks in sidebar
for idx, stock in enumerate(st.session_state.stocks_list):
    col1, col2 = st.sidebar.columns([3, 1])
    col1.text(stock)
    if col2.button("❌", key=f"remove_{idx}", use_container_width=True):
        st.session_state.stocks_list.pop(idx)
        st.rerun()

# Fetch and analyze data
st.markdown("---")
st.markdown("### 📈 Fetching Stock Data...")

progress_bar = st.progress(0)
results = []
errors = []

for idx, ticker in enumerate(st.session_state.stocks_list):
    result = g2g_model(ticker)
    if result:
        results.append(result)
    else:
        errors.append(ticker)
    progress_bar.progress((idx + 1) / len(st.session_state.stocks_list))

if not results:
    st.error("❌ No valid stock data found. Please check the ticker symbols.")
    st.stop()

results_df = pd.DataFrame(results).sort_values("G2G_Score", ascending=False)

# Score range legend
st.markdown("---")
st.markdown("### 📌 Score Range Guide")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown("""
    <div style="background-color: #00aa00; padding: 10px; border-radius: 5px; text-align: center; color: white;">
    <b>80-100</b><br>Strong Buy
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background-color: #ffaa00; padding: 10px; border-radius: 5px; text-align: center; color: white;">
    <b>60-79</b><br>Watchlist
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="background-color: #dd0000; padding: 10px; border-radius: 5px; text-align: center; color: white;">
    <b>40-59</b><br>Hold/Avoid
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div style="background-color: #666666; padding: 10px; border-radius: 5px; text-align: center; color: white;">
    <b>20-39</b><br>Keep Watching
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown("""
    <div style="background-color: #990000; padding: 10px; border-radius: 5px; text-align: center; color: white;">
    <b>0-19</b><br>Avoid
    </div>
    """, unsafe_allow_html=True)

# Charts
st.markdown("---")
st.markdown("### 📊 Stock Analysis Charts")

col1, col2 = st.columns(2)

with col1:
    # Overall G2G Score Chart
    fig_score = px.bar(
        results_df,
        x="Ticker",
        y="G2G_Score",
        title="G2G Scores by Stock",
        labels={"G2G_Score": "G2G Score"},
        color="G2G_Score",
        color_continuous_scale="RdYlGn"
    )
    fig_score.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_score, use_container_width=True)

with col2:
    # Score Breakdown Chart
    fig_breakdown = go.Figure()
    fig_breakdown.add_trace(go.Bar(
        x=results_df["Ticker"],
        y=results_df["PE_Score"],
        name="PE Score (30)"
    ))
    fig_breakdown.add_trace(go.Bar(
        x=results_df["Ticker"],
        y=results_df["PEG_Score"],
        name="PEG Score (30)"
    ))
    fig_breakdown.add_trace(go.Bar(
        x=results_df["Ticker"],
        y=results_df["Underval_Score"],
        name="Underval Score (40)"
    ))
    fig_breakdown.update_layout(
        barmode="stack",
        title="Score Breakdown by Component",
        height=400,
        yaxis_title="Score"
    )
    st.plotly_chart(fig_breakdown, use_container_width=True)

# PE vs PEG Chart
col1, col2 = st.columns(2)

with col1:
    fig_pe_peg = go.Figure()
    fig_pe_peg.add_trace(go.Scatter(
        x=results_df["PE"],
        y=results_df["PEG"],
        mode="markers+text",
        text=results_df["Ticker"],
        textposition="top center",
        marker=dict(
            size=results_df["G2G_Score"],
            color=results_df["G2G_Score"],
            colorscale="RdYlGn",
            showscale=True,
            colorbar=dict(title="G2G Score")
        )
    ))
    fig_pe_peg.update_layout(
        title="PE Ratio vs PEG Ratio",
        xaxis_title="PE Ratio",
        yaxis_title="PEG Ratio",
        height=400,
        hovermode="closest"
    )
    st.plotly_chart(fig_pe_peg, use_container_width=True)

with col2:
    fig_price = px.scatter(
        results_df,
        x="Price",
        y="G2G_Score",
        size="G2G_Score",
        color="G2G_Score",
        hover_data=["Ticker", "PE"],
        title="Stock Price vs G2G Score",
        color_continuous_scale="RdYlGn"
    )
    fig_price.update_layout(height=400)
    st.plotly_chart(fig_price, use_container_width=True)

# Detailed Table
st.markdown("---")
st.markdown("### 📋 Detailed Stock Analysis")

# Format the dataframe for display
display_df = results_df.copy()
display_df['Price'] = display_df['Price'].apply(lambda x: f"₹{x:.2f}" if x else "N/A")
display_df['PE'] = display_df['PE'].apply(lambda x: f"{x:.2f}" if x else "N/A")
display_df['EPS'] = display_df['EPS'].apply(lambda x: f"₹{x:.2f}" if x else "N/A")
display_df['PEG'] = display_df['PEG'].apply(lambda x: f"{x:.3f}" if x else "N/A")

# Rename columns for display
display_df = display_df[['Ticker', 'Price', 'PE', 'EPS', 'PEG', 'PE_Score', 'PEG_Score', 'Underval_Score', 'G2G_Score']]
display_df.columns = ['Ticker', 'Price', 'PE Ratio', 'EPS', 'PEG', 'PE (30)', 'PEG (30)', 'Underval (40)', 'Total Score']

st.dataframe(display_df, use_container_width=True, hide_index=True)

# Individual Stock Details
st.markdown("---")
st.markdown("### 🎯 Individual Stock Details")

selected_stock = st.selectbox("Select a stock for detailed analysis:", results_df["Ticker"].tolist())
stock_data = results_df[results_df["Ticker"] == selected_stock].iloc[0]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Current Price", f"₹{stock_data['Price']:.2f}")

with col2:
    st.metric("PE Ratio", f"{stock_data['PE']:.2f}")

with col3:
    st.metric("PEG Ratio", f"{stock_data['PEG']:.3f}")

with col4:
    rating, color = get_score_rating(stock_data['G2G_Score'])
    st.markdown(f"""
    <div style="background-color: {color}; padding: 20px; border-radius: 8px; text-align: center; color: white;">
    <h3 style="margin: 0;">G2G Score</h3>
    <h1 style="margin: 10px 0;">{stock_data['G2G_Score']:.0f}</h1>
    <p style="margin: 0;">{rating}</p>
    </div>
    """, unsafe_allow_html=True)

# Score breakdown
st.markdown("#### Score Breakdown:")
col1, col2, col3 = st.columns(3)

with col1:
    st.info(f"PE Factor Score: {stock_data['PE_Score']:.0f} / 30")

with col2:
    st.info(f"PEG Factor Score: {stock_data['PEG_Score']:.0f} / 30")

with col3:
    st.info(f"Undervaluation Score: {stock_data['Underval_Score']:.0f} / 40")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; font-size: 12px;">
<p>📊 Stock G2G Screener Dashboard | Data updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
<p>⚠️ Disclaimer: This tool is for educational purposes. Always do your own research before investing.</p>
</div>
""", unsafe_allow_html=True)

# Error handling
if errors:
    st.warning(f"⚠️ Could not fetch data for: {', '.join(errors)}")
