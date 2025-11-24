from flask import Flask, render_template, request, jsonify
import pandas as pd
import yfinance as yf
import json
from datetime import datetime

app = Flask(__name__)

# Initialize default stocks
default_stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFC.NS", "BAJAJFINSV.NS"]

# Stock Sectors Database
stock_sectors = {
    # IT & Technology
    "TCS.NS": "IT & Technology",
    "INFY.NS": "IT & Technology",
    "WIPRO.NS": "IT & Technology",
    "HCLTECH.NS": "IT & Technology",
    "LTIM.NS": "IT & Technology",
    "TECHM.NS": "IT & Technology",
    
    # Banking & Financial Services
    "SBIN.NS": "Banking & Finance",
    "AXISBANK.NS": "Banking & Finance",
    "ICICIBANK.NS": "Banking & Finance",
    "HDFC.NS": "Banking & Finance",
    
    # Energy & Oil/Gas
    "RELIANCE.NS": "Energy & Oil/Gas",
    "POWERGRID.NS": "Energy & Oil/Gas",
    "TATASTEEL.NS": "Energy & Oil/Gas",
    
    # Automobiles
    "MARUTI.NS": "Automobiles",
    "TATAMOTORS.NS": "Automobiles",
    "BAJAJFINSV.NS": "Automobiles",
    
    # Pharmaceuticals & Healthcare
    "SUNPHARMA.NS": "Pharmaceuticals",
    "CIPLA.NS": "Pharmaceuticals",
    "LUPIN.NS": "Pharmaceuticals",
    
    # Consumer & FMCG
    "ITC.NS": "Consumer & FMCG",
    "ASIANPAINT.NS": "Consumer & FMCG",
    "NESTLEIND.NS": "Consumer & FMCG",
    
    # Telecom
    "BHARTIARTL.NS": "Telecom",
    "JIOTELECOM.NS": "Telecom",
    
    # Real Estate & Construction
    "DLF.NS": "Real Estate",
    "PRESTIGE.NS": "Real Estate",
    
    # US Stocks (International)
    "AAPL": "Technology (US)",
    "MSFT": "Technology (US)",
    "GOOGL": "Technology (US)",
    "AMZN": "Consumer (US)",
    "TSLA": "Automobiles (US)",
    "META": "Technology (US)",
    "NVDA": "Technology (US)",
}

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
        
        # Extract key metrics with proper null handling
        price = info.get("currentPrice")
        pe = info.get("trailingPE")
        eps_y = info.get("trailingEps")
        low52 = info.get("fiftyTwoWeekLow")
        high52 = info.get("fiftyTwoWeekHigh")
        pb = info.get("priceToBook")
        market_cap = info.get("marketCap")
        
        # Ensure we have valid numbers
        if not price or price <= 0:
            return None
            
        if not pe or pe <= 0:
            # Try to calculate PE if not available
            if eps_y and eps_y > 0:
                pe = price / eps_y
            else:
                pe = None
        
        if not eps_y or eps_y <= 0:
            # Fallback: Calculate EPS from price and PE
            if pe and pe > 0:
                eps_y = price / pe
            else:
                eps_y = None
        
        # Use the available EPS value
        eps_final = eps_y if (eps_y and eps_y > 0) else None
        
        # ===== METRIC 1: PE VALUATION (30 Points Max) =====
        pe_threshold = 15
        if pe and pe > 0:
            pe_val = 1 if pe < pe_threshold else 0
            pe_score = pe_val * 30
            pe_status = f"✅ Good (PE: {pe:.2f})" if pe < pe_threshold else f"❌ Expensive (PE: {pe:.2f})"
        else:
            pe_val = 0
            pe_score = 0
            pe_status = "⚠️ No Data"
        
        # ===== METRIC 2: PEG VALUATION (30 Points Max) =====
        if eps_final and eps_final > 0 and pe and pe > 0:
            peg = pe / (eps_final * 5)
            peg_threshold = 1.0
            peg_val = 1 if peg < peg_threshold else 0
            peg_score = peg_val * 30
            peg_status = f"✅ Growth-Adjusted ({peg:.3f})" if peg < peg_threshold else f"❌ Overvalued ({peg:.3f})"
        else:
            peg = None
            peg_val = 0
            peg_score = 0
            peg_status = "⚠️ Cannot Calculate"
        
        # ===== METRIC 3: 52-WEEK UNDERVALUATION (40 Points Max) =====
        if price and low52 and low52 > 0:
            underval_threshold = low52 * 1.2
            underval = 1 if price < underval_threshold else 0
            underval_score = underval * 40
            price_to_low = price / low52
            underval_status = f"✅ Undervalued ({price_to_low:.2f}x)" if price < underval_threshold else f"❌ High ({price_to_low:.2f}x)"
        else:
            underval = 0
            underval_score = 0
            price_to_low = None
            underval_status = "⚠️ No Data"
        
        # ===== FINAL G2G SCORE =====
        g2g_score = pe_score + peg_score + underval_score
        
        # Determine rating
        if g2g_score >= 100:
            rating = "🟢 Perfect - Strong Buy"
        elif g2g_score >= 70:
            rating = "🟡 Very Good - Watchlist"
        elif g2g_score >= 40:
            rating = "🟠 Moderate - Hold"
        elif g2g_score >= 20:
            rating = "🔴 Poor - Avoid"
        else:
            rating = "❌ Very Poor - Avoid"
        
        return {
            "Ticker": ticker,
            "Price": price,
            "PE": pe,
            "PE_Threshold": 15,
            "PE_Status": pe_status,
            "EPS_Final": eps_final,
            "PEG": peg,
            "PEG_Threshold": 1.0,
            "PEG_Status": peg_status,
            "Low52": low52,
            "High52": high52,
            "Price_to_Low_Ratio": price_to_low,
            "Underval_Status": underval_status,
            "PB_Ratio": pb,
            "Market_Cap": market_cap,
            "PE_Score": pe_score,
            "PE_Score_Max": 30,
            "PEG_Score": peg_score,
            "PEG_Score_Max": 30,
            "Underval_Score": underval_score,
            "Underval_Score_Max": 40,
            "G2G_Score": g2g_score,
            "G2G_Max": 100,
            "Rating": rating
        }
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return None

def get_score_rating(score):
    if score >= 80:
        return ("🟢 Strong Buy", "#00aa00")
    elif score >= 60:
        return ("🟡 Watchlist", "#ffaa00")
    elif score >= 40:
        return ("🔴 Hold/Avoid", "#dd0000")
    elif score >= 20:
        return ("⚫ Keep Watching", "#666666")
    else:
        return ("❌ Avoid", "#990000")

@app.route('/')
def index():
    results = []
    for ticker in default_stocks:
        result = g2g_model(ticker)
        if result:
            results.append(result)
    
    results_df = pd.DataFrame(results).sort_values("G2G_Score", ascending=False)
    results_html = results_df.to_html(classes='table table-striped table-bordered', index=False)
    
    return render_template('index.html', 
                         results=results_df.to_dict('records'),
                         results_html=results_html,
                         stocks=default_stocks,
                         updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/api/add-stock', methods=['POST'])
def add_stock():
    data = request.json
    ticker = data.get('ticker', '').upper()
    
    if not ticker:
        return jsonify({"success": False, "message": "Invalid ticker"}), 400
    
    try:
        result = g2g_model(ticker)
    except Exception as e:
        # Return the exception message to help debugging client-side
        try:
            info = yf.Ticker(ticker).info
        except Exception:
            info = None
        return jsonify({"success": False, "message": "Exception during analysis", "error": str(e), "info": info}), 500

    if not result:
        # Try to include raw info to help diagnose missing data
        try:
            info = yf.Ticker(ticker).info
        except Exception:
            info = None
        return jsonify({"success": False, "message": "Could not fetch data for ticker", "info": info}), 400
    
    # Add to session stocks
    if 'stocks_list' not in data or not isinstance(data.get('stocks_list'), list):
        stocks_list = default_stocks
    else:
        stocks_list = data['stocks_list']
    
    if ticker not in stocks_list:
        stocks_list.append(ticker)
    
    return jsonify({"success": True, "result": result, "stocks": stocks_list})

@app.route('/api/remove-stock', methods=['POST'])
def remove_stock():
    data = request.json
    ticker = data.get('ticker', '').upper()
    stocks_list = data.get('stocks_list', default_stocks).copy()
    
    if ticker in stocks_list:
        stocks_list.remove(ticker)
        return jsonify({"success": True, "stocks": stocks_list, "message": f"✅ {ticker} removed from dashboard"})
    
    return jsonify({"success": False, "message": "Stock not found"}), 400

@app.route('/api/ticker-suggestions', methods=['GET'])
def ticker_suggestions():
    query = request.args.get('q', '').upper()
    
    # Popular Indian stock tickers
    indian_stocks = [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFC.NS", "BAJAJFINSV.NS",
        "WIPRO.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS", "TATASTEEL.NS",
        "POWERGRID.NS", "SBIN.NS", "AXISBANK.NS", "ICICIBANK.NS", "LTIM.NS",
        "TECHM.NS", "ASIANPAINT.NS", "TATAMOTORS.NS", "BHARTIARTL.NS", "ITC.NS"
    ]
    
    # US stocks
    us_stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "V", "WMT"]
    
    all_stocks = indian_stocks + us_stocks
    
    if not query or len(query) < 1:
        return jsonify([])
    
    # Filter suggestions
    suggestions = [s for s in all_stocks if query in s][:10]
    return jsonify(suggestions)

@app.route('/api/analyze', methods=['GET'])
def analyze():
    tickers = request.args.get('tickers', '').split(',')
    results = []
    
    for ticker in tickers:
        ticker = ticker.strip().upper()
        if ticker:
            result = g2g_model(ticker)
            if result:
                results.append(result)
    
    results_df = pd.DataFrame(results).sort_values("G2G_Score", ascending=False)
    return jsonify(results_df.to_dict('records'))


@app.route('/api/check-ticker', methods=['GET'])
def check_ticker():
    """Diagnostic endpoint: returns raw yfinance info and G2G analysis (if possible)."""
    ticker = request.args.get('ticker', '').strip().upper()
    if not ticker:
        return jsonify({"success": False, "message": "No ticker provided"}), 400

    try:
        stock = yf.Ticker(ticker)
        info = stock.info
    except Exception as e:
        return jsonify({"success": False, "message": "yfinance error", "error": str(e)}), 500

    try:
        analysis = g2g_model(ticker)
    except Exception as e:
        analysis = None

    return jsonify({"success": True, "ticker": ticker, "info": info, "analysis": analysis})

@app.route('/api/sector-leaders', methods=['GET'])
def sector_leaders():
    """Get top performing companies in Indian market by sector based on G2G model"""
    
    # Comprehensive list of Indian stocks by sector
    sector_stocks_map = {
        "IT & Technology": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "LTIM.NS", "TECHM.NS"],
        "Banking & Finance": ["SBIN.NS", "AXISBANK.NS", "ICICIBANK.NS", "HDFC.NS", "KOTAKBANK.NS", "INDUSIND.NS"],
        "Energy & Oil/Gas": ["RELIANCE.NS", "POWERGRID.NS", "TATASTEEL.NS", "IOCL.NS"],
        "Automobiles": ["MARUTI.NS", "TATAMOTORS.NS", "BAJAJFINSV.NS", "EICHER.NS", "ASHOKLEYLAND.NS"],
        "Pharmaceuticals": ["SUNPHARMA.NS", "CIPLA.NS", "LUPIN.NS", "DIVISLAB.NS", "BIOCON.NS"],
        "Consumer & FMCG": ["ITC.NS", "ASIANPAINT.NS", "NESTLEIND.NS", "BRITANNIA.NS", "MARICO.NS"],
        "Telecom": ["BHARTIARTL.NS", "IDEA.NS", "VODAFONE.NS"],
        "Real Estate": ["DLF.NS", "PRESTIGE.NS", "LODHA.NS", "ADANIPORTS.NS"],
        "Utilities": ["POWERGRID.NS", "NIITTECH.NS"],
    }
    
    sector_results = {}
    
    for sector, tickers in sector_stocks_map.items():
        sector_results[sector] = []
        
        for ticker in tickers:
            try:
                result = g2g_model(ticker)
                if result:
                    result['Sector'] = sector
                    sector_results[sector].append(result)
            except:
                pass
        
        # Sort by G2G Score and get top 3
        if sector_results[sector]:
            sector_results[sector].sort(key=lambda x: x['G2G_Score'], reverse=True)
            sector_results[sector] = sector_results[sector][:3]
    
    return jsonify(sector_results)

@app.route('/api/top-performers', methods=['GET'])
def top_performers():
    """Get overall top 10 performing companies in Indian market"""
    
    all_indian_stocks = [
        "TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "LTIM.NS", "TECHM.NS",
        "SBIN.NS", "AXISBANK.NS", "ICICIBANK.NS", "HDFC.NS", "KOTAKBANK.NS", "INDUSIND.NS",
        "RELIANCE.NS", "POWERGRID.NS", "TATASTEEL.NS", "IOCL.NS",
        "MARUTI.NS", "TATAMOTORS.NS", "BAJAJFINSV.NS", "EICHER.NS", "ASHOKLEYLAND.NS",
        "SUNPHARMA.NS", "CIPLA.NS", "LUPIN.NS", "DIVISLAB.NS", "BIOCON.NS",
        "ITC.NS", "ASIANPAINT.NS", "NESTLEIND.NS", "BRITANNIA.NS", "MARICO.NS",
        "BHARTIARTL.NS", "IDEA.NS", "VODAFONE.NS",
        "DLF.NS", "PRESTIGE.NS", "LODHA.NS", "ADANIPORTS.NS"
    ]
    
    results = []
    
    for ticker in all_indian_stocks:
        try:
            result = g2g_model(ticker)
            if result:
                sector = stock_sectors.get(ticker, "Other")
                result['Sector'] = sector
                results.append(result)
        except:
            pass
    
    # Sort by G2G Score and return top 15
    results.sort(key=lambda x: x['G2G_Score'], reverse=True)
    return jsonify(results[:15])

if __name__ == '__main__':
    app.run(debug=False, port=5000, host='0.0.0.0')
