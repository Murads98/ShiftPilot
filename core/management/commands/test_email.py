from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument(
            'recipient',
            type=str,
            help='Email address to send test email to'
        )

    def handle(self, *args, **options):
        recipient = options['recipient']

        self.stdout.write('Sending test email...')

        try:
            send_mail(
                subject='ShiftPilot Email Test',
                message='This is a test email from ShiftPilot. If you received this, your email configuration is working correctly!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )

            self.stdout.write(self.style.SUCCESS(f'✓ Test email sent successfully to {recipient}'))
            self.stdout.write('Check your inbox (and spam folder) for the email.')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to send email: {str(e)}'))
            self.stdout.write(self.style.WARNING('\nTroubleshooting tips:'))
            self.stdout.write('1. Check your EMAIL_HOST_USER in .env file')
            self.stdout.write('2. Check your EMAIL_HOST_PASSWORD (should be 16-character app password)')
            self.stdout.write('3. Make sure 2-Factor Authentication is enabled on your Gmail')
            self.stdout.write('4. Make sure you generated an App Password (not your regular password)')
