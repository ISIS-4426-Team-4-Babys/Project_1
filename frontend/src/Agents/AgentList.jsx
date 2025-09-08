import React, { useState } from "react";
import { Card, Form, ListGroup } from "react-bootstrap";
import { useLocation, useNavigate } from "react-router-dom";
import "./AgentList.css";
import Nav from "../Navbar/Nav.jsx";


export default function AgentList() {


    const navigate = useNavigate();
    const location = useLocation();
    const agents = location.state?.agents || [];
    const courseName = location.state?.courseName || 'Curso';

    const handleClick = (id, name) => {
        navigate('/chat', { state: { agentID: id, agentName: name, courseName: courseName } });
    };

    return (
        <Nav>
            <div className="item-list-container">
                <h2 style={{ fontWeight: 'bold', width: 'max-content', margin: '0 0 20px 0' }}>{courseName}</h2>
                <Card className="item-list-card">
                    <ListGroup variant="flush">
                        {agents.map((item) => (
                            <ListGroup.Item
                                key={item.id}
                                action
                                className="item-list-element"
                                onClick={() => handleClick(item.id, item.name)}
                            >
                                <div style={{ display: "flex", alignItems: "center", width: "100%" }}>
                                    <div style={{ flex: 1 }}>
                                        <h5 style={{ fontWeight: "bold", margin: 0 }}>{item.name}</h5>
                                        <p>{item.description}</p>
                                    </div>
                                    <Form.Check
                                        type="switch"
                                        id={`custom-switch-${item.id}`}
                                        disabled={true}
                                        checked={item.is_working}
                                        style={{ marginLeft: "auto" }}
                                    />
                                </div>
                            </ListGroup.Item>
                        ))}
                    </ListGroup>
                </Card>
            </div>
        </Nav>
    );
}
