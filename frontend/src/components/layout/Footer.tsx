import React from 'react';
import { Heart, Github, Twitter, Globe } from 'lucide-react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-gray-900 text-gray-300 mt-auto">
      <div className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand Section */}
          <div className="col-span-1 md:col-span-2">
            <h3 className="text-xl font-bold text-white mb-4">Smart Contract Rewriter</h3>
            <p className="text-gray-400 mb-4">
              AI-powered smart contract optimization and security analysis. 
              Rewrite your Solidity contracts for better gas efficiency, security, and code quality.
            </p>
            <div className="flex items-center space-x-4">
              <a 
                href="https://github.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="hover:text-primary-400 transition-colors"
              >
                <Github className="h-5 w-5" />
              </a>
              <a 
                href="https://twitter.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="hover:text-primary-400 transition-colors"
              >
                <Twitter className="h-5 w-5" />
              </a>
              <a 
                href="https://example.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="hover:text-primary-400 transition-colors"
              >
                <Globe className="h-5 w-5" />
              </a>
            </div>
          </div>

          {/* Features */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-4">Features</h4>
            <ul className="space-y-2 text-sm">
              <li className="hover:text-primary-400 transition-colors cursor-pointer">Gas Optimization</li>
              <li className="hover:text-primary-400 transition-colors cursor-pointer">Security Analysis</li>
              <li className="hover:text-primary-400 transition-colors cursor-pointer">Code Quality Check</li>
              <li className="hover:text-primary-400 transition-colors cursor-pointer">Best Practices</li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="text-lg font-semibold text-white mb-4">Resources</h4>
            <ul className="space-y-2 text-sm">
              <li className="hover:text-primary-400 transition-colors cursor-pointer">Documentation</li>
              <li className="hover:text-primary-400 transition-colors cursor-pointer">API Reference</li>
              <li className="hover:text-primary-400 transition-colors cursor-pointer">Examples</li>
              <li className="hover:text-primary-400 transition-colors cursor-pointer">Support</li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-700 mt-8 pt-8 flex flex-col md:flex-row justify-between items-center">
          <p className="text-sm text-gray-400">
            © 2025 Smart Contract Rewriter. All rights reserved.
          </p>
          <p className="text-sm text-gray-400 flex items-center mt-4 md:mt-0">
            Made with <Heart className="h-4 w-4 mx-1 text-red-500" /> for the blockchain community
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
