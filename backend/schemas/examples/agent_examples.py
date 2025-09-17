UUID_AGENT = "11111111-2222-3333-4444-555555555555"
UUID_COURSE = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
UUID_RESOURCE = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

resource_response_example = {
            "examples": [{
                "id": UUID_RESOURCE,
                "name": "Week 1 - Secure Coding Slides",
                "filetype": "application/pdf",
                "filepath": "/data/resources/SEC-101/week1.pdf",
                "size": 2487310
            }]
        }

course_response_example = {
            "examples": [{
                "id": UUID_COURSE,
                "name": "Secure Coding 101",
                "code": "SEC-101",
                "department": "Cybersecurity",
                "description": "Intro to secure development practices"
            }]
        }

agent_create_example = {
            "examples": [{
                "name": "Agent Introduction",
                "description": "Answers FAQs and onboarding questions",
                "is_working": True,
                "system_prompt": "You are the CyberLearn course agent. Answer in Spanish, be concise and cite sources when possible.",
                "model": "gpt-4o-mini",
                "language": "es",
                "retrieval_k": 25,
                "associated_course": UUID_COURSE
            }]
        }

agent_update_example = {
            "examples": [{
                "description": "Adds grading rubric guidance",
                "is_working": False,
                "retrieval_k": 30
            }]
        }

agent_response_example = {
            "examples": [{
                "id": UUID_AGENT,
                "name": "Agent Introduction",
                "description": "Answers FAQs and onboarding questions",
                "is_working": True,
                "system_prompt": "You are the CyberLearn course agent. Answer in Spanish, be concise and cite sources when possible.",
                "model": "gpt-4o-mini",
                "language": "es",
                "retrieval_k": 25,
                "associated_course": UUID_COURSE,
                "course": {
                    "id": UUID_COURSE,
                    "name": "Secure Coding 101",
                    "code": "SEC-101",
                    "department": "Cybersecurity",
                    "description": "Intro to secure development practices"
                },
                "resources": []
            }]
        }