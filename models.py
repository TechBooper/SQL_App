from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

# Database setup
engine = create_engine('sqlite:///app.db')
Session = sessionmaker(bind=engine)

# User model
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)

    role = relationship("Role")

# Role model
class Role(Base):
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)

# Client model
class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    company_name = Column(String(100))
    first_contact_date = Column(Date)
    last_update_date = Column(Date)
    commercial_contact = Column(Integer, ForeignKey('users.id'))  # The user responsible for the client

    user = relationship("User", back_populates="clients")

# Contract model
class Contract(Base):
    __tablename__ = 'contracts'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    commercial_contact = Column(Integer, ForeignKey('users.id'))  # The user handling the contract
    total_amount = Column(Float, nullable=False)
    amount_due = Column(Float, nullable=False)
    creation_date = Column(Date, nullable=False)
    signed = Column(Boolean, default=False)

    client = relationship("Client")
    user = relationship("User")

# Event model
class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey('contracts.id'), nullable=False)
    event_name = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    location = Column(String(255), nullable=False)
    support_contact = Column(Integer, ForeignKey('users.id'))  # User in charge of the event
    attendees = Column(Integer)
    notes = Column(String(500))

    contract = relationship("Contract")
    user = relationship("User")

# To create the tables
Base.metadata.create_all(engine)
