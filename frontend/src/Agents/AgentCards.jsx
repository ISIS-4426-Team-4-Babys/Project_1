import React, { useMemo, useState } from "react";
import {
  Button,
  Card,
  Col,
  Form,
  InputGroup,
  Modal,
  Row,
  Stack,
  Badge,
} from "react-bootstrap";
import { useLocation } from "react-router-dom";
import "./AgentsCards.css";
import Nav from "../Navbar/Nav.jsx";
import { useAuth } from "../Auth/AuthProvider.tsx";
import { set } from "date-fns";

/** ---- AddAgentModal ---- */
function AddAgentModal({ show, onHide, courseName, courseCode, courseId, setAgents }) {
    const { accessToken } = useAuth();

  const [form, setForm] = useState({
    name: "",
    description: "",
    is_working: true,
    system_prompt: "",
    model: "gpt-5",
    language: "es",
    retrieval_k: 5,
    resources: [],
  });
  const [resourceInput, setResourceInput] = useState("");
  const [resources, setResources] = useState([]);

  const update = (path, value) => {
    // Simple path updater: "course.name", "name", etc.
    setForm((prev) => {
      const next = { ...prev };
      next[path] = value;
      return next;
    });
  };

  const addResource = () => {
    const v = resourceInput.trim();
    if (!v) return;
    // @ts-ignore
    setForm((f) => ({ ...f, resources: [...f.resources, v] }));
    setResourceInput("");
  };

  const removeResource = (idx) => {
    setForm((f) => ({
      ...f,
      resources: f.resources.filter((_, i) => i !== idx),
    }));

    setResources((r) => r.filter((_, i) => i !== idx));
  };

  const onChangeFile = (e) => {
    setResourceInput(e.target.value);
    const file = e.target.files?.[0];
    if (file) {
      // @ts-ignore
      setResources((prev) => [...prev, file]);
    }
  };

  async function onSave(newAgent) {
    try{
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`
        };

        const response = await fetch('api/agents/', {
            method: 'POST',
            headers,
            body: JSON.stringify({...newAgent, associated_course: courseId})
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Failed to create agent');
        }
        setAgents((prev) => [data, ...prev]);
        for (const file of resources) {
            await uploadFiles(file, data.id, resources.length);
        }
        setResources([]);
    } catch (error) {
        alert("Error creating agent:" + error);
    }

  };

  async function uploadFiles(file, agent_id, docs) {
    const formData = new FormData();
    formData.append("file", file, file.name);
    formData.append("name", file.name);
    formData.append("consumed_by", String(agent_id));
    formData.append("total_docs", String(docs));

    try{
        const headers = {
            'Authorization': `Bearer ${accessToken}`
        };
        console.log(formData);

        const response = await fetch('api/resources/', {
            method: 'POST',
            headers,
            body: formData
        });
        const data = await response.json();
        console.log(data);

        if (!response.ok) {
            throw new Error(data.error || 'Failed to upload files');
        }
    } catch (error) {
        alert("Error uploading files:" + error);
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault();
    // Minimal validation
    if (
      !form.name ||
      !form.description ||
      !form.system_prompt

    ) {
      alert(
        "Por favor completa nombre, descripción, system prompt y nombre del curso."
      );
      return;
    }
    const payload = {
      ...form,
      retrieval_k: Number(form.retrieval_k) || 5,
    };
    onSave(payload);
    onHide();
    // Reset for next open
    setForm((prev) => ({
      ...prev,
      name: "",
      description: "",
      system_prompt: "",
      resources: [],
    }));
  };

  return (
    <Modal show={show} onHide={onHide} size="lg" centered scrollable>
      <Form onSubmit={handleSubmit}>
        <Modal.Header closeButton>
          <Modal.Title>Agregar agente</Modal.Title>
        </Modal.Header>
        <Modal.Body style={{ maxHeight: "70vh", overflowY: "auto" }}>
          <Stack gap={3}>
            <Row>
              <Col md={8}>
                <Form.Group className="mb-2">
                  <Form.Label>Nombre</Form.Label>
                  <Form.Control
                    value={form.name}
                    onChange={(e) => update("name", e.target.value)}
                    placeholder="Agente Administrativo"
                    required
                  />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-2">
                  <Form.Label>Estado</Form.Label>
                  <div className="d-flex align-items-center gap-2">
                    <Form.Check
                      type="switch"
                      id="is_working"
                      checked={form.is_working}
                      onChange={(e) => update("is_working", e.target.checked)}
                    />
                    <span>{form.is_working ? "Activo" : "Inactivo"}</span>
                  </div>
                </Form.Group>
              </Col>
            </Row>

            <Form.Group>
              <Form.Label>Descripción</Form.Label>
              <Form.Control
                as="textarea"
                rows={2}
                value={form.description}
                onChange={(e) => update("description", e.target.value)}
                placeholder="Agente con conocimiento del programa y estructura del curso"
                required
              />
            </Form.Group>

            <Form.Group>
              <Form.Label>System Prompt</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                value={form.system_prompt}
                onChange={(e) => update("system_prompt", e.target.value)}
                placeholder="Eres un agente administrativo..."
                required
              />
            </Form.Group>

            <Row>
              <Col md={4}>
                <Form.Group>
                  <Form.Label>Modelo</Form.Label>
                  <Form.Select
                    value={form.model}
                    onChange={(e) => update("model", e.target.value)}
                  >
                    <option value="gpt-5">gpt-5</option>
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group>
                  <Form.Label>Idioma</Form.Label>
                  <Form.Select
                    value={form.language}
                    onChange={(e) => update("language", e.target.value)}
                  >
                    <option value="es">es</option>
                    <option value="en">en</option>
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group>
                  <Form.Label>Retrieval K</Form.Label>
                  <Form.Control
                    type="number"
                    min={1}
                    step={1}
                    value={form.retrieval_k}
                    onChange={(e) => update("retrieval_k", e.target.value)}
                  />
                </Form.Group>
              </Col>
            </Row>

            <div className="border rounded p-3">
              <h6 className="mb-3">Curso</h6>
              <Row className="mb-2">
                <Col md={8}>
                  <Form.Group>
                    <Form.Label>Nombre</Form.Label>
                    <Form.Control
                      value={courseName}
                      disabled={true}
                    />
                  </Form.Group>
                </Col>
                <Col md={4}>
                  <Form.Group>
                    <Form.Label>Código</Form.Label>
                    <Form.Control
                      value={courseCode}
                      disabled={true}
                    />
                  </Form.Group>
                </Col>
              </Row>
            </div>

            <div className="border rounded p-3">
              <h6 className="mb-3">Resources</h6>
              <InputGroup className="mb-2">
                <Form.Control
                type="file"
                  value={resourceInput}
                  onChange={(e) => onChangeFile(e)}
                  onKeyDown={(e) => e.key === "Enter" && addResource()}
                />
                <Button variant="outline-primary" onClick={addResource}>
                  Añadir
                </Button>
              </InputGroup>
              {form.resources.length > 0 && (
                <Stack direction="horizontal" gap={2} className="flex-wrap">
                  {form.resources.map((r, idx) => (
                    <Badge key={idx} bg="secondary" className="p-2">
                      {r}{" "}
                      <Button
                        size="sm"
                        variant="light"
                        className="ms-2 py-0 px-1"
                        onClick={() => removeResource(idx)}
                      >
                        ×
                      </Button>
                    </Badge>
                  ))}
                </Stack>
              )}
            </div>
          </Stack>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={onHide}>
            Cancelar
          </Button>
          <Button type="submit" variant="primary">
            Guardar agente
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}

/** ---- AgentsCards (list + add button) ---- */
export default function AgentsCards() {
  const location = useLocation();
  const courseId = location.state?.courseId;
  const courseCode = location.state?.courseCode || "";
  const courseName = location.state?.courseName || "este curso";
  const [agents, setAgents] = useState(location.state?.agents || []);
  const [showAdd, setShowAdd] = useState(false);

  const handleSave = (newAgent) => {
    // Here you could POST to your backend instead of just updating UI
    setAgents((prev) => [newAgent, ...prev]);
    console.log("Nuevo agente:", newAgent);
  };

  return (
    <Nav>
      <div className="container py-4">
        <Stack direction="horizontal" className="mb-3" gap={2}>
          <h4 className="mb-0">Agentes de {courseName}</h4>
          <div className="ms-auto">
            <Button onClick={() => setShowAdd(true)}>+ Add Agent</Button>
          </div>
        </Stack>

        <Row xs={1} md={2} lg={3} className="g-3">
          {agents.map((a) => (
            <Col key={a.id}>
              <Card className="h-100">
                <Card.Body>
                  <Stack direction="horizontal" gap={2} className="mb-2">
                    <Card.Title className="mb-0">{a.name}</Card.Title>
                    <Badge bg={a.is_working ? "success" : "secondary"}>
                      {a.is_working ? "Activo" : "Inactivo"}
                    </Badge>
                  </Stack>
                  <Card.Subtitle className="text-muted mb-2">
                    {a.model} • {a.language?.toUpperCase()} • k={a.retrieval_k}
                  </Card.Subtitle>
                  <Card.Text className="mb-2">{a.description}</Card.Text>
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>

        <AddAgentModal
          show={showAdd}
          onHide={() => setShowAdd(false)}
            courseName={courseName}
            courseCode={courseCode}
            courseId={courseId}
            setAgents={setAgents}
        />
      </div>
    </Nav>
  );
}

/** ---- Example usage ----
import "bootstrap/dist/css/bootstrap.min.css";
import AgentsCards from "./AgentsCards";

const seed = [{
  name: "Agente Administrativo",
  description: "Agente con conocimiento del programa y estructura del curso",
  is_working: true,
  system_prompt:
    "Eres un agente administrativo. Usando tu conocimiento guía al estudiante en el programa del curso",
  model: "gpt-5",
  language: "es",
  retrieval_k: 5,
  id: "b313d4a2-dd24-4e15-8513-454a65789fa8",
  associated_course: "9e77f02e-8f1e-44c0-9a83-45c9490d627b",
  course: {
    id: "9e77f02e-8f1e-44c0-9a83-45c9490d627b",
    name: "Diseño y Aálisis de Algoritmos",
    code: "ISIS-1105",
    department: "Ingeniería de Sistemas y Computación",
    description: "La mejor materia del pregrado",
  },
  resources: [],
}];

function App() {
  return <AgentsCards initialAgents={seed} />;
}
----------------------------------------- */
