import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Phone, Lock, AlertCircle, LogIn, Pill, ShieldCheck } from "lucide-react";

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
    const user = MOCK_USERS.find(u => u.mobile === mobile && u.password === password);
    if (user) {
      localStorage.setItem("authUser", JSON.stringify(user));
      if (user.role === "admin") navigate("/admin");
      else navigate("/user");
    } else {
      setError("Invalid mobile number or password.");
    }
  };

  return (
    <div className="flex h-screen w-screen bg-white overflow-hidden">
      {/* Left Side: Branding & Visuals (Full Height) */}
      <div className="hidden lg:flex w-1/2 bg-blue-600 items-center justify-center p-12 relative">
        <div className="relative z-10 text-white max-w-lg">
          <div className="bg-white/20 p-4 rounded-3xl w-fit mb-8 backdrop-blur-md">
            <Pill size={48} className="text-white" />
          </div>
          <h1 className="text-6xl font-black tracking-tighter mb-6 leading-tight">
            Smart Pharmacy <br /> Management.
          </h1>
          <p className="text-blue-100 text-xl font-medium leading-relaxed opacity-90">
            Real-time inventory synchronization, AI-powered pharmaceutical assistance, and advanced sales analytics in one unified platform.
          </p>
          <div className="mt-12 flex items-center gap-4 text-blue-200 font-bold text-sm uppercase tracking-widest">
            <ShieldCheck size={20} />
            Enterprise Grade Security Active
          </div>
        </div>
        {/* Abstract Background Shapes */}
        <div className="absolute top-[-10%] left-[-10%] w-80 h-80 bg-blue-500 rounded-full blur-3xl opacity-50"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-blue-700 rounded-full blur-3xl opacity-50"></div>
      </div>

      {/* Right Side: Login Form (Full Height) */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-[#F8FAFC]">
        <div className="max-w-md w-full">
          <div className="mb-10 lg:hidden flex items-center gap-3">
             <div className="bg-blue-600 p-2 rounded-xl"><Pill className="text-white" /></div>
             <h2 className="text-2xl font-black text-gray-800">Pharmacy Pro</h2>
          </div>

          <h2 className="text-4xl font-black text-gray-900 mb-2 tracking-tight">Login</h2>
          <p className="text-gray-500 font-medium mb-10 text-lg">Enter your credentials to manage your pharmacy.</p>

          <form onSubmit={handleLogin} className="space-y-6">
            {error && (
              <div className="bg-red-50 text-red-600 p-4 rounded-2xl text-sm font-bold flex items-center gap-3 border border-red-100 animate-shake">
                <AlertCircle size={20} /> {error}
              </div>
            )}

            <div className="space-y-2">
              <label className="text-sm font-black text-gray-700 uppercase tracking-wider ml-1">Mobile Number</label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-5 flex items-center pointer-events-none text-gray-400 group-focus-within:text-blue-600 transition-colors">
                  <Phone size={20} />
                </div>
                <input
                  type="text"
                  maxLength="10"
                  value={mobile}
                  onChange={(e) => setMobile(e.target.value.replace(/\D/g, ""))}
                  className="w-full bg-white border-2 border-gray-100 rounded-2xl pl-14 pr-4 py-4 focus:outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-600 transition-all font-bold text-gray-700 shadow-sm"
                  placeholder="9999999999"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-black text-gray-700 uppercase tracking-wider ml-1">Password</label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-5 flex items-center pointer-events-none text-gray-400 group-focus-within:text-blue-600 transition-colors">
                  <Lock size={20} />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-white border-2 border-gray-100 rounded-2xl pl-14 pr-4 py-4 focus:outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-600 transition-all font-bold text-gray-700 shadow-sm"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button type="submit" className="w-full bg-blue-600 text-white font-black rounded-2xl py-5 flex items-center justify-center gap-3 hover:bg-blue-700 transition-all shadow-xl shadow-blue-100 active:scale-95 text-lg">
              <LogIn size={22} /> Login Securely
            </button>
          </form>

          <div className="mt-12 p-6 bg-white rounded-3xl border border-gray-100 shadow-sm">
            <h4 className="text-xs font-black text-gray-400 uppercase tracking-[0.2em] mb-4">Demo Accounts</h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-sm"><p className="text-gray-400">Admin</p><p className="font-bold text-gray-700">9999999999 / admin123</p></div>
              <div className="text-sm"><p className="text-gray-400">User</p><p className="font-bold text-gray-700">8888888888 / user123</p></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;