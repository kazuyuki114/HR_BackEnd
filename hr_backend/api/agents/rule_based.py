import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Any, Optional
import json
from database.hr_schema import *
from sqlalchemy import and_, or_, func

class HRRuleBasedAgent:
    """
    Rule-Based Agent for HR Operations
    Capabilities:
    - Policy enforcement and validation
    - Automated decision making based on business rules
    - Data quality checks
    - Compliance monitoring
    - Workflow automation
    """
    
    def __init__(self, database_url=None):
        """Initialize the rule-based agent"""
        if database_url is None:
            # Get path relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, "..", "..", "hr_database.db")
            database_url = f"sqlite:///{db_path}"
        self.engine = connect_to_existing_database(database_url)
        self.session = get_session(self.engine)
        self.rules_log = []
        
        # Define HR policies and rules
        self.policies = {
            'max_annual_leave': 25,
            'max_sick_leave': 15,
            'min_experience_manager': 3,
            'max_overtime_monthly': 40,
            'performance_review_frequency': 365,  # days
            'probation_period': 90,  # days
            'min_salary_increase': 0.03,  # 3%
            'max_salary_increase': 0.15,  # 15%
            'mandatory_training_hours': 40,  # per year
            'retirement_age': 65
        }
        
        # Salary bands by position level
        self.salary_bands = {
            'entry': {'min': 35000, 'max': 50000},
            'junior': {'min': 45000, 'max': 65000},
            'mid': {'min': 60000, 'max': 85000},
            'senior': {'min': 80000, 'max': 120000},
            'manager': {'min': 100000, 'max': 150000},
            'director': {'min': 140000, 'max': 200000}
        }
    
    def __del__(self):
        """Close database session"""
        try:
            if hasattr(self, 'session') and self.session:
                self.session.close()
        except (AttributeError, ImportError):
            # Ignore cleanup errors during Python shutdown
            pass
    
    def log_rule_action(self, rule_name: str, action: str, details: str, employee_id: Optional[int] = None):
        """Log rule enforcement actions"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'rule_name': rule_name,
            'action': action,
            'details': details,
            'employee_id': employee_id
        }
        self.rules_log.append(log_entry)
    
    # === LEAVE MANAGEMENT RULES ===
    
    def validate_leave_request(self, employee_id: int, leave_type: str, start_date: date, 
                             end_date: date, days_requested: int) -> Dict[str, Any]:
        """Validate leave request against HR policies"""
        result = {
            'valid': True,
            'violations': [],
            'warnings': [],
            'auto_approve': False
        }
        
        employee = self.session.query(Employee).filter(Employee.employee_id == employee_id).first()
        if not employee:
            result['valid'] = False
            result['violations'].append("Employee not found")
            return result
        
        # Check if employee is in probation period
        hire_date = employee.hire_date
        probation_end = hire_date + timedelta(days=self.policies['probation_period'])
        if start_date < probation_end:
            result['violations'].append(f"Employee in probation period until {probation_end}")
            result['valid'] = False
        
        # Check annual leave limit
        if leave_type == 'Annual Leave':
            current_year_leaves = self.session.query(func.sum(LeaveRequest.days_requested)).filter(
                and_(
                    LeaveRequest.employee_id == employee_id,
                    LeaveRequest.leave_type == LeaveTypeEnum.ANNUAL,
                    LeaveRequest.status == 'Approved',
                    func.extract('year', LeaveRequest.start_date) == start_date.year
                )
            ).scalar() or 0
            
            if current_year_leaves + days_requested > self.policies['max_annual_leave']:
                result['violations'].append(
                    f"Exceeds annual leave limit: {current_year_leaves + days_requested} > {self.policies['max_annual_leave']}"
                )
                result['valid'] = False
        
        # Check sick leave limit
        elif leave_type == 'Sick Leave':
            current_year_sick = self.session.query(func.sum(LeaveRequest.days_requested)).filter(
                and_(
                    LeaveRequest.employee_id == employee_id,
                    LeaveRequest.leave_type == LeaveTypeEnum.SICK,
                    LeaveRequest.status == 'Approved',
                    func.extract('year', LeaveRequest.start_date) == start_date.year
                )
            ).scalar() or 0
            
            if current_year_sick + days_requested > self.policies['max_sick_leave']:
                result['violations'].append(
                    f"Exceeds sick leave limit: {current_year_sick + days_requested} > {self.policies['max_sick_leave']}"
                )
                result['valid'] = False
        
        # Auto-approve short leaves for good performers
        if days_requested <= 3 and leave_type == 'Annual Leave':
            recent_performance = self.get_latest_performance_score(employee_id)
            if recent_performance and recent_performance >= 4.0:
                result['auto_approve'] = True
                result['warnings'].append("Auto-approved based on good performance")
        
        # Check for overlapping leaves
        overlapping = self.session.query(LeaveRequest).filter(
            and_(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.status.in_(['Pending', 'Approved']),
                or_(
                    and_(LeaveRequest.start_date <= start_date, LeaveRequest.end_date >= start_date),
                    and_(LeaveRequest.start_date <= end_date, LeaveRequest.end_date >= end_date),
                    and_(LeaveRequest.start_date >= start_date, LeaveRequest.end_date <= end_date)
                )
            )
        ).first()
        
        if overlapping:
            result['violations'].append(f"Overlapping with existing leave request #{overlapping.leave_id}")
            result['valid'] = False
        
        self.log_rule_action(
            'leave_validation', 
            'validated' if result['valid'] else 'rejected',
            f"Leave request for {days_requested} days: {result['violations'] or 'Valid'}",
            employee_id
        )
        
        return result
    
    # === SALARY AND PROMOTION RULES ===
    
    def validate_salary_adjustment(self, employee_id: int, new_salary: float, 
                                 adjustment_type: str = 'increase') -> Dict[str, Any]:
        """Validate salary adjustments against company policies"""
        result = {
            'valid': True,
            'violations': [],
            'warnings': [],
            'recommended_salary': None
        }
        
        # Get current employee and payroll data
        employee = self.session.query(Employee).filter(Employee.employee_id == employee_id).first()
        if not employee:
            result['valid'] = False
            result['violations'].append("Employee not found")
            return result
        
        latest_payroll = self.session.query(Payroll).filter(
            Payroll.employee_id == employee_id
        ).order_by(Payroll.pay_period_end.desc()).first()
        
        if not latest_payroll:
            result['warnings'].append("No previous salary data found")
            current_salary = 0
        else:
            current_salary = latest_payroll.basic_salary
        
        # Calculate adjustment percentage
        if current_salary > 0:
            adjustment_pct = (new_salary - current_salary) / current_salary
        else:
            adjustment_pct = 0
        
        # Check adjustment limits
        if adjustment_type == 'increase':
            if adjustment_pct < self.policies['min_salary_increase']:
                result['warnings'].append(
                    f"Increase below minimum policy: {adjustment_pct:.2%} < {self.policies['min_salary_increase']:.2%}"
                )
            
            if adjustment_pct > self.policies['max_salary_increase']:
                result['violations'].append(
                    f"Increase exceeds maximum policy: {adjustment_pct:.2%} > {self.policies['max_salary_increase']:.2%}"
                )
                result['valid'] = False
                result['recommended_salary'] = current_salary * (1 + self.policies['max_salary_increase'])
        
        # Check against salary bands
        position_level = self.determine_position_level(employee.position.position_title)
        if position_level in self.salary_bands:
            band = self.salary_bands[position_level]
            if new_salary < band['min']:
                result['violations'].append(
                    f"Salary below band minimum for {position_level}: ${new_salary:,} < ${band['min']:,}"
                )
                result['valid'] = False
            elif new_salary > band['max']:
                result['violations'].append(
                    f"Salary exceeds band maximum for {position_level}: ${new_salary:,} > ${band['max']:,}"
                )
                result['valid'] = False
        
        # Check performance justification for large increases
        if adjustment_pct > 0.10:  # 10%+ increase
            recent_performance = self.get_latest_performance_score(employee_id)
            if not recent_performance or recent_performance < 4.0:
                result['violations'].append(
                    "Large salary increase requires performance score ≥ 4.0"
                )
                result['valid'] = False
        
        self.log_rule_action(
            'salary_validation',
            'approved' if result['valid'] else 'rejected',
            f"Salary adjustment to ${new_salary:,} ({adjustment_pct:.2%}): {result['violations'] or 'Valid'}",
            employee_id
        )
        
        return result
    
    # === PROMOTION RULES ===
    
    def validate_promotion(self, employee_id: int, new_position_id: int) -> Dict[str, Any]:
        """Validate employee promotion against eligibility criteria"""
        result = {
            'valid': True,
            'violations': [],
            'warnings': [],
            'requirements_met': {}
        }
        
        employee = self.session.query(Employee).filter(Employee.employee_id == employee_id).first()
        new_position = self.session.query(Position).filter(Position.position_id == new_position_id).first()
        
        if not employee or not new_position:
            result['valid'] = False
            result['violations'].append("Employee or position not found")
            return result
        
        # Check tenure requirement
        tenure_days = (date.today() - employee.hire_date).days
        min_tenure = 365  # 1 year minimum
        result['requirements_met']['tenure'] = tenure_days >= min_tenure
        
        if not result['requirements_met']['tenure']:
            result['violations'].append(
                f"Insufficient tenure: {tenure_days} days < {min_tenure} days required"
            )
            result['valid'] = False
        
        # Check performance requirement
        recent_performance = self.get_latest_performance_score(employee_id)
        min_performance = 3.5
        result['requirements_met']['performance'] = recent_performance and recent_performance >= min_performance
        
        if not result['requirements_met']['performance']:
            result['violations'].append(
                f"Performance requirement not met: {recent_performance or 'No data'} < {min_performance}"
            )
            result['valid'] = False
        
        # Check experience for management positions
        if 'manager' in new_position.position_title.lower():
            experience_years = tenure_days / 365.25
            min_exp = self.policies['min_experience_manager']
            result['requirements_met']['management_experience'] = experience_years >= min_exp
            
            if not result['requirements_met']['management_experience']:
                result['violations'].append(
                    f"Insufficient experience for management: {experience_years:.1f} years < {min_exp} years"
                )
                result['valid'] = False
        
        # Check training requirements
        training_hours = self.get_training_hours_completed(employee_id)
        min_training = self.policies['mandatory_training_hours']
        result['requirements_met']['training'] = training_hours >= min_training
        
        if not result['requirements_met']['training']:
            result['warnings'].append(
                f"Training hours below recommended: {training_hours} < {min_training}"
            )
        
        self.log_rule_action(
            'promotion_validation',
            'approved' if result['valid'] else 'rejected',
            f"Promotion to {new_position.position_title}: {result['violations'] or 'Eligible'}",
            employee_id
        )
        
        return result
    
    # === ATTENDANCE RULES ===
    
    def analyze_attendance_violations(self, employee_id: int, period_days: int = 30) -> Dict[str, Any]:
        """Analyze attendance patterns and identify violations"""
        result = {
            'violations': [],
            'patterns': {},
            'recommendations': []
        }
        
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)
        
        attendance_records = self.session.query(Attendance).filter(
            and_(
                Attendance.employee_id == employee_id,
                Attendance.date >= start_date,
                Attendance.date <= end_date
            )
        ).all()
        
        if not attendance_records:
            result['patterns']['no_data'] = True
            return result
        
        # Calculate attendance statistics
        total_days = len(attendance_records)
        present_days = len([r for r in attendance_records if r.status == AttendanceStatusEnum.PRESENT])
        late_days = len([r for r in attendance_records if r.status == AttendanceStatusEnum.LATE])
        absent_days = len([r for r in attendance_records if r.status == AttendanceStatusEnum.ABSENT])
        
        attendance_rate = (present_days + late_days) / total_days if total_days > 0 else 0
        late_rate = late_days / total_days if total_days > 0 else 0
        
        result['patterns'] = {
            'attendance_rate': attendance_rate,
            'late_rate': late_rate,
            'absent_days': absent_days,
            'total_days': total_days
        }
        
        # Check violations
        if attendance_rate < 0.90:  # Less than 90% attendance
            result['violations'].append(f"Low attendance rate: {attendance_rate:.1%}")
        
        if late_rate > 0.20:  # More than 20% late arrivals
            result['violations'].append(f"Excessive late arrivals: {late_rate:.1%}")
        
        if absent_days > 5:  # More than 5 absent days in period
            result['violations'].append(f"Excessive absences: {absent_days} days")
        
        # Generate recommendations
        if result['violations']:
            result['recommendations'].append("Schedule attendance counseling")
            if attendance_rate < 0.80:
                result['recommendations'].append("Consider performance improvement plan")
        
        # Check for patterns (consecutive absences, Monday/Friday patterns)
        absent_dates = [r.date for r in attendance_records if r.status == AttendanceStatusEnum.ABSENT]
        if len(absent_dates) >= 3:
            # Check for consecutive absences
            consecutive = self.find_consecutive_dates(absent_dates)
            if consecutive:
                result['patterns']['consecutive_absences'] = consecutive
                result['recommendations'].append("Investigate reasons for consecutive absences")
        
        self.log_rule_action(
            'attendance_analysis',
            'completed',
            f"Attendance violations: {len(result['violations'])}, Rate: {attendance_rate:.1%}",
            employee_id
        )
        
        return result
    
    # === PERFORMANCE MANAGEMENT RULES ===
    
    def check_performance_review_due(self, employee_id: int) -> Dict[str, Any]:
        """Check if employee is due for performance review"""
        result = {
            'due': False,
            'overdue': False,
            'last_review_date': None,
            'days_since_review': None,
            'recommended_action': None
        }
        
        employee = self.session.query(Employee).filter(Employee.employee_id == employee_id).first()
        if not employee:
            return result
        
        last_review = self.session.query(PerformanceReview).filter(
            PerformanceReview.employee_id == employee_id
        ).order_by(PerformanceReview.review_date.desc()).first()
        
        if last_review:
            result['last_review_date'] = last_review.review_date
            days_since = (date.today() - last_review.review_date).days
        else:
            # If no review exists, use hire date
            result['last_review_date'] = employee.hire_date
            days_since = (date.today() - employee.hire_date).days
        
        result['days_since_review'] = days_since
        review_frequency = self.policies['performance_review_frequency']
        
        if days_since >= review_frequency:
            result['due'] = True
            if days_since >= review_frequency + 30:  # 30 days grace period
                result['overdue'] = True
                result['recommended_action'] = "Schedule immediate performance review"
            else:
                result['recommended_action'] = "Schedule performance review"
        elif days_since >= review_frequency - 30:  # Within 30 days
            result['recommended_action'] = "Performance review coming due"
        
        return result
    
    # === TRAINING COMPLIANCE RULES ===
    
    def check_training_compliance(self, employee_id: int) -> Dict[str, Any]:
        """Check employee training compliance"""
        result = {
            'compliant': True,
            'hours_completed': 0,
            'hours_required': self.policies['mandatory_training_hours'],
            'missing_hours': 0,
            'recommendations': []
        }
        
        # Get training hours for current year
        current_year = date.today().year
        training_records = self.session.query(TrainingRecord).join(TrainingProgram).filter(
            and_(
                TrainingRecord.employee_id == employee_id,
                TrainingRecord.status == 'Completed',
                func.extract('year', TrainingRecord.completion_date) == current_year
            )
        ).all()
        
        total_hours = sum([
            record.program.duration_hours for record in training_records 
            if record.program.duration_hours
        ])
        
        result['hours_completed'] = total_hours
        result['missing_hours'] = max(0, result['hours_required'] - total_hours)
        result['compliant'] = total_hours >= result['hours_required']
        
        if not result['compliant']:
            result['recommendations'].append(
                f"Complete {result['missing_hours']} additional training hours"
            )
        
        return result
    
    # === RETIREMENT ELIGIBILITY ===
    
    def check_retirement_eligibility(self, employee_id: int) -> Dict[str, Any]:
        """Check if employee is eligible for retirement"""
        result = {
            'eligible': False,
            'age': None,
            'years_of_service': None,
            'retirement_date': None
        }
        
        employee = self.session.query(Employee).filter(Employee.employee_id == employee_id).first()
        if not employee or not employee.date_of_birth:
            return result
        
        today = date.today()
        age = today.year - employee.date_of_birth.year
        if today < employee.date_of_birth.replace(year=today.year):
            age -= 1
        
        years_of_service = (today - employee.hire_date).days / 365.25
        
        result['age'] = age
        result['years_of_service'] = years_of_service
        
        # Standard retirement age
        if age >= self.policies['retirement_age']:
            result['eligible'] = True
            result['retirement_date'] = employee.date_of_birth.replace(
                year=employee.date_of_birth.year + self.policies['retirement_age']
            )
        
        return result
    
    # === UTILITY METHODS ===
    
    def get_latest_performance_score(self, employee_id: int) -> Optional[float]:
        """Get latest performance score for employee"""
        latest_review = self.session.query(PerformanceReview).filter(
            PerformanceReview.employee_id == employee_id
        ).order_by(PerformanceReview.review_date.desc()).first()
        
        return latest_review.overall_score if latest_review else None
    
    def get_training_hours_completed(self, employee_id: int, year: Optional[int] = None) -> int:
        """Get total training hours completed by employee"""
        if year is None:
            year = date.today().year
        
        training_records = self.session.query(TrainingRecord).join(TrainingProgram).filter(
            and_(
                TrainingRecord.employee_id == employee_id,
                TrainingRecord.status == 'Completed',
                func.extract('year', TrainingRecord.completion_date) == year
            )
        ).all()
        
        return sum([
            record.program.duration_hours for record in training_records 
            if record.program.duration_hours
        ])
    
    def determine_position_level(self, position_title: str) -> str:
        """Determine position level from title"""
        title_lower = position_title.lower()
        
        if any(word in title_lower for word in ['director', 'vp', 'vice president']):
            return 'director'
        elif any(word in title_lower for word in ['manager', 'lead', 'head']):
            return 'manager'
        elif any(word in title_lower for word in ['senior', 'sr']):
            return 'senior'
        elif any(word in title_lower for word in ['junior', 'jr', 'associate']):
            return 'junior'
        elif any(word in title_lower for word in ['intern', 'trainee', 'entry']):
            return 'entry'
        else:
            return 'mid'
    
    def find_consecutive_dates(self, dates: List[date]) -> List[List[date]]:
        """Find consecutive date sequences"""
        if not dates:
            return []
        
        sorted_dates = sorted(dates)
        consecutive_groups = []
        current_group = [sorted_dates[0]]
        
        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                current_group.append(sorted_dates[i])
            else:
                if len(current_group) >= 3:  # 3+ consecutive days
                    consecutive_groups.append(current_group)
                current_group = [sorted_dates[i]]
        
        if len(current_group) >= 3:
            consecutive_groups.append(current_group)
        
        return consecutive_groups
    
    # === BATCH OPERATIONS ===
    
    def run_compliance_audit(self) -> Dict[str, Any]:
        """Run comprehensive compliance audit for all employees"""
        audit_results = {
            'timestamp': datetime.now().isoformat(),
            'employees_audited': 0,
            'violations': [],
            'summary': {
                'attendance_violations': 0,
                'performance_reviews_overdue': 0,
                'training_non_compliant': 0,
                'retirement_eligible': 0
            }
        }
        
        # Get all active employees
        employees = self.session.query(Employee).filter(
            Employee.employment_status == EmploymentStatusEnum.ACTIVE
        ).all()
        
        audit_results['employees_audited'] = len(employees)
        
        for employee in employees:
            employee_violations = []
            
            # Check attendance
            attendance_result = self.analyze_attendance_violations(employee.employee_id)
            if attendance_result['violations']:
                employee_violations.extend(attendance_result['violations'])
                audit_results['summary']['attendance_violations'] += 1
            
            # Check performance reviews
            review_status = self.check_performance_review_due(employee.employee_id)
            if review_status['overdue']:
                employee_violations.append("Performance review overdue")
                audit_results['summary']['performance_reviews_overdue'] += 1
            
            # Check training compliance
            training_status = self.check_training_compliance(employee.employee_id)
            if not training_status['compliant']:
                employee_violations.append(f"Training non-compliant: {training_status['missing_hours']} hours missing")
                audit_results['summary']['training_non_compliant'] += 1
            
            # Check retirement eligibility
            retirement_status = self.check_retirement_eligibility(employee.employee_id)
            if retirement_status['eligible']:
                employee_violations.append("Eligible for retirement")
                audit_results['summary']['retirement_eligible'] += 1
            
            if employee_violations:
                audit_results['violations'].append({
                    'employee_id': employee.employee_id,
                    'employee_name': f"{employee.first_name} {employee.last_name}",
                    'violations': employee_violations
                })
        
        self.log_rule_action(
            'compliance_audit',
            'completed',
            f"Audited {audit_results['employees_audited']} employees, found {len(audit_results['violations'])} with violations"
        )
        
        return audit_results
    
    def get_rules_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent rule enforcement log"""
        return self.rules_log[-limit:] if self.rules_log else []
    
    def export_audit_report(self, audit_results: Dict[str, Any], filename: str = None) -> str:
        """Export audit results to JSON file"""
        if filename is None:
            filename = f"hr_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(audit_results, f, indent=2, default=str)
        
        return filename

# Example usage and testing
if __name__ == "__main__":
    # Initialize the rule-based agent
    agent = HRRuleBasedAgent()
    
    print("🤖 HR Rule-Based Agent Initialized!")
    print("=" * 50)
    
    # Example: Run compliance audit
    print("Running compliance audit...")
    audit_results = agent.run_compliance_audit()
    
    print(f"\n📋 AUDIT SUMMARY:")
    print(f"• Employees Audited: {audit_results['employees_audited']}")
    print(f"• Attendance Violations: {audit_results['summary']['attendance_violations']}")
    print(f"• Overdue Performance Reviews: {audit_results['summary']['performance_reviews_overdue']}")
    print(f"• Training Non-Compliant: {audit_results['summary']['training_non_compliant']}")
    print(f"• Retirement Eligible: {audit_results['summary']['retirement_eligible']}")
    
    if audit_results['violations']:
        print(f"\n⚠️  VIOLATIONS FOUND ({len(audit_results['violations'])}):")
        for violation in audit_results['violations'][:5]:  # Show first 5
            print(f"• {violation['employee_name']}: {', '.join(violation['violations'])}")
    
    # Export audit report
    report_file = agent.export_audit_report(audit_results)
    print(f"\n📄 Audit report saved to: {report_file}")
    
    print("\n✅ Rule-based agent demonstration completed!")
