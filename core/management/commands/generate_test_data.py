from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, time
import random
from core.models import (
    Employee, ShiftType, Shift, EmployeeAvailability,
    AvailabilityChoice
)


class Command(BaseCommand):
    help = 'Generate test data for ShiftPilot (employees, shifts, availability)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            # Don't delete superusers
            Employee.objects.filter(is_superuser=False).delete()
            ShiftType.objects.all().delete()
            Shift.objects.all().delete()
            EmployeeAvailability.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Data cleared'))

        self.stdout.write(self.style.SUCCESS('Generating test data...'))

        # Create employees
        employees = self.create_employees()
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(employees)} employees'))

        # Create shift types
        shift_types = self.create_shift_types()
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(shift_types)} shift types'))

        # Create shifts for the next 2 weeks
        shifts = self.create_shifts(shift_types)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(shifts)} shifts'))

        # Create availability data
        availability_count = self.create_availability(employees, shifts)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {availability_count} availability entries'))

        self.stdout.write(self.style.SUCCESS('\n=== Test Data Summary ==='))
        self.stdout.write(f'Employees: {len(employees)}')
        self.stdout.write(f'Shift Types: {len(shift_types)}')
        self.stdout.write(f'Shifts: {len(shifts)}')
        self.stdout.write(f'Availability Entries: {availability_count}')
        self.stdout.write(self.style.SUCCESS('\n✓ Test data generation complete!'))
        self.stdout.write(self.style.WARNING('\nYou can now use the AI scheduler to generate assignments.'))

    def create_employees(self):
        """Create diverse set of employees with different ranks"""
        employees_data = [
            # Team Leaders (Rank 4)
            {'username': 'sarah_johnson', 'first_name': 'Sarah', 'last_name': 'Johnson', 'rank': 4, 'email': 'sarah.j@example.com'},
            {'username': 'michael_brown', 'first_name': 'Michael', 'last_name': 'Brown', 'rank': 4, 'email': 'michael.b@example.com'},

            # Senior (Rank 3)
            {'username': 'emily_davis', 'first_name': 'Emily', 'last_name': 'Davis', 'rank': 3, 'email': 'emily.d@example.com'},
            {'username': 'james_wilson', 'first_name': 'James', 'last_name': 'Wilson', 'rank': 3, 'email': 'james.w@example.com'},
            {'username': 'olivia_garcia', 'first_name': 'Olivia', 'last_name': 'Garcia', 'rank': 3, 'email': 'olivia.g@example.com'},

            # Regular (Rank 2)
            {'username': 'david_martinez', 'first_name': 'David', 'last_name': 'Martinez', 'rank': 2, 'email': 'david.m@example.com'},
            {'username': 'sophia_rodriguez', 'first_name': 'Sophia', 'last_name': 'Rodriguez', 'rank': 2, 'email': 'sophia.r@example.com'},
            {'username': 'daniel_lopez', 'first_name': 'Daniel', 'last_name': 'Lopez', 'rank': 2, 'email': 'daniel.l@example.com'},
            {'username': 'ava_hernandez', 'first_name': 'Ava', 'last_name': 'Hernandez', 'rank': 2, 'email': 'ava.h@example.com'},
            {'username': 'william_gonzalez', 'first_name': 'William', 'last_name': 'Gonzalez', 'rank': 2, 'email': 'william.g@example.com'},

            # Junior (Rank 1)
            {'username': 'isabella_perez', 'first_name': 'Isabella', 'last_name': 'Perez', 'rank': 1, 'email': 'isabella.p@example.com'},
            {'username': 'ethan_sanchez', 'first_name': 'Ethan', 'last_name': 'Sanchez', 'rank': 1, 'email': 'ethan.s@example.com'},
            {'username': 'mia_ramirez', 'first_name': 'Mia', 'last_name': 'Ramirez', 'rank': 1, 'email': 'mia.r@example.com'},
            {'username': 'alexander_torres', 'first_name': 'Alexander', 'last_name': 'Torres', 'rank': 1, 'email': 'alex.t@example.com'},
            {'username': 'charlotte_flores', 'first_name': 'Charlotte', 'last_name': 'Flores', 'rank': 1, 'email': 'charlotte.f@example.com'},
        ]

        employees = []
        work_start_base = timezone.now().date() - timedelta(days=365)

        for i, emp_data in enumerate(employees_data):
            # Check if employee already exists
            if Employee.objects.filter(username=emp_data['username']).exists():
                employee = Employee.objects.get(username=emp_data['username'])
            else:
                employee = Employee.objects.create_user(
                    username=emp_data['username'],
                    password='password123',  # Default password for testing
                    first_name=emp_data['first_name'],
                    last_name=emp_data['last_name'],
                    email=emp_data['email'],
                    rank=emp_data['rank'],
                    work_start_date=work_start_base + timedelta(days=i*30),
                    is_staff=emp_data['rank'] >= 4  # Team leaders are staff
                )
            employees.append(employee)

        return employees

    def create_shift_types(self):
        """Create common shift types"""
        shift_types_data = [
            {'name': 'Morning Shift', 'start_time': time(6, 0), 'end_time': time(14, 0)},
            {'name': 'Day Shift', 'start_time': time(9, 0), 'end_time': time(17, 0)},
            {'name': 'Evening Shift', 'start_time': time(14, 0), 'end_time': time(22, 0)},
            {'name': 'Night Shift', 'start_time': time(22, 0), 'end_time': time(6, 0)},
        ]

        shift_types = []
        for st_data in shift_types_data:
            shift_type, created = ShiftType.objects.get_or_create(
                name=st_data['name'],
                defaults={
                    'start_time': st_data['start_time'],
                    'end_time': st_data['end_time']
                }
            )
            shift_types.append(shift_type)

        return shift_types

    def create_shifts(self, shift_types):
        """Create shifts for the next 2 weeks"""
        shifts = []
        today = timezone.now().date()

        # Create shifts for next 14 days
        for day_offset in range(14):
            date = today + timedelta(days=day_offset)
            weekday = date.weekday()  # 0=Monday, 6=Sunday

            # Determine which shifts to create based on day of week
            if weekday < 5:  # Monday-Friday
                # Weekdays: Morning, Day, and Evening shifts
                shift_configs = [
                    {'shift_type': shift_types[0], 'staff': 3, 'r1': 1, 'r2': 1, 'r3': 0, 'r4': 1},  # Morning: 1 Junior, 1 Regular, 1 Lead
                    {'shift_type': shift_types[1], 'staff': 4, 'r1': 1, 'r2': 2, 'r3': 1, 'r4': 0},  # Day: 1 Junior, 2 Regular, 1 Senior
                    {'shift_type': shift_types[2], 'staff': 3, 'r1': 1, 'r2': 1, 'r3': 1, 'r4': 0},  # Evening: 1 Junior, 1 Regular, 1 Senior
                ]
            else:  # Weekend
                # Weekends: Reduced shifts
                shift_configs = [
                    {'shift_type': shift_types[1], 'staff': 2, 'r1': 0, 'r2': 1, 'r3': 1, 'r4': 0},  # Day: 1 Regular, 1 Senior
                    {'shift_type': shift_types[2], 'staff': 2, 'r1': 1, 'r2': 0, 'r3': 1, 'r4': 0},  # Evening: 1 Junior, 1 Senior
                ]

            for config in shift_configs:
                shift, created = Shift.objects.get_or_create(
                    date=date,
                    shift_type=config['shift_type'],
                    defaults={
                        'total_required_staff': config['staff'],
                        'required_rank_1': config['r1'],
                        'required_rank_2': config['r2'],
                        'required_rank_3': config['r3'],
                        'required_rank_4': config['r4'],
                    }
                )
                if created:
                    shifts.append(shift)

        return shifts

    def create_availability(self, employees, shifts):
        """Create realistic availability data"""
        count = 0

        for shift in shifts:
            for employee in employees:
                # Create availability for ~80% of employee-shift combinations
                if random.random() < 0.8:
                    # Weight availability towards "available"
                    weights = [0.7, 0.2, 0.1]  # 70% available, 20% prefer not, 10% unavailable
                    status = random.choices(
                        [AvailabilityChoice.AVAILABLE, AvailabilityChoice.PREFER_NOT, AvailabilityChoice.UNAVAILABLE],
                        weights=weights
                    )[0]

                    # Some realistic scenarios:
                    # - Junior employees less likely to be unavailable
                    if employee.rank == 1 and status == AvailabilityChoice.UNAVAILABLE:
                        if random.random() < 0.5:  # 50% chance to change to "prefer not"
                            status = AvailabilityChoice.PREFER_NOT

                    # - Team leaders more likely to be available
                    if employee.rank == 4 and status == AvailabilityChoice.UNAVAILABLE:
                        if random.random() < 0.7:  # 70% chance to change to "available"
                            status = AvailabilityChoice.AVAILABLE

                    # - Night shifts generally less preferred
                    if shift.shift_type.name == 'Night Shift':
                        if random.random() < 0.4 and status == AvailabilityChoice.AVAILABLE:
                            status = AvailabilityChoice.PREFER_NOT

                    EmployeeAvailability.objects.get_or_create(
                        employee=employee,
                        shift=shift,
                        defaults={'availability_status': status}
                    )
                    count += 1

        return count
