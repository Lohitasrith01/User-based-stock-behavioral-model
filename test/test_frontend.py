import requests

# Function to test the Frontend service to check if a lookup request is success
def test_frontend_lookup_success():
    # Passing the correct stock name in url
    url = "http://localhost:5002/catalog/GameStart"
    # Calling API with request module
    response = requests.get(url)
    # Checking if the status code in response is success
    assert response.status_code == 200
    # Checking if the returned response is inline with the expected response structure
    assert response.json()['data']["name"] == "GameStart"
    assert response.json()['data']["price"] == 100
    # As quantity might change, so checking for positive quantity
    assert response.json()['data']["quantity"] > 0

# Function to test the Frontend service to check if a lookup request is Failure
def test_frontend_lookup_failure():
    url = "http://localhost:5002/catalog/sample"
    # Calling API with request module
    response = requests.get(url)
    # Checking if the status code in response is 404
    assert response.status_code == 404
    # Checking if the error code in response is 404 and checking if the error response format is corect
    assert response.json()['error']['code'] == 404
    # Checking if the given stock is not found
    assert response.json()['error']['message'] == 'Stock Not Found!'

# Function to test the Frontend service to check if a trade request is success
def test_frontend_trade_success():
    url = "http://localhost:5002/orders"
    # Passing the correct stock name data structure in url
    data = {
        "name":"GameStart",
        "quantity": 20,
        "type": "sell"
    }
    # Calling API with request module with json data
    response = requests.post(url, json=data)
    # Checking if the status code in response is success and checking if the response format is corect
    assert response.status_code == 200
    # Asserting if the transaction number is generated
    assert response.json()['data']["transaction_number"] >= 0

# Function to test the Frontend service to check if a stock is not found as part of trade request
def test_frontend_trade_stock_not_found():
    url = "http://localhost:5002/orders"
    data = {
        "name":"sample",
        "quantity": 20,
        "type": "sell"
    }
    # Calling API with request module with json data
    response = requests.post(url, json=data)
    # Checking if the status code in response is 404 and checking if the error response format is corect
    assert response.status_code == 404

    assert response.json()['error']['code'] == 404
    # Checking if the given stock is not found
    assert response.json()['error']['message'] == 'Stock Not Found!'

# Function to test the Frontend service to check if a stock requested quantity exceeded the limit as part of trade request
def test_frontend_trade_quantity_exceeded():
    url = "http://localhost:5002/orders"
    data = {
        "name":"GameStart",
        "quantity": 200000,
        "type": "buy"
    }
    # Calling API with request module with json data
    response = requests.post(url, json=data)
    # Checking if the status code in response is 400 and checking if the error response format is corect
    assert response.status_code == 400
    assert response.json()['error']['code'] == 400
    # Asserting if the passed quantity exceeded the limit
    assert response.json()['error']['message'] == 'Quantity Exceeded Available Quantity!'

def test_frontend_order_info():
    url = "http://localhost:5002/orders/0"
    # calling API with requests module
    response = requests.get(url)

    # checking if status code is 200 and checking if the response is in correct format
    assert response.status_code == 200
    # since we dont know the order info for 0th order id, we cant validate any data here
    # so just checking for only 200 status code and just checking for the response format
    assert response.json()['data'] is not None

def test_frontend_order_id_not_found():
    url = "http://localhost:5002/orders/200000"
    # calling API with requests module
    response = requests.get(url)

    # checking if the status code in response is 404 and checking if the error response format is correct
    assert response.status_code == 404
    assert response.json()['error']['code'] == 404
    # asserting if the order id not found and matching the correct error message
    assert response.json()['error']['message'] == "Order does not exist"