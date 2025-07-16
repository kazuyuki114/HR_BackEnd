from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Float, Boolean, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum
import os

Base = declarative_base()

class GenderEnum(enum.Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"

class EmploymentStatusEnum(enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    TERMINATED = "Terminated"
    ON_LEAVE = "On Leave"

class LeaveTypeEnum(enum.Enum):
    ANNUAL = "Annual Leave"
    SICK = "Sick Leave"
    MATERNITY = "Maternity Leave"
    PATERNITY = "Paternity Leave"
    UNPAID = "Unpaid Leave"

class AttendanceStatusEnum(enum.Enum):
    PRESENT = "Present"
    ABSENT = "Absent"
    LATE = "Late"
    HALF_DAY = "Half Day"

# 1. Departments Table
class Department(Base):
    __tablename__ = 'departments'
    
    department_id = Column(Integer, primary_key=True, autoincrement=True)
    department_name = Column(String(100), nullable=False, unique=True)
    department_code = Column(String(10), nullable=False, unique=True)
    manager_id = Column(Integer, ForeignKey('employees.employee_id'))
    budget = Column(Float)
    location = Column(String(100))
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    employees = relationship("Employee", foreign_keys="Employee.department_id", back_populates="department")
    manager = relationship("Employee", foreign_keys=[manager_id])

# 2. Positions/Job Titles Table
class Position(Base):
    __tablename__ = 'positions'
    
    position_id = Column(Integer, primary_key=True, autoincrement=True)
    position_title = Column(String(100), nullable=False)
    position_code = Column(String(20), nullable=False, unique=True)
    department_id = Column(Integer, ForeignKey('departments.department_id'))
    job_description = Column(Text)
    min_salary = Column(Float)
    max_salary = Column(Float)
    required_experience = Column(Integer)  # years
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    department = relationship("Department")
    employees = relationship("Employee", back_populates="position")

# 3. Employees Table
class Employee(Base):
    __tablename__ = 'employees'
    
    employee_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_code = Column(String(20), nullable=False, unique=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    phone = Column(String(20))
    date_of_birth = Column(Date)
    gender = Column(Enum(GenderEnum))
    address = Column(Text)
    hire_date = Column(Date, nullable=False)
    department_id = Column(Integer, ForeignKey('departments.department_id'))
    position_id = Column(Integer, ForeignKey('positions.position_id'))
    manager_id = Column(Integer, ForeignKey('employees.employee_id'))
    employment_status = Column(Enum(EmploymentStatusEnum), default=EmploymentStatusEnum.ACTIVE)
    created_date = Column(DateTime, default=datetime.utcnow)
    updated_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    department = relationship("Department", foreign_keys=[department_id], back_populates="employees")
    position = relationship("Position", back_populates="employees")
    manager = relationship("Employee", remote_side=[employee_id], foreign_keys=[manager_id])
    subordinates = relationship("Employee", foreign_keys=[manager_id], overlaps="manager")
    attendance_records = relationship("Attendance", back_populates="employee")
    leave_requests = relationship("LeaveRequest", foreign_keys="LeaveRequest.employee_id", back_populates="employee")
    payroll_records = relationship("Payroll", back_populates="employee")
    performance_reviews = relationship("PerformanceReview", foreign_keys="PerformanceReview.employee_id", back_populates="employee")
    training_records = relationship("TrainingRecord", back_populates="employee")

# 4. Attendance Table
class Attendance(Base):
    __tablename__ = 'attendance'
    
    attendance_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employees.employee_id'), nullable=False)
    date = Column(Date, nullable=False)
    check_in_time = Column(DateTime)
    check_out_time = Column(DateTime)
    total_hours = Column(Float)
    status = Column(Enum(AttendanceStatusEnum), default=AttendanceStatusEnum.PRESENT)
    remarks = Column(String(200))
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", back_populates="attendance_records")

# 5. Leave Requests Table
class LeaveRequest(Base):
    __tablename__ = 'leave_requests'
    
    leave_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employees.employee_id'), nullable=False)
    leave_type = Column(Enum(LeaveTypeEnum), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days_requested = Column(Integer, nullable=False)
    reason = Column(Text)
    status = Column(String(20), default='Pending')  # Pending, Approved, Rejected
    approved_by = Column(Integer, ForeignKey('employees.employee_id'))
    approved_date = Column(DateTime)
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id], back_populates="leave_requests")
    approver = relationship("Employee", foreign_keys=[approved_by])

# 6. Payroll Table
class Payroll(Base):
    __tablename__ = 'payroll'
    
    payroll_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employees.employee_id'), nullable=False)
    pay_period_start = Column(Date, nullable=False)
    pay_period_end = Column(Date, nullable=False)
    basic_salary = Column(Float, nullable=False)
    overtime_hours = Column(Float, default=0)
    overtime_rate = Column(Float, default=0)
    allowances = Column(Float, default=0)
    deductions = Column(Float, default=0)
    tax_deduction = Column(Float, default=0)
    net_salary = Column(Float, nullable=False)
    pay_date = Column(Date)
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", back_populates="payroll_records")

# 7. Performance Reviews Table
class PerformanceReview(Base):
    __tablename__ = 'performance_reviews'
    
    review_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employees.employee_id'), nullable=False)
    reviewer_id = Column(Integer, ForeignKey('employees.employee_id'), nullable=False)
    review_period_start = Column(Date, nullable=False)
    review_period_end = Column(Date, nullable=False)
    goals_score = Column(Float)  # 1-5 scale
    competency_score = Column(Float)  # 1-5 scale
    overall_score = Column(Float)  # 1-5 scale
    strengths = Column(Text)
    areas_for_improvement = Column(Text)
    development_plan = Column(Text)
    comments = Column(Text)
    review_date = Column(Date, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id], back_populates="performance_reviews")
    reviewer = relationship("Employee", foreign_keys=[reviewer_id])

# 8. Training Programs Table
class TrainingProgram(Base):
    __tablename__ = 'training_programs'
    
    program_id = Column(Integer, primary_key=True, autoincrement=True)
    program_name = Column(String(100), nullable=False)
    program_code = Column(String(20), nullable=False, unique=True)
    description = Column(Text)
    duration_hours = Column(Integer)
    trainer_name = Column(String(100))
    cost = Column(Float)
    max_participants = Column(Integer)
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    training_records = relationship("TrainingRecord", back_populates="program")

# 9. Training Records Table
class TrainingRecord(Base):
    __tablename__ = 'training_records'
    
    record_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employees.employee_id'), nullable=False)
    program_id = Column(Integer, ForeignKey('training_programs.program_id'), nullable=False)
    enrollment_date = Column(Date, nullable=False)
    start_date = Column(Date)
    completion_date = Column(Date)
    status = Column(String(20), default='Enrolled')  # Enrolled, In Progress, Completed, Cancelled
    score = Column(Float)
    certification_earned = Column(Boolean, default=False)
    comments = Column(Text)
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", back_populates="training_records")
    program = relationship("TrainingProgram", back_populates="training_records")

# 10. Employee Benefits Table
class EmployeeBenefit(Base):
    __tablename__ = 'employee_benefits'
    
    benefit_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employees.employee_id'), nullable=False)
    benefit_type = Column(String(50), nullable=False)  # Health Insurance, Life Insurance, Retirement Plan, etc.
    benefit_name = Column(String(100), nullable=False)
    provider = Column(String(100))
    coverage_amount = Column(Float)
    employee_contribution = Column(Float)
    company_contribution = Column(Float)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    is_active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee")

# Database setup
def connect_to_existing_database(database_url=None):
    """Connect to existing database"""
    if database_url is None:
        # Get path relative to this file  
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, "..", "..", "hr_database.db")
        database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url)
    return engine

def get_session(engine):
    """Get database session"""
    Session = sessionmaker(bind=engine)
    return Session()

def load_existing_data(session):
    """Load and display existing data from the database"""
    print("Loading existing HR data...")
    print("=" * 50)
    
    # Load departments
    departments = session.query(Department).all()
    print(f"Departments ({len(departments)}):")
    for dept in departments[:5]:  # Show first 5
        print(f"  - {dept.department_name} ({dept.department_code}) - Budget: ${dept.budget:,.2f}" if dept.budget else f"  - {dept.department_name} ({dept.department_code})")
    if len(departments) > 5:
        print(f"  ... and {len(departments) - 5} more")
    print()
    
    # Load positions
    positions = session.query(Position).all()
    print(f"Positions ({len(positions)}):")
    for pos in positions[:5]:  # Show first 5
        salary_range = f"${pos.min_salary:,.0f} - ${pos.max_salary:,.0f}" if pos.min_salary and pos.max_salary else "N/A"
        print(f"  - {pos.position_title} ({pos.position_code}) - Salary: {salary_range}")
    if len(positions) > 5:
        print(f"  ... and {len(positions) - 5} more")
    print()
    
    # Load employees
    employees = session.query(Employee).all()
    print(f"Employees ({len(employees)}):")
    for emp in employees[:5]:  # Show first 5
        dept_name = emp.department.department_name if emp.department else "No Department"
        pos_name = emp.position.position_title if emp.position else "No Position"
        print(f"  - {emp.first_name} {emp.last_name} ({emp.employee_code}) - {dept_name}, {pos_name}")
    if len(employees) > 5:
        print(f"  ... and {len(employees) - 5} more")
    print()
    
    # Load other tables counts
    attendance_count = session.query(Attendance).count()
    leave_count = session.query(LeaveRequest).count()
    payroll_count = session.query(Payroll).count()
    review_count = session.query(PerformanceReview).count()
    training_programs_count = session.query(TrainingProgram).count()
    training_records_count = session.query(TrainingRecord).count()
    benefits_count = session.query(EmployeeBenefit).count()
    
    print("Other Records:")
    print(f"  - Attendance Records: {attendance_count}")
    print(f"  - Leave Requests: {leave_count}")
    print(f"  - Payroll Records: {payroll_count}")
    print(f"  - Performance Reviews: {review_count}")
    print(f"  - Training Programs: {training_programs_count}")
    print(f"  - Training Records: {training_records_count}")
    print(f"  - Employee Benefits: {benefits_count}")
    
    return {
        'departments': len(departments),
        'positions': len(positions),
        'employees': len(employees),
        'attendance': attendance_count,
        'leave_requests': leave_count,
        'payroll': payroll_count,
        'reviews': review_count,
        'training_programs': training_programs_count,
        'training_records': training_records_count,
        'benefits': benefits_count
    }

def get_database_summary(session):
    """Get a summary of the database contents"""
    summary = {
        'departments': session.query(Department).count(),
        'positions': session.query(Position).count(),
        'employees': session.query(Employee).count(),
        'attendance': session.query(Attendance).count(),
        'leave_requests': session.query(LeaveRequest).count(),
        'payroll': session.query(Payroll).count(),
        'reviews': session.query(PerformanceReview).count(),
        'training_programs': session.query(TrainingProgram).count(),
        'training_records': session.query(TrainingRecord).count(),
        'benefits': session.query(EmployeeBenefit).count()
    }
    return summary

if __name__ == "__main__":
    # Connect to existing database
    engine = connect_to_existing_database()
    session = get_session(engine)
    
    try:
        # Load and display existing data
        data_summary = load_existing_data(session)
        print("\n" + "=" * 50)
        print("HR Database connection successful!")
        print(f"Total records: {sum(data_summary.values())}")
    except Exception as e:
        print(f"Error connecting to database: {e}")
    finally:
        session.close()
