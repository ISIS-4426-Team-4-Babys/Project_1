register_responses = {
    400: {
        "description": "Duplicate user",
        "content": {"application/json": {"example": 
             {"detail": r"Duplicate user with email:{email}"}
        }},
    },
    409: {
        "description": "Integrity constraint violation",
        "content": {"application/json": {"example":
            {"detail": r"Duplicate user with name={name}"}
        }},
    },
}

login_responses = {
    401: {
        "description": "Invalid credentials",
        "content": {"application/json": {"example":
            {"detail": "Invalid email or password"}
        }},
    },
}
