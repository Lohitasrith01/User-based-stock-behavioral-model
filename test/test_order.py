import requests

# Function to test the order service to check if a trade request is success
def test_order_success():
    url = "http://localhost:4000/orders"
    # Input to the order service
    data = {
        "name":"GameStart",
        "quantity": 20,
        "type": "sell"
    }
    # Calling API using request module with json payload
    response = requests.post(url, json=data)
    # Checking if status code in response is success
    assert response.status_code == 200
    # Asserting if the transaction number is generated
    assert response.json()["transaction_number"] >= 0

# Function to test the order service to check trade request if incorrect stock is passed
def test_order_stock_not_found():
    url = "http://localhost:4000/orders"
    # Input to the order service with incorrect stock name
    data = {
        "name":"sample",
        "quantity": 20,
        "type": "sell"
    }
    # Calling API using request module with json payload
    response = requests.post(url, json=data)
    # Checking if status code in response is 404
    assert response.status_code == 404
    # Checking if the given stock is not found
    assert response.json()['error'] == 'Stock Not Found!'

# Function to test the order service to check if a trade request exceeded the quantity limit
def test_order_quantity_exceeded():
    url = "http://localhost:4000/orders"
    # Input to the order service with higher quantity
    data = {
        "name":"GameStart",
        "quantity": 200000,
        "type": "buy"
    }
    # Calling API using request module with json payload
    response = requests.post(url, json=data)
    # Checking if status code in response is 400
    assert response.status_code == 400
    # Checking if the given stock is exceeded the quantity limit
    assert response.json()['error'] == 'Quantity Exceeded Available Quantity!'

def test_order_info():
    url = "http://localhost:4000/orders/0"
    # calling API with requests module
    response = requests.get(url)

    # checking if status code is 200 and checking if the response is in correct format
    assert response.status_code == 200
    # since we dont know the order info for 0th order id, we cant validate any data here
    # so just checking for only 200 status code and just checking for the response format
    assert response.json() is not None

def test_order_id_not_found():
    url = "http://localhost:4000/orders/200000"
    # calling API with requests module
    response = requests.get(url)

    # checking if the status code in response is 404 and checking if the error response format is correct
    assert response.status_code == 404
    assert response.json()['code'] == 404
    # asserting if the order id not found and matching the correct error message
    assert response.json()['message'] == "Order does not exist"
