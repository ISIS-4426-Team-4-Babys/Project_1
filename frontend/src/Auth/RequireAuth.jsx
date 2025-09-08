import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from './AuthProvider.tsx';
import React from 'react';
import { useNavigate } from 'react-router-dom';


export default function RequireAuth() {
  const { status } = useAuth();
  const navigate = useNavigate();

  React.useEffect(() => {
    if (status !== 'loading' && status !== 'authenticated') {
      navigate('/login');
    }
  }, [status, navigate]);

  if (status === 'loading') {
    return <div style={{ padding: 24 }}>Checking session…</div>;
  }

  return <Outlet />; // render the protected child route(s)
}
