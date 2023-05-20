from flask_sqlalchemy import SQLAlchemy
import csv
from datetime import datetime

db = SQLAlchemy()

class Household(db.Model):
    household_id = db.Column(db.Integer,primary_key=True)

class Client(db.Model):
    household_id = db.Column(db.Integer,db.ForeignKey('household.household_id'))
    client_id = db.Column(db.String(9),primary_key=True)
    client_name = db.Column(db.String(100))

class Enrollment(db.Model):
    client_id = db.Column(db.String(9),db.ForeignKey('client.client_id'))
    enrollment_id = db.Column(db.Integer,primary_key=True)
    program_name = db.Column(db.String(100))
    hoh = db.Column(db.String(3))
    entry_date = db.Column(db.Date)
    exit_date = db.Column(db.Date, nullable=True)

class Service(db.Model):
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollment.enrollment_id'))
    service_id = db.Column(db.Integer,primary_key=True)
    service_name = db.Column(db.String(100))
    service_amount = db.Column(db.Float)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()

        # Add households to database.
        with open('data/enrollments.csv', 'r') as f:
            reader = csv.DictReader(f)
            data = [row for row in reader]
        for row in data:
            existing_household = Household.query.filter_by(household_id=row['Household ID']).first()
            if existing_household:
                continue
            record = Household(household_id=row['Household ID'])
            db.session.add(record)

        # Add clients to households in database.
        with open('data/enrollments.csv', 'r') as f:
            reader = csv.DictReader(f)
            data = [row for row in reader]
        for row in data:
            existing_client = Client.query.filter_by(client_id=row['Client ID']).first()
            if existing_client:
                continue
            record = Client(household_id=row['Household ID'], client_id=row['Client ID'], client_name=row['Client Name'])
            db.session.add(record)

        # Add enrollments to clients in database.
        with open('data/enrollments.csv', 'r') as f:
            reader = csv.DictReader(f)
            data = [row for row in reader]
        for row in data:
            existing_enrollment = Enrollment.query.filter_by(enrollment_id=row['Enrollment ID']).first()
            if existing_enrollment:
                continue
            entry_date = datetime.strptime(row['Entry Date'], '%Y-%m-%d').date()
            exit_date = datetime.strptime(row['Exit Date'], '%Y-%m-%d').date() if row['Exit Date'] else None
            record = Enrollment(client_id=row['Client ID'], enrollment_id=row['Enrollment ID'], hoh=row['HoH'], program_name=row['Program Name'], entry_date=entry_date, exit_date=exit_date)
            db.session.add(record)

        # Add services to enrollments in database.
        with open('data/services.csv', 'r') as f:
            reader = csv.DictReader(f)
            data = [row for row in reader]
        for row in data:
            existing_service = Service.query.filter_by(service_id=row['Service ID']).first()
            if existing_service:
                continue
            start_date = datetime.strptime(row['Start Date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(row['End Date'], '%Y-%m-%d').date()
            record = Service(enrollment_id=row['Enrollment ID'], service_id=row['Service ID'], service_name=row['Service Name'], service_amount=float(row['Service Amount']), start_date=start_date, end_date=end_date)
            db.session.add(record)
        db.session.commit()