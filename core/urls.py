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
    path('employees/<int:pk>/delete/', views.EmployeeDeleteView.as_view(), name='employee-delete'),
    
    # Shift Type URLs
    path('shift-types/', views.ShiftTypeListView.as_view(), name='shift-type-list'),
    path('shift-types/new/', views.ShiftTypeCreateView.as_view(), name='shift-type-create'),
    path('shift-types/<int:pk>/update/', views.ShiftTypeUpdateView.as_view(), name='shift-type-update'),
    path('shift-types/<int:pk>/delete/', views.ShiftTypeDeleteView.as_view(), name='shift-type-delete'),
    
    # Shift URLs
    path('shifts/', views.ShiftListView.as_view(), name='shift-list'),
    path('shifts/new/', views.ShiftCreateView.as_view(), name='shift-create'),
    path('shifts/<int:pk>/update/', views.ShiftUpdateView.as_view(), name='shift-update'),
    path('shifts/<int:pk>/delete/', views.ShiftDeleteView.as_view(), name='shift-delete'),
    
    # Availability URLs
    path('availability/', views.availability_calendar, name='availability-calendar'),
    path('availability/<int:shift_id>/', views.availability_submit, name='availability-submit'),
    path('availability/status/', views.availability_status, name='availability-status'),

    # Email Logs
    path('emails/logs/', views.email_log_list, name='email-log-list'),
    
    # Schedule URLs
    path('schedule/', views.schedule_view, name='schedule-view'),
    path('schedule/<int:config_id>/', views.schedule_view, name='schedule-view'),
    path('schedule/published/', views.schedule_published, name='schedule-published'),
    path('schedule/configs/', views.ScheduleConfigListView.as_view(), name='schedule-config-list'),
    path('schedule/configs/new/', views.ScheduleConfigCreateView.as_view(), name='schedule-config-create'),
    path('schedule/generate/<int:config_id>/', views.generate_schedule, name='generate-schedule'),
    path('schedule/publish/<int:config_id>/', views.publish_schedule, name='publish-schedule'),
    
    # Assignment URLs
    path('assignments/new/', views.assignment_create, name='assignment-create'),
    path('assignments/new/<int:shift_id>/', views.assignment_create, name='assignment-create-for-shift'),
    path('assignments/<int:pk>/delete/', views.assignment_delete, name='assignment-delete'),

    path('test/availability/', views.bulk_availability_test, name='bulk-availability-test'),

    # Shift Template URLs
    path('templates/', views.ShiftTemplateListView.as_view(), name='shift-template-list'),
    path('templates/new/', views.ShiftTemplateCreateView.as_view(), name='shift-template-create'),
    path('templates/<int:pk>/', views.ShiftTemplateDetailView.as_view(), name='shift-template-detail'),
    path('templates/<int:pk>/update/', views.ShiftTemplateUpdateView.as_view(), name='shift-template-update'),
    path('templates/<int:pk>/delete/', views.ShiftTemplateDeleteView.as_view(), name='shift-template-delete'),
    path('templates/<int:template_id>/items/new/', views.template_item_create, name='template-item-create'),
    path('templates/items/<int:pk>/update/', views.template_item_update, name='template-item-update'),
    path('templates/items/<int:pk>/delete/', views.template_item_delete, name='template-item-delete'),
    path('templates/apply/', views.apply_template, name='apply-template'),
]