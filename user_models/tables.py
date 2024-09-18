"""
This module defines SQLAlchemy ORM models for `Account`, `Dealer`, and `Opportunity` tables.

It captures details about customer accounts, dealers, and opportunities.
"""

# SQLAlchemy imports
from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.orm import declarative_base

# Date and UUID imports
from datetime import datetime
import uuid
import pytz


# Base class for SQLAlchemy ORM models
Base = declarative_base()


# --------------------------------------- Account Table -----------------------------------------------------------
class Account(Base):
    """
    SQLAlchemy ORM class representing the 'account' table.

    This table stores customer account details like account_id and account_name.
    """
    __tablename__ = 'account'

    account_id = Column("account_id", String(10), primary_key=True)  # We are using First 3 letters of account name +
    # 4 random digits

    account_name = Column("account_name", String, nullable=False)

    def account_serialize_to_dict(self):
        """
        Converts the Account object into a dictionary.
        """
        return {
            'account_id': self.account_id,
            'account_name': self.account_name
        }


# ------------------------------------------ Dealer Table ---------------------------------------------------------
class Dealer(Base):
    """
    This table stores dealer information like dealer ID, code, and opportunity owner.
    """
    __tablename__ = 'dealer'

    dealer_id = Column("dealer_id", String, primary_key=True, default=lambda: str(uuid.uuid1()))
    dealer_code = Column("dealer_code", String, nullable=False)
    opportunity_owner = Column("opportunity_owner", String, nullable=False)

    def dealer_serialize_to_dict(self):
        """
        Converts the Dealer object into a dictionary.
        """
        return {
            'dealer_id': self.dealer_id,
            'dealer_code': self.dealer_code,
            'opportunity_owner': self.opportunity_owner
        }


#  Opportunity Table

class Opportunity(Base):
    __tablename__ = 'opportunity'

    opportunity_id = Column("opportunity_id", String, primary_key=True, default=lambda: str(uuid.uuid1()))
    opportunity_name = Column("opportunity_name", String, nullable=False)
    account_name = Column("account_name", String, nullable=False)
    close_date = Column("close_date", DateTime, nullable=False)
    amount = Column("amount", Float, nullable=False)
    description = Column("description", String)
    dealer_id = Column("dealer_id", String, nullable=False)
    dealer_code = Column("dealer_code", String, nullable=False)
    stage = Column("stage", String, nullable=False)
    probability = Column("probability", Integer)
    next_step = Column("next_step", String)
    created_date = Column("created_date", DateTime, nullable=False,
                          default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))

    # New fields for currency conversions and amount in words
    amount_in_words = Column("amount_in_words", String)
    usd = Column("usd", Float)  # US Dollars
    aus = Column("aus", Float)  # Australian Dollars
    cad = Column("cad", Float)  # Canadian Dollars
    jpy = Column("jpy", Float)  # Japanese Yen
    eur = Column("eur", Float)  # Euros
    gbp = Column("gbp", Float)  # British Pounds
    cny = Column("cny", Float)  # Chinese Yuan

    def serialize_to_dict(self):
        """
        Serialize the Opportunity instance to a dictionary with formatted dates and currency conversions.
        :return: dict
        """

        def format_datetime(dt):
            """Format datetime to 12-hour format with AM/PM"""
            return dt.strftime("%I:%M %p, %B %d, %Y") if dt else None

        def format_currency_conversions():
            """Format currency conversions into a readable string"""
            currencies = {
                'USD': self.usd,
                'AUD': self.aus,
                'CAD': self.cad,
                'JPY': self.jpy,
                'EUR': self.eur,
                'GBP': self.gbp,
                'CNY': self.cny
            }
            return '\n'.join(
                f"{currency}: {value if value is not None else 'None'}" for currency, value in currencies.items())

        return {
            'opportunity_id': self.opportunity_id,
            'opportunity_name': self.opportunity_name,
            'account_name': self.account_name,
            'close_date': format_datetime(self.close_date),
            'amount': self.amount,
            'description': self.description,
            'dealer_id': self.dealer_id,
            'dealer_code': self.dealer_code,
            'stage': self.stage,
            'probability': self.probability,
            'next_step': self.next_step,
            'created_date': format_datetime(self.created_date),
            'amount_in_words': self.amount_in_words,
            'currency_conversions': format_currency_conversions()
        }

