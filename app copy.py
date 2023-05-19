from flask import Flask, render_template, request
from flask_material import Material
from database import db, init_db, Household, Client, Enrollment, Service
from sqlalchemy import create_engine, or_, and_, inspect
from sqlalchemy.orm import sessionmaker, joinedload
app = Flask(__name__)
Material(app)


from jinja2 import Environment
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
def index():
    enrollments = Enrollment.query.all()
    services = Service.query.all()
    clients = Client.query.all()

    return render_template('index.html', enrollments=enrollments, services=services, clients = clients)

@app.route('/search', methods=['GET', 'POST'])
def search():
    return render_template('search.html')
from sqlalchemy.orm import aliased
@app.route('/results', methods=['POST'])
def search_results():
    # Get form data from request
    search_fields = request.form.getlist('search-field')
    search_operators = request.form.getlist('search-operator')
    search_values = request.form.getlist('search-value')
    search_logics = request.form.getlist('search-logic')

    # Build SQLAlchemy query dynamically based on form data
    print(search_fields)
    hasClient, hasEnrollment, hasService = False, False, False
    for search_field in search_fields:
        if "client" in search_field:
            hasClient = True
        elif "enrollment" in search_field:
            hasEnrollment = True
        elif "service" in search_field:
            hasService=True

    # Start with the Household table
    query = db.session.query(Household)

    # Include all columns from the tables involved in the query
    if hasClient or hasEnrollment or hasService:
        query = db.session.query(Household, Client)
    if hasEnrollment or hasService:
        query = db.session.query(Household, Client, Enrollment)
    if hasService:
        query = db.session.query(Household, Client, Enrollment, Service)

    # Join the tables based on the foreign keys
    if hasClient or hasEnrollment or hasService:
        query = query.join(Client, Household.household_id == Client.household_id)

    if hasEnrollment or hasService:
        query = query.join(Enrollment, Client.client_id == Enrollment.client_id)

    if hasService:
        query = query.join(Service, Enrollment.enrollment_id == Service.enrollment_id)

    criteria = []

    for i in range(len(search_fields)):
        objectName, field = search_fields[i].split(".")
        operator = search_operators[i]
        value = search_values[i]
        logic = search_logics[i]

        object_map = {
            'household': Household,
            'enrollment': Enrollment,
            'service': Service,
            'client': Client
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
    print("\n\n\n\n",criteria,"\n\n\n\n")   

    thing = criteria[0]
    print(thing)
    for i in range(len(search_logics)-1):
        print(search_logics[i],"LOL", criteria[i+1])
        if(search_logics[i] == "OR"):
            thing = or_(thing,criteria[i+1])
        else:
            thing = and_(thing,criteria[i+1])

    query = query.filter(thing)
 
    print(query.statement.compile(dialect=engine.dialect, compile_kwargs={"literal_binds": True}))


    # Execute query and get results
    results = query.all()
    tableHeader = []
    tableValues = []
    for row in results:
        rowValues = []
        for model_instance in row:
            model_class = type(model_instance)
            table_name = model_class.__table__.name
            model_columns = inspect(model_class).columns
            for column in model_columns:
                value = getattr(model_instance, column.name)
                if f"{table_name.title()}.{column.name}" not in tableHeader:
                    tableHeader.append(f"{table_name.title()}.{column.name}")
                rowValues.append(value)
        tableValues.append(rowValues)
    # Render the template with the query results
    print(tableHeader, tableValues)
    return render_template('results.html', results={'header' : tableHeader, 'body' : tableValues})


if __name__ == '__main__':
    app.run(debug=True)
