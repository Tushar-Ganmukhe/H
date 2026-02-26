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

// Helper: Cleans Markdown & Emojis so the speech sounds natural
const cleanTextForSpeech = (text) => {
  return text
    .replace(/(\*\*|__)(.*?)\1/g, "$2") // Remove bold
    .replace(/(\*|_)(.*?)\1/g, "$2") // Remove italics
    .replace(/`([^`]+)`/g, "$1") // Remove inline code
    .replace(/#/g, "") // Remove headers
    .replace(/([\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF])/g, '') // Remove emojis
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
  const [messages, setMessages] = useState([
    { 
      role: "bot", 
      text: `### ${t.welcome}, **${authUser?.name || "User"}**! 👋\n${t.botIntro}` 
    }
  ]);
  const [loading, setLoading] = useState(false);
  
  // VOICE STATES
  const [isListening, setIsListening] = useState(false);
  const [isMuted, setIsMuted] = useState(false); 
  
  // IMAGE UPLOAD STATE
  const [selectedImage, setSelectedImage] = useState(null);
  const fileInputRef = useRef(null);
  
  const recognitionRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Initialize Speech Recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);
      recognition.onerror = (e) => {
        console.error("Speech recognition error:", e.error);
        setIsListening(false);
      };
      recognition.onresult = (e) => {
        const transcript = e.results[0][0].transcript;
        setInput((prev) => (prev ? prev + " " + transcript : transcript));
      };
      
      recognitionRef.current = recognition;
    }
    
    return () => window.speechSynthesis.cancel();
  }, []);

  useEffect(() => {
    if (!authUser) navigate("/");
  }, [authUser, navigate]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (view === "chat") scrollToBottom();
  }, [messages, loading, view, selectedImage]);

  const handleLogout = () => {
    localStorage.removeItem("authUser");
    navigate("/");
  };

  const fetchOrders = async () => {
    if (view === "history") {
      setView("chat");
      return;
    }
    try {
      const patientId = authUser?.mobile || "user_1";
      const res = await axios.get(`${API_BASE}/orders/history/${patientId}`);
      setOrders(res.data);
      setView("history");
    } catch (err) {
      console.error("Failed to fetch order history:", err);
      alert("Failed to load history. Is the backend running?");
    }
  };

  const speakText = (text, currentLang) => {
    if (isMuted || !window.speechSynthesis) return;

    window.speechSynthesis.cancel(); 
    const cleanedText = cleanTextForSpeech(text);
    const utterance = new SpeechSynthesisUtterance(cleanedText);

    if (currentLang === "hi") utterance.lang = "hi-IN";
    else if (currentLang === "mr") utterance.lang = "mr-IN";
    else utterance.lang = "en-IN"; 

    utterance.rate = 1.0; 
    window.speechSynthesis.speak(utterance);
  };

  // --- HANDLE IMAGE UPLOAD ---
  const handleFileClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setSelectedImage(reader.result); // Sets Base64 string
      };
      reader.readAsDataURL(file);
    }
  };

  const clearImage = () => {
    setSelectedImage(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSend = async (customMessage = null) => {
    const messageToSend = customMessage || input;
    if (!messageToSend.trim() && !selectedImage) return;

    // Add user message to UI
    const newUserMsg = { 
      role: "user", 
      text: messageToSend,
      image: selectedImage // Store image for local UI display if needed
    };
    
    setMessages((prev) => [...prev, newUserMsg]);
    setInput("");
    const imageToSend = selectedImage; // Capture current image before clearing
    clearImage(); // Clear image from input immediately
    setLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/chat`, {
        message: messageToSend,
        session_id: authUser?.mobile || "user_1",
        image: imageToSend // Pass base64 string to API
      });
      
      const botReply = res.data.message || "Processed.";
      setMessages((prev) => [...prev, { role: "bot", text: botReply }]);
      speakText(botReply, lang);

    } catch (err) {
      const errorMsg = "Sorry, I could not connect to the server.";
      setMessages((prev) => [...prev, { role: "bot", text: `❌ ${errorMsg}` }]);
      speakText(errorMsg, lang);
    } finally {
      setLoading(false);
    }
  };

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert("Voice input is not supported in this browser. Please use Chrome or Edge.");
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
    } else {
      if (lang === "hi") recognitionRef.current.lang = "hi-IN";
      else if (lang === "mr") recognitionRef.current.lang = "mr-IN";
      else recognitionRef.current.lang = "en-US";
      
      recognitionRef.current.start();
    }
  };

  if (!authUser) return null;

  return (
    <div className="flex h-screen w-screen bg-white overflow-hidden">
      
      {/* SIDEBAR */}
      <div className="hidden lg:flex w-24 bg-blue-600 flex-col items-center py-10 gap-10 shadow-2xl z-20">
         <div className="bg-white/20 p-4 rounded-[1.5rem] text-white"><Pill size={32} /></div>
         <div className="flex flex-col gap-10 mt-10">
            <button 
              onClick={() => setView("chat")}
              className={`p-3 rounded-2xl shadow-inner transition-all ${view === "chat" ? "bg-white/20 text-white" : "text-blue-200 hover:text-white"}`}>
              <MessageSquare size={24}/>
            </button>
            <button 
              onClick={fetchOrders}
              className={`p-3 rounded-2xl shadow-inner transition-all ${view === "history" ? "bg-white/20 text-white" : "text-blue-200 hover:text-white"}`}>
              <Clock size={24}/>
            </button>
         </div>
         <div className="mt-auto flex flex-col gap-6 items-center">
            {['en', 'hi', 'mr'].map(l => (
              <button key={l} onClick={() => {
                setLang(l);
                window.speechSynthesis.cancel(); 
              }} className={`text-[10px] font-black uppercase ${lang === l ? "text-white underline" : "text-blue-300"}`}>{l}</button>
            ))}
            <button onClick={handleLogout} className="text-red-300 hover:text-red-100 mb-6 transition-all"><LogOut size={24}/></button>
         </div>
      </div>

      {/* MAIN AREA */}
      <div className="flex-1 flex flex-col overflow-hidden bg-[#F8FAFC]">
        
        {/* HEADER */}
        <header className="bg-white border-b border-gray-100 px-10 py-6 flex justify-between items-center shadow-sm z-10">
          <div>
            <h1 className="text-3xl font-black text-gray-800 tracking-tight leading-none mb-1">{t.title}</h1>
            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">{t.activeUser}: {authUser?.mobile}</p>
          </div>
          <div className="flex gap-4">
            <button 
              onClick={fetchOrders} 
              className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-600 font-bold rounded-xl hover:bg-blue-100 transition-all border border-blue-100">
              {view === "history" ? <MessageSquare size={18}/> : <ShoppingCart size={18}/>}
              <span className="text-sm uppercase tracking-wider">{view === "history" ? t.backToChat : t.historyBtn}</span>
            </button>
            {view === "chat" && (
              <button onClick={() => {
                setMessages([messages[0]]);
                window.speechSynthesis.cancel();
              }} className="p-4 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-2xl transition-all border border-transparent hover:border-red-100">
                <Trash2 size={22}/>
              </button>
            )}
          </div>
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
                        
                        {/* Render User Uploaded Image if exists */}
                        {msg.image && (
                          <div className="mb-4">
                            <img src={msg.image} alt="Prescription" className="max-w-full h-auto rounded-xl border-2 border-white/30" style={{ maxHeight: '200px' }} />
                          </div>
                        )}

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
                {/* PREVIEW AREA FOR UPLOADED IMAGE */}
                {selectedImage && (
                  <div className="mb-4 flex items-center gap-4 animate-in slide-in-from-bottom-2">
                    <div className="relative">
                      <img src={selectedImage} alt="Preview" className="h-20 w-20 object-cover rounded-xl border-2 border-blue-200 shadow-md" />
                      <button onClick={clearImage} className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 shadow hover:bg-red-600">
                        <X size={12} />
                      </button>
                    </div>
                    <span className="text-sm text-blue-600 font-bold bg-blue-50 px-3 py-1 rounded-lg">Image attached</span>
                  </div>
                )}

                <div className="flex gap-4 mb-8 overflow-x-auto scrollbar-hide pb-2">
                   <button onClick={() => handleSend("Tell me about Paracetamol")} className="flex-shrink-0 px-8 py-3.5 bg-indigo-50 text-indigo-600 rounded-full text-xs font-black uppercase tracking-widest hover:bg-indigo-100 border border-indigo-100 transition-all">{t.actions[0]}</button>
                   <button onClick={() => handleSend("Order 2 Paracetamol")} className="flex-shrink-0 px-8 py-3.5 bg-green-50 text-green-600 rounded-full text-xs font-black uppercase tracking-widest hover:bg-green-100 border border-green-100 transition-all">{t.actions[1]}</button>
                </div>
                
                <div className="relative group flex gap-4 items-center">
                  
                  {/* MUTE TOGGLE BUTTON */}
                  <button 
                    onClick={() => {
                      setIsMuted(!isMuted);
                      if (!isMuted) window.speechSynthesis.cancel(); 
                    }} 
                    className={`flex-shrink-0 p-5 rounded-full transition-all duration-300 shadow-sm ${
                      isMuted ? "bg-gray-100 text-gray-400 hover:bg-gray-200" : "bg-blue-50 text-blue-600 hover:bg-blue-100"
                    }`}
                  >
                    {isMuted ? <VolumeX size={24} /> : <Volume2 size={24} />}
                  </button>

                  {/* FILE UPLOAD BUTTON */}
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    onChange={handleFileChange} 
                    accept="image/*" 
                    className="hidden" 
                  />
                  <button 
                    onClick={handleFileClick}
                    title="Upload Prescription"
                    className={`flex-shrink-0 p-5 rounded-full transition-all duration-300 shadow-sm ${
                      selectedImage ? "bg-blue-600 text-white shadow-blue-300" : "bg-gray-50 text-gray-400 hover:text-blue-600 hover:bg-blue-50"
                    }`}
                  >
                    <Paperclip size={24} />
                  </button>

                  {/* MIC BUTTON */}
                  <button 
                    onClick={toggleListening} 
                    className={`flex-shrink-0 p-5 rounded-full transition-all duration-300 shadow-sm ${
                      isListening ? "bg-red-50 border-2 border-red-500 text-red-500 animate-pulse shadow-red-200" : "bg-gray-50 border-2 border-gray-100 text-gray-400 hover:text-blue-600 hover:border-blue-200 hover:bg-blue-50"
                    }`}
                  >
                    <Mic size={28} />
                  </button>

                  <div className="relative flex-1">
                    <input
                      className="w-full bg-gray-50 border-2 border-gray-100 rounded-[2.5rem] px-8 py-8 pr-28 focus:outline-none focus:ring-[12px] focus:ring-blue-500/5 focus:bg-white focus:border-blue-500 transition-all text-2xl font-bold text-gray-700 shadow-inner"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleSend()}
                      placeholder={isListening ? "Listening..." : t.inputPlaceholder}
                    />
                    <button onClick={() => handleSend()} className="absolute right-4 top-4 p-6 bg-blue-600 text-white rounded-[2rem] hover:bg-blue-700 transition-all shadow-xl shadow-blue-200 active:scale-95 disabled:bg-gray-300" disabled={loading || (!input.trim() && !selectedImage)}>
                      <Send size={32} />
                    </button>
                  </div>

                </div>
              </div>
            </footer>
          </>
        ) : (
          /* HISTORY VIEW */
          <main className="flex-1 overflow-y-auto p-10 animate-in">
            <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-8">
              <h2 className="text-2xl font-black text-gray-800 mb-6 flex items-center gap-3">
                <Clock className="text-blue-500" /> Your Recent Orders
              </h2>
              
              {orders.length === 0 ? (
                <div className="text-center py-20 text-gray-400">
                  <ShoppingCart size={48} className="mx-auto mb-4 opacity-20" />
                  <p className="text-lg font-bold">No orders found yet.</p>
                  <p className="text-sm">Start chatting to place your first order!</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-gray-50 text-gray-500 text-xs uppercase tracking-widest">
                        <th className="p-4 rounded-tl-2xl">Order ID</th>
                        <th className="p-4">Date</th>
                        <th className="p-4">Product Name</th>
                        <th className="p-4">Qty</th>
                        <th className="p-4 rounded-tr-2xl">Total Price</th>
                      </tr>
                    </thead>
                    <tbody>
                      {orders.map((order, idx) => (
                        <tr key={idx} className="border-b border-gray-50 hover:bg-blue-50/50 transition-colors">
                          <td className="p-4 text-sm font-mono text-gray-500">{order.order_id.substring(0, 8)}...</td>
                          <td className="p-4 text-sm font-medium text-gray-600">{new Date(order.created_at).toLocaleDateString()}</td>
                          <td className="p-4 text-base font-bold text-gray-800">{order.product_name}</td>
                          <td className="p-4 text-sm font-bold text-gray-600 text-center">{order.quantity}</td>
                          <td className="p-4 text-base font-black text-blue-600">${order.total_price.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </main>
        )}
      </div>
    </div>
  );
};

export default UserDashboard;