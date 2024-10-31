import re

class EmailParser:
    @staticmethod
    def parse_original_email(email_content):
        # Split the email content by lines
        lines = email_content.strip().split('\n')

        # Initialize variables
        subject = ''
        body_lines = []
        subject_found = False
        body_started = False

        for line in lines:
            line = line.strip()
            if not subject_found:
                if line.lower().startswith('subject:'):
                    # Extract the subject line
                    subject = line[len('Subject:'):].strip()
                    subject_found = True
                # Skip any lines before the Subject line
            else:
                if not body_started:
                    if line.lower().startswith('body:'):
                        # Skip the 'Body:' line
                        body_started = True
                        continue
                    elif line == '':
                        # Skip empty lines immediately after the subject
                        continue
                    else:
                        # Start of body without 'Body:' label
                        body_started = True
                # Append lines to body
                body_lines.append(line)

        # Join the body lines
        body = '\n'.join(body_lines).strip()

        return subject, body

    @staticmethod
    def parse_followup_email(email_content):
        # Split the email content by lines
        lines = email_content.strip().split('\n')

        # Initialize variables
        body_lines = []
        body_started = False

        for line in lines:
            line = line.strip()
            
            # Skip the header if present
            if line.endswith(':') and not body_started:
                continue
            
            # Check if this line starts the actual email body
            if (line.startswith("Hey") or line.startswith("Hi")) and not body_started:
                body_started = True
            
            # If we've started the body, add all subsequent lines
            if body_started:
                body_lines.append(line)

        # Join the body lines
        body = '\n'.join(body_lines).strip()

        return body