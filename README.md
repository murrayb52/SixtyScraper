# Checkers Sixty60 Invoice Processing Program

This program is designed to fetch, parse, and store invoice data from Checkers Sixty60 emails. It retrieves emails from a specified email account, parses the HTML content of invoices using BeautifulSoup, converts relevant data into pandas DataFrames, and then saves the processed data into JSON format for further use.

## Features

- **Email Retrieval**: Fetches emails from a specified email account using IMAP.
- **HTML Parsing**: Uses BeautifulSoup to extract structured data (invoice details and product lists) from HTML content.
- **Data Handling**: Utilizes pandas DataFrames to organize and manipulate invoice data.
- **JSON Serialization**: Converts parsed invoice data into JSON format for storage and further processing.

## Requirements

- Python 3.x
- Libraries:
  - `email`: For handling email messages.
  - `imapclient`: For connecting to and retrieving emails from an IMAP server.
  - `beautifulsoup4`: For parsing HTML content.
  - `pandas`: For data manipulation and analysis.
  - `json`: For handling JSON data serialization and deserialization.
  - `pwinput`: For securely inputting passwords.
  
## Installation

1. Clone this repository to your local machine:

   ```bash
   git clone https://github.com/your/repository.git

2. Install required Python libraries:
    ```bash
    pip install -r requirements.txt

3. Populate email_details.json with your email account details. Ensure it contains the following fields:
    ```bash
    {
    "HOST": "imap.your-email-provider.com",
    "USERNAME": "your-email@example.com",
    "PASSWORD": "your-email-password",
    "ssl": "True"
    }


## Usage

1. Ensure that your email_details.json file is properly populated with your email account details.

2.  Place your email invoices in the mails directory (if not fetching directly from email).

3.  Run the program:
    ```bash
    python main.py

4. The program will process each email or file in the mails directory, extract invoice data, and save it to invoice_library/history.json.


## Notes
    Data Structure: Each invoice is stored as a JSON object containing details such as customer information, order details, grocery lists, and cost breakdowns.
    Error Handling: The program includes basic error handling for missing files or incorrect JSON formatting in email_details.json.