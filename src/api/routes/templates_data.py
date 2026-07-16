DEFAULT_TEMPLATES = [
    {
        "template_id": "employment_agreement",
        "name": "Employment Agreement",
        "category": "contract",
        "description": "Standard employment contract per Industrial Relations Code, 2020",
        "variables": {
            "company_name": {"label": "Company Name", "type": "text", "required": True},
            "employee_name": {"label": "Employee Name", "type": "text", "required": True},
            "position": {"label": "Designation / Position", "type": "text", "required": True},
            "salary": {"label": "CTC / Monthly Salary (INR)", "type": "number", "required": True},
            "start_date": {"label": "Date of Joining", "type": "date", "required": True},
            "contract_type": {"label": "Contract Type", "type": "select", "options": ["Fixed Term", "Permanent", "Probationary", "Contractual"], "required": True},
            "duration_months": {"label": "Duration (months)", "type": "number", "required": False},
        }
    },
    {
        "template_id": "service_agreement",
        "name": "Service Agreement",
        "category": "contract",
        "description": "Service agreement / professional services contract",
        "variables": {
            "provider_name": {"label": "Service Provider", "type": "text", "required": True},
            "client_name": {"label": "Client", "type": "text", "required": True},
            "service_description": {"label": "Scope of Services", "type": "textarea", "required": True},
            "fee": {"label": "Service Fee (INR)", "type": "number", "required": True},
            "duration": {"label": "Duration / Term", "type": "text", "required": True},
        }
    },
    {
        "template_id": "board_resolution",
        "name": "Board Resolution",
        "category": "corporate",
        "description": "Company board resolution template",
        "variables": {
            "company_name": {"label": "Company Name", "type": "text", "required": True},
            "resolution_number": {"label": "Resolution Number", "type": "text", "required": True},
            "subject": {"label": "Subject / Purpose", "type": "textarea", "required": True},
            "effective_date": {"label": "Effective Date", "type": "date", "required": True},
        }
    },
    {
        "template_id": "official_letter",
        "name": "Official Letter",
        "category": "administrative",
        "description": "Formal business correspondence template",
        "variables": {
            "sender": {"label": "Sender / Organisation", "type": "text", "required": True},
            "recipient": {"label": "Recipient", "type": "text", "required": True},
            "subject": {"label": "Subject", "type": "text", "required": True},
            "content": {"label": "Body / Content", "type": "textarea", "required": True},
        }
    },
    {
        "template_id": "standing_orders",
        "name": "Standing Orders / HR Policy",
        "category": "hr",
        "description": "Internal HR standing orders per Industrial Relations Code, 2020",
        "variables": {
            "company_name": {"label": "Company Name", "type": "text", "required": True},
            "working_hours": {"label": "Working Hours", "type": "text", "required": True},
            "leave_policy": {"label": "Leave Policy", "type": "textarea", "required": False},
        }
    },
    {
        "template_id": "meeting_minutes",
        "name": "Meeting Minutes",
        "category": "corporate",
        "description": "Minutes of meeting template",
        "variables": {
            "meeting_title": {"label": "Meeting Title", "type": "text", "required": True},
            "date": {"label": "Date of Meeting", "type": "date", "required": True},
            "attendees": {"label": "Attendees", "type": "textarea", "required": True},
            "agenda": {"label": "Agenda / Minutes", "type": "textarea", "required": True},
        }
    },
    {
        "template_id": "notice",
        "name": "Notice",
        "category": "administrative",
        "description": "Internal / external notice template",
        "variables": {
            "company_name": {"label": "Company Name", "type": "text", "required": True},
            "subject": {"label": "Notice Subject", "type": "textarea", "required": True},
            "effective_date": {"label": "Effective Date", "type": "date", "required": True},
        }
    },
    {
        "template_id": "lease_agreement",
        "name": "Lease / Rental Agreement",
        "category": "contract",
        "description": "Commercial or residential lease agreement",
        "variables": {
            "landlord": {"label": "Lessor / Landlord", "type": "text", "required": True},
            "tenant": {"label": "Lessee / Tenant", "type": "text", "required": True},
            "address": {"label": "Property Address", "type": "text", "required": True},
            "rent": {"label": "Monthly Rent (INR)", "type": "number", "required": True},
            "deposit": {"label": "Security Deposit (INR)", "type": "number", "required": True},
            "duration": {"label": "Lease Term", "type": "text", "required": True},
        }
    }
]
