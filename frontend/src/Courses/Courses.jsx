import { Container, Row, Col, Card, Badge} from "react-bootstrap";
import "./Courses.css";
import React, { useEffect, useState } from "react";
import { useAuth } from '../Auth/AuthProvider.tsx';
import Nav from '../Navbar/Nav.jsx';
import { useNavigate } from "react-router-dom";



const taughtByLabel = (taught_by) => {
  if (!taught_by) return "Por asignar";
  const isPlaceholder = /^\s*\{\{.*\}\}\s*$/.test(taught_by);
  return isPlaceholder ? "Por asignar" : taught_by;
};

const CourseCard = ({ course, role }) => {

  const navigate = useNavigate();

  const handleCardClick = () => {
    if (role === 'professor') {
        navigate("/agentsT", { state: { agents: course.agents, courseId: course.id, courseName: course.name, courseCode: course.code } });
        return;
    } else if (role === 'student') {
        navigate("/agentsS", { state: { agents: course.agents, courseId: course.id, courseName: course.name, courseCode: course.code } });
        return;
    }
  };

  return (
    <>
      <Card className="course-card h-100 shadow-sm" onClick={handleCardClick}>
        <Card.Body>
          <div className="d-flex align-items-start justify-content-between mb-2">
            <Card.Title className="mb-0 course-title">{course.name}</Card.Title>
            <Badge bg="secondary" pill className="ms-2 flex-shrink-0">
              {course.code}
            </Badge>
          </div>

          <div className="mb-2">
            <Badge className="badge-soft">{course.department}</Badge>
          </div>

          <Card.Text className="course-desc line-clamp-3">
            {course.description}
          </Card.Text>

          {role === 'student' && (
            <div className="text-muted small mt-3">
              <span className="fw-semibold">Dictada por:</span>{" "}
              {taughtByLabel(course.teacher.name)}
            </div>
          )}
        </Card.Body>
      </Card>
    </>
  );
};

export default function Courses() {
    const [courses, setCourses] = useState([]);
    const [loading, setLoading] = useState(true);
    const { user, status, accessToken } = useAuth();


    useEffect(() => {
        async function fetchData() {
            try{
                if (status !== 'authenticated') return;
                const headers = {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`,
                };
    
                const response = await fetch(`api/users/${user?.role}/${user?.id}`, {
                    method: 'GET',
                    headers
                });
                const data = await response.json();
    
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to fetch courses');
                }
    
                setCourses(data || []);
            } catch (error) {
                alert(error);
            }  
        }

        fetchData().finally(() => setLoading(false));
    }, [accessToken, status, user]);

    if (loading) {
        return (
            <Container className="py-4">
                <div>Loading...</div>
            </Container>
        );
    }


    return (
            <Nav>
            <h2 className="mb-4" style={{ fontWeight: "bold" }}>Mis Cursos</h2>
            <Row xs={1} sm={2} md={3} lg={4} className="g-3">
                {courses.map((c, idx) => (
                    <Col key={`${c.
// @ts-ignore
                    code}-${idx}`}>
                        <CourseCard course={c} role={user?.role} />
                    </Col>
                ))}
            </Row>
        </Nav>
    );
}
