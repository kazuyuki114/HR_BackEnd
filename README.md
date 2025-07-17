# HR Backend API - Comprehensive Guide

A sophisticated Django REST Framework-based Human Resources management system providing comprehensive APIs for managing employees, departments, payroll, attendance, performance reviews, training programs, and benefits.

## 🚀 Quick Start

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt
```

### Setup & Run
```bash
# Navigate to project directory
cd hr_backend

# Run database migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

**API Base URL**: `http://localhost:8000/api/`

## 📚 Complete API Reference

### 🏢 Department Management APIs

#### 1. List All Departments
```http
GET /api/departments/
```

**Query Parameters:**
- `name` (string): Filter by department name (case-insensitive)
- `location` (string): Filter by location (case-insensitive)

**Response:**
```json
[
    {
        "department_id": 1,
        "department_name": "Information Technology",
        "department_code": "IT",
        "manager": 15,
        "manager_details": {
            "employee_id": 15,
            "first_name": "John",
            "last_name": "Smith",
            "full_name": "John Smith",
            "email": "john.smith@vpbank.com"
        },
        "budget": 500000.0,
        "location": "Head Office",
        "created_date": "2024-01-15T10:30:00Z",
        "employee_count": 78,
        "position_count": 12
    }
]
```

**Example Requests:**
```bash
# Get all departments
curl http://localhost:8000/api/departments/

# Filter by name
curl "http://localhost:8000/api/departments/?name=IT"

# Filter by location
curl "http://localhost:8000/api/departments/?location=Head Office"
```

#### 2. Get Department Details with Analytics
```http
GET /api/departments/{id}/
```

**Response includes comprehensive analytics:**
```json
{
    "department_id": 1,
    "department_name": "Information Technology",
    "department_code": "IT",
    "manager_details": { ... },
    "budget": 500000.0,
    "location": "Head Office",
    "employee_count": 78,
    "position_count": 12,
    "employees": [ ... ],
    "positions": [ ... ],
    "analytics": {
        "financial_metrics": {
            "average_salary": 85000.0,
            "total_salary_cost": 6630000.0,
            "total_cost": 9945000.0,
            "cost_per_employee": 127500.0,
            "budget_utilization_percent": 132.6
        },
        "workforce_metrics": {
            "total_employees": 78,
            "employees_with_salary_data": 78,
            "salary_data_coverage_percent": 100.0,
            "headcount_growth_percent": 12.5,
            "turnover_rate_percent": 8.3
        },
        "cost_breakdown": {
            "base_salary_cost": 6630000.0,
            "overhead_multiplier": 1.5,
            "overhead_cost": 3315000.0,
            "cost_formula": "Total Cost = (Sum of all salaries) × 1.5"
        },
        "salary_statistics": {
            "highest_salary": 150000.0,
            "lowest_salary": 45000.0,
            "median_salary": 82000.0
        }
    }
}
```

#### 3. Get Department Employees
```http
GET /api/departments/{id}/employees/
```

Returns all employees in the specified department with basic information.

#### 4. Get Department Positions  
```http
GET /api/departments/{id}/positions/
```

Returns all available positions in the department.

#### 5. Company-Wide Department Analytics
```http
GET /api/departments/analytics_all/
```

**Comprehensive analytics for all departments:**
```json
{
    "departments_analytics": [
        {
            "department": { ... },
            "financial_metrics": {
                "average_salary": 85000.0,
                "total_cost": 9945000.0,
                "cost_per_employee": 127500.0
            },
            "workforce_metrics": {
                "total_employees": 78,
                "headcount_growth_percent": 12.5,
                "turnover_rate_percent": 8.3
            }
        }
    ],
    "company_summary": {
        "total_departments_analyzed": 10,
        "total_company_cost": 45678000.0,
        "total_employees": 966,
        "average_cost_per_employee": 47280.0,
        "cost_breakdown_by_department": [
            {
                "department": "Retail Banking",
                "cost": 19500000.0,
                "percentage_of_total": 42.7
            }
        ]
    }
}
```

#### 6. Department Statistics
```http
GET /api/departments/stats/
```

Basic statistics summary for all departments including employee counts and budget analysis.

### 👥 Employee Management APIs

#### 1. List Employees with Search
```http
GET /api/employees/
```

**Query Parameters:**
- `name` (string): Search by first name, last name, or full name (case-insensitive, supports partial matches)
- `department` (integer): Filter by department ID

**Response:**
```json
[
    {
        "employee_id": 1,
        "employee_code": "EMP001",
        "first_name": "Jane",
        "last_name": "Doe", 
        "full_name": "Jane Doe",
        "email": "jane.doe@vpbank.com",
        "phone": "+1-555-0123",
        "department_info": {
            "department_id": 1,
            "department_name": "Information Technology",
            "department_code": "IT",
            "location": "Head Office"
        },
        "position_info": {
            "position_id": 3,
            "position_title": "Senior Software Engineer",
            "position_code": "SSE001",
            "min_salary": 80000.0,
            "max_salary": 130000.0
        },
        "employment_status": "ACTIVE"
    }
]
```

**Search Examples:**
```bash
# Search by first name
curl "http://localhost:8000/api/employees/?name=John"

# Search by last name
curl "http://localhost:8000/api/employees/?name=Smith"

# Search by full name
curl "http://localhost:8000/api/employees/?name=John Smith"

# Partial name search
curl "http://localhost:8000/api/employees/?name=Joh"

# Filter by department
curl "http://localhost:8000/api/employees/?department=1"

# Combined search
curl "http://localhost:8000/api/employees/?name=John&department=1"
```

#### 2. Get Employee Details with Comprehensive Analytics
```http
GET /api/employees/{id}/
```

**Response includes complete employee profile:**
```json
{
    "employee_id": 1,
    "employee_code": "EMP001",
    "first_name": "Jane",
    "last_name": "Doe",
    "full_name": "Jane Doe",
    "email": "jane.doe@vpbank.com",
    "phone": "+1-555-0123",
    "date_of_birth": "1990-05-15",
    "gender": "FEMALE",
    "address": "123 Main St, City, State 12345",
    "hire_date": "2022-03-01",
    "department_info": { ... },
    "position_info": { ... },
    "manager_info": { ... },
    "employment_status": "ACTIVE",
    "recent_payrolls": [ ... ],
    "recent_reviews": [ ... ],
    "recent_attendance": [ ... ],
    "analytics": {
        "payroll": {
            "current_salary": 95000.0,
            "average_salary": 87500.0,
            "salary_growth_percent": 8.7,
            "total_earnings_ytd": 71250.0,
            "highest_salary": 95000.0,
            "lowest_salary": 80000.0,
            "payroll_records_count": 24
        },
        "performance": {
            "latest_overall_score": 4.2,
            "average_overall_score": 4.0,
            "average_goals_score": 4.1,
            "average_competency_score": 3.9,
            "performance_trend": "Improving",
            "reviews_count": 3,
            "highest_score": 4.2,
            "lowest_score": 3.7
        },
        "attendance": {
            "attendance_rate_percent": 97.5,
            "average_hours_per_day": 8.2,
            "total_hours_ytd": 1476.0,
            "total_days_recorded": 180,
            "present_days": 175,
            "late_days": 3,
            "absent_days": 2
        },
        "career": {
            "tenure_years": 2.4,
            "tenure_days": 876,
            "promotion_potential_percent": 87.3,
            "skill_rating": 4.2,
            "employment_status": "ACTIVE",
            "has_direct_reports": true,
            "direct_reports_count": 3
        }
    }
}
```

#### 3. Employee Analytics Summary
```http
GET /api/employees/analytics_summary/
```

Organization-wide employee analytics:
```json
{
    "summary": {
        "total_employees": 966,
        "active_employees": 920,
        "inactive_employees": 46,
        "average_tenure_years": 3.2
    },
    "department_distribution": [
        {
            "department__department_name": "Retail Banking",
            "count": 390
        },
        {
            "department__department_name": "Compliance",
            "count": 110
        }
    ],
    "employment_status_breakdown": [
        {
            "employment_status": "ACTIVE",
            "count": 920
        },
        {
            "employment_status": "INACTIVE", 
            "count": 46
        }
    ]
}
```

## 📊 Data Models Reference

### Core Models

#### Department
```python
{
    "department_id": Integer (Primary Key),
    "department_name": String (max 100 chars),
    "department_code": String (max 10 chars, unique),
    "manager": ForeignKey (Employee),
    "budget": Float,
    "location": String (max 100 chars),
    "created_date": DateTime
}
```

#### Employee
```python
{
    "employee_id": Integer (Primary Key),
    "employee_code": String (max 20 chars, unique),
    "first_name": String (max 50 chars),
    "last_name": String (max 50 chars), 
    "email": Email (unique),
    "phone": String (max 20 chars),
    "date_of_birth": Date,
    "gender": Choice ["MALE", "FEMALE", "OTHER"],
    "address": Text,
    "hire_date": Date (required),
    "department": ForeignKey (Department),
    "position": ForeignKey (Position),
    "manager": ForeignKey (Employee, self-referential),
    "employment_status": Choice ["ACTIVE", "INACTIVE", "ON_LEAVE", "TERMINATED"],
    "created_date": DateTime,
    "updated_date": DateTime
}
```

#### Position
```python
{
    "position_id": Integer (Primary Key),
    "position_title": String (max 100 chars),
    "position_code": String (max 20 chars, unique),
    "department": ForeignKey (Department),
    "job_description": Text,
    "min_salary": Float,
    "max_salary": Float,
    "required_experience": Integer (years),
    "created_date": DateTime
}
```

### Supporting Models

#### Payroll
- Pay period tracking
- Salary components (basic, overtime, allowances, deductions)
- Tax calculations and net salary
- Payment dates

#### PerformanceReview  
- Review periods and scoring (1-5 scale)
- Goals, competency, and overall scores
- Feedback and development plans
- Reviewer assignments

#### Attendance
- Daily attendance tracking
- Check-in/out times and total hours
- Status: PRESENT, ABSENT, LATE, HALF_DAY
- Remarks and notes

#### LeaveRequest
- Leave types: ANNUAL, SICK, MATERNITY, PATERNITY, UNPAID, EMERGENCY
- Date ranges and approval workflow
- Status tracking: Pending, Approved, Rejected, Cancelled

#### TrainingProgram & TrainingRecord
- Training program catalog
- Employee enrollment and progress tracking
- Completion status and scoring
- Certification management

#### EmployeeBenefit
- Benefits portfolio (Health, Life, Retirement, Dental, Vision, Disability)
- Coverage amounts and contribution tracking
- Provider information and active status

## 🔍 Advanced Search Capabilities

### Employee Search Features

1. **Intelligent Name Search**
   - Searches both first and last names
   - Case-insensitive partial matching
   - Handles full name queries
   - Supports incomplete searches

2. **Department Filtering**
   - Filter employees by department ID
   - Combine with name search

3. **Search Examples**
```bash
# All variations find "John Smith"
curl "http://localhost:8000/api/employees/?name=John"
curl "http://localhost:8000/api/employees/?name=Smith"
curl "http://localhost:8000/api/employees/?name=John Smith"
curl "http://localhost:8000/api/employees/?name=joh"

# Department-specific searches
curl "http://localhost:8000/api/employees/?department=1"
curl "http://localhost:8000/api/employees/?name=John&department=1"
```

## 📈 Analytics Engine

### Automatic Calculations

#### Department Analytics
- **Financial Metrics**: 
  - Average salary calculations
  - Total cost with 50% overhead (Base Salary × 1.5)
  - Budget utilization percentages
  - Cost per employee analysis

- **Workforce Metrics**:
  - Headcount growth rates
  - Turnover rate calculations
  - Employee coverage statistics

- **Salary Statistics**:
  - Min/max/median salary analysis
  - Salary distribution insights

#### Employee Analytics
- **Payroll Analysis**: 
  - Salary growth tracking over time
  - Year-to-date earnings calculations
  - Historical salary comparisons

- **Performance Tracking**:
  - Score trends and improvements
  - Review frequency analysis
  - Performance trajectory mapping

- **Attendance Patterns**:
  - Attendance rate calculations
  - Hours tracking and averages
  - Late/absent day analysis

- **Career Progression**:
  - Tenure calculations from hire date
  - Promotion potential scoring
  - Direct reports management

## 🛠️ Management Commands

### Generate Sample Data

#### Add Leave Requests and Benefits
```bash
python manage.py add_leave_and_benefits
```

**Options:**
- `--leave-only`: Generate only leave requests
- `--benefits-only`: Generate only employee benefits  
- `--skip-confirmation`: Skip confirmation prompt

**What it generates:**
- **Leave Requests**: Realistic leave data with proper approval workflows for both active and inactive employees
- **Employee Benefits**: Comprehensive benefits packages including:
  - Health Insurance (Comprehensive Health Plan)
  - Life Insurance (Group Life Insurance) 
  - Retirement Plan (401k Savings Plan)
  - Dental Insurance (Dental Care Plan)
  - Vision Insurance (Vision Care Plan)
  - Disability Insurance (Short & Long Term)

**Example Usage:**
```bash
# Generate both leave and benefits data
python manage.py add_leave_and_benefits --skip-confirmation

# Generate only leave requests
python manage.py add_leave_and_benefits --leave-only

# Generate only benefits
python manage.py add_leave_and_benefits --benefits-only
```

## 🏗️ System Architecture

### Technology Stack
- **Backend**: Django 5.2.4
- **API Framework**: Django REST Framework
- **Database**: SQLite (development) 
- **Data Processing**: Pandas, NumPy
- **ML Libraries**: scikit-learn, XGBoost, LightGBM, Prophet
- **Visualization**: Matplotlib, Seaborn

### Key Features
✅ **Read-Only API** - Data integrity protection  
✅ **Comprehensive Analytics** - Automatic KPI calculations  
✅ **Advanced Search** - Flexible filtering and search  
✅ **Related Data** - Rich nested serializations  
✅ **Performance Optimized** - Efficient database queries  
✅ **Complete HR Ecosystem** - End-to-end HR management  
✅ **Sample Data Generation** - Built-in realistic test data  
✅ **Department Hierarchy** - Manager relationships  
✅ **Employee Lifecycle** - Complete employment tracking  

## 🌐 API Access

### Development Server
```bash
# Start server
python manage.py runserver

# Access points
API Root: http://localhost:8000/api/
Admin Panel: http://localhost:8000/admin/
API Browser: Available for all endpoints
```

### Response Formats
All endpoints return JSON with consistent structure:
- **Success**: HTTP 200 with data
- **Not Found**: HTTP 404 with error message  
- **Server Error**: HTTP 500 with error details

### CORS and Headers
Currently configured for development use. For production:
- Configure CORS settings
- Add authentication/authorization
- Set up proper security headers

## 📝 Sample Workflows

### 1. Employee Onboarding Report
```bash
# Get department overview
curl http://localhost:8000/api/departments/1/

# Find available positions
curl http://localhost:8000/api/departments/1/positions/

# Check team members
curl http://localhost:8000/api/departments/1/employees/
```

### 2. Performance Analysis
```bash
# Get employee details with performance analytics
curl http://localhost:8000/api/employees/15/

# Department-wide analytics
curl http://localhost:8000/api/departments/analytics_all/
```

### 3. HR Dashboard Data
```bash
# Company overview
curl http://localhost:8000/api/employees/analytics_summary/

# Department statistics
curl http://localhost:8000/api/departments/stats/

# Individual department deep-dive
curl http://localhost:8000/api/departments/1/
```

## 🔒 Security Considerations

### Current State (Development)
- No authentication required
- Full read access to all data
- SQLite database for development

### Production Recommendations
- Implement JWT or session-based authentication
- Add role-based access control (RBAC)
- Migrate to PostgreSQL/MySQL
- Add rate limiting
- Configure HTTPS
- Implement audit logging

## 📚 Additional Resources

### Database Schema
Full schema definition available in: `hr_backend/api/database/hr_schema.py`

### Model Definitions  
Django models: `hr_backend/api/models.py`

### API Serializers
Data serialization: `hr_backend/api/serializers.py`

### URL Configuration
Endpoint routing: `hr_backend/api/urls.py`

---

**Built with ❤️ using Django REST Framework**

For support or questions, please refer to the Django and DRF documentation or create an issue in the project repository.
