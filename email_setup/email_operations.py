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
from typing import List, Dict, Optional


# Application-specific imports from our application(for email configuration details)
from email_setup.email_config import (
    RECEIVER_EMAIL,
    ERROR_HANDLING_GROUP_EMAIL,
    SENDER_EMAIL,
    PASSWORD,
    SMTP_SERVER,
    SMTP_PORT
)
from logging_package.logging_utility import log_info, log_error


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
            f"Vehicle Model: {opp['vehicle_model']}\n"
            f"Vehicle Year: {opp['vehicle_year']}\n"
            f"Vehicle Color: {opp['vehicle_color']}\n"
            f"Amount: {opp['amount']}\n"
            f"Vehicle Model ID: {opp['vehicle_model_id']}\n"
            f"********************************************\n\n"
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
    if "vehicle_model" in updated_fields:
        email_content += f"{index}. Vehicle Model: {updated_fields['vehicle_model']}\n"
        index += 1
    if "vehicle_year" in updated_fields:
        email_content += f"{index}. Vehicle Year: {updated_fields['vehicle_year']}\n"
        index += 1
    if "vehicle_color" in updated_fields:
        email_content += f"{index}. Vehicle Color: {updated_fields['vehicle_color']}\n"
        index += 1

    email_content += "********************************************\n"
    email_content += "\nRegards,\nOpportunity Management Team"

    # Send the email with the correct recipient list
    send_email(RECEIVER_EMAIL, subject, email_content)


def notify_warning(subject, details):
    """
    Sends a warning notification email with detailed information.

    :param subject: Subject of the warning email.
    :param details: Detailed information to include in the email body.
    """
    body = f"Warning!\n\nDetails:\n********************************************\n{details}"
    send_email(ERROR_HANDLING_GROUP_EMAIL, subject, body)


def format_vehicle_details(vehicle):
    """
    Formats vehicle details into a structured format for emails or return responses.
    :param vehicle: Dictionary or object containing vehicle details.
    :return: Formatted string of vehicle details.
    """
    return (
        f"Vehicle Model: {vehicle.get('vehicle_model')}\n"
        f"Vehicle Year: {vehicle.get('vehicle_year')}\n"
        f"Engine Type: {vehicle.get('engine_type', 'N/A')}\n"
        f"Transmission: {vehicle.get('transmission', 'N/A')}\n"
        f"Fuel Type: {vehicle.get('fuel_type', 'N/A')}\n"
        f"Body Type: {vehicle.get('body_type', 'N/A')}\n"
        f"Warranty Period (years): {vehicle.get('warranty_period_years', 'N/A')}\n"
        f"Color: {vehicle.get('color', 'N/A')}\n"
        f"Model Variant: {vehicle.get('model_variant', 'N/A')}\n"
        f"Tyre Company: {vehicle.get('tyre_company', 'N/A')}\n"
        f"Tyre Size: {vehicle.get('tyre_size', 'N/A')}\n"
        f"Start Type: {vehicle.get('start_type', 'N/A')}\n"
        f"Sunroof Available: {vehicle.get('sunroof_available', 'N/A')}\n"
        f"Gear Type: {vehicle.get('gear_type', 'N/A')}\n"
        f"Vehicle Type: {vehicle.get('vehicle_type', 'N/A')}\n"
    )


def generate_vehicle_details_email_body(
        vehicles_info: Optional[List[Dict]] = None,
        vehicle_info: Optional[Dict] = None,
        total_count: Optional[int] = None,
        vehicle_model_id: Optional[str] = None,
        include_additional_info: bool = False
) -> str:
    """
    Generates an email body with vehicle details in a structured format.

    :param vehicles_info: List of dictionaries containing details of all vehicles.
    :param vehicle_info: Dictionary containing details of a specific vehicle.
    :param total_count: Total number of vehicles.
    :param vehicle_model_id: Vehicle model ID for the specific vehicle.
    :param include_additional_info: Whether to include additional information.
    :return: A formatted string to be used as the email body.
    """
    email_body = "Hello,\n\n"

    if vehicles_info:
        email_body += f"Here are the details for all vehicles retrieved from the database:\n\n"
        email_body += f"Total Number of Vehicles: {total_count}\n\n"
        email_body += "Vehicle Details:\n"

        for vehicle in vehicles_info:
            email_body += (
                f"---\n"
                f"Vehicle Model ID: {vehicle.get('vehicle_model_id', 'N/A')}\n"
                f"Vehicle Model: {vehicle.get('vehicle_model', 'N/A')}\n"
                f"Vehicle Year: {vehicle.get('vehicle_year', 'N/A')}\n"
                f"Engine Type: {vehicle.get('engine_type', 'N/A')}\n"
                f"Transmission: {vehicle.get('transmission', 'N/A')}\n"
                f"Fuel Type: {vehicle.get('fuel_type', 'N/A')}\n"
                f"Body Type: {vehicle.get('body_type', 'N/A')}\n"
                f"Warranty Period (Years): {vehicle.get('warranty_period_years', 'N/A')}\n"
                f"Color: {vehicle.get('color', 'N/A')}\n"
                f"Model Variant: {vehicle.get('model_variant', 'N/A')}\n"
                f"Tyre Company: {vehicle.get('tyre_company', 'N/A')}\n"
                f"Tyre Size: {vehicle.get('tyre_size', 'N/A')}\n"
                f"Start Type: {vehicle.get('start_type', 'N/A')}\n"
                f"Sunroof Available: {vehicle.get('sunroof_available', 'N/A')}\n"
                f"Gear Type: {vehicle.get('gear_type', 'N/A')}\n"
                f"Vehicle Type: {vehicle.get('vehicle_type', 'N/A')}\n"
                f"---\n\n"
            )

    elif vehicle_info:
        email_body += f"Here are the details for the vehicle with ID {vehicle_model_id}:\n\n"
        email_body += (
            f"Vehicle Model ID: {vehicle_info.get('vehicle_model_id', 'N/A')}\n"
            f"Vehicle Model: {vehicle_info.get('vehicle_model', 'N/A')}\n"
            f"Vehicle Year: {vehicle_info.get('vehicle_year', 'N/A')}\n"
            f"Engine Type: {vehicle_info.get('engine_type', 'N/A')}\n"
            f"Transmission: {vehicle_info.get('transmission', 'N/A')}\n"
            f"Fuel Type: {vehicle_info.get('fuel_type', 'N/A')}\n"
            f"Body Type: {vehicle_info.get('body_type', 'N/A')}\n"
            f"Warranty Period (Years): {vehicle_info.get('warranty_period_years', 'N/A')}\n"
            f"Color: {vehicle_info.get('color', 'N/A')}\n"
            f"Model Variant: {vehicle_info.get('model_variant', 'N/A')}\n"
            f"Tyre Company: {vehicle_info.get('tyre_company', 'N/A')}\n"
            f"Tyre Size: {vehicle_info.get('tyre_size', 'N/A')}\n"
            f"Start Type: {vehicle_info.get('start_type', 'N/A')}\n"
            f"Sunroof Available: {vehicle_info.get('sunroof_available', 'N/A')}\n"
            f"Gear Type: {vehicle_info.get('gear_type', 'N/A')}\n"
            f"Vehicle Type: {vehicle_info.get('vehicle_type', 'N/A')}\n"
            f"---\n\n"
        )

        if include_additional_info:
            email_body += f"Additional Information: {vehicle_info.get('additional_info', 'N/A')}\n\n"

    email_body += "Best regards,\nYour Team"

    return email_body


def generate_detailed_vehicle_email(vehicle_info, action="Update", admin_email=None):
    """
    Generates a detailed email format for vehicle details.

    :param vehicle_info: Dict containing vehicle details
    :param action: Action performed on the vehicle (e.g., "Update")
    :param admin_email: The recipient email address
    :return: String containing the formatted email body
    """
    email_body = f"""
    Dear Team,

    This email is to inform you that the following vehicle has been {action.lower()}d successfully:

    Vehicle Details:
    -----------------------------------------------------
    Vehicle Model ID         : {vehicle_info['vehicle_model_id']}
    Vehicle Model            : {vehicle_info['vehicle_model']}
    Vehicle Year             : {vehicle_info['vehicle_year']}
    Engine Type              : {vehicle_info['engine_type']}
    Transmission             : {vehicle_info['transmission']}
    Fuel Type                : {vehicle_info['fuel_type']}
    Body Type                : {vehicle_info['body_type']}
    Warranty Period (Years)  : {vehicle_info['warranty_period_years']}
    Color                    : {vehicle_info['color']}
    Model Variant            : {vehicle_info['model_variant']}
    Tyre Company             : {vehicle_info['tyre_company']}
    Tyre Size                : {vehicle_info['tyre_size']}
    Start Type               : {vehicle_info['start_type']}
    Sunroof Available        : {vehicle_info['sunroof_available']}
    Gear Type                : {vehicle_info['gear_type']}
    Vehicle Type             : {vehicle_info['vehicle_type']}
    -----------------------------------------------------

    Please review the details above. If you have any concerns, kindly reach out to the admin at {admin_email}.

    Best regards,
    Your Vehicle Management Team
    """
    return email_body


def send_deletion_email(
        to_email: List[str],
        num_deleted: int,
        criteria: Dict[str, str],
        deleted_vehicles: List[Dict[str, str]]
) -> None:
    """
    Sends an email notification about vehicle deletion using SMTP.

    :param to_email: List of recipient email addresses.
    :param num_deleted: Number of vehicles deleted.
    :param criteria: Dictionary of criteria used for the deletion.
    :param deleted_vehicles: List of deleted vehicles' details.
    """
    email_subject = "Vehicles Deleted"

    # Generate the email body
    email_body = generate_vehicle_details_email_body(
        vehicles_info=deleted_vehicles,
        total_count=num_deleted
    )

    # Add criteria to the email body
    criteria_body = "Criteria Used for Deletion:\n" + ''.join(
        [f'{key}: {value}\n' for key, value in criteria.items() if value]) + '\n'
    email_body += criteria_body

    # Create and send the email
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(to_email)
    msg['Subject'] = email_subject
    msg.attach(MIMEText(email_body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())

        log_info(f"Email sent successfully to {', '.join(to_email)} with subject '{email_subject}'.")

    except Exception as e:
        log_error(f"Failed to send email to {', '.join(to_email)}. Error: {str(e)}")
