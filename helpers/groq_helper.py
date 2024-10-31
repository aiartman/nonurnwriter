import os
from groq import Groq
import logging
from dotenv import load_dotenv

load_dotenv()

class GroqHelper:
    def __init__(self):
        self.api_key = os.environ.get('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.1-70b-versatile"
        logging.error(f"GroqHelper initialized with model: {self.model}")

    def create_prompt(self, prompt_template_path, profile_data):
        """Create a prompt from template and profile data"""
        try:
            with open(prompt_template_path, 'r') as file:
                prompt = file.read()
            # Replace placeholders in prompt with actual data
            for key, value in profile_data.items():
                if isinstance(value, str):
                    prompt = prompt.replace(f'{{{{{key}}}}}', value)
            return prompt
        except Exception as e:
            logging.error(f"Error creating prompt: {str(e)}")
            raise

    def generate_email(self, prompt):
        """Generate email using Groq API"""
        try:
            logging.error(f"Generating email with prompt length: {len(prompt)}")
            
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert email writer. Your task is to write personalized cold emails based on LinkedIn profiles."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=self.model
            )
            
            response = chat_completion.choices[0].message.content
            logging.error(f"Successfully generated email, length: {len(response)}")
            
            return response
            
        except Exception as e:
            logging.error(f"Error generating email with Groq: {str(e)}")
            raise 