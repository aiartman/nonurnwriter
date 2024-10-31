import requests
import os
import logging
import json
from requests.exceptions import RequestException

class RapidAPIHelper:
    def __init__(self):
        self.api_key = os.environ.get('RAPIDAPI_KEY')
        self.api_host = "linkedin-data-scraper.p.rapidapi.com"
        self.base_url = "https://linkedin-data-scraper.p.rapidapi.com/person"
        
        if not self.api_key:
            raise ValueError("RAPIDAPI_KEY environment variable is not set")
        
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.api_host,
            "Content-Type": "application/json"
        }
        
        # Log initialization
        logging.error(f"RapidAPIHelper initialized with host: {self.api_host}")
        logging.error(f"API Key present: {'Yes' if self.api_key else 'No'}")

    def get_linkedin_profile(self, linkedin_url, email):
        """
        Fetch LinkedIn profile data using the new API endpoint
        """
        try:
            # Clean and standardize URL
            if linkedin_url:
                linkedin_url = linkedin_url.strip()
                if not linkedin_url.startswith('http'):
                    linkedin_url = 'https://' + linkedin_url.lstrip('/')
                linkedin_url = linkedin_url.rstrip('/')
                
            payload = {"link": linkedin_url}
            
            # Log request details
            logging.error(f"Making API request with:")
            logging.error(f"URL: {self.base_url}")
            logging.error(f"Headers: {json.dumps({k: '***' if k == 'x-rapidapi-key' else v for k, v in self.headers.items()})}")
            logging.error(f"Payload: {json.dumps(payload)}")
            
            # Make the request
            response = requests.post(self.base_url, json=payload, headers=self.headers)
            
            # Log response status
            logging.error(f"Response status code: {response.status_code}")
            logging.error(f"Response headers: {dict(response.headers)}")
            
            # Try to get response text safely
            try:
                response_text = response.text
                logging.error(f"Raw response text (first 500 chars): {response_text[:500]}...")
            except Exception as e:
                logging.error(f"Error getting response text: {str(e)}")
                response_text = "Unable to get response text"
            
            response.raise_for_status()
            
            # Parse JSON response
            try:
                data = response.json()
                logging.error(f"Successfully parsed JSON response")
                logging.error(f"Response keys: {list(data.keys())}")
                
                if data.get('success') and data.get('status') == 200:
                    profile_data = data.get('data')
                    if profile_data:
                        logging.error(f"Successfully retrieved profile data")
                        logging.error(f"Profile data keys: {list(profile_data.keys()) if isinstance(profile_data, dict) else 'Not a dict'}")
                        return profile_data
                    else:
                        logging.error("Profile data is empty in the response")
                        return None
                else:
                    error_msg = data.get('message', 'Unknown error')
                    logging.error(f"API returned error: {error_msg}")
                    return None
                    
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error: {str(e)}")
                logging.error(f"Response content that failed JSON parsing: {response_text[:500]}...")
                return None
                
        except RequestException as e:
            logging.error(f"Request error: {str(e)}")
            logging.error(f"Request details: URL={self.base_url}, Payload={payload}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            logging.error(f"Full error context: {str(e.__class__.__name__)}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return None