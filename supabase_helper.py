import pandas as pd
from supabase import create_client, Client
import os

class SupabaseHelper:
    def __init__(self):
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_KEY')
        self.client: Client = create_client(url, key)

    def upload_csv_to_supabase(self, file_path):
        # Read CSV file into DataFrame
        data = pd.read_csv(file_path)
        # Upload data to Supabase table
        self.client.table('your_table_name').insert(data.to_dict('records')).execute()
        return data