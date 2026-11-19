import os
import pandas as pd

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
os.makedirs(SAMPLE_DIR, exist_ok=True)

# Sample messy employee dataset
data = [
    # Valid or safely repairable records
    {"Employee_ID": "EMP-1001", "Name": "Alice Walker", "Department": "Engineering", "Salary": 85000, "Join_Date": "2021-04-15", "Age": 29, "Email": "alice.w@company.com"},
    {"Employee_ID": "EMP-1002", "Name": "  Bob  Smith  ", "Department": "Marketing", "Salary": 62000, "Join_Date": "12/05/2020", "Age": 34, "Email": "bob.smith@company.com"}, # Whitespace & date format -> Safe Repair!
    {"Employee_ID": "EMP-1003", "Name": "Charlie Davis", "Department": "Finance", "Salary": 91000, "Join_Date": "2019/11/01", "Age": 41, "Email": "charlie.d@company.com"}, # Date format -> Safe Repair!
    {"Employee_ID": "EMP-1004", "Name": "Diana Prince ", "Department": "Engineering", "Salary": 105000, "Join_Date": "2018-08-20", "Age": 32, "Email": "diana.p@company.com"}, # Whitespace -> Safe Repair!

    # RED Records requiring Human Intervention
    {"Employee_ID": "EMP-1005", "Name": "Evan Wright", "Department": "Sales", "Salary": None, "Join_Date": "2022-01-10", "Age": 28, "Email": "evan.w@company.com"}, # Missing salary -> RED!
    {"Employee_ID": None, "Name": "Fiona Gallagher", "Department": "HR", "Salary": 54000, "Join_Date": "2023-03-01", "Age": 26, "Email": "fiona.g@company.com"}, # Missing identifier -> RED!
    {"Employee_ID": "EMP-1007", "Name": "George Clark", "Department": "Operations", "Salary": -45000, "Join_Date": "2020-09-14", "Age": 38, "Email": "george.c@company.com"}, # Negative salary -> RED!
    {"Employee_ID": "EMP-1008", "Name": "Hannah Abbott", "Department": "Finance", "Salary": 78000, "Join_Date": "2022-02-31", "Age": 30, "Email": "hannah.a@company.com"}, # Invalid calendar date (Feb 31) -> RED!
    {"Employee_ID": "EMP-1009", "Name": "Ian Malcolm", "Department": "Research", "Salary": 95000, "Join_Date": "2017-06-12", "Age": -5, "Email": "ian.m@company.com"}, # Negative age -> RED!
    {"Employee_ID": "EMP-1010", "Name": "Julia Roberts", "Department": "Legal", "Salary": 115000, "Join_Date": "2016-10-05", "Age": 45, "Email": "julia.roberts-company"}, # Corrupted email -> RED!

    # Candidate Duplicate Records -> RED!
    {"Employee_ID": "EMP-1011", "Name": "Kevin Bacon", "Department": "Marketing", "Salary": 60000, "Join_Date": "2021-07-22", "Age": 33, "Email": "kevin.b@company.com"},
    {"Employee_ID": "EMP-1011", "Name": "Kevin Bacon", "Department": "Marketing", "Salary": 60000, "Join_Date": "2021-07-22", "Age": 33, "Email": "kevin.b@company.com"}, # Exact duplicate -> RED!
]

df = pd.DataFrame(data)

# Export to CSV
csv_path = os.path.join(SAMPLE_DIR, "sample_employees.csv")
df.to_csv(csv_path, index=False)

# Export to Excel (.xlsx)
xlsx_path = os.path.join(SAMPLE_DIR, "sample_employees.xlsx")
df.to_excel(xlsx_path, index=False)

print(f"Generated sample datasets:\n- {csv_path}\n- {xlsx_path}")
