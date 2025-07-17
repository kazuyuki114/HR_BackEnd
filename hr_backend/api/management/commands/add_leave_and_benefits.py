from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker
import random
from datetime import datetime, timedelta, date

from api.models import Employee, LeaveRequest, EmployeeBenefit

fake = Faker()

class Command(BaseCommand):
    help = 'Add leave requests and employee benefits to the HR database'
    
    # Leave types available
    LEAVE_TYPES = [
        'ANNUAL', 'SICK', 'MATERNITY', 'PATERNITY', 'UNPAID', 'EMERGENCY'
    ]
    
    # Benefit types and their details
    BENEFIT_TYPES = [
        {
            'type': 'Health Insurance',
            'name': 'Comprehensive Health Plan',
            'provider': 'VPBank Health Services',
            'coverage_amount': 50000.00,
            'employee_contribution': 200.00,
            'company_contribution': 800.00
        },
        {
            'type': 'Life Insurance',
            'name': 'Group Life Insurance',
            'provider': 'VPBank Life Insurance Co.',
            'coverage_amount': 100000.00,
            'employee_contribution': 50.00,
            'company_contribution': 150.00
        },
        {
            'type': 'Retirement Plan',
            'name': '401(k) Retirement Savings Plan',
            'provider': 'VPBank Retirement Services',
            'coverage_amount': 0.00,
            'employee_contribution': 500.00,
            'company_contribution': 750.00
        },
        {
            'type': 'Dental Insurance',
            'name': 'Dental Care Plan',
            'provider': 'DentalCare Plus',
            'coverage_amount': 5000.00,
            'employee_contribution': 75.00,
            'company_contribution': 125.00
        },
        {
            'type': 'Vision Insurance',
            'name': 'Vision Care Plan',
            'provider': 'VisionCare Pro',
            'coverage_amount': 2000.00,
            'employee_contribution': 25.00,
            'company_contribution': 50.00
        },
        {
            'type': 'Disability Insurance',
            'name': 'Short & Long Term Disability',
            'provider': 'DisabilityCare Inc.',
            'coverage_amount': 75000.00,
            'employee_contribution': 100.00,
            'company_contribution': 200.00
        }
    ]
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--leave-only',
            action='store_true',
            help='Only add leave requests, skip benefits',
        )
        parser.add_argument(
            '--benefits-only',
            action='store_true',
            help='Only add benefits, skip leave requests',
        )
        parser.add_argument(
            '--skip-confirmation',
            action='store_true',
            help='Skip confirmation prompt',
        )
    
    def handle(self, *args, **options):
        if not options['skip_confirmation']:
            confirm = input(
                "This will add leave requests and employee benefits to the database. "
                "Continue? Type 'yes' to proceed: "
            )
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return
        
        with transaction.atomic():
            self.stdout.write("Starting to add leave requests and benefits...")
            
            # Get all employees
            employees = list(Employee.objects.all())
            if not employees:
                self.stdout.write(self.style.ERROR('No employees found in database!'))
                return
            
            leave_count = 0
            benefit_count = 0
            
            # Add leave requests unless --benefits-only is specified
            if not options['benefits_only']:
                leave_count = self.create_leave_requests(employees)
            
            # Add benefits unless --leave-only is specified
            if not options['leave_only']:
                benefit_count = self.create_employee_benefits(employees)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully added {leave_count} leave requests and {benefit_count} benefits!'
                )
            )
            
            # Show statistics
            self.show_statistics()
    
    def create_leave_requests(self, employees):
        """Create leave requests for employees"""
        self.stdout.write("Creating leave requests...")
        
        active_employees = [emp for emp in employees if emp.employment_status == 'ACTIVE']
        inactive_employees = [emp for emp in employees if emp.employment_status == 'INACTIVE']
        
        leave_requests = []
        leave_id_counter = LeaveRequest.objects.count() + 1
        
        # Add leave requests for active employees (mix of approved, pending, rejected)
        for employee in active_employees[:50]:  # First 50 active employees
            # Random leave type
            leave_type = random.choice(self.LEAVE_TYPES)
            
            # Random dates in the past year
            start_date = date.today() - timedelta(days=random.randint(1, 365))
            days_requested = random.randint(1, 14)
            end_date = start_date + timedelta(days=days_requested - 1)
            
            # Random status for active employees (mostly approved or pending)
            status = random.choices(['Approved', 'Pending', 'Rejected'], weights=[70, 20, 10])[0]
            
            # Get approver (manager or random active employee)
            approver = employee.manager if employee.manager else random.choice(active_employees)
            approved_date = start_date - timedelta(days=random.randint(1, 30)) if status == 'Approved' else None
            
            leave_request = LeaveRequest(
                leave_id=leave_id_counter,
                employee=employee,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                days_requested=days_requested,
                reason=f"Personal {leave_type.lower()} request",
                status=status,
                approved_by=approver if status == 'Approved' else None,
                approved_date=approved_date,
                created_date=timezone.now() - timedelta(days=random.randint(1, 30))
            )
            leave_requests.append(leave_request)
            leave_id_counter += 1
        
        # Add leave requests for inactive employees (these will be approved since they're no longer active)
        for employee in inactive_employees[:20]:  # First 20 inactive employees
            # Create leave requests that were approved before they became inactive
            leave_type = random.choice(self.LEAVE_TYPES)
            
            # Leave dates in the past (before they became inactive)
            start_date = date.today() - timedelta(days=random.randint(30, 200))
            days_requested = random.randint(5, 30)  # Longer leave periods
            end_date = start_date + timedelta(days=days_requested - 1)
            
            # All leave requests for inactive employees are approved
            status = 'Approved'
            
            # Get approver
            approver = random.choice(active_employees) if active_employees else None
            approved_date = start_date - timedelta(days=random.randint(1, 15))
            
            leave_request = LeaveRequest(
                leave_id=leave_id_counter,
                employee=employee,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                days_requested=days_requested,
                reason=f"Extended {leave_type.lower()} - employee later became inactive",
                status=status,
                approved_by=approver if approver else None,
                approved_date=approved_date,
                created_date=timezone.now() - timedelta(days=random.randint(40, 220))
            )
            leave_requests.append(leave_request)
            leave_id_counter += 1
        
        # Bulk create leave requests
        LeaveRequest.objects.bulk_create(leave_requests)
        self.stdout.write(f"✓ Created {len(leave_requests)} leave requests")
        return len(leave_requests)
    
    def create_employee_benefits(self, employees):
        """Create employee benefits"""
        self.stdout.write("Creating employee benefits...")
        
        # Get all active employees
        active_employees = [emp for emp in employees if emp.employment_status == 'ACTIVE']
        
        benefits = []
        benefit_id_counter = EmployeeBenefit.objects.count() + 1
        
        for employee in active_employees:
            # Each employee gets 3-5 random benefits
            num_benefits = random.randint(3, 5)
            selected_benefits = random.sample(self.BENEFIT_TYPES, num_benefits)
            
            for benefit_info in selected_benefits:
                # Random start date (within the last 2 years)
                start_date = date.today() - timedelta(days=random.randint(1, 730))
                
                # Some benefits might have end dates (10% chance)
                end_date = None
                is_active = True
                if random.random() < 0.1:
                    end_date = start_date + timedelta(days=random.randint(365, 1095))
                    is_active = end_date > date.today()
                
                # Add some variation to contribution amounts
                employee_contribution = benefit_info['employee_contribution'] * random.uniform(0.8, 1.2)
                company_contribution = benefit_info['company_contribution'] * random.uniform(0.9, 1.1)
                coverage_amount = benefit_info['coverage_amount'] * random.uniform(0.9, 1.1) if benefit_info['coverage_amount'] > 0 else 0
                
                benefit = EmployeeBenefit(
                    benefit_id=benefit_id_counter,
                    employee=employee,
                    benefit_type=benefit_info['type'],
                    benefit_name=benefit_info['name'],
                    provider=benefit_info['provider'],
                    coverage_amount=round(coverage_amount, 2),
                    employee_contribution=round(employee_contribution, 2),
                    company_contribution=round(company_contribution, 2),
                    start_date=start_date,
                    end_date=end_date,
                    is_active=is_active,
                    created_date=timezone.now() - timedelta(days=random.randint(1, 30))
                )
                benefits.append(benefit)
                benefit_id_counter += 1
        
        # Bulk create benefits
        EmployeeBenefit.objects.bulk_create(benefits)
        self.stdout.write(f"✓ Created {len(benefits)} employee benefits")
        return len(benefits)
    
    def show_statistics(self):
        """Show statistics about the data added"""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("DATABASE STATISTICS:")
        self.stdout.write("=" * 50)
        
        # Leave Request Statistics
        total_leaves = LeaveRequest.objects.count()
        approved_leaves = LeaveRequest.objects.filter(status='Approved').count()
        pending_leaves = LeaveRequest.objects.filter(status='Pending').count()
        rejected_leaves = LeaveRequest.objects.filter(status='Rejected').count()
        
        self.stdout.write(f"Leave Requests: {total_leaves}")
        self.stdout.write(f"  - Approved: {approved_leaves}")
        self.stdout.write(f"  - Pending: {pending_leaves}")
        self.stdout.write(f"  - Rejected: {rejected_leaves}")
        
        # Leave requests by employee status
        active_employee_leaves = LeaveRequest.objects.filter(employee__employment_status='ACTIVE').count()
        inactive_employee_leaves = LeaveRequest.objects.filter(employee__employment_status='INACTIVE').count()
        
        self.stdout.write(f"  - For active employees: {active_employee_leaves}")
        self.stdout.write(f"  - For inactive employees: {inactive_employee_leaves}")
        
        # Benefit Statistics
        total_benefits = EmployeeBenefit.objects.count()
        active_benefits = EmployeeBenefit.objects.filter(is_active=True).count()
        inactive_benefits = EmployeeBenefit.objects.filter(is_active=False).count()
        
        self.stdout.write(f"\nEmployee Benefits: {total_benefits}")
        self.stdout.write(f"  - Active benefits: {active_benefits}")
        self.stdout.write(f"  - Inactive benefits: {inactive_benefits}")
        
        # Benefit types breakdown
        benefit_types = EmployeeBenefit.objects.values('benefit_type').distinct().count()
        self.stdout.write(f"  - Benefit types available: {benefit_types}") 