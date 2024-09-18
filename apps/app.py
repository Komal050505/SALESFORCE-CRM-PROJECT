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

# Email Operations
from email_setup.email_operations import (  # Email notifications
    notify_success,
    notify_failure,
    notify_opportunity_details,
    notify_opportunity_update_success
)

# Logging Utility
from logging_package.logging_utility import (  # Logging information, errors, and debugging
    log_info,
    log_error,
    log_debug
)

# User Models
from user_models.tables import Account, Dealer, Opportunity  # Database models for account, dealer, and opportunity

# Utility Functions
from utilities.reusables import (  # Reusable utility functions for validations and conversions
    get_currency_conversion,
    get_opportunity_stage,
    validate_stage,
    validate_probability,
    parse_date,
    validate_positive_number
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


# ----------------------------------------------- OPPORTUNITY TABLE ------------------------------------------------


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

        account_name = payload.get("account_name")
        account = session.query(Account).filter_by(account_name=account_name).first()

        if not account:
            error_message = f"Account does not exist: {account_name}"
            log_error(error_message)
            detailed_error_message = (f"Failed to create customer due to missing account.\n"
                                      f"Account Name: {account_name}")
            notify_failure("Customer Creation Failed", detailed_error_message)
            return jsonify({"error": error_message}), 400
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
            error_message = f"Invalid dealer details: {dealer_id}, {dealer_code}, {opportunity_owner}"
            log_error(error_message)
            detailed_error_message = (f"Failed to create customer due to invalid dealer details.\n"
                                      f"Dealer ID: {dealer_id}\n"
                                      f"Dealer Code: {dealer_code}\n"
                                      f"Opportunity Owner: {opportunity_owner}")
            notify_failure("Customer Creation Failed", detailed_error_message)
            return jsonify({"error": error_message}), 400
        log_info(f"Dealer found: {dealer_id}, {dealer_code}, {opportunity_owner}")

        close_date_str = payload.get("close_date")
        if close_date_str:
            try:
                close_date = datetime.strptime(close_date_str, "%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                error_message = f"Invalid date format for close_date: {str(e)}"
                log_error(error_message)
                detailed_error_message = f"Failed to create customer due to invalid date format.\nError: {str(e)}"
                notify_failure("Customer Creation Failed", detailed_error_message)
                return jsonify({"error": error_message}), 400
        else:
            close_date = None

        probability = payload.get("probability")
        if probability is not None:
            try:
                stage = get_opportunity_stage(probability)
            except ValueError as e:
                error_message = f"Invalid probability value: {str(e)}"
                log_error(error_message)
                notify_failure("Customer Creation Failed", error_message)
                return jsonify({"error": error_message}), 400
        else:
            stage = payload.get("stage", "Unknown")

        amount = payload.get("amount")
        if amount:
            currency_conversions = get_currency_conversion(amount)
        else:
            currency_conversions = {}

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
            amount_in_words=str(amount)
        )

        session.add(new_opportunity)
        session.commit()
        log_info(f"Opportunity created successfully: {opportunity_id}")

        customer_details = new_opportunity.serialize_to_dict()

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
                           f"Created Date: {created_date.strftime('%Y-%m-%d %H:%M:%S')}")
        notify_success("Customer Creation Successful", success_message)

        return jsonify({
            "message": "Created successfully",
            "customer_details": customer_details
        }), 201

    except Exception as e:
        error_message = f"Error in creating customer: {str(e)}"
        log_error(error_message)
        detailed_error_message = f"Failed to create customer due to an internal server error.\nDetails: {str(e)}"
        notify_failure("Customer Creation Failed", detailed_error_message)
        return jsonify({"error": "Internal server error", "details": error_message}), 500

    finally:
        log_info("End of create_new_customer function")


@app.route('/get-opportunities', methods=['GET'])
def get_opportunities():
    """
    Fetches opportunities from the opportunity table based on query parameters.
    :return: JSON response with filtered opportunity details and total count.
    """
    log_info("Received request to get opportunities with query parameters")

    try:
        opportunity_id = request.args.get('opportunity_id')
        opportunity_name = request.args.get('opportunity_name')
        account_name = request.args.get('account_name')
        stage = request.args.get('stage')
        probability_min = request.args.get('probability_min', type=int)
        probability_max = request.args.get('probability_max', type=int)
        created_date_start = request.args.get('created_date_start')
        created_date_end = request.args.get('created_date_end')

        if created_date_start:
            created_date_start = parse_date(created_date_start)
        if created_date_end:
            created_date_end = parse_date(created_date_end)

        if probability_min is not None and not validate_probability(probability_min):
            raise ValueError(f"Invalid minimum probability: {probability_min}. Must be between 0 and 100")

        if probability_max is not None and not validate_probability(probability_max):
            raise ValueError(f"Invalid maximum probability: {probability_max}. Must be between 0 and 100")

        if probability_min is not None and probability_max is not None and probability_min > probability_max:
            raise ValueError("Minimum probability cannot be greater than maximum probability")

        if stage:
            stage = validate_stage(stage)

        query = session.query(Opportunity)

        if opportunity_id:
            query = query.filter(Opportunity.opportunity_id == opportunity_id)
        if opportunity_name:
            if len(opportunity_name) > 255:
                raise ValueError("Opportunity name is too long. Maximum length is 255 characters.")
            query = query.filter(Opportunity.opportunity_name.like(f'%{opportunity_name}%'))
        if account_name:
            if len(account_name) > 255:
                raise ValueError("Account name is too long. Maximum length is 255 characters.")
            query = query.filter(Opportunity.account_name.like(f'%{account_name}%'))
        if stage:
            query = query.filter(Opportunity.stage == stage)
        if probability_min is not None:
            query = query.filter(Opportunity.probability >= probability_min)
        if probability_max is not None:
            query = query.filter(Opportunity.probability <= probability_max)
        if created_date_start:
            query = query.filter(Opportunity.created_date >= created_date_start)
        if created_date_end:
            query = query.filter(Opportunity.created_date <= created_date_end)

        opportunities = query.all()
        total_count = len(opportunities)
        log_info(f"Fetched {total_count} opportunities based on query parameters")

        opportunities_list = [opportunity.serialize_to_dict() for opportunity in opportunities]

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

        if not opportunity_id:
            raise ValueError("Opportunity ID is required.")

        if opportunity_name and len(opportunity_name) > 255:
            raise ValueError("Opportunity name is too long. Maximum length is 255 characters.")

        if account_name and len(account_name) > 255:
            raise ValueError("Account name is too long. Maximum length is 255 characters.")

        if close_date:
            close_date = parse_date(close_date)

        if amount is not None and not validate_positive_number(amount):
            raise ValueError("Amount must be a positive number.")

        if probability is not None and not validate_probability(probability):
            raise ValueError("Probability must be between 0 and 100.")

        if stage:
            stage = validate_stage(stage)

        valid_currencies = ['usd', 'aus', 'cad', 'jpy', 'eur', 'gbp', 'cny']
        for currency in valid_currencies:
            if currency in currency_conversions:
                if not validate_positive_number(currency_conversions[currency]):
                    raise ValueError(f"Invalid value for currency conversion {currency}. Must be a positive number.")

        opportunity = session.query(Opportunity).filter_by(opportunity_id=opportunity_id).first()
        if not opportunity:
            raise ValueError("Opportunity not found.")

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
        if currency_conversions:
            opportunity.usd = currency_conversions.get('usd')
            opportunity.aus = currency_conversions.get('aus')
            opportunity.cad = currency_conversions.get('cad')
            opportunity.jpy = currency_conversions.get('jpy')
            opportunity.eur = currency_conversions.get('eur')
            opportunity.gbp = currency_conversions.get('gbp')
            opportunity.cny = currency_conversions.get('cny')
            updated_fields['currency_conversions'] = currency_conversions

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


if __name__ == "__main__":
    app.run(debug=True)
