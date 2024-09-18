"""
Email Setup and Notification Module

This module provides functions to set up email configurations and send email notifications.

Functions:
    send_email(too_email, subject, body): Sends an email to the specified recipients.
    notify_success(subject, body): Sends a success notification email.
    notify_failure(subject, body): Sends a failure notification email.
"""

# Standard library imports (for sending emails)
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Application-specific imports from our application(for email configuration details)
from email_setup.email_config import (
    RECEIVER_EMAIL,
    ERROR_HANDLING_GROUP_EMAIL,
    SENDER_EMAIL,
    PASSWORD,
    SMTP_SERVER,
    SMTP_PORT
)


def send_email(too_email, subject, body):
    """
    This function is used to send emails whenever there are changes in CRUD operations
    :param too_email: list of email addresses needed to be sent
    :param subject: The subject of the email
    :param body: The message which user needs to be notified
    :return: None
    """
    if too_email is None:
        too_email = []

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(too_email)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, PASSWORD)
        server.sendmail(SENDER_EMAIL, too_email, msg.as_string())


def notify_success(subject, details):
    """
    Sends a success notification email with detailed information.

    :param subject: Subject of the success email.
    :param details: Detailed information to include in the email body.
    """
    body = f"Successful!\n\nDetails:\n********************************************\n{details}"
    send_email(RECEIVER_EMAIL, subject, body)


def notify_failure(subject, details):
    """
    Sends a failure notification email with detailed information.

    :param subject: Subject of the failure email.
    :param details: Detailed information to include in the email body.
    """
    body = f"Failure!\n\nDetails:\n********************************************\n{details}"
    send_email(ERROR_HANDLING_GROUP_EMAIL, subject, body)


def format_opportunities_for_email(opportunities):
    """
    Format opportunities data for email content.
    :param opportunities: List of opportunities in dictionary format
    :return: str
    """
    email_content = ""
    for opp in opportunities:
        email_content += (
            f"Opportunity ID: {opp['opportunity_id']}\n"
            f"Name: {opp['opportunity_name']}\n"
            f"Account: {opp['account_name']}\n"
            f"Amount: {opp['amount']}\n"
            f"Amount in Words: {opp['amount_in_words']}\n"
            f"Close Date: {opp['close_date']}\n"
            f"Created Date: {opp['created_date']}\n"
            f"Dealer ID: {opp['dealer_id']}\n"
            f"Dealer Code: {opp['dealer_code']}\n"
            f"Stage: {opp['stage']}\n"
            f"Probability: {opp['probability']}%\n"
            f"Next Step: {opp['next_step']}\n"
            f"Description: {opp['description']}\n"
            f"Currency Conversions:\n{opp['currency_conversions']}\n\n"
        )
    return email_content


def notify_opportunity_details(subject, opportunities, total_count):
    """
    Sends an email with detailed opportunity information including the total count.

    :param subject: Subject of the email.
    :param opportunities: List of opportunities in dictionary format to include in the email body.
    :param total_count: Total number of opportunities.
    """
    body = (
        f"Opportunity Details:\n"
        f"********************************************\n"
        f"Total Count of Opportunities: {total_count}\n\n"
    )
    body += format_opportunities_for_email(opportunities)
    send_email(RECEIVER_EMAIL, subject, body)


def notify_customer_creation_success(subject, customer_details):
    """
    Sends a formatted success notification email for a new customer creation.
    :param subject: Subject of the email.
    :param customer_details: Dictionary containing the details of the newly created customer.
    """
    opportunity_id = customer_details.get("opportunity_id")
    opportunity_name = customer_details.get("opportunity_name")
    account_name = customer_details.get("account_name")
    close_date = customer_details.get("close_date").strftime("%d %B %Y, %I:%M %p") if customer_details.get(
        "close_date") else "N/A"
    amount = customer_details.get("amount", "N/A")
    stage = customer_details.get("stage", "N/A")
    probability = customer_details.get("probability", "N/A")
    created_date = customer_details.get("created_date").strftime("%d %B %Y, %I:%M %p")
    currency_conversions = customer_details.get("currency_conversions", {})

    # Build the email content (email body)
    email_content = f"Dear Team,\n\nA new customer has been successfully created with the following details:\n"
    email_content += "********************************************\n"
    email_content += f"Opportunity ID: {opportunity_id}\n"
    email_content += f"Opportunity Name: {opportunity_name}\n"
    email_content += f"Account Name: {account_name}\n"
    email_content += f"Close Date: {close_date}\n"
    email_content += f"Amount: {amount}\n"
    email_content += f"Stage: {stage}\n"
    email_content += f"Probability: {probability}%\n"
    email_content += "Currency Conversions:\n"

    for currency, value in currency_conversions.items():
        email_content += f"   - {currency.upper()}: {value:.2f}\n"

    email_content += f"Created Date: {created_date}\n"
    email_content += "********************************************\n"
    email_content += "\nRegards,\nCustomer Management Team"

    # Send the email
    send_email(RECEIVER_EMAIL, subject, email_content)


def notify_opportunity_update_success(subject, details):
    """
    Sends a formatted success notification email for opportunity updates.
    :param subject: Subject of the email.
    :param details: Dictionary containing the details of the updated opportunity.
    """
    opportunity_id = details.get("opportunity_id")
    updated_fields = details.get("updated_fields", {})

    # Build the email content (email body)
    email_content = f"Dear Team,\n\nThe opportunity has been successfully updated with the following details:\n"
    email_content += "********************************************\n"
    email_content += f"Opportunity ID: {opportunity_id}\n\nUpdated Fields:\n"

    # Formatting updated fields
    index = 1
    if "opportunity_name" in updated_fields:
        email_content += f"{index}. Opportunity Name: {updated_fields['opportunity_name']}\n"
        index += 1
    if "account_name" in updated_fields:
        email_content += f"{index}. Account Name: {updated_fields['account_name']}\n"
        index += 1
    if "close_date" in updated_fields:
        close_date = updated_fields['close_date'].strftime("%d %B %Y, %I:%M %p")
        email_content += f"{index}. Close Date: {close_date}\n"
        index += 1
    if "amount" in updated_fields:
        email_content += f"{index}. Amount: {updated_fields['amount']:.2f}\n"
        index += 1
    if "currency_conversions" in updated_fields:
        conversions = updated_fields['currency_conversions']
        email_content += f"{index}. Currency Conversions:\n"
        for currency, value in conversions.items():
            email_content += f"   - {currency.upper()}: {value:.2f}\n"
        index += 1
    if "description" in updated_fields:
        email_content += f"{index}. Description: {updated_fields['description']}\n"
        index += 1
    if "dealer_id" in updated_fields:
        email_content += f"{index}. Dealer ID: {updated_fields['dealer_id']}\n"
        index += 1
    if "dealer_code" in updated_fields:
        email_content += f"{index}. Dealer Code: {updated_fields['dealer_code']}\n"
        index += 1
    if "stage" in updated_fields:
        email_content += f"{index}. Stage: {updated_fields['stage']}\n"
        index += 1
    if "probability" in updated_fields:
        email_content += f"{index}. Probability: {updated_fields['probability']}%\n"
        index += 1
    if "next_step" in updated_fields:
        email_content += f"{index}. Next Step: {updated_fields['next_step']}\n"
        index += 1
    if "amount_in_words" in updated_fields:
        email_content += f"{index}. Amount in Words: {updated_fields['amount_in_words']}\n"
        index += 1

    email_content += "********************************************\n"
    email_content += "\nRegards,\nOpportunity Management Team"

    # Send the email with the correct recipient list
    send_email(RECEIVER_EMAIL, subject, email_content)
