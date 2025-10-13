from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class Employee(AbstractUser):
    """
    Extended user model that includes basic employee information
    """
    # Keep essential fields from AbstractUser (username, password, etc.)
    
    # Employee rank (seniority/skill level)
    RANK_CHOICES = [
        (1, 'Junior'),
        (2, 'Regular'),
        (3, 'Senior'),
        (4, 'Team Leader'),
    ]
    rank = models.IntegerField(choices=RANK_CHOICES, default=1)
    
    # Work start date
    work_start_date = models.DateField(null=True, blank=True)
    
    # Method to check if user is a manager
    def is_manager(self):
        return self.is_staff or self.rank >= 4
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} (ID: {self.id})"


class ShiftType(models.Model):
    """
    Defines different types of shifts (e.g., Morning, Evening, Night)
    """
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    def __str__(self):
        return f"{self.name} ({self.start_time}-{self.end_time})"


class Shift(models.Model):
    """
    A specific shift on a specific date
    """
    date = models.DateField()
    shift_type = models.ForeignKey(ShiftType, on_delete=models.CASCADE)
    
    # Required staff counts by rank
    total_required_staff = models.IntegerField(default=1)
    required_rank_1 = models.IntegerField(default=0)
    required_rank_2 = models.IntegerField(default=0)
    required_rank_3 = models.IntegerField(default=0)
    required_rank_4 = models.IntegerField(default=0)
    
    notes = models.TextField(blank=True)

    def clean(self):
        """
        Validate that rank requirements add up to total required staff
        """
        super().clean()
        
        # Calculate total rank requirements
        total_rank_requirements = (
            (self.required_rank_1 or 0) +
            (self.required_rank_2 or 0) +
            (self.required_rank_3 or 0) +
            (self.required_rank_4 or 0)
        )
        
        # Check if rank requirements match total staff
        if total_rank_requirements != self.total_required_staff:
            raise ValidationError({
                'total_required_staff': f'Total required staff ({self.total_required_staff}) must equal the sum of rank requirements ({total_rank_requirements}). '
            })
    
    def __str__(self):
        return f"{self.date} - {self.shift_type.name}"
    
    class Meta:
        unique_together = ('date', 'shift_type')


class AvailabilityChoice(models.TextChoices):
    AVAILABLE = 'available', 'Available'
    PREFER_NOT = 'prefer_not', 'Prefer Not'
    UNAVAILABLE = 'unavailable', 'Unavailable'


class EmployeeAvailability(models.Model):
    """
    Records an employee's availability for a specific shift
    """
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='availabilities')
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='employee_availabilities')
    availability_status = models.CharField(
        max_length=20,
        choices=AvailabilityChoice.choices,
        default=AvailabilityChoice.AVAILABLE
    )
    
    class Meta:
        unique_together = ('employee', 'shift')


class ShiftAssignment(models.Model):
    """
    Records the assignment of an employee to a specific shift
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='assigned_shifts')
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='assignments')
    assigned_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='shift_assignments_made')
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.employee} assigned to {self.shift}"
    
    class Meta:
        unique_together = ('employee', 'shift')


class ScheduleConfig(models.Model):
    """
    Stores configuration for schedule generation
    """
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    claude_response = models.TextField(blank=True, null=True, help_text="Claude's reasoning for the schedule")
    
    # Configuration for the AI scheduling algorithm (stored as JSON)
    algorithm_config = models.JSONField(default=dict)
    
    # Who created this configuration
    created_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='schedule_configs')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Status tracking
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('published', 'Published'),
        ('error', 'Error'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"
