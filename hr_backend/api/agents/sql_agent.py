import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import re
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, date, timedelta
import pandas as pd
from database.hr_schema import *
from sqlalchemy import text, func, and_, or_, desc, asc
from openai import OpenAI
import json
from dotenv import load_dotenv

load_dotenv()

class HRSQLAgent:
    """
    Natural Language to SQL Agent for HR Database using OpenAI LLM
    Capabilities:
    - Convert natural language queries to SQL using LLM
    - Understand HR domain terminology
    - Execute queries and return results
    - Provide query explanations
    """
    
    def __init__(self, database_url=None, openai_api_key=None):
        """Initialize the SQL agent with OpenAI LLM"""
        if database_url is None:
            # Get path relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, "..", "..", "hr_database.db")
            database_url = f"sqlite:///{db_path}"
        self.engine = connect_to_existing_database(database_url)
        self.session = get_session(self.engine)
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=openai_api_key or os.getenv("OPENAI_API_KEY_3PARTY"),
            base_url=os.getenv("OPENAI_API_URL_3PARTY"),
            max_retries=3
        )
        
        if not (openai_api_key or os.getenv("OPENAI_API_KEY_3PARTY")):
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY_3PARTY environment variable or pass it as parameter.")
        
        # Database schema information for LLM
        self.schema_description = self._build_schema_description()
        
        # System prompt for the LLM
        self.system_prompt = f"""You are an expert SQL generator for an HR database. Given a natural language query, generate the appropriate SQL query.

Database Schema:
{self.schema_description}

Rules:
1. Generate only valid SQL queries
2. Use proper table aliases (e for employees, d for departments, p for positions, etc.)
3. Always include proper JOINs when accessing related tables
4. Use LIMIT when appropriate for "top X" queries
5. For aggregations, include proper GROUP BY clauses
6. Return only the SQL query, no explanations
7. Use SQLite syntax

Examples:
- "How many employees in IT?" → SELECT COUNT(*) FROM employees e JOIN departments d ON e.department_id = d.department_id WHERE d.department_name = 'Information Technology'
- "List top 5 salaries" → SELECT e.first_name, e.last_name, pr.net_salary FROM employees e JOIN payroll pr ON e.employee_id = pr.employee_id ORDER BY pr.net_salary DESC LIMIT 5
"""

    def _build_schema_description(self) -> str:
        """Build a comprehensive schema description for the LLM"""
        schema_desc = """
Tables and Relationships:

1. EMPLOYEES (e)
   - employee_id (PK), employee_code, first_name, last_name, email, phone
   - date_of_birth, gender, address, hire_date
   - department_id (FK), position_id (FK), manager_id (FK)
   - employment_status

2. DEPARTMENTS (d)
   - department_id (PK), department_name, department_code
   - manager_id (FK), budget, location
   Common names: IT=Information Technology, HR=Human Resources, Finance=Finance & Accounting

3. POSITIONS (p)
   - position_id (PK), position_title, position_code
   - department_id (FK), job_description
   - min_salary, max_salary, required_experience

4. PAYROLL (pr)
   - payroll_id (PK), employee_id (FK)
   - pay_period_start, pay_period_end
   - basic_salary, overtime_hours, overtime_rate
   - allowances, deductions, tax_deduction, net_salary, pay_date

5. ATTENDANCE (a)
   - attendance_id (PK), employee_id (FK), date
   - check_in_time, check_out_time, total_hours
   - status, remarks

6. LEAVE_REQUESTS (lr)
   - leave_id (PK), employee_id (FK), leave_type
   - start_date, end_date, days_requested
   - reason, status, approved_by

7. PERFORMANCE_REVIEWS (pr_rev)
   - review_id (PK), employee_id (FK), reviewer_id (FK)
   - review_period_start, review_period_end
   - goals_score, competency_score, overall_score, review_date

8. TRAINING_RECORDS (tr)
   - record_id (PK), employee_id (FK), program_id (FK)
   - enrollment_date, start_date, completion_date
   - status, score

9. TRAINING_PROGRAMS (tp)
   - program_id (PK), program_name, program_code
   - description, duration_hours, trainer_name
   - cost, max_participants

10. EMPLOYEE_BENEFITS (eb)
    - benefit_id (PK), employee_id (FK)
    - benefit_type, benefit_name, provider
    - coverage_amount, employee_contribution, company_contribution
    - start_date, end_date, is_active
"""
        return schema_desc
    
    def __del__(self):
        """Close database session"""
        if hasattr(self, 'session'):
            self.session.close()
    
    def generate_sql_with_llm(self, natural_query: str) -> Dict[str, Any]:
        """Generate SQL using OpenAI LLM"""
        try:
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": natural_query}
                ],
                temperature=0.1,
                max_tokens=500,
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Clean up the SQL (remove markdown formatting if present)
            if sql_query.startswith('```sql'):
                sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
            elif sql_query.startswith('```'):
                sql_query = sql_query.replace('```', '').strip()
            
            return {
                'sql': sql_query,
                'success': True,
                'error': None,
                'tokens_used': response.usage.total_tokens
            }
            
        except Exception as e:
            return {
                'sql': None,
                'success': False,
                'error': str(e),
                'tokens_used': 0
            }
    
    def validate_sql(self, sql: str) -> Tuple[bool, str]:
        """Validate SQL query without executing it"""
        try:
            # Basic SQL injection prevention
            forbidden_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
            sql_upper = sql.upper()
            
            for keyword in forbidden_keywords:
                if keyword in sql_upper:
                    return False, f"Forbidden operation: {keyword}"
            
            # Try to parse the SQL using SQLAlchemy
            text(sql)
            return True, "Valid SQL"
            
        except Exception as e:
            return False, f"Invalid SQL: {str(e)}"
    
    def execute_query(self, sql: str) -> Tuple[pd.DataFrame, str]:
        """Execute SQL query and return results"""
        try:
            # Validate SQL first
            is_valid, validation_msg = self.validate_sql(sql)
            if not is_valid:
                error_df = pd.DataFrame({'Error': [validation_msg]})
                return error_df, f"Validation Error: {validation_msg}"
            
            result_df = pd.read_sql(sql, self.engine)
            status = "Success"
            return result_df, status
        except Exception as e:
            error_df = pd.DataFrame({'Error': [str(e)]})
            status = f"Error: {str(e)}"
            return error_df, status
    
    def explain_query_with_llm(self, natural_query: str, sql: str) -> str:
        """Generate explanation using LLM"""
        try:
            explanation_prompt = f"""Explain this SQL query in simple terms for HR users:

Original Request: "{natural_query}"
Generated SQL: {sql}

Provide a clear, non-technical explanation of:
1. What data is being retrieved
2. Which tables are involved
3. Any filters or conditions applied
4. How results are organized (grouping, sorting, limits)

Keep it concise and user-friendly."""

            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=[
                    {"role": "user", "content": explanation_prompt}
                ],
                temperature=0.3,
                max_tokens=300,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"🔍 Query Explanation:\nOriginal request: '{natural_query}'\nGenerated SQL: {sql}\n(Explanation generation failed: {str(e)})"
    
    def process_natural_language_query(self, natural_query: str) -> Dict[str, Any]:
        """Process complete natural language to SQL workflow using LLM"""
        # Generate SQL using LLM
        llm_result = self.generate_sql_with_llm(natural_query)
        
        if not llm_result['success']:
            return {
                'natural_query': natural_query,
                'generated_sql': None,
                'results': pd.DataFrame({'Error': [llm_result['error']]}),
                'execution_status': f"LLM Error: {llm_result['error']}",
                'explanation': f"Failed to generate SQL: {llm_result['error']}",
                'row_count': 0,
                'tokens_used': llm_result['tokens_used']
            }
        
        sql = llm_result['sql']
        
        # Execute query
        results, status = self.execute_query(sql)
        
        # Generate explanation
        explanation = self.explain_query_with_llm(natural_query, sql)
        
        return {
            'natural_query': natural_query,
            'generated_sql': sql,
            'results': results,
            'execution_status': status,
            'explanation': explanation,
            'row_count': len(results) if not results.empty else 0,
            'tokens_used': llm_result['tokens_used']
        }
    
    def suggest_queries(self) -> List[str]:
        """Suggest example queries users can try"""
        return [
            "How many employees are in the IT department?",
            "List all employees with salary greater than 70000",
            "What is the average salary by department?",
            "Show top 10 highest paid employees",
            "Count employees hired this year",
            "List female employees in management positions",
            "What is the total payroll cost?",
            "Show employees with performance score above 4.0",
            "List all departments and their budgets",
            "Count leave requests by type",
            "Show attendance rate by department",
            "List employees due for performance review",
            "What training programs are available?",
            "Show employee benefits by type",
            "List employees hired in the last 6 months"
        ]
    
    def get_schema_summary(self) -> str:
        """Get a summary of the database schema"""
        return f"🗄️ HR Database Schema Summary:\n{self.schema_description}"
    
    def interactive_mode(self):
        """Run interactive query mode"""
        print("🤖 HR SQL Agent - Natural Language Query Interface (Powered by OpenAI)")
        print("=" * 70)
        print(self.get_schema_summary())
        print("\n💡 Example queries:")
        for query in self.suggest_queries()[:5]:
            print(f"  • {query}")
        print("\nType 'exit' to quit, 'help' for examples, 'schema' for database info")
        print("=" * 70)
        
        total_tokens = 0
        
        while True:
            try:
                user_input = input("\n🔍 Enter your query: ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    print(f"👋 Goodbye! Total tokens used: {total_tokens}")
                    break
                elif user_input.lower() == 'help':
                    print("\n💡 Example queries:")
                    for query in self.suggest_queries():
                        print(f"  • {query}")
                    continue
                elif user_input.lower() == 'schema':
                    print(self.get_schema_summary())
                    continue
                elif not user_input:
                    continue
                
                # Process the query
                result = self.process_natural_language_query(user_input)
                total_tokens += result.get('tokens_used', 0)
                
                # Display results
                print(f"\n💻 Generated SQL:\n{result['generated_sql']}")
                print(f"\n{result['explanation']}")
                print(f"\n📊 Results ({result['row_count']} rows) | Tokens used: {result.get('tokens_used', 0)}")
                print("=" * 50)
                
                if result['execution_status'] == "Success":
                    if not result['results'].empty:
                        print(result['results'].to_string(index=False, max_rows=20))
                        if len(result['results']) > 20:
                            print(f"... and {len(result['results']) - 20} more rows")
                    else:
                        print("No results found.")
                else:
                    print(f"❌ {result['execution_status']}")
                
            except KeyboardInterrupt:
                print(f"\n👋 Goodbye! Total tokens used: {total_tokens}")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")

# Example usage and testing
if __name__ == "__main__":
    # Initialize the SQL agent
    try:
        agent = HRSQLAgent()
        print("🤖 HR SQL Agent with OpenAI LLM Initialized!")
        
        # Test some example queries
        test_queries = [
            "How many employees are in the IT department?",
            "List employees with salary greater than 60000",
            "What is the average salary by department?",
            "Show top 5 highest paid employees"
        ]
        
        for query in test_queries:
            print(f"\n" + "="*60)
            result = agent.process_natural_language_query(query)
            print(f"Query: {query}")
            print(f"SQL: {result['generated_sql']}")
            print(f"Results: {result['row_count']} rows | Tokens: {result.get('tokens_used', 0)}")
            if result['execution_status'] == "Success" and not result['results'].empty:
                print(result['results'].head().to_string(index=False))
            
        # Start interactive mode
        print(f"\n" + "="*60)
        print("Starting interactive mode...")
        agent.interactive_mode()
        
    except ValueError as e:
        print(f"❌ {e}")
        print("Please set your OpenAI API key in the OPENAI_API_KEY_3PARTY environment variable.")
        #     # Map column names to appropriate table aliases
        #     if column == 'department_name':
        #         column = 'd.department_name'
        #     elif column == 'position_title':
        #         column = 'p.position_title'
        #     elif column == 'net_salary':
        #         column = 'pr.net_salary'
        #     elif column in ['gender', 'employment_status', 'hire_date']:
        #         column = f'e.{column}'
            
        #     if operator == 'BETWEEN':
        #         where_parts.append(f"{column} BETWEEN '{value[0]}' AND '{value[1]}'")
        #     elif operator in ['=', '>', '<', '>=', '<=']:
        #         if isinstance(value, str):
        #             where_parts.append(f"{column} {operator} '{value}'")
        #         else:
        #             where_parts.append(f"{column} {operator} {value}")
        
        # return f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
    
    def execute_query(self, sql: str) -> Tuple[pd.DataFrame, str]:
        """Execute SQL query and return results"""
        try:
            result_df = pd.read_sql(sql, self.engine)
            status = "Success"
            return result_df, status
        except Exception as e:
            error_df = pd.DataFrame({'Error': [str(e)]})
            status = f"Error: {str(e)}"
            return error_df, status
    
    def explain_query(self, sql: str, parsed: Dict[str, Any]) -> str:
        """Provide explanation of the generated query"""
        explanation = f"🔍 Query Explanation:\n"
        explanation += f"Original request: '{parsed['raw_query']}'\n\n"
        
        explanation += f"📊 Intent: {parsed['intent'].title()}\n"
        
        if parsed['tables']:
            explanation += f"📋 Tables involved: {', '.join(parsed['tables'])}\n"
        
        if parsed['conditions']:
            explanation += f"🔧 Filters applied:\n"
            for condition in parsed['conditions']:
                explanation += f"  - {condition['column']} {condition['operator']} {condition['value']}\n"
        
        if parsed['grouping']:
            explanation += f"📊 Grouped by: {', '.join(parsed['grouping'])}\n"
        
        if parsed['ordering']:
            explanation += f"📈 Ordered by: {', '.join([f'{col} ({direction})' for col, direction in parsed['ordering']])}\n"
        
        if parsed['limit']:
            explanation += f"🔢 Limited to: {parsed['limit']} results\n"
        
        explanation += f"\n💻 Generated SQL:\n{sql}"
        
        return explanation
    
    def process_natural_language_query(self, natural_query: str) -> Dict[str, Any]:
        """Process complete natural language to SQL workflow"""
        # Parse the natural language
        parsed = self.parse_natural_language(natural_query)
        
        # Generate SQL
        sql = self.generate_sql(parsed)
        
        # Execute query
        results, status = self.execute_query(sql)
        
        # Generate explanation
        explanation = self.explain_query(sql, parsed)
        
        return {
            'natural_query': natural_query,
            'parsed_components': parsed,
            'generated_sql': sql,
            'results': results,
            'execution_status': status,
            'explanation': explanation,
            'row_count': len(results) if not results.empty else 0
        }
    
    def suggest_queries(self) -> List[str]:
        """Suggest example queries users can try"""
        return [
            "How many employees are in the IT department?",
            "List all employees with salary greater than 70000",
            "What is the average salary by department?",
            "Show top 10 highest paid employees",
            "Count employees hired this year",
            "List female employees in management positions",
            "What is the total payroll cost?",
            "Show employees with performance score above 4.0",
            "List all departments and their budgets",
            "Count leave requests by type",
            "Show attendance rate by department",
            "List employees due for performance review",
            "What training programs are available?",
            "Show employee benefits by type",
            "List employees hired in the last 6 months"
        ]
    
    def get_schema_summary(self) -> str:
        """Get a summary of the database schema"""
        summary = "🗄️ HR Database Schema Summary:\n\n"
        
        for table, info in self.schema_info['tables'].items():
            summary += f"📋 {table.upper()}:\n"
            summary += f"   Columns: {', '.join(info['columns'][:5])}{'...' if len(info['columns']) > 5 else ''}\n"
            summary += f"   Aliases: {', '.join(info['aliases'])}\n\n"
        
        return summary
    
    def interactive_mode(self):
        """Run interactive query mode"""
        print("🤖 HR SQL Agent - Natural Language Query Interface")
        print("=" * 60)
        print(self.get_schema_summary())
        print("💡 Example queries:")
        for query in self.suggest_queries()[:5]:
            print(f"  • {query}")
        print("\nType 'exit' to quit, 'help' for examples, 'schema' for database info")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n🔍 Enter your query: ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    print("\n💡 Example queries:")
                    for query in self.suggest_queries():
                        print(f"  • {query}")
                    continue
                elif user_input.lower() == 'schema':
                    print(self.get_schema_summary())
                    continue
                elif not user_input:
                    continue
                
                # Process the query
                result = self.process_natural_language_query(user_input)
                
                # Display results
                print(f"\n{result['explanation']}")
                print(f"\n📊 Results ({result['row_count']} rows):")
                print("=" * 50)
                
                if result['execution_status'] == "Success":
                    if not result['results'].empty:
                        print(result['results'].to_string(index=False, max_rows=20))
                        if len(result['results']) > 20:
                            print(f"... and {len(result['results']) - 20} more rows")
                    else:
                        print("No results found.")
                else:
                    print(f"❌ {result['execution_status']}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")

# Example usage and testing
if __name__ == "__main__":
    # Initialize the SQL agent
    agent = HRSQLAgent()
    
    print("🤖 HR SQL Agent Initialized!")
    
    # Test some example queries
    test_queries = [
        "How many employees are in the IT department?",
        "List employees with salary greater than 60000",
        "What is the average salary by department?",
        "Show top 5 highest paid employees"
    ]
    
    for query in test_queries:
        print(f"\n" + "="*60)
        result = agent.process_natural_language_query(query)
        print(result['explanation'])
        print(f"\nResults: {result['row_count']} rows")
        if result['execution_status'] == "Success" and not result['results'].empty:
            print(result['results'].head().to_string(index=False))
        
    # Start interactive mode
    print(f"\n" + "="*60)
    print("Starting interactive mode...")
    agent.interactive_mode()
