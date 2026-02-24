import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Phone, Lock, AlertCircle, LogIn, Pill, ShieldCheck } from "lucide-react";

const translations = {
  en: {
    title: "Smart Pharmacy Management.",
    subtitle: "Real-time inventory, AI assistance, and advanced analytics.",
    login: "Login",
    mobile: "Mobile Number",
    password: "Password",
    btn: "Login Securely",
    demo: "Demo Accounts",
    error: "Invalid mobile number or password."
  },
  hi: {
    title: "स्मार्ट फार्मेसी प्रबंधन।",
    subtitle: "वास्तविक समय सूची, एआई सहायता और उन्नत विश्लेषण।",
    login: "लॉगिन",
    mobile: "मोबाइल नंबर",
    password: "पासवर्ड",
    btn: "सुरक्षित लॉगिन करें",
    demo: "डेमो अकाउंट",
    error: "अमान्य मोबाइल नंबर या पासवर्ड।"
  },
  mr: {
    title: "स्मार्ट फार्मसी व्यवस्थापन।",
    subtitle: "रिअल-टाइम इन्व्हेंटरी, एआय सहाय्य आणि प्रगत विश्लेषण.",
    login: "लॉगिन",
    mobile: "मोबाईल नंबर",
    password: "पासवर्ड",
    btn: "सुरक्षित लॉगिन करा",
    demo: "डेमो खाती",
    error: "अवैध मोबाईल नंबर किंवा पासवर्ड."
  }
};

const Login = () => {
  const [lang, setLang] = useState("en");
  const [mobile, setMobile] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const t = translations[lang];

  const handleLogin = (e) => {
    e.preventDefault();
    setError("");
    // Check credentials
    if ((mobile === "9999999999" && password === "admin123") || (mobile === "8888888888" && password === "user123")) {
      const role = mobile === "9999999999" ? "admin" : "user";
      localStorage.setItem("authUser", JSON.stringify({ 
        mobile, 
        role, 
        name: role === 'admin' ? 'System Admin' : 'Regular User',
        lang 
      }));
      navigate(role === "admin" ? "/admin" : "/user");
    } else {
      setError(t.error);
    }
  };

  return (
    <div className="flex h-screen w-screen bg-white overflow-hidden relative">
      {/* Language Toggle */}
      <div className="absolute top-8 right-8 z-50 flex gap-2 bg-white/80 backdrop-blur-md p-2 rounded-2xl border border-gray-100 shadow-xl">
        {['en', 'hi', 'mr'].map((l) => (
          <button key={l} onClick={() => setLang(l)} 
            className={`px-4 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${lang === l ? "bg-blue-600 text-white shadow-lg" : "text-gray-400 hover:bg-gray-50"}`}>
            {l}
          </button>
        ))}
      </div>

      {/* Left Decoration */}
      <div className="hidden lg:flex w-1/2 bg-blue-600 items-center justify-center p-12 relative overflow-hidden">
        <div className="relative z-10 text-white max-w-lg">
          <div className="bg-white/20 p-4 rounded-3xl w-fit mb-8 backdrop-blur-md"><Pill size={48} /></div>
          <h1 className="text-6xl font-black tracking-tighter mb-6 leading-tight">{t.title}</h1>
          <p className="text-blue-100 text-xl font-medium opacity-90">{t.subtitle}</p>
        </div>
        <div className="absolute top-[-10%] left-[-10%] w-80 h-80 bg-blue-500 rounded-full blur-3xl opacity-50"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-blue-700 rounded-full blur-3xl opacity-50"></div>
      </div>

      {/* Right Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-[#F8FAFC]">
        <div className="max-w-md w-full">
          <h2 className="text-4xl font-black text-gray-900 mb-2 tracking-tight">{t.login}</h2>
          <form onSubmit={handleLogin} className="space-y-6 mt-10">
            {error && <div className="bg-red-50 text-red-600 p-4 rounded-2xl text-sm font-bold flex items-center gap-3 border border-red-100"><AlertCircle size={20} /> {error}</div>}
            
            <div className="space-y-2">
              <label className="text-sm font-black text-gray-700 uppercase tracking-wider ml-1">{t.mobile}</label>
              <input type="text" value={mobile} onChange={(e) => setMobile(e.target.value)} className="w-full bg-white border-2 border-gray-100 rounded-2xl px-6 py-4 focus:border-blue-600 outline-none font-bold text-gray-700 shadow-sm transition-all" placeholder="9999999999" />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-black text-gray-700 uppercase tracking-wider ml-1">{t.password}</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full bg-white border-2 border-gray-100 rounded-2xl px-6 py-4 focus:border-blue-600 outline-none font-bold text-gray-700 shadow-sm transition-all" placeholder="••••••••" />
            </div>

            <button type="submit" className="w-full bg-blue-600 text-white font-black rounded-2xl py-5 flex items-center justify-center gap-3 hover:bg-blue-700 transition-all shadow-xl shadow-blue-100 active:scale-95 text-lg">
              <LogIn size={22} /> {t.btn}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;