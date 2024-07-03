from flask import Flask, request, jsonify
import threading
import json
import requests
import time
import argparse

# reading the port number from the arguments
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, help='port number')
args = parser.parse_args()

# reading the config file to get the environment variables
with open('../config.json', 'r') as file:
    data = file.read()

config = json.loads(data)

app = Flask(__name__)

# initializing the cache
caching = {}
# intitalizing the max cache size
MAX_CACHE_SIZE = 6
leader_node = {}

# initializing the locks
read_lock = threading.Lock()
write_lock = threading.Lock()

# API endpoint to handle lookup requests
@app.get("/catalog/<stock_name>")
def catalog_lookup(stock_name):

    # acquring read lock as we are reading the caching data as its a shared DS
    with read_lock:
        if stock_name in caching and config['cache']:
            # if stock name is in cache, then reading it from the cache and directly returning it
            # whenever reading the cache, we are updating time for LRU eviction policy
            caching[stock_name]['last_access'] = time.time()
            response = caching[stock_name]['value']
            return response
    
    # reading catalog config
    catalog_host = config['catalog']['host']
    catalog_port = str(config['catalog']['port'])

    # setting content type headers
    headers = {
        'Content-Type': 'application/json'
    }

    # constructing the url
    url = 'http://'+catalog_host+':'+catalog_port+'/catalog/'+stock_name

    # calling the catalog API with requests module
    result = requests.get(url, headers=headers)
    # reading the json response
    res_json = result.json()
    response = {}

    # reading the status code
    if result.status_code == 200:
        # constructing the response with top level data object
        response['data'] = res_json
        # acquiring write lock as we are updating the cache
        with write_lock:
            if len(caching) >= MAX_CACHE_SIZE:
                # if the length of the cache is more than the max size, then we are evicting a key that is 
                # least recently used (LRU policy)
                lru_key = min(caching, key=lambda k: caching[k]['last_access'])
                del caching[lru_key]
            # updating the cache value for the stock name
            caching[stock_name] = {'value': response, 'last_access': time.time()}
        # returning response
        return response
    else:
        # if there is error, then constructing error object with top level error field
        error = {}
        error['message'] = res_json['error']
        error['code'] = result.status_code
        response['error'] = error
        return response, result.status_code

# API endpoint to handle the trade requests
@app.post("/orders")
def trade_API():
    # reading the json data from request payload
    data = request.get_json()
    # reading response from trade function call
    response, error = trade(data)

    if not error:
        # if not error, returning 200 ok response
        status_code = response['code']

        del response['code']
        return response, status_code
    else:
        # if there is any error, that means leader node is crashed, so re-electing the leader again
        voting_result = elect_order_leader()
        if voting_result:
            # if voting result is successful, then calling the trade function again with the same trade data
            response, error = trade(data) 
            # returning the response received from the trade
            status_code = response['code']
            del response['code']
            return response, status_code
        else:
            # if error occurs then there is no order node avaiable to handle the trade requests
            # so returning with 500 error code and appropriate message
            error = {}
            error['message'] = 'No Order replicas found to handle trade requests'
            error['code'] = 500
            response['error'] = error
            return response, 500

# function to hanlde trade API calls
def trade(payload):
    # reading the leader details
    host = leader_node['host']
    port = str(leader_node['port'])
    # setting the content type headers
    headers = {
        'Content-Type': 'application/json'
    }
    # constructing the url
    url = 'http://'+host+':'+port+'/orders'

    response = {}
    try:
        # calling the API with requests module
        result = requests.post(url, json=payload,headers=headers)
        # reading the json response
        res_json = result.json()
        if result.status_code == 200:
            # if 200 response, then returning it
            response['data'] = res_json
            response['code'] = 200
            return response, False
        else:
            # if not 200, then returning with error field at top level
            error = {}
            error['message'] = res_json['error']
            error['code'] = result.status_code
            response['error'] = error
            response['code'] = result.status_code
            return response, False
    except:
        # if a request fails, then throwing error to retry on other nodes
        print("leader order request failed running on", port)
        return response, True

# API endpoint to get order info by order number
@app.get("/orders/<order_number>")
def order_info_API(order_number):
    # getting the rwsponse from the order info function
    response, error = get_order_info(order_number)
    if not error:
        # if no error, then returning the order response received
        status_code = response['code']

        del response['code']
        return response, status_code
    else:
        # if error, then the leader node is crashed, so re-elect the leader again
        voting_result = elect_order_leader()
        if voting_result:
            # if voting result is successful, then calling the order info function again with the same order id
            response, error = get_order_info(order_number) 
            status_code = response['code']
            # returning the response as received
            del response['code']
            return response, status_code
        else:
            # if error occurs then there is no order node avaiable to handle the get order info requests
            # so returning with 500 error code and appropriate message
            error = {}
            error['message'] = 'No Order replicas found to handle trade requests'
            error['code'] = 500
            response['error'] = error
            return response, 500

# function to handle the order info API calls
def get_order_info(order_number):
    # reading the leader node details
    host = leader_node['host']
    port = str(leader_node['port'])

    # constructing the url
    url = 'http://'+host+':'+port+'/orders/'+order_number
    result = {}

    try:
        # calling the API with requests module
        response = requests.get(url)
        # reading the json data from the response
        res_json = response.json()

        if response.status_code == 200:
            # if 200 success, then constructing the response as given in the lab readme
            del res_json['trading_volume']
            res_json['number'] = res_json['transaction_number']
            del res_json['transaction_number']
            result['data'] = res_json
            result['code'] = response.status_code
            return result, False
        else:
            # if error occurs, then constructing the error object as told
            status_code = res_json['code']
            result['error'] = res_json
            result['code'] = status_code
            return result, False
    except:
        # if a request fails, then throwing error to retry on other nodes
        return result, True

# API endpoint to invalidate the cache
@app.post("/cache")
def invalidate_cache():
    # reding the json data from the request payload
    data = request.get_json()
    stock_name = data['name']
    # reading the stock name
    print("caching before deletion: ", caching)
    # acquiring the write lock as we are accessing the shared DS
    with write_lock:
        # if stock name is found then deleting it from the cache
        if stock_name in caching:
            print("deleting ", stock_name, " from cache")
            del caching[stock_name]
    
    print("caching after deletion: ", caching)
    # return json 200 ok response
    return jsonify({'status': 'ok'})

# function to hanlde leader election
def elect_order_leader():
    # reading order nodes from the config
    order_nodes = config['order']['nodes']
    # soritng the nodes based on the id
    order_nodes = sorted(order_nodes, key=lambda x: x["id"], reverse=True)
    found = None
    global leader_node

    # looping through the order nodes
    for node in order_nodes:
        # reading the host and port
        host = node['host']
        port = str(node['port'])

        # constructing the url
        url = 'http://'+host+':'+port+'/ping'
        try:
            # calling API with requests module
            result = requests.get(url)
            # stroign the leader node info if found
            leader_node_id = node['id']
            found = True
            leader_node = node
            # notifying the other nodes if a leader is elected
            notify_nodes(order_nodes,leader_node_id)

            # updating the leader id in the config
            config['order']['leader_id'] = leader_node_id
            # acquring write lock
            with write_lock:
                # updating the config file
                with open('../config.json', 'w') as file:
                    json.dump(config, file)
            break
        except:
            # if the request to a node failed
            print("request failed for order service on ", node['port'])
    
    if not found:
        # if no node is found, then retrning 
        print("No order services available")
        return False
    else:
        return True

# function to notify the nodes about the leader
def notify_nodes(order_nodes, leader_node_id):
    data = {}
    # constructing the json payload
    data['leader_id'] = leader_node_id
    # setting content type headers
    headers = {
        'Content-Type': 'application/json'
    }

    # looping throught the order nodes
    for node in order_nodes:
        # reading the host , port
        host = node['host']
        port = str(node['port'])

        # constructing the url
        url = 'http://'+host+':'+port+'/notify_leader'
        try:
            # calling API with requests module
            result = requests.post(url, json=data, headers=headers)
        except:
            # if a request failed on the current node
            print("request failed for notify leader on ", node['port'])
        
# function to run the flask application on given port and listen on given host
def run_flask_app(host, port):
    app.run(host=host, port=port)

if __name__ == '__main__':
    # electing the leaders on start
    elect_order_leader()
    # submitting each request to thread with target as run flask app
    thread = threading.Thread(target=run_flask_app, args=('0.0.0.0',args.port,))
    # starting the thread
    thread.start()