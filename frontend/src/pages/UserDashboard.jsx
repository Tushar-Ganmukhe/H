import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import { Send, Mic, Bell, Pill, User, Bot, Trash2, Loader2, PlusCircle, LogOut } from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";

const UserDashboard = () => {
  const navigate = useNavigate();
  const authUser = JSON.parse(localStorage.getItem("authUser"));
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([{ 
      role: "bot", 
      text: `### Welcome back, **${authUser?.name || "User"}**! 👋\nI am your AI pharmacist. How can I help you today?` 
  }]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  useEffect(() => { scrollToBottom(); }, [messages, loading]);

  const handleLogout = () => { localStorage.removeItem("authUser"); navigate("/"); };

  const handleSend = async (customMessage = null) => {
    const messageToSend = customMessage || input;
    if (!messageToSend.trim()) return;
    setMessages((prev) => [...prev, { role: "user", text: messageToSend }]);
    setInput("");
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/chat`, {
        message: messageToSend,
        session_id: authUser?.mobile || "user_1",
      });
      setMessages((prev) => [...prev, { role: "bot", text: res.data.message || "Processed." }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "bot", text: "❌ Connection error." }]);
    } finally { setLoading(false); }
  };

  return (
    <div className="flex h-screen w-screen bg-[#F8FAFC] overflow-hidden">
      {/* Sidebar - Optional for full app feel */}
      <div className="hidden lg:flex w-24 bg-blue-600 flex-col items-center py-10 gap-10">
         <div className="bg-white/20 p-3 rounded-2xl text-white"><Pill size={32} /></div>
         <div className="mt-auto mb-10 flex flex-col gap-8">
            <button onClick={() => {}} className="text-blue-200 hover:text-white transition-colors"><Bell size={24}/></button>
            <button onClick={handleLogout} className="text-red-300 hover:text-red-100 transition-all"><LogOut size={24}/></button>
         </div>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header - Stretches Full Width */}
        <header className="bg-white border-b border-gray-200 px-10 py-6 flex justify-between items-center z-10">
          <div>
            <h1 className="text-2xl font-black text-gray-800 tracking-tight">Pharmacy Assistant</h1>
            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Active User: {authUser?.mobile}</p>
          </div>
          <div className="flex gap-4">
             <button onClick={() => setMessages([messages[0]])} className="p-3 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-2xl transition-all"><Trash2 size={20}/></button>
             <button onClick={handleLogout} className="lg:hidden flex items-center gap-2 px-5 py-2.5 bg-red-50 text-red-600 rounded-2xl font-black text-xs transition-all tracking-widest uppercase">Logout</button>
          </div>
        </header>

        {/* Chat Area - Stretches Full Width */}
        <main className="flex-1 overflow-y-auto px-10 py-10">
          <div className="w-full max-w-full space-y-10">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-in slide-in-from-bottom-5 duration-500`}>
                <div className={`flex gap-6 max-w-[80%] ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                  <div className={`w-14 h-14 rounded-3xl flex items-center justify-center shrink-0 shadow-lg ${msg.role === "user" ? "bg-blue-600 text-white" : "bg-white text-blue-600 border border-gray-100"}`}>
                    {msg.role === "user" ? <User size={28} /> : <Bot size={28} />}
                  </div>
                  <div className={`p-8 rounded-[2.5rem] shadow-sm leading-relaxed text-lg ${msg.role === "user" ? "bg-blue-600 text-white rounded-tr-none" : "bg-white text-gray-800 border border-gray-100 rounded-tl-none"}`}>
                    <ReactMarkdown className="prose prose-lg max-w-none prose-headings:text-inherit prose-p:m-0 font-medium">
                      {msg.text}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-6 items-center">
                <div className="w-14 h-14 rounded-3xl bg-white border border-gray-200 flex items-center justify-center shadow-lg"><Loader2 size={24} className="text-blue-600 animate-spin" /></div>
                <div className="text-sm text-gray-400 font-black uppercase tracking-widest animate-pulse">Consulting pharmaceutical database...</div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </main>

        {/* Footer Input - Stretches Full Width */}
        <footer className="bg-white border-t border-gray-200 p-10">
          <div className="w-full">
            <div className="flex gap-4 mb-8">
               <button onClick={() => handleSend("Tell me about Paracetamol")} className="px-8 py-3 bg-indigo-50 text-indigo-600 rounded-full text-xs font-black uppercase tracking-widest hover:bg-indigo-100 border border-indigo-100 transition-all">Paracetamol Info</button>
               <button onClick={() => handleSend("Order 2 Paracetamol")} className="px-8 py-3 bg-green-50 text-green-600 rounded-full text-xs font-black uppercase tracking-widest hover:bg-green-100 border border-green-100 transition-all">Order Now</button>
            </div>
            <div className="relative">
              <input
                className="w-full bg-gray-50 border-2 border-gray-100 rounded-[2.5rem] px-10 py-7 pr-24 focus:outline-none focus:ring-8 focus:ring-blue-500/5 focus:bg-white focus:border-blue-500 transition-all text-xl font-bold text-gray-700 shadow-inner"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder="How can I help you today?"
              />
              <button onClick={() => handleSend()} className="absolute right-4 top-4 p-5 bg-blue-600 text-white rounded-[1.8rem] hover:bg-blue-700 transition-all shadow-xl active:scale-95 disabled:bg-gray-300" disabled={loading}>
                <Send size={28} />
              </button>
            </div>
            <div className="flex justify-center mt-6">
               <button className="text-gray-300 hover:text-blue-600 transition-colors transform hover:scale-125 duration-300"><Mic size={32}/></button>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default UserDashboard;