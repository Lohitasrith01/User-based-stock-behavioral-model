import requests

# Function to test the catalog service to check if a lookup request is success
def test_catalog_success():
    # Passing the correct stock name in url
    url = "http://localhost:3000/catalog/GameStart"
    # Calling API with request module
    response = requests.get(url)
    # Checking if the status code in response is success
    assert response.status_code == 200
    # Checking if the returned response is inline with the expected response structure
    assert response.json()["name"] == "GameStart"
    assert response.json()["price"] == 100
    # As quantity might change, so checking for positive quantity
    assert response.json()["quantity"] > 0

# Function to test the catalog service to check if a lookup request is Failure
def test_catalog_failure():
    # Passing the incorrect stock name in url
    url = "http://localhost:3000/catalog/sample"
    # Calling API with request module
    response = requests.get(url)
    # Checking if the status code in response is failure
    assert response.status_code == 404
    # Checking if the returned response is inline with the expected error response structure
    # Checking if the passed stock is not found
    assert response.json()['error'] == 'Stock Not Found!'