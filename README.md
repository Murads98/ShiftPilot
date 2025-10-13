# ShiftPilot

**AI-Powered Employee Shift Scheduling System**

ShiftPilot is a Django web application that uses Claude AI (Anthropic's language model) to intelligently generate work shift schedules for employees, balancing business requirements with employee availability preferences.

## Features

### Core Functionality
- **Employee Management**: Track employees with customizable ranks (Junior, Regular, Senior, Team Leader)
- **Shift Types**: Define flexible shift types (Morning, Evening, Night) with specific time periods
- **Availability System**: Employees can mark their availability as Available, Prefer Not, or Unavailable
- **AI-Powered Scheduling**: Uses Claude 3.5 Sonnet to generate optimal shift assignments
- **Schedule Management**: Create, review, and publish schedules with full audit trails

### Key Highlights
- **Intelligent Assignment**: Claude AI considers employee availability, rank requirements, and fair distribution
- **Rank-Based Requirements**: Specify how many employees of each rank are needed per shift
- **Conflict Detection**: Prevents double-booking and validates shift assignments
- **Manager Dashboard**: Quick overview of understaffed shifts and pending schedules
- **Employee Dashboard**: View upcoming shifts and submit availability preferences

## Technology Stack

- **Backend**: Django 5.2.1 (Python)
- **Database**: SQLite
- **AI Integration**: Anthropic Claude API
- **Authentication**: Django's built-in auth system with custom Employee model

## Setup Instructions

### Prerequisites
- Python 3.10 or higher
- Git
- Anthropic API key ([Get one here](https://console.anthropic.com/))

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ShiftPilot
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy the example file
   cp .env.example .env

   # Edit .env and add your keys
   # - SECRET_KEY: Django secret key (generate a new one for production)
   # - ANTHROPIC_API_KEY: Your Anthropic API key
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main app: http://localhost:8000/
   - Admin panel: http://localhost:8000/admin/

## Usage Guide

### For Managers

1. **Set up shift types**: Define your shift patterns (e.g., Morning 8am-4pm, Evening 4pm-12am)
2. **Create shifts**: Add shifts for specific dates with staffing requirements
3. **Create employees**: Add employees with their ranks
4. **Collect availability**: Employees submit their availability preferences
5. **Generate schedule**: Create a schedule configuration and let Claude AI generate assignments
6. **Review & publish**: Review the AI-generated schedule and publish it to employees

### For Employees

1. **Login**: Access your personal dashboard
2. **Submit availability**: Mark your availability for upcoming shifts
3. **View schedule**: See your assigned shifts once published

## Project Structure

```
ShiftPilot/
├── core/                   # Main application
│   ├── models.py          # Database models (Employee, Shift, etc.)
│   ├── views.py           # View logic and request handling
│   ├── forms.py           # Form definitions and validation
│   ├── urls.py            # URL routing
│   ├── admin.py           # Django admin configuration
│   └── claude_scheduler.py # AI scheduling integration
├── shiftpilot/            # Project configuration
│   ├── settings.py        # Django settings
│   └── urls.py            # Root URL configuration
├── templates/             # HTML templates
├── static/               # CSS, JavaScript, images
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── manage.py            # Django management script
```

## AI Integration

ShiftPilot uses Claude 3.5 Sonnet to generate optimal shift schedules. The AI considers:

- **Employee availability preferences** (respects unavailable, minimizes prefer-not)
- **Rank requirements** (ensures shifts have appropriately skilled staff)
- **Total staffing needs** (meets minimum staff requirements)
- **Fair distribution** (balances shifts across employees)

Claude's reasoning is saved with each schedule for transparency and review.

## Development

This project was developed as a final year project demonstrating:
- Full-stack web development with Django
- AI/LLM integration for complex scheduling problems
- User authentication and authorization
- Database design and modeling
- Form validation and error handling
- Modern web development practices (environment variables, version control)

## Future Enhancements

- Email notifications for shift assignments
- Shift swap requests between employees
- Time-off request system
- Analytics dashboard (overtime tracking, fairness metrics)
- Mobile-responsive design improvements
- Export schedules to PDF/Excel

## License

This is an academic project developed for educational purposes.

## Author

Morad - Final Year Project

## Acknowledgments

- Anthropic for Claude AI API
- Django community for excellent documentation
- [Add your university/professor if required]
