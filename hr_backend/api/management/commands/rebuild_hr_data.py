from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker
import random
from datetime import datetime, timedelta
from decimal import Decimal

from api.models import (
    Department, Employee, Position, Attendance, 
    Payroll, PerformanceReview, TrainingRecord
)

fake = Faker()

class Command(BaseCommand):
    help = 'Rebuild HR database with new employee data based on department structure'
    
    # Department data with employee counts
    DEPARTMENT_DATA = {
        'Compliance': {'code': 'COM', 'employee_count': 110, 'budget': 400000.0, 'location': 'Floor 1'},
        'Coporate': {'code': 'COP', 'employee_count': 38, 'budget': 350000.0, 'location': 'Floor 4'},
        'Finance & Accounting': {'code': 'FIN', 'employee_count': 76, 'budget': 800000.0, 'location': 'Floor 2'},
        'Human Resources': {'code': 'HR', 'employee_count': 64, 'budget': 500000.0, 'location': 'Floor 1'},
        'Information Technology': {'code': 'IT', 'employee_count': 78, 'budget': 1200000.0, 'location': 'Floor 5'},
        'Operations': {'code': 'OPS', 'employee_count': 40, 'budget': 700000.0, 'location': 'Floor 4'},
        'Retail Banking': {'code': 'RB', 'employee_count': 390, 'budget': 800000.0, 'location': 'Floor 1'},
        'Risk Management': {'code': 'RM', 'employee_count': 40, 'budget': 1000000.0, 'location': 'Floor 6'},
        'Transformation Office': {'code': 'TO', 'employee_count': 40, 'budget': 300000.0, 'location': 'Floor 2'},
        'Treasury & Markets': {'code': 'TM', 'employee_count': 90, 'budget': 450000.0, 'location': 'Floor 5'},
    }
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-confirmation',
            action='store_true',
            help='Skip confirmation prompt',
        )
    
    def handle(self, *args, **options):
        if not options['skip_confirmation']:
            confirm = input(
                "This will DELETE ALL existing employees, attendance, payroll, and performance data. "
                "Are you sure? Type 'yes' to continue: "
            )
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return
        
        with transaction.atomic():
            self.stdout.write("Starting database rebuild...")
            
            # Step 1: Clear existing data
            self.clear_existing_data()
            
            # Step 2: Create employees for each department
            employees = self.create_employees()
            
            # Step 3: Create 1000 attendance records
            self.create_attendance_records(employees)
            
            # Step 4: Create payroll records for each employee
            self.create_payroll_records(employees)
            
            # Step 5: Create performance reviews for each employee
            self.create_performance_reviews(employees)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully rebuilt HR database with {len(employees)} employees!'
                )
            )
    
    def clear_existing_data(self):
        """Clear existing employee-related data"""
        self.stdout.write("Clearing existing data...")
        
        # Clear in order to respect foreign key constraints
        TrainingRecord.objects.all().delete()
        PerformanceReview.objects.all().delete()
        Payroll.objects.all().delete()
        Attendance.objects.all().delete()
        Employee.objects.all().delete()
        
        self.stdout.write("✓ Cleared existing data")
    
    def create_employees(self):
        """Create employees for each department according to specified counts"""
        self.stdout.write("Creating employees...")
        
        employees = []
        employee_id_counter = 1
        
        for dept_name, dept_info in self.DEPARTMENT_DATA.items():
            try:
                department = Department.objects.get(department_name=dept_name)
            except Department.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Department '{dept_name}' not found, skipping...")
                )
                continue
            
            # Get positions for this department
            positions = list(department.positions.all())
            if not positions:
                self.stdout.write(
                    self.style.WARNING(f"No positions found for '{dept_name}', skipping...")
                )
                continue
            
            # Create employees for this department
            for i in range(dept_info['employee_count']):
                employee = self.create_single_employee(
                    employee_id_counter, department, positions
                )
                employees.append(employee)
                employee_id_counter += 1
            
            self.stdout.write(f"✓ Created {dept_info['employee_count']} employees for {dept_name}")
        
        return employees
    
    def create_single_employee(self, emp_id, department, positions):
        """Create a single employee"""
        position = random.choice(positions)
        
        # Generate employee data
        gender = random.choice(['MALE', 'FEMALE'])
        first_name = fake.first_name_male() if gender == 'MALE' else fake.first_name_female()
        last_name = fake.last_name()
        
        # Create unique email by adding employee ID to ensure no duplicates
        email = f"{first_name.lower()}.{last_name.lower()}.{emp_id}@company.com"
        
        employee = Employee.objects.create(
            employee_id=emp_id,
            employee_code=f"EMP{emp_id:04d}",
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=fake.phone_number()[:20],
            date_of_birth=fake.date_of_birth(minimum_age=22, maximum_age=65),
            gender=gender,
            address=fake.address(),
            hire_date=fake.date_between(start_date='-5y', end_date='today'),
            department=department,
            position=position,
            employment_status=random.choice(['ACTIVE', 'ACTIVE', 'ACTIVE', 'ACTIVE', 'ON_LEAVE']),  # 80% active
            created_date=timezone.now(),
            updated_date=timezone.now()
        )
        
        return employee
    
    def create_attendance_records(self, employees):
        """Create 1000 attendance records"""
        self.stdout.write("Creating 1000 attendance records...")
        
        attendance_records = []
        for i in range(1000):
            employee = random.choice(employees)
            attendance_date = fake.date_between(start_date='-6m', end_date='today')
            
            # Generate realistic datetime for check-in (8-10 AM)
            check_in_hour = random.randint(8, 10)
            check_in_minute = random.randint(0, 59)
            check_in_datetime = timezone.make_aware(
                datetime.combine(attendance_date, datetime.min.time().replace(
                    hour=check_in_hour, minute=check_in_minute
                ))
            )
            
            # Generate check-out time (7-10 hours later)
            work_hours = random.uniform(7, 10)
            check_out_datetime = check_in_datetime + timedelta(hours=work_hours)
            
            # Calculate total hours
            total_hours = (check_out_datetime - check_in_datetime).total_seconds() / 3600
            
            attendance = Attendance(
                attendance_id=i + 1,
                employee=employee,
                date=attendance_date,
                check_in_time=check_in_datetime,
                check_out_time=check_out_datetime,
                total_hours=round(total_hours, 2),
                status=random.choice(['PRESENT', 'PRESENT', 'PRESENT', 'LATE', 'ABSENT']),  # Mostly present
                remarks=random.choice([None, 'On time', 'Late arrival', 'Early departure']),
                created_date=timezone.now()
            )
            attendance_records.append(attendance)
        
        Attendance.objects.bulk_create(attendance_records)
        self.stdout.write("✓ Created 1000 attendance records")
    
    def create_payroll_records(self, employees):
        """Create payroll records for each employee"""
        self.stdout.write(f"Creating payroll records for {len(employees)} employees...")
        
        payroll_records = []
        payroll_id_counter = 1
        
        # Create 3 months of payroll for each employee
        for month_offset in [0, 1, 2]:
            pay_date = timezone.now().date().replace(day=1) - timedelta(days=30 * month_offset)
            
            for employee in employees:
                # Base salary based on position salary range
                if employee.position and employee.position.min_salary and employee.position.max_salary:
                    base_salary = random.uniform(employee.position.min_salary, employee.position.max_salary)
                else:
                    base_salary = random.uniform(30000, 100000)  # Default range
                
                # Calculate components
                basic_salary = base_salary * 0.7
                allowances = base_salary * 0.2
                overtime_hours = random.uniform(0, 20)  # 0-20 overtime hours
                overtime_rate = 1.5 * (basic_salary / 160)  # 1.5x hourly rate (160 hours/month)
                deductions = base_salary * random.uniform(0.05, 0.15)  # 5-15% deductions
                tax_deduction = basic_salary * random.uniform(0.10, 0.20)  # 10-20% tax
                
                # Calculate net salary
                total_overtime = overtime_hours * overtime_rate
                gross_salary = basic_salary + allowances + total_overtime
                total_deductions = deductions + tax_deduction
                net_salary = gross_salary - total_deductions
                
                payroll = Payroll(
                    payroll_id=payroll_id_counter,
                    employee=employee,
                    pay_period_start=pay_date,
                    pay_period_end=pay_date.replace(day=28),  # End of month
                    basic_salary=round(basic_salary, 2),
                    overtime_hours=round(overtime_hours, 2),
                    overtime_rate=round(overtime_rate, 2),
                    allowances=round(allowances, 2),
                    deductions=round(deductions, 2),
                    tax_deduction=round(tax_deduction, 2),
                    net_salary=round(net_salary, 2),
                    pay_date=pay_date,
                    created_date=timezone.now()
                )
                payroll_records.append(payroll)
                payroll_id_counter += 1
        
        Payroll.objects.bulk_create(payroll_records)
        self.stdout.write(f"✓ Created {len(payroll_records)} payroll records")
    
    def create_performance_reviews(self, employees):
        """Create performance reviews for each employee"""
        self.stdout.write(f"Creating performance reviews for {len(employees)} employees...")
        
        review_records = []
        review_id_counter = 1
        
        # Create annual reviews for each employee
        for employee in employees:
            # Annual review
            review_date = fake.date_between(start_date='-1y', end_date='today')
            
            # Generate scores (1-5 scale)
            goals_score = round(random.uniform(2.0, 5.0), 1)
            competency_score = round(random.uniform(2.0, 5.0), 1)
            overall_score = round((goals_score + competency_score) / 2, 1)
            
            # Select a reviewer (could be manager or senior employee)
            possible_reviewers = [emp for emp in employees if emp != employee]
            reviewer = random.choice(possible_reviewers) if possible_reviewers else employee
            
            review = PerformanceReview(
                review_id=review_id_counter,
                employee=employee,
                reviewer=reviewer,
                review_period_start=review_date - timedelta(days=365),
                review_period_end=review_date,
                goals_score=goals_score,
                competency_score=competency_score,
                overall_score=overall_score,
                strengths=fake.text(max_nb_chars=200),
                areas_for_improvement=fake.text(max_nb_chars=150),
                development_plan=fake.text(max_nb_chars=200),
                comments=fake.text(max_nb_chars=200),
                review_date=review_date,
                created_date=timezone.now()
            )
            review_records.append(review)
            review_id_counter += 1
        
        PerformanceReview.objects.bulk_create(review_records)
        self.stdout.write(f"✓ Created {len(review_records)} performance reviews") 