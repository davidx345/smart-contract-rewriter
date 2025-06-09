import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Home, ArrowLeft } from 'lucide-react';
import Button from '../components/ui/Button';

const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
      <div className="text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          {/* Animated 404 */}
          <motion.h1
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="text-9xl font-bold text-primary-600 mb-4"
          >
            404
          </motion.h1>
          
          {/* Error message */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.6 }}
          >
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Page Not Found
            </h2>
            <p className="text-xl text-gray-600 mb-8 max-w-md mx-auto">
              Oops! The page you're looking for doesn't exist. It might have been moved or deleted.
            </p>
          </motion.div>

          {/* Action buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.6 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <Button
              onClick={() => navigate('/')}
              className="flex items-center space-x-2"
            >
              <Home className="h-4 w-4" />
              <span>Go Home</span>
            </Button>
            <Button
              onClick={() => navigate(-1)}
              variant="outline"
              className="flex items-center space-x-2"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Go Back</span>
            </Button>
          </motion.div>

          {/* Floating shapes for visual appeal */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <motion.div
              animate={{
                y: [0, -20, 0],
                rotate: [0, 5, 0]
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
                ease: "easeInOut"
              }}
              className="absolute top-1/4 left-1/4 w-16 h-16 bg-blue-200 rounded-full opacity-60"
            />
            <motion.div
              animate={{
                y: [0, 20, 0],
                rotate: [0, -5, 0]
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 1
              }}
              className="absolute top-1/3 right-1/4 w-12 h-12 bg-purple-200 rounded-full opacity-60"
            />
            <motion.div
              animate={{
                y: [0, -15, 0],
                x: [0, 10, 0]
              }}
              transition={{
                duration: 5,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 2
              }}
              className="absolute bottom-1/3 left-1/3 w-8 h-8 bg-green-200 rounded-full opacity-60"
            />
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default NotFoundPage;
