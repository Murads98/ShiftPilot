# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Employee URLs
    path('employees/', views.EmployeeListView.as_view(), name='employee-list'),
    path('employees/<int:pk>/', views.EmployeeDetailView.as_view(), name='employee-detail'),
    path('employees/new/', views.EmployeeCreateView.as_view(), name='employee-create'),
    path('employees/<int:pk>/update/', views.EmployeeUpdateView.as_view(), name='employee-update'),
    
    # Shift Type URLs
    path('shift-types/', views.ShiftTypeListView.as_view(), name='shift-type-list'),
    path('shift-types/new/', views.ShiftTypeCreateView.as_view(), name='shift-type-create'),
    path('shift-types/<int:pk>/update/', views.ShiftTypeUpdateView.as_view(), name='shift-type-update'),
    
    # Shift URLs
    path('shifts/', views.ShiftListView.as_view(), name='shift-list'),
    path('shifts/new/', views.ShiftCreateView.as_view(), name='shift-create'),
    path('shifts/<int:pk>/update/', views.ShiftUpdateView.as_view(), name='shift-update'),
    
    # Availability URLs
    path('availability/', views.availability_calendar, name='availability-calendar'),
    path('availability/<int:shift_id>/', views.availability_submit, name='availability-submit'),
    
    # Schedule URLs
    path('schedule/', views.schedule_view, name='schedule-view'),
    path('schedule/<int:config_id>/', views.schedule_view, name='schedule-view'),
    path('schedule/configs/', views.ScheduleConfigListView.as_view(), name='schedule-config-list'),
    path('schedule/configs/new/', views.ScheduleConfigCreateView.as_view(), name='schedule-config-create'),
    path('schedule/generate/<int:config_id>/', views.generate_schedule, name='generate-schedule'),
    path('schedule/publish/<int:config_id>/', views.publish_schedule, name='publish-schedule'),
    
    # Assignment URLs
    path('assignments/new/', views.assignment_create, name='assignment-create'),
    path('assignments/new/<int:shift_id>/', views.assignment_create, name='assignment-create-for-shift'),
    path('assignments/<int:pk>/delete/', views.assignment_delete, name='assignment-delete'),

    path('test/availability/', views.bulk_availability_test, name='bulk-availability-test'),
]