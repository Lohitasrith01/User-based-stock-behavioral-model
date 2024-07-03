#!/bin/bash

cd backend/catalog

nohup python3 app.py --port 3000 > catalog_3000.log 2>&1 &

cd ../order

nohup python3 app.py --port 4000 > order_4000.log 2>&1 &
nohup python3 app.py --port 4001 > order_4001.log 2>&1 &
nohup python3 app.py --port 4002 > order_4002.log 2>&1 &