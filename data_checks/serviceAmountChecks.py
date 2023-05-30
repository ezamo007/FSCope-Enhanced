from flask import jsonify, render_template
from database import db, Client, Enrollment, Service

def find_members_with_expenses():
    # Retrieve all client enrollments
    query = db.session.query(Enrollment, Client, Service)
    services = query.join(Client, Enrollment.client_id == Client.client_id).join(Service, Enrollment.enrollment_id == Service.enrollment_id).all()

    errors = []

    for result in services:
        if(result.Enrollment.hoh == 'No' and result.Service.service_amount > 0):

            error = {
                    'client_name': result.Client.client_name,
                    'client_id': result.Client.client_id,
                    'program_name': result.Enrollment.program_name,
                    'entry_date': result.Enrollment.entry_date,
                    'exit_date': result.Enrollment.exit_date if result.Enrollment.exit_date is not None else "",
                    'service_name': result.Service.service_name,
                    'service_amount': result.Service.service_amount,
                    'start_date': result.Service.start_date,
                    'end_date': result.Service.end_date
                    }
            print(error)
            errors.append(error)
    return errors


