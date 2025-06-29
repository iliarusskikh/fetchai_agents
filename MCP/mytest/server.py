from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Create a FastMCP server instance
mcp = FastMCP("justwill_test")

#NWS_API_BASE = "https://api.weather.gov"
#USER_AGENT = "weather-app/1.0"


class CoinInfoResponse(Model):
    name: str
    symbol: str
    current_price: float
    market_cap: float
    total_volume: float
    price_change_24h: float



#
#async def make_nws_request(url: str) -> dict[str, Any] | None:
#    headers = {
#        "User-Agent": USER_AGENT,
#        "Accept": "application/geo+json"
#    }
#    async with httpx.AsyncClient() as client:
#        try:
#            response = await client.get(url, headers=headers, timeout=30.0)
#            response.raise_for_status()
#            return response.json()
#        except Exception:
#            return None
#
#def format_alert(feature: dict) -> str:
#    props = feature["properties"]
#    return f""" Event: {props.get('event', 'Unknown')} Area: {props.get('areaDesc', 'Unknown')} Severity: {props.get('severity', 'Unknown')} Description: {props.get('description', 'No description available')} Instructions: {props.get('instruction', 'No specific instructions provided')}"""
#
#
def get_crypto_info(blockchain: str) -> CoinInfoResponse:
    coin_id =""
    match blockchain:
        case "ethereum"|"Ethereum"|"Ethereum network"|"ETH"|"eth"|"ethereum network":
            coin_id = "ethereum"
        case "base"| "Base" | "Base network"|"Base blockchain"| "base network"|"base blockchain":
            coin_id = "ethereum"
        case "solana"|"Solana"|"SOL"|"solana blockchain"|"solana network":
            coin_id = "solana"
        case "bsc"|"Bsc"| "Bsc network"|"BNB":
            coin_id = "binancecoin"
        case "polygon"|"Polygon"|"Matic-network"|"Matic"|"POL":
            coin_id = "matic-network"
        case "avalanche"|"Avalanche":
            coin_id = "avalanche-2"
        case "arbitrum" | "Arbitrum"|"Arbitrum network"|"ARB"|"arb":
            coin_id = "arbitrum"
        case "optimism" |"Optimism"|"Optimism network"|"OP"|"op":
            coin_id = "optimism"
        case "sui"|"Sui":
            coin_id = "sui"
        case "ronin"|"Ronin":
            coin_id = "ronin"
        case "bitcoin"|"Bitcoin"|"btc"|"BTC":
            coin_id = "bitcoin"
        case _:
            return ValueError(f"Unsupported blockchain name: {blockchain}. Please, input the name of the supported blockchain.")  # Handle unexpected inputs
            #raise

    """Fetch cryptocurrency information from CoinGecko API"""
    
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    
    try:
        response = requests.get(url)
        logging.info(f"🚀 URL for {coint_id} received...")
        response.raise_for_status()  # Raises an error for non-200 responses

        data = response.json()
        
        return CoinInfoResponse(
            name=data['name'],
            symbol=data['symbol'].upper(),
            current_price=data['market_data']['current_price']['usd'],
            market_cap=data['market_data']['market_cap']['usd'],
            total_volume=data['market_data']['total_volume']['usd'],
            price_change_24h=data['market_data']['price_change_percentage_24h']
        )
    
    except requests.exceptions.RequestException as e:
        logging.error(f"⚠️ API Request Failed: {e}")
        return CoinInfoResponse(
            name="Unknown",
            symbol="N/A",
            current_price=0.0,
            market_cap=0.0,
            total_volume=0.0,
            price_change_24h=0.0
        )




@mcp.tool()
async def get_crypto(blockchain: str) -> CoinInfoResponse:#(str)
    """Get information about user selected blockchain. 
    Takes blockchain name as a function parameter"""
    
    crypto_data = get_crypto_info(blockchain) #to be tested
    return crypto_data
    #reply = f"Welcome to the test MCP! Wanna learn about {cryptocurrency}?"
    #return "\n---\n".join(reply)



@mcp.tool()
async def get_pokemon(pokemon: str) -> str:
    """Get information about a pokemon."""
    
#    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
#    points_data = await make_nws_request(points_url)
#
#    if not points_data:
#        return "Unable to fetch forecast data for this location."
#
#    forecast_url = points_data["properties"]["forecast"]
#    forecast_data = await make_nws_request(forecast_url)
#
#    if not forecast_data:
#        return "Unable to fetch detailed forecast."
#
#    periods = forecast_data["properties"]["periods"]
#    forecasts = []
#    for period in periods[:5]:
#        forecast = f"""{period['name']}: Temperature: {period['temperature']}°{period['temperatureUnit']} Wind: {period['windSpeed']} {period['windDirection']} Forecast: {period['detailedForecast']}"""
#        forecasts.append(forecast)
    reply = f"Here is some information about {pokemon}!"
    return "\n---\n".join(reply)



if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') #why do we need this - ask LLM
    #how do i convert class(model) into dictionary?
