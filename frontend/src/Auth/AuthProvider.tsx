import React, { createContext, useContext, useEffect, useState } from 'react';
import { jwtDecode } from 'jwt-decode';

type Decoded = { sub: string; email?: string; exp: number; [k: string]: any };
type User = { id: string; name: string; email: string; role: string; profile_image: string } | null;


type AuthState = {
  user: User;
  accessToken: string | null;
  status: 'idle' | 'loading' | 'authenticated' | 'unauthenticated';
};

const API = '/api/auth';

type AuthContextType = AuthState & {
  login: (email: string, password: string, remember: boolean) => Promise<void>;
  register: (user: { email: string; password: string; name: string; role: string; profile_image: string }) => Promise<void>;
  logout: () => Promise<void>;
};

const STORAGE_TOKEN = 't';

const AuthContext = createContext<AuthContextType | null>(null);
export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    accessToken: null,
    status: 'loading',
  });

  async function login(email: string, password: string, remember: boolean) {
    const res = await fetch(`${API}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password }),
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || 'Login failed');
    localStorage.setItem(STORAGE_TOKEN, result.access_token);
    localStorage.setItem('user', JSON.stringify(result.user));
    setState((prev) => ({
      user: result.user,
      status: 'authenticated',
      accessToken: result.access_token,
    }));
  }

  async function register(user: { email: string; password: string; name: string; role: string; profile_image: string }) {
    const res = await fetch(`${API}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(user),
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || 'Register failed');
    await login(user.email, user.password, true);
  }

  async function logout() {
    setState({ user: null, accessToken: null, status: 'unauthenticated' });
    localStorage.removeItem(STORAGE_TOKEN);
    localStorage.removeItem('user');
  }

  // Hydrate from localStorage or refresh on mount
  useEffect(() => {
    const token = localStorage.getItem(STORAGE_TOKEN);
    const user = localStorage.getItem('user');
    if (token) {
      setState((prev) => ({ ...prev, accessToken: token, status: 'authenticated', user: user ? JSON.parse(user) : null }));
    } else {
      setState((prev) => ({ ...prev, accessToken: null, status: 'unauthenticated', user: null }));
    }
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
