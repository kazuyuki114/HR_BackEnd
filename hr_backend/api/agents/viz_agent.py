import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from database.hr_schema import *
import warnings
warnings.filterwarnings('ignore')

# Set style for better-looking plots
plt.style.use('default')
sns.set_palette("husl")

class HRVisualizationAgent:
    """
    AI Agent for HR Data Visualization and Analysis
    Capabilities:
    - Generate various types of charts from HR data
    - Provide insights and explanations
    - Interactive analysis based on user queries
    """
    
    def __init__(self, database_url=None):
        """Initialize the visualization agent"""
        if database_url is None:
            # Get path relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, "..", "..", "hr_database.db")
            database_url = f"sqlite:///{db_path}"
        self.engine = connect_to_existing_database(database_url)
        self.session = get_session(self.engine)
        self.insights = []
        
    def __del__(self):
        """Close database session"""
        try:
            if hasattr(self, 'session') and self.session:
                self.session.close()
        except (AttributeError, ImportError):
            # Ignore cleanup errors during Python shutdown
            pass
    
    def get_employee_data(self):
        """Get employee data with department and position info"""
        query = self.session.query(
            Employee.employee_id,
            Employee.first_name,
            Employee.last_name,
            Employee.gender,
            Employee.hire_date,
            Employee.employment_status,
            Department.department_name,
            Position.position_title
        ).select_from(Employee)\
         .join(Department, Employee.department_id == Department.department_id)\
         .join(Position, Employee.position_id == Position.position_id)
        
        df = pd.read_sql(query.statement, self.engine)
        
        # Convert enum columns to strings to avoid sorting issues
        if 'gender' in df.columns:
            df['gender'] = df['gender'].astype(str)
        if 'employment_status' in df.columns:
            df['employment_status'] = df['employment_status'].astype(str)
        
        return df

    def get_payroll_data(self):
        """Get payroll data with employee info"""
        query = self.session.query(
            Payroll.payroll_id,
            Payroll.employee_id,
            Payroll.basic_salary,
            Payroll.net_salary,
            Payroll.pay_period_start,
            Employee.first_name,
            Employee.last_name,
            Department.department_name,
            Position.position_title
        ).select_from(Payroll)\
         .join(Employee, Payroll.employee_id == Employee.employee_id)\
         .join(Department, Employee.department_id == Department.department_id)\
         .join(Position, Employee.position_id == Position.position_id)
        
        return pd.read_sql(query.statement, self.engine)
    
    def get_attendance_data(self):
        """Get attendance data with employee info"""
        query = self.session.query(
            Attendance.attendance_id,
            Attendance.employee_id,
            Attendance.date,
            Attendance.total_hours,
            Attendance.status,
            Employee.first_name,
            Employee.last_name,
            Department.department_name
        ).select_from(Attendance)\
         .join(Employee, Attendance.employee_id == Employee.employee_id)\
         .join(Department, Employee.department_id == Department.department_id)
        
        df = pd.read_sql(query.statement, self.engine)
        
        # Convert enum columns to strings
        if 'status' in df.columns:
            df['status'] = df['status'].astype(str)
        
        return df

    def get_performance_data(self):
        """Get performance review data"""
        query = self.session.query(
            PerformanceReview.review_id,
            PerformanceReview.employee_id,
            PerformanceReview.overall_score,
            PerformanceReview.goals_score,
            PerformanceReview.competency_score,
            PerformanceReview.review_date,
            Employee.first_name,
            Employee.last_name,
            Department.department_name,
            Position.position_title
        ).select_from(PerformanceReview)\
         .join(Employee, PerformanceReview.employee_id == Employee.employee_id)\
         .join(Department, Employee.department_id == Department.department_id)\
         .join(Position, Employee.position_id == Position.position_id)
        
        return pd.read_sql(query.statement, self.engine)
    
    def visualize_department_distribution(self, save_path=None):
        """Visualize employee distribution by department"""
        df = self.get_employee_data()
        
        # Handle empty data
        if df.empty:
            print("No employee data available for analysis")
            return "No employee data available for analysis"
        
        # Count employees by department
        dept_counts = df['department_name'].value_counts()
        
        # Create subplot with pie and bar chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Pie chart
        colors = plt.cm.Set3(np.linspace(0, 1, len(dept_counts)))
        ax1.pie(dept_counts.values, labels=dept_counts.index, autopct='%1.1f%%', colors=colors)
        ax1.set_title('Employee Distribution by Department', fontsize=14, fontweight='bold')
        
        # Bar chart
        bars = ax2.bar(dept_counts.index, dept_counts.values, color=colors)
        ax2.set_title('Number of Employees by Department', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Number of Employees')
        ax2.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        # Generate insights
        total_employees = len(df)
        largest_dept = dept_counts.index[0]
        largest_count = dept_counts.iloc[0]
        smallest_dept = dept_counts.index[-1]
        smallest_count = dept_counts.iloc[-1]
        
        insight = f"""
        📊 DEPARTMENT DISTRIBUTION ANALYSIS:
        
        • Total Employees: {total_employees}
        • Largest Department: {largest_dept} ({largest_count} employees, {largest_count/total_employees*100:.1f}%)
        • Smallest Department: {smallest_dept} ({smallest_count} employees, {smallest_count/total_employees*100:.1f}%)
        • Average Department Size: {total_employees/len(dept_counts):.1f} employees
        
        💡 INSIGHTS:
        • Department size distribution shows {'balanced' if dept_counts.std() < dept_counts.mean()*0.5 else 'uneven'} organization structure
        • Consider {'redistributing workload' if largest_count > total_employees*0.3 else 'current distribution seems optimal'}
        """
        
        self.insights.append(insight)
        print(insight)
        return insight
    
    def visualize_salary_analysis(self, save_path=None):
        """Analyze salary distribution across departments and positions"""
        df = self.get_payroll_data()
        
        # Handle empty data
        if df.empty:
            print("No payroll data available for analysis")
            return "No payroll data available for analysis"
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Salary distribution histogram
        ax1.hist(df['net_salary'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.set_title('Salary Distribution', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Net Salary ($)')
        ax1.set_ylabel('Frequency')
        ax1.axvline(df['net_salary'].mean(), color='red', linestyle='--', label=f'Mean: ${df["net_salary"].mean():,.0f}')
        ax1.legend()
        
        # 2. Average salary by department
        dept_salary = df.groupby('department_name')['net_salary'].mean().sort_values(ascending=False)
        bars1 = ax2.bar(range(len(dept_salary)), dept_salary.values, color='lightcoral')
        ax2.set_title('Average Salary by Department', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Average Net Salary ($)')
        ax2.set_xticks(range(len(dept_salary)))
        ax2.set_xticklabels(dept_salary.index, rotation=45, ha='right')
        
        # Add value labels
        for i, bar in enumerate(bars1):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'${height:,.0f}', ha='center', va='bottom')
        
        # 3. Salary box plot by department
        df_sample = df.sample(min(200, len(df)))  # Sample for better visualization
        sns.boxplot(data=df_sample, x='department_name', y='net_salary', ax=ax3)
        ax3.set_title('Salary Distribution by Department', fontsize=12, fontweight='bold')
        ax3.tick_params(axis='x', rotation=45)
        ax3.set_ylabel('Net Salary ($)')
        
        # 4. Top paying positions
        pos_salary = df.groupby('position_title')['net_salary'].mean().sort_values(ascending=False).head(10)
        bars2 = ax4.barh(range(len(pos_salary)), pos_salary.values, color='lightgreen')
        ax4.set_title('Top 10 Highest Paying Positions', fontsize=12, fontweight='bold')
        ax4.set_xlabel('Average Net Salary ($)')
        ax4.set_yticks(range(len(pos_salary)))
        ax4.set_yticklabels(pos_salary.index)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        # Generate insights
        avg_salary = df['net_salary'].mean()
        median_salary = df['net_salary'].median()
        highest_dept = dept_salary.index[0]
        lowest_dept = dept_salary.index[-1]
        salary_gap = dept_salary.iloc[0] - dept_salary.iloc[-1]
        
        insight = f"""
        💰 SALARY ANALYSIS:
        
        • Average Salary: ${avg_salary:,.0f}
        • Median Salary: ${median_salary:,.0f}
        • Highest Paying Department: {highest_dept} (${dept_salary.iloc[0]:,.0f})
        • Lowest Paying Department: {lowest_dept} (${dept_salary.iloc[-1]:,.0f})
        • Department Salary Gap: ${salary_gap:,.0f}
        
        💡 INSIGHTS:
        • Salary distribution is {'right-skewed' if avg_salary > median_salary else 'left-skewed' if avg_salary < median_salary else 'normal'}
        • Department salary gap is {'significant' if salary_gap > avg_salary*0.5 else 'moderate'}
        • Consider {'salary equity review' if salary_gap > avg_salary*0.7 else 'current structure appears balanced'}
        """
        
        self.insights.append(insight)
        print(insight)
        return insight
    
    def visualize_attendance_patterns(self, save_path=None):
        """Analyze attendance patterns and trends"""
        df = self.get_attendance_data()
        
        # Handle empty data
        if df.empty:
            print("No attendance data available for analysis")
            return "No attendance data available for analysis"
        
        df['date'] = pd.to_datetime(df['date'])
        df['weekday'] = df['date'].dt.day_name()
        df['month'] = df['date'].dt.month_name()
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Attendance status distribution
        status_counts = df['status'].value_counts()
        colors = ['lightgreen', 'lightcoral', 'lightskyblue', 'lightyellow']
        ax1.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%', colors=colors)
        ax1.set_title('Attendance Status Distribution', fontsize=12, fontweight='bold')
        
        # 2. Average hours by weekday
        weekday_hours = df.groupby('weekday')['total_hours'].mean()
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_hours = weekday_hours.reindex([day for day in weekday_order if day in weekday_hours.index])
        
        bars = ax2.bar(weekday_hours.index, weekday_hours.values, color='lightblue')
        ax2.set_title('Average Working Hours by Weekday', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Average Hours')
        ax2.tick_params(axis='x', rotation=45)
        
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}h', ha='center', va='bottom')
        
        # 3. Department attendance rate
        dept_attendance = df[df['status'] == 'Present'].groupby('department_name').size() / df.groupby('department_name').size() * 100
        dept_attendance = dept_attendance.sort_values(ascending=False)
        
        bars = ax3.bar(range(len(dept_attendance)), dept_attendance.values, color='lightgreen')
        ax3.set_title('Attendance Rate by Department', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Attendance Rate (%)')
        ax3.set_xticks(range(len(dept_attendance)))
        ax3.set_xticklabels(dept_attendance.index, rotation=45, ha='right')
        ax3.set_ylim(0, 100)
        
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%', ha='center', va='bottom')
        
        # 4. Daily attendance trend
        daily_attendance = df.groupby('date').agg({
            'total_hours': 'mean',
            'status': lambda x: (x == 'Present').sum() / len(x) * 100
        })
        
        ax4_twin = ax4.twinx()
        line1 = ax4.plot(daily_attendance.index, daily_attendance['total_hours'], 'b-', label='Avg Hours', alpha=0.7)
        line2 = ax4_twin.plot(daily_attendance.index, daily_attendance['status'], 'r-', label='Attendance %', alpha=0.7)
        
        ax4.set_title('Daily Attendance Trends', fontsize=12, fontweight='bold')
        ax4.set_ylabel('Average Hours', color='b')
        ax4_twin.set_ylabel('Attendance Rate (%)', color='r')
        ax4.tick_params(axis='x', rotation=45)
        
        # Combine legends
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax4.legend(lines, labels, loc='upper left')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        # Generate insights
        overall_attendance = (df['status'] == 'Present').sum() / len(df) * 100
        avg_hours = df['total_hours'].mean()
        best_dept = dept_attendance.index[0]
        worst_dept = dept_attendance.index[-1]
        
        insight = f"""
        ⏰ ATTENDANCE ANALYSIS:
        
        • Overall Attendance Rate: {overall_attendance:.1f}%
        • Average Working Hours: {avg_hours:.1f} hours/day
        • Best Attendance Department: {best_dept} ({dept_attendance.iloc[0]:.1f}%)
        • Lowest Attendance Department: {worst_dept} ({dept_attendance.iloc[-1]:.1f}%)
        
        💡 INSIGHTS:
        • Attendance rate is {'excellent' if overall_attendance > 95 else 'good' if overall_attendance > 90 else 'needs improvement'}
        • {'Monday blues effect detected' if weekday_hours.iloc[0] < weekday_hours.mean() - 0.5 else 'Consistent weekly performance'}
        • {'Consider flexible work arrangements' if avg_hours < 7.5 else 'Standard work hours maintained'}
        """
        
        self.insights.append(insight)
        print(insight)
        return insight
    
    def visualize_performance_trends(self, save_path=None):
        """Analyze employee performance trends"""
        df = self.get_performance_data()
        
        # Handle empty data
        if df.empty:
            print("No performance data available for analysis")
            return "No performance data available for analysis"
        
        # Check if required columns exist
        required_columns = ['review_date', 'overall_score', 'goals_score', 'competency_score', 'department_name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            error_msg = f"Missing required columns for performance analysis: {missing_columns}"
            print(error_msg)
            return error_msg
        
        df['review_date'] = pd.to_datetime(df['review_date'])
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Overall performance distribution
        ax1.hist(df['overall_score'], bins=20, alpha=0.7, color='gold', edgecolor='black')
        ax1.set_title('Overall Performance Score Distribution', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Performance Score (1-5)')
        ax1.set_ylabel('Frequency')
        ax1.axvline(df['overall_score'].mean(), color='red', linestyle='--', 
                   label=f'Mean: {df["overall_score"].mean():.2f}')
        ax1.legend()
        
        # 2. Performance by department
        dept_performance = df.groupby('department_name')['overall_score'].mean().sort_values(ascending=False)
        bars = ax2.bar(range(len(dept_performance)), dept_performance.values, color='lightcoral')
        ax2.set_title('Average Performance by Department', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Average Performance Score')
        ax2.set_xticks(range(len(dept_performance)))
        ax2.set_xticklabels(dept_performance.index, rotation=45, ha='right')
        ax2.set_ylim(0, 5)
        
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}', ha='center', va='bottom')
        
        # 3. Performance components comparison
        performance_components = df[['goals_score', 'competency_score', 'overall_score']].mean()
        bars = ax3.bar(performance_components.index, performance_components.values, 
                      color=['lightblue', 'lightgreen', 'gold'])
        ax3.set_title('Average Scores by Performance Component', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Average Score')
        ax3.set_ylim(0, 5)
        
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}', ha='center', va='bottom')
        
        # 4. Performance trend over time
        monthly_performance = df.groupby(df['review_date'].dt.to_period('M'))['overall_score'].mean()
        ax4.plot(monthly_performance.index.astype(str), monthly_performance.values, 
                marker='o', color='purple', linewidth=2)
        ax4.set_title('Performance Trend Over Time', fontsize=12, fontweight='bold')
        ax4.set_ylabel('Average Performance Score')
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        # Generate insights
        avg_performance = df['overall_score'].mean()
        top_dept = dept_performance.index[0]
        bottom_dept = dept_performance.index[-1]
        performance_std = df['overall_score'].std()
        
        insight = f"""
        🎯 PERFORMANCE ANALYSIS:
        
        • Average Performance Score: {avg_performance:.2f}/5.0
        • Performance Standard Deviation: {performance_std:.2f}
        • Top Performing Department: {top_dept} ({dept_performance.iloc[0]:.2f})
        • Lowest Performing Department: {bottom_dept} ({dept_performance.iloc[-1]:.2f})
        
        💡 INSIGHTS:
        • Overall performance level is {'excellent' if avg_performance >= 4 else 'good' if avg_performance >= 3.5 else 'needs improvement'}
        • Performance consistency is {'high' if performance_std < 0.5 else 'moderate' if performance_std < 1 else 'variable'}
        • {'Focus on performance development programs' if avg_performance < 3.5 else 'Maintain current performance standards'}
        """
        
        self.insights.append(insight)
        print(insight)
        return insight
    
    def visualize_gender_diversity(self, save_path=None):
        """Analyze gender diversity across departments and positions"""
        df = self.get_employee_data()
        
        # Handle empty data
        if df.empty:
            print("No employee data available for diversity analysis")
            return "No employee data available for diversity analysis"
        
        # Check if required columns exist
        required_columns = ['gender', 'department_name', 'position_title', 'hire_date']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            error_msg = f"Missing required columns for diversity analysis: {missing_columns}"
            print(error_msg)
            return error_msg
        
        # Clean gender data - remove any enum prefixes and handle None values
        df['gender'] = df['gender'].fillna('Unknown').astype(str)
        df['gender'] = df['gender'].str.replace('GenderEnum.', '', regex=False)
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Overall gender distribution
        gender_counts = df['gender'].value_counts()
        colors = ['lightblue', 'lightpink', 'lightgreen']
        ax1.pie(gender_counts.values, labels=gender_counts.index, autopct='%1.1f%%', colors=colors[:len(gender_counts)])
        ax1.set_title('Overall Gender Distribution', fontsize=12, fontweight='bold')
        
        # 2. Gender distribution by department
        gender_dept = pd.crosstab(df['department_name'], df['gender'], normalize='index') * 100
        gender_dept.plot(kind='bar', ax=ax2, color=colors[:len(gender_dept.columns)], alpha=0.8)
        ax2.set_title('Gender Distribution by Department (%)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Percentage')
        ax2.tick_params(axis='x', rotation=45)
        ax2.legend(title='Gender')
        
        # 3. Gender distribution in leadership positions
        leadership_keywords = ['Manager', 'Director', 'Lead', 'Head', 'Chief']
        df['is_leadership'] = df['position_title'].str.contains('|'.join(leadership_keywords), case=False, na=False)
        
        leadership_gender = df[df['is_leadership']]['gender'].value_counts()
        non_leadership_gender = df[~df['is_leadership']]['gender'].value_counts()
        
        # Ensure both series have the same index
        all_genders = df['gender'].unique()
        leadership_gender = leadership_gender.reindex(all_genders, fill_value=0)
        non_leadership_gender = non_leadership_gender.reindex(all_genders, fill_value=0)
        
        x = np.arange(len(all_genders))
        width = 0.35
        
        bars1 = ax3.bar(x - width/2, leadership_gender.values, width, label='Leadership', color='darkblue', alpha=0.7)
        bars2 = ax3.bar(x + width/2, non_leadership_gender.values, width, label='Non-Leadership', color='lightblue', alpha=0.7)
        
        ax3.set_title('Gender Distribution: Leadership vs Non-Leadership', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Number of Employees')
        ax3.set_xticks(x)
        ax3.set_xticklabels(all_genders)
        ax3.legend()
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom')
        
        # 4. Hiring trend by gender over time
        df['hire_year'] = pd.to_datetime(df['hire_date']).dt.year
        yearly_gender = pd.crosstab(df['hire_year'], df['gender'])
        
        yearly_gender.plot(kind='line', ax=ax4, marker='o', color=colors[:len(yearly_gender.columns)])
        ax4.set_title('Hiring Trend by Gender Over Years', fontsize=12, fontweight='bold')
        ax4.set_ylabel('Number of Hires')
        ax4.set_xlabel('Year')
        ax4.legend(title='Gender')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        # Generate insights
        total_employees = len(df)
        female_pct = (df['gender'] == 'Female').sum() / total_employees * 100 if total_employees > 0 else 0
        male_pct = (df['gender'] == 'Male').sum() / total_employees * 100 if total_employees > 0 else 0
        leadership_total = df['is_leadership'].sum()
        female_leadership_pct = (df[df['is_leadership']]['gender'] == 'Female').sum() / leadership_total * 100 if leadership_total > 0 else 0
        
        insight = f"""
        👥 GENDER DIVERSITY ANALYSIS:
        
        • Female Representation: {female_pct:.1f}%
        • Male Representation: {male_pct:.1f}%
        • Women in Leadership: {female_leadership_pct:.1f}%
        • Total Leadership Positions: {leadership_total}
        
        💡 INSIGHTS:
        • Overall gender balance is {'well-balanced' if 40 <= female_pct <= 60 else 'skewed'}
        • Leadership gender diversity {'needs improvement' if female_leadership_pct < 30 else 'is progressing well' if female_leadership_pct < 45 else 'is excellent'}
        • {'Implement diversity hiring initiatives' if female_pct < 35 else 'Continue current diversity efforts'}
        """
        
        self.insights.append(insight)
        print(insight)
        return insight
    
    def generate_comprehensive_report(self, save_dir="hr_reports"):
        """Generate a comprehensive HR analytics report"""
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        print("🤖 HR Visualization Agent - Comprehensive Analysis Report")
        print("=" * 60)
        
        # Clear previous insights
        self.insights = []
        
        # Generate all visualizations
        print("📊 Generating Department Distribution Analysis...")
        self.visualize_department_distribution(f"{save_dir}/department_distribution.png")
        
        print("\n💰 Generating Salary Analysis...")
        self.visualize_salary_analysis(f"{save_dir}/salary_analysis.png")
        
        print("\n⏰ Generating Attendance Analysis...")
        self.visualize_attendance_patterns(f"{save_dir}/attendance_patterns.png")
        
        print("\n🎯 Generating Performance Analysis...")
        self.visualize_performance_trends(f"{save_dir}/performance_trends.png")
        
        print("\n👥 Generating Diversity Analysis...")
        self.visualize_gender_diversity(f"{save_dir}/gender_diversity.png")
        
        # Generate summary report
        print("\n📋 COMPREHENSIVE HR INSIGHTS SUMMARY")
        print("=" * 60)
        for i, insight in enumerate(self.insights, 1):
            print(f"\n{i}. {insight}")
        
        # Save insights to file
        with open(f"{save_dir}/hr_insights_report.txt", "w") as f:
            f.write("HR ANALYTICS COMPREHENSIVE REPORT\n")
            f.write("Generated on: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
            f.write("=" * 60 + "\n\n")
            
            for i, insight in enumerate(self.insights, 1):
                f.write(f"{i}. {insight}\n\n")
        
        print(f"\n✅ Complete report saved to '{save_dir}' directory")
        print(f"📁 Generated files:")
        print(f"   • department_distribution.png")
        print(f"   • salary_analysis.png") 
        print(f"   • attendance_patterns.png")
        print(f"   • performance_trends.png")
        print(f"   • gender_diversity.png")
        print(f"   • hr_insights_report.txt")
    
    def interactive_query(self, query_type):
        """Handle interactive queries for specific analysis"""
        if query_type.lower() == "department":
            return self.visualize_department_distribution()
        elif query_type.lower() == "salary":
            return self.visualize_salary_analysis()
        elif query_type.lower() == "attendance":
            return self.visualize_attendance_patterns()
        elif query_type.lower() == "performance":
            return self.visualize_performance_trends()
        elif query_type.lower() == "diversity":
            return self.visualize_gender_diversity()
        elif query_type.lower() == "all":
            return self.generate_comprehensive_report()
        else:
            available_queries = ["department", "salary", "attendance", "performance", "diversity", "all"]
            return f"Available query types: {', '.join(available_queries)}"

# Example usage and testing
if __name__ == "__main__":
    # Initialize the agent
    agent = HRVisualizationAgent()
    
    print("🤖 HR Visualization Agent Initialized!")
    print("Available analysis types:")
    print("• department - Employee distribution by department")
    print("• salary - Salary analysis across departments and positions")
    print("• attendance - Attendance patterns and trends")  
    print("• performance - Performance review analysis")
    print("• diversity - Gender diversity analysis")
    print("• all - Generate comprehensive report")
    
    # Generate comprehensive report
    agent.generate_comprehensive_report()
