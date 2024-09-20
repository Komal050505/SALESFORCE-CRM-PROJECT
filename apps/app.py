"""
This module contains api's for Account table operations, Dealer table operations and Opportunity table operations
"""

# Standard library imports
import uuid  # For generating universally unique identifiers (UUIDs)
from datetime import datetime  # For date and time manipulations

# Third-Party/External Library Imports
import pytz  # For timezone handling and conversions
from flask import Flask, request, jsonify  # For building web applications and handling requests/responses
from sqlalchemy.exc import SQLAlchemyError  # For handling SQLAlchemy database exceptions

# # # Project-Specific Imports ********
# Database Session
from db_connections.configurations import session  # For managing database session connections
from email_setup.email_config import RECEIVER_EMAIL

# Email Operations
from email_setup.email_operations import (  # Email notifications
    notify_success,
    notify_failure,
    notify_opportunity_details,
    notify_opportunity_update_success, format_vehicle_details, send_email,
    generate_vehicle_details_email_body, generate_detailed_vehicle_email, send_deletion_email,
    generate_user_vehicle_purchase_email, generate_team_vehicle_purchase_email,
    generate_error_email, generate_success_email, notify_vehicle_update_success
)

# Logging Utility
from logging_package.logging_utility import (  # Logging information, errors, and debugging
    log_info,
    log_error,
    log_debug
)

# User Models
from user_models.tables import Account, Dealer, Opportunity, \
    VehicleDetails, PurchasedVehicles, Insurance, \
    VehicleServices, Taxes  # Database models for account, dealer, and opportunity

# Utility Functions
from utilities.reusables import (  # Reusable utility functions for validations and conversions
    get_currency_conversion,
    get_opportunity_stage,
    validate_stage,
    validate_probability,
    parse_date,
    validate_positive_number, schedule_next_service, calculate_taxes
)

# Create Flask app instance
app = Flask(__name__)


# ----------------------------------------------- ACCOUNT TABLE ------------------------------------------------
@app.route('/add-account', methods=['POST'])
def add_account():
    """
    Adds new accounts to account table
    :return: JSON response with email notifications
    """
    log_info("Received request to add new account")
    try:
        payload = request.get_json()
        log_debug(f"Request payload: {payload}")

        if not payload or 'account_id' not in payload or 'account_name' not in payload:
            error_message = "Invalid input data. 'account_id' and 'account_name' are required."
            log_error(error_message)
            notify_failure("Add Account Failed", error_message)
            return jsonify({"error": error_message}), 400

        new_account = Account(
            account_id=payload['account_id'],
            account_name=payload['account_name']
        )

        session.add(new_account)
        session.commit()
        log_info(f"Account added successfully: {payload['account_id']}")

        success_message = (f"Account added successfully.\nAccount ID: {payload['account_id']}\n"
                           f"Account Name: {payload['account_name']}")
        notify_success("Add Account Successful", success_message)

        return jsonify({"message": "Account added successfully", "account_id": payload['account_id'],
                        "account_name": payload['account_name']}), 201

    except SQLAlchemyError as e:
        session.rollback()
        error_message = f"Error inserting account: {str(e)}"
        log_error(error_message)
        notify_failure("Add Account Failed", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        log_error(error_message)
        notify_failure("Add Account Failed", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500
    finally:
        log_info("End of add_account function")


@app.route('/get-all-accounts', methods=['GET'])
def get_all_accounts():
    """
    Fetches all accounts from the account table.
    :return: JSON response with account details and total count, and sends an email notification.
    """
    log_info("Received request to get all accounts")
    try:
        # Fetch accounts from the database
        accounts = session.query(Account).all()
        total_count = len(accounts)
        log_info(f"Fetched {total_count} accounts")

        accounts_list = []
        for account in accounts:
            account_dict = account.account_serialize_to_dict()

            # Format currency_conversions
            if isinstance(account_dict.get('currency_conversions'), str):
                currency_conversions = {}
                conversions = account_dict['currency_conversions'].strip().split('\n')
                for conversion in conversions:
                    if conversion:
                        currency, value = conversion.split(': ', 1)
                        currency_conversions[currency] = value
                account_dict['currency_conversions'] = currency_conversions

            accounts_list.append(account_dict)

        # Format account details for response
        account_details = "\n".join(
            [f"Account ID: {account['account_id']}\n"
             f"Account Name: {account['account_name']}\n"
             f"Currency Conversions:\n" +
             "\n".join(
                 [f"{currency}: {value}" for currency, value in account.get('currency_conversions', {}).items()]) + "\n"
             for account in accounts_list]
        )

        # Construct success message
        success_message = (
            f"Successfully retrieved Total {total_count} accounts.\n\n"
            f"Account Details:\n*********************************************\n{account_details}\n"
            f"\nTotal count of accounts: {total_count}"
        )

        # Send email notification
        notify_success("Get All Accounts Successful", success_message)

        # Return JSON response
        return jsonify({"Accounts": accounts_list, "Total count of accounts": total_count}), 200

    except Exception as e:
        # Handle exception
        error_message = f"Error in fetching accounts: {str(e)}"
        log_error(error_message)
        notify_failure("Get Accounts Failed", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500
    finally:
        log_info("End of get_all_accounts function")


@app.route('/get-single-account', methods=['GET'])
def get_single_account():
    """
    Fetched single account details
    :return: JSON response with email notifications
    """
    log_info(f"Received request to get account details with account id {'account_id'}")
    try:
        # Fetch account_id from query parameters
        accountid = request.args.get('account_id')
        log_debug(f"Account ID fetched is: {accountid}")

        # Check if account_id is provided
        if not accountid:
            error_message = "Account ID not provided or invalid. Please provide a valid Account ID."
            log_error(error_message)
            notify_failure("Get Single Account Failed", error_message)  # Send email for failure
            return jsonify({"error": error_message}), 400

        # Fetch the account from the database
        account = session.query(Account).filter_by(account_id=accountid).first()

        if not account:
            error_message = f"Account not found: {accountid}"
            log_error(error_message)
            notify_failure("Get Single Account Failed", error_message)  # Send email for failure
            return jsonify({"error": "Account not found"}), 404

        log_info(f"Fetched account: {accountid}")

        # Serialize account data to dictionary
        account_details = account.account_serialize_to_dict()

        # Prepare success message
        success_message = (f"Successfully fetched single account details - "
                           f"\n\nAccount ID: {account_details['account_id']}, "
                           f"\nName: {account_details['account_name']}")

        # Send email notification with the account details
        notify_success("Get Single Account Success", success_message)

        # Return response with serialized account details
        return jsonify({"Account": account_details, "Message": "Single Account Details:"}), 200

    except Exception as e:
        error_message = f"Error in fetching account: {str(e)}"
        log_error(error_message)
        notify_failure("Get Single Account Failed", error_message)  # Send email for failure
        return jsonify({"error": "Internal server error", "details": error_message}), 500

    finally:
        log_info("End of get_single_account function")


@app.route('/update-account', methods=['PUT'])
def update_account():
    """
    Updates account name
    :return: JSON response with email notifications
    """
    log_info("Received request to update account details")
    try:
        data = request.get_json()
        account_id = data.get('account_id')
        new_account_name = data.get('account_name')

        log_debug(f"Account ID to update: {account_id}, New Name: {new_account_name}")

        if not account_id or not new_account_name:
            error_message = "Account ID and new Account Name must be provided."
            log_error(error_message)
            notify_failure("Update Account Failed", error_message)
            return jsonify({"error": error_message}), 400

        account = session.query(Account).filter_by(account_id=account_id).first()

        if not account:
            error_message = f"Account not found: {account_id}"
            log_error(error_message)
            notify_failure("Update Account Failed", error_message)
            return jsonify({"error": "Account not found"}), 404

        account.account_name = new_account_name
        session.commit()

        success_message = (f"Account ID: \n{account_id}\n\n"
                           f"Successfully updated with new name: \n{new_account_name}")
        log_info(success_message)
        notify_success("Update Account Success", success_message)

        return jsonify({
            "message": "Account details updated successfully.",
            "account_id": account_id,
            "new_account_name": new_account_name
        }), 200

    except Exception as e:
        error_message = f"Error in updating account: {str(e)}"
        log_error(error_message)
        notify_failure("Update Account Failed", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500

    finally:
        log_info("End of update_account function")


@app.route('/delete-account', methods=['DELETE'])
def delete_account():
    """
    Deletes account based on account id
    :return: JSON response with email notifications
    """
    log_info("Received request to delete account")
    try:
        account_id = request.args.get('account_id')
        log_debug(f"Account ID to delete: {account_id}")

        if not account_id:
            error_message = "Account ID must be provided."
            log_error(error_message)
            notify_failure("Delete Account Failed", error_message)
            return jsonify({"error": error_message}), 400

        account = session.query(Account).filter_by(account_id=account_id).first()

        if not account:
            error_message = f"Account not found: {account_id}"
            log_error(error_message)
            notify_failure("Delete Account Failed", error_message)
            return jsonify({"error": "Account not found"}), 404

        session.delete(account)
        session.commit()

        success_message = (f"Account ID: {account_id}\n"
                           f"Successfully account deleted. Details:\n"
                           f"Account ID: {account.account_id}\n"
                           f"Account Name: {account.account_name}")
        log_info(success_message)
        notify_success("Delete Account Success", success_message)

        return jsonify({
            "message": "Account successfully deleted.",
            "deleted_account_id": account_id,
            "account_name": account.account_name
        }), 200

    except Exception as e:
        error_message = f"Error in deleting account: {str(e)}"
        log_error(error_message)
        notify_failure("Delete Account Failed", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500

    finally:
        log_info("End of delete_account function")


# ----------------------------------------------- DEALER TABLE ------------------------------------------------

@app.route('/add-dealer', methods=['POST'])
def add_dealer():
    """
    Adds new Dealer to the dealer table
    :return: JSON response with email notifications
    """
    log_info("Received request to add new dealer")
    try:
        payload = request.get_json()
        log_debug(f"Request payload: {payload}")

        if not payload or 'dealer_code' not in payload or 'opportunity_owner' not in payload:
            error_message = "Invalid input data. 'dealer_code' and 'opportunity_owner' are required."
            log_error(error_message)
            notify_failure("Add Dealer Failed", error_message)
            return jsonify({"error": error_message}), 400

        new_dealer = Dealer(
            dealer_code=payload['dealer_code'],
            opportunity_owner=payload['opportunity_owner']
        )

        session.add(new_dealer)
        session.commit()
        log_info(f"Dealer added successfully: {new_dealer.dealer_id}")

        success_message = (f"Dealer added successfully.\n\n"
                           f"Dealer ID: {new_dealer.dealer_id}\n\n"
                           f"Dealer Code: {payload['dealer_code']}\n\n"
                           f"Opportunity Owner: {payload['opportunity_owner']}")
        notify_success("Add Dealer Successful", success_message)

        return jsonify({
            "message": "Dealer added successfully",
            "dealer_id": new_dealer.dealer_id,
            "dealer_code": payload['dealer_code'],
            "opportunity_owner": payload['opportunity_owner']
        }), 201

    except SQLAlchemyError as e:
        session.rollback()
        error_message = f"Error inserting dealer: {str(e)}"
        log_error(error_message)
        notify_failure("Add Dealer Failed", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        log_error(error_message)
        notify_failure("Add Dealer Failed", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500
    finally:
        log_info("End of add_dealer function")


@app.route('/get-all-dealers', methods=['GET'])
def get_all_dealers():
    log_info("Received request to get all dealers")
    try:
        # Fetch all dealers from the database
        dealers = session.query(Dealer).all()

        if not dealers:
            log_info("No dealers found.")
            return jsonify({"message": "No dealers found"}), 404

        # Serialize dealer data
        dealers_data = [dealer.dealer_serialize_to_dict() for dealer in dealers]

        # Prepare formatted success message for email
        success_message = f"Dealers retrieved successfully. Count: {len(dealers)}"
        log_info(success_message)
        notify_success("Get All Dealers Successful", success_message)

        # Return the response with dealer data
        return jsonify({
            "message": "Dealers retrieved successfully.",
            "Total count": len(dealers),
            "dealers": dealers_data
        }), 200

    except SQLAlchemyError as e:
        session.rollback()  # Rollback transaction in case of error
        error_message = f"Error retrieving dealers: {str(e)}"
        log_error(error_message)
        notify_failure("Get All Dealers Failed", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        log_error(error_message)
        notify_failure("Get All Dealers Failed", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500
    finally:
        log_info("End of get_all_dealers function")


@app.route('/get-particular-dealers', methods=['GET'])
def get_particular_dealers():
    """
    Fetches particular dealers based on dealer id, dealer code, opportunity owner
    :return: JSON response with email notifications
    """
    log_info("Received request to get particular dealers by parameters")
    try:
        dealer_id = request.args.get('dealer_id')
        dealer_code = request.args.get('dealer_code')
        opportunity_owner = request.args.get('opportunity_owner')

        log_debug(
            f"Search parameters - dealer_id: {dealer_id}, dealer_code: {dealer_code}, "
            f"opportunity_owner: {opportunity_owner}")

        if not dealer_id and not dealer_code and not opportunity_owner:
            error_message = "At least one of 'dealer_id', 'dealer_code', or 'opportunity_owner' must be provided."
            log_error(error_message)
            notify_failure("Get Dealers Failed", error_message)
            return jsonify({"error": error_message}), 400

        query = session.query(Dealer)

        if dealer_id:
            query = query.filter_by(dealer_id=dealer_id)
        if dealer_code:
            query = query.filter_by(dealer_code=dealer_code)
        if opportunity_owner:
            query = query.filter_by(opportunity_owner=opportunity_owner)

        dealers = query.all()

        if not dealers:
            error_message = "No dealers found with the provided parameters."
            log_info(error_message)
            notify_success("Get Dealers", error_message)
            return jsonify({"message": error_message}), 404

        dealers_data = [dealer.dealer_serialize_to_dict() for dealer in dealers]

        formatted_dealers_info = "\n".join([
            f"Dealer ID: {dealer['dealer_id']}\n"
            f"Dealer Code: {dealer['dealer_code']}\n"
            f"Opportunity Owner: {dealer['opportunity_owner']}\n"
            "-------------------------"
            for dealer in dealers_data
        ])
        success_message = (f"Retrieved {len(dealers)} dealer(s) successfully.\n\n"
                           f"Dealer Details:\n{formatted_dealers_info}")
        log_info(success_message)
        notify_success("Get Dealers Successful", success_message)

        # Return the response with dealer data
        return jsonify({
            "message": f"Retrieved Total {len(dealers)} dealer(s) successfully.",
            "dealers": dealers_data
        }), 200

    except SQLAlchemyError as e:
        session.rollback()
        error_message = f"Error retrieving dealers: {str(e)}"
        log_error(error_message)
        notify_failure("Get Dealers Failed", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        log_error(error_message)
        notify_failure("Get Dealers Failed", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500
    finally:
        log_info("End of get_dealers function")


@app.route('/update-dealer', methods=['PUT'])
def update_dealer():
    """
    Updates dealer based on dealer id
    :return: JSON response with email notifications
    """
    log_info("Received request to update a dealer")
    try:
        data = request.json
        dealer_id = data.get('dealer_id')
        dealer_code = data.get('dealer_code')
        opportunity_owner = data.get('opportunity_owner')

        log_debug(
            f"Data received for update: dealer_id={dealer_id}, dealer_code={dealer_code}, "
            f"opportunity_owner={opportunity_owner}")

        if not dealer_id:
            error_message = "Dealer ID must be provided to update a dealer."
            log_error(error_message)
            notify_failure("Update Dealer Failed", error_message)
            return jsonify({"error": error_message}), 400

        dealer = session.query(Dealer).filter_by(dealer_id=dealer_id).first()

        if not dealer:
            error_message = f"No dealer found with dealer_id: {dealer_id}"
            log_error(error_message)
            notify_failure("Update Dealer Failed", error_message)
            return jsonify({"error": "Dealer not found"}), 404

        if dealer_code:
            dealer.dealer_code = dealer_code
        if opportunity_owner:
            dealer.opportunity_owner = opportunity_owner

        session.commit()

        updated_dealer_data = dealer.dealer_serialize_to_dict()

        success_message = (f"Dealer updated successfully.\n\n"
                           f"Updated Dealer ID: {updated_dealer_data['dealer_id']}\n"
                           f"Updated Dealer Code: {updated_dealer_data['dealer_code']}\n"
                           f"Updated Opportunity Owner: {updated_dealer_data['opportunity_owner']}")
        log_info(success_message)
        notify_success("Dealer Updated Successfully", success_message)

        return jsonify({
            "message": "Dealer updated successfully.",
            "dealer": updated_dealer_data
        }), 200

    except SQLAlchemyError as e:
        session.rollback()
        error_message = f"Error updating dealer: {str(e)}"
        log_error(error_message)
        notify_failure("Update Dealer Failed", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        log_error(error_message)
        notify_failure("Update Dealer Failed", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500
    finally:
        log_info("End of update_dealer function")


@app.route('/delete-single-dealer', methods=['DELETE'])
def delete_single_dealer():
    """
    Deletes the single dealer based on dealer id/ dealer code/ opportunity owner
    :return: JSON response with email notifications
    """
    log_info("Received request to delete a dealer")
    try:
        dealer_id = request.args.get('dealer_id')
        dealer_code = request.args.get('dealer_code')
        opportunity_owner = request.args.get('opportunity_owner')
        log_debug(f"Dealer ID: {dealer_id}, Dealer Code: {dealer_code}, Opportunity Owner: {opportunity_owner}")

        if not dealer_id and not dealer_code and not opportunity_owner:
            error_message = "At least one of 'dealer_id', 'dealer_code', or 'opportunity_owner' must be provided."
            log_error(error_message)
            notify_failure("Delete Dealer Failed", error_message)
            return jsonify({"error": error_message}), 400

        query = session.query(Dealer)
        if dealer_id:
            query = query.filter_by(dealer_id=dealer_id)
        if dealer_code:
            query = query.filter_by(dealer_code=dealer_code)
        if opportunity_owner:
            query = query.filter_by(opportunity_owner=opportunity_owner)

        dealers_to_delete = query.first()

        if not dealers_to_delete:
            error_message = "Dealer not found with the given criteria."
            log_error(error_message)
            notify_failure("Delete Dealer Failed", error_message)
            return jsonify({"error": error_message}), 404

        for dealer in dealers_to_delete:
            session.delete(dealer)

        session.commit()
        success_message = f"Deleted {len(dealers_to_delete)} dealer(s) successfully."
        log_info(success_message)
        notify_success("Delete Dealer Successful", success_message)

        return jsonify({"message": success_message}), 200

    except SQLAlchemyError as e:
        session.rollback()
        error_message = f"Error deleting dealer: {str(e)}"
        log_error(error_message)
        notify_failure("Delete Dealer Failed", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        log_error(error_message)
        notify_failure("Delete Dealer Failed", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500
    finally:
        log_info("End of delete_dealer function")


@app.route('/delete-all-dealers', methods=['DELETE'])
def delete_all_dealers():
    """
    Deletes all dealers based on dealer id/ dealer code/ opportunity owner
    :return: JSON response with email notifications
    """
    log_info("Received request to delete dealers")
    try:
        dealer_id = request.args.get('dealer_id')
        dealer_code = request.args.get('dealer_code')
        opportunity_owner = request.args.get('opportunity_owner')

        if not dealer_id and not dealer_code and not opportunity_owner:
            error_message = "At least one of 'dealer_id', 'dealer_code', or 'opportunity_owner' must be provided."
            log_error(error_message)
            return jsonify({"error": error_message}), 400

        query = session.query(Dealer)

        if dealer_id:
            query = query.filter(Dealer.dealer_id == dealer_id)
        if dealer_code:
            query = query.filter(Dealer.dealer_code == dealer_code)
        if opportunity_owner:
            query = query.filter(Dealer.opportunity_owner == opportunity_owner)

        dealers_to_delete = query.all()

        if not dealers_to_delete:
            error_message = "No dealers found with the given criteria."
            log_error(error_message)
            return jsonify({"error": error_message}), 404

        for dealer in dealers_to_delete:
            session.delete(dealer)
        session.commit()

        success_message = f"Deleted {len(dealers_to_delete)} dealer(s) successfully."
        log_info(success_message)
        notify_success("Delete Dealers Successful", success_message)

        return jsonify({"message": success_message}), 200

    except SQLAlchemyError as e:
        session.rollback()
        error_message = f"Error deleting dealers: {str(e)}"
        log_error(error_message)
        notify_failure("Delete Dealers Failed", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500

    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        log_error(error_message)
        notify_failure("Delete Dealers Failed", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500

    finally:
        log_info("End of delete_dealers function")


# ----------------------------------------------- OPPORTUNITY TABLE ----------------------------------------------------


@app.route('/new-customer', methods=["POST"])
def create_new_customer():
    """
    Creates a new customer in the opportunity table.
    :return: JSON response with email notifications and detailed customer information.
    """
    log_info("Received request to create new customer")
    try:
        payload = request.get_json()
        log_debug(f"Request payload: {payload}")

        opportunity_id = str(uuid.uuid1())
        log_info(f"Generated opportunity_id: {opportunity_id}")

        created_date = datetime.now(pytz.timezone('Asia/Kolkata'))
        payload.update({'created_date': created_date, 'opportunity_id': opportunity_id})
        log_info(f"Payload after adding created_date and opportunity_id: {payload}")

        account_name = payload.get("account_name")
        account = session.query(Account).filter_by(account_name=account_name).first()

        if not account:
            # Account does not exist, add new account
            new_account_id = str(uuid.uuid4())  # Example of auto-generating a UUID for account_id
            new_account = Account(
                account_id=new_account_id,
                account_name=account_name
            )
            session.add(new_account)
            session.commit()
            log_info(f"New account added: {account_name}")

            # Notify user about the new account addition
            account_creation_message = (f"New account added to the database:\n"
                                        f"Account Name: {account_name}")
            notify_success("New Account Added", account_creation_message)
        else:
            log_info(f"Account found: {account_name}")

        dealer_id = payload.get("dealer_id")
        dealer_code = payload.get("dealer_code")
        opportunity_owner = payload.get("opportunity_owner")

        dealer = session.query(Dealer).filter_by(
            dealer_id=dealer_id,
            dealer_code=dealer_code,
            opportunity_owner=opportunity_owner
        ).first()

        if not dealer:
            log_info(
                f"Dealer with ID {dealer_id} not found, but no need to create new dealer. Proceeding with existing dealers.")

        else:
            log_info(f"Dealer found: {dealer_id}, {dealer_code}, {opportunity_owner}")

        close_date_str = payload.get("close_date")

        if close_date_str:
            try:
                close_date = datetime.strptime(close_date_str, "%Y-%m-%d %H:%M:%S")
                log_info(f"Parsed close_date: {close_date}")
            except ValueError as e:
                error_message = f"Invalid date format for close_date: {str(e)}"
                log_error(error_message)
                detailed_error_message = f"Failed to create customer due to invalid date format.\nError: {str(e)}"
                notify_failure("Customer Creation Failed", detailed_error_message)
                return jsonify({"error": error_message}), 400
        else:
            close_date = None
            log_info("No close_date provided, set to None")

        probability = payload.get("probability")

        if probability is not None:
            try:
                stage = get_opportunity_stage(probability)
                log_info(f"Determined stage from probability: {stage}")
            except ValueError as e:
                error_message = f"Invalid probability value: {str(e)}"
                log_error(error_message)
                notify_failure("Customer Creation Failed", error_message)
                return jsonify({"error": error_message}), 400
        else:
            stage = payload.get("stage", "Unknown")
            log_info(f"No probability provided, defaulting stage to: {stage}")

        amount = payload.get("amount")

        if amount:
            currency_conversions = get_currency_conversion(amount)
            log_info(f"Currency conversions for amount {amount}: {currency_conversions}")
        else:
            currency_conversions = {}
            log_info("No amount provided, currency conversions set to empty")

        new_opportunity = Opportunity(
            opportunity_id=opportunity_id,
            opportunity_name=payload.get("opportunity_name"),
            account_name=account_name,
            close_date=close_date,
            amount=amount,
            description=payload.get("description"),
            dealer_id=dealer_id,
            dealer_code=dealer_code,
            stage=stage,
            probability=probability,
            next_step=payload.get("next_step"),
            created_date=created_date,
            usd=currency_conversions.get("USD"),
            aus=currency_conversions.get("AUD"),
            cad=currency_conversions.get("CAD"),
            jpy=currency_conversions.get("JPY"),
            eur=currency_conversions.get("EUR"),
            gbp=currency_conversions.get("GBP"),
            cny=currency_conversions.get("CNY"),
            amount_in_words=str(amount),
            vehicle_model=payload.get("vehicle_model"),
            vehicle_year=payload.get("vehicle_year"),
            vehicle_color=payload.get("vehicle_color"),
            vehicle_model_id=payload.get("vehicle_model_id")
        )
        log_info(f"New Opportunity object created: {new_opportunity}")

        session.add(new_opportunity)
        session.commit()
        log_info(f"Opportunity created successfully: {opportunity_id}")

        customer_details = new_opportunity.serialize_to_dict()
        log_info(f"Serialized customer details: {customer_details}")

        formatted_currency_conversions = "\n".join(f"{key}: {value}" for key, value in currency_conversions.items())
        success_message = (f"Customer created successfully.\n\n\n"
                           f"Opportunity ID: {opportunity_id}\n\n"
                           f"Opportunity Name: {payload.get('opportunity_name')}\n\n"
                           f"Account Name: {account_name}\n\n"
                           f"Close Date: {close_date.strftime('%Y-%m-%d %H:%M:%S') if close_date else None}\n\n"
                           f"Amount: {payload.get('amount')}\n\n"
                           f"Stage: {stage}\n\n"
                           f"Probability: {payload.get('probability')}\n\n"
                           f"Currency Conversions:\n{formatted_currency_conversions}\n\n"
                           f"Vehicle Model: {payload.get('vehicle_model')}\n\n"
                           f"Vehicle Year: {payload.get('vehicle_year')}\n\n"
                           f"Vehicle Color: {payload.get('vehicle_color')}\n\n"
                           f"Vehicle model id: {payload.get('vehicle_model_id')}\n\n"
                           f"Created Date: {created_date.strftime('%Y-%m-%d %H:%M:%S')}")

        notify_success("Customer Creation Successful", success_message)

        return jsonify({
            "message": "Created successfully",
            "customer_details": customer_details
        }), 201

    except SQLAlchemyError as e:
        session.rollback()  # Rollback the session on error
        error_message = f"Error in creating customer: {str(e)}"
        log_error(error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500

    except Exception as e:
        session.rollback()
        error_message = f"Error in creating customer: {str(e)}"
        log_error(error_message)
        detailed_error_message = f"Failed to create customer due to an internal server error.\nDetails: {str(e)}"
        notify_failure("Customer Creation Failed", detailed_error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500

    finally:
        session.close()
        log_info("End of create_new_customer function")


@app.route('/get-opportunities', methods=['GET'])
def get_opportunities():
    """
    Fetches opportunities from the opportunity table based on query parameters.
    :return: JSON response with filtered opportunity details and total count.
    """
    log_info("Received request to get opportunities with query parameters")

    try:
        # Retrieve and process query parameters
        opportunity_id = request.args.get('opportunity_id')
        opportunity_name = request.args.get('opportunity_name', '').strip()
        account_name = request.args.get('account_name', '').strip()
        stage = request.args.get('stage', '').strip()
        probability_min = request.args.get('probability_min', type=int)
        probability_max = request.args.get('probability_max', type=int)
        created_date_start = request.args.get('created_date_start')
        close_date_end = request.args.get('close_date_end')
        vehicle_model = request.args.get('vehicle_model', '').strip()
        vehicle_year_min = request.args.get('vehicle_year_min', type=int)
        vehicle_year_max = request.args.get('vehicle_year_max', type=int)
        vehicle_color = request.args.get('vehicle_color', '').strip()
        amount_min = request.args.get('amount_min', type=float)
        amount_max = request.args.get('amount_max', type=float)
        vehicle_model_id = request.args.get('vehicle_model_id', '').strip()
        case_sensitive = request.args.get('case_sensitive', default='false').lower() == 'true'

        log_info(f"Query parameters retrieved: opportunity_id={opportunity_id}, opportunity_name={opportunity_name}, "
                 f"account_name={account_name}, stage={stage}, probability_min={probability_min}, "
                 f"probability_max={probability_max}, created_date_start={created_date_start}, "
                 f"close_date_end={close_date_end}, vehicle_model={vehicle_model}, "
                 f"vehicle_year_min={vehicle_year_min}, vehicle_year_max={vehicle_year_max}, "
                 f"vehicle_color={vehicle_color}, amount_min={amount_min}, amount_max={amount_max}, "
                 f"vehicle_model_id={vehicle_model_id}, case_sensitive={case_sensitive}")

        # Convert date strings to datetime objects
        if created_date_start:
            created_date_start = datetime.fromisoformat(created_date_start.replace('Z', '+00:00'))
            log_info(f"Parsed created_date_start: {created_date_start}")

        if close_date_end:
            close_date_end = datetime.fromisoformat(close_date_end.replace('Z', '+00:00'))
            log_info(f"Parsed close_date_end: {close_date_end}")

        if probability_min is not None and not validate_probability(probability_min):
            raise ValueError(f"Invalid minimum probability: {probability_min}. Must be between 0 and 100")

        if probability_max is not None and not validate_probability(probability_max):
            raise ValueError(f"Invalid maximum probability: {probability_max}. Must be between 0 and 100")

        if probability_min is not None and probability_max is not None and probability_min > probability_max:
            raise ValueError("Minimum probability cannot be greater than maximum probability")

        if stage:
            stage = validate_stage(stage)
            log_info(f"Validated stage: {stage}")

        # Validate vehicle_model_id
        if vehicle_model_id and len(vehicle_model_id) > 255:
            raise ValueError("Vehicle model ID is too long. Maximum length is 255 characters.")

        query = session.query(Opportunity)
        log_info("Constructed initial query")

        # Apply filters based on query parameters
        if opportunity_id:
            query = query.filter(Opportunity.opportunity_id == opportunity_id)
            log_info(f"Applied filter: opportunity_id = {opportunity_id}")

        if opportunity_name:
            if len(opportunity_name) > 255:
                raise ValueError("Opportunity name is too long. Maximum length is 255 characters.")
            if case_sensitive:
                query = query.filter(Opportunity.opportunity_name == opportunity_name)
            else:
                query = query.filter(Opportunity.opportunity_name.ilike(f'%{opportunity_name}%'))
            log_info(
                f"Applied filter: opportunity_name {'case-sensitive' if case_sensitive else 'case-insensitive'} contains '{opportunity_name}'")

        if account_name:
            if len(account_name) > 255:
                raise ValueError("Account name is too long. Maximum length is 255 characters.")
            if case_sensitive:
                query = query.filter(Opportunity.account_name == account_name)
            else:
                query = query.filter(Opportunity.account_name.ilike(f'%{account_name}%'))
            log_info(
                f"Applied filter: account_name {'case-sensitive' if case_sensitive else 'case-insensitive'} contains '{account_name}'")

        if stage:
            if case_sensitive:
                query = query.filter(Opportunity.stage == stage)
            else:
                query = query.filter(Opportunity.stage.ilike(f'%{stage}%'))
            log_info(f"Applied filter: stage {'case-sensitive' if case_sensitive else 'case-insensitive'} = {stage}")

        if probability_min is not None:
            query = query.filter(Opportunity.probability >= probability_min)
            log_info(f"Applied filter: probability >= {probability_min}")

        if probability_max is not None:
            query = query.filter(Opportunity.probability <= probability_max)
            log_info(f"Applied filter: probability <= {probability_max}")

        if created_date_start:
            query = query.filter(Opportunity.created_date >= created_date_start)
            log_info(f"Applied filter: created_date >= {created_date_start}")

        if close_date_end:
            query = query.filter(Opportunity.close_date <= close_date_end)
            log_info(f"Applied filter: close_date <= {close_date_end}")

        if vehicle_model:
            if len(vehicle_model) > 255:
                raise ValueError("Vehicle model is too long. Maximum length is 255 characters.")
            if case_sensitive:
                query = query.filter(Opportunity.vehicle_model == vehicle_model)
            else:
                query = query.filter(Opportunity.vehicle_model.ilike(f'%{vehicle_model}%'))
            log_info(
                f"Applied filter: vehicle_model {'case-sensitive' if case_sensitive else 'case-insensitive'} contains '{vehicle_model}'")

        if vehicle_year_min is not None:
            query = query.filter(Opportunity.vehicle_year >= vehicle_year_min)
            log_info(f"Applied filter: vehicle_year >= {vehicle_year_min}")

        if vehicle_year_max is not None:
            query = query.filter(Opportunity.vehicle_year <= vehicle_year_max)
            log_info(f"Applied filter: vehicle_year <= {vehicle_year_max}")

        if vehicle_color:
            if len(vehicle_color) > 255:
                raise ValueError("Vehicle color is too long. Maximum length is 255 characters.")
            if case_sensitive:
                query = query.filter(Opportunity.vehicle_color == vehicle_color)
            else:
                query = query.filter(Opportunity.vehicle_color.ilike(f'%{vehicle_color}%'))
            log_info(
                f"Applied filter: vehicle_color {'case-sensitive' if case_sensitive else 'case-insensitive'} contains '{vehicle_color}'")

        if amount_min is not None:
            query = query.filter(Opportunity.amount >= amount_min)
            log_info(f"Applied filter: amount >= {amount_min}")

        if amount_max is not None:
            query = query.filter(Opportunity.amount <= amount_max)
            log_info(f"Applied filter: amount <= {amount_max}")

        if vehicle_model_id:
            query = query.filter(Opportunity.vehicle_model_id == vehicle_model_id)
            log_info(f"Applied filter: vehicle_model_id = {vehicle_model_id}")

        opportunities = query.all()
        total_count = len(opportunities)
        log_info(f"Fetched {total_count} opportunities based on query parameters")

        opportunities_list = [opportunity.serialize_to_dict() for opportunity in opportunities]
        log_info("Serialized opportunities to dictionary format")

        # Notify with detailed opportunity information
        notify_opportunity_details("Get Opportunities Successful", opportunities_list, total_count)

        return jsonify({"Opportunities": opportunities_list, "Total count of opportunities": total_count}), 200

    except ValueError as ve:
        error_message = f"Validation error: {str(ve)}"
        log_error(error_message)
        notify_failure("Get Opportunities Validation Failed", error_message)
        return jsonify({"error": "Bad Request", "details": error_message}), 400

    except SQLAlchemyError as sae:
        error_message = f"Database error: {str(sae)}"
        log_error(error_message)
        notify_failure("Get Opportunities Database Error", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500

    except Exception as e:
        error_message = f"Error in fetching opportunities: {str(e)}"
        log_error(error_message)
        notify_failure("Get Opportunities Failed", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500

    finally:
        log_info("End of get_opportunities function")


@app.route('/update-opportunity', methods=['PUT'])
def update_opportunity():
    """
    Update an existing Opportunity record.
    :return: JSON response indicating success or failure.
    """
    log_info("Received request to update opportunity")

    try:
        data = request.get_json()
        log_info(f"Request data: {data}")

        # Retrieve and log the input data
        opportunity_id = data.get('opportunity_id')
        opportunity_name = data.get('opportunity_name')
        account_name = data.get('account_name')
        close_date = data.get('close_date')
        amount = data.get('amount')
        description = data.get('description')
        dealer_id = data.get('dealer_id')
        dealer_code = data.get('dealer_code')
        stage = data.get('stage')
        probability = data.get('probability')
        next_step = data.get('next_step')
        amount_in_words = data.get('amount_in_words')
        currency_conversions = data.get('currency_conversions', {})
        vehicle_model = data.get('vehicle_model')
        vehicle_year = data.get('vehicle_year')
        vehicle_color = data.get('vehicle_color')
        vehicle_model_id = data.get('vehicle_model_id')
        log_info(f"Extracted fields: opportunity_id={opportunity_id}, opportunity_name={opportunity_name}, "
                 f"account_name={account_name}, close_date={close_date}, amount={amount}, description={description}, "
                 f"dealer_id={dealer_id}, dealer_code={dealer_code}, stage={stage}, probability={probability}, "
                 f"next_step={next_step}, amount_in_words={amount_in_words}, currency_conversions={currency_conversions}, "
                 f"vehicle_model={vehicle_model}, vehicle_year={vehicle_year}, vehicle_color={vehicle_color},"
                 f"vehicle_model_id={vehicle_model_id}")
        if not opportunity_id:
            raise ValueError("Opportunity ID is required.")
        log_info("Opportunity ID provided.")

        if opportunity_name and len(opportunity_name) > 255:
            raise ValueError("Opportunity name is too long. Maximum length is 255 characters.")

        if account_name and len(account_name) > 255:
            raise ValueError("Account name is too long. Maximum length is 255 characters.")
        log_info("Validated length of opportunity_name and account_name.")

        if close_date:
            close_date = parse_date(close_date)
            log_info(f"Parsed close_date: {close_date}")

        if amount is not None and not validate_positive_number(amount):
            raise ValueError("Amount must be a positive number.")

        if probability is not None and not validate_probability(probability):
            raise ValueError("Probability must be between 0 and 100.")

        if stage:
            stage = validate_stage(stage)
            log_info(f"Validated stage: {stage}")

        valid_currencies = ['usd', 'aus', 'cad', 'jpy', 'eur', 'gbp', 'cny']

        for currency in valid_currencies:
            if currency in currency_conversions:
                if not validate_positive_number(currency_conversions[currency]):
                    raise ValueError(f"Invalid value for currency conversion {currency}. Must be a positive number.")
        log_info("Validated currency conversions.")

        if vehicle_model_id and not isinstance(vehicle_model_id, int):
            raise ValueError("Vehicle model ID must be an integer.")

        opportunity = session.query(Opportunity).filter_by(opportunity_id=opportunity_id).first()

        if not opportunity:
            raise ValueError("Opportunity not found.")
        log_info(f"Found opportunity with ID {opportunity_id}.")

        updated_fields = {}

        if opportunity_name:
            opportunity.opportunity_name = opportunity_name
            updated_fields['opportunity_name'] = opportunity_name

        if account_name:
            opportunity.account_name = account_name
            updated_fields['account_name'] = account_name

        if close_date:
            opportunity.close_date = close_date
            updated_fields['close_date'] = close_date

        if amount is not None:
            opportunity.amount = amount
            conversions = get_currency_conversion(amount)
            opportunity.usd = conversions.get('USD')
            opportunity.aus = conversions.get('AUD')
            opportunity.cad = conversions.get('CAD')
            opportunity.jpy = conversions.get('JPY')
            opportunity.eur = conversions.get('EUR')
            opportunity.gbp = conversions.get('GBP')
            opportunity.cny = conversions.get('CNY')
            updated_fields['amount'] = amount
            updated_fields['currency_conversions'] = conversions

        if description:
            opportunity.description = description
            updated_fields['description'] = description

        if dealer_id:
            opportunity.dealer_id = dealer_id
            updated_fields['dealer_id'] = dealer_id

        if dealer_code:
            opportunity.dealer_code = dealer_code
            updated_fields['dealer_code'] = dealer_code

        if stage:
            opportunity.stage = stage
            updated_fields['stage'] = stage

        if probability is not None:
            opportunity.probability = probability
            updated_fields['probability'] = probability

        if next_step:
            opportunity.next_step = next_step
            updated_fields['next_step'] = next_step

        if amount_in_words:
            opportunity.amount_in_words = amount_in_words
            updated_fields['amount_in_words'] = amount_in_words

        if vehicle_model:
            opportunity.vehicle_model = vehicle_model
            updated_fields['vehicle_model'] = vehicle_model

        if vehicle_year:
            if not isinstance(vehicle_year, int) or vehicle_year < 1900 or vehicle_year > datetime.now().year:
                raise ValueError("Vehicle year must be a valid year.")
            opportunity.vehicle_year = vehicle_year
            updated_fields['vehicle_year'] = vehicle_year

        if vehicle_color:
            opportunity.vehicle_color = vehicle_color
            updated_fields['vehicle_color'] = vehicle_color

        if vehicle_model_id:
            opportunity.vehicle_model_id = vehicle_model_id
            updated_fields['vehicle_model_id'] = vehicle_model_id

        if currency_conversions:
            opportunity.usd = currency_conversions.get('usd')
            opportunity.aus = currency_conversions.get('aus')
            opportunity.cad = currency_conversions.get('cad')
            opportunity.jpy = currency_conversions.get('jpy')
            opportunity.eur = currency_conversions.get('eur')
            opportunity.gbp = currency_conversions.get('gbp')
            opportunity.cny = currency_conversions.get('cny')
            updated_fields['currency_conversions'] = currency_conversions

        log_info(f"Updating fields: {updated_fields}")
        session.commit()
        log_info(f"Opportunity with ID {opportunity_id} updated successfully.")

        notify_opportunity_update_success(
            "Update Opportunity Successful",
            {"opportunity_id": opportunity_id, "updated_fields": updated_fields}
        )

        return jsonify({
            "message": "Opportunity updated successfully.",
            "opportunity_id": opportunity_id,
            "updated_fields": updated_fields
        }), 200

    except ValueError as ve:
        error_message = f"Validation error: {str(ve)}"
        log_error(error_message)
        notify_failure("Update Opportunity Validation Failed", error_message)
        return jsonify({"error": "Bad Request", "details": error_message}), 400

    except SQLAlchemyError as sae:
        error_message = f"Database error: {str(sae)}"
        log_error(error_message)
        notify_failure("Update Opportunity Database Error", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500

    except Exception as e:
        error_message = f"Error updating opportunity: {str(e)}"
        log_error(error_message)
        notify_failure("Update Opportunity Failed", error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500

    finally:
        log_info("End of update_opportunity function")


@app.route('/delete-customer', methods=["DELETE"])
def delete_customer():
    """
    Deletes a customer from the opportunity table based on query parameters.
    :return: JSON response with email notifications and result of deletion.
    """
    log_info("Received request to delete customer")
    try:
        opportunity_id = request.args.get("opportunity_id")
        account_name = request.args.get("account_name")
        dealer_id = request.args.get("dealer_id")
        dealer_code = request.args.get("dealer_code")
        opportunity_name = request.args.get("opportunity_name")
        stage = request.args.get("stage")
        probability = request.args.get("probability", type=int)
        close_date = request.args.get("close_date")

        if not any([opportunity_id, account_name, dealer_id, dealer_code, opportunity_name, stage, probability,
                    close_date]):
            error_message = ("At least one query parameter (opportunity_id, account_name, dealer_id, dealer_code, "
                             "opportunity_name, stage, probability, or close_date) is required for deletion.")
            log_error(error_message)
            detailed_error_message = "Failed to delete customer due to missing query parameters."
            notify_failure("Customer Deletion Failed", detailed_error_message)
            return jsonify({"error": error_message}), 400

        if close_date:
            try:
                close_date = datetime.strptime(close_date, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                error_message = "Invalid close_date format. Use 'YYYY-MM-DD HH:MM:SS'."
                log_error(error_message)
                detailed_error_message = "Failed to delete customer due to invalid close_date format."
                notify_failure("Customer Deletion Failed", detailed_error_message)
                return jsonify({"error": error_message}), 400

        query = session.query(Opportunity)

        if opportunity_id:
            query = query.filter(Opportunity.opportunity_id == opportunity_id)

        if account_name:
            query = query.filter(Opportunity.account_name == account_name)

        if dealer_id:
            query = query.filter(Opportunity.dealer_id == dealer_id)

        if dealer_code:
            query = query.filter(Opportunity.dealer_code == dealer_code)

        if opportunity_name:
            query = query.filter(Opportunity.opportunity_name == opportunity_name)

        if stage:
            query = query.filter(Opportunity.stage == stage)

        if probability is not None:
            query = query.filter(Opportunity.probability == probability)

        if close_date:
            query = query.filter(Opportunity.close_date == close_date)

        customers_to_delete = query.all()

        if not customers_to_delete:
            error_message = "Customer(s) not found based on provided query parameters."
            log_error(error_message)
            detailed_error_message = "Failed to delete customer(s). No matching customer(s) found."
            notify_failure("Customer Deletion Failed", detailed_error_message)
            return jsonify({"error": error_message}), 404

        for customer in customers_to_delete:
            session.delete(customer)

        session.commit()

        success_message = (
                f"Customer(s) deleted successfully.\n\n\n"
                f"Deleted Customers:\n" + "\n".join([f"Opportunity ID: {customer.opportunity_id}\n"
                                                     f"Opportunity Name: {customer.opportunity_name}\n"
                                                     f"Account Name: {customer.account_name}\n"
                                                     f"Dealer ID: {customer.dealer_id}\n"
                                                     f"Dealer Code: {customer.dealer_code}\n"
                                                     f"Amount: {customer.amount}\n"
                                                     f"Close Date: {customer.close_date.strftime('%Y-%m-%d %H:%M:%S') if customer.close_date else None}\n"
                                                     f"Created Date: {customer.created_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                                                     for customer in customers_to_delete])

        )
        notify_success("Customer Deletion Successful", success_message)

        return jsonify({"message": "Deleted successfully"}), 200

    except Exception as e:
        error_message = f"Error in deleting customer: {str(e)}"
        log_error(error_message)
        detailed_error_message = f"Failed to delete customer due to an internal server error.\nDetails: {str(e)}"
        notify_failure("Customer Deletion Failed", detailed_error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500

    finally:
        log_info("End of delete_customer function")


# ----------------------------------------------- VEHICLE DETAILS TABLE ------------------------------------------------


@app.route('/vehicle-details', methods=['POST'])
def create_new_vehicle_details():
    data = request.get_json()

    # Validate incoming data
    required_fields = ['vehicle_model', 'vehicle_year']
    for field in required_fields:
        if field not in data:
            log_error(f'Missing required field: {field}')
            return jsonify({'error': f'Missing required field: {field}'}), 400

    if not isinstance(data.get('vehicle_year'), int) or data.get('vehicle_year') <= 0:
        log_error('Invalid vehicle_year: must be a positive integer')
        return jsonify({'error': 'Invalid vehicle_year: must be a positive integer'}), 400

    # Additional validations for new fields
    if 'color' in data and not isinstance(data['color'], str):
        log_error('Invalid color: must be a string')
        return jsonify({'error': 'Invalid color: must be a string'}), 400

    if 'sunroof_available' in data and not isinstance(data['sunroof_available'], bool):
        log_error('Invalid sunroof_available: must be a boolean')
        return jsonify({'error': 'Invalid sunroof_available: must be a boolean'}), 400

    log_debug(f'Received request to create vehicle details: {data}')

    try:
        new_vehicle = VehicleDetails(
            vehicle_model=data['vehicle_model'],
            vehicle_year=data['vehicle_year'],
            engine_type=data.get('engine_type'),
            transmission=data.get('transmission'),
            fuel_type=data.get('fuel_type'),
            body_type=data.get('body_type'),
            warranty_period_years=data.get('warranty_period_years'),
            color=data.get('color'),
            model_variant=data.get('model_variant'),
            tyre_company=data.get('tyre_company'),
            tyre_size=data.get('tyre_size'),
            start_type=data.get('start_type'),
            sunroof_available=data.get('sunroof_available'),
            gear_type=data.get('gear_type'),
            vehicle_type=data.get('vehicle_type')
        )

        session.add(new_vehicle)
        session.commit()

        vehicle_details = new_vehicle.serialize_to_dict()
        formatted_details = format_vehicle_details(vehicle_details)

        log_info(f'Created new vehicle details: {formatted_details}')

        # Notify success with formatted vehicle details
        notify_success(
            subject='New Vehicle Details Created',
            details=f'New vehicle details created:\n{formatted_details}'
        )

        return jsonify({'message': 'Vehicle details created successfully', 'vehicle': vehicle_details}), 201

    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e)
        log_error(f'Failed to create vehicle details: {error_message}')

        # Notify failure with error message
        notify_failure(
            subject='Error Creating Vehicle Details',
            details=f'Failed to create vehicle details:\n{error_message}'
        )

        return jsonify({'error': error_message}), 400


@app.route('/search-vehicles', methods=['GET'])
def search_vehicles():
    """
    Searches for vehicles based on various query parameters.

    Query Parameters:
    - vehicle_model_id (str): ID of the vehicle.
    - vehicle_model (str): Filter by vehicle model.
    - vehicle_year (int): Filter by vehicle year.
    - engine_type (str): Filter by engine type.
    - transmission (str): Filter by transmission type.
    - fuel_type (str): Filter by fuel type.
    - body_type (str): Filter by body type.
    - warranty_period_years (int): Filter by warranty period in years.
    - color (str): Filter by vehicle color.
    - model_variant (str): Filter by model variant (e.g., Top, Mid, Base).
    - tyre_company (str): Filter by tyre company.
    - tyre_size (str): Filter by tyre size.
    - start_type (str): Filter by start type (e.g., Key, Push Start).
    - sunroof_available (bool): Filter by sunroof availability.
    - gear_type (str): Filter by gear type (e.g., Gear, Gearless).
    - vehicle_type (str): Filter by vehicle type (e.g., SUV, Sedan, Hatchback).

    :return: JSON response with vehicle details or an error message.
    """
    # Extract query parameters
    vehicle_model_id = request.args.get('vehicle_model_id')
    vehicle_model = request.args.get('vehicle_model')
    vehicle_year = request.args.get('vehicle_year', type=int)
    engine_type = request.args.get('engine_type')
    transmission = request.args.get('transmission')
    fuel_type = request.args.get('fuel_type')
    body_type = request.args.get('body_type')
    warranty_period_years = request.args.get('warranty_period_years', type=int)
    color = request.args.get('color')
    model_variant = request.args.get('model_variant')
    tyre_company = request.args.get('tyre_company')
    tyre_size = request.args.get('tyre_size')
    start_type = request.args.get('start_type')
    sunroof_available = request.args.get('sunroof_available')
    gear_type = request.args.get('gear_type')
    vehicle_type = request.args.get('vehicle_type')

    log_info("Received request with parameters: "
             f"vehicle_model_id={vehicle_model_id}, vehicle_model={vehicle_model}, vehicle_year={vehicle_year}, "
             f"engine_type={engine_type}, transmission={transmission}, fuel_type={fuel_type}, body_type={body_type}, "
             f"warranty_period_years={warranty_period_years}, color={color}, model_variant={model_variant}, "
             f"tyre_company={tyre_company}, tyre_size={tyre_size}, start_type={start_type}, "
             f"sunroof_available={sunroof_available}, gear_type={gear_type}, vehicle_type={vehicle_type}")

    try:
        # Start with the base query
        query = session.query(VehicleDetails)

        # Apply filters based on provided query parameters
        if vehicle_model_id:
            query = query.filter(VehicleDetails.vehicle_model_id == vehicle_model_id)
        if vehicle_model:
            query = query.filter(VehicleDetails.vehicle_model.ilike(f"%{vehicle_model}%"))
        if vehicle_year:
            query = query.filter(VehicleDetails.vehicle_year == vehicle_year)
        if engine_type:
            query = query.filter(VehicleDetails.engine_type.ilike(f"%{engine_type}%"))
        if transmission:
            query = query.filter(VehicleDetails.transmission.ilike(f"%{transmission}%"))
        if fuel_type:
            query = query.filter(VehicleDetails.fuel_type.ilike(f"%{fuel_type}%"))
        if body_type:
            query = query.filter(VehicleDetails.body_type.ilike(f"%{body_type}%"))
        if warranty_period_years:
            query = query.filter(VehicleDetails.warranty_period_years == warranty_period_years)
        if color:
            query = query.filter(VehicleDetails.color.ilike(f"%{color}%"))
        if model_variant:
            query = query.filter(VehicleDetails.model_variant.ilike(f"%{model_variant}%"))
        if tyre_company:
            query = query.filter(VehicleDetails.tyre_company.ilike(f"%{tyre_company}%"))
        if tyre_size:
            query = query.filter(VehicleDetails.tyre_size.ilike(f"%{tyre_size}%"))
        if start_type:
            query = query.filter(VehicleDetails.start_type.ilike(f"%{start_type}%"))
        if sunroof_available is not None:
            sunroof_available = sunroof_available.lower() == 'true'
            query = query.filter(VehicleDetails.sunroof_available == sunroof_available)
        if gear_type:
            query = query.filter(VehicleDetails.gear_type.ilike(f"%{gear_type}%"))
        if vehicle_type:
            query = query.filter(VehicleDetails.vehicle_type.ilike(f"%{vehicle_type}%"))

        # Execute the query
        vehicles = query.all()
        total_count = len(vehicles)

        if total_count == 0:
            log_error("No vehicle details found with the specified criteria.")
            send_email(RECEIVER_EMAIL, "No Vehicle Details Found",
                       "Dear Team,\n\nNo vehicle details were found with the specified criteria.\n\nBest regards,\nYour Team")
            return jsonify({"error": "No vehicle details found"}), 404

        vehicles_info = [vehicle.serialize_to_dict() for vehicle in vehicles]

        # Generate the email body
        email_subject = "Vehicle Details Retrieved"
        email_body = generate_vehicle_details_email_body(
            vehicles_info=vehicles_info,
            total_count=total_count
        )
        send_email(RECEIVER_EMAIL, email_subject, email_body)

        log_info("Vehicle details retrieved successfully.")
        return jsonify({
            "total_count": total_count,
            "vehicles": vehicles_info
        })

    except SQLAlchemyError as e:
        # Log database errors and notify via email
        error_message = f"Database error occurred: {str(e)}"
        log_error(error_message)
        send_email(RECEIVER_EMAIL, "Database Error",
                   f"Dear Team,\n\nAn error occurred while accessing the database.\n\nError Details:\n{error_message}\n\nBest regards,\nYour Team")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

    except Exception as e:
        # Log unexpected errors and notify via email
        error_message = f"Unexpected error occurred: {str(e)}"
        log_error(error_message)
        send_email(RECEIVER_EMAIL, "Unexpected Error",
                   f"Dear Team,\n\nAn unexpected error occurred.\n\nError Details:\n{error_message}\n\nBest regards,\nYour Team")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

    finally:
        log_info("End of search_vehicles function")


@app.route('/update-vehicle-details', methods=['PUT'])
def update_vehicle_details():
    """
    Updates the details of a specific vehicle.

    JSON Body:
    - vehicle_model_id (str): The unique ID of the vehicle to be updated.
    - vehicle_model (str): New vehicle model name.
    - vehicle_year (int): New vehicle year.
    - engine_type (str): New engine type.
    - transmission (str): New transmission type.
    - fuel_type (str): New fuel type.
    - body_type (str): New body type.
    - warranty_period_years (int): New warranty period in years.

    :return: JSON response with updated vehicle details or an error message.
    """
    data = request.get_json()

    vehicle_model_id = data.get('vehicle_model_id')
    if not vehicle_model_id:
        log_error("Vehicle model ID is missing from the request body.")
        return jsonify({"error": "Vehicle model ID is required"}), 400

    log_info(f"Request to update vehicle details received for vehicle_model_id={vehicle_model_id}")

    vehicle = session.query(VehicleDetails).get(vehicle_model_id)
    if vehicle is None:
        log_error(f"Vehicle with ID {vehicle_model_id} not found.")
        send_email(
            RECEIVER_EMAIL,
            "Vehicle Not Found",
            f"Dear Team,\n\nVehicle with ID {vehicle_model_id} could not be found in the database.\nPlease check and verify the details.\n\nBest regards,\nYour Team"
        )
        return jsonify({"error": "Vehicle not found"}), 404

    try:
        # Log the initial state of the vehicle
        log_info(f"Original vehicle data: {vehicle.serialize_to_dict()}")

        # Update fields with new values, or retain current values if not provided
        vehicle.vehicle_model = data.get('vehicle_model', vehicle.vehicle_model)
        vehicle.vehicle_year = data.get('vehicle_year', vehicle.vehicle_year)
        vehicle.engine_type = data.get('engine_type', vehicle.engine_type)
        vehicle.transmission = data.get('transmission', vehicle.transmission)
        vehicle.fuel_type = data.get('fuel_type', vehicle.fuel_type)
        vehicle.body_type = data.get('body_type', vehicle.body_type)
        vehicle.warranty_period_years = data.get('warranty_period_years', vehicle.warranty_period_years)

        # Commit the changes to the database
        session.commit()

        # Serialize updated vehicle data
        updated_vehicle_info = vehicle.serialize_to_dict()

        # Log the updated data
        log_info(f"Vehicle with ID {vehicle_model_id} successfully updated.")
        log_info(f"Updated vehicle data: {updated_vehicle_info}")

        # Generate a detailed email format for the updated vehicle details
        email_subject = "Vehicle Details Updated"
        email_body = generate_detailed_vehicle_email(
            vehicle_info=updated_vehicle_info,
            action="Update",
            admin_email=RECEIVER_EMAIL
        )

        # Send the email with updated details
        send_email(RECEIVER_EMAIL, email_subject, email_body)

        # Return the updated vehicle details in a neat format
        return jsonify({
            "message": "Vehicle details updated successfully.",
            "updated_vehicle_details": updated_vehicle_info,
            "vehicle_model_id": vehicle_model_id
        }), 200

    except SQLAlchemyError as e:
        # Rollback the transaction in case of an error
        session.rollback()

        log_error(f"SQL error occurred while updating vehicle with ID {vehicle_model_id}: {str(e)}")
        send_email(
            RECEIVER_EMAIL,
            "Database Error",
            f"Dear Team,\n\nAn error occurred while updating the vehicle with ID {vehicle_model_id}.\nError Details:\n{str(e)}\n\nBest regards,\nYour Team"
        )
        return jsonify({"error": "Database error", "details": str(e)}), 500

    except Exception as e:
        # Handle unexpected errors
        log_error(f"Unexpected error occurred while updating vehicle with ID {vehicle_model_id}: {str(e)}")
        send_email(
            RECEIVER_EMAIL,
            "Unexpected Error",
            f"Dear Team,\n\nAn unexpected error occurred while updating the vehicle with ID {vehicle_model_id}.\nError Details:\n{str(e)}\n\nBest regards,\nYour Team"
        )
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

    finally:
        log_info(f"End of update_vehicle_details function for vehicle_model_id={vehicle_model_id}")


@app.route('/delete-vehicles', methods=['DELETE'])
def delete_vehicles():
    """
    Deletes vehicle details based on provided query parameters.
    Parameters can include vehicle_model_id, vehicle_model, vehicle_year, and other optional fields.

    Query Parameters:
    - vehicle_model_id (str): The unique ID of the vehicle.
    - vehicle_model (str): The vehicle model name.
    - vehicle_year (int): The vehicle year.
    - engine_type (str): The engine type of the vehicle.
    - transmission (str): The transmission type of the vehicle.
    - fuel_type (str): The fuel type of the vehicle.
    - body_type (str): The body type of the vehicle.
    - warranty_period_years (int): The warranty period in years.
    - color (str): The color of the vehicle.
    - model_variant (str): The model variant (e.g., Top, Mid, Base).
    - tyre_company (str): The company of the tyre.
    - tyre_size (str): The size of the tyre.
    - start_type (str): The start type (e.g., Key, Push Start).
    - sunroof_available (bool): Whether the sunroof is available.
    - gear_type (str): The gear type (e.g., Gear, Gearless).
    - vehicle_type (str): The type of vehicle (e.g., SUV, Sedan, Hatchback).

    :return: JSON response with the number of vehicles deleted or error details.
    """
    log_info("Received request to delete vehicles with specified criteria.")

    # Extract query parameters
    criteria = {
        'vehicle_model': request.args.get('vehicle_model'),
        'vehicle_year': request.args.get('vehicle_year', type=int),
        'engine_type': request.args.get('engine_type'),
        'transmission': request.args.get('transmission'),
        'fuel_type': request.args.get('fuel_type'),
        'body_type': request.args.get('body_type'),
        'warranty_period_years': request.args.get('warranty_period_years', type=int),
        'color': request.args.get('color'),
        'model_variant': request.args.get('model_variant'),
        'tyre_company': request.args.get('tyre_company'),
        'tyre_size': request.args.get('tyre_size'),
        'start_type': request.args.get('start_type'),
        'sunroof_available': request.args.get('sunroof_available', type=bool),
        'gear_type': request.args.get('gear_type'),
        'vehicle_type': request.args.get('vehicle_type')
    }

    try:
        # Build query based on provided parameters
        query = session.query(VehicleDetails)
        for key, value in criteria.items():
            if value is not None:
                query = query.filter(getattr(VehicleDetails, key) == value)

        # Retrieve all vehicles that match the criteria
        vehicles_to_delete = query.all()

        # If no vehicles are found, return a message
        if not vehicles_to_delete:
            log_info("No vehicles found matching the criteria.")
            send_deletion_email(RECEIVER_EMAIL, 0, criteria, [])
            return jsonify({"message": "No vehicles found matching the criteria"}), 404

        # Delete the vehicles
        for vehicle in vehicles_to_delete:
            session.delete(vehicle)
        session.commit()

        # Log and notify about successful deletion
        num_deleted = len(vehicles_to_delete)
        log_info(f"{num_deleted} vehicles deleted successfully based on the provided criteria.")

        # Prepare detailed email content
        send_deletion_email(RECEIVER_EMAIL, num_deleted, criteria,
                            [vehicle.serialize_to_dict() for vehicle in vehicles_to_delete])

        # Return success message with the number of vehicles deleted and details
        return jsonify({
            "message": "Vehicle details deleted successfully.",
            "num_deleted": num_deleted,
            "deleted_vehicles": [vehicle.serialize_to_dict() for vehicle in vehicles_to_delete]
        }), 200

    except SQLAlchemyError as e:
        session.rollback()  # Rollback in case of error

        # Log and notify about the error
        log_error(f"Database error occurred while deleting vehicles: {str(e)}")
        send_deletion_email(RECEIVER_EMAIL, 0, criteria, [])

        return jsonify({"error": "Internal server error", "details": str(e)}), 500

    except Exception as e:
        # Handle any unexpected exceptions
        log_error(f"Unexpected error occurred while deleting vehicles: {str(e)}")
        send_deletion_email(RECEIVER_EMAIL, 0, criteria, [])

        return jsonify({"error": "Internal server error", "details": str(e)}), 500

    finally:
        log_info("End of delete_vehicles function.")


# --------------------------------------------- PURCHASED VEHICLES TABLE -----------------------------------------------


@app.route('/vehicle-purchase', methods=["POST"])
def handle_vehicle_purchase():
    """
    API to handle the purchase of a vehicle. It adds the vehicle purchase record, assigns the first 3 free services,
    and schedules the next service based on kilometers or date.
    """
    log_info("Received request to handle vehicle purchase")
    try:
        payload = request.get_json()
        log_debug(f"Request payload: {payload}")

        opportunity_id = payload.get("opportunity_id")
        log_info(f"Opportunity ID: {opportunity_id}")

        # Fetch the opportunity from the database
        opportunity = session.query(Opportunity).filter_by(opportunity_id=opportunity_id).first()

        if not opportunity:
            error_message = f"Opportunity not found for ID: {opportunity_id}"
            log_error(error_message)
            return jsonify({"error": error_message}), 404

        # Check if the opportunity indicates a completed vehicle purchase
        if opportunity.probability != 100:
            error_message = f"Vehicle not purchased yet, probability is {opportunity.probability}%"
            log_info(error_message)
            return jsonify({"message": "Vehicle purchase not confirmed"}), 400

        # Record the new vehicle purchase
        new_purchase = PurchasedVehicles(
            opportunity_id=opportunity_id,
            vehicle_model_id=opportunity.vehicle_model_id,
            vehicle_color=opportunity.vehicle_color,
            current_kilometers=0
        )
        session.add(new_purchase)
        session.commit()
        log_info(f"New vehicle purchase recorded: {new_purchase.vehicle_id}")

        # Assign the first 3 free services to the vehicle
        new_purchase.add_free_services(session)
        session.commit()
        log_info(f"First three free services added for vehicle {new_purchase.vehicle_id}")

        # Calculate and record the tax amount
        tax_amount = opportunity.amount * 0.05
        tax_record = calculate_taxes(new_purchase.vehicle_id, tax_amount)
        session.add(tax_record)
        session.commit()
        log_info(f"Tax record added for vehicle {new_purchase.vehicle_id}")

        # Prepare vehicle info for emails
        vehicle_info = new_purchase.serialize_to_dict()  # Serialize vehicle details
        next_service_info = schedule_next_service(new_purchase)  # Schedule next service
        free_services_left = 3  # Assuming 3 free services initially assigned

        # User email content preparation
        insurance_info = {"insurance_policy": "Policy XYZ"}  # Placeholder for insurance details
        user_email_body = generate_user_vehicle_purchase_email(
            vehicle_info, tax_amount, insurance_info, next_service_info, free_services_left
        )
        notify_success("Vehicle Purchase Confirmation", user_email_body)

        # Team email content preparation
        opportunity_info = opportunity.serialize_to_dict()  # Serialize opportunity details
        team_email_body = generate_team_vehicle_purchase_email(
            vehicle_info, opportunity_info, tax_amount, next_service_info, free_services_left
        )
        notify_success("New Vehicle Purchase - Internal Notification", team_email_body)

        # Return success message with details for response
        purchase_message = (f"Vehicle purchase registered successfully.\n\n"
                            f"Opportunity ID: {opportunity_id}\n"
                            f"Vehicle Model: {opportunity.vehicle_model}\n"
                            f"Vehicle Color: {opportunity.vehicle_color}\n"
                            f"First three free services have been added.\n"
                            f"Tax Amount: {tax_amount}")
        log_info(purchase_message)

        return jsonify({
            "message": "Vehicle purchased and services scheduled successfully",
            "purchase_details": vehicle_info,
            "next_service": next_service_info
        }), 201

    except SQLAlchemyError as e:
        session.rollback()
        error_message = f"Error in processing vehicle purchase: {str(e)}"
        log_error(error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500

    except Exception as e:
        session.rollback()
        error_message = f"Error in processing vehicle purchase: {str(e)}"
        log_error(error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500

    finally:
        session.close()
        log_info("End of handle_vehicle_purchase function")


@app.route('/purchased-vehicles', methods=["GET"])
def get_purchased_vehicles():
    log_info("Received request to get purchased vehicle details")
    log_info(f"Processing query parameters: {request.args}")

    try:
        # Get query parameters for filtering
        vehicle_id = request.args.get('vehicle_id')
        opportunity_id = request.args.get('opportunity_id')

        log_info(f"Filters applied: Vehicle ID: {vehicle_id}, Opportunity ID: {opportunity_id}")

        # Start the query for purchased vehicles
        query = session.query(PurchasedVehicles)

        # Apply filters if provided
        if vehicle_id:
            log_info(f"Applying filter: vehicle_id = {vehicle_id}")
            query = query.filter(PurchasedVehicles.vehicle_id == vehicle_id)

        if opportunity_id:
            log_info(f"Applying filter: opportunity_id = {opportunity_id}")
            query = query.filter(PurchasedVehicles.opportunity_id == opportunity_id)

        purchased_vehicles = query.all()
        log_info(f"Retrieved {len(purchased_vehicles)} purchased vehicles from the database")

        # Prepare vehicle list for response
        purchased_vehicles_list = [vehicle.serialize_to_dict() for vehicle in purchased_vehicles]

        # Prepare the result response
        result = {
            "total_purchased_vehicles": len(purchased_vehicles_list),
            "purchased_vehicles": purchased_vehicles_list,
        }

        # Email notification for successful retrieval
        if purchased_vehicles_list:
            email_body = generate_success_email(purchased_vehicles_list)
            send_email(RECEIVER_EMAIL, "Purchased Vehicle Details Retrieved", email_body)
            log_info(f"Sent email notification for {len(purchased_vehicles_list)} purchased vehicles")

        return jsonify(result), 200

    except SQLAlchemyError as e:
        error_message = f"Error retrieving purchased vehicles: {str(e)}"
        log_error(error_message)

        # Email notification for error
        error_email_body = generate_error_email(error_message)
        send_email(RECEIVER_EMAIL, "Error Retrieving Purchased Vehicles", error_email_body)

        return jsonify({"error": "Internal server error", "details": error_message}), 500

    except Exception as e:
        error_message = f"Unexpected error occurred: {str(e)}"
        log_error(error_message)

        # Email notification for unexpected error
        unexpected_error_email_body = generate_error_email(error_message)
        send_email(RECEIVER_EMAIL, "Unexpected Error Retrieving Purchased Vehicles",
                   unexpected_error_email_body)

        return jsonify({"error": "Internal server error", "details": error_message}), 500

    finally:
        session.close()
        log_info("End of get_purchased_vehicles function")


@app.route('/update-purchased-vehicle', methods=["PUT"])
def update_purchased_vehicle():
    """
    API to update the details of a purchased vehicle.
    """
    vehicle_id = request.args.get('vehicle_id')  # Ensure you get the vehicle ID from the request
    log_info(f"Received request to update vehicle with ID: {vehicle_id}")

    try:
        # Get the payload from the request
        payload = request.get_json()
        log_debug(f"Request payload: {payload}")

        # Fetch the existing vehicle record
        vehicle = session.query(PurchasedVehicles).filter_by(vehicle_id=vehicle_id).first()

        if not vehicle:
            error_message = f"Vehicle not found for ID: {vehicle_id}"
            log_error(error_message)
            return jsonify({"error": error_message}), 404

        updated_fields = {}

        if 'vehicle_color' in payload:
            updated_fields['vehicle_color'] = payload['vehicle_color']
            vehicle.vehicle_color = payload['vehicle_color']
            log_info(f"Updated vehicle color to: {vehicle.vehicle_color}")

        if 'current_kilometers' in payload:
            updated_fields['current_kilometers'] = payload['current_kilometers']
            vehicle.current_kilometers = payload['current_kilometers']
            log_info(f"Updated current kilometers to: {vehicle.current_kilometers}")

        # Update services if provided
        if 'services' in payload:
            for service_data in payload['services']:
                service_id = service_data.get('service_id')
                if service_id:
                    service = session.query(VehicleServices).filter_by(id=service_id, vehicle_id=vehicle_id).first()
                    if service:
                        updated_fields['services'] = updated_fields.get('services', [])
                        updated_fields['services'].append(service_id)
                        service.service_type = service_data.get('service_type', service.service_type)
                        service.kilometers_at_service = service_data.get('kilometers_at_service', service.kilometers_at_service)
                        service.description = service_data.get('description', service.description)
                        log_info(f"Updated service ID {service_id}")

        # Update taxes if provided
        if 'taxes' in payload:
            for tax_data in payload['taxes']:
                tax_id = tax_data.get('tax_id')
                if tax_id:
                    tax = session.query(Taxes).filter_by(tax_id=tax_id, vehicle_id=vehicle_id).first()
                    if tax:
                        updated_fields['taxes'] = updated_fields.get('taxes', [])
                        updated_fields['taxes'].append(tax_id)
                        tax.tax_amount = tax_data.get('tax_amount', tax.tax_amount)
                        tax.tax_type = tax_data.get('tax_type', tax.tax_type)
                        tax.due_date = tax_data.get('due_date', tax.due_date)
                        log_info(f"Updated tax ID {tax_id}")

        session.commit()
        log_info(f"Vehicle with ID {vehicle_id} updated successfully")

        # Prepare response
        response = vehicle.serialize_to_dict()
        # Send email notification
        notify_vehicle_update_success("Vehicle Update Notification", response, updated_fields)

        return jsonify({
            "message": "Vehicle updated successfully",
            "updated_vehicle": response
        }), 200

    except SQLAlchemyError as e:
        session.rollback()
        error_message = f"Error updating vehicle: {str(e)}"
        log_error(error_message)

        # Send failure email notification
        failure_email_body = generate_failure_email(error_message)
        send_email(RECEIVER_EMAIL, "Error Updating Vehicle", failure_email_body)

        return jsonify({"error": "Internal server error", "details": error_message}), 500

    except Exception as e:
        session.rollback()
        error_message = f"Unexpected error occurred: {str(e)}"
        log_error(error_message)

        # Send unexpected error email notification
        unexpected_error_email_body = generate_failure_email(error_message)
        send_email(RECEIVER_EMAIL, "Unexpected Error Updating Vehicle", unexpected_error_email_body)

        return jsonify({"error": "Internal server error", "details": error_message}), 500

    finally:
        session.close()
        log_info("End of update_purchased_vehicle function")


if __name__ == "__main__":
    app.run(debug=True)
