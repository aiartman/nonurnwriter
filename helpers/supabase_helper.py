import pandas as pd
import os
import json
import logging
from dotenv import load_dotenv
from supabase.client import create_client, Client

class SupabaseHelper:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.ERROR)
        
        load_dotenv()
        
        self.url = os.environ.get('SUPABASE_URL')
        self.key = os.environ.get('SUPABASE_KEY')
        
        if not self.url or not self.key:
            self.logger.error("Supabase URL or Key is missing from environment variables")
            raise ValueError("Supabase URL and Key must be set in environment variables")
        
        try:
            self.client = create_client(self.url, self.key)
            self.logger.error("Successfully initialized Supabase client")
        except Exception as e:
            self.logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise

    def insert_data(self, table_name, data):
        """Insert or update data in Supabase table"""
        try:
            self.logger.error(f"Attempting to insert data into {table_name}")
            
            # Filter data to match schema
            valid_columns = {
                'linkedin_url',
                'first_name',
                'last_name',
                'full_name',
                'email',
                'company_name',
                'formatted_linkedin_data',
                'email_subject',
                'email_body',
                'followup_email_subject',
                'followup_email_body',
                'status'
            }
            
            # Only include valid columns and non-None values
            insert_data = {k: v for k, v in data.items() 
                         if k in valid_columns and v is not None}
            
            # Set status if not provided
            if 'status' not in insert_data:
                insert_data['status'] = 'processed'
            
            self.logger.error(f"Filtered data keys: {list(insert_data.keys())}")
            
            # Check if record already exists
            existing = self.client.table(table_name)\
                .select('*')\
                .eq('linkedin_url', insert_data['linkedin_url'])\
                .execute()
            
            if existing.data:
                self.logger.error(f"Record exists for URL: {insert_data['linkedin_url']}")
                # Update only if new data is available
                if 'email_body' in insert_data or 'followup_email_body' in insert_data:
                    response = self.client.table(table_name)\
                        .update(insert_data)\
                        .eq('linkedin_url', insert_data['linkedin_url'])\
                        .execute()
                    self.logger.error("Updated existing record with new email data")
                else:
                    self.logger.error("No new email data to update")
                    return existing.data
            else:
                # Insert new record
                response = self.client.table(table_name)\
                    .insert(insert_data)\
                    .execute()
                self.logger.error("Inserted new record")
            
            if response.data:
                self.logger.error(f"Successfully processed data in {table_name}")
                return response.data
            else:
                self.logger.error(f"No data returned from operation for {table_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error processing data in {table_name}: {str(e)}")
            self.logger.error(f"Full error context: {str(e.__class__.__name__)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def upload_csv_to_supabase(self, file_path):
        """Read CSV data and return records without uploading to Supabase"""
        try:
            data = pd.read_csv(file_path)
            self.logger.error(f"Successfully read CSV with {len(data)} rows")

            # Ensure required columns exist
            required_columns = {'linkedin_url', 'email'}
            missing_columns = required_columns - set(data.columns)
            if missing_columns:
                self.logger.error(f"Missing required columns: {missing_columns}")
                return None

            # Standardize column names
            column_mapping = {
                'LinkedIn_URL': 'linkedin_url',
                'First_Name': 'first_name',
                'Last_Name': 'last_name',
                'Full_Name': 'full_name',
                'Email': 'email',
                'Company_Name': 'company_name'
            }
            data = data.rename(columns=column_mapping)

            # Remove duplicates
            data = data.drop_duplicates(subset=['linkedin_url'], keep='first')
            
            # Convert to records and filter for valid columns
            records = data.where(pd.notnull(data), None).to_dict(orient='records')
            self.logger.error(f"Returning {len(records)} records from CSV")
            
            return records
            
        except Exception as e:
            self.logger.error(f"Error reading CSV data: {str(e)}")
            return None

    def fetch_processed_data(self, linkedin_urls):
        """Fetch processed data for given LinkedIn URLs"""
        try:
            response = self.client.table('linkedin_emails')\
                .select('*')\
                .in_('linkedin_url', linkedin_urls)\
                .execute()
                
            if response.data:
                return response.data
            else:
                self.logger.error("No processed data found")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching processed data: {str(e)}")
            return None

    def update_followup_email(self, contact_id, followup_email_subject, followup_email_body):
        """Update follow-up email data"""
        try:
            response = self.client.table('linkedin_emails')\
                .update({
                    'followup_email_subject': followup_email_subject,
                    'followup_email_body': followup_email_body
                })\
                .eq('id', contact_id)\
                .execute()
            
            if response.data:
                self.logger.error(f"Successfully updated follow-up email for contact ID {contact_id}")
                return True
            else:
                self.logger.error(f"Failed to update follow-up email for contact ID {contact_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating follow-up email: {str(e)}")
            return False
