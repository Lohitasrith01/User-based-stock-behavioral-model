#!/bin/bash

sudo apt-get update
sudo apt-get install build-essential libpq-dev libssl-dev openssl libffi-dev zlib1g-dev

sudo apt-get install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update

sudo apt-get install python3-pip
sudo apt-get install python3.7

sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1

pip3 install Flask