UUID_USER = "9f8f5e64-5717-4562-b3fc-2c963f66afa6"
UUID_COURSE = "3fa85f64-5717-4562-b3fc-2c963f66afa6"

user_create_example = {
            "examples": [{
                "name": "John Doe",
                "email": "john.doe@example.edu",
                "role": "student",
                "profile_image": "https://cdn.example.com/u/juan.png",
                "password": "S3cure!Passw0rd"
            }]
        }

user_update_example = {
            "examples": [{
                "name": "John Doe",
                "role": "professor",
                "password": "New!S3cureP4ss"
            }]
        }

user_response_example = {
            "examples": [{
                "id": UUID_USER,
                "name": "John Doe",
                "email": "john.doe@example.edu",
                "role": "student",
                "profile_image": "https://cdn.example.com/u/juan.png",
                "courses_taught": [],
                "courses_taken": []
            }]
        }

token_response_example = {
            "examples": [{
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }]
        }

login_request_example = {
            "examples": [{
                "email": "john.doe@example.edu",
                "password": "S3cure!Passw0rd"
            }]
        }

login_response_example = {
            "examples": [{
                "user": {
                    "id": UUID_USER,
                    "name": "John Doe",
                    "email": "john.doe@example.edu",
                    "role": "student",
                    "profile_image": "https://cdn.example.com/u/juan.png",
                    "courses_taught": [{
                        "id": UUID_COURSE,
                        "name": "Secure Coding 101",
                        "code": "SEC-101"
                    }],
                    "courses_taken": [{
                        "id": "7c6c1d2e-aaaa-bbbb-cccc-ddddeeeeffff",
                        "name": "Networks & Security",
                        "code": "NET-201"
                    }]
                },
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }]
        }