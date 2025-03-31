from flask import Flask, render_template, request
import pandas as pd
import requests
import json
import time
import math
import os

# Set up the Flask app and specify the absolute path for the templates folder.
app = Flask(__name__, template_folder='c:/Users/jerry/bullishllama/templates/')



# ----------------------------
# Step 1: Fetch and Process Data from APIs
# ----------------------------

# API 1 – Bluechip data
url = "https://ow-scanx-analytics.dhan.co/customscan/fetchdt"
payload = {
    "data": {
        "sort": "Mcap",
        "sorder": "desc",
        "count": 50,
        "params": [
            {"field": "idxlist.Indexid", "op": "", "val": "13"},
            {"field": "Exch", "op": "", "val": "NSE"},
            {"field": "OgInst", "op": "", "val": "ES"}
        ],
        "fields": ["Sym"],
        "pgno": 1
    }
}
headers = {
    "Content-Type": "application/json; charset=UTF-8",
    "Accept": "*/*",
    "Origin": "https://dhan.co",
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/133.0.0.0 Safari/537.36")
}

response = requests.post(url, json=payload, headers=headers)
json_data = response.json()

# API 2 – Penny stocks data
url_new = "https://ow-scanx-analytics.dhan.co/customscan/fetchdt"
payload_new = {
    "data": {
        "sort": "Mcap",
        "sorder": "desc",
        "count": 50,
        "params": [
            {"field": "Ltp", "op": "lte", "val": "50"},
            {"field": "OgInst", "op": "", "val": "ES"},
            {"field": "Seg", "op": "", "val": "E"},
            {"field": "Exch", "op": "", "val": "NSE"}
        ],
        "fields": [
            "Isin", "DispSym", "Mcap", "Pe", "DivYeild", "Revenue",
            "Year1RevenueGrowth", "NetProfitMargin", "YoYLastQtrlyProfitGrowth",
            "Year1ROCE", "EBIDTAMargin", "volume", "PricePerchng1year",
            "PricePerchng3year", "PricePerchng5year", "Ind_Pe", "Pb",
            "DivYeild", "Eps", "DaySMA50CurrentCandle", "DaySMA200CurrentCandle",
            "DayRSI14CurrentCandle", "Year1ROCE", "Year1ROE", "Sym"
        ],
        "pgno": 1
    }
}
headers_new = {
    "Content-Type": "application/json; charset=UTF-8",
    "Accept": "*/*",
    "Origin": "https://dhan.co",
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/133.0.0.0 Safari/537.36")
}

response_new = requests.post(url_new, json=payload_new, headers=headers_new)
json_data_new = response_new.json()

# Combine data from both APIs into one list.
combined_data = []

if "data" in json_data:
    for stock in json_data["data"]:
        # Ensure the necessary keys exist
        if all(k in stock for k in ["Ltp", "Low1Yr", "High1Yr", "Pchange", "PPerchange", "DispSym"]):
            combined_data.append(stock)

if "data" in json_data_new:
    for stock in json_data_new["data"]:
        if all(k in stock for k in ["Ltp", "Low1Yr", "High1Yr", "Pchange", "PPerchange", "DispSym"]):
            combined_data.append(stock)

# ----------------------------
# Step 2: Technical Analysis Functions
# ----------------------------

def estimate_buy_stop(stock):
    """
    Estimate the ideal buy price, buy range (±10%), and stop loss (5% below the ideal buy).
    """
    ltp = stock["Ltp"]
    low1yr = stock["Low1Yr"]
    ideal_buy = (ltp + low1yr) / 2
    buy_range_lower = ideal_buy * 0.90
    buy_range_upper = ideal_buy * 1.10
    stop_loss = ideal_buy * 0.95
    return {
        "Ideal Buy Price": round(ideal_buy, 2),
        "Buy Range Lower Bound": round(buy_range_lower, 2),
        "Buy Range Upper Bound": round(buy_range_upper, 2),
        "Stop Loss": round(stop_loss, 2)
    }

def advanced_technical_analysis(stock):
    """
    Perform enhanced technical analysis and include buy/stop estimates.
    """
    ltp = stock["Ltp"]
    low1yr = stock["Low1Yr"]
    high1yr = stock["High1Yr"]
    pchange = stock["Pchange"]
    yr_range = high1yr - low1yr
    position = (ltp - low1yr) / yr_range if yr_range != 0 else None

    if position is not None:
        if position < 0.10 and pchange < 0:
            decision = "STRONG BUY"
        elif position < 0.30 and pchange < 0:
            decision = "BUY"
        elif position < 0.70:
            decision = "NEUTRAL"
        else:
            decision = "WAIT"
    else:
        decision = "N/A"

    result = {
        "Symbol": stock["DispSym"],
        "LTP": ltp,
        "Decision": decision
    }
    result.update(estimate_buy_stop(stock))
    return result

analyzed_stocks = [advanced_technical_analysis(stock) for stock in combined_data]
buy_signals = [stock for stock in analyzed_stocks if stock["Decision"] in ["STRONG BUY", "BUY"]]
selected_columns = ["Symbol", "LTP", "Decision", "Ideal Buy Price", "Stop Loss",
                    "Buy Range Upper Bound", "Buy Range Lower Bound"]

if buy_signals:
    df_clean = pd.DataFrame(buy_signals)[selected_columns]
else:
    df_clean = pd.DataFrame(columns=selected_columns)

# ----------------------------
# Step 3: Fundamental Analysis via Gemini API
# ----------------------------

api_key = "AIzaSyCbOevy-PUL9NPnsI2FnQkBMzo_zQor2jI"
url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={api_key}"
headers_gemini = {"Content-Type": "application/json"}

def parse_gemini_response(response_text):
    """
    Parse the Gemini API response.
    """
    if "XXXX" in response_text:
        decision = "Buy"
    elif "YYYY" in response_text:
        decision = "Don't buy"
    else:
        decision = ""
    fundamental_analysis = response_text.replace("XXXX", "").replace("YYYY", "").strip()
    return fundamental_analysis, decision

fund_analysis_list = []
buy_decision_list = []
api_responses_list = []

for idx, row in df_clean.iterrows():
    symbol = row["Symbol"]
    prompt_text = f"2 line Fundamental Analysis of {symbol} with a Buy (Write XXXX for Buy) or Don't buy (Write YYYY for Don't Buy) output."
    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }
    try:
        response = requests.post(url_gemini, headers=headers_gemini, json=payload)
        if response.ok:
            data = response.json()
            api_responses_list.append(data)
            output_text = data["candidates"][0]["content"]["parts"][0].get("text", "")
            fund_analysis, decision = parse_gemini_response(output_text)
        else:
            print(f"Error {response.status_code}: {response.text}")
            fund_analysis = ""
            decision = ""
            api_responses_list.append(response.text)
    except Exception as e:
        print(f"Exception occurred: {e}")
        fund_analysis = ""
        decision = ""
        api_responses_list.append(str(e))
    fund_analysis_list.append(fund_analysis)
    buy_decision_list.append(decision)
    time.sleep(1)

df_clean["Fundamental Analysis"] = fund_analysis_list
df_clean["Buy Decision"] = buy_decision_list

filtered_stocks = df_clean[
    (df_clean["Decision"].isin(["STRONG BUY", "BUY"])) &
    (df_clean["Buy Decision"] == "Buy")
].reset_index(drop=True)

# ----------------------------
# Step 4: Flask Routes and Allocation Logic
# ----------------------------

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            investment_amount = float(request.form.get('investment_amount'))
        except (ValueError, TypeError):
            investment_amount = 0
        risk = request.form.get('risk_appetite').lower()

        # Use filtered stocks for allocation
        filtered = filtered_stocks.copy()
        df_above = filtered[filtered["Ideal Buy Price"] > 100].copy()
        df_below = filtered[filtered["Ideal Buy Price"] <= 100].copy()

        allocation = {"above": 0, "below": 0}
        if risk == "low":
            allocation["above"] = investment_amount
        elif risk == "medium":
            allocation["above"] = investment_amount * 0.70
            allocation["below"] = investment_amount * 0.30
        elif risk == "high":
            allocation["above"] = investment_amount * 0.30
            allocation["below"] = investment_amount * 0.70

        max_alloc_frac = 0.30 if risk in ["low", "medium"] else 0.50
        max_allocation_per_stock = investment_amount * max_alloc_frac

        def allocate_group(df_group, allocated_funds, max_alloc_per_stock):
            df_group = df_group.sort_values(by="Ideal Buy Price")
            allocation_dict = {row["Symbol"]: 0 for _, row in df_group.iterrows()}
            prices = {row["Symbol"]: row["Ideal Buy Price"] for _, row in df_group.iterrows()}
            remaining = allocated_funds
            purchase_made = True
            while remaining >= min(prices.values()) and purchase_made:
                purchase_made = False
                for sym in allocation_dict:
                    price = prices[sym]
                    if allocation_dict[sym] * price < max_alloc_per_stock and remaining >= price:
                        allocation_dict[sym] += 1
                        remaining -= price
                        purchase_made = True
            portfolio_entries = []
            for _, row in df_group.iterrows():
                sym = row["Symbol"]
                qty = allocation_dict[sym]
                if qty > 0:
                    total_cost = qty * prices[sym]
                    portfolio_entries.append({
                        "Stock": sym,
                        "Price": round(prices[sym], 2),
                        "Quantity": qty,
                        "Total": round(total_cost, 2),
                        "Analysis": row.get("Fundamental Analysis", "")
                    })
            return portfolio_entries

        portfolio = allocate_group(df_above, allocation["above"], max_allocation_per_stock) + \
                    allocate_group(df_below, allocation["below"], max_allocation_per_stock)
        portfolio_df = pd.DataFrame(portfolio)
        total_allocated = portfolio_df["Total"].sum() if not portfolio_df.empty else 0
        within_tolerance = (abs(total_allocated - investment_amount) / investment_amount <= 0.10) if investment_amount > 0 else True

        return render_template('portfolio.html',
                               portfolio=portfolio_df.to_dict(orient='records'),
                               total_allocated=total_allocated,
                               within_tolerance=within_tolerance,
                               investment_amount=investment_amount)
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('aboutus.html')

if __name__ == '__main__':
    app.run(debug=True)
