import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_rapidapi_request(profile_url):
    base_url_profile = 'https://linkedin-data-scraper.p.rapidapi.com/person_urn'
    headers = {
        'x-rapidapi-key': os.environ.get('RAPIDAPI_KEY'),
        'x-rapidapi-host': 'linkedin-data-scraper.p.rapidapi.com',
        'Content-Type': 'application/json'
    }
    payload = {'link': profile_url}
    try:
        response = requests.post(base_url_profile, json=payload, headers=headers)
        print(f"Response type: {type(response)}")
        print(f"Status code: {response.status_code}")
        print("Response Headers:", response.headers)
        print("Response Content:", response.text)
    except requests.exceptions.RequestException as e:
        print(f"An exception occurred: {e}")

if __name__ == '__main__':
    # Replace the profile URL with a valid LinkedIn profile URL
    test_profile_url = 'https://www.linkedin.com/in/ACwAADd29ScBRP2TPEKZoMNkAEW-FFbzlpExC0w'
    test_rapidapi_request(test_profile_url)