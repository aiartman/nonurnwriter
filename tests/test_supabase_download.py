import os
from supabase import create_client, Client
from dotenv import load_dotenv

def test_supabase_download():
    # Load environment variables from .env file
    load_dotenv()

    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')

    if not url or not key:
        print("Error: SUPABASE_URL or SUPABASE_KEY is not set in the environment variables.")
        return

    supabase: Client = create_client(url, key)

    try:
        # Replace 'linkedin_emails' with your table name
        response = supabase.table('linkedin_emails').select('*').execute()

        # The response is already the data, no need to check status_code
        data = response.data

        if not data:
            print("No data returned from Supabase.")
        else:
            print(f"Retrieved {len(data)} records from Supabase.")
            for record in data:
                print(record)

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        # You might want to add more detailed error handling here

if __name__ == "__main__":
    test_supabase_download()
