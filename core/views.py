# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.utils import timezone
from django.db.models import Q, Count, F
from django.contrib import messages
from datetime import datetime, timedelta
import json
from .claude_scheduler import ClaudeScheduler

from .models import (
    Employee, ShiftType, Shift,
    EmployeeAvailability, ShiftAssignment, ScheduleConfig, AvailabilityChoice
)
from .forms import (
    EmployeeCreationForm, ShiftTypeForm, ShiftForm, 
    AvailabilityForm, BulkAvailabilityForm, ScheduleConfigForm, ShiftAssignmentForm
)


# Helper function to check if user is manager
def is_manager(user):
    return user.is_staff or user.rank >= 4


# Dashboard Views
@login_required
def dashboard(request):
    """Main dashboard view - shows different content based on user role"""
    # Get upcoming shifts for this user
    upcoming_shifts = ShiftAssignment.objects.filter(
        employee=request.user,
        shift__date__gte=timezone.now().date()
    ).order_by('shift__date', 'shift__shift_type__start_time')[:5]
    
    # Get pending availability requests
    pending_availability = Shift.objects.filter(
        date__gte=timezone.now().date()
    ).exclude(
        employee_availabilities__employee=request.user
    ).order_by('date', 'shift_type__start_time')[:5]
    
    context = {
        'upcoming_shifts': upcoming_shifts,
        'pending_availability': pending_availability,
    }
    
    # Add manager-specific data
    if is_manager(request.user):
        # Get recent schedule configurations
        recent_schedules = ScheduleConfig.objects.all().order_by('-created_at')[:3]

        # Get shifts that need more staff (compare assignment count vs required)
        understaffed_shifts = Shift.objects.filter(
            date__gte=timezone.now().date(),
            total_required_staff__gt=0
        ).annotate(
            assignment_count=Count('assignments')
        ).filter(
            assignment_count__lt=F('total_required_staff')
        ).order_by('date', 'shift_type__start_time')[:5]
        
        context.update({
            'recent_schedules': recent_schedules,
            'understaffed_shifts': understaffed_shifts,
        })
    
    return render(request, 'core/dashboard.html', context)


# Employee Views
class EmployeeListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View for managers to see all employees"""
    model = Employee
    context_object_name = 'employees'
    template_name = 'core/employee_list.html'
    ordering = ['last_name', 'first_name']
    
    def test_func(self):
        return is_manager(self.request.user)


class EmployeeDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View employee details"""
    model = Employee
    context_object_name = 'employee'
    template_name = 'core/employee_detail.html'
    
    def test_func(self):
        # Allow managers to view any employee, employees can only view themselves
        return is_manager(self.request.user) or self.get_object() == self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_object()
        
        # Get upcoming shifts for this employee
        today = timezone.now().date()
        upcoming_assignments = ShiftAssignment.objects.filter(
            employee=employee,
            shift__date__gte=today
        ).select_related('shift', 'shift__shift_type').order_by('shift__date', 'shift__shift_type__start_time')

        # Get availability preferences for this employee
        availability_preferences = EmployeeAvailability.objects.filter(
        employee=employee,
        shift__date__gte=today
        ).select_related('shift', 'shift__shift_type').order_by('shift__date', 'shift__shift_type__start_time')
        
        context['upcoming_shifts'] = upcoming_assignments
        context['availability_preferences'] = availability_preferences
        return context


class EmployeeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new employee (managers only)"""
    model = Employee
    form_class = EmployeeCreationForm
    template_name = 'core/employee_form.html'
    success_url = reverse_lazy('employee-list')
    
    def test_func(self):
        return is_manager(self.request.user)


class EmployeeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update employee information"""
    model = Employee
    fields = ['first_name', 'last_name', 'email', 'rank', 'work_start_date']
    template_name = 'core/employee_form.html'

    def test_func(self):
        # Allow managers to update any employee, employees can only update themselves
        return is_manager(self.request.user) or self.get_object() == self.request.user

    def get_success_url(self):
        return reverse('employee-detail', kwargs={'pk': self.object.pk})


class EmployeeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete an employee (managers only)"""
    model = Employee
    template_name = 'core/employee_confirm_delete.html'
    success_url = reverse_lazy('employee-list')

    def test_func(self):
        # Only managers can delete employees
        return is_manager(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_object()

        # Get counts of related data that will be affected
        future_assignments = ShiftAssignment.objects.filter(
            employee=employee,
            shift__date__gte=timezone.now().date()
        ).count()

        past_assignments = ShiftAssignment.objects.filter(
            employee=employee,
            shift__date__lt=timezone.now().date()
        ).count()

        context['future_assignments'] = future_assignments
        context['past_assignments'] = past_assignments
        return context

    def post(self, request, *args, **kwargs):
        employee = self.get_object()

        # Prevent deletion of currently logged-in user
        if employee == request.user:
            messages.error(request, 'You cannot delete your own account.')
            return redirect('employee-detail', pk=employee.pk)

        messages.success(request, f'Employee {employee.first_name} {employee.last_name} has been deleted.')
        return super().post(request, *args, **kwargs)


# Shift Type Views
class ShiftTypeListView(LoginRequiredMixin, ListView):
    """View all shift types"""
    model = ShiftType
    context_object_name = 'shift_types'
    template_name = 'core/shift_type_list.html'
    ordering = ['start_time']


from django.http import JsonResponse
from django.template.loader import render_to_string

class ShiftTypeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new shift type (managers only)"""
    model = ShiftType
    form_class = ShiftTypeForm
    template_name = 'core/shift_type_form.html'
    success_url = reverse_lazy('shift-type-list')
    
    def test_func(self):
        return is_manager(self.request.user)
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests - return form for AJAX or normal page"""
        self.object = None
        form = self.get_form()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request - return just the form HTML
            html = render_to_string('core/shift_type_modal_form.html', {
                'form': form,
            }, request=request)
            return JsonResponse({'html': html})
        
        # Normal request - return full page
        return self.render_to_response(self.get_context_data(form=form))
    
    def post(self, request, *args, **kwargs):
        """Handle POST requests - return JSON for AJAX or normal redirect"""
        self.object = None
        form = self.get_form()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request
            if form.is_valid():
                self.object = form.save()
                return JsonResponse({'success': True})
            else:
                # Form has errors - return form with errors
                html = render_to_string('core/shift_type_modal_form.html', {
                    'form': form,
                }, request=request)
                return JsonResponse({'success': False, 'html': html})
        
        # Normal request - use default behavior
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class ShiftTypeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update a shift type (managers only)"""
    model = ShiftType
    form_class = ShiftTypeForm
    template_name = 'core/shift_type_form.html'
    success_url = reverse_lazy('shift-type-list')
    
    def test_func(self):
        return is_manager(self.request.user)
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests - return form for AJAX or normal page"""
        self.object = self.get_object()
        form = self.get_form()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request - return just the form HTML
            html = render_to_string('core/shift_type_modal_form.html', {
                'form': form,
                'object': self.object,
                'is_update': True,
            }, request=request)
            return JsonResponse({'html': html})
        
        # Normal request - return full page
        return self.render_to_response(self.get_context_data(form=form))
    
    def post(self, request, *args, **kwargs):
        """Handle POST requests - return JSON for AJAX or normal redirect"""
        self.object = self.get_object()
        form = self.get_form()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request
            if form.is_valid():
                self.object = form.save()
                return JsonResponse({'success': True})
            else:
                # Form has errors - return form with errors
                html = render_to_string('core/shift_type_modal_form.html', {
                    'form': form,
                    'object': self.object,
                    'is_update': True,
                }, request=request)
                return JsonResponse({'success': False, 'html': html})
        
        # Normal request - use default behavior
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class ShiftTypeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a shift type (managers only)"""
    model = ShiftType
    template_name = 'core/shift_type_confirm_delete.html'
    success_url = reverse_lazy('shift-type-list')

    def test_func(self):
        return is_manager(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shift_type = self.get_object()

        # Count only future/current shifts using this shift type
        today = timezone.now().date()
        future_shifts = Shift.objects.filter(
            shift_type=shift_type,
            date__gte=today
        ).count()

        # Count past shifts for information only
        past_shifts = Shift.objects.filter(
            shift_type=shift_type,
            date__lt=today
        ).count()

        context['future_shifts'] = future_shifts
        context['past_shifts'] = past_shifts
        return context

    def post(self, request, *args, **kwargs):
        shift_type = self.get_object()
        today = timezone.now().date()

        # Only check for future/current shifts
        future_shifts_count = Shift.objects.filter(
            shift_type=shift_type,
            date__gte=today
        ).count()

        if future_shifts_count > 0:
            messages.error(
                request,
                f'Cannot delete shift type "{shift_type.name}". '
                f'It is being used by {future_shifts_count} upcoming shift(s). '
                f'Please delete or reassign those shifts first.'
            )
            return redirect('shift-type-list')

        messages.success(request, f'Shift type "{shift_type.name}" has been deleted.')
        return super().post(request, *args, **kwargs)


# Shift Views
class ShiftListView(LoginRequiredMixin, ListView):
    """View all shifts"""
    model = Shift
    context_object_name = 'shifts'
    template_name = 'core/shift_list.html'
    ordering = ['date', 'shift_type__start_time']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by date range if provided
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        else:
            # Default to current week
            today = timezone.now().date()
            start_of_week = today - timedelta(days=today.weekday())
            queryset = queryset.filter(date__gte=start_of_week)
        
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        else:
            # Default to current week + 1 week
            today = timezone.now().date()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=13)  # Two weeks
            queryset = queryset.filter(date__lte=end_of_week)
        
        return queryset


class ShiftCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new shift (managers only)"""
    model = Shift
    form_class = ShiftForm
    template_name = 'core/shift_form.html'
    success_url = reverse_lazy('shift-list')
    
    def test_func(self):
        return is_manager(self.request.user)


class ShiftUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update a shift (managers only)"""
    model = Shift
    form_class = ShiftForm
    template_name = 'core/shift_form.html'
    success_url = reverse_lazy('shift-list')

    def test_func(self):
        return is_manager(self.request.user)


class ShiftDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a shift (managers only)"""
    model = Shift
    template_name = 'core/shift_confirm_delete.html'
    success_url = reverse_lazy('shift-list')

    def test_func(self):
        return is_manager(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shift = self.get_object()

        # Get assignments for this shift
        assignments = ShiftAssignment.objects.filter(shift=shift).select_related('employee')

        context['assignments'] = assignments
        context['assignments_count'] = assignments.count()
        context['is_future'] = shift.date >= timezone.now().date()
        return context

    def post(self, request, *args, **kwargs):
        shift = self.get_object()
        shift_info = f"{shift.date.strftime('%B %d, %Y')} - {shift.shift_type.name}"

        messages.success(request, f'Shift "{shift_info}" has been deleted.')
        return super().post(request, *args, **kwargs)


# Availability Views
@login_required
def availability_submit(request, shift_id):
    """Submit availability for a single shift"""
    shift = get_object_or_404(Shift, id=shift_id)
    
    # Check if availability already exists
    availability, created = EmployeeAvailability.objects.get_or_create(
        employee=request.user,
        shift=shift,
        defaults={'availability_status': AvailabilityChoice.AVAILABLE}
    )
    
    if request.method == 'POST':
        form = AvailabilityForm(request.POST, instance=availability)
        if form.is_valid():
            availability = form.save(commit=False)
            availability.employee = request.user
            availability.shift = shift
            availability.save()
            messages.success(request, 'Availability updated successfully!')
            return redirect('availability-calendar')
    else:
        form = AvailabilityForm(instance=availability)
    
    return render(request, 'core/availability_form.html', {
        'form': form,
        'shift': shift
    })


@login_required
def availability_calendar(request):
    """Calendar view of shifts with availability options"""
    # Get date range (default to next 2 weeks)
    today = timezone.now().date()
    start_date = request.GET.get('start_date', today.strftime('%Y-%m-%d'))
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = start_date + timedelta(days=13)  # Two weeks
    
    # Get all shifts in this date range
    shifts = Shift.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date', 'shift_type__start_time')
    
    # Get user's availability for these shifts
    availabilities = EmployeeAvailability.objects.filter(
        employee=request.user,
        shift__in=shifts
    )
    
    # Create a dictionary of shift_id -> availability for easy lookup
    availability_dict = {a.shift_id: a for a in availabilities}
    
    if request.method == 'POST':
        form = BulkAvailabilityForm(request.POST, shifts=shifts)
        if form.is_valid():
            for shift in shifts:
                field_name = f'shift_{shift.id}'
                status = form.cleaned_data.get(field_name)
                if status:
                    EmployeeAvailability.objects.update_or_create(
                        employee=request.user,
                        shift=shift,
                        defaults={'availability_status': status}
                    )
            messages.success(request, 'Availability updated successfully!')
            return redirect('availability-calendar')
    else:
        # Pre-populate form with existing availability
        initial_data = {}
        for shift in shifts:
            if shift.id in availability_dict:
                initial_data[f'shift_{shift.id}'] = availability_dict[shift.id].availability_status
        
        form = BulkAvailabilityForm(initial=initial_data, shifts=shifts)
    
    # Group shifts by date for the calendar display
    shifts_by_date = {}
    date_range = [start_date + timedelta(days=i) for i in range(14)]
    
    for date in date_range:
        shifts_by_date[date] = []
    
    for shift in shifts:
        shifts_by_date[shift.date].append({
            'shift': shift,
            'availability': availability_dict.get(shift.id, None)
        })
    
    return render(request, 'core/availability_calendar.html', {
        'form': form,
        'shifts_by_date': shifts_by_date,
        'start_date': start_date,
        'end_date': end_date,
    })


# Schedule Generation Views
class ScheduleConfigCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new schedule configuration (managers only)"""
    model = ScheduleConfig
    form_class = ScheduleConfigForm
    template_name = 'core/schedule_config_form.html'
    success_url = reverse_lazy('schedule-config-list')
    
    def test_func(self):
        return is_manager(self.request.user)
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ScheduleConfigListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View all schedule configurations (managers only)"""
    model = ScheduleConfig
    context_object_name = 'configs'
    template_name = 'core/schedule_config_list.html'
    ordering = ['-created_at']
    
    def test_func(self):
        return is_manager(self.request.user)


@login_required
def schedule_view(request, config_id=None):
    # Get date range from GET parameters
    start_date_param = request.GET.get('start_date')
    end_date_param = request.GET.get('end_date')
    
    if start_date_param and end_date_param:
        start_date = datetime.strptime(start_date_param, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
    elif config_id:
        config = get_object_or_404(ScheduleConfig, id=config_id)
        start_date = config.start_date
        end_date = config.end_date
    else:
        # Default to current week
        today = timezone.now().date()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)

    
    # Get all shifts in this date range
    shifts = Shift.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date', 'shift_type__start_time')
    
    # Get all assignments for these shifts
    assignments = ShiftAssignment.objects.filter(
        shift__in=shifts
    ).select_related('employee', 'shift')
    
    # Create a dictionary of shift_id -> list of assignments for easy lookup
    assignments_by_shift = {}
    for assignment in assignments:
        if assignment.shift_id not in assignments_by_shift:
            assignments_by_shift[assignment.shift_id] = []
        assignments_by_shift[assignment.shift_id].append(assignment)
    
    # Group shifts by date for the calendar display
    shifts_by_date = {}
    date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    
    for date in date_range:
        shifts_by_date[date] = []
    
    for shift in shifts:
        shift_info = {
            'shift': shift,
            'assignments': assignments_by_shift.get(shift.id, []),
            'is_fully_staffed': len(assignments_by_shift.get(shift.id, [])) >= shift.total_required_staff
        }
        shifts_by_date[shift.date].append(shift_info)


    return render(request, 'core/schedule_view.html', {
        'shifts_by_date': shifts_by_date,
        'start_date': start_date,
        'end_date': end_date,
        'config': config if config_id else None,
    })


@login_required
def schedule_published(request):
    """Clean, employee-facing view of published schedules"""
    # Get date range from GET parameters
    start_date_param = request.GET.get('start_date')
    end_date_param = request.GET.get('end_date')

    if start_date_param and end_date_param:
        start_date = datetime.strptime(start_date_param, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
    else:
        # Default to current week
        today = timezone.now().date()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)

    # Get all shifts in this date range
    shifts = Shift.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date', 'shift_type__start_time')

    # Get all assignments for these shifts
    assignments = ShiftAssignment.objects.filter(
        shift__in=shifts
    ).select_related('employee', 'shift')

    # Create a dictionary of shift_id -> list of assignments
    assignments_by_shift = {}
    for assignment in assignments:
        if assignment.shift_id not in assignments_by_shift:
            assignments_by_shift[assignment.shift_id] = []
        assignments_by_shift[assignment.shift_id].append(assignment)

    # Group shifts by date for calendar display
    shifts_by_date = {}
    date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    for date in date_range:
        shifts_by_date[date] = []

    for shift in shifts:
        shift_info = {
            'shift': shift,
            'assignments': assignments_by_shift.get(shift.id, [])
        }
        shifts_by_date[shift.date].append(shift_info)

    return render(request, 'core/schedule_published.html', {
        'shifts_by_date': shifts_by_date,
        'start_date': start_date,
        'end_date': end_date,
    })


@login_required
def generate_schedule(request, config_id):
    """Generate schedule using Claude AI"""
    if not is_manager(request.user):
        messages.error(request, 'Only managers can generate schedules.')
        return redirect('dashboard')
    
    config = get_object_or_404(ScheduleConfig, id=config_id)
    
    if config.status != 'draft':
        messages.error(request, 'This schedule has already been processed.')
        return redirect('schedule-config-list')
    
    try:
        # Update status to processing
        config.status = 'processing'
        config.save()
        
        # Get shifts and employees for this schedule
        shifts = Shift.objects.filter(
            date__gte=config.start_date,
            date__lte=config.end_date
        ).select_related('shift_type')
        
        employees = Employee.objects.filter(is_active=True)
        
        # Use Claude to generate the schedule
        claude_scheduler = ClaudeScheduler()
        assignments, claude_response = claude_scheduler.generate_schedule(shifts, employees)
        
        # Save Claude's response to the config
        config.claude_response = claude_response
        config.save()
        
        # Create the assignments in the database
        for assignment_data in assignments:
            ShiftAssignment.objects.create(
                shift=assignment_data['shift'],
                employee=assignment_data['employee'],
                assigned_by=request.user
            )
        
        # Update config status
        config.status = 'completed'
        config.save()
        
        messages.success(request, f'Schedule generated successfully! {len(assignments)} assignments created.')
        return redirect('schedule-view', config_id=config.id)
        
    except Exception as e:
        config.status = 'error'
        config.save()
        messages.error(request, f'Error generating schedule: {str(e)}')
        return redirect('schedule-config-list')


@login_required
def publish_schedule(request, config_id):
    """Publish a schedule - making it visible to all employees"""
    if not is_manager(request.user):
        messages.error(request, 'Only managers can publish schedules.')
        return redirect('dashboard')
    
    config = get_object_or_404(ScheduleConfig, id=config_id)
    
    if config.status != 'completed':
        messages.error(request, 'Only completed schedules can be published.')
        return redirect('schedule-view', config_id=config.id)
    
    config.status = 'published'
    config.save()
    
    messages.success(request, 'Schedule published successfully!')
    return redirect('schedule-view', config_id=config.id)


# Assignment Management Views
@login_required
def assignment_create(request, shift_id=None):
    """Manually create a shift assignment (managers only)"""
    if not is_manager(request.user):
        messages.error(request, 'Only managers can create assignments.')
        return redirect('dashboard')
    
    initial_data = {}
    if shift_id:
        shift = get_object_or_404(Shift, id=shift_id)
        initial_data['shift'] = shift
    
    if request.method == 'POST':
        form = ShiftAssignmentForm(request.POST, initial=initial_data)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.assigned_by = request.user
            assignment.save()
            messages.success(request, 'Assignment created successfully!')
            return redirect('schedule-view')
    else:
        form = ShiftAssignmentForm(initial=initial_data)
    
    return render(request, 'core/assignment_form.html', {
        'form': form,
        'shift': shift
    })


@login_required
def assignment_delete(request, pk):
    """Delete a shift assignment (managers only)"""
    if not is_manager(request.user):
        messages.error(request, 'Only managers can delete assignments.')
        return redirect('dashboard')
    
    assignment = get_object_or_404(ShiftAssignment, id=pk)
    
    if request.method == 'POST':
        assignment.delete()
        messages.success(request, 'Assignment deleted successfully!')
        return redirect('schedule-view')
    
    return render(request, 'core/assignment_confirm_delete.html', {
        'assignment': assignment
    })

@login_required
def bulk_availability_test(request):
    """Quick tool for managers to set test availability data"""
    if not is_manager(request.user):
        messages.error(request, 'Only managers can use this tool.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Clear existing availability
        EmployeeAvailability.objects.all().delete()
        
        # Create some test availability data
        shifts = Shift.objects.all()[:5]  # Get first 5 shifts
        employees = Employee.objects.filter(is_active=True)
        
        import random
        statuses = ['available', 'prefer_not', 'unavailable']
        
        for shift in shifts:
            for employee in employees:
                status = random.choice(statuses)
                EmployeeAvailability.objects.create(
                    employee=employee,
                    shift=shift,
                    availability_status=status
                )
        
        messages.success(request, f'Created test availability data for {len(shifts)} shifts and {len(employees)} employees.')
        return redirect('dashboard')
    
    return render(request, 'core/bulk_availability_test.html')