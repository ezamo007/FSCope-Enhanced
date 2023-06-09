from flask import jsonify, render_template
from database import db, Client, Enrollment
import sqlalchemy
from collections import Counter

def execute_sql_query(query, params = None):
    """
    Executes the given SQL query and returns the results as a list of lists.

    Parameters:
    query (str): The SQL query to be executed.

    Returns:
    list: A list of lists representing the query results.
    """
    results = db.session.execute(sqlalchemy.text(query), params)
    return [list(result) for result in results]

def create_chart_object(counter):
    """
    Creates a chart object with data from a Counter object.

    Parameters:
    counter (Counter): The Counter object containing the data.

    Returns:
    dict: A dictionary with the chart labels and chart data.
          - chart_labels (list): A list of labels for the chart.
          - chart_data (list): A list of data points for the chart.
    """
    chart_labels = []
    chart_data = []

    for label, count in counter.items():
        chart_labels.append(label)
        chart_data.append(count)
    
    return {"chart_labels": chart_labels, "chart_data": chart_data}


def count_active_enrollments():
    """
    Retrieves details on active enrollments.
    Prints the results for now.
    """
    # SQL Query for Active Enrollments
    query = """
    SELECT c.client_name, e.program_name, e.entry_date, e.exit_date
    FROM Enrollment e
    JOIN Client c ON e.client_id = c.client_id
    WHERE e.exit_date IS NULL AND e.hoh = "Yes";
    """

    # Execute the SQL query
    results = execute_sql_query(query)
    counter = Counter(item[1] for item in results)
    #TODO: Add details.
    return counter



def count_active_enrollments(programName, month):
    """
    Retrieves details on active enrollments.
    Prints the results for now.
    """
    # SQL Query for Active Enrollments
    query = """
    SELECT c.client_name, e.program_name, e.entry_date, e.exit_date
    FROM Enrollment e
    JOIN Client c ON e.client_id = c.client_id
    WHERE e.exit_date IS NULL AND e.hoh = "Yes";
    """


    # Execute the SQL query
    results = execute_sql_query(query)
    counter = Counter(item[1] for item in results)
    #TODO: Add details.
    return counter


def get_program_metrics():
    listOfPrograms = execute_sql_query("""
    SELECT Distinct e.program_name
    FROM Enrollment e
    """)

    fiscalYear = [
    "2022-07", "2022-08", "2022-09", "2022-10", "2022-11", "2022-12",
    "2023-01", "2023-02", "2023-03", "2023-04", "2023-05", "2023-06"]

    monthlyProgramSizes = {}
    for [program] in listOfPrograms:
        monthlyProgramSizes[program] = []   
        for month in fiscalYear:
            month_pattern = f"{month}%"
            count = execute_sql_query("""
                SELECT COUNT(*)
                FROM Enrollment e
                WHERE  (e.entry_date <= :month OR  e.entry_date LIKE :month_pattern) and (e.exit_date IS NULL OR e.exit_date >= :month OR e.exit_date LIKE :month_pattern) AND e.hoh = "Yes" AND e.program_name LIKE :program;
                """, {"month": month, "program": program, "month_pattern":month_pattern})
            monthlyProgramSizes[program].extend(count[0])

    return {"month_list": fiscalYear, "monthlyProgramSizes": monthlyProgramSizes}
