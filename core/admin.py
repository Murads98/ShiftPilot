# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Employee, ShiftType, Shift, 
    EmployeeAvailability, ShiftAssignment, ScheduleConfig
)

class EmployeeAdmin(UserAdmin):
    # Add our custom fields to the admin
    fieldsets = UserAdmin.fieldsets + (
        ('Employee Info', {'fields': ('rank', 'work_start_date')}),
    )
    list_display = ('username', 'first_name', 'last_name', 'rank', 'work_start_date', 'is_staff')
    list_filter = UserAdmin.list_filter + ('rank',)
    search_fields = ('username', 'first_name', 'last_name', 'email')


class ShiftTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time')


class ShiftAdmin(admin.ModelAdmin):
    list_display = ('date', 'shift_type', 'total_required_staff')
    list_filter = ('date', 'shift_type')
    search_fields = ('notes',)


class EmployeeAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('employee', 'shift', 'availability_status')
    list_filter = ('availability_status', 'shift__date', 'shift__shift_type')
    search_fields = ('employee__username', 'employee__first_name', 'employee__last_name')


class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'shift', 'assigned_by', 'assigned_at')
    list_filter = ('shift__date', 'shift__shift_type')
    search_fields = ('employee__username', 'employee__first_name', 'employee__last_name')


class ScheduleConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'created_by')
    search_fields = ('name',)


# Register models
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(ShiftType, ShiftTypeAdmin)
admin.site.register(Shift, ShiftAdmin)
admin.site.register(EmployeeAvailability, EmployeeAvailabilityAdmin)
admin.site.register(ShiftAssignment, ShiftAssignmentAdmin)
admin.site.register(ScheduleConfig, ScheduleConfigAdmin)