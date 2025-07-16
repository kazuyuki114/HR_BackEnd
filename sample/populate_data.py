import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'database'))

from database.hr_schema import *
from faker import Faker
import random
from datetime import datetime, date, timedelta
import math

fake = Faker(['vi_VN', 'en_US'])  # Vietnamese and English locales

def populate_hr_data():
    """Populate HR database with realistic sample data"""
    
    # Create database and session
    engine = create_database("sqlite:///hr_database.db")
    session = get_session(engine)
    
    
    # 3. Create Employees (200 employees)
    employees = []
    employee_codes = set()
    
    for i in range(200):
        # Generate unique employee code
        while True:
            emp_code = f"EMP{random.randint(1000, 9999)}"
            if emp_code not in employee_codes:
                employee_codes.add(emp_code)
                break
        
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}@company.com"
        
        # Ensure unique email
        email_counter = 1
        original_email = email
        while any(emp.email == email for emp in employees):
            email = f"{original_email.split('@')[0]}{email_counter}@company.com"
            email_counter += 1
        
        hire_date = fake.date_between(start_date='-10y', end_date='today')
        
        emp = Employee(
            employee_code=emp_code,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=fake.phone_number()[:20],
            date_of_birth=fake.date_of_birth(minimum_age=22, maximum_age=65),
            gender=random.choice(list(GenderEnum)),
            address=fake.address(),
            hire_date=hire_date,
            department_id=random.randint(1, 10),
            position_id=random.randint(1, 30),
            employment_status=random.choice(list(EmploymentStatusEnum))
        )
        employees.append(emp)
    
    session.add_all(employees)
    session.commit()
    print(f"Created {len(employees)} employees")
    
    # Update managers for employees
    for i, emp in enumerate(employees):
        if i % 10 != 0:  # 10% of employees don't have managers (top level)
            potential_managers = [e for e in employees if e.department_id == emp.department_id and e.employee_id != emp.employee_id]
            if potential_managers:
                emp.manager_id = random.choice(potential_managers).employee_id
    
    session.commit()
    
    
    # 5. Create Attendance Records 
    attendance_records = []
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    for _ in range(1000):
        emp_id = random.randint(1, 200)
        attendance_date = fake.date_between(start_date=start_date, end_date=end_date)
        
        check_in = fake.time_object()
        check_out_time = datetime.combine(attendance_date, check_in) + timedelta(hours=random.randint(7, 10))
        total_hours = (check_out_time - datetime.combine(attendance_date, check_in)).total_seconds() / 3600
        
        att = Attendance(
            employee_id=emp_id,
            date=attendance_date,
            check_in_time=datetime.combine(attendance_date, check_in),
            check_out_time=check_out_time,
            total_hours=round(total_hours, 2),
            status=random.choice(list(AttendanceStatusEnum)),
            remarks=fake.sentence() if random.random() < 0.3 else None
        )
        attendance_records.append(att)
    
    session.add_all(attendance_records)
    session.commit()
    print(f"Created {len(attendance_records)} attendance records")
    
    
    # 7. Create Payroll Records (400 records)
    payroll_records = []
    for _ in range(400):
        emp_id = random.randint(1, 200)
        period_start = fake.date_between(start_date='-2y', end_date='today')
        period_end = period_start + timedelta(days=30)
        
        basic_sal = random.randint(35000, 150000)
        overtime_hrs = random.uniform(0, 20)
        overtime_rate = basic_sal / 2080 * 1.5  # 1.5x hourly rate
        allowances = random.uniform(0, 5000)
        deductions = random.uniform(0, 2000)
        tax = basic_sal * random.uniform(0.15, 0.35)
        net_sal = basic_sal + (overtime_hrs * overtime_rate) + allowances - deductions - tax
        
        payroll = Payroll(
            employee_id=emp_id,
            pay_period_start=period_start,
            pay_period_end=period_end,
            basic_salary=basic_sal,
            overtime_hours=round(overtime_hrs, 2),
            overtime_rate=round(overtime_rate, 2),
            allowances=round(allowances, 2),
            deductions=round(deductions, 2),
            tax_deduction=round(tax, 2),
            net_salary=round(net_sal, 2),
            pay_date=period_end + timedelta(days=5)
        )
        payroll_records.append(payroll)
    
    session.add_all(payroll_records)
    session.commit()
    print(f"Created {len(payroll_records)} payroll records")
    
    # 8. Create Performance Reviews (150 reviews)
    performance_reviews = []
    for _ in range(150):
        emp_id = random.randint(1, 200)
        reviewer_id = random.randint(1, 200)
        review_start = fake.date_between(start_date='-2y', end_date='-6m')
        review_end = review_start + timedelta(days=365)
        
        review = PerformanceReview(
            employee_id=emp_id,
            reviewer_id=reviewer_id,
            review_period_start=review_start,
            review_period_end=review_end,
            goals_score=round(random.uniform(1.0, 5.0), 2),
            competency_score=round(random.uniform(1.0, 5.0), 2),
            overall_score=round(random.uniform(1.0, 5.0), 2),
            strengths=fake.text(max_nb_chars=200),
            areas_for_improvement=fake.text(max_nb_chars=200),
            development_plan=fake.text(max_nb_chars=300),
            comments=fake.text(max_nb_chars=250),
            review_date=review_end + timedelta(days=30)
        )
        performance_reviews.append(review)
    
    session.add_all(performance_reviews)
    session.commit()
    print(f"Created {len(performance_reviews)} performance reviews")
    
    # 9. Create Training Records (250 records)
    training_records = []
    for _ in range(250):
        emp_id = random.randint(1, 200)
        prog_id = random.randint(1, 20)
        enroll_date = fake.date_between(start_date='-2y', end_date='today')
        
        record = TrainingRecord(
            employee_id=emp_id,
            program_id=prog_id,
            enrollment_date=enroll_date,
            start_date=enroll_date + timedelta(days=random.randint(1, 30)),
            completion_date=enroll_date + timedelta(days=random.randint(31, 90)) if random.random() < 0.8 else None,
            status=random.choice(['Enrolled', 'In Progress', 'Completed', 'Cancelled']),
            score=round(random.uniform(60, 100), 2) if random.random() < 0.7 else None,
            certification_earned=random.choice([True, False]),
            comments=fake.sentence() if random.random() < 0.4 else None
        )
        training_records.append(record)
    
    session.add_all(training_records)
    session.commit()
    print(f"Created {len(training_records)} training records")
    
    
    session.close()
    print("\n=== Data Population Complete ===")
    print("Total records created:")
    print(f"- Departments: 10")
    print(f"- Positions: 30")
    print(f"- Employees: 200")
    print(f"- Training Programs: 20")
    print(f"- Attendance Records: 300")
    print(f"- Leave Requests: 100")
    print(f"- Payroll Records: 400")
    print(f"- Performance Reviews: 150")
    print(f"- Training Records: 250")
    print(f"- Employee Benefits: 300")
    print(f"Total: 1,760 records")

if __name__ == "__main__":
    populate_hr_data()
