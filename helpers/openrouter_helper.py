import requests
import json
import os
import time
from retry_decorator import retry
from dotenv import load_dotenv

load_dotenv()

class OpenRouterHelper:
    def __init__(self):
        self.api_url = 'https://openrouter.ai/api/v1/chat/completions'
        self.headers = {
            'Authorization': f"Bearer {os.environ.get('OPENROUTER_API_KEY')}",
            'HTTP-Referer': os.environ.get('YOUR_SITE_URL', 'http://localhost:5000'),
            'X-Title': os.environ.get('YOUR_APP_NAME', 'EmailWriter'),
            'Content-Type': 'application/json'
        }
        self.requests_made = 0
        self.start_time = time.time()

    def rate_limit(self):
        if self.requests_made >= 5:
            elapsed = time.time() - self.start_time
            if elapsed < 1:
                time.sleep(1 - elapsed)
            self.requests_made = 0
            self.start_time = time.time()
        self.requests_made += 1

    def create_prompt(self, prompt_template_path, profile_data):
        with open(prompt_template_path, 'r') as file:
            prompt = file.read()
        # Replace placeholders in prompt with actual data from profile_data
        for key, value in profile_data.items():
            if isinstance(value, str):
                prompt = prompt.replace(f'{{{{{key}}}}}', value)
        return prompt

    @retry(Exception, tries=3, delay=1)
    def generate_email(self, prompt):
        self.rate_limit()
        payload = {
            "model": "meta-llama/llama-3.1-70b-instruct",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        headers = {
            "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}",
            "HTTP-Referer": os.environ.get('YOUR_SITE_URL', 'http://localhost:5000'),
            "X-Title": os.environ.get('YOUR_APP_NAME', 'EmailWriter'),
            "Content-Type": "application/json"
        }
        print(f"Sending payload: {json.dumps(payload, indent=2)}")
        print(f"Headers: {json.dumps({k: v for k, v in headers.items() if k != 'Authorization'}, indent=2)}")

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            response_json = response.json()
            if 'choices' not in response_json or len(response_json['choices']) == 0:
                raise ValueError("API response does not contain expected 'choices' field")
            
            return response_json['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            if e.response:
                print(f"Response status code: {e.response.status_code}")
                print(f"Response content: {e.response.text}")
            raise
        except (KeyError, IndexError, ValueError) as e:
            print(f"Error parsing API response: {str(e)}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            raise