#!/bin/bash

# Deploy Django backend to EC2
echo "Deploying Django backend to EC2..."

# Install Python dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Create virtual environment
python3 -m venv /home/ubuntu/venv
source /home/ubuntu/venv/bin/activate

# Install requirements
pip install -r /home/ubuntu/requirements.txt

# Run migrations
cd /home/ubuntu
python manage.py migrate

# Start Django server
python manage.py runserver 0.0.0.0:8000 &

echo "Django backend deployed successfully!"