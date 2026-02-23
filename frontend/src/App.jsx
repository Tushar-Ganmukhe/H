import { useState, useEffect, useRef } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import { Send, Mic, Bell, Pill, User, Bot, Trash2, Loader2, PlusCircle, AlertCircle } from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    { 
      role: "bot", 
      text: "### Welcome to Agentic Pharmacy Assistant 👋\nI am your AI pharmacist. I can help you with:\n1. **Ordering Medicines** (e.g., 'Order 2 Paracetamol')\n2. **Refill Alerts** (Click the button below)\n3. **Drug Information**\n\nHow can I help you today?" 
    }
  ]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (customMessage = null) => {
    const messageToSend = customMessage || input;
    if (!messageToSend.trim()) return;

    const userMsg = { role: "user", text: messageToSend };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      // Fixed: Removed trailing slash to match FastAPI router prefix
      const res = await axios.post(`${API_BASE}/chat`, {
        message: messageToSend,
        session_id: "user_1",
      });

      const botText = res.data.message || res.data.reason || "I have processed your request.";
      setMessages((prev) => [...prev, { role: "bot", text: botText }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev, 
        { role: "bot", text: "❌ **Connection Error**: Make sure your backend is running at `localhost:8000` and CORS is enabled." }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/refill/refill-alerts`);
      let alertMsg = "### 🔔 Medication Refill Alerts\n";
      if (!res.data || res.data.length === 0) {
        alertMsg += "All your prescriptions are up to date.";
      } else {
        res.data.forEach(a => {
          alertMsg += `- **${a.product_name}**: Needed by ${a.expected_refill_date}\n`;
        });
      }
      setMessages((prev) => [...prev, { role: "bot", text: alertMsg }]);
    } catch (error) {
      setMessages((prev) => [...prev, { role: "bot", text: "Failed to fetch alerts." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#F8FAFC]">
      {/* HEADER */}
      <header className="bg-white border-b border-gray-200 px-8 py-4 flex justify-between items-center shadow-sm">
        <div className="flex items-center gap-4">
          <div className="bg-blue-600 p-2.5 rounded-2xl shadow-lg shadow-blue-100">
            <Pill className="text-white" size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-800 tracking-tight">Pharmacy Assistant</h1>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span className="text-[11px] font-bold text-gray-400 uppercase tracking-widest">Secure Server Active</span>
            </div>
          </div>
        </div>
        <button onClick={() => setMessages([messages[0]])} className="p-2.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all">
          <Trash2 size={20} />
        </button>
      </header>

      {/* CHAT AREA */}
      <main className="flex-1 overflow-y-auto px-4 py-8">
        <div className="max-w-3xl mx-auto space-y-8">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-in fade-in slide-in-from-bottom-2`}>
              <div className={`flex gap-4 max-w-[85%] ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                <div className={`w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 shadow-sm
                  ${msg.role === "user" ? "bg-blue-600 text-white" : "bg-white border border-gray-200 text-blue-600"}`}>
                  {msg.role === "user" ? <User size={20} /> : <Bot size={20} />}
                </div>
                <div className={`p-5 rounded-3xl shadow-sm leading-relaxed ${
                  msg.role === "user" 
                    ? "bg-blue-600 text-white rounded-tr-none" 
                    : "bg-white text-gray-800 border border-gray-100 rounded-tl-none"
                }`}>
                  <div className="prose prose-sm max-w-none prose-headings:text-inherit prose-p:m-0">
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  </div>
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex gap-4 items-center">
              <div className="w-10 h-10 rounded-2xl bg-white border border-gray-200 flex items-center justify-center shadow-sm">
                <Loader2 size={20} className="text-blue-600 animate-spin" />
              </div>
              <div className="text-sm text-gray-400 font-medium animate-pulse">Consulting pharmaceutical database...</div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* FOOTER / INPUT */}
      <footer className="bg-white border-t border-gray-200 p-6">
        <div className="max-w-3xl mx-auto">
          <div className="flex gap-3 mb-6">
            <button onClick={fetchAlerts} className="flex items-center gap-2 px-4 py-2 bg-white border border-orange-200 text-orange-600 rounded-full text-xs font-bold hover:bg-orange-50 transition-all shadow-sm">
              <Bell size={14} /> Refill Alerts
            </button>
            <button onClick={() => handleSend("Order 2 strips of Paracetamol")} className="flex items-center gap-2 px-4 py-2 bg-white border border-blue-200 text-blue-600 rounded-full text-xs font-bold hover:bg-blue-50 transition-all shadow-sm">
              <PlusCircle size={14} /> Order Paracetamol
            </button>
          </div>

          <div className="relative group">
            <input
              className="w-full bg-gray-50 border border-gray-200 rounded-3xl px-6 py-5 pr-16 focus:outline-none focus:ring-4 focus:ring-blue-500/10 focus:bg-white focus:border-blue-500 transition-all shadow-inner text-gray-700"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="How can I help you today?"
            />
            <button 
              onClick={() => handleSend()}
              className="absolute right-3 top-3 p-3 bg-blue-600 text-white rounded-2xl hover:bg-blue-700 transition-all shadow-lg active:scale-95 disabled:bg-gray-300"
              disabled={loading}
            >
              <Send size={20} />
            </button>
          </div>
          <div className="flex justify-center mt-4">
            <button onClick={() => {}} className="text-gray-400 hover:text-blue-600 transition-colors">
              <Mic size={24} />
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;