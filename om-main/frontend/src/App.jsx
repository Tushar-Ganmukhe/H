import { useState, useEffect, useRef } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import { 
  Send, Mic, Bell, Pill, User, Bot, Trash2, 
  Loader2, PlusCircle, History, ArrowLeft, Calendar, Package 
} from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";

// ===== LOGIN FORM COMPONENT (separate to avoid hook ordering issues) =====
function LoginForm({ onLogin }) {
  const [loginRole, setLoginRole] = useState("user");
  const [loginStep, setLoginStep] = useState("role");
  const [showRegister, setShowRegister] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [loginData, setLoginData] = useState({
    phone: "",
    password: "",
    age: "",
    name: "",
    shopId: "",
  });

  const isAdmin = loginRole === "admin";

  const handleSubmit = async () => {
    setError("");
    
    if (!loginData.password.trim()) {
      setError("Password is required");
      return;
    }

    if (showRegister) {
      // REGISTER
      if (!loginData.name.trim()) {
        setError("Name is required");
        return;
      }
      if (isAdmin && !loginData.shopId.trim()) {
        setError("Shop ID is required");
        return;
      }
      if (!isAdmin && !loginData.phone.trim()) {
        setError("Phone number is required");
        return;
      }

      setLoading(true);
      try {
        const res = await axios.post(`${API_BASE}/auth/register`, {
          name: loginData.name,
          phone: isAdmin ? null : loginData.phone,
          shop_id: isAdmin ? loginData.shopId : null,
          password: loginData.password,
          age: isAdmin ? null : (loginData.age ? parseInt(loginData.age) : null),
        });

        if (res.data.success) {
          // Trigger login with the new credentials
          onLogin(loginRole, res.data.user, res.data.session_id);
        } else {
          setError(res.data.message || "Registration failed");
        }
      } catch (err) {
        setError(err.response?.data?.detail || "Registration error: " + err.message);
      } finally {
        setLoading(false);
      }
    } else {
      // LOGIN
      if (isAdmin && !loginData.shopId.trim()) {
        setError("Shop ID is required");
        return;
      }
      if (!isAdmin && !loginData.phone.trim()) {
        setError("Phone number is required");
        return;
      }

      setLoading(true);
      try {
        const res = await axios.post(`${API_BASE}/auth/login`, {
          phone: isAdmin ? null : loginData.phone,
          shop_id: isAdmin ? loginData.shopId : null,
          password: loginData.password,
        });

        if (res.data.success) {
          onLogin(loginRole, res.data.user, res.data.session_id);
        } else {
          setError(res.data.message || "Login failed");
        }
      } catch (err) {
        setError(err.response?.data?.detail || "Login error: " + err.message);
      } finally {
        setLoading(false);
      }
    }
  };

  if (loginStep === "role") {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-blue-50 to-blue-100">
        <div className="bg-white p-10 rounded-2xl shadow-xl w-full max-w-md">
          <h1 className="text-4xl font-extrabold text-center mb-6 text-blue-700">
            Agentic Pharmacy
          </h1>
          <p className="text-center text-gray-600 mb-6">
            Choose how you want to proceed
          </p>
          <div className="flex flex-col gap-4">
            <select
              value={loginRole}
              onChange={(e) => setLoginRole(e.target.value)}
              className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="user">User (chatbot)</option>
              <option value="admin">Admin (inventory)</option>
            </select>
            <button
              onClick={() => setLoginStep("credentials")}
              className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Continue
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center h-screen bg-gradient-to-br from-blue-50 to-blue-100">
      <div className="bg-white p-10 rounded-2xl shadow-xl w-full max-w-md">
        <h1 className="text-3xl font-bold text-center mb-6 text-blue-700">
          {showRegister ? "Register" : "Login"} as {isAdmin ? "Admin" : "User"}
        </h1>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div className="flex flex-col gap-4">
          {!isAdmin && (
            <>
              {showRegister && (
                <input
                  type="text"
                  placeholder="Name"
                  value={loginData.name}
                  onChange={(e) => setLoginData({ ...loginData, name: e.target.value })}
                  className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              )}
              <input
                type="text"
                placeholder="Phone number"
                value={loginData.phone}
                onChange={(e) => setLoginData({ ...loginData, phone: e.target.value })}
                className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {showRegister && (
                <input
                  type="number"
                  placeholder="Age"
                  value={loginData.age}
                  onChange={(e) => setLoginData({ ...loginData, age: e.target.value })}
                  className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              )}
              <input
                type="password"
                placeholder="Password"
                value={loginData.password}
                onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </>
          )}
          {isAdmin && (
            <>
              {showRegister && (
                <input
                  type="text"
                  placeholder="Name"
                  value={loginData.name}
                  onChange={(e) => setLoginData({ ...loginData, name: e.target.value })}
                  className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              )}
              <input
                type="text"
                placeholder="Shop ID"
                value={loginData.shopId}
                onChange={(e) => setLoginData({ ...loginData, shopId: e.target.value })}
                className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                type="password"
                placeholder="Password"
                value={loginData.password}
                onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                className="border border-gray-300 p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </>
          )}

          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400"
          >
            {loading ? "Processing..." : showRegister ? "Register" : "Login"}
          </button>

          <button
            onClick={() => {
              setShowRegister(!showRegister);
              setError("");
            }}
            className="text-sm text-blue-500 hover:underline mt-2"
          >
            {showRegister ? "Already have an account? Login" : "Don't have an account? Register"}
          </button>
        </div>
      </div>
    </div>
  );
}

function App() {
  // ⚠️ ALL HOOKS MUST BE CALLED HERE IN SAME ORDER EVERY RENDER
  
  // Login / Role State
  const [role, setRole] = useState(null);
  const [user, setUser] = useState(null); // Store logged-in user data
  const [sessionId, setSessionId] = useState(null); // store backend session/user id

  // Navigation State
  const [view, setView] = useState("chat");

  // Chat States
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    { 
      role: "bot",
      text: "### Welcome to Agentic Pharmacy Assistant 👋\nI am your AI pharmacist. I can help you with:\n1. **Ordering Medicines** (e.g., 'Order 2 Paracetamol')\n2. **Refill Alerts** (Click the button below)\n3. **Drug Information\n\nHow can I help you today?" 
    }
  ]);
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);

  // History States
  const [orderHistory, setOrderHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Refs
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  // Effects - all called in same order every render
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = "en-US";

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        setIsListening(false);
      };

      recognitionRef.current.onerror = () => setIsListening(false);
      recognitionRef.current.onend = () => setIsListening(false);
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, view]);

  // Helper function to toggle microphone
  const toggleMic = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      if (!recognitionRef.current) {
        alert("Speech recognition is not supported in this browser. Please use Chrome or Edge.");
        return;
      }
      setIsListening(true);
      recognitionRef.current.start();
    }
  };

  // Handle login - receives user data from auth endpoint
  const handleLogin = (selectedRole, userData, sessionIdFromServer) => {
    setRole(selectedRole);
    setUser(userData);
    setSessionId(sessionIdFromServer || userData?.id || null);
  };

  // Show login form if not authenticated
  if (!role) {
    return <LoginForm onLogin={handleLogin} />;
  }

  // if signed in as admin, render admin dashboard
  if (role === "admin") {
    return <AdminView logout={() => { setRole(null); setUser(null); }} />;
  }

  
  // --- CHAT LOGIC ---
  const handleSend = async (customMessage = null) => {
    const messageToSend = customMessage || input;
    if (!messageToSend.trim()) return;

    const userMsg = { role: "user", text: messageToSend };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/chat`, {
        message: messageToSend,
        session_id: sessionId || "guest",
      });

      const botText = res.data.message || res.data.reason || "I have processed your request.";
      setMessages((prev) => [...prev, { role: "bot", text: botText }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev, 
        { role: "bot", text: "❌ **Connection Error**: Make sure your backend is running at `localhost:8000`." }
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

  // --- HISTORY LOGIC ---
  const openHistory = async () => {
    setView("history");
    setLoadingHistory(true);
    try {
      const res = await axios.get(`${API_BASE}/patients/1/history`);
      setOrderHistory(res.data);
    } catch (error) {
      console.error("Failed to load history", error);
    } finally {
      setLoadingHistory(false);
    }
  };


  // ==========================================
  // VIEW: HISTORY PAGE
  // ==========================================
  if (view === "history") {
    return (
      <div className="flex flex-col h-screen bg-[#F8FAFC]">
        <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center gap-4 shadow-sm">
          <button 
            onClick={() => setView("chat")} 
            className="p-2.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all"
          >
            <ArrowLeft size={24} />
          </button>
          <div>
            <h1 className="text-xl font-bold text-gray-800 tracking-tight">Your Order History</h1>
            <p className="text-sm text-gray-400">Past prescriptions and purchases</p>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            {loadingHistory ? (
              <div className="flex justify-center py-20">
                <Loader2 size={40} className="text-blue-600 animate-spin" />
              </div>
            ) : orderHistory.length === 0 ? (
              <div className="text-center py-20 text-gray-400">
                <Package size={64} className="mx-auto mb-4 opacity-20" />
                <p>No order history found for this patient.</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {orderHistory.map((item, index) => {
                  const productName = item["Product Name"] || item.product_name || "Unknown Product";
                  const quantity = item["Quantity"] || item.quantity || "-";
                  const date = item["Purchase date"] || item.purchase_date || "Unknown Date";
                  const dosage = item["Dosage frequency"] || item.dosage_frequency || "N/A";

                  return (
                    <div key={index} className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm flex flex-col sm:flex-row justify-between sm:items-center gap-4 hover:shadow-md transition-all">
                      <div className="flex items-start gap-4">
                        <div className="bg-blue-50 p-3 rounded-xl text-blue-600">
                          <Package size={24} />
                        </div>
                        <div>
                          <h3 className="font-bold text-gray-800 text-lg">{productName}</h3>
                          <div className="flex items-center gap-3 text-sm text-gray-500 mt-1">
                            <span className="flex items-center gap-1"><Calendar size={14}/> {date}</span>
                            <span className="bg-gray-100 px-2 py-0.5 rounded-md text-xs font-medium">Qty: {quantity}</span>
                          </div>
                          <p className="text-xs text-gray-400 mt-2">Dosage: {dosage}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="inline-block px-3 py-1 bg-green-50 text-green-600 font-bold text-xs rounded-full border border-green-200 uppercase tracking-wide">
                          Completed
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </main>
      </div>
    );
  }

  // ==========================================
  // VIEW: CHAT PAGE
  // ==========================================
  return (
    <div className="flex flex-col h-screen bg-[#F8FAFC]">
      {/* HEADER */}
      <header className="bg-white border-b border-gray-200 px-8 py-4 flex justify-between items-center shadow-sm">
        <div className="flex items-center gap-4">
          <img src="/logo192.png" alt="logo" className="h-8" />
          <div>
            <h1 className="text-xl font-bold text-gray-800 tracking-tight">Pharmacy Assistant</h1>
            {user && (
              <p className="text-sm text-gray-500">Hello, {user.name}!</p>
            )}
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span className="text-[11px] font-bold text-gray-400 uppercase tracking-widest">Secure Server Active</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={openHistory} 
            className="flex items-center gap-2 px-4 py-2 bg-gray-50 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all font-semibold text-sm border border-gray-200"
          >
            <History size={18} /> History
          </button>
          
          <button 
            onClick={() => setMessages([messages[0]])} 
            className="p-2.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all"
          >
            <Trash2 size={20} />
          </button>
          <button
            onClick={() => { setRole(null); setUser(null); }}
            className="ml-4 px-3 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition"
          >
            Logout
          </button>
        </div>
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

          <div className="flex items-center gap-3 relative group">
            {/* ✅ NEW: MICROPHONE BUTTON */}
            <button 
              onClick={toggleMic}
              className={`p-4 rounded-2xl transition-all shadow-md flex items-center justify-center ${
                isListening 
                ? "bg-red-500 text-white animate-pulse shadow-red-200" 
                : "bg-gray-100 text-gray-500 hover:bg-blue-50 hover:text-blue-600"
              }`}
            >
              <Mic size={22} />
            </button>

            <div className="relative flex-1">
              <input
                className="w-full bg-gray-50 border border-gray-200 rounded-3xl px-6 py-5 pr-16 focus:outline-none focus:ring-4 focus:ring-blue-500/10 focus:bg-white focus:border-blue-500 transition-all shadow-inner text-gray-700"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder={isListening ? "Listening... speak now" : "How can I help you today?"}
              />
              <button 
                onClick={() => handleSend()}
                className="absolute right-3 top-3 p-3 bg-blue-600 text-white rounded-2xl hover:bg-blue-700 transition-all shadow-lg active:scale-95 disabled:bg-gray-300"
                disabled={loading}
              >
                <Send size={20} />
              </button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

// ---------------------------
// Admin dashboard component
// ---------------------------
function AdminView({ logout }) {
  const [products, setProducts] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    axios
      .get(`${API_BASE}/admin/products`)
      .then((res) => {
        setProducts(res.data.products || []);
        setAnalysis(res.data.analysis || null);
      })
      .catch((err) => console.error("admin fetch error", err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-col h-screen bg-[#F8FAFC]">
      <header className="bg-teal-600 border-b border-teal-700 px-8 py-4 flex justify-between items-center shadow-sm">
        <div className="flex items-center gap-3">
          <img src="/logo192.png" alt="logo" className="h-8" />
          <h1 className="text-xl font-bold text-white">Admin Dashboard</h1>
        </div>
        <button
          onClick={logout}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
        >
          Logout
        </button>
      </header>

      <main className="flex-1 overflow-auto p-6">
        {loading ? (
          <div className="flex justify-center py-20">
            <Loader2 size={40} className="text-teal-600 animate-spin" />
          </div>
        ) : (
          <>
            {analysis && (
              <div className="mb-6 space-y-1 text-sm text-gray-800 bg-white p-4 rounded shadow">
                <p>Total products: <span className="text-teal-600 font-bold">{analysis.total_products}</span></p>
                <p>Avg price: <span className="text-teal-600 font-bold">{analysis.average_price.toFixed(2)}</span></p>
                <p>Min price: <span className="text-teal-600 font-bold">{analysis.min_price}</span></p>
                <p>Max price: <span className="text-teal-600 font-bold">{analysis.max_price}</span></p>
              </div>
            )}

            <div className="overflow-auto">
              <table className="w-full table-auto border-collapse text-sm admin-table font-semibold">
                <thead>
                  <tr className="bg-teal-600">
                    <th className="border px-2 py-1 font-bold text-white">ID</th>
                    <th className="border px-2 py-1 font-bold text-white">Name</th>
                    <th className="border px-2 py-1 font-bold text-white">PZN</th>
                    <th className="border px-2 py-1 font-bold text-white">Package</th>
                    <th className="border px-2 py-1 font-bold text-white">Price</th>
                    <th className="border px-2 py-1 font-bold text-white">Stock</th>
                    <th className="border px-2 py-1 font-bold text-white">Prescription</th>
                    <th className="border px-2 py-1 font-bold text-white">Description (DE)</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map((p, i) => (
                    <tr key={i} className="bg-white hover:bg-teal-100 even:bg-gray-50">
                      <td className="border px-2 py-1 text-black">{p['product id'] || p.product_id}</td>
                      <td className="border px-2 py-1 text-black">{p['product name'] || p.product_name}</td>
                      <td className="border px-2 py-1 text-black">{p.pzn}</td>
                      <td className="border px-2 py-1 text-black">{p['package size'] || p.package_size}</td>
                      <td className="border px-2 py-1 text-black">{p['price rec'] || p.price}</td>
                      <td className="border px-2 py-1 text-black">{p.stock ?? p['stock'] ?? ''}</td>
                      <td className="border px-2 py-1 text-black">{p.prescription ?? p['prescription_rec'] ?? p['prescription record'] ?? p['prescription_required'] ?? ''}</td>
                      <td className="border px-2 py-1 text-black">{p.descriptions || p.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default App;