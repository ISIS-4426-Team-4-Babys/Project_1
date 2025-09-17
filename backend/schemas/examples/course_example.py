UUID_COURSE = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
UUID_TEACHER = "9f8f5e64-5717-4562-b3fc-2c963f66afa6"
UUID_AGENT = "11111111-2222-3333-4444-555555555555"
UUID_STUDENT = "77777777-8888-9999-aaaa-bbbbbbbbbbbb"

course_create_example = {
            "examples": [{
                "name": "Secure Coding 101",
                "code": "SEC-101",
                "department": "Cybersecurity",
                "description": "Intro to secure development practices",
                "taught_by": UUID_TEACHER
            }]
        }

course_update_example = {
            "examples": [{
                "code": "SEC-101H",
                "description": "Updated syllabus with OWASP Top 10"
            }]
        }

course_response_example = {
            "examples": [{
                "id": UUID_COURSE,
                "name": "Secure Coding 101",
                "code": "SEC-101",
                "department": "Cybersecurity",
                "description": "Intro to secure development practices",
                "taught_by": UUID_TEACHER,
                "teacher": {
                    "id": UUID_TEACHER,
                    "name": "Dr. Alice Mendoza",
                    "email": "alice.mendoza@example.edu"
                },
                "agents": [],
                "students": []
            }]
        }
