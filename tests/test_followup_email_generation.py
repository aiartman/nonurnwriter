import os
from dotenv import load_dotenv
from helpers.openrouter_helper import OpenRouterHelper
from helpers.email_parser import EmailParser

# Load environment variables
load_dotenv()

def test_followup_email_generation():
    # Initialize helpers
    openrouter = OpenRouterHelper()
    email_parser = EmailParser()

    # Read the follow-up prompt template
    with open('prompts/followup_prompt.txt', 'r') as f:
        followup_prompt_template = f.read()

    # Sample original email
    original_subject = "Introducing Our New Product Line"
    original_body = """
    Dear [Name],

    I hope this email finds you well. I wanted to reach out and introduce you to our exciting new product line that I believe could greatly benefit your business.

    Our latest offerings are designed to streamline your operations and boost productivity. I'd love the opportunity to discuss how these solutions can be tailored to your specific needs.

    Would you be interested in scheduling a brief call to learn more?

    Best regards,
    [Your Name]
    """

    # Append the original email to the follow-up prompt
    followup_prompt = f"{followup_prompt_template}\n\nHere is the original email:\n\nSubject: {original_subject}\n\n{original_body}"

    # Generate follow-up email using OpenRouter
    followup_email_content = openrouter.generate_email(followup_prompt)

    if followup_email_content:
        # Parse the generated email
        subject, body = email_parser.parse_email(followup_email_content)

        print("Follow-up Email Generated:")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        return True
    else:
        print("Failed to generate follow-up email.")
        return False

if __name__ == "__main__":
    success = test_followup_email_generation()
    print(f"Test {'passed' if success else 'failed'}.")