# HR Analytics API

A Django REST Framework-based HR management and analytics platform. Provides CRUD operations and advanced analytics for departments and employees, including payroll, performance, and attendance insights.

## Features
- Department and Employee CRUD APIs
- Department-level analytics (financial, workforce, cost breakdown)
- Employee-level analytics (payroll, performance, attendance, career)
- Search/filter employees by name, department, status, and position
- Management command to generate realistic sample data

## Requirements
- Python 3.10+
- Django
- djangorestframework
- django-extensions
- pillow
- sqlalchemy
- faker
- dotenv
- numpy
- pandas
- seaborn
- openai

Install all dependencies:
```sh
pip install -r requirements.txt
```

## Setup
1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd HR_BackEnd
   ```
2. **Apply migrations:**
   ```sh
   cd hr_backend
   python manage.py migrate
   ```
3. **(Optional) Generate sample data:**
   This will clear all existing data and create new departments, employees, payroll, attendance, and performance records.
   ```sh
   python manage.py rebuild_hr_data --skip-confirmation
   ```
4. **Run the development server:**
   ```sh
   python manage.py runserver
   ```

## API Endpoints

### Departments
- `GET /departments/` — List all departments (lightweight)
- `POST /departments/` — Create new department
- `GET /departments/{id}/` — Department details with analytics
- `PUT /departments/{id}/` — Update department
- `PATCH /departments/{id}/` — Partial update
- `DELETE /departments/{id}/` — Delete department
- `GET /departments/{id}/employees/` — Employees in department
- `GET /departments/{id}/positions/` — Positions in department
- `GET /departments/stats/` — Basic stats for all departments
- `GET /departments/analytics_all/` — Analytics for all departments

#### Department Analytics (in detail endpoint)
- Financial metrics: average salary, total cost, cost per employee, budget utilization
- Workforce metrics: headcount, growth %, turnover %, salary data coverage
- Cost breakdown: base salary, overhead, formula
- Salary statistics: highest, lowest, median

### Employees
- `GET /employees/` — List all employees (lightweight)
- `POST /employees/` — Create new employee
- `GET /employees/{id}/` — Employee details with analytics
- `PUT /employees/{id}/` — Update employee
- `PATCH /employees/{id}/` — Partial update
- `DELETE /employees/{id}/` — Delete employee
- `GET /employees/analytics_summary/` — Analytics summary for all employees

#### Employee Search & Filtering
- `?name=` — Search by employee name (first or last)
- `?department_name=` — Search by department name
- `?department=` — Filter by department ID
- `?status=` — Filter by employment status
- `?position=` — Filter by position ID

#### Employee Analytics (in detail endpoint)
- Payroll: current salary, average, growth %, YTD earnings, stats
- Performance: latest/average scores, trend, review count
- Attendance: attendance rate, avg hours, YTD hours, late/absent counts
- Career: tenure, promotion potential, skill rating, direct reports

## Data Generation
To generate realistic sample data (departments, employees, payroll, attendance, performance):
```sh
python manage.py rebuild_hr_data --skip-confirmation
```

## Environment Variables
Create a `.env` file in the project root for any sensitive settings (not tracked by git).

## License
MIT
