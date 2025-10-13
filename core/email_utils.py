"""
Email utility functions for sending notifications
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import EmailLog


def send_email_notification(email_type, subject, recipient, context, sent_by=None, template_name=None):
    """
    Send an email notification and log it

    Args:
        email_type: Type of email (from EmailLog.EMAIL_TYPE_CHOICES)
        subject: Email subject line
        recipient: Employee object or email string
        context: Dictionary of context variables for the email template
        sent_by: Employee who triggered the email (optional)
        template_name: Template file name (optional, defaults to email_type)

    Returns:
        Boolean indicating success
    """
    # Get recipient email
    if hasattr(recipient, 'email'):
        recipient_email = recipient.email
        recipient_name = recipient.get_full_name() or recipient.username
    else:
        recipient_email = recipient
        recipient_name = ''

    # Determine template name
    if not template_name:
        template_name = f'emails/{email_type}.html'

    try:
        # Render HTML email
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)

        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )

        # Log successful email
        EmailLog.objects.create(
            email_type=email_type,
            subject=subject,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            sent_by=sent_by,
            success=True
        )

        return True

    except Exception as e:
        # Log failed email
        EmailLog.objects.create(
            email_type=email_type,
            subject=subject,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            sent_by=sent_by,
            success=False,
            error_message=str(e)
        )

        return False


def send_availability_reminder(employees, shifts, sent_by=None, request=None):
    """
    Send availability reminder to employees who haven't submitted

    Args:
        employees: QuerySet or list of Employee objects
        shifts: QuerySet or list of Shift objects they need to submit for
        sent_by: Employee who triggered the email
        request: HTTP request object for URL generation (optional)

    Returns:
        Tuple of (success_count, fail_count)
    """
    from django.conf import settings

    success_count = 0
    fail_count = 0

    for employee in employees:
        context = {
            'employee': employee,
            'shifts': shifts,
        }

        # Add request-like context if not provided
        if request:
            context['request'] = request
        else:
            # Create a mock request object for URL generation
            class MockRequest:
                def __init__(self):
                    self.scheme = 'http'

                def get_host(self):
                    return settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'

            context['request'] = MockRequest()

        subject = 'Reminder: Submit Your Availability'

        if send_email_notification('availability_reminder', subject, employee, context, sent_by):
            success_count += 1
        else:
            fail_count += 1

    return success_count, fail_count


def send_schedule_published_notification(employees, start_date, end_date, sent_by=None, request=None):
    """
    Notify employees that a new schedule has been published

    Args:
        employees: QuerySet or list of Employee objects
        start_date: Schedule start date
        end_date: Schedule end date
        sent_by: Employee who triggered the email
        request: HTTP request object for URL generation (optional)

    Returns:
        Tuple of (success_count, fail_count)
    """
    from django.conf import settings

    success_count = 0
    fail_count = 0

    for employee in employees:
        context = {
            'employee': employee,
            'start_date': start_date,
            'end_date': end_date,
        }

        # Add request-like context if not provided
        if request:
            context['request'] = request
        else:
            # Create a mock request object for URL generation
            class MockRequest:
                def __init__(self):
                    self.scheme = 'http'

                def get_host(self):
                    return settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'

            context['request'] = MockRequest()

        subject = f'New Schedule Published: {start_date.strftime("%b %d")} - {end_date.strftime("%b %d, %Y")}'

        if send_email_notification('schedule_published', subject, employee, context, sent_by):
            success_count += 1
        else:
            fail_count += 1

    return success_count, fail_count


def send_shift_assignment_notification(employee, assignments, sent_by=None, request=None):
    """
    Notify an employee about their shift assignments

    Args:
        employee: Employee object
        assignments: QuerySet or list of ShiftAssignment objects
        sent_by: Employee who triggered the email
        request: HTTP request object for URL generation (optional)

    Returns:
        Boolean indicating success
    """
    from django.conf import settings

    context = {
        'employee': employee,
        'assignments': assignments,
    }

    # Add request-like context if not provided
    if request:
        context['request'] = request
    else:
        # Create a mock request object for URL generation
        class MockRequest:
            def __init__(self):
                self.scheme = 'http'

            def get_host(self):
                return settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'

        context['request'] = MockRequest()

    subject = 'You\'ve Been Assigned to Shifts'

    return send_email_notification('shift_assigned', subject, employee, context, sent_by)
