import requests
import json

data = {
    "check_interval": 25,
}

response = requests.post("http://localhost:5000/update", json=data)

print(response.json())