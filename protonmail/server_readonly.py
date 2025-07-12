from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import os
import logging
from protonmail import ProtonMail
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv
import asyncio

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)  # Changed to INFO to see ProtonMail logs

# Create a FastMCP server instance
mcp = FastMCP("protonmail")

def clean_email_body(body):
    """
    Clean email body by removing HTML markup, signatures, and extra whitespace.
    Works for HTML, plain text, or mixed formats.
    """
    if not body:
        return ""

    is_html = bool(re.search(r'<[a-zA-Z][^>]*>', body))

    if is_html:
        try:
            soup = BeautifulSoup(body, 'html.parser')
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

            for element in soup.find_all(['blockquote', 'div'], class_=re.compile(r'(reply|forward|quoted)')):
                element.decompose()

            text = ' '.join(soup.get_text().split())
        except Exception as e:
            logging.error(f"Error parsing HTML: {str(e)}")
            text = ' '.join(body.split())
    else:
        text = ' '.join(body.split())

    boilerplate_patterns = [
        r'Sent from my [^\s]+',
        r'Sent with [^\s]+',
        r'--\s*Sent from',
        r'On\s+.*\swrote:',
    ]
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    text = re.sub(r'\s+', ' ', text).strip()
    return text


def format_message(idx, message_content) -> str:
    """
    Format message details into a clean string.
    """
    message_details = ""
    message_details += f"Message {idx}\n"
    message_details += f"From: {getattr(message_content, 'sender', type('obj', (object,), {'address': 'Unknown'})).address}\n"
    message_details += f"Subject: {getattr(message_content, 'subject', 'No Subject')}\n"
    message_details += f"Body:\n{clean_email_body(getattr(message_content, 'body', ''))}\n"
    message_details += "-" * 40 + "\n"
    return message_details

async def run_in_thread(func, *args):
    """
    Run a synchronous function in a separate thread to avoid blocking the event loop.
    """
    return await asyncio.to_thread(func, *args)


@mcp.tool()
async def read_last_email(username: str, password: str, number_of_messages: int) -> str:
    """Fetches the received messages from ProtonMail API. Receives username (email address), user password, number of messages. Returns requested received messages as a string."""
    try:
        # Initialize ProtonMail client
        proton = ProtonMail()
        output = ""

        # Login to ProtonMail
        logging.info("Logging in to ProtonMail...")
        await run_in_thread(proton.login, username, password)

        # Get list of all messages
        logging.info("Fetching messages...")
        messages = await run_in_thread(proton.get_messages)

        if not messages:
            logging.warning("No messages found in the inbox.")
            return "No messages found in the inbox."

        # Read the last number_of_messages messages (or fewer if less exist)
        last_messages = messages[:number_of_messages]

        for idx, message in enumerate(last_messages, 1):
            try:
                # Read the message
                logging.info(f"Reading message {idx}...")
                message_content = await run_in_thread(proton.read_message, message)

                # Append formatted message to output
                output += format_message(idx, message_content)

            except Exception as e:
                logging.error(f"Error processing message {idx}: {str(e)}")
                output += f"Error processing message {idx}: {str(e)}\n{'-' * 40}\n"

        # Save session for future use
        await run_in_thread(proton.save_session, 'session.pickle')
        logging.info("Session saved to session.pickle")

        # Revoke all sessions except the current one
        logging.info("Revoking all other sessions...")
        await run_in_thread(proton.revoke_all_sessions)
        logging.info("All other sessions revoked")

        return output if output else "No messages processed."

    except Exception as e:
        exception_msg = f"An error occurred: {str(e)}"
        logging.error(exception_msg)
        return exception_msg

if __name__ == "__main__":
    # Run the FastMCP server
    mcp.run(transport='stdio')
