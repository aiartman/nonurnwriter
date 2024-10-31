import requests

response = requests.get('https://httpbin.org/get')
print(f"Response Status Code: {response.status_code}")