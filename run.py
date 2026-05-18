import requests

url = "http://localhost:5678/webhook/rest-hook"

params = {
    "name": "John",
    "message": "hello from python"
}

response = requests.get(url, params=params)

print("Status:", response.status_code)
print("Response:", response.json())
