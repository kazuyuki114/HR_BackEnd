from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'departments', views.DepartmentViewSet, basename='department')
router.register(r'employees', views.EmployeeViewSet, basename='employee')


urlpatterns = [
    # ViewSet URLs (provides full CRUD with additional actions)
    path('', include(router.urls)),
    
    # Additional API endpoints
] 