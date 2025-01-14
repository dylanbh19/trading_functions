import azure.functions as func
import logging
from azure.cosmos import CosmosClient
import os
import json

# Cosmos DB settings
COSMOS_ENDPOINT = os.environ["COSMOS_ENDPOINT"]
COSMOS_KEY = os.environ["COSMOS_KEY"]
COSMOS_DB_NAME = os.environ["COSMOS_DB_NAME"]
COSMOS_CONTAINER_NAME = os.environ["COSMOS_CONTAINER_NAME"]

# Initialize Cosmos DB client
client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
database = client.get_database_client(COSMOS_DB_NAME)
container = database.get_container_client(COSMOS_CONTAINER_NAME)

app = func.FunctionApp()

@app.function_name(name="buy_shares")
@app.route(route="buy_shares", auth_level=func.AuthLevel.FUNCTION)
def buy_shares(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a buy request.')
    
    try:
        user_id = req.params.get('user_id')
        symbol = req.params.get('symbol')
        shares = float(req.params.get('shares', 0))
        
        if not all([user_id, symbol, shares]):
            return func.HttpResponse(
                json.dumps({"error": "Missing required parameters"}),
                status_code=400,
                mimetype="application/json"
            )
            
        user = container.read_item(item=user_id, partition_key=user_id)
        portfolio = user.get("portfolio", [])
        symbol = symbol.upper()
        
        position = next((p for p in portfolio if p["symbol"] == symbol), None)
        
        if position:
            position["shares"] += shares
        else:
            portfolio.append({
                "symbol": symbol,
                "shares": shares
            })
            
        user["portfolio"] = portfolio
        container.upsert_item(user)
        
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "message": f"Bought {shares} shares of {symbol}",
                "updated_portfolio": portfolio
            }),
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error in buy_shares: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.function_name(name="sell_shares")
@app.route(route="sell_shares", auth_level=func.AuthLevel.FUNCTION)
def sell_shares(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a sell request.')
    
    try:
        user_id = req.params.get('user_id')
        symbol = req.params.get('symbol')
        shares = float(req.params.get('shares', 0))
        
        if not all([user_id, symbol, shares]):
            return func.HttpResponse(
                json.dumps({"error": "Missing required parameters"}),
                status_code=400,
                mimetype="application/json"
            )
            
        user = container.read_item(item=user_id, partition_key=user_id)
        portfolio = user.get("portfolio", [])
        symbol = symbol.upper()
        
        position = next((p for p in portfolio if p["symbol"] == symbol), None)
        
        if not position:
            return func.HttpResponse(
                json.dumps({"error": f"No position found for {symbol}"}),
                status_code=400,
                mimetype="application/json"
            )
            
        if position["shares"] < shares:
            return func.HttpResponse(
                json.dumps({"error": f"Insufficient shares for {symbol}"}),
                status_code=400,
                mimetype="application/json"
            )
            
        position["shares"] -= shares
        
        if position["shares"] <= 0:
            portfolio.remove(position)
            
        user["portfolio"] = portfolio
        container.upsert_item(user)
        
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "message": f"Sold {shares} shares of {symbol}",
                "updated_portfolio": portfolio
            }),
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error in sell_shares: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
