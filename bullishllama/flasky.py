from flask import Flask, render_template, request
import pandas as pd
import requests
import json
import time
import math

app = Flask(__name__)

# Dummy processed DataFrame from your existing logic
# In production, this should be generated from your full logic pipeline.
df_clean = pd.DataFrame({
    "Symbol": ["STOCK1", "STOCK2"],
    "LTP": [110, 45],
    "Decision": ["BUY", "STRONG BUY"],
    "Ideal Buy Price": [105, 40],
    "Stop Loss": [100, 38],
    "Buy Range Upper Bound": [115, 44],
    "Buy Range Lower Bound": [95, 36],
    "Fundamental Analysis": ["Strong fundamentals", "High growth potential"],
    "Buy Decision": ["Buy", "Buy"]
})

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        investment_amount = float(request.form.get('investment_amount'))
        risk = request.form.get('risk_appetite').lower()

        # Filter by buy decision
        filtered_stocks = df_clean[
            (df_clean["Decision"].isin(["STRONG BUY", "BUY"])) &
            (df_clean["Buy Decision"] == "Buy")
        ].reset_index(drop=True)

        df_above = filtered_stocks[filtered_stocks["Ideal Buy Price"] > 100].copy()
        df_below = filtered_stocks[filtered_stocks["Ideal Buy Price"] <= 100].copy()

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
                        "Price to enter at": round(prices[sym], 2),
                        "Quantity": qty,
                        "Total": round(total_cost, 2),
                        "Fundamental Analysis": row.get("Fundamental Analysis", "")
                    })
            return portfolio_entries

        portfolio = allocate_group(df_above, allocation["above"], max_allocation_per_stock) + \
                    allocate_group(df_below, allocation["below"], max_allocation_per_stock)

        portfolio_df = pd.DataFrame(portfolio)
        total_allocated = portfolio_df["Total"].sum()
        within_tolerance = abs(total_allocated - investment_amount) / investment_amount <= 0.10

        return render_template('portfolio.html', 
                               portfolio=portfolio_df.to_dict(orient='records'),
                               total_allocated=total_allocated,
                               within_tolerance=within_tolerance,
                               investment_amount=investment_amount)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)