import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import { Send, Mic, Pill, User, Bot, Trash2, Loader2, LogOut, MessageSquare, ShoppingCart, Clock, Volume2, VolumeX, Paperclip, X } from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";

const translations = {
  en: {
    title: "Pharmacy Assistant", activeUser: "Active User",
    welcome: "Welcome back", botIntro: "I am your AI pharmacist. How can I help you today?",
    inputPlaceholder: "How can I help you today?", logout: "Logout",
    actions: ["Paracetamol Info", "Order 2 Paracetamol"], loading: "Consulting database...",
    historyBtn: "Order History", backToChat: "Back to Chat"
  },
  hi: {
    title: "फार्मेसी सहायक", activeUser: "सक्रिय उपयोगकर्ता",
    welcome: "आपका स्वागत है", botIntro: "मैं आपका एआई फार्मासिस्ट हूं। आज मैं आपकी क्या मदद कर सकता हूं?",
    inputPlaceholder: "आज मैं आपकी क्या मदद कर सकता हूं?", logout: "लॉगआउट",
    actions: ["पैरासिटामोल जानकारी", "2 पैरासिटामोल ऑर्डर करें"], loading: "डेटाबेस की जाँच हो रही है...",
    historyBtn: "ऑर्डर इतिहास", backToChat: "चैट पर वापस जाएं"
  },
  mr: {
    title: "फार्मसी सहाय्यक", activeUser: "सक्रिय वापरकर्ता",
    welcome: "पुन्हा स्वागत आहे", botIntro: "मी तुमचा एआय फार्मासिस्ट आहे. आज मी तुम्हाला कशी मदत करू शकतो?",
    inputPlaceholder: "आज मी तुम्हाला कशी मदत करू शकतो?", logout: "लॉगआउट",
    actions: ["पॅरासिटामोल माहिती", "2 पॅरासिटामोल ऑर्डर करा"], loading: "डेटाबेस तपासत आहे...",
    historyBtn: "ऑर्डर इतिहास", backToChat: "चॅटवर परत जा"
  }
};

const cleanTextForSpeech = (text) => {
  return text
    .replace(/(\*\*|__)(.*?)\1/g, "$2")
    .replace(/(\*|_)(.*?)\1/g, "$2")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/#/g, "")
    .replace(/([\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF])/g, '')
    .trim();
};

const UserDashboard = () => {
  const navigate = useNavigate();
  const rawUser = localStorage.getItem("authUser");
  const authUser = rawUser ? JSON.parse(rawUser) : null;
  const [lang, setLang] = useState(authUser?.lang || "en");
  const t = translations[lang] || translations["en"];
  const [view, setView] = useState("chat"); 
  const [orders, setOrders] = useState([]);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([{ role: "bot", text: `### ${t.welcome}, **${authUser?.name || "User"}**! 👋\n${t.botIntro}` }]);
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isMuted, setIsMuted] = useState(false); 
  const [selectedImage, setSelectedImage] = useState(null);
  const fileInputRef = useRef(null);
  const recognitionRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);
      recognition.onresult = (e) => {
        const transcript = e.results[0][0].transcript;
        setInput((prev) => (prev ? prev + " " + transcript : transcript));
      };
      recognitionRef.current = recognition;
    }
    return () => window.speechSynthesis.cancel();
  }, []);

  useEffect(() => { if (!authUser) navigate("/"); }, [authUser, navigate]);
  const scrollToBottom = () => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); };
  useEffect(() => { if (view === "chat") scrollToBottom(); }, [messages, loading, view, selectedImage]);

  const handleLogout = () => { localStorage.removeItem("authUser"); navigate("/"); };

  const fetchOrders = async () => {
    if (view === "history") { setView("chat"); return; }
    try {
      const patientId = authUser?.mobile || "user_1";
      const res = await axios.get(`${API_BASE}/orders/history/${patientId}`);
      setOrders(res.data);
      setView("history");
    } catch (err) { alert("Failed to load history."); }
  };

  const speakText = (text, currentLang) => {
    if (isMuted || !window.speechSynthesis) return;
    window.speechSynthesis.cancel(); 
    const cleanedText = cleanTextForSpeech(text);
    const utterance = new SpeechSynthesisUtterance(cleanedText);
    if (currentLang === "hi") utterance.lang = "hi-IN";
    else if (currentLang === "mr") utterance.lang = "mr-IN";
    else utterance.lang = "en-IN"; 
    window.speechSynthesis.speak(utterance);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setSelectedImage(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handleSend = async (customMessage = null) => {
    const messageToSend = customMessage || input;
    if (!messageToSend.trim() && !selectedImage) return;

    const newUserMsg = { role: "user", text: messageToSend, image: selectedImage };
    setMessages((prev) => [...prev, newUserMsg]);
    setInput("");
    const imageToSend = selectedImage;
    setSelectedImage(null);
    setLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/chat`, {
        message: messageToSend,
        session_id: authUser?.mobile || "user_1",
        image: imageToSend,
        user_lang: lang // SYNCED: Sends current UI language to backend
      });
      
      const botReply = res.data.message || "Processed.";
      setMessages((prev) => [...prev, { role: "bot", text: botReply }]);
      speakText(botReply, lang);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "bot", text: "❌ Connection Error." }]);
    } finally { setLoading(false); }
  };

  const toggleListening = () => {
    if (isListening) { recognitionRef.current.stop(); } 
    else { 
      recognitionRef.current.lang = lang === "hi" ? "hi-IN" : lang === "mr" ? "mr-IN" : "en-US";
      recognitionRef.current.start(); 
    }
  };

  if (!authUser) return null;

  return (
    <div className="flex h-screen w-screen bg-white overflow-hidden">
      <div className="hidden lg:flex w-24 bg-blue-600 flex-col items-center py-10 gap-10 z-20">
         <div className="bg-white/20 p-4 rounded-[1.5rem] text-white"><Pill size={32} /></div>
         <div className="flex flex-col gap-10 mt-10">
            <button onClick={() => setView("chat")} className={`p-3 rounded-2xl transition-all ${view === "chat" ? "bg-white/20 text-white" : "text-blue-200 hover:text-white"}`}><MessageSquare size={24}/></button>
            <button onClick={fetchOrders} className={`p-3 rounded-2xl transition-all ${view === "history" ? "bg-white/20 text-white" : "text-blue-200 hover:text-white"}`}><Clock size={24}/></button>
         </div>
         <div className="mt-auto flex flex-col gap-6 items-center">
            {['en', 'hi', 'mr'].map(l => (
              <button key={l} onClick={() => { setLang(l); window.speechSynthesis.cancel(); }} className={`text-[10px] font-black uppercase ${lang === l ? "text-white underline" : "text-blue-300"}`}>{l}</button>
            ))}
            <button onClick={handleLogout} className="text-red-300 hover:text-red-100 mb-6"><LogOut size={24}/></button>
         </div>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden bg-[#F8FAFC]">
        <header className="bg-white border-b border-gray-100 px-10 py-6 flex justify-between items-center shadow-sm z-10">
          <div>
            <h1 className="text-3xl font-black text-gray-800 tracking-tight leading-none mb-1">{t.title}</h1>
            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">{t.activeUser}: {authUser?.mobile}</p>
          </div>
          <button onClick={fetchOrders} className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-600 font-bold rounded-xl border border-blue-100">
            {view === "history" ? <MessageSquare size={18}/> : <ShoppingCart size={18}/>}
            <span className="text-sm uppercase tracking-wider">{view === "history" ? t.backToChat : t.historyBtn}</span>
          </button>
        </header>

        {view === "chat" ? (
          <>
            <main className="flex-1 overflow-y-auto px-10 py-10">
              <div className="w-full space-y-10">
                {messages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-in`}>
                    <div className={`flex gap-6 max-w-[85%] ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                      <div className={`w-14 h-14 rounded-3xl flex items-center justify-center shrink-0 shadow-lg ${msg.role === "user" ? "bg-blue-600 text-white" : "bg-white text-blue-600 border border-gray-100"}`}>
                        {msg.role === "user" ? <User size={28} /> : <Bot size={28} />}
                      </div>
                      <div className={`p-8 rounded-[2.5rem] shadow-sm text-xl ${msg.role === "user" ? "bg-blue-600 text-white rounded-tr-none shadow-blue-100" : "bg-white text-gray-800 border border-gray-100 rounded-tl-none"}`}>
                        {msg.image && <img src={msg.image} alt="Prescription" className="max-w-full h-auto rounded-xl mb-4" style={{ maxHeight: '200px' }} />}
                        <div className="prose prose-lg max-w-none font-medium whitespace-pre-wrap"><ReactMarkdown>{msg.text}</ReactMarkdown></div>
                      </div>
                    </div>
                  </div>
                ))}
                {loading && <div className="flex gap-6 items-center"><div className="w-14 h-14 rounded-3xl bg-white border border-gray-100 flex items-center justify-center shadow-lg"><Loader2 size={24} className="text-blue-600 animate-spin" /></div><div className="text-sm text-gray-400 font-black uppercase tracking-widest animate-pulse">{t.loading}</div></div>}
                <div ref={messagesEndRef} />
              </div>
            </main>

            <footer className="bg-white border-t border-gray-100 p-10">
              <div className="w-full">
                {selectedImage && (
                  <div className="mb-4 flex items-center gap-4 animate-in">
                    <div className="relative"><img src={selectedImage} alt="Preview" className="h-20 w-20 object-cover rounded-xl border-2 border-blue-200"/><button onClick={() => setSelectedImage(null)} className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1"><X size={12}/></button></div>
                    <span className="text-sm text-blue-600 font-bold bg-blue-50 px-3 py-1 rounded-lg">Image attached</span>
                  </div>
                )}
                <div className="flex gap-4 mb-8 overflow-x-auto pb-2 scrollbar-hide">
                   <button onClick={() => handleSend(t.actions[0])} className="flex-shrink-0 px-8 py-3.5 bg-indigo-50 text-indigo-600 rounded-full text-xs font-black uppercase tracking-widest border border-indigo-100">{t.actions[0]}</button>
                   <button onClick={() => handleSend(t.actions[1])} className="flex-shrink-0 px-8 py-3.5 bg-green-50 text-green-600 rounded-full text-xs font-black uppercase tracking-widest border border-green-100">{t.actions[1]}</button>
                </div>
                <div className="relative flex gap-4 items-center">
                  <button onClick={() => { setIsMuted(!isMuted); window.speechSynthesis.cancel(); }} className={`p-5 rounded-full ${isMuted ? "bg-gray-100 text-gray-400" : "bg-blue-50 text-blue-600"}`}>{isMuted ? <VolumeX size={24} /> : <Volume2 size={24} />}</button>
                  <input type="file" ref={fileInputRef} onChange={handleFileChange} accept="image/*" className="hidden" />
                  <button onClick={() => fileInputRef.current.click()} className={`p-5 rounded-full ${selectedImage ? "bg-blue-600 text-white" : "bg-gray-50 text-gray-400"}`}><Paperclip size={24} /></button>
                  <button onClick={toggleListening} className={`p-5 rounded-full ${isListening ? "bg-red-50 border-2 border-red-500 text-red-500 animate-pulse" : "bg-gray-50 border-2 border-gray-100 text-gray-400"}`}><Mic size={28} /></button>
                  <div className="relative flex-1">
                    <input className="w-full bg-gray-50 border-2 border-gray-100 rounded-[2.5rem] px-8 py-8 pr-28 focus:outline-none focus:border-blue-500 text-2xl font-bold text-gray-700 shadow-inner" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSend()} placeholder={isListening ? "Listening..." : t.inputPlaceholder}/>
                    <button onClick={() => handleSend()} className="absolute right-4 top-4 p-6 bg-blue-600 text-white rounded-[2rem] shadow-xl disabled:bg-gray-300" disabled={loading || (!input.trim() && !selectedImage)}><Send size={32} /></button>
                  </div>
                </div>
              </div>
            </footer>
          </>
        ) : (
          <main className="flex-1 overflow-y-auto p-10 animate-in">
            <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-8">
              <h2 className="text-2xl font-black text-gray-800 mb-6 flex items-center gap-3"><Clock className="text-blue-500" /> Your Recent Orders</h2>
              {orders.length === 0 ? <div className="text-center py-20 text-gray-400"><ShoppingCart size={48} className="mx-auto mb-4 opacity-20" /><p className="text-lg font-bold">No orders found.</p></div> : (
                <div className="overflow-x-auto"><table className="w-full text-left">
                  <thead><tr className="bg-gray-50 text-gray-500 text-xs uppercase"><th className="p-4">Order ID</th><th className="p-4">Date</th><th className="p-4">Medicine</th><th className="p-4">Qty</th><th className="p-4">Total</th></tr></thead>
                  <tbody>{orders.map((order, idx) => (<tr key={idx} className="border-b border-gray-50 hover:bg-blue-50/50 transition-colors"><td className="p-4 text-sm font-mono">{order.order_id.substring(0, 8)}...</td><td className="p-4 text-sm">{new Date(order.created_at).toLocaleDateString()}</td><td className="p-4 font-bold">{order.product_name}</td><td className="p-4 text-center">{order.quantity}</td><td className="p-4 font-black text-blue-600">${order.total_price.toFixed(2)}</td></tr>))}</tbody>
                </table></div>
              )}
            </div>
          </main>
        )}
      </div>
    </div>
  );
};

export default UserDashboard;