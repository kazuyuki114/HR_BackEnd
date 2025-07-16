#!/usr/bin/env python3
"""
Script to generate a comprehensive JSON file from department CSV files
Reads all CSV files from the sample folder and creates department_headcount_history.json
"""

import os
import csv
import json
from datetime import datetime
from pathlib import Path

def read_csv_file(file_path):
    """Read a CSV file and return the data as a list of dictionaries"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data.append({
                'month_year': row['month/year'],
                'headcount': int(row['headcount'])
            })
    return data

def extract_department_name(filename):
    """Extract department name from filename and map to full name"""
    name_mapping = {
        'compliance': 'Compliance',
        'coporate': 'Corporate',
        'finance_accounting': 'Finance & Accounting',
        'human_resource': 'Human Resources',
        'it_digital': 'Information Technology',
        'operations': 'Operations',
        'retail_banking': 'Retail Banking',
        'risk_management': 'Risk Management',
        'transformation_office': 'Transformation Office',
        'treasury_markets': 'Treasury & Markets'
    }
    
    base_name = filename.replace('.csv', '')
    return name_mapping.get(base_name, base_name.title())

def calculate_growth_rate(data):
    """Calculate growth rate from first to last entry"""
    if len(data) < 2:
        return 0
    first_headcount = data[0]['headcount']
    last_headcount = data[-1]['headcount']
    return round(((last_headcount - first_headcount) / first_headcount) * 100, 2)

def get_peak_headcount(data):
    """Get the peak headcount and when it occurred"""
    if not data:
        return None, None
    peak_entry = max(data, key=lambda x: x['headcount'])
    return peak_entry['headcount'], peak_entry['month_year']

def generate_headcount_json():
    """Main function to generate the JSON file"""
    
    # Get the sample directory path
    script_dir = Path(__file__).parent
    sample_dir = script_dir.parent / 'sample'
    
    # Dictionary to store all department data
    departments_data = {}
    total_current_headcount = 0
    
    # Department codes mapping
    dept_codes = {
        'Compliance': 'COM',
        'Corporate': 'COP',
        'Finance & Accounting': 'FIN',
        'Human Resources': 'HR',
        'Information Technology': 'IT',
        'Operations': 'OPS',
        'Retail Banking': 'RB',
        'Risk Management': 'RM',
        'Transformation Office': 'TO',
        'Treasury & Markets': 'TM'
    }
    
    # Process each CSV file
    csv_files = [f for f in os.listdir(sample_dir) if f.endswith('.csv')]
    
    for csv_file in csv_files:
        file_path = sample_dir / csv_file
        dept_name = extract_department_name(csv_file)
        
        # Read CSV data
        historical_data = read_csv_file(file_path)
        
        if historical_data:
            current_headcount = historical_data[-1]['headcount']
            total_current_headcount += current_headcount
            
            # Calculate metrics
            growth_rate = calculate_growth_rate(historical_data)
            peak_headcount, peak_month = get_peak_headcount(historical_data)
            avg_headcount = round(sum(entry['headcount'] for entry in historical_data) / len(historical_data), 1)
            
            departments_data[dept_name] = {
                'department_code': dept_codes.get(dept_name, dept_name[:3].upper()),
                'current_headcount': current_headcount,
                'growth_rate_percent': growth_rate,
                'average_headcount': avg_headcount,
                'peak_headcount': peak_headcount,
                'peak_month': peak_month,
                'data_points': len(historical_data),
                'historical_data': historical_data,
                'trends': {
                    'starting_headcount': historical_data[0]['headcount'],
                    'ending_headcount': current_headcount,
                    'total_growth': current_headcount - historical_data[0]['headcount'],
                    'period_covered': f"{historical_data[0]['month_year']} to {historical_data[-1]['month_year']}"
                }
            }
    
    # Calculate summary statistics
    current_headcounts = [dept['current_headcount'] for dept in departments_data.values()]
    largest_dept = max(departments_data.items(), key=lambda x: x[1]['current_headcount'])
    smallest_dept = min(departments_data.items(), key=lambda x: x[1]['current_headcount'])
    
    # Create the final JSON structure
    output_data = {
        'metadata': {
            'generated_timestamp': datetime.now().isoformat(),
            'data_source': 'CSV files from sample folder',
            'total_departments': len(departments_data),
            'data_period': f"{historical_data[0]['month_year']} to {historical_data[-1]['month_year']}" if historical_data else "N/A"
        },
        'summary': {
            'total_current_headcount': total_current_headcount,
            'average_headcount_per_department': round(total_current_headcount / len(departments_data), 1),
            'largest_department': {
                'name': largest_dept[0],
                'headcount': largest_dept[1]['current_headcount'],
                'percentage_of_total': round((largest_dept[1]['current_headcount'] / total_current_headcount) * 100, 2)
            },
            'smallest_department': {
                'name': smallest_dept[0],
                'headcount': smallest_dept[1]['current_headcount'],
                'percentage_of_total': round((smallest_dept[1]['current_headcount'] / total_current_headcount) * 100, 2)
            }
        },
        'departments': departments_data,
        'monthly_totals': {}
    }
    
    # Calculate monthly totals across all departments
    if historical_data:  # Use the last read historical_data as reference for dates
        for entry in historical_data:
            month_year = entry['month_year']
            total_for_month = 0
            for dept_data in departments_data.values():
                # Find the headcount for this month in each department
                for hist_entry in dept_data['historical_data']:
                    if hist_entry['month_year'] == month_year:
                        total_for_month += hist_entry['headcount']
                        break
            output_data['monthly_totals'][month_year] = total_for_month
    
    # Write to JSON file
    output_file = script_dir / 'department_headcount_history.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Successfully generated: {output_file}")
    print(f"📊 Total departments: {len(departments_data)}")
    print(f"👥 Total current headcount: {total_current_headcount}")
    print(f"📈 Data period: {output_data['metadata']['data_period']}")
    print(f"📁 Largest department: {largest_dept[0]} ({largest_dept[1]['current_headcount']} employees)")
    
    return output_file

if __name__ == "__main__":
    generate_headcount_json() 