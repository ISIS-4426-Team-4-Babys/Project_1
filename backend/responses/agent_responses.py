create_agent_responses = {
    409: {
        "description": "Integrity constraint violation",
        "content": {"application/json": {"example":
            {"detail": r"Duplicate agent with name={name}"}
        }},
    },
}

get_agent_by_id_responses = {
    404: {
        "description": "Agent not found",
        "content": {"application/json": {"example":
            {"detail": r"Agent with id={agent_id} not found"}
        }},
    },
}

update_agent_responses = {
    404: {
        "description": "Agent not found",
        "content": {"application/json": {"example":
            {"detail": r"Agent with id={agent_id} not found"}
        }},
    },
    409: {
        "description": "Integrity constraint violation",
        "content": {"application/json": {"example":
            {"detail": r"Duplicate agent with name={name}"}
        }},
    },
}

delete_agent_responses = {
    404: {
        "description": "Agent not found",
        "content": {"application/json": {"example":
            {"detail": r"Agent with id={agent_id} not found"}
        }},
    },
}

agent_resources_responses = {
    404: {
        "description": "Agent not found",
        "content": {"application/json": {"example":
            {"detail": r"Agent with id={agent_id} not found"}
        }},
    },
}
