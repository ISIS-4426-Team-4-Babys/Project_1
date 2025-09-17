create_course_responses = {
    400: {
        "description": "Duplicate course",
        "content": {"application/json": {"example":
            {"detail": r"Duplicate course with code={course_code}"}
        }},
    },
    409: {
        "description": "Integrity constraint violation",
        "content": {"application/json": {"example":
            {"detail": r"Integrity constraint violation: {constraint_name}"}
        }},
    },
}

get_course_by_id_responses = {
    404: {
        "description": "Course not found",
        "content": {"application/json": {"example":
            {"detail": r"Course with id={course_id} not found"}
        }},
    },
}

update_course_responses = {
    404: {
        "description": "Course not found",
        "content": {"application/json": {"example":
            {"detail": r"Course with id={course_id} not found"}
        }},
    },
    400: {
        "description": "Duplicate course",
        "content": {"application/json": {"example":
            {"detail": r"Duplicate course with code={course_code}"}
        }},
    },
    409: {
        "description": "Integrity constraint violation",
        "content": {"application/json": {"example":
            {"detail": r"Integrity constraint violation: {constraint_name}"}
        }},
    },
}

delete_course_responses = {
    404: {
        "description": "Course not found",
        "content": {"application/json": {"example":
            {"detail": r"Course with id={course_id} not found"}
        }},
    },
}

enroll_student_responses = {
    400: {
        "description": "Invalid user role",
        "content": {"application/json": {"example":
            {"detail": r"User id={student_id} is not a student"}
        }},
    },
    404: {
        "description": "Course not found",
        "content": {"application/json": {"example":
            {"detail": r"Course with id={course_id} not found"}
        }},
    },
}

unenroll_student_responses = {
    400: {
        "description": "Invalid user role",
        "content": {"application/json": {"example":
            {"detail": r"User id={student_id} is not a student"}
        }},
    },
    404: {
        "description": "Course not found",
        "content": {"application/json": {"example":
            {"detail": r"Course with id={course_id} not found"}
        }},
    },
}
