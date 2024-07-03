#!/bin/bash

cd frontend

nohup python3 app.py --port 5000 > frontend.log 2>&1 &