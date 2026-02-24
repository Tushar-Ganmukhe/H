import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import { Send, Mic, Bell, Pill, User, Bot, Trash2, Loader2, LogOut, MessageSquare, Info, ShoppingCart } from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";

const translations = {
  en: {
    title: "Pharmacy Assistant", activeUser: "Active User",
    welcome: "Welcome back", botIntro: "I am your AI pharmacist. How can I help you today?",
    inputPlaceholder: "How can I help you today?", logout: "Logout",
    actions: ["Paracetamol Info", "Order 2 Paracetamol"], loading: "Consulting database..."
  },
  hi: {
    title: "फार्मेसी सहायक", activeUser: "सक्रिय उपयोगकर्ता",
    welcome: "आपका स्वागत है", botIntro: "मैं आपका एआई फार्मासिस्ट हूं। आज मैं आपकी क्या मदद कर सकता हूं?",
    inputPlaceholder: "आज मैं आपकी क्या मदद कर सकता हूं?", logout: "लॉगआउट",
    actions: ["पैरासिटामोल जानकारी", "2 पैरासिटामोल ऑर्डर करें"], loading: "डेटाबेस की जाँच हो रही है..."
  },
  mr: {
    title: "फार्मसी सहाय्यक", activeUser: "सक्रिय वापरकर्ता",
    welcome: "पुन्हा स्वागत आहे", botIntro: "मी तुमचा एआय फार्मासिस्ट आहे. आज मी तुम्हाला कशी मदत करू शकतो?",
    inputPlaceholder: "आज मी तुम्हाला कशी मदत करू शकतो?", logout: "लॉगआउट",
    actions: ["पॅरासिटामोल माहिती", "2 पॅरासिटामोल ऑर्डर करा"], loading: "डेटाबेस तपासत आहे..."
  }
};

const UserDashboard = () => {
  const navigate = useNavigate();
  
  // Safety Guard: Check session
  const rawUser = localStorage.getItem("authUser");
  const authUser = rawUser ? JSON.parse(rawUser) : null;

  const [lang, setLang] = useState(authUser?.lang || "en");
  const t = translations[lang] || translations["en"];

  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    { 
      role: "bot", 
      text: `### ${t.welcome}, **${authUser?.name || "User"}**! 👋\n${t.botIntro}` 
    }
  ]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (!authUser) navigate("/");
  }, [authUser, navigate]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleLogout = () => {
    localStorage.removeItem("authUser");
    navigate("/");
  };

  const handleSend = async (customMessage = null) => {
    const messageToSend = customMessage || input;
    if (!messageToSend.trim()) return;

    setMessages((prev) => [...prev, { role: "user", text: messageToSend }]);
    setInput("");
    setLoading(true);

    try {
      // Sync: sending mobile ensures Langfuse and Agent memory are connected
      const res = await axios.post(`${API_BASE}/chat`, {
        message: messageToSend,
        session_id: authUser?.mobile || "user_1",
      });
      setMessages((prev) => [...prev, { role: "bot", text: res.data.message || "Processed." }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "bot", text: "❌ Connection error." }]);
    } finally {
      setLoading(false);
    }
  };

  if (!authUser) return null;

  return (
    <div className="flex h-screen w-screen bg-white overflow-hidden">
      
      {/* SIDEBAR */}
      <div className="hidden lg:flex w-24 bg-blue-600 flex-col items-center py-10 gap-10 shadow-2xl z-20">
         <div className="bg-white/20 p-4 rounded-[1.5rem] text-white"><Pill size={32} /></div>
         <div className="flex flex-col gap-10 mt-10">
            <button className="text-white bg-white/10 p-3 rounded-2xl shadow-inner"><MessageSquare size={24}/></button>
            <button className="text-blue-200 hover:text-white transition-all"><Bell size={24}/></button>
         </div>
         <div className="mt-auto flex flex-col gap-6 items-center">
            {['en', 'hi', 'mr'].map(l => (
              <button key={l} onClick={() => setLang(l)} className={`text-[10px] font-black uppercase ${lang === l ? "text-white underline" : "text-blue-300"}`}>{l}</button>
            ))}
            <button onClick={handleLogout} className="text-red-300 hover:text-red-100 mb-6 transition-all"><LogOut size={24}/></button>
         </div>
      </div>

      {/* CHAT AREA */}
      <div className="flex-1 flex flex-col overflow-hidden bg-[#F8FAFC]">
        
        <header className="bg-white border-b border-gray-100 px-10 py-6 flex justify-between items-center shadow-sm z-10">
          <div>
            <h1 className="text-3xl font-black text-gray-800 tracking-tight leading-none mb-1">{t.title}</h1>
            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">{t.activeUser}: {authUser?.mobile}</p>
          </div>
          <button onClick={() => setMessages([messages[0]])} className="p-4 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-2xl transition-all border border-transparent hover:border-red-100">
            <Trash2 size={22}/>
          </button>
        </header>

        <main className="flex-1 overflow-y-auto px-10 py-10">
          <div className="w-full space-y-10">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-in`}>
                <div className={`flex gap-6 max-w-[85%] ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                  <div className={`w-14 h-14 rounded-3xl flex items-center justify-center shrink-0 shadow-lg ${msg.role === "user" ? "bg-blue-600 text-white" : "bg-white text-blue-600 border border-gray-100"}`}>
                    {msg.role === "user" ? <User size={28} /> : <Bot size={28} />}
                  </div>
                  
                  {/* FIX: className moved to wrapper div to prevent crash */}
                  <div className={`p-8 rounded-[2.5rem] shadow-sm text-xl ${
                    msg.role === "user" ? "bg-blue-600 text-white rounded-tr-none shadow-blue-100" : "bg-white text-gray-800 border border-gray-100 rounded-tl-none"
                  }`}>
                    <div className="prose prose-lg max-w-none prose-p:m-0 font-medium whitespace-pre-wrap prose-headings:text-inherit prose-strong:text-inherit">
                      <ReactMarkdown>{msg.text}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-6 items-center">
                <div className="w-14 h-14 rounded-3xl bg-white border border-gray-100 flex items-center justify-center shadow-lg"><Loader2 size={24} className="text-blue-600 animate-spin" /></div>
                <div className="text-sm text-gray-400 font-black uppercase tracking-widest animate-pulse">{t.loading}</div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </main>

        <footer className="bg-white border-t border-gray-100 p-10">
          <div className="w-full">
            <div className="flex gap-4 mb-8 overflow-x-auto scrollbar-hide pb-2">
               <button onClick={() => handleSend("Tell me about Paracetamol")} className="flex-shrink-0 px-8 py-3.5 bg-indigo-50 text-indigo-600 rounded-full text-xs font-black uppercase tracking-widest hover:bg-indigo-100 border border-indigo-100 transition-all">{t.actions[0]}</button>
               <button onClick={() => handleSend("Order 2 Paracetamol")} className="flex-shrink-0 px-8 py-3.5 bg-green-50 text-green-600 rounded-full text-xs font-black uppercase tracking-widest hover:bg-green-100 border border-green-100 transition-all">{t.actions[1]}</button>
            </div>
            <div className="relative group">
              <input
                className="w-full bg-gray-50 border-2 border-gray-100 rounded-[2.5rem] px-10 py-8 pr-28 focus:outline-none focus:ring-[12px] focus:ring-blue-500/5 focus:bg-white focus:border-blue-500 transition-all text-2xl font-bold text-gray-700 shadow-inner"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder={t.inputPlaceholder}
              />
              <button onClick={() => handleSend()} className="absolute right-4 top-4 p-6 bg-blue-600 text-white rounded-[2rem] hover:bg-blue-700 transition-all shadow-xl shadow-blue-200 active:scale-95 disabled:bg-gray-300" disabled={loading}>
                <Send size={32} />
              </button>
            </div>
            <div className="flex justify-center mt-8">
               <button className="text-gray-300 hover:text-blue-600 transition-all transform hover:scale-125 duration-300"><Mic size={40}/></button>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default UserDashboard;