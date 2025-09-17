UUID_AGENT = "11111111-2222-3333-4444-555555555555"
UUID_RESOURCE = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
ISO_TS = "2025-01-15T14:32:00Z"

agent_response_example = {
            "examples": [{
                "id": UUID_AGENT,
                "name": "Agent Introduction",
                "description": "Answers FAQs and onboarding questions",
                "is_working": True,
                "model": "gpt-4o-mini",
                "language": "es"
            }]
        }

resource_create_example = {
            "examples": [{
                "name": "Week 1 - Secure Coding Slides",
                "filetype": "application/pdf",
                "filepath": "/data/resources/SEC-101/week1.pdf",
                "size": 2487310,
                "timestamp": ISO_TS,
                "consumed_by": UUID_AGENT,
                "total_docs": 12
            }]
        }

resource_response_example = {
            "examples": [{
                "id": UUID_RESOURCE,
                "name": "Week 1 - Secure Coding Slides",
                "filetype": "application/pdf",
                "filepath": "/data/resources/SEC-101/week1.pdf",
                "size": 2487310,
                "timestamp": ISO_TS,  
                "consumed_by": UUID_AGENT,
                "agent": {
                    "id": UUID_AGENT,
                    "name": "Agent Introduction",
                    "description": "Answers FAQs and onboarding questions",
                    "is_working": True,
                    "model": "gpt-4o-mini",
                    "language": "es"
                }
            }]
        }