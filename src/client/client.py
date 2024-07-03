import random
import time
import requests
import json
import argparse

# defining stocks list to randomly pick one stock from the list
stocks = ["GameStart", "FishCo", "MenhirCo", "BoarCo", "Google", "Netflix", "Amazon", "Apple", "Tesla", "Meta"]

# Parser to extract the command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--probability')
args = parser.parse_args()

# reading the config file to get the environment variables
with open('../config.json', 'r') as file:
    config_file_data = file.read()

config = json.loads(config_file_data)

frontend_config = config['frontend']

# Read the probability from command line arguments and set the probability "p" for sending another order request
p = 0.5 if args.probability == None else float(args.probability)

# variables to maintain all the aggregate latencies
lookup_sum = 0
trade_sum = 0
order_info_sum = 0


# initiating session object using requests module
session = requests.Session()
# setting a flag to check if a session is closed or not
is_session_closed = False

trade_data = []

# method to pick a random stock from the stocks list
def pick_random_stock():
    # pick a random stock
    stock = random.choice(stocks)
    return stock

def start(iterations):
    global is_session_closed
    global session
    global lookup_sum
    global trade_sum
    # while True:
    for i in range(iterations):
        print("iteration ", i)
        if is_session_closed:
            session = requests.Session()
            is_session_closed = False

        # pick a random stock
        stock_name = pick_random_stock()

        host = frontend_config['host']
        port = str(frontend_config['port'])

        start_time = time.time()

        # calling the lookup method with the previous session created
        response = session.get('http://'+host+':'+port+'/catalog/' + stock_name)

        lookup_latency = time.time() - start_time

        # aggregating the latency sum 
        lookup_sum += lookup_latency

        # decoding the response into JSON format and deserializing the response
        response_data = response.json()
        print('response_data: ', response_data)

        # checking for the positive quantity
        if response_data["data"]["quantity"] > 0:
            # Randomly decide whether to send another order request based on probability "p"
            if random.random() < p:
                # construct the payload object for order request with required fields
                payload = {
                    'name': stock_name,
                    'type': random.choice(['sell', 'buy']),
                    'quantity': random.randint(1, 100)
                }
                # add content-type as json in headers
                headers = {
                    'Content-Type': 'application/json'
                }

                start_time = time.time()

                # Send another order request using the same HTTP connection (same session)
                order_response = session.post('http://'+host+':'+port+'/orders', json=payload, headers=headers)

                trade_latency = time.time() - start_time

                trade_sum += trade_latency
                
                # decoding the response into JSON format and deserializing the response
                order_response_data = order_response.json()
                print('order_response_data: ', order_response_data)
                if order_response.status_code == 200:
                    # print(order_response_data)
                    item = {}
                    item['number'] = order_response_data['data']['transaction_number']
                    item.update(payload)
                    # item['order_payload'] = payload
                    trade_data.append(item)
        else:
            print("session closed")
            is_session_closed = True
            session.close()
        
# fucntion to validate its data and server data
def validate():
    global order_info_sum
    success = 0
    failed = 0
    host = frontend_config['host']
    port = str(frontend_config['port'])
    # looping through the order response data
    for item in trade_data:
        # reading ther order number for get order info API
        order_number = item['number']
        start_time = time.time()
        # construting the url for get order info api
        url = 'http://'+host+':'+port+'/orders/'+str(order_number)

        # calling API with requests module
        response = requests.get(url=url)

        order_latency = time.time() - start_time
        
        order_info_sum += order_latency
        if response.status_code == 200:
            # if status is 200, 
            # reading json response
            order_info = response.json()
            # if the local data matched witht the server then incrementing the success otherwise failed
            if item == order_info['data']:
                success += 1
            else:
                failed += 1
    
    return success, failed

if __name__ == "__main__":
    try:
        # starting the cloent main process
        iterations = 50
        start(iterations)
        # validating the local data and server data
        success, failed = validate()
        print("succesful validations: ", success)
        print("failed validations: ", failed)
        print('lookup_sum: ', lookup_sum/iterations)
        print('order_info_sum: ', order_info_sum/len(trade_data))
        print('trade_sum: ', trade_sum/len(trade_data))
    except KeyboardInterrupt:
        # validating the local data and server data
        success, failed = validate()
        print("succesful validations: ", success)
        print("failed validations: ", failed)