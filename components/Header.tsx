
import React, { useContext } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { AuthContext } from '../App';
import { BookOpen, User, LayoutDashboard, LogOut } from 'lucide-react';

const Header: React.FC = () => {
  const auth = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    if (auth) {
      auth.logout();
      navigate('/login');
    }
  };

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
      isActive ? 'bg-purple-100 text-purple-700' : 'text-gray-600 hover:bg-purple-50 hover:text-purple-600'
    }`;

  return (
    <header className="bg-white/80 backdrop-blur-sm shadow-md rounded-full max-w-4xl mx-auto mb-8 sticky top-4 z-50">
      <div className="container mx-auto px-6 py-3 flex justify-between items-center">
        <NavLink to="/" className="text-2xl font-brand text-purple-600">
          StoryWeaver
        </NavLink>
        <nav className="hidden md:flex items-center gap-4">
          <NavLink to="/" className={navLinkClass}>
            <BookOpen size={18} />
            New Story
          </NavLink>
          <NavLink to="/profile" className={navLinkClass}>
            <User size={18} />
            Profile
          </NavLink>
          <NavLink to="/dashboard" className={navLinkClass}>
            <LayoutDashboard size={18} />
            Dashboard
          </NavLink>
        </nav>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium bg-red-500 text-white hover:bg-red-600 transition-colors"
        >
          <LogOut size={16} />
          Logout
        </button>
      </div>
    </header>
  );
};

export default Header;
