import os
import logging
from protonmail import ProtonMail
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.ERROR)

def clean_email_body(body):
    """
    Clean email body by removing HTML markup, signatures, and extra whitespace.
    Works for HTML, plain text, or mixed formats.
    """
    # If body is empty or None, return empty string
    if not body:
        return ""

    # Check if the body contains HTML tags
    is_html = bool(re.search(r'<[a-zA-Z][^>]*>', body))

    if is_html:
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(body, 'html.parser')

            # Remove common signature blocks
            signature_classes = [
                'protonmail_signature_block',  # Proton Mail
                'gmail_signature',            # Gmail
                'signature',                  # Generic signature class
                'sig',                       # Common abbreviation
                'email-signature'            # Another common class
            ]
            for sig_class in signature_classes:
                for sig in soup.find_all(class_=sig_class):
                    sig.decompose()

            # Remove other common boilerplate (e.g., reply/forward headers)
            for element in soup.find_all(['blockquote', 'div'], class_=re.compile(r'(reply|forward|quoted)')):
                element.decompose()

            # Extract text and clean up whitespace
            text = ' '.join(soup.get_text().split())
        except Exception as e:
            logging.error(f"Error parsing HTML: {str(e)}")
            # Fallback to plain text if HTML parsing fails
            text = ' '.join(body.split())
    else:
        # Handle plain text directly
        text = ' '.join(body.split())

    # Remove common email boilerplate phrases
    boilerplate_patterns = [
        r'Sent from my [^\s]+',           # Sent from my iPhone, Samsung, etc.
        r'Sent with [^\s]+',              # Sent with Proton Mail, etc.
        r'--\s*Sent from',                # Common signature prefix
        r'On\s+.*\swrote:',               # Reply/forward headers
    ]
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Final cleanup: remove extra spaces and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def format_message(idx, message_content):
    """
    Format message details into a clean string.
    """
    # Initialize empty string for message details
    message_details = ""

    # Append message details with fallback for missing attributes
    message_details += f"Message {idx}\n"
    message_details += f"From: {getattr(message_content, 'sender', type('obj', (object,), {'address': 'Unknown'})).address}\n"
    message_details += f"Subject: {getattr(message_content, 'subject', 'No Subject')}\n"
    message_details += f"Body:\n{clean_email_body(getattr(message_content, 'body', ''))}\n"
    message_details += "-" * 40 + "\n"

    return message_details

def read_last_email(username, password, number_of_messages):
    try:
        # Initialize ProtonMail client
        proton = ProtonMail()
        
        # Login to ProtonMail
        logging.info("Logging in to ProtonMail...")
        proton.login(username, password)
        
        # Get list of all messages
        logging.info("Fetching messages...")
        messages = proton.get_messages()
        
        if not messages:
            logging.warning("No messages found in the inbox.")
            return
        
        # Read the last number_of_messages messages (or fewer if less exist)
        last_messages = messages[:number_of_messages]
        
        for idx, message in enumerate(last_messages, 1):
            try:
                # Read the message
                logging.info(f"Reading message {idx}...")
                message_content = proton.read_message(message)
                
                # Format and print message details using format_message
                print(format_message(idx, message_content))
                
            except Exception as e:
                logging.error(f"Error processing message {idx}: {str(e)}")
                
        # Save session for future use
        proton.save_session('session.pickle')
        logging.info("Session saved to session.pickle")
        
        # Revoke all sessions except the current one
        logging.info("Revoking all other sessions...")
        proton.revoke_all_sessions()
        logging.info("All other sessions revoked")
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    # Replace with your ProtonMail credentials
    USERNAME = os.getenv('USERNAME')
    PASSWORD = os.getenv('PASSWORD')
    
    num = 3
    read_last_email(USERNAME, PASSWORD, num)
