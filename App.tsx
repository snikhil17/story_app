
import React, { createContext, useState, useEffect, useCallback } from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import type { UserProfile, Story } from './types';
import { storageService } from './services/storageService';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import LandingPage from './pages/LandingPage';
import StoryPage from './pages/StoryPage';
import ProfilePage from './pages/ProfilePage';
import DashboardPage from './pages/DashboardPage';
import Header from './components/Header';

interface AuthContextType {
  user: UserProfile | null;
  login: (email: string) => void;
  signup: (profile: UserProfile) => void;
  logout: () => void;
  updateUser: (profile: UserProfile) => void;
}

export const AuthContext = createContext<AuthContextType | null>(null);

const App: React.FC = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const currentUser = storageService.getCurrentUser();
    if (currentUser) {
      const userProfile = storageService.getUserProfile(currentUser.email);
      setUser(userProfile);
    }
    setLoading(false);
  }, []);

  const login = (email: string) => {
    const userProfile = storageService.getUserProfile(email);
    if (userProfile) {
      storageService.setCurrentUser(userProfile);
      setUser(userProfile);
    }
  };

  const signup = (profile: UserProfile) => {
    storageService.saveUserProfile(profile);
    storageService.setCurrentUser(profile);
    setUser(profile);
  };

  const logout = () => {
    storageService.clearCurrentUser();
    setUser(null);
  };
  
  const updateUser = (profile: UserProfile) => {
    storageService.saveUserProfile(profile);
    setUser(profile);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-purple-100 to-blue-100">
        <div className="text-2xl font-brand text-purple-600">Loading StoryWeaver...</div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, updateUser }}>
      <HashRouter>
        <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50 text-gray-800">
          {user && <Header />}
          <main className="p-4 sm:p-6 md:p-8">
            <Routes>
              <Route path="/login" element={!user ? <LoginPage /> : <Navigate to="/" />} />
              <Route path="/signup" element={!user ? <SignupPage /> : <Navigate to="/" />} />
              <Route path="/" element={user ? <LandingPage /> : <Navigate to="/login" />} />
              <Route path="/story" element={user ? <StoryPage /> : <Navigate to="/login" />} />
              <Route path="/profile" element={user ? <ProfilePage /> : <Navigate to="/login" />} />
              <Route path="/dashboard" element={user ? <DashboardPage /> : <Navigate to="/login" />} />
              <Route path="*" element={<Navigate to={user ? "/" : "/login"} />} />
            </Routes>
          </main>
        </div>
      </HashRouter>
    </AuthContext.Provider>
  );
};

export default App;
