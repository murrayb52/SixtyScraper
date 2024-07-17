# Sixty60 Invoice Parser

## Overview

This Python script automates the parsing and storage of Sixty60 grocery delivery invoices from email. It converts HTML invoices into structured JSON format for easy storage and analysis.

## Usage

Checkers allows users to have invoices sent to their email address. This program will scrape the HTML from the email file to extract the invoice data and store it in a usable form.

### 1. Get your invoices
To request your invoices be sent to your email address:
**On the Sixty60 App:**
   - Navigate to Profile > Orders.
   - Click on each order to view details.
   - Click "Request Invoice" to have the invoice emailed to your registered email address.

### 2. Email Retrieval
Save the received invoice emails as `.eml` files into the `./mails` directory of this project.
Due to current limitations, emails cannot be automatically retrieved. This is planned for a future update.

### 3. Setup the environment
   - Install dependencies (see _Installation_ section)
   - Ensure that your email_details.json file is properly populated with your email account details. If you prefer leaving your password out, it will be requested whenever you run the programme.

### 3. Run the programme
- The script automatically parses the HTML content of each `.eml` file in the `./mails` directory.
- It extracts the invoice data from the HTML tables within each email.
- It creates a JSON object for each invoice and updates the `invoice_history.json` file while preserving existing data.

## Features
- **HTML Parsing**: Uses BeautifulSoup to extract structured data (invoice details and product lists) from HTML content.
- **Data Handling**: Utilizes pandas DataFrames to organize and manipulate invoice data.
- **JSON Serialization**: Converts parsed invoice data into JSON format for storage and further processing.

## Future Plans
- **Automated Email Retrieval:** Future updates aim to automate the retrieval of Sixty60 invoice emails directly from your inbox using IMAP. This will reduce manual effort and streamline the invoice processing workflow.
- **Monthly Expense Reports:**

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
   git clone https://github.com/your_username/Sixty60-Invoice-Parser.git
   cd Sixty60-Invoice-Parser

2. Install required Python libraries:
    ```bash
    pip install -r requirements.txt

3. Populate email_details.json with your email account details. Ensure it contains the following fields:
    ```bash
    {
        "HOST": "imap.your-email-provider.com",
        "USERNAME": "your-email@example.com",
        "PASSWORD": "your-email-password",
    }