import Auth from './Auth/Auth.jsx';
import './App.css';
import { AuthProvider } from './Auth/AuthProvider.tsx';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import RequireAuth from './Auth/RequireAuth.jsx';
import Courses from './Courses/Courses.jsx';
import AgentsCards from './Agents/AgentCards.jsx';
import AgentList from './Agents/AgentList.jsx';
import Chat from './Chat/Chat.jsx';


function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Auth />} />

          <Route element={<RequireAuth />}>
            <Route path="/" element={<Courses />} />
            <Route path="/agentsT" element={<AgentsCards />} />
            <Route path="/agentsS" element={<AgentList />} />
            <Route path="/chat" element={<Chat />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;