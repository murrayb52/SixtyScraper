import email
from datetime import datetime, timedelta
from imapclient import IMAPClient
import json
import pwinput
import os
from bs4 import BeautifulSoup
import pandas as pd

EMAIL_DETAILS_PATH = r"./email_details.json"
SENDER = "no-reply@sixty60.co.za"       # sender address
SEARCH_DAYS_INTO_PAST = 5               # days
SUBJECT = 'Sixty60 invoice for order'   # subject contains string (case sensitive)
MAILS_DIRECTORY = './mails'             # location of manually-downloaded emails
HISTORY_LOCATION = './invoice_history.json'


# ingest email from file and create object
def get_message_from_email_string(raw_message):
    msg = email.message_from_string(raw_message)
    msg.get_payload()


def parse_html_table_to_dataframe(html_content):
    soup = BeautifulSoup(html_content, 'lxml')

    # Find all tables in the HTML content
    tables = soup.find_all('table')

    # Initialize variables to store parsed data and cost breakdown
    parsed_data = None
    cost_breakdown = {}

    # Iterate over each table to find the one with the correct headers
    for table in tables:
        # Find all rows in the table
        rows = table.find_all('tr')

        # Check if the first row contains the correct headers
        if rows:
            headers = rows[0].find_all(['th', 'td'])
            headers_text = [header.text.strip() for header in headers]

            # Check if the table has the expected headers
            if headers_text[:4] == ["Product Details", "QTY", "Price per item", "Total"]:
                product_data = []
                cost_breakdown_data = []

                for row in rows[1:]:
                    cols = row.find_all(['td', 'th'])
                    cols = [ele.text.strip().replace("=\n", "").replace("\n", "").replace("=20\n", "").replace("=20", "").strip() for ele in cols]  # Remove unwanted substrings
                    
                    if len(cols) == 4 and cols[1]:  # Ensure there are exactly 4 columns and QTY is not empty
                        product_data.append(cols)
                    elif len(cols) == 2:  # Handle cost breakdown rows with 2 columns (label and value)
                        cost_breakdown_data.append(cols)

                # Create DataFrame for product data
                parsed_data = pd.DataFrame(product_data, columns=["Product Details", "QTY", "Price per item", "Total"])

                # Extract cost breakdown information from the cost_breakdown_data
                for row in cost_breakdown_data:
                    if "Product Total" in row[0]:
                        cost_breakdown["Product Total"] = row[1]
                    elif "Delivery Fee" in row[0]:
                        cost_breakdown["Delivery Fee"] = row[1]
                    elif "Total" in row[0]:
                        cost_breakdown["Total"] = row[1]
                    elif "Includes VAT of" in row[0]:
                        cost_breakdown["Includes VAT of"] = row[1]

                break  # Stop searching after finding the correct table

    return parsed_data if parsed_data is not None else pd.DataFrame(), cost_breakdown


def dataframe_and_costbreakdown_to_json(parsed_data, cost_breakdown):
    # Convert DataFrame to list of dictionaries
    parsed_data_list = parsed_data.to_dict('records') if not parsed_data.empty else []

    # Combine parsed_data_list and cost_breakdown into a JSON object
    json_object = {
        "Grocery_list": parsed_data_list,
        "Breakdown": cost_breakdown
    }

    return json_object


def get_email_details():
    """
    Deserialize a JSON string into a Python dictionary.

    Args:
        json_str (str): A string containing JSON data.

    Returns:
        dict: A dictionary representing the JSON data.
    """
    try:
        with open(EMAIL_DETAILS_PATH, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        with open(EMAIL_DETAILS_PATH, 'w', encoding='utf-8') as file:
            json.dumps({
                    "HOST": "imap.gmail.com",
                    "USERNAME": "",
                    "PASSWORD": "",
                    "ssl": "True"
                })
        input(f"Please populate the file at '{EMAIL_DETAILS_PATH}'.\nPress 'Enter'to exit. ")
        raise FileNotFoundError()
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON data: {e}")
    except Exception as e:
        raise Exception(f"An error occurred while reading the file: {e}")


def get_password(prompt='Enter your password: '):
    password = pwinput.pwinput(prompt=prompt)
    return password


def fetch_emails(email_details):
    today = datetime.today()
    cutoff = today - timedelta(days=SEARCH_DAYS_INTO_PAST)

    ## Connect, login and select the INBOX
    server = IMAPClient(email_details["HOST"], use_uid=True, ssl='ssl')
    if email_details['PASSWORD'] == "":
        server.login(email_details["USERNAME"], get_password())
    else:
        server.login(email_details["USERNAME"], email_details['PASSWORD'])
    
    select_info = server.select_folder('INBOX')

    ## Search for relevant messages
    ## see http://tools.ietf.org/html/rfc3501#section-6.4.5
    messages = server.search(
        ['FROM %s' % SENDER, 'SINCE %s' % cutoff.strftime('%d-%b-%Y')])
    response = server.fetch(messages, ['RFC822'])               # https://datatracker.ietf.org/doc/html/rfc822

    for msgid, data in response.iteritems():
        msg_string = data['RFC822']
        msg = email.message_from_string(msg_string)
        #print('ID %d: From: %s Date: %s' % (msgid, msg['From'], msg['date']))


# Function to extract data from HTML content
def parse_html(raw_html):
    soup = BeautifulSoup(raw_html, 'lxml')
    
    # Example extraction: get the email subject and body
    subject = soup.find('title').get_text() if soup.find('title') else 'No Subject'
    body = soup.find('body').get_text() if soup.find('body') else 'No Body'
    
    # You can customize this part to extract other relevant information
    return {
        'subject': subject,
        'body': body
    }


def parse_order_details(row_text):
    # Clean up the row text
    cleaned_text = row_text.replace('=20\n', '').replace('=\n', '').replace('\n', '').strip()

    # Initialize variables to store order details
    order_reference = None
    delivery_date_time = None
    your_driver = None

    # Use BeautifulSoup to parse the cleaned text
    soup = BeautifulSoup(cleaned_text, 'html.parser')

    # Find all span tags
    spans = soup.find_all('span')

    # Iterate through spans to extract order details
    for span in spans:
        if 'Order Reference' in span.text:
            order_reference = span.text.split('Order Reference')[-1].strip()
        elif 'Delivery Date & Time' in span.text:
            delivery_date_time = span.text.split('Delivery Date & Time')[-1].strip()
        elif 'Your driver' in span.text:
            your_driver = span.text.split('Your driver')[-1].strip()

    # Construct the Order Details object
    order_details = {
        "Order Reference": order_reference,
        "Delivery Date & Time": delivery_date_time,
        "Your driver": your_driver
    }

    return order_details


def parse_your_details(row_text):
    # Clean up the row text
    cleaned_text = row_text.replace('=20\n', '').replace('=\n', '').strip()

    # Initialize variables to store your details
    customer_name = None
    phone_number = None
    xtra_savings_card_nr = None
    delivery_address = None

    # Split cleaned_text into lines and iterate through them
    lines = cleaned_text.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('Customer Name'):
            customer_name = line.split('Customer Name')[-1].strip()
        elif line.startswith('Phone Number'):
            phone_number = line.split('Phone Number')[-1].strip()
        elif line.startswith('Xtra Savings Card Nr.'):
            xtra_savings_card_nr = line.split('Xtra Savings Card Nr.')[-1].strip()
        elif line.startswith('Delivery Address'):
            delivery_address = line.split('Delivery Address')[-1].strip()

    # Construct the Your Details object
    your_details = {
        "Customer Name": customer_name,
        "Phone Number": phone_number,
        "Xtra Savings Card Nr.": xtra_savings_card_nr,
        "Delivery Address": delivery_address
    }

    return your_details


def parse_invoice_details(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Initialize variables to store parsed details
    your_details = {
        "Customer Name": "",
        "Phone Number": "",
        "Xtra Savings Card Nr.": "",
        "Delivery Address": "",
    }
    order_details = {
        "Order Reference": "",
        "Delivery Date & Time": "",
        "Your driver": "",
    }

    # Find all rows in the HTML content
    large_rows = soup.find_all('tr')

    # Iterate over each large row to extract groups of details
    for large_row in large_rows:

        # Extract "Your Details" section
        if "Your Details" in large_row.text:
            large_row = large_row.text.replace("=\n", "").replace("=20\n", "").replace("<span>", "").replace("</span>", "")
            lines = large_row.split('\n')
            for index in range(len(lines)):
                match(lines[index].strip()):
                    case("Customer Name"):
                        your_details["Customer Name"] = str(lines[index + 3].strip())
                    case("Phone Number"):
                        your_details["Phone Number"] = str(lines[index + 4].strip())
                    case("Xtra Savings Card Nr."):
                        your_details["Xtra Savings Card Nr."] = str(lines[index + 3].strip())
                    case("Delivery Address"):
                        your_details["Delivery Address"] = str(lines[index + 3].strip())

        # Extract "Order Details" section
        elif "Order Details" in large_row.text:
            large_row = large_row.text.replace("=\n", "").replace("=20\n", "").replace("<span>", "").replace("</span>", "")
            lines = large_row.split('\n')
            for index in range(len(lines)):
                match(lines[index].strip()):
                    case("Order Reference"):
                        order_details["Order Reference"] = str(lines[index + 3].strip())
                    case("Delivery Date & Time"):
                        order_details["Delivery Date & Time"] = str(lines[index + 3].strip())
                    case("Your driver"):
                        order_details["Your driver"] = str(lines[index + 3].strip())

    # Construct the invoice object
    invoice_object = {
        "Your Details": your_details,
        "Order Details": order_details
    }

    return invoice_object


def generate_invoice_object(html_content):
    # Simulate fetching details from HTML content (replace with actual parsing logic)
    customer_name = "John Doe"
    phone_number = "+123456789"
    xtra_savings_card_nr = "1234567890"
    delivery_address = "123 Main St, City, Country"
    order_reference = "12345"
    delivery_date_time = "31 December 2024, 14:00"
    driver_name = "John Smith"

    # Parse HTML table to get grocery list and breakdown
    parsed_data, cost_breakdown = parse_html_table_to_dataframe(html_content)

    # Build invoice object
    invoice_object = {
        "Your Details": {
            "Customer Name": customer_name,
            "Phone Number": phone_number,
            "Xtra Savings Card Nr.": xtra_savings_card_nr,
            "Delivery Address": delivery_address
        },
        "Order Details": {
            "Order Reference": order_reference,
            "Delivery Date & Time": delivery_date_time,
            "Your driver": driver_name
        },
        "Grocery_list": parsed_data.to_dict(orient='records') if not parsed_data.empty else [],
        "Breakdown": cost_breakdown
    }

    return invoice_object


def save_invoice_object(invoice_object):
    with open(HISTORY_LOCATION, 'w') as f:
        json.dump(invoice_object, f, indent=4)


def save_invoice_to_history(invoice_object):
    with open(HISTORY_LOCATION, 'w') as f:
        json.dump(all_invoices, f, indent=4, default=str)  # Use default=str to handle non-serializable types

    print(f"Invoice history saved to '{HISTORY_LOCATION}'")


def get_invoice_history():
    # Initialize an empty dict to hold all invoices
    invoice_history = {}

    # Load existing data from history.json if it exists
    if os.path.exists(HISTORY_LOCATION):
        with open(HISTORY_LOCATION, 'r') as f:
            invoice_history = json.load(f)
        print(f"Found previous records in '{HISTORY_LOCATION}'")
    
    return invoice_history


if __name__ == "__main__":
    #email_details = get_email_details()
    #emails = fetch_emails(email_details)
    print("")
    
    all_invoices = get_invoice_history()

    # Extract invoices from email data in the mails directory
    for filename in os.listdir(MAILS_DIRECTORY):
        file_path = os.path.join(MAILS_DIRECTORY, filename)
        
        # Ensure it's a file and not a directory
        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                raw_mail = file.read()

            # Initialize invoice_object as a dictionary
            invoice_object = {}

            # Parse and generate invoice object
            invoice_details = parse_invoice_details(raw_mail)
            parsed_data, cost_breakdown = parse_html_table_to_dataframe(raw_mail)
            invoice_json = dataframe_and_costbreakdown_to_json(parsed_data, cost_breakdown)

            order_reference = invoice_details["Order Details"]["Order Reference"]
            
            invoice_object[order_reference] = {
                "Your Details": invoice_details["Your Details"],
                "Order Details": invoice_details["Order Details"],
                "Grocery_list": invoice_json,  # Assuming this is how your shopping list is structured
                }

            # Update all_invoices with the new invoice data
            all_invoices.update(invoice_object)
            print(f" > Added invoice {order_reference}")

    # Save all_invoices object as JSON in ./invoice_library/{Order Reference}.json
    save_invoice_to_history(all_invoices)