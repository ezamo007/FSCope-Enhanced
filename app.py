from jinja2 import Environment
from data_checks.enrollmentDateChecks import findDuplicateEnrollments
import csv
from flask import Flask, render_template, request, jsonify
from flask_material import Material
from database import db, init_db, Household, Client, Enrollment, Service
from sqlalchemy import create_engine, or_, and_, inspect, text
from sqlalchemy.orm import sessionmaker
app = Flask(__name__, static_folder='static')
Material(app)

def get_attr(obj, attr):
    return getattr(obj, attr)

env = Environment()

env.filters['get_attr'] = get_attr

# Set the app configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the data from the CSV files
with app.app_context():
    init_db(app)

# Create SQLAlchemy engine and session
engine = create_engine('sqlite:///database.db')
Session = sessionmaker(bind=engine)
session = Session()

# Define the app routes
@app.route('/')
def display_csv():
    # Create spreadsheet object.
    spreadsheetData = {}

    # Read the CSV file
    with open('data/enrollments.csv', 'r') as file:
        csv_data = csv.reader(file)
        spreadsheetData["enrollments"] = list(csv_data)
    with open('data/notes.csv', 'r') as file:
            csv_data = csv.reader(file)
            spreadsheetData["notes"] = list(csv_data)
    with open('data/services.csv', 'r') as file:
            csv_data = csv.reader(file)
            spreadsheetData["services"] = list(csv_data)

    # Render the HTML template and pass the CSV data
    return render_template('index.html', spreadsheetData = spreadsheetData)

@app.route('/search', methods=['GET', 'POST'])
def search():
    return render_template('search.html')


@app.route('/results', methods=['POST'])
def search_results():
    # Get form data from request
    search_fields = request.form.getlist('search-field')
    search_operators = request.form.getlist('search-operator')
    search_values = request.form.getlist('search-value')
    search_logics = request.form.getlist('search-logic')
    columns = request.form.getlist('columns')
    # Build SQLAlchemy query dynamically based on form data
    print(f"Search fields: {search_fields}")
    print(f"Columns requested: {columns}")
    
    
    def levelOfDetail(attribute_list):
        hasClient = any("Client" in attribute for attribute in attribute_list)
        hasEnrollment = any("Enrollment" in attribute for attribute in attribute_list)
        hasService = any("Service" in attribute for attribute in attribute_list)

        if hasService:
            return 4
        elif hasEnrollment:
            return 3
        elif hasClient:
            return 2
        else:
            return 1

    columns_lvl = levelOfDetail(columns)
    search_fields_lvl = levelOfDetail(search_fields)

    print("Level of detail (columns)", columns_lvl)

    # Start with the Household table
    query = db.session.query(Household)

    # Determine the maximum level of detail
    max_lvl = max(columns_lvl, search_fields_lvl)

    if max_lvl >= 2:
        query = query.add_columns(Client).join(Client, Household.household_id == Client.household_id)
        if max_lvl >= 3:
            query = query.add_columns(Enrollment).join(Enrollment, Client.client_id == Enrollment.client_id)
            if max_lvl == 4:
                query = query.add_columns(Service).join(Service, Enrollment.enrollment_id == Service.enrollment_id)
        
    if search_fields_lvl > columns_lvl:
        if columns_lvl == 2:  # If columns ask for clients, but search-fields ask for enrollment info.
            query = query.distinct(Client.client_id)
        elif columns_lvl == 3:  # Columns ask for enrollments, but search-fields ask for service info.
            query = query.distinct(Enrollment.enrollment_id)

    # Create a mapping of strings to class attributes:
    attr_map = {
        'Enrollment.enrollment_id': Enrollment.enrollment_id,
        'Enrollment.program_name': Enrollment.program_name,  
        'Enrollment.entry_date': Enrollment.entry_date,  
        'Enrollment.exit_date': Enrollment.exit_date,  
        'Client.client_name': Client.client_name,
        'Client.client_id': Client.client_id,
        'Service.service_name': Service.service_name,
        'Service.start_date': Service.start_date,
        'Service.end_date': Service.end_date,
        'Service.service_amount': Service.service_amount,
    }

    # Convert list of strings to a list of attributes:
    attr_list = [attr_map[attr] for attr in columns]

    # Use this list in query:
    query = query.with_entities(*attr_list) 

    
    criteria = []

    criteria_ands = []

    for i in range(len(search_fields)):
        objectName, field = search_fields[i].split(".")
        operator = search_operators[i]
        value = search_values[i]

        object_map = {
            'Household': Household,
            'Enrollment': Enrollment,
            'Service': Service,
            'Client': Client
        }
        obj = object_map[objectName]

        # Handle different operators
        if operator == "=":
            criterion = getattr(obj, field) == value
        elif operator == ">":
            criterion = getattr(obj, field) > value
        elif operator == "<":
            criterion = getattr(obj, field) < value
        elif operator == "!=":
            criterion = getattr(obj, field) != value
        elif operator == "like":
            criterion = getattr(obj, field).like(f"%{value}%")
        elif operator == "not-like":
            criterion = ~getattr(obj, field).like(f"%{value}%")

        criteria.append(criterion)

    thing = criteria[0]
    
    for i in range(len(search_logics)-1):
       # print(search_logics[i], "LOL", criteria[i+1])
        if (search_logics[i] == "AND"):
            thing = and_(thing, criteria[i+1])
        else:
            criteria_ands.append(thing)
            thing = criteria[i+1]
            
    criteria_ands.append(thing)
    query = query.filter(or_(*criteria_ands))



    

    commonNamesMap = {
            'Enrollment.program_name': "Program Name",  
            'Enrollment.entry_date': "Program Entry Date",  
            'Enrollment.exit_date': "Program Exit Date",  
            'Client.client_name': "Client Name",
            'Client.client_id': "Client ID",
            'Service.service_name': "Service Name",
            'Service.start_date': "Service Start Date",
            'Service.end_date': "Service End Date",
            'Service.service_amount': "Service Amount",
        }

    print(f"SQL Query: {query.statement.compile(dialect=engine.dialect, compile_kwargs={'literal_binds': True})}")

    # Execute query and get results
    results = query.all()
    tableHeader = []
    tableValues = []
    for row in results:
        tableValues.append(row)
    # Render the template with the query results
    return render_template('results.html', results={'header': [commonNamesMap[column] for column in columns], 'body': tableValues})

@app.route('/me')
def me():
    return render_template('me.html')

@app.route('/checks')
def checks():
    allErrors = {}
    # Retrieve all client enrollments
    allErrors["Duplicate Enrollments"] = findDuplicateEnrollments()
    print(allErrors)
    return render_template('checks.html', allErrors = allErrors)

if __name__ == '__main__':
    app.run(debug=True)

