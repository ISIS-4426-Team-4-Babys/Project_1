create_user_responses = {
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

get_user_by_id_responses = {
    404: {
        "description": "User not found",
        "content": {"application/json": {"example":
            {"detail": r"User with id={user_id} not found"}
        }},
    },
}

get_user_by_email_responses = {
    404: {
        "description": "User not found",
        "content": {"application/json": {"example":
            {"detail": r"User with email={email} not found"}
        }},
    },
}

update_user_responses = {
    404: {
        "description": "User not found",
        "content": {"application/json": {"example":
            {"detail": r"User with id={user_id} not found"}
        }},
    },
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

delete_user_responses = {
    404: {
        "description": "User not found",
        "content": {"application/json": {"example":
            {"detail": r"User with id={user_id} not found"}
        }},
    },
}

student_courses_responses = {
    400: {
        "description": "Invalid user role",
        "content": {"application/json": {"example":
            {"detail": r"User id={student_id} is not a student"}
        }},
    },
}

professor_courses_responses = {
    400: {
        "description": "Invalid user role",
        "content": {"application/json": {"example":
            {"detail": r"User id={professor_id} is not a professor"}
        }},
    },
}