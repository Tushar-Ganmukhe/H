import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Phone, Lock, AlertCircle, LogIn, Pill } from "lucide-react";

const MOCK_USERS = [
  { mobile: "9999999999", password: "admin123", role: "admin", name: "System Admin" },
  { mobile: "8888888888", password: "user123", role: "user", name: "Regular User" }
];

const Login = () => {
  const [mobile, setMobile] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    setError("");

    const mobileRegex = /^[0-9]{10}$/;
    if (!mobileRegex.test(mobile)) {
      setError("Please enter a valid 10-digit mobile number.");
      return;
    }

    if (!password) {
      setError("Please enter your password.");
      return;
    }

    const user = MOCK_USERS.find(
      (u) => u.mobile === mobile && u.password === password
    );

    if (user) {
      localStorage.setItem("authUser", JSON.stringify({
        mobile: user.mobile,
        role: user.role,
        name: user.name
      }));

      if (user.role === "admin") navigate("/admin");
      else navigate("/user");
    } else {
      setError("Invalid mobile number or password.");
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center p-4">
      <div className="bg-white max-w-md w-full rounded-3xl shadow-lg border border-gray-100 overflow-hidden">
        <div className="bg-blue-600 p-8 text-center flex flex-col items-center">
          <div className="bg-white/20 p-3 rounded-2xl mb-4">
            <Pill className="text-white" size={32} />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Pharmacy Assistant</h2>
          <p className="text-blue-100 text-sm">Sign in to your account</p>
        </div>

        <form onSubmit={handleLogin} className="p-8 space-y-6">
          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-xl text-sm flex items-center gap-2">
              <AlertCircle size={16} />
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Mobile Number</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400">
                <Phone size={18} />
              </div>
              <input
                type="text"
                maxLength="10"
                value={mobile}
                onChange={(e) => setMobile(e.target.value.replace(/\D/g, ""))}
                className="w-full bg-gray-50 border border-gray-200 rounded-2xl pl-11 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                placeholder="Enter 10-digit number"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400">
                <Lock size={18} />
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-gray-50 border border-gray-200 rounded-2xl pl-11 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                placeholder="Enter password"
              />
            </div>
          </div>

          <button type="submit" className="w-full bg-blue-600 text-white font-semibold rounded-2xl py-3.5 flex items-center justify-center gap-2 hover:bg-blue-700 transition-all">
            <LogIn size={18} /> Login Securely
          </button>

          <div className="mt-4 pt-4 border-t border-gray-100 text-xs text-gray-500 text-center flex justify-between">
            <p><strong>Admin:</strong> 9999999999<br/>admin123</p>
            <p><strong>User:</strong> 8888888888<br/>user123</p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;