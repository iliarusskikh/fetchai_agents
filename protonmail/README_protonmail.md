![domain:innovation-lab](https://img.shields.io/badge/innovation--lab-3D8BD3)
![domain:fetchfund](https://img.shields.io/badge/fetchfund-3D23DD)
![tag:fetchfund](https://img.shields.io/badge/fetchfund-4648A3)
![tag:fetchfund](https://img.shields.io/badge/protonmail-4648A3)
![domain:research](https://img.shields.io/badge/research-3D23AD)

# Agent Description
## Role: 

A specialized email agent that connects to the ProtonMail API through an MCP (Model Context Protocol) server. This agent enables secure interaction with ProtonMail accounts, allowing users to read and send emails programmatically.


## Capabilities:

This agent can:


Retrieve and display the latest emails from a ProtonMail inbox
Send emails to specified recipients with custom subjects and message content
Clean email bodies by removing HTML markup, signatures, and boilerplate text
Manage ProtonMail sessions securely, including saving and revoking sessions
Access ProtonMail API through a standardized interface


## Connected MCP Server:


The agent connects to a specialized email server that implements the following tools:



### Read Last Email


Function: read_last_email(username: str, password: str, number_of_messages: int)Description: 
Retrieves the specified number of recent emails from the ProtonMail inbox, returning formatted details including sender, subject, and cleaned body text.Example: Fetch the last 2 emails for a given ProtonMail account.


### Send Email


Function: send_email(username: str, password: str, recipient_email: str, subject: str, message_text: str)Description: 
Sends an email to a specified recipient with a custom subject and message text via the ProtonMail API.Example: Send an email to recipient@protonmail.com with subject "Meeting" and body "Let's meet tomorrow at 10 AM."
