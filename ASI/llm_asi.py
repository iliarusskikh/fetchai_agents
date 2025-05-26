import requests
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Retrieve the API key from environment variables
api_key = os.getenv("ASI1_API_KEY")

# ASI1-Mini LLM API endpoint
url = "https://api.asi1.ai/v1/chat/completions"

# Define headers for API requests, including authentication
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Bearer {api_key}"
}

def query_llm(query):
    data = {
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant specialized in Web3 technologies."
            },
            {
                "role": "user", #The role of the message author. Must be one of "system", "user", or "assistant".
                "content": query
            }
        ],  # User input for the chat model
        "conversationId": None,  # No conversation history tracking
        "model": "asi1-extended",  # Specifies the model version to use
        "temperature": 0.1,#between 0 and 2
        "stream": False,
        #"max_tokens": 0
    }

    try:
        # Send a POST request to the LLM API with the input query
        with requests.post(url, headers=headers, json=data) as response:
            output = response.json()  # Parse the JSON response

            # Extract and return the generated message content
            print(f"Prompt tokens:{output['usage']['prompt_tokens']} \n")
            print(f"Completion tokens:{output['usage']['completion_tokens']} \n")
            print(f"Total tokens:{output['usage']['total_tokens']} \n")

            return output["choices"][0]["message"]["content"]
    
    except requests.exceptions.RequestException as e:
        # Handle and return any request-related exceptions (e.g., network errors)
        return str(e)

print(query_llm("What is the most expensive city in the world!"))
