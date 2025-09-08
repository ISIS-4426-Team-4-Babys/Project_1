import { useEffect, useState } from 'react';
import { Container, Row, Col, Card, Tabs, Tab, Form, Button, InputGroup } from 'react-bootstrap';
import './Auth.css';
import { useAuth } from './AuthProvider.tsx';
import { useNavigate } from 'react-router-dom';

export default function Auth() {
    const { login, status, register, user } = useAuth();
    const [activeKey, setActiveKey] = useState('signin');
    const navigate = useNavigate();

    // Sign In state
    const [siEmail, setSiEmail] = useState('');
    const [siPassword, setSiPassword] = useState('');
    const [siShowPwd, setSiShowPwd] = useState(false);
    const [siTouched, setSiTouched] = useState(false);

    // Sign Up state
    const [suName, setSuName] = useState('');
    const [suEmail, setSuEmail] = useState('');
    const [suPassword, setSuPassword] = useState('');
    const [suRole, setSuRole] = useState('');
    const [suShowPwd, setSuShowPwd] = useState(false);
    const [suTouched, setSuTouched] = useState(false);

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/i;

    const pps = [
    "https://www.lego.com/cdn/cs/set/assets/blt5106608431ab56b9/02_Emmet_top_Hero_w_block.jpg?fit=crop&format=jpg&quality=80&width=800&height=426&dpr=1",
    "https://platform.vox.com/wp-content/uploads/sites/2/chorus/uploads/chorus_asset/file/7952371/legobatmancover.jpg?quality=90&strip=all&crop=7.8125,0,84.375,100",
    "https://ew.com/thmb/472JmfUozswCxY4Jb7yIIK3QRuc=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/LEGO-SPIDER-MAN-ACROSS-THE-SPIDER-VERSE-01-060823-b4eca70b1c594de6aa9de422989a0902.jpg",
    "https://external-preview.redd.it/8Sn6amMRK0xH1blmK0TKPxDOh8-Gnj-7d7qLgs993G4.jpg?width=640&crop=smart&auto=webp&s=93e474c24df6a02de84deee77460b99057b6fcd7",
    "https://m.media-amazon.com/images/M/MV5BZWU2ZDI4ZGYtODNkMi00ODYyLWJhMTItMTNlNzkyYmU4ZDRkXkEyXkFqcGdeQVRoaXJkUGFydHlJbmdlc3Rpb25Xb3JrZmxvdw@@._V1_QL75_UX500_CR0,0,500,281_.jpg",
    "https://static01.nyt.com/images/2019/02/01/arts/01tvcol-legomovie/01tvcol-legomovie-articleLarge.jpg?quality=75&auto=webp&disable=upscale"
    ];


    useEffect(() => {
        if (status === 'authenticated') {
            navigate('/');
        }
    }, [status, navigate, user]);

    // Simple validations
    const siErrors = {
        email: siTouched && (!siEmail || !emailRegex.test(siEmail)) ? 'Please enter a valid email.' : '',
        password: siTouched && (!siPassword || siPassword.length < 6) ? 'Minimum 6 characters.' : ''
    };

    const suErrors = {
        name: suTouched && (!suName || suName.length < 2) ? 'Enter your name.' : '',
        email: suTouched && (!suEmail || !emailRegex.test(suEmail)) ? 'Please enter a valid email.' : '',
        password: suTouched && (!suPassword || suPassword.length < 8) ? 'At least 8 characters.' : '',
    };

    const handleSignIn = async (e) => {
        e.preventDefault();
        setSiTouched(true);
        if (!siErrors.email && !siErrors.password) {
            // Replace with your API call
            try{
                await login(siEmail, siPassword, true);
                navigate('/');
            } catch (error) {
                alert("Login failed: " + (error.response?.data?.message || error.message));
            }
        }
    };

    const handleSignUp = async (e) => {
        e.preventDefault();
        setSuTouched(true);
        if (!suErrors.name && !suErrors.email && !suErrors.password && !suErrors.confirm) {
            try{
                await register({ 
                    name: suName, 
                    email: suEmail, 
                    password: suPassword, 
                    role: suRole,
                    profile_image: pps[Math.floor(Math.random() * pps.length)] 
                });
                navigate('/');
            } catch (error) {
                alert("Registration failed: " + (error.response?.data?.message || error.message));
            }
        }
    };

    return (
        <div className="auth-wrap">
            <Container>
                <Row className="justify-content-center">
                    <Col xs={12} sm={10} md={8} lg={6} xl={5}>
                        <Card className="auth-card shadow-lg">
                            <Card.Body>
                                <h1 className="auth-title mb-3 text-center">Welcome</h1>
                                <p className="text-center text-muted mb-4">Sign in to continue or create an account</p>
                                <Tabs
                                    id="auth-tabs"
                                    activeKey={activeKey}
                                    onSelect={(k) => setActiveKey(k || 'signin')}
                                    className="mb-4 justify-content-center"
                                >
                                    <Tab eventKey="signin" title="Sign In">
                                        <Form className="pt-3" onSubmit={handleSignIn} noValidate>
                                            <Form.Group className="mb-3" controlId="siEmail">
                                                <Form.Label>Email</Form.Label>
                                                <Form.Control
                                                    type="email"
                                                    placeholder="you@example.com"
                                                    value={siEmail}
                                                    onChange={(e) => setSiEmail(e.target.value)}
                                                    onBlur={() => setSiTouched(true)}
                                                    isInvalid={!!siErrors.email}
                                                />
                                                <Form.Control.Feedback type="invalid">{siErrors.email}</Form.Control.Feedback>
                                            </Form.Group>

                                            <Form.Group className="mb-3" controlId="siPassword">
                                                <Form.Label>Password</Form.Label>
                                                <InputGroup>
                                                    <Form.Control
                                                        type={siShowPwd ? 'text' : 'password'}
                                                        placeholder="Password"
                                                        value={siPassword}
                                                        onChange={(e) => setSiPassword(e.target.value)}
                                                        onBlur={() => setSiTouched(true)}
                                                        isInvalid={!!siErrors.password}
                                                    />
                                                    <Button
                                                        variant="outline-secondary"
                                                        type="button"
                                                        onClick={() => setSiShowPwd((v) => !v)}
                                                        aria-label={siShowPwd ? 'Hide password' : 'Show password'}
                                                    >
                                                        {siShowPwd ? 'Hide' : 'Show'}
                                                    </Button>
                                                    <Form.Control.Feedback type="invalid">{siErrors.password}</Form.Control.Feedback>
                                                </InputGroup>
                                            </Form.Group>
                                            <Button type="submit" className="w-100" variant="primary">Sign In</Button>
                                        </Form>
                                    </Tab>

                                    <Tab eventKey="signup" title="Sign Up">
                                        <Form className="pt-3" onSubmit={handleSignUp} noValidate>
                                            <Form.Group className="mb-3" controlId="suName">
                                                <Form.Label>Full Name</Form.Label>
                                                <Form.Control
                                                    type="text"
                                                    placeholder="Jane Doe"
                                                    value={suName}
                                                    onChange={(e) => setSuName(e.target.value)}
                                                    onBlur={() => setSuTouched(true)}
                                                    isInvalid={!!suErrors.name}
                                                />
                                                <Form.Control.Feedback type="invalid">{suErrors.name}</Form.Control.Feedback>
                                            </Form.Group>

                                            <Form.Group className="mb-3" controlId="suEmail">
                                                <Form.Label>Email</Form.Label>
                                                <Form.Control
                                                    type="email"
                                                    placeholder="you@example.com"
                                                    value={suEmail}
                                                    onChange={(e) => setSuEmail(e.target.value)}
                                                    onBlur={() => setSuTouched(true)}
                                                    isInvalid={!!suErrors.email}
                                                />
                                                <Form.Control.Feedback type="invalid">{suErrors.email}</Form.Control.Feedback>
                                            </Form.Group>

                                            <Form.Group className="mb-3" controlId="suPassword">
                                                <Form.Label>Password</Form.Label>
                                                <InputGroup>
                                                    <Form.Control
                                                        type={suShowPwd ? 'text' : 'password'}
                                                        placeholder="At least 8 characters"
                                                        value={suPassword}
                                                        onChange={(e) => setSuPassword(e.target.value)}
                                                        onBlur={() => setSuTouched(true)}
                                                        isInvalid={!!suErrors.password}
                                                    />
                                                    <Button
                                                        variant="outline-secondary"
                                                        type="button"
                                                        onClick={() => setSuShowPwd((v) => !v)}
                                                        aria-label={suShowPwd ? 'Hide password' : 'Show password'}
                                                    >
                                                        {suShowPwd ? 'Hide' : 'Show'}
                                                    </Button>
                                                    <Form.Control.Feedback type="invalid">{suErrors.password}</Form.Control.Feedback>
                                                </InputGroup>
                                            </Form.Group>

                                            <Form.Group className="mb-4" controlId="suRole">
                                                <Form.Label>Role</Form.Label>
                                                <Form.Select
                                                    aria-label="Select a role"
                                                    value={suRole}
                                                    onChange={(e) => setSuRole(e.target.value)}
                                                >
                                                    <option value="" disabled>Choose…</option>
                                                    <option key={"professor"} value={"professor"}>
                                                       {"Professor"}
                                                    </option>
                                                    <option key={"student"} value={"student"}>
                                                       {"Student"}
                                                    </option>
                                                </Form.Select>
                                            </Form.Group>

                                            <Button type="submit" className="w-100">Create Account</Button>
                                        </Form>
                                    </Tab>
                                </Tabs>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            </Container>
        </div>
    );
}