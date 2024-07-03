Commands to run the server and clients.

Before running the all services, please make sure that all the ports are configured correctly in 
config.json file

    Backend:
        Catalog:
            python3 app.py --port 3000
        Order:
            python3 app.py --port 4000
            python3 app.py --port 4001
            python3 app.py --port 4002
    
    Frontend:
        python3 app.py --port 5000

    Client:
        python3 client.py
            Options:
                --probability (optional, default is 0.5)
                    probability
            Example:
                python3 client.py --probability=0.9

    Alternatively we can run backend services using the following command:
        bash backend.sh
    To run frontend service, we can run the following command:
        bash frontend.sh