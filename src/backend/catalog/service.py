import threading
import json

# defining locks
read_lock = threading.Lock()
write_lock = threading.Lock()

# on server start reading the db.json file and loading its contents to in-memory catalog data
with open('db.json', 'r') as file:
    data = file.read()

catalog = json.loads(data)
    
# function to lookup the stock by its name
def lookup(stock_name):
    # acquiring the read lock
    with read_lock:
        # iterating over the catalog data and if a stock is matched with its name, returning that item
        for item in catalog:
            if item['name'] == stock_name:
                return item

    # if a stock is not found, we are returning the None value to handle the errors
    return None

# function to check if the trade is valid or not
def is_trade_valid(payload):
    # acquiring the write lock
    with write_lock:
        # iterating over the catalog data
        for item in catalog:
            # checking if the stock name is matched
            if item['name'] == payload['name']:
                # checking for the transaction type
                if payload['type'] == 'buy':
                    # checking for the available quantity
                    if payload['quantity'] > item['quantity']:
                        # returning error if the requested quantity exceeded the limit
                        return None, {'code': 400, 'error':'Quantity Exceeded Available Quantity!'}
                    # decrementing the stock quantity for buy type
                    item['quantity'] -= payload['quantity']
                else:
                    # incrmenting the stock quantity for sell type
                    item['quantity'] += payload['quantity']

                # incrementing the trading volume for all types of transactions
                item['trading_volume'] += payload['quantity']
                # return the updated stock item and error as None
                return item, None

    # return success as None and error if the stock is not found
    return None, {'code': 404, 'error':'Stock Not Found!'}
