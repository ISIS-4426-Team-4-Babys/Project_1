import { useState } from 'react';
import {  Form, InputGroup, Button } from 'react-bootstrap';
import Message from './Message';
import './Chat.css';
import { Container, Row, Col, OverlayTrigger, Tooltip } from 'react-bootstrap';
// @ts-ignore
import { ReactComponent as Arrowhead } from '../resources/arrowhead.svg';
import { useRef, useEffect } from 'react';
// @ts-ignore
import { ReactComponent as ReloadArrow } from '../resources/reloadArrow.svg';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../Auth/AuthProvider.tsx';
import Nav from "../Navbar/Nav.jsx";



export default function Chat() {
  const location = useLocation();
  const agentID = location.state?.agentID || 'default-agent-id';
  const agentName = location.state?.agentName || 'Asistente';
  const courseName = location.state?.courseName || 'Curso';
  const { user, accessToken } = useAuth();
  

  const [messages, setMessages] = useState([]);

  const [input, setInput] = useState('');
  const [started, setStarted] = useState(false);

  const handleSend = async () => {
    if (input.trim() === '') return;
    // @ts-ignore
    setMessages(prevMessages => [...prevMessages, { from: 'user', text: String(input) }]);
    setInput('');
    setStarted(true);
    try {
      const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      };

      const response = await fetch(`/agent/ask?agentID=${agentID}`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ question: input }),
      });
      const data = await response.json();
      console.log('Prueba ', data)
      // @ts-ignore
      setMessages(prevMessages => [...prevMessages, { from: 'bot', text: data.answer }]);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const handleReload = () => {
    setMessages([]);
    setInput('');
    setStarted(false);
  };


  // @ts-ignore
  // @ts-ignore
  const handleStart = () => {
    setStarted(true);
  };
  const messagesEndRef = useRef(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      // @ts-ignore
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [messages]);
  
  if (!started) {
    return (
      <Nav>
      <div className="welcomeScreen" style={{ minHeight: '100vh', position: 'relative' }}>
      <Container className="mt-5">
      <Row className="justify-content-center align-items-center">
      <Col xs={12} md={10} lg={9}>
        <h1 className="welcomeText">¡Hola, {user?.name?.split(' ')[0]}! Estoy listo para responder tus preguntas cuando quieras.</h1>
      </Col>
      </Row>
      </Container>

      {TextBox(input, handleSend, setInput, handleReload, started, agentName)}
      </div>
      </Nav>
    );
  }


  return (
    <Nav>
      <div style={{ position: 'sticky', top: 0, zIndex: 100, background: 'white' }}>
        <Row className="justify-content-center align-items-center">
          <Col xs={12} md={10} lg={8} style={{ backgroundColor: 'white' }}>
            <h2 style={{ fontWeight: 'bold', width: 'max-content' }}>
              {courseName}: {agentName}
            </h2>
          </Col>
        </Row>
      </div>
      <Row className="justify-content-center">
        <Col
          xs={12}
          md={10}
          lg={8}
          className="chatContainer"
          style={{
            height: 'calc(100vh - 120px)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'flex-end',
            paddingTop: '16px',
            paddingBottom: '20px',
          }}
        >
          <div
            className="flex-grow-1 messageContainer"
            style={{
              overflowY: 'auto',
              flexGrow: 1,
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {messages.map((msg, idx) => (
              // @ts-ignore
              <Message key={idx} from={msg.from} text={msg.text} />
            ))}
            <div ref={messagesEndRef} />
          </div>
          <Container
            style={{
              position: 'fixed',
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              justifyContent: 'center',
              background: 'white',
              zIndex: 101,
            }}
          >
            {TextBox(input, handleSend, setInput, handleReload, started, agentName)}
          </Container>
        </Col>
      </Row>
    </Nav>
  );
}

function TextBox(input, handleSend, setInput, handleReload, started, agentName) {
  const inputRef = useRef(null);

  const handleInputChange = (e) => {
    setInput(e.target.value);
    const textarea = inputRef.current;
    const maxHeight = 200; 
    // @ts-ignore
    textarea.style.height = 'auto';
    // @ts-ignore
    textarea.style.overflowY = 'hidden';
    
    // @ts-ignore
    if (textarea.scrollHeight > maxHeight) {
      // @ts-ignore
      textarea.style.height = `${maxHeight}px`;
      // @ts-ignore
      textarea.style.overflowY = 'auto';
    }
    else {
      // @ts-ignore
      textarea.style.height = `${textarea.scrollHeight}px`;
    }

  };

  
  return(
    <Col xs={12} md={12} lg={9} className="d-flex flex-column align-items-center">
    <InputGroup className="inputWrapper mt-4">
      <Form.Control
        className="inputBox"
        placeholder={`Soy el ${agentName}. Preguntame lo que quieras saber`}
        value={input}
        onChange={handleInputChange}
        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        rows={1}
        as="textarea"
        ref={inputRef}
      />
      <Button className="sendButton" variant="dark" onClick={handleSend}>
        <Arrowhead className="arrowhead"/>
      </Button>
      {started && (
        <OverlayTrigger
          placement="top"
          overlay={<Tooltip id="send-tooltip">Clear Session</Tooltip>}
        >
          <Button className="sendButton" variant="dark" onClick={handleReload}>
            <ReloadArrow className="reload"/>
          </Button>
        </OverlayTrigger>
      )}
    </InputGroup>

    <p className="warningText">
      DEPLO es un prototipo en evaluación. Por favor verifica la información importante.
    </p>
    </Col>

  );
}