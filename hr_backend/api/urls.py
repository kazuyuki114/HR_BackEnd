from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'departments', views.DepartmentViewSet, basename='department')
router.register(r'employees', views.EmployeeViewSet, basename='employee')

# Available ViewSet endpoints:
# 
# DEPARTMENTS:
# GET /departments/ - List all departments (lightweight)
# POST /departments/ - Create new department  
# GET /departments/{id}/ - Get department details WITH ANALYTICS
# PUT /departments/{id}/ - Update department
# PATCH /departments/{id}/ - Partial update department
# DELETE /departments/{id}/ - Delete department
# GET /departments/{id}/employees/ - Get employees in department
# GET /departments/{id}/positions/ - Get positions in department  
# GET /departments/stats/ - Get basic stats for all departments
# GET /departments/analytics_all/ - Get detailed analytics for all departments
#
# EMPLOYEES (NEW!):
# GET /employees/ - List all employees (lightweight)
# POST /employees/ - Create new employee
# GET /employees/{id}/ - Get employee details WITH COMPREHENSIVE ANALYTICS
# PUT /employees/{id}/ - Update employee
# PATCH /employees/{id}/ - Partial update employee  
# DELETE /employees/{id}/ - Delete employee
# GET /employees/analytics_summary/ - Get analytics summary for all employees
#
# Query parameters for employees:
# ?department={id} - Filter by department
# ?status={ACTIVE|INACTIVE|ON_LEAVE|TERMINATED} - Filter by employment status
# ?position={id} - Filter by position

urlpatterns = [
    # ViewSet URLs (provides full CRUD with additional actions)
    path('', include(router.urls)),
    
    # Alternative direct API view URLs (if you prefer explicit routing)
    path('departments-list/', views.DepartmentListCreateView.as_view(), name='department-list-create'),
    path('departments-detail/<int:department_id>/', views.DepartmentDetailView.as_view(), name='department-detail'),
    
    # Additional API endpoints
    path('departments/summary/', views.department_summary, name='department-summary'),
    path('departments/managers/', views.active_managers, name='active-managers'),
] 