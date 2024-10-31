import requests
import os
import logging
from requests.exceptions import RequestException
from retry_decorator import retry

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
        logging.error("RapidAPIHelper initialized")

    @retry(Exception, tries=3, delay=2, backoff=2)
    def get_linkedin_profile(self, linkedin_url, email):
        """
        Fetch LinkedIn profile data with retry logic
        """
        try:
            # Clean and standardize URL
            if linkedin_url:
                linkedin_url = linkedin_url.strip()
                if not linkedin_url.startswith('http'):
                    linkedin_url = 'https://' + linkedin_url.lstrip('/')
                linkedin_url = linkedin_url.rstrip('/')
            
            payload = {"link": linkedin_url}
            logging.error(f"Attempting API request for profile: {linkedin_url}")
            
            # Log request details
            logging.error(f"Request URL: {self.base_url}")
            logging.error(f"Request payload: {payload}")
            
            response = requests.post(self.base_url, json=payload, headers=self.headers)
            logging.error(f"Response status code: {response.status_code}")
            
            # If response is not successful, raise exception for retry
            if response.status_code != 200:
                logging.error(f"API request failed with status {response.status_code}")
                logging.error(f"Response content: {response.text[:500]}...")
                raise RequestException(f"API request failed with status {response.status_code}")
            
            data = response.json()
            logging.error(f"Response JSON structure: {list(data.keys())}")
            
            if data.get('success') and data.get('status') == 200:
                profile_data = data.get('data')
                if profile_data:
                    logging.error(f"Successfully retrieved profile data for: {profile_data.get('fullName', 'Unknown')}")
                    return profile_data
                else:
                    logging.error("Profile data is empty in the response")
                    raise Exception("Empty profile data received")
            else:
                error_msg = data.get('message', 'Unknown error')
                logging.error(f"API returned error: {error_msg}")
                raise Exception(f"API error: {error_msg}")
                
        except RequestException as e:
            logging.error(f"Request error: {str(e)}")
            raise
        except ValueError as e:
            logging.error(f"JSON decode error: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            raise

    @retry(Exception, tries=2, delay=1)
    def validate_profile_data(self, profile_data):
        """
        Validate that we have the minimum required data
        """
        required_fields = ['fullName', 'headline', 'experiences']
        missing_fields = [field for field in required_fields if not profile_data.get(field)]
        
        if missing_fields:
            logging.error(f"Missing required fields: {missing_fields}")
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        if not profile_data.get('experiences'):
            logging.error("No experience data found")
            raise ValueError("No experience data found")
            
        return True