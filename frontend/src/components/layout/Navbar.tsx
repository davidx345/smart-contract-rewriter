import React, { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { 
  ShieldCheck, 
  History, 
  LayoutDashboard, 
  Linkedin, 
  User, 
  LogOut, 
  LogIn, 
  Building2, 
  CreditCard, 
  Shield,
  ChevronDown
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const Navbar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const [showEnterpriseMenu, setShowEnterpriseMenu] = useState(false);

  return (
    <nav className="bg-gray-900/80 backdrop-blur-md text-white shadow-lg sticky top-0 z-50">
      <div className="container mx-auto px-6 py-3 flex justify-between items-center">
        <Link to="/" className="flex items-center space-x-2">
          <ShieldCheck className="h-8 w-8 text-primary-500" />
          <h1 className="text-2xl font-bold tracking-tight">
            SoliVolt
          </h1>
        </Link>
        
        <div className="flex items-center space-x-6">
          {/* Navigation Links */}
          {isAuthenticated ? (
            <>
              <NavLink
                to="/dashboard"
                className={({ isActive }) =>
                  `hover:text-primary-400 transition-colors ${isActive ? 'text-primary-500 font-semibold' : ''}`
                }
              >
                <LayoutDashboard className="inline-block h-5 w-5 mr-1" />
                Dashboard
              </NavLink>
              <NavLink
                to="/"
                className={({ isActive }) =>
                  `hover:text-primary-400 transition-colors ${isActive ? 'text-primary-500 font-semibold' : ''}`
                }
              >
                <ShieldCheck className="inline-block h-5 w-5 mr-1" />
                Analyze
              </NavLink>
              <NavLink
                to="/history"
                className={({ isActive }) =>
                  `hover:text-primary-400 transition-colors ${isActive ? 'text-primary-500 font-semibold' : ''}`
                }
              >
                <History className="inline-block h-5 w-5 mr-1" />
                History
              </NavLink>
              
              {/* Enterprise Menu */}
              <div className="relative">
                <button
                  onClick={() => setShowEnterpriseMenu(!showEnterpriseMenu)}
                  className="flex items-center space-x-1 hover:text-primary-400 transition-colors"
                >
                  <Building2 className="h-5 w-5" />
                  <span>Enterprise</span>
                  <ChevronDown className="h-4 w-4" />
                </button>
                
                {showEnterpriseMenu && (
                  <div className="absolute top-full right-0 mt-2 w-48 bg-white text-gray-800 rounded-lg shadow-lg border">
                    <NavLink
                      to="/organization"
                      className={({ isActive }) =>
                        `block px-4 py-2 text-sm hover:bg-gray-100 transition-colors ${isActive ? 'bg-blue-50 text-blue-600' : ''}`
                      }
                      onClick={() => setShowEnterpriseMenu(false)}
                    >
                      <Building2 className="inline-block h-4 w-4 mr-2" />
                      Organization
                    </NavLink>
                    <NavLink
                      to="/billing"
                      className={({ isActive }) =>
                        `block px-4 py-2 text-sm hover:bg-gray-100 transition-colors ${isActive ? 'bg-blue-50 text-blue-600' : ''}`
                      }
                      onClick={() => setShowEnterpriseMenu(false)}
                    >
                      <CreditCard className="inline-block h-4 w-4 mr-2" />
                      Billing
                    </NavLink>
                    <NavLink
                      to="/security"
                      className={({ isActive }) =>
                        `block px-4 py-2 text-sm hover:bg-gray-100 transition-colors ${isActive ? 'bg-blue-50 text-blue-600' : ''}`
                      }
                      onClick={() => setShowEnterpriseMenu(false)}
                    >
                      <Shield className="inline-block h-4 w-4 mr-2" />
                      Security
                    </NavLink>
                  </div>
                )}
              </div>
            </>
          ) : (
            <NavLink
              to="/"
              className={({ isActive }) =>
                `hover:text-primary-400 transition-colors ${isActive ? 'text-primary-500 font-semibold' : ''}`
              }
            >
              <ShieldCheck className="inline-block h-5 w-5 mr-1" />
              Platform
            </NavLink>
          )}

          {/* Authentication Section */}
          {isAuthenticated ? (
            <div className="flex items-center space-x-4">
              {/* User Menu */}
              <div className="flex items-center space-x-2">
                <User className="h-5 w-5" />
                <span className="text-sm">{user?.full_name}</span>
                {user?.role !== 'user' && (
                  <span className="px-2 py-1 bg-blue-500 text-xs rounded-full">
                    {user.role.toUpperCase()}
                  </span>
                )}
              </div>
              
              {/* Logout Button */}
              <button
                onClick={logout}
                className="flex items-center space-x-1 hover:text-primary-400 transition-colors"
                title="Sign Out"
              >
                <LogOut className="h-5 w-5" />
                <span className="text-sm">Sign Out</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-4">
              <Link
                to="/login"
                className="flex items-center space-x-1 hover:text-primary-400 transition-colors"
              >
                <LogIn className="h-5 w-5" />
                <span>Sign In</span>
              </Link>
              <Link
                to="/register"
                className="bg-primary-600 hover:bg-primary-700 px-4 py-2 rounded-lg transition-colors"
              >
                Get Started
              </Link>
            </div>
          )}

          {/* LinkedIn Profile */}
          <a 
            href="https://www.linkedin.com/in/david-ayodele-ayo" 
            target="_blank" 
            rel="noopener noreferrer"
            className="hover:text-primary-400 transition-colors"
            title="LinkedIn Profile"
          >
            <Linkedin className="h-6 w-6" />
          </a>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
