from rest_framework import serializers
from .models import Department, Employee, Position, Payroll, PerformanceReview, Attendance


class EmployeeBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for Employee (used in nested relationships)"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = ['employee_id', 'first_name', 'last_name', 'full_name', 'email']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class PositionBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for Position (used in nested relationships)"""
    
    class Meta:
        model = Position
        fields = ['position_id', 'position_title', 'position_code', 'min_salary', 'max_salary']


class DepartmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for Department list view - no nested employees"""
    manager_details = EmployeeBasicSerializer(source='manager', read_only=True)
    employee_count = serializers.SerializerMethodField()
    position_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = [
            'department_id',
            'department_name',
            'department_code',
            'manager',
            'manager_details',
            'budget',
            'location',
            'created_date',
            'employee_count',
            'position_count'
        ]
        read_only_fields = ['department_id', 'created_date']
    
    def get_employee_count(self, obj):
        return obj.employees.count()
    
    def get_position_count(self, obj):
        return obj.positions.count()


class DepartmentSerializer(serializers.ModelSerializer):
    """Full serializer for Department detail view with nested relationships"""
    manager_details = EmployeeBasicSerializer(source='manager', read_only=True)
    employee_count = serializers.SerializerMethodField()
    position_count = serializers.SerializerMethodField()
    employees = EmployeeBasicSerializer(many=True, read_only=True)
    positions = PositionBasicSerializer(many=True, read_only=True)
    
    class Meta:
        model = Department
        fields = [
            'department_id',
            'department_name',
            'department_code',
            'manager',
            'manager_details',
            'budget',
            'location',
            'created_date',
            'employee_count',
            'position_count',
            'employees',
            'positions'
        ]
        read_only_fields = ['department_id', 'created_date']
    
    def get_employee_count(self, obj):
        return obj.employees.count()
    
    def get_position_count(self, obj):
        return obj.positions.count()
    
    def validate_department_code(self, value):
        """Ensure department code is unique"""
        if self.instance:
            # For updates, exclude current instance from uniqueness check
            if Department.objects.exclude(pk=self.instance.pk).filter(department_code=value).exists():
                raise serializers.ValidationError("A department with this code already exists.")
        else:
            # For creation, check if code already exists
            if Department.objects.filter(department_code=value).exists():
                raise serializers.ValidationError("A department with this code already exists.")
        return value
    
    def validate_manager(self, value):
        """Ensure manager is an active employee"""
        if value and value.employment_status != 'ACTIVE':
            raise serializers.ValidationError("Manager must be an active employee.")
        return value
    
    def validate_budget(self, value):
        """Ensure budget is positive"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Budget cannot be negative.")
        return value


class DepartmentCreateUpdateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating/updating departments"""
    
    class Meta:
        model = Department
        fields = [
            'department_name',
            'department_code', 
            'manager',
            'budget',
            'location'
        ]
    
    def validate_department_code(self, value):
        """Ensure department code is unique"""
        if self.instance:
            # For updates, exclude current instance from uniqueness check
            if Department.objects.exclude(pk=self.instance.pk).filter(department_code=value).exists():
                raise serializers.ValidationError("A department with this code already exists.")
        else:
            # For creation, check if code already exists
            if Department.objects.filter(department_code=value).exists():
                raise serializers.ValidationError("A department with this code already exists.")
        return value
    
    def validate_manager(self, value):
        """Ensure manager is an active employee"""
        if value and value.employment_status != 'ACTIVE':
            raise serializers.ValidationError("Manager must be an active employee.")
        return value
    
    def validate_budget(self, value):
        """Ensure budget is positive"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Budget cannot be negative.")
        return value


class DepartmentStatsSerializer(serializers.Serializer):
    """Serializer for department statistics"""
    department = DepartmentListSerializer(read_only=True)  # Use list serializer for stats too
    employee_count = serializers.IntegerField(read_only=True)
    position_count = serializers.IntegerField(read_only=True)
    avg_budget_per_employee = serializers.FloatField(read_only=True)
    total_salary_expense = serializers.FloatField(read_only=True, required=False)


# Employee Serializers

class DepartmentBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for Department (used in employee relationships)"""
    
    class Meta:
        model = Department
        fields = ['department_id', 'department_name', 'department_code', 'location']


class PositionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Position"""
    department_info = DepartmentBasicSerializer(source='department', read_only=True)
    
    class Meta:
        model = Position
        fields = [
            'position_id', 'position_title', 'position_code', 
            'department_info', 'job_description', 'min_salary', 
            'max_salary', 'required_experience'
        ]


class EmployeeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for Employee list view"""
    full_name = serializers.SerializerMethodField()
    department_info = DepartmentBasicSerializer(source='department', read_only=True)
    position_info = PositionBasicSerializer(source='position', read_only=True)
    
    class Meta:
        model = Employee
        fields = [
            'employee_id', 'employee_code', 'first_name', 'last_name', 'full_name',
            'email', 'phone', 'department_info', 'position_info', 'employment_status'
        ]
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class PayrollBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for Payroll records"""
    
    class Meta:
        model = Payroll
        fields = [
            'payroll_id', 'pay_period_start', 'pay_period_end',
            'basic_salary', 'allowances', 'deductions', 'net_salary', 'pay_date'
        ]


class PerformanceReviewBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for Performance Reviews"""
    reviewer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PerformanceReview
        fields = [
            'review_id', 'review_period_start', 'review_period_end',
            'goals_score', 'competency_score', 'overall_score',
            'reviewer_name', 'review_date'
        ]
    
    def get_reviewer_name(self, obj):
        if obj.reviewer:
            return f"{obj.reviewer.first_name} {obj.reviewer.last_name}"
        return None


class AttendanceBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for Attendance records"""
    
    class Meta:
        model = Attendance
        fields = [
            'attendance_id', 'date', 'check_in_time', 'check_out_time',
            'total_hours', 'status', 'remarks'
        ]


class EmployeeDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Employee with all related data"""
    full_name = serializers.SerializerMethodField()
    department_info = DepartmentBasicSerializer(source='department', read_only=True)
    position_info = PositionDetailSerializer(source='position', read_only=True)
    manager_info = EmployeeBasicSerializer(source='manager', read_only=True)
    recent_payrolls = serializers.SerializerMethodField()
    recent_reviews = serializers.SerializerMethodField()
    recent_attendance = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = [
            'employee_id', 'employee_code', 'first_name', 'last_name', 'full_name',
            'email', 'phone', 'date_of_birth', 'gender', 'address', 'hire_date',
            'department_info', 'position_info', 'manager_info', 'employment_status',
            'created_date', 'updated_date', 'recent_payrolls', 'recent_reviews', 'recent_attendance'
        ]
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    def get_recent_payrolls(self, obj):
        """Get last 3 payroll records"""
        recent_payrolls = Payroll.objects.filter(employee=obj).order_by('-pay_period_end')[:3]
        return PayrollBasicSerializer(recent_payrolls, many=True).data
    
    def get_recent_reviews(self, obj):
        """Get last 2 performance reviews"""
        recent_reviews = PerformanceReview.objects.filter(employee=obj).order_by('-review_date')[:2]
        return PerformanceReviewBasicSerializer(recent_reviews, many=True).data
    
    def get_recent_attendance(self, obj):
        """Get last 10 attendance records"""
        recent_attendance = Attendance.objects.filter(employee=obj).order_by('-date')[:10]
        return AttendanceBasicSerializer(recent_attendance, many=True).data


class EmployeeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating employees"""
    
    class Meta:
        model = Employee
        fields = [
            'employee_code', 'first_name', 'last_name', 'email', 'phone',
            'date_of_birth', 'gender', 'address', 'hire_date', 'department',
            'position', 'manager', 'employment_status'
        ]
    
    def validate_email(self, value):
        """Ensure email is unique"""
        if self.instance:
            if Employee.objects.exclude(pk=self.instance.pk).filter(email=value).exists():
                raise serializers.ValidationError("An employee with this email already exists.")
        else:
            if Employee.objects.filter(email=value).exists():
                raise serializers.ValidationError("An employee with this email already exists.")
        return value
    
    def validate_employee_code(self, value):
        """Ensure employee code is unique"""
        if self.instance:
            if Employee.objects.exclude(pk=self.instance.pk).filter(employee_code=value).exists():
                raise serializers.ValidationError("An employee with this code already exists.")
        else:
            if Employee.objects.filter(employee_code=value).exists():
                raise serializers.ValidationError("An employee with this code already exists.")
        return value 