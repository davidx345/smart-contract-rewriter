import React from 'react';
import { Link, NavLink } from 'react-router-dom';
import { 
  ShieldCheck, 
  History, 
  Linkedin, 
} from 'lucide-react';

const Navbar: React.FC = () => {
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
