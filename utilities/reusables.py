"""
This module contains all reusable functions that can be used based on requirements in app.py
"""

# Regular expression module import
import re

# Date and time import
from datetime import datetime, timedelta

from user_models.tables import Taxes


def get_opportunity_stage(probability):
    """
    Determine the sales opportunity stage based on the probability value.

    :param probability: Integer representing the probability percentage (0 to 100).
    :return: String representing the stage name.
    :raises ValueError: If the probability value is out of range (0-100) or invalid.
    """
    if 10 <= probability <= 20:
        return "Prospecting"
    elif 21 <= probability <= 40:
        return "Qualification"
    elif 41 <= probability <= 60:
        return "Needs Analysis"
    elif 61 <= probability <= 70:
        return "Value Proposition"
    elif 71 <= probability <= 80:
        return "Decision Makers"
    elif 81 <= probability <= 85:
        return "Perception Analysis"
    elif 86 <= probability <= 90:
        return "Proposal/Price Quote"
    elif 91 <= probability <= 95:
        return "Negotiation/Review"
    elif probability == 100:
        return "Closed Won"
    elif probability == 0:
        return "Closed Lost"
    else:
        raise ValueError("Invalid probability value")


def get_currency_conversion(amount):
    """
    Convert a given amount from INR to various other currencies using predefined rates.

    :param amount: Amount in INR to be converted.
    :return: Dictionary with the amount converted to various currencies (USD, AUD, CAD, JPY, EUR, GBP, CNY) and INR.
    """
    # Dummy conversion rates (assumed for demonstration)
    usd_rate = 10
    aus_rate = 5
    cad_rate = 1
    jpy_rate = 1.76
    eur_rate = 0.012
    gbp_rate = 20
    cny_rate = 6

    # Perform currency conversions
    usd = amount * usd_rate
    aus = amount * aus_rate
    cad = amount * cad_rate
    jpy = amount * jpy_rate
    eur = amount * eur_rate
    gbp = amount * gbp_rate
    cny = amount * cny_rate

    # Return a dictionary with all conversions rounded to 2 decimal places
    return {
        'USD': round(usd, 2),
        'AUD': round(aus, 2),
        'CAD': round(cad, 2),
        'JPY': round(jpy, 2),
        'EUR': round(eur, 2),
        'GBP': round(gbp, 2),
        'CNY': round(cny, 2),
        'INR': round(amount, 2)  # Original amount in INR
    }


def validate_probability(prob):
    """
    Validate probability value.
    :param prob: Probability value.
    :return: Boolean indicating validity.
    """
    return isinstance(prob, int) and 0 <= prob <= 100


def validate_positive_number(value):
    """
    Validate positive number.
    :param value: Number to validate.
    :return: Boolean indicating validity.
    """
    return isinstance(value, (int, float)) and value > 0


def validate_stage(stage_str):
    """
    Validate stage value.
    :param stage_str: Stage value to validate.
    :return: None if valid, otherwise raises ValueError.
    """
    stage_str = stage_str.strip()  # Remove leading and trailing spaces
    if not stage_str:
        raise ValueError("Stage value cannot be empty or contain only spaces.")
    if not re.match(r'^[A-Za-z\s]+$', stage_str):
        raise ValueError(f"Invalid stage value: '{stage_str}'. Must contain only letters and spaces.")
    if len(stage_str) > 100:  # Assuming a max length of 100 characters
        raise ValueError(f"Stage is too long. Maximum length is 100 characters.")
    return stage_str


def parse_date(date_str):
    """
    Parse date from string.
    :param date_str: Date string.
    :return: Parsed datetime object.
    """
    try:
        return datetime.strptime(date_str, "%I:%M %p, %B %d, %Y")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Expected format: '10:00 AM, September 30, 2024'")


def schedule_next_service(purchase):
    """
    Schedule the next service for a purchased vehicle based on kilometers or date.
    :param purchase: PurchasedVehicles instance
    :return: dict containing next service details
    """
    # Assuming service intervals are after 5000 kilometers or 6 months
    kilometers_interval = 5000
    months_interval = 6
    next_service_due_kilometers = purchase.current_kilometers + kilometers_interval
    next_service_due_date = purchase.purchase_date + timedelta(days=months_interval * 30)

    next_service_info = {
        "service_type": "Regular Maintenance",
        "due_date": next_service_due_date.strftime("%B %d, %Y"),
        "kilometers_due": next_service_due_kilometers
    }

    return next_service_info


def calculate_taxes(vehicle_id, tax_amount):
    """
    Create a tax record for a given vehicle.

    :param vehicle_id: ID of the vehicle for which the tax is being calculated.
    :param tax_amount: Amount of the tax.
    :return: A Taxes instance representing the tax record.
    """
    # Create a tax record
    tax_record = Taxes(
        vehicle_id=vehicle_id,
        tax_amount=tax_amount,
        tax_type="Road Tax",  # Example type, this could be dynamic based on context
        due_date=datetime.now() + timedelta(days=365)  # Example due date: 1 year from now
    )
    return tax_record


from functools import wraps
from flask import request, jsonify
import random
import time

# In-memory store for OTPs (you should replace this with a database in a production environment)
otp_store = {}





# Universal OTP Decorator
def otp_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        payload = request.get_json()

        # Check if the payload contains the email and OTP
        if not payload or 'email' not in payload or 'otp' not in payload:
            return jsonify({"error": "Email and OTP are required."}), 400

        email = payload['email']
        otp = payload['otp']

        # Check if OTP exists for this email
        if email not in otp_store:
            return jsonify({"error": "No OTP generated for this email."}), 400

        stored_otp_data = otp_store[email]
        if time.time() - stored_otp_data['timestamp'] > 300:  # OTP valid for 5 minutes
            return jsonify({"error": "OTP has expired."}), 400
        if int(otp) != stored_otp_data['otp']:
            return jsonify({"error": "Invalid OTP."}), 400

        # OTP is valid, proceed with the function
        return func(*args, **kwargs)

    return wrapper
