from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Department(models.Model):
    department_id = models.AutoField(primary_key=True)
    department_name = models.CharField(max_length=100)
    department_code = models.CharField(max_length=10, unique=True)
    manager = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments', db_column='manager_id')
    budget = models.FloatField(null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.department_name} ({self.department_code})"

    class Meta:
        db_table = 'departments'


class Position(models.Model):
    position_id = models.AutoField(primary_key=True)
    position_title = models.CharField(max_length=100)
    position_code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='positions', db_column='department_id')
    job_description = models.TextField(null=True, blank=True)
    min_salary = models.FloatField(null=True, blank=True)
    max_salary = models.FloatField(null=True, blank=True)
    required_experience = models.IntegerField(null=True, blank=True, help_text="Required experience in years")
    created_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.position_title} ({self.position_code})"

    class Meta:
        db_table = 'positions'


class Employee(models.Model):
    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
    ]
    
    EMPLOYMENT_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('ON_LEAVE', 'On Leave'),
        ('TERMINATED', 'Terminated'),
    ]

    employee_id = models.AutoField(primary_key=True)
    employee_code = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=100, unique=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    hire_date = models.DateField()
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees', db_column='department_id')
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees', db_column='position_id')
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates', db_column='manager_id')
    employment_status = models.CharField(max_length=10, choices=EMPLOYMENT_STATUS_CHOICES, null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_code})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        db_table = 'employees'


class TrainingProgram(models.Model):
    program_id = models.AutoField(primary_key=True)
    program_name = models.CharField(max_length=100)
    program_code = models.CharField(max_length=20, unique=True)
    description = models.TextField(null=True, blank=True)
    duration_hours = models.IntegerField(null=True, blank=True)
    trainer_name = models.CharField(max_length=100, null=True, blank=True)
    cost = models.FloatField(null=True, blank=True)
    max_participants = models.IntegerField(null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.program_name} ({self.program_code})"

    class Meta:
        db_table = 'training_programs'


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('HALF_DAY', 'Half Day'),
        ('LATE', 'Late'),
    ]

    attendance_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records', db_column='employee_id')
    date = models.DateField()
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    total_hours = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, null=True, blank=True)
    remarks = models.CharField(max_length=200, null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.date}"

    class Meta:
        db_table = 'attendance'


class LeaveRequest(models.Model):
    LEAVE_TYPE_CHOICES = [
        ('ANNUAL', 'Annual Leave'),
        ('SICK', 'Sick Leave'),
        ('MATERNITY', 'Maternity Leave'),
        ('PATERNITY', 'Paternity Leave'),
        ('UNPAID', 'Unpaid Leave'),
        ('EMERGENCY', 'Emergency Leave'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    ]

    leave_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests', db_column='employee_id')
    leave_type = models.CharField(max_length=9, choices=LEAVE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    days_requested = models.IntegerField()
    reason = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, null=True, blank=True)
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves', db_column='approved_by')
    approved_date = models.DateTimeField(null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type} ({self.start_date} to {self.end_date})"

    class Meta:
        db_table = 'leave_requests'


class Payroll(models.Model):
    payroll_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payroll_records', db_column='employee_id')
    pay_period_start = models.DateField()
    pay_period_end = models.DateField()
    basic_salary = models.FloatField()
    overtime_hours = models.FloatField(null=True, blank=True)
    overtime_rate = models.FloatField(null=True, blank=True)
    allowances = models.FloatField(null=True, blank=True)
    deductions = models.FloatField(null=True, blank=True)
    tax_deduction = models.FloatField(null=True, blank=True)
    net_salary = models.FloatField()
    pay_date = models.DateField(null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.pay_period_start} to {self.pay_period_end}"

    class Meta:
        db_table = 'payroll'


class PerformanceReview(models.Model):
    review_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='performance_reviews', db_column='employee_id')
    reviewer = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='conducted_reviews', db_column='reviewer_id')
    review_period_start = models.DateField()
    review_period_end = models.DateField()
    goals_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(5)])
    competency_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(5)])
    overall_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(5)])
    strengths = models.TextField(null=True, blank=True)
    areas_for_improvement = models.TextField(null=True, blank=True)
    development_plan = models.TextField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    review_date = models.DateField()
    created_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee.full_name} - Review by {self.reviewer.full_name} ({self.review_date})"

    class Meta:
        db_table = 'performance_reviews'


class TrainingRecord(models.Model):
    STATUS_CHOICES = [
        ('Enrolled', 'Enrolled'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Dropped', 'Dropped'),
        ('Failed', 'Failed'),
    ]

    record_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='training_records', db_column='employee_id')
    program = models.ForeignKey(TrainingProgram, on_delete=models.CASCADE, related_name='training_records', db_column='program_id')
    enrollment_date = models.DateField()
    start_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, null=True, blank=True)
    score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    certification_earned = models.BooleanField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.program.program_name}"

    class Meta:
        db_table = 'training_records'


class EmployeeBenefit(models.Model):
    benefit_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='benefits', db_column='employee_id')
    benefit_type = models.CharField(max_length=50)
    benefit_name = models.CharField(max_length=100)
    provider = models.CharField(max_length=100, null=True, blank=True)
    coverage_amount = models.FloatField(null=True, blank=True)
    employee_contribution = models.FloatField(null=True, blank=True)
    company_contribution = models.FloatField(null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.benefit_name}"

    class Meta:
        db_table = 'employee_benefits'
