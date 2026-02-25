import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Phone, UserPlus, LogIn, Pill, User, ShieldCheck, AlertCircle } from "lucide-react";

const Login = () => {
  const navigate = useNavigate();
  const [isRegister, setIsRegister] = useState(false);
  const [formData, setFormData] = useState({ name: "", mobile: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleAuth = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const endpoint = isRegister ? "/auth/register" : "/auth/login";
      const res = await axios.post(`http://localhost:8000${endpoint}`, formData);
      
      localStorage.setItem("authUser", JSON.stringify(res.data));
      if (res.data.role === "admin") navigate("/admin");
      else navigate("/user");
    } catch (err) {
      setError(err.response?.data?.detail || "Authentication Failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-[#0F172A] p-6">
      <div className="w-full max-w-md bg-[#1E293B] rounded-[3rem] p-12 shadow-2xl border border-slate-800">
        <div className="flex flex-col items-center mb-10 text-center">
          <div className="bg-blue-600 p-4 rounded-3xl text-white mb-6 shadow-xl shadow-blue-500/20"><Pill size={40}/></div>
          <h2 className="text-3xl font-black text-white tracking-tight">Pharmacy AI</h2>
          <p className="text-slate-400 font-bold mt-2 uppercase tracking-widest text-[10px]">Level-3 Agentic System</p>
        </div>

        <form onSubmit={handleAuth} className="space-y-4">
          {isRegister && (
            <div className="relative group">
              <User className="absolute left-5 top-5 text-slate-500 group-focus-within:text-blue-500 transition-colors" size={20}/>
              <input required className="w-full bg-slate-900 border-2 border-slate-800 rounded-2xl py-5 pl-14 pr-6 text-white font-bold focus:border-blue-500 outline-none transition-all" 
                placeholder="Full Name" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})}/>
            </div>
          )}
          <div className="relative group">
            <Phone className="absolute left-5 top-5 text-slate-500 group-focus-within:text-blue-500 transition-colors" size={20}/>
            <input required className="w-full bg-slate-900 border-2 border-slate-800 rounded-2xl py-5 pl-14 pr-6 text-white font-bold focus:border-blue-500 outline-none transition-all" 
              placeholder="Mobile Number" value={formData.mobile} onChange={e => setFormData({...formData, mobile: e.target.value})}/>
          </div>

          {error && <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-xs font-bold flex items-center gap-2 animate-pulse"><AlertCircle size={16}/>{error}</div>}

          <button type="submit" disabled={loading} className="w-full bg-blue-600 hover:bg-blue-500 text-white py-6 rounded-3xl font-black text-sm uppercase tracking-[0.2em] mt-8 shadow-xl shadow-blue-500/10 transition-all flex items-center justify-center gap-3">
            {loading ? "..." : isRegister ? <><UserPlus size={20}/> Create Account</> : <><LogIn size={20}/> Sign In</>}
          </button>
        </form>

        <button onClick={() => setIsRegister(!isRegister)} className="w-full text-slate-500 font-bold text-xs mt-8 hover:text-blue-400 transition-colors">
          {isRegister ? "Already have an account? Sign In" : "New Patient? Register Here"}
        </button>
      </div>
    </div>
  );
};

export default Login;