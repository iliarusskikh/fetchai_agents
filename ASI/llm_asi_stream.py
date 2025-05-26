import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve the API key
api_key = os.getenv("ASI1_API_KEY")
if not api_key:
    raise ValueError("API key not found. Ensure ASI1_API_KEY is set in .env file.")

url = "https://api.asi1.ai/v1/chat/completions"

payload = {
    "model": "asi1-extended",
    "messages": [
        {
            "role": "user",
            "content": "Explain the concept of decentralized AI"
        }
    ],
    "temperature": 0.7,
    "stream": True,
    "max_tokens": 500
}

headers = {
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream',  # SSE content type
    'Authorization': f'Bearer {api_key}'  # Use the loaded API key
}

print("Sending the request...")
try:
    # Send the request with streaming enabled
    response = requests.post(url, headers=headers, json=payload, stream=True, timeout=30)
    
    # Check if the request was successful
    response.raise_for_status()
    
    # Verify content type is text/event-stream for SSE
    content_type = response.headers.get('content-type', '')
    if 'text/event-stream' not in content_type:
        print(f"Unexpected content type: {content_type}. Expected text/event-stream.")
        response.close()
        exit(1)
    
    print("Receiving stream...")
    # Iterate over the streaming response
    for line in response.iter_lines():
        if line:
            line_text = line.decode('utf-8')
            #print(f"Raw line: {line_text}")  # Debug output
            if line_text.startswith('data: '):
                data_str = line_text[6:]  # Remove 'data: ' prefix
                if data_str == '[DONE]':
                    print("\nStream ended with [DONE]")
                    break
                try:
                    data = json.loads(data_str)
                    if 'choices' in data and len(data['choices']) > 0:
                        delta = data['choices'][0].get('delta', {})
                        if 'content' in delta and delta['content']:
                            print(delta['content'], end='', flush=True)
                except json.JSONDecodeError as e:
                    print(f"\nJSON decode error: {e} on line: {line_text}")
                    continue
                except KeyError as e:
                    print(f"\nKey error: {e} on data: {data}")
                    continue
        else:
            #pass
            print("Empty line received")
    
    response.close()  # Ensure the connection is closed
except requests.exceptions.HTTPError as http_err:
    print(f"HTTP error occurred: {http_err}")
    print(f"Response text: {response.text}")
except requests.exceptions.RequestException as req_err:
    print(f"Request error occurred: {req_err}")
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    print("\nRequest completed.")
