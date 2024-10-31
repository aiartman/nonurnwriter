import os
import requests
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

def test_generate_email():
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("Error: OPENROUTER_API_KEY is not set in the environment variables")
        return

    api_url = "https://openrouter.ai/api/v1/chat/completions"
    
    payload = {
        "model": "meta-llama/llama-3.1-70b-instruct",
        "messages": [
            {
                "role": "user",
                "content": "Write a short email to John Doe about a job opportunity."
            }
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": os.getenv('YOUR_SITE_URL', 'http://localhost:5000'),
        "X-Title": os.getenv('YOUR_APP_NAME', 'EmailWriter'),
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        print("Status Code:", response.status_code)
        print("\nResponse Headers:")
        print(json.dumps(dict(response.headers), indent=2))
        
        print("\nResponse Content:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            print("\nGenerated Email Content:")
            print(content)
        else:
            print("\nError in API response")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    test_generate_email()