from flask import Flask, request, jsonify
import json
import requests
from concurrent.futures import ThreadPoolExecutor
import os
import threading
import argparse

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

# initializing the leader_id
leader_id = None

# initializing the locks
read_lock = threading.Lock()
write_lock = threading.Lock()

# initializing the transaction number and history
transaction_number = -1
transaction_history = []

# method to call the catalog microservice API
def update_catalog(payload):
    # getting the catalog config to read host and port
    catalog_config = config['catalog']
    host = catalog_config['host']
    port = str(catalog_config['port'])
    # constructing the URL
    url = 'http://'+host+':'+port+'/catalog'
    # setting headers to support json request payload
    headers = {
        'Content-Type': 'application/json'
    }
    # calling PUT method of catalog service with requests module with json payload
    response = requests.put(url, json=payload, headers=headers)
    return response

# function to handle the request and update the transaction information accordingly
def handle_request(payload):
    global transaction_number
    # calling catalog api to lookup stock info and update the stock info in the catalog microservice
    catalog_response = update_catalog(payload)
    # decoding the response into JSON format and deserializing the response
    result = catalog_response.json()

    # checking for the response status code
    if catalog_response.status_code == 200:
        # acquiring the write lock
        with write_lock:
            # incrementing the transaction number
            if len(transaction_history) != 0:
                transaction_number = transaction_history[-1]['transaction_number']
            transaction_number += 1
            # deleting the price from result as it is not required
            del result['price']
            # adding additional required fields to the result object
            result['type'] = payload['type']
            result['quantity'] = payload['quantity']
            result['transaction_number'] = transaction_number
            # adding the result object at the end of the transaction history list
            transaction_history.append(result)
            # updating the db file with the updated data
            with open(f'log_{args.port}.json', 'w') as file:
                json.dump(transaction_history, file)
            
            # calling a function to sync data with other nodes (replication)
            sync_data_with_nodes(result)
        # returning success and None as error
        return transaction_history, None
    else:
        # reading the error code from response status code
        code = catalog_response.status_code
        # returning None as success and error object in a structured format as error
        return None, {'code': code, 'error': result['error']}

# API endpoint for trade requests
@app.post("/orders")
def trade_API():
    # reading the request payload
    data = request.get_json()

    # submitting the trade request to the threadpool
    future = pool.submit(handle_request, data)
    # reading the result received from the threadpool
    result, error = future.result()
    if(result != None):
        # if the result is not None, creating a response object and constructing the object as required
        response = {}
        response = {'transaction_number': result[-1]['transaction_number']}
        # returning the response
        return response
    else:
        # if the result is None, returning with error and appropriate status code
        status_code = error['code']
        del error['code']
        return error, status_code
    
# API endpoint to get the order info by order number
@app.get("/orders/<order_number>")
def get_order_info(order_number):
    # submitting the task to threadpool
    future = pool.submit(order_info, order_number)
    # reading the result received from the threadpool
    result = future.result()
    if not result:
        # if order is not found for a given order number, returning the 404 error with message
        response = {}
        response['message'] = "Order does not exist"
        response['code'] = 404
        return response, 404
    else:
        # if order is found, then returning
        return result
    
# API endpoing to check the node health
@app.get("/ping")
def check_health():
    # sending the json data that its healthy
    return jsonify({'status': 'ok'})

# API endpoint to notify the nodes about the elected leader
@app.post("/notify_leader")
def notify_leader():
    # reading the request payload
    data = request.get_json()
    global leader_id
    # setting the leader id with the id received in the request payload
    leader_id = data['leader_id']
    # return json data with 200 ok response
    return jsonify({'status': 'ok'})

# API endpoint to sync data when the leader pushes the data to the nodes
@app.post("/sync_data")
def sync_data():
    # reading the request payload 
    data = request.get_json()
    global transaction_history
    # acquiring the write lock as we are updating the shared data structure
    with write_lock:
        # append the received data to the transaction history
        transaction_history.append(data)
        # update the db file with the updated data
        with open(f'log_{args.port}.json', 'w') as file:
            json.dump(transaction_history, file)
    # return 200 ok response as json 
    return jsonify({'status': 'ok'})

# API endpoint to get the backlog data from the leader if a node comes back online after the crash
@app.get('/backlog/<transaction_id>')
def get_backlog_data(transaction_id):
    # if the order number is -1, then returning the complete transaction history
    if transaction_id == str(-1):
        return transaction_history
    
    # variable to track the matched index in the list
    match_index = -1
    found = None
    # acquiring the read lock as we are reading the transaction history (shared)
    with read_lock:
        # iterating through the transaction list
        for index, item in enumerate(transaction_history):
            if str(item['transaction_number']) == transaction_id:
                # if the order number matches, then stopping the loop as we found required id
                match_index = index
                found = True
                break
    
    # if nothing is found then returning empty list
    if not found:
        return []
    
    # slicing the list, after the matched index because the node already has the data till matched index
    sliced_tr_history = transaction_history[match_index+1:]
    print('sliced_tr_history: ', sliced_tr_history)

    # returning the sliced data
    return sliced_tr_history

# function to load the db file to in memory data structure
def load_db(port):

    # maintaining a individual db file for each node 
    filename = f'log_{port}.json'
    global transaction_history

    # if the db file does not exist, then creating it with the empty list
    if not os.path.exists(filename):
        with open(filename, "w") as file:
            json.dump([], file)
    else:
        # on server start reading the log.json file and loading its contents to in-memory transaction history data
        with open(filename, 'r') as file:
            db = file.read()
        
        transaction_history = json.loads(db)

# function to get the order information by order number
def order_info(order_number):
    global transaction_history
    order = None
    # acquring the read lock as we are using the shared data structure
    with read_lock:
        # looping through the transaction history
        for item in transaction_history:
            # checking for the order number in the list
            if str(item['transaction_number']) == order_number:
                # if found then assigning it to a variable to use it 
                order = item
                break
    
    # if not found, then returning false, else returning the found item
    if not order:
        return False
    else:
        return order

# function to sync data with the nodes 
def sync_data_with_nodes(result):
    # reading order config from the config
    order_nodes = config['order']['nodes']
    # looping through order replicas
    for node in order_nodes:
        # checking if the same node is trying to send request
        if args.port != node['port']:
            # reading host and port
            host = node['host']
            port = str(node['port'])

            # setting content type headers
            headers = {
                'Content-Type': 'application/json'
            }
            # constructing the url
            url = 'http://'+host+':'+port+'/sync_data'
            try:
                # calling the other nodes with requests module
                response = requests.post(url, json=result, headers=headers)
            except:
                # if the node is unresponse, just printing that the node is unavailable
                print("data sync failed for order service running on ", node['port'])

# function to sync with the leader after it back online from a crash
def sync_with_leader():
    # getting the current leader id from the config
    running_leader_id = config['order']['leader_id']
    # getting the order nodes info
    order_nodes = config['order']['nodes']
    global transaction_number
    global transaction_history

    # getting the last transaction number its db had
    if len(transaction_history) != 0:
        transaction_number = transaction_history[-1]['transaction_number']
    
    leader_node_details = {}
    found = None
    # looping through the order nodes
    for node in order_nodes:
        # checking for the leader id and checking if the same node is acting as the leader at start time
        if node['id'] == running_leader_id and node['port'] != args.port:
            # if found, stroing its info
            leader_node_details = node
            found = True
            break
    
    # if not found, just returning
    if not found:
        return
    
    # leader node details
    host = leader_node_details['host']
    port = str(leader_node_details['port'])

    try:
        # constructing the url
        url = 'http://'+host+':'+port+'/backlog/'+str(transaction_number)
        # calling the API with reqests module
        response = requests.get(url)
        # reading the json data
        json_resp = response.json()
        print('missed data when offline: ', json_resp)

        # concatenating the received data with already present data
        transaction_history = transaction_history + json_resp
        # updating the db file with the new data, here we are not using locks because 
        # this process happens at the start of the program and no thread can handle 
        # this before that time
        with open(f'log_{args.port}.json', 'w') as file:
            json.dump(transaction_history, file)
    except:
        pass
    return

if __name__ == "__main__":
    # loading db to in memory data
    load_db(args.port)
    # syncing data wiht the leader if this node is crashed
    sync_with_leader()
    # running the server to listen for all ips (for AWS part) and running on the port passed from the args
    app.run(host="0.0.0.0", port=args.port)