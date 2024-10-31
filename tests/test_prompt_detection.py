import os
import sys

# Add the parent directory to the Python path to import from the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helpers.openrouter_helper import OpenRouterHelper

def test_prompt_template_detection():
    openrouter = OpenRouterHelper()
    prompt_template_path = 'prompts/prompt.txt'
    
    # Test if the file exists
    assert os.path.exists(prompt_template_path), f"Prompt template file not found at {prompt_template_path}"
    
    # Test if the file can be read
    try:
        with open(prompt_template_path, 'r') as file:
            content = file.read()
        print(f"Successfully read prompt template. Content preview:\n{content[:100]}...")
    except Exception as e:
        print(f"Error reading prompt template: {str(e)}")
        assert False, "Failed to read prompt template"
    
    # Test the create_prompt method
    try:
        sample_profile_data = {
            "name": "John Doe",
            "current_company": "Tech Corp",
            "current_position": "Software Engineer"
        }
        prompt = openrouter.create_prompt(prompt_template_path, sample_profile_data)
        if prompt is None:
            print("Error: create_prompt method returned None")
            assert False, "Failed to create prompt"
        else:
            print(f"Successfully created prompt. Prompt preview:\n{prompt[:100]}...")
            assert prompt, "Created prompt is empty"
    except Exception as e:
        print(f"Error creating prompt: {str(e)}")
        assert False, "Failed to create prompt"

    print("All tests passed successfully!")

if __name__ == "__main__":
    test_prompt_template_detection()