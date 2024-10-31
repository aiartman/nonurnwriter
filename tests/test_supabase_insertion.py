import logging
from helpers.supabase_helper import SupabaseHelper
from helpers.openrouter_helper import OpenRouterHelper
from helpers.email_parser import EmailParser
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    filename='test_supabase_insertion.log',
    filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_supabase_insertion():
    logger = logging.getLogger('test_supabase_insertion')
    logger.debug("Starting Supabase insertion test.")
    supabase_helper = SupabaseHelper()

    test_data = {
        'linkedin_url': 'https://www.linkedin.com/in/testuser',
        'first_name': 'Test',
        'last_name': 'User',
        'full_name': 'Test User',
        'email': 'testuser@example.com',
        'company_name': 'Test Company',
        'formatted_linkedin_data': json.dumps({
            'headline': 'Testing Headline',
            'summary': 'This is a test summary.',
            'experiences': [],
            'educations': [],
            'skills': []
        }),
        'email_subject': 'Test Subject',
        'email_body': 'Test Email Body',
        'followup_email_subject': 'Test Follow-up Subject',
        'followup_email_body': 'Test Follow-up Body',
        'status': 'pending'
    }

    try:
        result = supabase_helper.insert_data('linkedin_emails', test_data)
        logger.debug(f"Insert result: {result}")
        if result:
            logger.info("Supabase insertion successful.")
            logger.debug(f"Inserted data: {result}")
        else:
            logger.error("Supabase insertion failed.")
    except Exception as e:
        logger.exception(f"An exception occurred during Supabase insertion: {e}")

    # Query the table after insertion attempt
    try:
        response = supabase_helper.client.table('linkedin_emails').select('*').limit(5).execute()
        logger.debug(f"Query response: {response}")
    except Exception as e:
        logger.exception(f"Error querying table: {e}")

def test_update_followup_email():
    logger = logging.getLogger('test_update_followup_email')
    logger.debug("Starting update follow-up email test.")
    supabase_helper = SupabaseHelper()
    
    test_contact_id = 1  # Replace with a valid contact ID from your database
    test_followup_email_subject = "Test Follow-up Subject"
    test_followup_email_body = "This is a test follow-up email body."
    
    try:
        supabase_helper.update_followup_email(test_contact_id, test_followup_email_subject, test_followup_email_body)
    except Exception as e:
        logger.exception(f"An exception occurred during follow-up email update: {e}")

def test_followup_email_generation_and_insertion():
    logger = logging.getLogger('test_followup_email')
    logger.debug("Starting follow-up email generation and insertion test.")
    
    supabase_helper = SupabaseHelper()
    openrouter_helper = OpenRouterHelper()
    email_parser = EmailParser()

    # Sample profile data
    profile_data = {
        'linkedin_url': 'https://www.linkedin.com/in/testuser',
        'first_name': 'Test',
        'last_name': 'User',
        'full_name': 'Test User',
        'email': 'testuser@example.com',
        'company_name': 'Test Company',
        'formatted_linkedin_data': json.dumps({
            'headline': 'Testing Headline',
            'summary': 'This is a test summary.',
            'experiences': [],
            'educations': [],
            'skills': []
        }),
        'email_subject': 'Initial Email Subject',
        'email_body': 'This is the body of the initial email.',
        'status': 'pending'
    }

    try:
        # First, insert or update the initial data
        initial_result = supabase_helper.insert_data('linkedin_emails', profile_data)
        logger.debug(f"Initial data insertion result: {initial_result}")

        if initial_result:
            # Generate follow-up prompt
            followup_prompt = openrouter_helper.create_prompt('prompts/followup_prompt.txt', profile_data)
            followup_prompt = followup_prompt.replace('{{original_email}}', profile_data['email_body'])

            logger.debug(f"Follow-up prompt: {followup_prompt}")

            # Generate follow-up email
            followup_email_content = openrouter_helper.generate_email(followup_prompt)
            
            # Save the generated email content to a file
            with open('generated_followup_email.txt', 'w') as f:
                f.write(followup_email_content)
            logger.info("Generated follow-up email content saved to 'generated_followup_email.txt'")
            
            if followup_email_content:
                logger.debug(f"Generated follow-up email content: {followup_email_content}")
                
                # Use the new parsing logic for follow-up emails
                followup_body = email_parser.parse_followup_email(followup_email_content)
                
                logger.debug(f"Parsed follow-up email body: {followup_body}")
                
                # Update only the followup_email_body, keeping the original email_subject
                profile_data['followup_email_body'] = followup_body

                # Insert/update the data in Supabase
                update_result = supabase_helper.insert_data('linkedin_emails', profile_data)
                
                logger.debug(f"Follow-up email update result: {update_result}")

                if update_result:
                    logger.info("Follow-up email inserted/updated in Supabase successfully.")
                    logger.debug(f"Updated data: {update_result}")
                else:
                    logger.error("Failed to insert/update follow-up email in Supabase.")
            else:
                logger.error("Failed to generate follow-up email content.")
        else:
            logger.error("Failed to insert initial data into Supabase.")
    
    except Exception as e:
        logger.exception(f"An exception occurred during follow-up email generation and insertion: {e}")

    # Query the table after insertion attempt
    try:
        response = supabase_helper.client.table('linkedin_emails').select('*').eq('linkedin_url', profile_data['linkedin_url']).execute()
        logger.debug(f"Query response after follow-up email insertion: {response}")
    except Exception as e:
        logger.exception(f"Error querying table after follow-up email insertion: {e}")

if __name__ == '__main__':
    test_supabase_insertion()
    test_update_followup_email()
    test_followup_email_generation_and_insertion()