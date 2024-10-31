import os
import json
import logging
from dotenv import load_dotenv
from helpers.rapidapi_helper import RapidAPIHelper

# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def format_linkedin_data(linkedin_data):
    """Format LinkedIn data for the prompt suitable for email writing"""
    formatted_text = []
    
    # Print raw data for debugging
    print("\nRAW DATA STRUCTURE:")
    print(json.dumps(linkedin_data, indent=2)[:1000] + "...\n")  # Print first 1000 chars
    
    try:
        print("\nFORMATTED DATA:")
        # Add name and headline
        formatted_text.append(f"Name: {linkedin_data.get('fullName', 'N/A')}")
        formatted_text.append(f"Headline: {linkedin_data.get('headline', 'N/A')}")
        formatted_text.append(f"Location: {linkedin_data.get('addressWithCountry', 'N/A')}")
        
        # Add about section
        about = linkedin_data.get('about')
        if about:
            formatted_text.append(f"\nAbout:\n{about}")
        
        # Add current position
        experiences = linkedin_data.get('experiences', [])
        if experiences:
            current_exp = experiences[0]
            print("\nDEBUG - Current Experience Raw Data:")
            print(json.dumps(current_exp, indent=2))
            
            formatted_text.append("\nCurrent Position:")
            if isinstance(current_exp, dict):
                formatted_text.append(f"Title: {current_exp.get('title', 'N/A')}")
                formatted_text.append(f"Details: {current_exp.get('subtitle', 'N/A')}")
                if current_exp.get('caption'):
                    formatted_text.append(f"Location: {current_exp.get('caption', 'N/A')}")
                
                # Add responsibilities
                if current_exp.get('subComponents'):
                    for comp in current_exp['subComponents']:
                        if comp.get('description'):
                            formatted_text.append("Responsibilities:")
                            for desc in comp['description']:
                                if isinstance(desc, dict) and desc.get('text'):
                                    formatted_text.append(f"- {desc['text']}")
        
        # Add education
        educations = linkedin_data.get('educations', [])
        if educations:
            print("\nDEBUG - Education Raw Data:")
            print(json.dumps(educations[0], indent=2))
            
            formatted_text.append("\nEducation:")
            for edu in educations[:1]:
                if isinstance(edu, dict):
                    formatted_text.append(f"{edu.get('title', 'N/A')} - {edu.get('subtitle', 'N/A')}")
        
        # Add skills
        skills = linkedin_data.get('skills', [])
        if skills:
            print("\nDEBUG - Skills Raw Data:")
            print(json.dumps(skills[:2], indent=2))
            
            formatted_text.append("\nSkills:")
            for skill in skills[:5]:
                if isinstance(skill, dict):
                    formatted_text.append(f"- {skill.get('title', 'N/A')}")
        
        formatted_result = "\n".join(formatted_text)
        print("\nFINAL FORMATTED OUTPUT:")
        print(formatted_result)
        
        return formatted_result
        
    except Exception as e:
        print(f"Error during formatting: {str(e)}")
        print("Raw linkedin_data structure:")
        print(json.dumps(linkedin_data, indent=2))
        return "Error formatting LinkedIn data"

def test_profile_formatting():
    # Load environment variables
    load_dotenv()
    
    # Initialize RapidAPI helper
    rapidapi = RapidAPIHelper()
    
    # Test URLs
    test_urls = [
        "https://www.linkedin.com/in/ingmar-klein/",
        # Add more test URLs here
    ]
    
    for url in test_urls:
        print(f"\n{'='*80}")
        print(f"Testing URL: {url}")
        print(f"{'='*80}\n")
        
        try:
            # Get profile data
            response = rapidapi.get_linkedin_profile(url, "test@email.com")
            
            if response:
                print("Successfully retrieved profile data")
                
                # Save raw response for debugging
                with open('raw_response.json', 'w', encoding='utf-8') as f:
                    json.dump(response, f, indent=2)
                print("\nRaw response saved to 'raw_response.json'")
                
                # Format the data
                formatted_data = format_linkedin_data(response)
                
                # Save the formatted data
                with open('formatted_data.txt', 'w', encoding='utf-8') as f:
                    f.write(formatted_data)
                print("Formatted data saved to 'formatted_data.txt'")
            else:
                print("Failed to retrieve profile data")
                
        except Exception as e:
            print(f"Error processing profile: {str(e)}")
            import traceback
            print(traceback.format_exc())

if __name__ == "__main__":
    test_profile_formatting() 