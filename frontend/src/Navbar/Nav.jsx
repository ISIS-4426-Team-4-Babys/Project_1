import { Container, Navbar, Button, Col } from 'react-bootstrap';
import { useAuth } from '../Auth/AuthProvider.tsx';


export default function Layout({ children }) {
    const { logout } = useAuth();
  
  return (
    <>
      <Navbar bg="dark" variant="dark" expand="lg" className={`justify-content-between px-4 py-2 navbar`}>
        <Col xs={6} md={6} lg={9}>
          <Navbar.Brand href="/" className="d-flex align-items-center">
            <p style={{ margin: 0, fontWeight: "bold" }}>DEPLO</p>
          </Navbar.Brand>
        </Col>
        <Button variant="dark" onClick={logout}>Log out</Button>
      </Navbar>
      <Container className="py-4">{children}</Container>
    </>
  );
}