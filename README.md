# 📊 Stock G2G Screener Dashboard

A comprehensive Streamlit-based dashboard for screening stocks using the Growth-to-Growth (G2G) valuation model.

## Features

✨ **Interactive Dashboard**
- Real-time stock data fetching from yfinance
- Add/remove stocks dynamically from the UI
- Beautiful, responsive design with custom CSS

📈 **Multiple Visualizations**
- G2G Score comparison bar chart
- Score breakdown by components (PE, PEG, Undervaluation)
- PE vs PEG scatter plot
- Price vs G2G Score relationship
- Detailed stock metrics table

🎯 **Stock Analysis**
- PE Ratio Analysis
- PEG (Price/Earnings-to-Growth) Ratio
- 52-week price range analysis
- Undervaluation detection

## Score Ranges

| Score | Meaning | Action |
|-------|---------|--------|
| 80-100 | Highly undervalued, strong fundamentals | 🟢 Strong Buy |
| 60-79 | Fairly valued, some undervaluation | 🟡 Watchlist |
| 40-59 | Slightly overpriced or average | 🔴 Hold/Avoid |
| 20-39 | Weak valuation, only 1 factor passed | ⚫ Keep Watching |
| 0-19 | Overvalued or bad fundamentals | ❌ Avoid |

## Installation

1. **Install Python 3.8+** (if not already installed)

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

## Running the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

## How to Use

### Adding Stocks
1. Look at the left sidebar under "⚙️ Stock Selection"
2. Enter a stock ticker (e.g., `INFY.NS`, `TCS.NS`, `RELIANCE.NS`)
3. Click "➕ Add Stock"
4. The dashboard will automatically fetch data and update

### Removing Stocks
1. Click the "❌" button next to any stock in the sidebar list
2. The dashboard will refresh automatically

### Understanding the Metrics

- **G2G Score**: Overall valuation score (0-100)
- **PE Score**: Based on PE ratio < 15 (0-30 points)
- **PEG Score**: Based on PEG ratio < 1 (0-30 points)
- **Underval Score**: Based on price vs 52-week average (0-40 points)

### Interpreting the Charts

1. **G2G Scores by Stock**: Compare overall scores across all stocks
2. **Score Breakdown**: See which factors contribute to each stock's score
3. **PE vs PEG Scatter**: Identify stocks with good growth valuations
4. **Price vs Score**: Find lower-priced high-scoring stocks

## Stock Ticker Format

For Indian stocks (NSE), use the following format:
- `RELIANCE.NS` - Reliance Industries
- `TCS.NS` - Tata Consultancy Services
- `INFY.NS` - Infosys
- `HDFC.NS` - HDFC Bank
- `BAJAJFINSV.NS` - Bajaj Financial Services

For international stocks:
- `AAPL` - Apple Inc.
- `MSFT` - Microsoft Corp.
- `GOOGL` - Alphabet Inc.

## Data Sources

- **Price & PE Data**: Yahoo Finance (yfinance)
- **Historical EPS Data**: Screener.in

## Disclaimer

⚠️ This tool is for **educational purposes only**. Always conduct your own research before making investment decisions. Past performance does not guarantee future results.

## Future Enhancements

- [ ] Save watchlist to CSV
- [ ] Email alerts for score changes
- [ ] Historical score tracking
- [ ] Sector-wise comparison
- [ ] Export reports to PDF
