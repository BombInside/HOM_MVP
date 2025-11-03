import { motion } from "framer-motion";
import { Lock } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-sky-50 to-white">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center p-8 rounded-2xl bg-white shadow-lg"
      >
        <h1 className="text-3xl font-bold text-gray-800 mb-4">
          H.O.M Monitoring System
        </h1>
        <p className="text-gray-500 mb-8 max-w-md mx-auto">
          Добро пожаловать в систему мониторинга и управления.
        </p>

        <button
          onClick={() => navigate("/admin")}
          className="inline-flex items-center gap-2 px-6 py-3 text-white bg-sky-600 rounded-xl hover:bg-sky-700 transition-colors"
        >
          <Lock className="w-5 h-5" />
          Войти в админ-панель
        </button>
      </motion.div>
    </div>
  );
}
