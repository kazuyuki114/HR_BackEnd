from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.db.models import Count, Sum, Avg, Q
from .models import Department, Employee, Payroll, PerformanceReview, Attendance
import random
from datetime import datetime, timedelta
from .serializers import (
    DepartmentSerializer, 
    DepartmentListSerializer,
    DepartmentCreateUpdateSerializer,
    DepartmentStatsSerializer,
    EmployeeBasicSerializer,
    EmployeeListSerializer,
    EmployeeDetailSerializer,
    EmployeeCreateUpdateSerializer,
    PayrollBasicSerializer,
    PerformanceReviewBasicSerializer,
    AttendanceBasicSerializer
)


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Department read-only operations
    Provides: list, retrieve
    """
    queryset = Department.objects.select_related('manager').prefetch_related('positions', 'employees')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DepartmentListSerializer
        return DepartmentSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Get department details with analytics data"""
        department = self.get_object()
        
        # Get base department data
        serializer = self.get_serializer(department)
        response_data = serializer.data
        
        # Get all employees in the department
        employees = Employee.objects.filter(department=department)
        employee_count = employees.count()
        
        if employee_count > 0:
            # Get salary data from payroll records (latest records for each employee)
            latest_payrolls = []
            total_salary = 0
            salary_count = 0
            
            for employee in employees:
                # Get the most recent payroll record for each employee
                latest_payroll = Payroll.objects.filter(employee=employee).order_by('-pay_period_end').first()
                if latest_payroll:
                    latest_payrolls.append(latest_payroll)
                    total_salary += latest_payroll.net_salary
                    salary_count += 1
            
            # Calculate metrics
            avg_salary = round(total_salary / salary_count, 2) if salary_count > 0 else 0
            total_cost = round(total_salary * 1.5, 2)  # Total cost = all salaries * 1.5
            cost_per_employee = round(total_cost / employee_count, 2) if employee_count > 0 else 0
            
            # Generate random KPIs (as requested)
            headcount_growth = round(random.uniform(-5.0, 15.0), 2)  # -5% to +15% growth
            turnover_rate = round(random.uniform(2.0, 20.0), 2)  # 2% to 20% turnover
            
            # Additional calculated metrics
            salary_coverage = round((salary_count / employee_count) * 100, 2) if employee_count > 0 else 0
            budget_utilization = round((total_cost / department.budget) * 100, 2) if department.budget else 0
            
            # Add analytics data to response
            response_data['analytics'] = {
                'financial_metrics': {
                    'average_salary': avg_salary,
                    'total_salary_cost': round(total_salary, 2),
                    'total_cost': total_cost,
                    'cost_per_employee': cost_per_employee,
                    'budget_utilization_percent': budget_utilization
                },
                'workforce_metrics': {
                    'total_employees': employee_count,
                    'employees_with_salary_data': salary_count,
                    'salary_data_coverage_percent': salary_coverage,
                    'headcount_growth_percent': headcount_growth,
                    'turnover_rate_percent': turnover_rate
                },
                'cost_breakdown': {
                    'base_salary_cost': round(total_salary, 2),
                    'overhead_multiplier': 1.5,
                    'overhead_cost': round(total_salary * 0.5, 2),
                    'cost_formula': 'Total Cost = (Sum of all salaries) × 1.5'
                },
                'salary_statistics': {
                    'highest_salary': round(max([p.net_salary for p in latest_payrolls]), 2) if latest_payrolls else 0,
                    'lowest_salary': round(min([p.net_salary for p in latest_payrolls]), 2) if latest_payrolls else 0,
                    'median_salary': round(sorted([p.net_salary for p in latest_payrolls])[len(latest_payrolls)//2], 2) if latest_payrolls else 0
                }
            }
        else:
            response_data['analytics'] = {
                'error': 'No employees found in this department',
                'financial_metrics': {
                    'average_salary': 0,
                    'total_cost': 0,
                    'cost_per_employee': 0
                },
                'workforce_metrics': {
                    'total_employees': 0,
                    'headcount_growth_percent': 0,
                    'turnover_rate_percent': 0
                }
            }
        
        return Response(response_data)
    
    def get_queryset(self):
        # Optimize queryset based on action
        if self.action == 'list':
            # For list view, we don't need to prefetch employees - just count them
            queryset = Department.objects.select_related('manager').prefetch_related('positions')
        else:
            # For detail view, prefetch employees for full data
            queryset = Department.objects.select_related('manager').prefetch_related('positions', 'employees')
        
        # Optional filtering
        department_name = self.request.query_params.get('name', None)
        if department_name is not None:
            queryset = queryset.filter(department_name__icontains=department_name)
        
        location = self.request.query_params.get('location', None)
        if location is not None:
            queryset = queryset.filter(location__icontains=location)
            
        return queryset.order_by('department_name')
    
    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """Get all employees in this department"""
        department = self.get_object()
        employees = Employee.objects.filter(department=department).order_by('last_name', 'first_name')
        serializer = EmployeeBasicSerializer(employees, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def positions(self, request, pk=None):
        """Get all positions in this department"""
        department = self.get_object()
        positions = department.positions.all().order_by('position_title')
        from .serializers import PositionBasicSerializer
        serializer = PositionBasicSerializer(positions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get detailed analytics for a specific department"""
        department = self.get_object()
        
        # Get all employees in the department
        employees = Employee.objects.filter(department=department)
        employee_count = employees.count()
        
        if employee_count == 0:
            return Response({
                'error': 'No employees found in this department',
                'department': DepartmentListSerializer(department).data
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get salary data from payroll records (latest records for each employee)
        latest_payrolls = []
        total_salary = 0
        salary_count = 0
        
        for employee in employees:
            # Get the most recent payroll record for each employee
            latest_payroll = Payroll.objects.filter(employee=employee).order_by('-pay_period_end').first()
            if latest_payroll:
                latest_payrolls.append(latest_payroll)
                total_salary += latest_payroll.net_salary
                salary_count += 1
        
        # Calculate metrics
        avg_salary = round(total_salary / salary_count, 2) if salary_count > 0 else 0
        total_cost = round(total_salary * 1.5, 2)  # Total cost = all salaries * 1.5
        cost_per_employee = round(total_cost / employee_count, 2) if employee_count > 0 else 0
        
        # Generate random KPIs (as requested)
        headcount_growth = round(random.uniform(-5.0, 15.0), 2)  # -5% to +15% growth
        turnover_rate = round(random.uniform(2.0, 20.0), 2)  # 2% to 20% turnover
        
        # Additional calculated metrics
        salary_coverage = round((salary_count / employee_count) * 100, 2) if employee_count > 0 else 0
        budget_utilization = round((total_cost / department.budget) * 100, 2) if department.budget else 0
        
        return Response({
            'department': DepartmentListSerializer(department).data,
            'financial_metrics': {
                'average_salary': avg_salary,
                'total_salary_cost': round(total_salary, 2),
                'total_cost': total_cost,
                'cost_per_employee': cost_per_employee,
                'budget_utilization_percent': budget_utilization
            },
            'workforce_metrics': {
                'total_employees': employee_count,
                'employees_with_salary_data': salary_count,
                'salary_data_coverage_percent': salary_coverage,
                'headcount_growth_percent': headcount_growth,
                'turnover_rate_percent': turnover_rate
            },
            'cost_breakdown': {
                'base_salary_cost': round(total_salary, 2),
                'overhead_multiplier': 1.5,
                'overhead_cost': round(total_salary * 0.5, 2),
                'cost_formula': 'Total Cost = (Sum of all salaries) × 1.5'
            },
            'salary_statistics': {
                'highest_salary': round(max([p.net_salary for p in latest_payrolls]), 2) if latest_payrolls else 0,
                'lowest_salary': round(min([p.net_salary for p in latest_payrolls]), 2) if latest_payrolls else 0,
                'median_salary': round(sorted([p.net_salary for p in latest_payrolls])[len(latest_payrolls)//2], 2) if latest_payrolls else 0
            }
        })
    
    @action(detail=False, methods=['get'])
    def analytics_all(self, request):
        """Get detailed analytics for all departments"""
        departments = self.get_queryset()
        
        analytics_data = []
        total_company_cost = 0
        total_company_employees = 0
        
        for dept in departments:
            # Get all employees in the department
            employees = Employee.objects.filter(department=dept)
            employee_count = employees.count()
            
            if employee_count == 0:
                continue
            
            # Get salary data from payroll records (latest records for each employee)
            latest_payrolls = []
            total_salary = 0
            salary_count = 0
            
            for employee in employees:
                latest_payroll = Payroll.objects.filter(employee=employee).order_by('-pay_period_end').first()
                if latest_payroll:
                    latest_payrolls.append(latest_payroll)
                    total_salary += latest_payroll.net_salary
                    salary_count += 1
            
            # Calculate metrics
            avg_salary = round(total_salary / salary_count, 2) if salary_count > 0 else 0
            total_cost = round(total_salary * 1.5, 2)
            cost_per_employee = round(total_cost / employee_count, 2) if employee_count > 0 else 0
            
            # Random KPIs
            headcount_growth = round(random.uniform(-5.0, 15.0), 2)
            turnover_rate = round(random.uniform(2.0, 20.0), 2)
            
            total_company_cost += total_cost
            total_company_employees += employee_count
            
            analytics_data.append({
                'department': DepartmentListSerializer(dept).data,
                'financial_metrics': {
                    'average_salary': avg_salary,
                    'total_cost': total_cost,
                    'cost_per_employee': cost_per_employee
                },
                'workforce_metrics': {
                    'total_employees': employee_count,
                    'headcount_growth_percent': headcount_growth,
                    'turnover_rate_percent': turnover_rate
                }
            })
        
        return Response({
            'departments_analytics': analytics_data,
            'company_summary': {
                'total_departments_analyzed': len(analytics_data),
                'total_company_cost': round(total_company_cost, 2),
                'total_employees': total_company_employees,
                'average_cost_per_employee': round(total_company_cost / total_company_employees, 2) if total_company_employees > 0 else 0,
                'cost_breakdown_by_department': [
                    {
                        'department': dept['department']['department_name'],
                        'cost': dept['financial_metrics']['total_cost'],
                        'percentage_of_total': round((dept['financial_metrics']['total_cost'] / total_company_cost) * 100, 2) if total_company_cost > 0 else 0
                    }
                    for dept in analytics_data
                ]
            }
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get statistics for all departments"""
        departments = self.get_queryset()
        
        stats_data = []
        total_employees = 0
        total_budget = 0
        
        for dept in departments:
            employee_count = Employee.objects.filter(department=dept).count()
            position_count = dept.positions.count()
            avg_budget_per_employee = dept.budget / employee_count if dept.budget and employee_count > 0 else 0
            
            stats_data.append({
                'department': DepartmentListSerializer(dept).data,
                'employee_count': employee_count,
                'position_count': position_count,
                'avg_budget_per_employee': round(avg_budget_per_employee, 2)
            })
            
            total_employees += employee_count
            if dept.budget:
                total_budget += dept.budget
        
        return Response({
            'department_stats': stats_data,
            'summary': {
                'total_departments': len(stats_data),
                'total_employees': total_employees,
                'total_budget': round(total_budget, 2),
                'avg_employees_per_department': round(total_employees / len(stats_data), 2) if stats_data else 0
            }
        })


# Employee Views

class EmployeeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Employee read-only operations
    Provides: list, retrieve
    """
    queryset = Employee.objects.select_related('department', 'position', 'manager').all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeListSerializer
        return EmployeeDetailSerializer
    
    def get_queryset(self):
        queryset = Employee.objects.select_related('department', 'position', 'manager')
        
        # Search by name (searches both first_name and last_name)
        name = self.request.query_params.get('name', None)
        if name is not None:
            queryset = queryset.filter(
                Q(first_name__icontains=name) | 
                Q(last_name__icontains=name) |
                Q(first_name__icontains=name.split()[0] if ' ' in name else name) |
                Q(last_name__icontains=name.split()[-1] if ' ' in name else name)
            )
        
        # Filter by department ID
        department_id = self.request.query_params.get('department', None)
        if department_id is not None:
            queryset = queryset.filter(department_id=department_id)
            
        return queryset.order_by('last_name', 'first_name')
    
    def retrieve(self, request, *args, **kwargs):
        """Get employee details with comprehensive analytics"""
        employee = self.get_object()
        
        # Get base employee data
        serializer = self.get_serializer(employee)
        response_data = serializer.data
        
        # Calculate analytics
        analytics = self.calculate_employee_analytics(employee)
        response_data['analytics'] = analytics
        
        return Response(response_data)
    
    def calculate_employee_analytics(self, employee):
        """Calculate comprehensive analytics for an employee"""
        
        # Payroll Analytics
        payrolls = Payroll.objects.filter(employee=employee).order_by('-pay_period_end')
        payroll_analytics = self.get_payroll_analytics(payrolls)
        
        # Performance Analytics
        reviews = PerformanceReview.objects.filter(employee=employee).order_by('-review_date')
        performance_analytics = self.get_performance_analytics(reviews)
        
        # Attendance Analytics
        attendance_records = Attendance.objects.filter(employee=employee).order_by('-date')
        attendance_analytics = self.get_attendance_analytics(attendance_records)
        
        # Career Analytics
        career_analytics = self.get_career_analytics(employee)
        
        return {
            'payroll': payroll_analytics,
            'performance': performance_analytics,
            'attendance': attendance_analytics,
            'career': career_analytics
        }
    
    def get_payroll_analytics(self, payrolls):
        """Calculate payroll-related analytics"""
        if not payrolls:
            return {
                'current_salary': 0,
                'average_salary': 0,
                'salary_growth': 0,
                'total_earnings_ytd': 0,
                'highest_salary': 0,
                'lowest_salary': 0
            }
        
        current_salary = payrolls[0].net_salary if payrolls else 0
        salaries = [p.net_salary for p in payrolls]
        
        # Calculate year-to-date earnings (current year)
        current_year = datetime.now().year
        ytd_payrolls = [p for p in payrolls if p.pay_period_start.year == current_year]
        total_earnings_ytd = sum([p.net_salary for p in ytd_payrolls])
        
        # Calculate salary growth (compare latest vs 6 months ago)
        six_months_ago = datetime.now() - timedelta(days=180)
        older_payrolls = [p for p in payrolls if p.pay_period_start <= six_months_ago.date()]
        
        salary_growth = 0
        if older_payrolls and payrolls:
            old_salary = older_payrolls[0].net_salary
            salary_growth = round(((current_salary - old_salary) / old_salary) * 100, 2) if old_salary > 0 else 0
        
        return {
            'current_salary': round(current_salary, 2),
            'average_salary': round(sum(salaries) / len(salaries), 2) if salaries else 0,
            'salary_growth_percent': salary_growth,
            'total_earnings_ytd': round(total_earnings_ytd, 2),
            'highest_salary': round(max(salaries), 2) if salaries else 0,
            'lowest_salary': round(min(salaries), 2) if salaries else 0,
            'payroll_records_count': len(payrolls)
        }
    
    def get_performance_analytics(self, reviews):
        """Calculate performance-related analytics"""
        if not reviews:
            return {
                'latest_overall_score': 0,
                'average_overall_score': 0,
                'performance_trend': 'No data',
                'reviews_count': 0
            }
        
        overall_scores = [r.overall_score for r in reviews if r.overall_score]
        goals_scores = [r.goals_score for r in reviews if r.goals_score]
        competency_scores = [r.competency_score for r in reviews if r.competency_score]
        
        # Calculate trend
        trend = 'Stable'
        if len(overall_scores) >= 2:
            latest_score = overall_scores[0]
            previous_score = overall_scores[1]
            if latest_score > previous_score:
                trend = 'Improving'
            elif latest_score < previous_score:
                trend = 'Declining'
        
        return {
            'latest_overall_score': overall_scores[0] if overall_scores else 0,
            'average_overall_score': round(sum(overall_scores) / len(overall_scores), 2) if overall_scores else 0,
            'average_goals_score': round(sum(goals_scores) / len(goals_scores), 2) if goals_scores else 0,
            'average_competency_score': round(sum(competency_scores) / len(competency_scores), 2) if competency_scores else 0,
            'performance_trend': trend,
            'reviews_count': len(reviews),
            'highest_score': round(max(overall_scores), 2) if overall_scores else 0,
            'lowest_score': round(min(overall_scores), 2) if overall_scores else 0
        }
    
    def get_attendance_analytics(self, attendance_records):
        """Calculate attendance-related analytics"""
        if not attendance_records:
            return {
                'attendance_rate': 0,
                'average_hours_per_day': 0,
                'total_hours_ytd': 0,
                'late_days_count': 0,
                'absent_days_count': 0
            }
        
        # Filter current year records
        current_year = datetime.now().year
        current_year_records = [a for a in attendance_records if a.date.year == current_year]
        
        # Calculate metrics
        total_records = len(current_year_records)
        present_records = [a for a in current_year_records if a.status == 'PRESENT']
        late_records = [a for a in current_year_records if a.status == 'LATE']
        absent_records = [a for a in current_year_records if a.status == 'ABSENT']
        
        attendance_rate = (len(present_records) + len(late_records)) / total_records * 100 if total_records > 0 else 0
        
        # Calculate average hours
        hours_records = [a for a in current_year_records if a.total_hours]
        avg_hours = sum([a.total_hours for a in hours_records]) / len(hours_records) if hours_records else 0
        total_hours_ytd = sum([a.total_hours for a in hours_records])
        
        return {
            'attendance_rate_percent': round(attendance_rate, 2),
            'average_hours_per_day': round(avg_hours, 2),
            'total_hours_ytd': round(total_hours_ytd, 2),
            'total_days_recorded': total_records,
            'present_days': len(present_records),
            'late_days': len(late_records),
            'absent_days': len(absent_records)
        }
    
    def get_career_analytics(self, employee):
        """Calculate career-related analytics"""
        # Calculate tenure
        tenure_days = (datetime.now().date() - employee.hire_date).days
        tenure_years = round(tenure_days / 365.25, 1)
        
        # Generate some random but realistic career metrics
        promotion_potential = round(random.uniform(60, 95), 2)  # 60-95% potential
        skill_rating = round(random.uniform(3.0, 5.0), 1)  # 3-5 rating
        
        return {
            'tenure_years': tenure_years,
            'tenure_days': tenure_days,
            'promotion_potential_percent': promotion_potential,
            'skill_rating': skill_rating,
            'employment_status': employee.employment_status,
            'has_direct_reports': Employee.objects.filter(manager=employee).exists(),
            'direct_reports_count': Employee.objects.filter(manager=employee).count()
        }
    
    @action(detail=False, methods=['get'])
    def analytics_summary(self, request):
        """Get analytics summary for all employees"""
        employees = self.get_queryset()
        
        # Basic counts
        total_employees = employees.count()
        active_employees = employees.filter(employment_status='ACTIVE').count()
        
        # Department distribution
        dept_distribution = employees.values('department__department_name').annotate(
            count=Count('employee_id')
        ).order_by('-count')
        
        # Average tenure
        tenures = [(datetime.now().date() - emp.hire_date).days / 365.25 for emp in employees]
        avg_tenure = round(sum(tenures) / len(tenures), 1) if tenures else 0
        
        return Response({
            'summary': {
                'total_employees': total_employees,
                'active_employees': active_employees,
                'inactive_employees': total_employees - active_employees,
                'average_tenure_years': avg_tenure
            },
            'department_distribution': dept_distribution,
            'employment_status_breakdown': employees.values('employment_status').annotate(
                count=Count('employee_id')
            )
        })
