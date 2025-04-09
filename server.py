from mcp.server.fastmcp import FastMCP
import requests
import os

# Initialize the MCP server
app = FastMCP("AlphaVantage MCP Server")

# Hardcoded for demo — in prod, use dotenv/env vars
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")

# -- TOOLS ----------------------------------------------------
@app.tool()
def place_order(pair: str, side: str, quantity: float, price: float = None) -> dict:
    """
    Simulate placing a forex order.
    This does not connect to a live broker — it's a placeholder for integration.
    """
    order_type = "LIMIT" if price else "MARKET"
    return {
        "status": "accepted",
        "symbol": pair.upper(),
        "side": side.upper(),
        "qty": quantity,
        "type": order_type,
        "price": price or "market"
    }

# -- RESOURCES ------------------------------------------------
@app.resource("forex://{pair}")
def get_forex_price(pair: str) -> dict:
    """
    Get the real-time exchange rate for a forex pair using Alpha Vantage.
    Example pair: USDJPY, EURUSD
    """
    from_curr = pair[:3].upper()
    to_curr = pair[3:].upper()
    url = (
        f"https://www.alphavantage.co/query?"
        f"function=CURRENCY_EXCHANGE_RATE"
        f"&from_currency={from_curr}&to_currency={to_curr}"
        f"&apikey={ALPHA_VANTAGE_KEY}"
    )
    response = requests.get(url)
    return response.json()

# -- PROMPTS --------------------------------------------------
@app.prompt()
def summarize_forex_price(data: str) -> str:
    return f"""
You are a financial assistant. Summarize the current exchange rate data:

{data}

Explain the base and quote currency, rate, and any interesting trends.
"""

# -- SAMPLING -------------------------------------------------
@app.tool()
def should_buy(pair: str, context: SamplingContext) -> str:
    """
    Ask the model whether it is a good time to buy the given currency pair.
    This demonstrates MCP sampling (server asking model for input).
    """
    prompt = f"Given recent market conditions, should we buy {pair}? Justify your reasoning."
    completion = context.sample(prompt)
    return completion

# -- ROOTS (OPTIONAL) -----------------------------------------
@app.tool()
def list_allowed_pairs(root: str = None) -> list[str]:
    """
    Show the scoped forex pairs allowed in this session. Uses root config.
    """
    # Normally you'd filter pairs based on `root` info
    return ["USDJPY", "EURUSD", "GBPUSD"] if root else ["ROOT NOT SET"]

# -- STARTUP --------------------------------------------------
@app.on_initialize
def configure_server(session):
    """
    Configure roots, if provided by the client.
    This function runs at handshake time.
    """
    roots = session.client_roots or []
    print("Client roots:", roots)
    # You could restrict visible forex pairs based on roots here

# -- RUN ------------------------------------------------------
if __name__ == "__main__":
    # Local-only development transport; replace with serve_http(port=...) for production
    app.serve_stdio()
