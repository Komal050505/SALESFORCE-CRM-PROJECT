"""
This module defines SQLAlchemy ORM models for `Account`, `Dealer`, and `Opportunity` tables.

It captures details about customer accounts, dealers, and opportunities.
"""

# SQLAlchemy imports
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship

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

    account_id = Column("account_id", String(100), primary_key=True)  # We are using First 3 letters of account name +
    # 4 random digits for manually created at the time of account creation, not in create new customer api remember

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


# ------------------------------------------ Opportunity Table ---------------------------------------------------------
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

    # New fields for vehicle details
    vehicle_model_id = Column("vehicle_model_id", String, ForeignKey('vehicle_details.vehicle_model_id'))
    vehicle_model = Column("vehicle_model", String)
    vehicle_year = Column("vehicle_year", Integer)
    vehicle_color = Column("vehicle_color", String)

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
            'currency_conversions': format_currency_conversions(),
            'vehicle_model_id': self.vehicle_model_id,
            'vehicle_model': self.vehicle_model,
            'vehicle_year': self.vehicle_year,
            'vehicle_color': self.vehicle_color
        }


# ------------------------------------------ Vehicle Details Table -----------------------------------------------------


# VehicleDetails model (Vehicle catalog information)
class VehicleDetails(Base):
    __tablename__ = 'vehicle_details'

    vehicle_model_id = Column("vehicle_model_id", String, primary_key=True, default=lambda: str(uuid.uuid1()))
    vehicle_model = Column("vehicle_model", String, nullable=False)
    vehicle_year = Column("vehicle_year", Integer, nullable=False)
    engine_type = Column("engine_type", String, nullable=True)
    transmission = Column("transmission", String, nullable=True)
    fuel_type = Column("fuel_type", String, nullable=True)
    body_type = Column("body_type", String, nullable=True)
    warranty_period_years = Column("warranty_period_years", Integer, nullable=True)
    color = Column("color", String, nullable=True)
    model_variant = Column("model_variant", String, nullable=True)  # e.g., Top, Mid, Base
    tyre_company = Column("tyre_company", String, nullable=True)
    tyre_size = Column("tyre_size", String, nullable=True)
    start_type = Column("start_type", String, nullable=True)  # e.g., Key, Push Start
    sunroof_available = Column("sunroof_available", Boolean, nullable=True)
    gear_type = Column("gear_type", String, nullable=True)  # e.g., Gear, Gearless
    vehicle_type = Column("vehicle_type", String, nullable=True)  # e.g., SUV, Sedan, Hatchback

    def serialize_to_dict(self):
        return {
            'vehicle_model_id': self.vehicle_model_id,
            'vehicle_model': self.vehicle_model,
            'vehicle_year': self.vehicle_year,
            'engine_type': self.engine_type,
            'transmission': self.transmission,
            'fuel_type': self.fuel_type,
            'body_type': self.body_type,
            'warranty_period_years': self.warranty_period_years,
            'color': self.color,
            'model_variant': self.model_variant,
            'tyre_company': self.tyre_company,
            'tyre_size': self.tyre_size,
            'start_type': self.start_type,
            'sunroof_available': self.sunroof_available,
            'gear_type': self.gear_type,
            'vehicle_type': self.vehicle_type
        }


# ------------------------------------------ Purchased Vehicles Table ---------------------------------------------------------


# PurchasedVehicles model (Information about purchased vehicles)
class PurchasedVehicles(Base):
    __tablename__ = 'purchased_vehicles'

    vehicle_id = Column("vehicle_id", String, primary_key=True, default=lambda: str(uuid.uuid1()))
    opportunity_id = Column("opportunity_id", String, ForeignKey('opportunity.opportunity_id'), nullable=False)
    purchase_date = Column("purchase_date", DateTime, nullable=False,
                           default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    vehicle_model_id = Column("vehicle_model_id", String, ForeignKey('vehicle_details.vehicle_model_id'),
                              nullable=False)
    vehicle_color = Column("vehicle_color", String, nullable=False)
    current_kilometers = Column("current_kilometers", Float, nullable=False)

    # Relationships
    opportunity = relationship("Opportunity", backref="purchased_vehicles")
    vehicle_details = relationship("VehicleDetails", backref="purchased_vehicles")
    services = relationship("VehicleServices", backref="purchased_vehicle", cascade="all, delete-orphan")
    insurance = relationship("Insurance", uselist=False, backref="purchased_vehicle", cascade="all, delete-orphan")

    def add_free_services(self, session):
        """
        Add first three free services upon vehicle purchase.
        """
        free_service_types = ["First Free Service", "Second Free Service", "Third Free Service"]
        kilometers_at_service = [1000, 5000, 10000]  # Set service intervals (in kilometers)

        for index, service_type in enumerate(free_service_types):
            new_service = VehicleServices(
                vehicle_id=self.vehicle_id,
                service_type=service_type,
                kilometers_at_service=kilometers_at_service[index],
                description=f"{service_type} up to {kilometers_at_service[index]} kilometers."
            )
            session.add(new_service)

    def serialize_to_dict(self):
        """
        Serialize the purchased vehicle to a dictionary, including services and insurance.
        :return: dict
        """
        return {
            'vehicle_id': self.vehicle_id,
            'opportunity_id': self.opportunity_id,
            'purchase_date': self.purchase_date.strftime("%I:%M %p, %B %d, %Y"),
            'vehicle_model_id': self.vehicle_model_id,
            'vehicle_model': self.vehicle_details.vehicle_model if self.vehicle_details else None,
            'vehicle_year': self.vehicle_details.vehicle_year if self.vehicle_details else None,
            'vehicle_color': self.vehicle_color,
            'current_kilometers': self.current_kilometers,
            'services': [service.serialize_to_dict() for service in self.services],
            'insurance': self.insurance.serialize_to_dict() if self.insurance else None
        }


# ------------------------------------------ Taxes Table ---------------------------------------------------------------
class Taxes(Base):
    __tablename__ = 'taxes'

    tax_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    vehicle_id = Column(String, ForeignKey('purchased_vehicles.vehicle_id'), nullable=False)
    tax_amount = Column(Float, nullable=False)
    tax_type = Column(String, nullable=False)
    due_date = Column(DateTime, nullable=False)

    # Relationship with PurchasedVehicles
    purchased_vehicle = relationship("PurchasedVehicles", backref="taxes")


# ------------------------------------------ Vehicle Services Table ----------------------------------------------------


# VehicleServices model (Details about services performed on the vehicle)

class VehicleServices(Base):
    __tablename__ = 'vehicle_services'

    service_id = Column("service_id", String, primary_key=True, default=lambda: str(uuid.uuid1()))
    vehicle_id = Column("vehicle_id", String, ForeignKey('purchased_vehicles.vehicle_id'), nullable=False)
    service_date = Column("service_date", DateTime, nullable=False,
                          default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    service_type = Column("service_type", String,
                          nullable=False)  # Type of service (e.g., Oil Change, Tire Replacement)
    kilometers_at_service = Column("kilometers_at_service", Float)  # Kilometers reading at the time of service
    description = Column("description", String)  # Additional details about the service

    def serialize_to_dict(self):
        """
        Serialize the vehicle service to a dictionary.
        :return: dict
        """
        return {
            'service_id': self.service_id,
            'vehicle_id': self.vehicle_id,
            'service_date': self.service_date.strftime("%I:%M %p, %B %d, %Y"),
            'service_type': self.service_type,
            'kilometers_at_service': self.kilometers_at_service,
            'description': self.description
        }


# ------------------------------------------ Insurance Table ---------------------------------------------------------

# Insurance model (Details about the insurance policy of the purchased vehicle)
class Insurance(Base):
    __tablename__ = 'insurance'

    insurance_id = Column("insurance_id", String, primary_key=True, default=lambda: str(uuid.uuid1()))
    vehicle_id = Column("vehicle_id", String, ForeignKey('purchased_vehicles.vehicle_id'), nullable=False)
    insurance_company = Column("insurance_company", String, nullable=False)
    policy_number = Column("policy_number", String, nullable=False, unique=True)
    insurance_start_date = Column("insurance_start_date", DateTime, nullable=False)
    insurance_expiry_date = Column("insurance_expiry_date", DateTime, nullable=False)
    coverage_amount = Column("coverage_amount", Float, nullable=False)

    def serialize_to_dict(self):
        """
        Serialize the insurance record to a dictionary.
        :return: dict
        """
        return {
            'insurance_id': self.insurance_id,
            'vehicle_id': self.vehicle_id,
            'insurance_company': self.insurance_company,
            'policy_number': self.policy_number,
            'insurance_start_date': self.insurance_start_date.strftime("%B %d, %Y"),
            'insurance_expiry_date': self.insurance_expiry_date.strftime("%B %d, %Y"),
            'coverage_amount': self.coverage_amount
        }
