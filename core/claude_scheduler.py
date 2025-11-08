import anthropic
from django.conf import settings
from .models import Shift, Employee, ShiftAssignment, EmployeeAvailability

class ClaudeScheduler:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    def generate_schedule(self, shifts, employees):
        """Generate schedule using Claude API"""
        
        # Build the prompt with all scheduling data
        prompt = self._build_scheduling_prompt(shifts, employees)
        
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Get Claude's response text
            claude_response_text = message.content[0].text
            
            # Parse Claude's response and create assignments
            assignments = self._parse_claude_response(claude_response_text, shifts)
            
            # Return BOTH assignments and Claude's response
            return assignments, claude_response_text
            
        except Exception as e:
            # Return empty assignments and error message
            return [], str(e)

    def _build_scheduling_prompt(self, shifts, employees):
        """Build the prompt for Claude"""
        
        # Get availability data
        availabilities = EmployeeAvailability.objects.filter(
            shift__in=shifts
        ).select_related('employee', 'shift')
        
        prompt = f"""You are an expert shift scheduler. Please create optimal shift assignments.

    EMPLOYEES:
    """
        
        for employee in employees:
            prompt += f"- {employee.username} (Rank {employee.rank})\n"
        
        prompt += f"\nSHIFTS TO SCHEDULE:\n"
        
        for shift in shifts:
            prompt += f"- ID:{shift.id} | {shift.date} {shift.shift_type.name} ({shift.shift_type.start_time}-{shift.shift_type.end_time})\n"
            prompt += f"  Required: {shift.total_required_staff} total staff"
            
            if shift.required_rank_1 or shift.required_rank_2 or shift.required_rank_3 or shift.required_rank_4:
                prompt += f" (R1:{shift.required_rank_1 or 0}, R2:{shift.required_rank_2 or 0}, R3:{shift.required_rank_3 or 0}, R4:{shift.required_rank_4 or 0})"
            prompt += f"\n"
        
        prompt += f"""
    EMPLOYEE AVAILABILITY:
    """
        
        for availability in availabilities:
            status = availability.availability_status
            prompt += f"- {availability.employee.username}: ID:{availability.shift.id} ({availability.shift.date} {availability.shift.shift_type.name}) = {status}\n"
        
        prompt += f"""
    Please assign employees to shifts following these rules:
    1. Respect employee availability (avoid 'unavailable', minimize 'prefer_not')
    2. Meet rank requirements for each shift
    3. Meet total staff requirements
    4. Distribute shifts fairly among employees
    5. CRITICAL: Each employee can only be assigned to ONE shift per day (not multiple shifts on the same day)

    IMPORTANT: Use the shift ID numbers in your response, not dates!

    Respond with assignments in this exact format:
    ASSIGNMENTS:
    ShiftID-EmployeeUsername
    ShiftID-EmployeeUsername
    ...

    For example:
    ASSIGNMENTS:
    7-john
    7-mary
    8-john
    """
        
        return prompt

    def _parse_claude_response(self, response_text, shifts):
        """Parse Claude's response into assignments"""
        assignments = []

        try:
            # Find the ASSIGNMENTS section
            if "ASSIGNMENTS:" in response_text:
                assignments_section = response_text.split("ASSIGNMENTS:")[1].strip()

                # Parse each assignment line
                for line in assignments_section.split('\n'):
                    line = line.strip()
                    if '-' in line and line:
                        try:
                            shift_id, username = line.split('-', 1)
                            shift_id = int(shift_id)

                            # Find the shift and employee
                            shift = next((s for s in shifts if s.id == shift_id), None)
                            employee = Employee.objects.filter(username=username).first()

                            if shift and employee:
                                assignments.append({
                                    'shift': shift,
                                    'employee': employee
                                })
                        except (ValueError, IndexError):
                            # Skip lines that can't be parsed
                            continue

            return assignments

        except Exception as e:
            # Log error but return empty list to avoid crashing
            return []