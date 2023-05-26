from flask import jsonify, render_template
from database import db, Client, Enrollment

def findDuplicateEnrollments():
    # Retrieve all client enrollments
    query = db.session.query(Enrollment, Client)
    enrollments = query.join(Client, Enrollment.client_id == Client.client_id).all()

    errors = []

    for result in enrollments:
        print(result.Client.client_name)

    for i in range(len(enrollments)):
        for j in range(i + 1, len(enrollments)):
            enrollment1, client1 = enrollments[i]
            enrollment2, client2 = enrollments[j]

            if (
                # Ensure enrollments are from the same client, with the same program name.
                client1.client_id == client2.client_id
                and enrollment1.program_name == enrollment2.program_name
                and (
                    (
                        enrollment1.entry_date <= enrollment2.entry_date
                        and (enrollment1.exit_date is None or enrollment2.exit_date is None or enrollment1.exit_date >= enrollment2.entry_date)
                    )
                    or (
                        enrollment1.entry_date <= enrollment2.exit_date <= enrollment1.exit_date
                    )
                )
            ):
                # Overlapping date ranges found
                error = {
                    'client_name': client1.client_name,
                    'enrollment_id_1': enrollment1.enrollment_id,
                    'enrollment_id_2': enrollment2.enrollment_id
                }
                errors.append(error)
    return errors