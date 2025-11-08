# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import (
    Employee, ShiftType, Shift,
    EmployeeAvailability, ShiftAssignment, ScheduleConfig, AvailabilityChoice,
    ShiftTemplate, ShiftTemplateItem
)
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime


class EmployeeCreationForm(UserCreationForm):
    """Form for creating new employees"""
    class Meta:
        model = Employee
        fields = ('username', 'first_name', 'last_name', 'email', 'rank', 'work_start_date')
        widgets = {
            'work_start_date': forms.DateInput(attrs={'type': 'date'}),
        }


class ShiftTypeForm(forms.ModelForm):
    """Form for creating/editing shift types"""
    class Meta:
        model = ShiftType
        fields = ('name', 'start_time', 'end_time')
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise ValidationError("End time must be after start time")
        
        return cleaned_data


class ShiftForm(forms.ModelForm):
    """Form for creating/editing shifts"""
    class Meta:
        model = Shift
        fields = ('date', 'shift_type', 'total_required_staff',
                 'required_rank_1', 'required_rank_2', 'required_rank_3', 'required_rank_4',
                 'notes')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make rank fields optional and set initial value to 0
        self.fields['required_rank_1'].required = False
        self.fields['required_rank_1'].initial = 0
        self.fields['required_rank_2'].required = False
        self.fields['required_rank_2'].initial = 0
        self.fields['required_rank_3'].required = False
        self.fields['required_rank_3'].initial = 0
        self.fields['required_rank_4'].required = False
        self.fields['required_rank_4'].initial = 0

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get('total_required_staff')
        r1 = cleaned_data.get('required_rank_1') or 0
        r2 = cleaned_data.get('required_rank_2') or 0
        r3 = cleaned_data.get('required_rank_3') or 0
        r4 = cleaned_data.get('required_rank_4') or 0

        # Set default values if empty
        cleaned_data['required_rank_1'] = r1
        cleaned_data['required_rank_2'] = r2
        cleaned_data['required_rank_3'] = r3
        cleaned_data['required_rank_4'] = r4

        sum_by_rank = r1 + r2 + r3 + r4

        if sum_by_rank > total:
            raise ValidationError("Sum of required staff by rank cannot exceed total required staff")

        return cleaned_data


class AvailabilityForm(forms.ModelForm):
    """Form for submitting employee availability"""
    class Meta:
        model = EmployeeAvailability
        fields = ('availability_status',)
        
    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop('employee', None)
        self.shift = kwargs.pop('shift', None)
        super().__init__(*args, **kwargs)
        
        # Use radio buttons for availability status
        self.fields['availability_status'].widget = forms.RadioSelect(
            choices=AvailabilityChoice.choices
        )


class BulkAvailabilityForm(forms.Form):
    """Form for submitting availability for multiple shifts at once"""
    # Will be dynamically populated with shift choices
    
    def __init__(self, *args, **kwargs):
        shifts = kwargs.pop('shifts', None)
        super().__init__(*args, **kwargs)
        
        if shifts:
            for shift in shifts:
                field_name = f'shift_{shift.id}'
                self.fields[field_name] = forms.ChoiceField(
                    label=f"{shift.date} - {shift.shift_type.name}",
                    choices=AvailabilityChoice.choices,
                    widget=forms.RadioSelect,
                    initial=AvailabilityChoice.AVAILABLE
                )


class ScheduleConfigForm(forms.ModelForm):
    """Form for creating a new schedule configuration"""
    class Meta:
        model = ScheduleConfig
        fields = ('name', 'start_date', 'end_date')
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError("End date must be after start date")
            
            # Verify schedule doesn't start in the past
            if start_date < timezone.now().date():
                raise ValidationError("Start date cannot be in the past")
            
            # Verify the date range isn't too long (e.g., 4 weeks max)
            date_difference = (end_date - start_date).days
            if date_difference > 28:
                raise ValidationError("Schedule period cannot exceed 4 weeks")
        
        return cleaned_data


class ShiftAssignmentForm(forms.ModelForm):
    """Form for manually assigning an employee to a shift"""
    class Meta:
        model = ShiftAssignment
        fields = ('employee', 'shift')
    
    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get('employee')
        shift = cleaned_data.get('shift')

        if employee and shift:
            # Check if employee already assigned to this shift
            existing = ShiftAssignment.objects.filter(employee=employee, shift=shift).exists()
            if existing:
                raise ValidationError("This employee is already assigned to this shift")

            # Check if employee is already assigned to ANY shift on the same day
            same_day_assignment = ShiftAssignment.objects.filter(
                employee=employee,
                shift__date=shift.date
            ).exclude(shift=shift).select_related('shift__shift_type').first()

            if same_day_assignment:
                raise ValidationError(
                    f"This employee is already assigned to another shift on {shift.date}: "
                    f"{same_day_assignment.shift.shift_type.name}"
                )

            # Check if shift has specific rank requirements
            # Count how many employees of each rank are already assigned
            existing_assignments = ShiftAssignment.objects.filter(shift=shift).select_related('employee')
            rank_counts = {1: 0, 2: 0, 3: 0, 4: 0}
            for assignment in existing_assignments:
                rank_counts[assignment.employee.rank] += 1

            # Check if adding this employee would exceed rank requirements or if we need different ranks
            employee_rank = employee.rank
            required_for_rank = getattr(shift, f'required_rank_{employee_rank}', 0)

            # If there are specific rank requirements, validate them
            if any([shift.required_rank_1, shift.required_rank_2, shift.required_rank_3, shift.required_rank_4]):
                # Check if this rank is still needed
                if required_for_rank > 0 and rank_counts[employee_rank] >= required_for_rank:
                    rank_name = dict(Employee.RANK_CHOICES).get(employee_rank, f'Rank {employee_rank}')
                    raise ValidationError(
                        f"This shift already has enough {rank_name} employees assigned "
                        f"({rank_counts[employee_rank]}/{required_for_rank})"
                    )

        return cleaned_data


class ShiftTemplateForm(forms.ModelForm):
    """Form for creating/editing shift templates"""
    class Meta:
        model = ShiftTemplate
        fields = ('name', 'description', 'is_active')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ShiftTemplateItemForm(forms.ModelForm):
    """Form for creating/editing individual template items"""
    class Meta:
        model = ShiftTemplateItem
        fields = ('weekday', 'shift_type', 'total_required_staff',
                 'required_rank_1', 'required_rank_2', 'required_rank_3', 'required_rank_4',
                 'notes')
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make rank fields optional and set initial value to 0
        self.fields['required_rank_1'].required = False
        self.fields['required_rank_1'].initial = 0
        self.fields['required_rank_2'].required = False
        self.fields['required_rank_2'].initial = 0
        self.fields['required_rank_3'].required = False
        self.fields['required_rank_3'].initial = 0
        self.fields['required_rank_4'].required = False
        self.fields['required_rank_4'].initial = 0

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get('total_required_staff')
        r1 = cleaned_data.get('required_rank_1') or 0
        r2 = cleaned_data.get('required_rank_2') or 0
        r3 = cleaned_data.get('required_rank_3') or 0
        r4 = cleaned_data.get('required_rank_4') or 0

        # Set default values if empty
        cleaned_data['required_rank_1'] = r1
        cleaned_data['required_rank_2'] = r2
        cleaned_data['required_rank_3'] = r3
        cleaned_data['required_rank_4'] = r4

        sum_by_rank = r1 + r2 + r3 + r4

        if sum_by_rank != total:
            raise ValidationError(
                f"Sum of required staff by rank ({sum_by_rank}) must equal total required staff ({total})"
            )

        return cleaned_data


class ApplyTemplateForm(forms.Form):
    """Form for applying a template to generate shifts"""
    template = forms.ModelChoiceField(
        queryset=ShiftTemplate.objects.filter(is_active=True),
        label="Select Template",
        help_text="Choose a weekly template to generate shifts"
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Start Date",
        help_text="First day of the period (should be a Monday for best results)"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="End Date",
        help_text="Last day of the period"
    )
    overwrite_existing = forms.BooleanField(
        required=False,
        initial=False,
        label="Overwrite existing shifts",
        help_text="If checked, existing shifts in this date range will be deleted before generating new ones"
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError("End date must be after start date")

            # Check the date range isn't too long
            date_difference = (end_date - start_date).days
            if date_difference > 84:  # ~12 weeks
                raise ValidationError("Date range cannot exceed 12 weeks")

            # Warn if start date is not a Monday
            if start_date.weekday() != 0:
                self.add_error('start_date', ValidationError(
                    "Warning: Start date is not a Monday. Template will apply based on the actual weekday.",
                    code='warning'
                ))

        return cleaned_data