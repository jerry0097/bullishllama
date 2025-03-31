import ipywidgets as widgets
from IPython.display import display, clear_output
import pandas as pd
import requests
import json
import time
import math

#bluechip

url = "https://ow-scanx-analytics.dhan.co/customscan/fetchdt"

# Updated payload with count set to 50
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

# Define the headers as provided in the updated API details
headers = {
    "Content-Type": "application/json; charset=UTF-8",
    "Accept": "*/*",
    "Origin": "https://dhan.co",
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/133.0.0.0 Safari/537.36")
}

# Make the POST request to the updated API endpoint
response = requests.post(url, json=payload, headers=headers)
json_data = response.json()


#penny
# Define the endpoint URL for the new API call
url_new = "https://ow-scanx-analytics.dhan.co/customscan/fetchdt"

# Define the new payload with count set to 8 and specific filter parameters
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
            "Isin",
            "DispSym",
            "Mcap",
            "Pe",
            "DivYeild",
            "Revenue",
            "Year1RevenueGrowth",
            "NetProfitMargin",
            "YoYLastQtrlyProfitGrowth",
            "Year1ROCE",
            "EBIDTAMargin",
            "volume",
            "PricePerchng1year",
            "PricePerchng3year",
            "PricePerchng5year",
            "Ind_Pe",
            "Pb",
            "DivYeild",
            "Eps",
            "DaySMA50CurrentCandle",
            "DaySMA200CurrentCandle",
            "DayRSI14CurrentCandle",
            "Year1ROCE",
            "Year1ROE",
            "Sym"
        ],
        "pgno": 1
    }
}

# Define the headers based on the provided request details
headers_new = {
    "Content-Type": "application/json; charset=UTF-8",
    "Accept": "*/*",
    "Origin": "https://dhan.co",
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/133.0.0.0 Safari/537.36")
}

# Make the POST request using the new API details
response_new = requests.post(url_new, json=payload_new, headers=headers_new)

# Convert the response to a Python dictionary
json_data_new = response_new.json()



combined_data = []

# API 1 data might be minimal; add only records that contain key details
if "data" in json_data:
    for stock in json_data["data"]:
        # Ensure necessary keys exist for analysis (e.g., Ltp, Low1Yr, High1Yr, etc.)
        if all(k in stock for k in ["Ltp", "Low1Yr", "High1Yr", "Pchange", "PPerchange", "DispSym"]):
            combined_data.append(stock)

# API 2 should have the detailed records; add them directly
if "data" in json_data_new:
    for stock in json_data_new["data"]:
        if all(k in stock for k in ["Ltp", "Low1Yr", "High1Yr", "Pchange", "PPerchange", "DispSym"]):
            combined_data.append(stock)

def estimate_buy_stop(stock):
    """
    Estimate the ideal buy price, the buy range (±10% of the ideal buy price),
    and the stop loss (5% below the ideal buy price) for a stock.

    Parameters:
        stock (dict): Contains stock data with keys "Ltp" and "Low1Yr".

    Returns:
        dict: Contains:
              - 'Ideal Buy Price': Average of LTP and 1-Year Low.
              - 'Buy Range Lower Bound': 10% below the Ideal Buy Price.
              - 'Buy Range Upper Bound': 10% above the Ideal Buy Price.
              - 'Stop Loss': 5% below the Ideal Buy Price.
    """
    ltp = stock["Ltp"]
    low1yr = stock["Low1Yr"]

    # Heuristic 1: Average of current price and 1-year low.
    ideal_buy = (ltp + low1yr) / 2

    # Calculate the buy range: ±10% of the ideal buy price.
    buy_range_lower = ideal_buy * 0.90
    buy_range_upper = ideal_buy * 1.10

    # Set a stop loss at 5% below the ideal buy price.
    stop_loss = ideal_buy * 0.95

    return {
        "Ideal Buy Price": round(ideal_buy, 2),
        "Buy Range Lower Bound": round(buy_range_lower, 2),
        "Buy Range Upper Bound": round(buy_range_upper, 2),
        "Stop Loss": round(stop_loss, 2)
    }

def advanced_technical_analysis(stock):
    """
    Perform enhanced technical analysis for a stock and integrate the
    ideal buy price, buy range, and stop loss estimates.
    """
    ltp = stock["Ltp"]
    low1yr = stock["Low1Yr"]
    high1yr = stock["High1Yr"]
    pchange = stock["Pchange"]

    # Calculate the 1-year range.
    yr_range = high1yr - low1yr

    # Calculate the relative position of LTP within the 1-year range.
    if yr_range != 0:
        position = (ltp - low1yr) / yr_range
    else:
        position = None

    # Decision logic:
    # - If position < 10% of the range and price is falling, then STRONG BUY.
    # - If position < 30% of the range and price is falling, then BUY.
    # - If position is between 30% and 70%, then NEUTRAL.
    # - Otherwise, WAIT.
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

    # Build a clean result containing only the desired output fields.
    result = {
        "Symbol": stock["DispSym"],
        "LTP": ltp,
        "Decision": decision
    }
    result.update(estimate_buy_stop(stock))
    return result

# Process each stock using advanced analysis.
analyzed_stocks = [advanced_technical_analysis(stock) for stock in combined_data]

# Filter stocks that have a "STRONG BUY" or "BUY" decision.
buy_signals = [stock for stock in analyzed_stocks if stock["Decision"] in ["STRONG BUY", "BUY"]]

# Create a DataFrame to display the final output with only the desired columns.
selected_columns = [
    "Symbol",
    "LTP",
    "Decision",
    "Ideal Buy Price",
    "Stop Loss",
    "Buy Range Upper Bound",
    "Buy Range Lower Bound"
]

if buy_signals:
    df_clean = pd.DataFrame(buy_signals)[selected_columns]
    print("Stocks with BUY Signals:")
    display(df_clean)
else:
    print("No stocks meet the BUY criteria.")

api_key = "AIzaSyCbOevy-PUL9NPnsI2FnQkBMzo_zQor2jI"

url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

headers_gemini = {
    "Content-Type": "application/json"
}

def parse_gemini_response(response_text):
    """
    Parse the Gemini API response text.
    If the response text contains "XXXX", return decision "Buy";
    if it contains "YYYY", return decision "Don't buy".
    In either case, remove "XXXX" and "YYYY" from the fundamental analysis text.
    """
    if "XXXX" in response_text:
        decision = "Buy"
    elif "YYYY" in response_text:
        decision = "Don't buy"
    else:
        decision = ""

    # Remove the decision markers from the fundamental analysis text.
    fundamental_analysis = response_text.replace("XXXX", "").replace("YYYY", "").strip()

    return fundamental_analysis, decision


# Prepare lists to hold the new columns.
fund_analysis_list = []
buy_decision_list = []
api_responses_list = []  # To store the full API responses

# Loop over each stock in df_clean.
for idx, row in df_clean.iterrows():
    symbol = row["Symbol"]
    # Create a prompt with the stock symbol.
    prompt_text = f"2 line Fundamental Analysis of {symbol} with a Buy (Write XXXX for Buy) or Don't buy (Write YYYY for Don't Buy) output."

    # Create the payload for the Gemini API call.
    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }

    try:
        response = requests.post(url_gemini, headers=headers_gemini, json=payload)
        if response.ok:
            data = response.json()
            # Store the full API response.
            api_responses_list.append(data)
            # Access the text from the first candidate.
            # Expected location: data["candidates"][0]["content"]["parts"][0]["text"]
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

    # Delay for 1 second between requests.
    time.sleep(5)

# Add the new columns to df_clean.
df_clean["Fundamental Analysis"] = fund_analysis_list
df_clean["Buy Decision"] = buy_decision_list

filtered_stocks = df_clean[
    (df_clean["Decision"].isin(["STRONG BUY", "BUY"])) &
    (df_clean["Buy Decision"] == "Buy")
].reset_index(drop=True)

# Display the filtered stocks.
print("Stocks meeting both technical and fundamental criteria (Buy):")
display(filtered_stocks) 

# Define the input widgets
amount_input = widgets.FloatText(
    value=0,
    description='Investment Amount:',
    disabled=False,
    style={'description_width': 'initial'},
)

risk_appetite = widgets.Dropdown(
    options=[('Low', 'low'), ('Medium', 'medium'), ('High', 'high')],
    value='medium',
    description='Risk Appetite:',
    style={'description_width': 'initial'},
)

submit_button = widgets.Button(
    description='Submit',
    button_style='primary',  # 'success', 'info', 'warning', 'danger' for different styles
    tooltip='Click to submit your investment details'
)

# Output widget to display the results
output = widgets.Output()

# Define the submission behavior
def on_submit(b):
    with output:
        clear_output()  # Clear previous output
        data = {
            'Investment Amount': amount_input.value,
            'Risk Appetite': risk_appetite.value
        }
        print("Submitted Data:")
        for key, value in data.items():
            print(f" - {key}: {value}")
        # TODO: Connect this data to your analysis pipeline (e.g., trigger BSE API calls, technical analysis, etc.)

# Connect the button click to the on_submit function
submit_button.on_click(on_submit)

investment_amount = amount_input.value  # e.g., 10000
risk = risk_appetite.value.lower()        # "low", "medium", or "high"

# --- Split stocks into two groups based on Ideal Buy Price ---
df_above = df_clean[df_clean["Ideal Buy Price"] > 100].copy()
df_below = df_clean[df_clean["Ideal Buy Price"] <= 100].copy()

# --- Determine base allocation based on risk appetite ---
allocation = {"above": 0, "below": 0}
if risk == "low":
    allocation["above"] = investment_amount
elif risk == "medium":
    allocation["above"] = investment_amount * 0.70
    allocation["below"] = investment_amount * 0.30
elif risk == "high":
    allocation["above"] = investment_amount * 0.30
    allocation["below"] = investment_amount * 0.70
else:
    allocation["above"] = investment_amount

# --- Define diversification constraint ---
# For low/medium risk: no single stock exceeds 30% of total investment;
# for high risk: allow up to 50%.
if risk in ["low", "medium"]:
    max_alloc_frac = 0.30
else:
    max_alloc_frac = 0.50
max_allocation_per_stock = investment_amount * max_alloc_frac

def allocate_group_iterative(df_group, allocated_funds, max_alloc_per_stock):
    """
    Iteratively allocate funds to stocks in df_group (sorted by Ideal Buy Price ascending)
    in a round-robin fashion. For each stock, buy one share at a time as long as:
      - The remaining funds allow it.
      - The diversification constraint (max_alloc_per_stock) is not exceeded.
    Returns a list of portfolio entries for stocks that received at least one share.
    """
    # Sort stocks by ascending Ideal Buy Price
    df_group = df_group.sort_values(by="Ideal Buy Price", ascending=True)
    # Create dictionaries for allocation and prices.
    allocation_dict = {row["Symbol"]: 0 for _, row in df_group.iterrows()}
    prices = {row["Symbol"]: row["Ideal Buy Price"] for _, row in df_group.iterrows()}

    remaining = allocated_funds
    purchase_made = True
    while remaining >= min(prices.values()) and purchase_made:
        purchase_made = False
        for sym in allocation_dict:
            price = prices[sym]
            # Check diversification: total spent on this stock so far is allocation_dict[sym]*price.
            if allocation_dict[sym] * price < max_alloc_per_stock and remaining >= price:
                allocation_dict[sym] += 1
                remaining -= price
                purchase_made = True
    # Build portfolio entries for stocks with at least one share purchased.
    portfolio_entries = []
    for _, row in df_group.iterrows():
        sym = row["Symbol"]
        qty = allocation_dict[sym]
        if qty > 0:
            total_cost = qty * prices[sym]
            portfolio_entries.append({
                "Stock": sym,
                "Price to enter at": round(prices[sym], 2),
                "Quantity": qty,
                "Total": round(total_cost, 2),
                "Fundamental Analysis": row.get("Fundamental Analysis", "")
            })
    return portfolio_entries

# --- Allocate funds for each group using the iterative allocation ---
portfolio_above = allocate_group_iterative(df_above, allocation["above"], max_allocation_per_stock)
portfolio_below = allocate_group_iterative(df_below, allocation["below"], max_allocation_per_stock)

# Combine both groups
portfolio = portfolio_above + portfolio_below
portfolio_df = pd.DataFrame(portfolio)

# --- Calculate total allocation and verify tolerance (±10%) ---
total_allocated = portfolio_df["Total"].sum()
print(f"Total allocated: {total_allocated}")

if abs(total_allocated - investment_amount) / investment_amount <= 0.10:
    print("Total allocation is within ±10% of the investment amount.")
else:
    print("Warning: Total allocation is outside ±10% of the investment amount.")

# Display the final portfolio suggestions
portfolio_df

