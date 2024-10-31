from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
import os
import threading
import time
import pandas as pd  # Make sure to import pandas if not already imported
import csv
import logging
from tenacity import retry, stop_after_attempt, wait_fixed
from helpers.supabase_helper import SupabaseHelper
from helpers.rapidapi_helper import RapidAPIHelper
from helpers.groq_helper import GroqHelper
from helpers.email_parser import EmailParser
import io
import json
import requests
import concurrent.futures
from functools import partial
from requests.exceptions import RequestException
from retry_decorator import retry

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')  # Store your secret key in .env

# Global variable to store progress
progress = {
    'total': 0,
    'current': 0,
    'status': 'PENDING',  # can be 'PENDING', 'PROGRESS', 'SUCCESS', 'FAILURE'
    'result': None,  # You can store any result data here
    'file_path': None
}

# Function to save progress to a file
def save_progress():
    with open('progress.json', 'w') as f:
        json.dump(progress, f)

# Function to load progress from a file
def load_progress():
    global progress
    if os.path.exists('progress.json'):
        with open('progress.json', 'r') as f:
            progress = json.load(f)
        # Prevent automatic processing on server start
        if progress.get('status') == 'PROGRESS':
            progress['status'] = 'PENDING'
            progress['current'] = 0
            save_progress()
    else:
        progress = {
            'total': 0,
            'current': 0,
            'status': 'PENDING',
            'result': None,
            'file_path': None
        }

# Load progress when the app starts
load_progress()

class UploadForm(FlaskForm):
    csv_file = FileField('CSV File')
    submit = SubmitField('Upload')

# At the top of your app.py file, add this logging configuration
logging.basicConfig(
    level=logging.ERROR,
    filename='app.log',
    filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Disable all loggers except for errors
for name in logging.root.manager.loggerDict:
    logging.getLogger(name).setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

def get_usernames_to_process(data):
    # Extract LinkedIn usernames from the data
    usernames = []

    # If your data has a column 'linkedin_url' with URLs like 'https://www.linkedin.com/in/username/'
    for url in data['linkedin_url']:
        # Extract the username from the URL
        if pd.notna(url):  # Check for NaN values
            username = url.rstrip('/').split('/')[-1]
            usernames.append(username)

    return usernames

def read_csv_data(file_path):
    linkedin_urls = []
    emails = []
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for row in csv_reader:
                # Clean and standardize LinkedIn URL
                url = row['linkedin_url'].strip()
                if url:
                    # Ensure URL starts with https://
                    if not url.startswith('http'):
                        url = 'https://' + url.lstrip('/')
                    # Remove trailing slash
                    url = url.rstrip('/')
                    linkedin_urls.append(url)
                    emails.append(row['email'])
                    
        logging.error(f"Successfully read {len(linkedin_urls)} URLs from CSV")
        return linkedin_urls, emails
    except UnicodeDecodeError:
        logger.error(f"Failed to read the CSV file with UTF-8 encoding.")
        return [], []
    except KeyError as e:
        logger.error(f"The CSV file is missing a required column: {str(e)}")
        return [], []
    except Exception as e:
        logger.error(f"An error occurred while reading the CSV file: {str(e)}")
        return [], []

@retry(Exception, tries=3, delay=1, backoff=2)
def generate_followup_email(groq, email_parser, profile_data):
    """Generate follow-up email with retry logic using Groq"""
    try:
        followup_prompt = groq.create_prompt('prompts/followup_prompt.txt', profile_data)
        followup_prompt = followup_prompt.replace('{{original_email}}', profile_data['email_body'])
        
        followup_email_content = groq.generate_email(followup_prompt)
        logging.error(f"Raw follow-up email content received: {followup_email_content[:200]}..." if followup_email_content else "No follow-up email content received")
        
        if not followup_email_content:
            raise Exception("Empty follow-up email content received")
            
        return email_parser.parse_followup_email(followup_email_content)
    except Exception as e:
        logging.error(f"Error generating follow-up email: {str(e)}")
        raise

def keep_alive():
    while True:
        time.sleep(50)  # Sleep for 50 seconds
        try:
            # Option 1: Use a different URL (e.g., a public website)
            requests.get("https://www.google.com", timeout=10)
            
            # Option 2: Disable SSL verification (not recommended for production)
            # requests.get(f"https://{os.environ['REPL_SLUG']}.{os.environ['REPL_OWNER']}.repl.co", verify=False, timeout=10)
        except RequestException as e:
            print(f"Keep-alive request failed: {e}")

# Create a lock for Groq API calls
groq_lock = threading.Lock()

@retry(Exception, tries=3, delay=1, backoff=2)
def generate_original_email(groq, prompt, profile_data):
    """Generate original email with retry logic using Groq"""
    try:
        email_content = groq.generate_email(prompt)
        logging.error(f"Raw email content received: {email_content[:200]}..." if email_content else "No email content received")
        
        if not email_content:
            raise Exception("Empty email content received")
            
        return email_content
    except Exception as e:
        logging.error(f"Error generating original email: {str(e)}")
        raise

def process_profile(url, email, supabase, rapidapi, groq, email_parser):
    global progress
    try:
        # Clean and standardize URL
        if url:
            url = url.strip()
            if not url.startswith('http'):
                url = 'https://' + url.lstrip('/')
            url = url.rstrip('/')
            
        logging.error(f"Processing profile with cleaned URL: {url}")
        linkedin_data = rapidapi.get_linkedin_profile(url, email)
        
        if linkedin_data:
            logging.error(f"Retrieved LinkedIn data for: {linkedin_data.get('fullName', 'Unknown')}")
            
            # Map the new API response structure to our existing format
            profile_data = {
                'full_name': linkedin_data.get('fullName'),
                'first_name': linkedin_data.get('firstName'),
                'last_name': linkedin_data.get('lastName'),
                'headline': linkedin_data.get('headline'),
                'location': linkedin_data.get('addressWithCountry'),
                'about': linkedin_data.get('about'),
                'profile_picture': linkedin_data.get('profilePicture', {}).get('profilePictureLink'),
                'email': email,
                'linkedin_url': url
            }
            
            # Format LinkedIn data for email writing
            formatted_linkedin_data = format_linkedin_data(linkedin_data)
            profile_data['formatted_linkedin_data'] = formatted_linkedin_data
            
            logging.error(f"Formatted data prepared for {profile_data['full_name']}")
            logging.error(f"Formatted LinkedIn data length: {len(formatted_linkedin_data)}")
            
            # Generate and insert original email
            try:
                prompt_template_path = 'prompts/prompt.txt'
                logging.error(f"Reading prompt template from: {prompt_template_path}")
                
                prompt = groq.create_prompt(prompt_template_path, profile_data)
                prompt += f"\n\n{formatted_linkedin_data}"
                logging.error(f"Final prompt length with LinkedIn data: {len(prompt)}")
                
                logging.error(f"Attempting to generate email for {profile_data['full_name']}")
                
                with groq_lock:
                    try:
                        email_content = generate_original_email(groq, prompt, profile_data)
                        time.sleep(1)
                    except Exception as e:
                        logging.error(f"Failed to generate original email after retries: {str(e)}")
                        email_content = None
                
                if email_content:
                    try:
                        subject, body = email_parser.parse_original_email(email_content)
                        logging.error(f"Successfully parsed email - Subject length: {len(subject)}, Body length: {len(body)}")
                        
                        profile_data['email_subject'] = subject
                        profile_data['email_body'] = body
                        profile_data['status'] = 'processed'  # Set status explicitly
                        
                        result = supabase.insert_data('linkedin_emails', profile_data)
                        if result:
                            logging.error(f"Successfully inserted data for {profile_data['full_name']}")
                        else:
                            logging.error(f"Failed to insert data into Supabase for {profile_data['full_name']}")
                    except Exception as e:
                        logging.error(f"Error parsing email content: {str(e)}")
                        logging.error(f"Raw email content: {email_content}")
                else:
                    logging.error(f"Failed to generate original email for {profile_data.get('full_name', 'Unknown')}")
                    return  # Exit early if original email fails
                
            except Exception as e:
                logging.error(f"Error in email generation process: {str(e)}")
                return  # Exit early if there's an error

            progress['current'] += 1
            save_progress()

            # Generate and insert follow-up email
            if profile_data.get('email_body'):
                try:
                    with groq_lock:
                        followup_body = generate_followup_email(groq, email_parser, profile_data)
                        time.sleep(1)
                    
                    if followup_body:
                        profile_data['followup_email_body'] = followup_body
                        result = supabase.insert_data('linkedin_emails', profile_data)
                        if not result:
                            logger.error(f"Failed to insert follow-up email for {profile_data.get('full_name', 'Unknown')}")
                except Exception as e:
                    logger.error(f"Error generating follow-up email for {profile_data.get('full_name', 'Unknown')}: {str(e)}")
            else:
                logger.error(f"Skipping follow-up email for {profile_data.get('full_name', 'Unknown')} due to missing original email body")

            progress['current'] += 1
            save_progress()
        else:
            logging.error(f"Failed to fetch data for URL: {url}")
    except Exception as e:
        logging.error(f"Error in process_profile: {str(e)}")

def main(file_path):
    global progress
    progress['status'] = 'PROGRESS'
    progress['file_path'] = file_path
    save_progress()

    # Start the keep-alive thread
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()

    supabase = SupabaseHelper()
    data = supabase.upload_csv_to_supabase(file_path)

    if data is None or len(data) == 0:
        logger.error("No data uploaded to Supabase. Exiting.")
        progress['status'] = 'FAILURE'
        return

    rapidapi = RapidAPIHelper()
    groq = GroqHelper()
    email_parser = EmailParser()

    progress['total'] = len(data) * 2
    progress['current'] = 0

    linkedin_urls, emails = read_csv_data(file_path)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        process_func = partial(process_profile, supabase=supabase, rapidapi=rapidapi, 
                             groq=groq, email_parser=email_parser)
        futures = []
        for url, email in zip(linkedin_urls, emails):
            futures.append(executor.submit(process_func, url, email))
            time.sleep(1)  # Delay 1 second before starting the next task

        concurrent.futures.wait(futures)

    progress['status'] = 'SUCCESS'
    progress['result'] = {
        'file_name': os.path.basename(file_path),
        'total_emails_generated': progress['current']
    }
    save_progress()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            return jsonify({'error': 'No file part in request'}), 400

        csv_file = request.files['csv_file']
        if csv_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        filename = secure_filename(csv_file.filename)
        upload_folder = 'uploads'
        file_path = os.path.join(upload_folder, filename)

        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        csv_file.save(file_path)

        # Start processing in a separate thread
        thread = threading.Thread(target=main, args=(file_path,))
        thread.start()

        save_progress()  # Save progress after starting the thread

        # Return a JSON response
        return jsonify({
            'message': 'File uploaded successfully. Processing started.'
        })
    else:
        return render_template('index.html', progress=progress)

@app.route('/status')
def status():
    load_progress()  # Load the latest progress
    if progress['total'] == 0:
        percent = 0
    else:
        percent = int((progress['current'] / progress['total']) * 100)
    return jsonify({
        'state': progress['status'],
        'progress': percent,
        'result': progress['result'],
        'file_path': progress['file_path']
    })

@app.route('/download_csv')
def download_csv():
    try:
        # Fetch the original LinkedIn URLs from the uploaded CSV
        upload_folder = 'uploads'
        csv_files = [f for f in os.listdir(upload_folder) if f.endswith('.csv')]
        if not csv_files:
            return jsonify({'error': 'No CSV file found'}), 404
        
        file_path = os.path.join(upload_folder, csv_files[-1])  # Get the most recent CSV file
        linkedin_urls, _ = read_csv_data(file_path)

        supabase = SupabaseHelper()
        data = supabase.fetch_processed_data(linkedin_urls)

        if not data:
            return jsonify({'error': 'No processed data available'}), 404

        # Create a CSV file in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        for row in data:
            writer.writerow(row)

        # Create a response with the CSV file
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='processed_linkedin_emails.csv'
        )

    except Exception as e:
        logger.error(f"Error generating CSV: {str(e)}")
        return jsonify({'error': 'Failed to generate CSV'}), 500

def format_linkedin_data(linkedin_data):
    """Format LinkedIn data for the prompt suitable for email writing"""
    formatted_text = []
    
    try:
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
            formatted_text.append("\nEducation:")
            for edu in educations[:1]:
                if isinstance(edu, dict):
                    formatted_text.append(f"{edu.get('title', 'N/A')} - {edu.get('subtitle', 'N/A')}")
        
        # Add skills
        skills = linkedin_data.get('skills', [])
        if skills:
            formatted_text.append("\nSkills:")
            for skill in skills[:5]:
                if isinstance(skill, dict):
                    formatted_text.append(f"- {skill.get('title', 'N/A')}")
        
        # Add recent updates
        updates = linkedin_data.get('updates', [])
        if updates:
            formatted_text.append("\nRecent Professional Updates:")
            latest_update = updates[0]  # Most recent update
            if latest_update.get('postText'):
                formatted_text.append(latest_update['postText'][:200] + "..." if len(latest_update['postText']) > 200 else latest_update['postText'])
        
        return "\n".join(formatted_text)
        
    except Exception as e:
        logging.error(f"Error formatting LinkedIn data: {str(e)}")
        return "Error formatting LinkedIn data"

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8000)
