from flask import Flask, request
from concurrent.futures import ThreadPoolExecutor
import json
import requests
from service import lookup, is_trade_valid, catalog
import time
import argparse
import sys
import signal

# reading the port number from the arguments
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, help='port number')
args = parser.parse_args()

# initiating the threadpool with 10 threads
pool = ThreadPoolExecutor(max_workers=10)
app = Flask(__name__)

# reading the config file to get the environment variables
with open('../../config.json', 'r') as file:
    config_file_data = file.read()

config = json.loads(config_file_data)

# stock lookup API endpoint
@app.get("/catalog/<stock_name>")
def lookup_API(stock_name):
    # submitting the lookup task to the threadpool
    future = pool.submit(lookup, stock_name)
    # reading the result from the threadpool
    result = future.result()

    response = {}
    # time.sleep(2)

    if (result != None):
        # If the result is not None, construct the response object
        
        # iterating over the result to keep only the values needed
        for key in result.keys():
            if key != 'trading_volume':
                response[key] = result[key]
        # Send a success response to the client with body as response dictionary
        return response
    else:
        # If the result is None, send a 404 error response to the client
        response['error'] = 'Stock Not Found!'
        return response, 404

# update catalog API endpoint
@app.put("/catalog")
def update_catalog():
    # reading the request payload
    data = request.get_json()
    # submitting the request to the threadpool
    future = pool.submit(is_trade_valid, data)
    # reading the result received from the threadpool
    result, error = future.result()
    if result != None:
        # invalidating the cache only if caching is enabled 
        # getting the cache flag from the config file
        if config['cache']:
            # constructing the request payload for cache API
            # sending stock name in the payload such that frontend service will remove this stock from cache
            req_body = {
                'name': data['name']
            }
            # reading the frontend config from the config 
            frontend_config = config['frontend']
            host = frontend_config['host']
            port = str(frontend_config['port'])
            # url for frontend cache API endpoint
            url = 'http://'+host+':'+port+'/cache'
            # setting content type headers
            headers = {
                'Content-Type': 'application/json'
            }
            # calling the cache API with requests module
            cache_resp = requests.post(url=url, json=req_body, headers=headers)
        # returning the result 
        return result
    else:
        #if result is None, then returning error in the response
        status_code = error['code']
        del error['code']
        return error, status_code

def handler(sig, frame):
    print("shutdown called...")
    print("writing db file....")
    exit_flag = True
    # write the contents of the catalog to the db.json file
    with open('db.json', 'w') as file:
        json.dump(catalog, file)
    
    print("done writing to the file!!")
    print("shutting down the server...")
    sys.exit(0)

if __name__ == '__main__':
    # running the app and listening on all addresses (for AWS part) 
    # running on port passed from arguments
    app.run(host="0.0.0.0", port=args.port)
    signal.signal(signal.SIGINT, handler=handler)
    signal.pause()