import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { 
  ShieldCheck, Upload, Save, Edit2, TrendingUp, Package, 
  AlertCircle, CheckCircle, X, BarChart3, LineChart as LineChartIcon,
  BellRing, Calendar, User as UserIcon, MessageCircle, Mail
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";

const API_BASE = "http://127.0.0.1:8000";

const translations = {
  en: {
    portal: "Admin Portal", overview: "Overview", inventory: "Inventory", analytics: "Analytics", refills: "Refill Alerts",
    health: "System Health.", welcome: "Welcome, Admin. Database & AI Agents are Synced.",
    stats: ["Active Inventory", "7d Revenue", "Refills Due"],
    table: ["Product ID", "Medicine Name", "Stock Level", "Price", "Status", "Actions"],
    refillTable: ["Patient ID", "Medicine", "Next Needed", "Recommendation", "Action"],
    upload: "Bulk Sync Excel", logout: "Logout", otc: "OTC", rx: "Rx Required",
    empty: "No products found in database.", loading: "Querying AI Agents..."
  },
  hi: {
    portal: "एडमिन पोर्टल", overview: "अवलोकन", inventory: "इन्वेंटरी", analytics: "विश्लेषण", refills: "रिफिल अलर्ट",
    health: "सिस्टम स्वास्थ्य।", welcome: "नमस्ते एडमिन। डेटाबेस और एआई एजेंट सिंक्रनाइज़ हैं।",
    stats: ["सक्रिय सूची", "7दिन का राजस्व", "रिफिल देय"],
    table: ["उत्पाद आईडी", "दवा का नाम", "स्टॉक स्तर", "कीमत", "स्थिति", "कार्रवाई"],
    refillTable: ["रोगी आईडी", "दवा", "अगली आवश्यकता", "सिफारिश", "कार्रवाई"],
    upload: "एक्सेल सिंक करें", logout: "लॉगआउट", otc: "ओटीसी", rx: "नुस्खा आवश्यक",
    empty: "डेटाबेस में कोई उत्पाद नहीं मिला।", loading: "एआई एजेंटों से पूछताछ..."
  },
  mr: {
    portal: "अ‍ॅडमिन पोर्टल", overview: "आढावा", inventory: "इन्व्हेंटरी", analytics: "विश्लेषण", refills: "रिफिल अ‍ॅलर्ट",
    health: "सिस्टम आरोग्य।", welcome: "नमस्ते अ‍ॅडमिन. डेटाबेस आणि एआय एजंट सिंक्रोनाइझ झाले आहेत.",
    stats: ["सक्रिय इन्व्हेंटरी", "7दिवसांचा महसूल", "रिफिल बाकी"],
    table: ["उत्पादन आयडी", "औषधाचे नाव", "स्टॉक पातळी", "किंमत", "स्थिती", "कृती"],
    refillTable: ["रुग्ण आयडी", "औषध", "पुढील गरज", "शिफारस", "कृती"],
    upload: "एक्सेल सिंक करा", logout: "लॉगआउट", otc: "ओटीसी", rx: "प्रिस्क्रिप्शन आवश्यक",
    empty: "डेटाबेसमध्ये उत्पादने आढळली नाहीत.", loading: "AI एजंट तपासत आहे..."
  }
};

const AdminDashboard = () => {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("authUser"));
  const [lang, setLang] = useState(user?.lang || "en");
  const [activeTab, setActiveTab] = useState("overview");

  // --- DATA STATES ---
  const [inventory, setInventory] = useState([]);
  const [analytics, setAnalytics] = useState({ daily_trends: [], best_sellers: [] });
  const [alerts, setAlerts] = useState([]); // PROACTIVE REFILL ALERTS
  const [loading, setLoading] = useState(true);
  const [uploadStatus, setUploadStatus] = useState(null);
  
  // --- EDITING STATES ---
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ stock: 0, price: 0, prescription_required: false });

  const t = translations[lang];

  useEffect(() => {
    refreshAllData();
  }, []);

  const refreshAllData = async () => {
    setLoading(true);
    await fetchInventory();
    await fetchAnalytics();
    await fetchRefillAlerts();
    setLoading(false);
  };

  const fetchInventory = async () => {
    try {
      const res = await axios.get(`${API_BASE}/admin/inventory`);
      setInventory(res.data);
    } catch (err) { console.error("Inventory Fetch Error:", err); }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await axios.get(`${API_BASE}/admin/analytics/sales-report`);
      setAnalytics(res.data);
    } catch (err) { console.error("Analytics Fetch Error:", err); }
  };

  const fetchRefillAlerts = async () => {
    try {
      const res = await axios.get(`${API_BASE}/refill/refill-alerts`);
      setAlerts(res.data);
    } catch (err) { console.error("Refill Alerts Error:", err); }
  };

  const handleBulkUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    setUploadStatus({ type: "loading", msg: "⚙️ Syncing Excel & AI Memory..." });
    try {
      const res = await axios.post(`${API_BASE}/admin/upload-inventory`, formData);
      setUploadStatus({ type: "success", msg: `✅ Sync Done! Added: ${res.data.added}, Updated: ${res.data.updated}` });
      await fetchInventory();
    } catch (err) {
      setUploadStatus({ type: "error", msg: "❌ Sync Failed. Check Excel headers." });
    } finally { e.target.value = null; }
  };

  const handleSaveEdit = async (id) => {
    try {
      await axios.put(`${API_BASE}/admin/inventory/${id}`, editForm);
      setEditingId(null);
      await fetchInventory();
      setUploadStatus({ type: "success", msg: "✅ Product Updated Successfully." });
    } catch (err) { alert("Error saving product."); }
  };

  // --- NEW: HANDLE NOTIFICATIONS ---
  const handleNotify = async (patientId, product, type) => {
    setUploadStatus({ type: "loading", msg: `Sending ${type} to ${patientId}...` });
    try {
      await axios.post(`${API_BASE}/refill/notify`, {
        patient_id: patientId,
        product_name: product,
        message_type: type
      });
      setUploadStatus({ type: "success", msg: `✅ ${type} Sent Successfully!` });
    } catch (err) {
      setUploadStatus({ type: "error", msg: "❌ Failed to send notification." });
    }
  };

  const handleLogout = () => { localStorage.removeItem("authUser"); navigate("/"); };

  return (
    <div className="h-screen w-screen bg-[#F8FAFC] flex flex-col font-sans overflow-hidden">
      {/* HEADER */}
      <header className="bg-white border-b border-gray-200 px-10 py-5 flex justify-between items-center shadow-sm z-50">
        <div className="flex items-center gap-4">
          <ShieldCheck className="text-indigo-600" size={32} />
          <div>
            <h1 className="text-2xl font-black text-gray-800 tracking-tight">{t.portal}</h1>
            <div className="flex gap-2 mt-1">
              {['en', 'hi', 'mr'].map(l => (
                <button key={l} onClick={() => setLang(l)} className={`text-[10px] font-black px-2 py-0.5 rounded border transition-all ${lang === l ? "bg-indigo-600 text-white border-indigo-600 shadow-md" : "text-gray-400 border-gray-200"}`}>{l.toUpperCase()}</button>
              ))}
            </div>
          </div>
        </div>

        <nav className="flex bg-gray-100 p-1.5 rounded-2xl gap-2 border border-gray-200">
          {["overview", "inventory", "refills", "analytics"].map((tab) => (
            <button key={tab} onClick={() => setActiveTab(tab)}
              className={`px-6 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${activeTab === tab ? "bg-white text-indigo-600 shadow-md scale-105" : "text-gray-400"}`}>
              {t[tab]}
            </button>
          ))}
        </nav>

        <button onClick={handleLogout} className="px-6 py-3 bg-red-50 text-red-600 rounded-2xl font-black text-xs uppercase tracking-widest border border-red-100 hover:bg-red-100 transition-all">{t.logout}</button>
      </header>

      {/* MAIN VIEW */}
      <main className="flex-1 overflow-y-auto p-10">
        {uploadStatus && (
          <div className={`mb-8 p-5 rounded-3xl flex items-center justify-between border shadow-sm animate-in zoom-in ${uploadStatus.type === 'success' ? 'bg-green-50 text-green-700 border-green-200' : uploadStatus.type === 'error' ? 'bg-red-50 text-red-700 border-red-200' : 'bg-blue-50 text-blue-700 border-blue-200'}`}>
            <span className="font-bold flex items-center gap-2">
              {uploadStatus.type === 'success' ? <CheckCircle size={18}/> : uploadStatus.type === 'error' ? <AlertCircle size={18}/> : <Package size={18} className="animate-spin"/>}
              {uploadStatus.msg}
            </span>
            <button onClick={() => setUploadStatus(null)}><X size={20}/></button>
          </div>
        )}

        {/* OVERVIEW TAB */}
        {activeTab === "overview" && (
          <div className="space-y-10">
            <div className="bg-indigo-600 rounded-[3rem] p-16 text-white shadow-2xl relative overflow-hidden group">
               <h2 className="text-6xl font-black mb-4 tracking-tighter">{t.health}</h2>
               <p className="text-indigo-100 text-xl font-medium max-w-2xl opacity-90">{t.welcome}</p>
               <ShieldCheck size={300} className="absolute -right-20 -bottom-20 text-white/10 rotate-12" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <StatCard icon={<Package/>} label={t.stats[0]} value={inventory.length} color="blue" />
              <StatCard icon={<TrendingUp/>} label={t.stats[1]} value={`$${analytics.daily_trends.reduce((a, b) => a + b.revenue, 0).toFixed(2)}`} color="green" />
              <StatCard icon={<BellRing/>} label={t.stats[2]} value={alerts.length} color="orange" />
            </div>
          </div>
        )}

        {/* INVENTORY TAB */}
        {activeTab === "inventory" && (
          <div className="bg-white rounded-[3rem] border border-gray-200 shadow-2xl overflow-hidden min-h-[600px] animate-in slide-in-from-bottom-5">
            <div className="p-10 border-b border-gray-100 flex justify-between items-center bg-gray-50/30">
              <h3 className="text-3xl font-black text-gray-800 tracking-tighter">{t.inventory}</h3>
              <label className="cursor-pointer flex items-center gap-3 px-10 py-4 bg-indigo-600 text-white rounded-[1.5rem] font-black uppercase tracking-widest text-sm shadow-xl shadow-indigo-100">
                <Upload size={20} /> {t.upload}
                <input type="file" className="hidden" accept=".xlsx" onChange={handleBulkUpload} />
              </label>
            </div>
            {loading ? <LoadingPlaceholder text={t.loading} /> : (
              <table className="w-full text-left">
                <thead className="bg-gray-50 text-gray-400 text-[10px] uppercase font-black tracking-[0.2em] border-b border-gray-100">
                  <tr>{t.table.map(head => <th key={head} className="px-10 py-6">{head}</th>)}</tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {inventory.map((item) => (
                    <tr key={item.product_id} className="hover:bg-gray-50/50 transition-all group">
                      <td className="px-10 py-8 font-mono text-xs text-gray-400">{item.product_id}</td>
                      <td className="px-10 py-8 font-black text-gray-800 text-lg">{item.name}</td>
                      {editingId === item.product_id ? (
                        <EditRow form={editForm} setForm={setEditForm} onSave={() => handleSaveEdit(item.product_id)} onCancel={() => setEditingId(null)} t={t} />
                      ) : (
                        <DisplayRow item={item} t={t} onEdit={() => { setEditingId(item.product_id); setEditForm(item); }} />
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* REFILL ALERTS TAB (NEW PREDICTIVE INTELLIGENCE) */}
        {activeTab === "refills" && (
          <div className="bg-white rounded-[3rem] border border-gray-200 shadow-2xl overflow-hidden min-h-[600px] animate-in slide-in-from-bottom-5">
            <div className="p-10 border-b border-gray-100 bg-orange-50/30 flex justify-between items-center">
              <h3 className="text-3xl font-black text-gray-800 tracking-tighter flex items-center gap-4">
                <BellRing className="text-orange-500" /> {t.refills}
              </h3>
              <span className="bg-orange-100 text-orange-600 px-6 py-2 rounded-full font-black text-xs uppercase tracking-widest border border-orange-200">AI Predictive Engine Active</span>
            </div>
            {loading ? <LoadingPlaceholder text={t.loading} /> : (
              <table className="w-full text-left">
                <thead className="bg-gray-50 text-gray-400 text-[10px] uppercase font-black tracking-[0.2em] border-b border-gray-100">
                  <tr>{t.refillTable.map(head => <th key={head} className="px-10 py-6">{head}</th>)}</tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {alerts.map((alert, idx) => (
                    <tr key={idx} className="hover:bg-orange-50/30 transition-all">
                      <td className="px-10 py-8 flex items-center gap-3 font-bold text-gray-600">
                        <UserIcon className="text-gray-300" size={18} /> {alert.patient_id}
                      </td>
                      <td className="px-10 py-8 font-black text-gray-800 text-lg">{alert.product_name}</td>
                      <td className="px-10 py-8 font-bold text-orange-600">
                        <div className="flex items-center gap-2"><Calendar size={16}/> {alert.expected_refill_date}</div>
                      </td>
                      <td className="px-10 py-8 uppercase text-[10px] font-black tracking-widest text-orange-400">{alert.message}</td>
                      <td className="px-10 py-8 text-right">
                        <div className="flex justify-end gap-2">
                          <button onClick={() => handleNotify(alert.patient_id, alert.product_name, 'whatsapp')} className="p-3 bg-green-50 text-green-600 rounded-xl hover:bg-green-600 hover:text-white transition-all shadow-sm hover:shadow-md" title="WhatsApp Reminder"><MessageCircle size={20}/></button>
                          <button onClick={() => handleNotify(alert.patient_id, alert.product_name, 'email')} className="p-3 bg-blue-50 text-blue-600 rounded-xl hover:bg-blue-600 hover:text-white transition-all shadow-sm hover:shadow-md" title="Send Email"><Mail size={20}/></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            {alerts.length === 0 && !loading && <div className="p-32 text-center text-gray-300 font-black text-2xl">No predictive alerts generated by Agent.</div>}
          </div>
        )}

        {/* ANALYTICS TAB */}
        {activeTab === "analytics" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 h-[600px] animate-in zoom-in">
            <AnalyticsCard title="Revenue Trend" icon={<LineChartIcon className="text-indigo-600"/>} data={analytics.daily_trends} type="line" />
            <AnalyticsCard title="Best Sellers" icon={<BarChart3 className="text-orange-500"/>} data={analytics.best_sellers} type="bar" />
          </div>
        )}
      </main>
    </div>
  );
};

// --- SUB-COMPONENTS ---

const StatCard = ({ icon, label, value, color }) => (
  <div className="bg-white p-10 rounded-[3rem] border border-gray-100 shadow-xl flex items-center gap-8 group hover:scale-105 transition-transform duration-300">
    <div className={`p-8 rounded-[2rem] shadow-lg transition-transform group-hover:rotate-12 ${color === 'blue' ? 'bg-blue-50 text-blue-600' : color === 'green' ? 'bg-green-50 text-green-600' : 'bg-orange-50 text-orange-600'}`}>{icon}</div>
    <div>
      <p className="text-gray-400 text-sm font-black uppercase tracking-[0.2em] mb-1">{label}</p>
      <p className="text-5xl font-black text-gray-800 tracking-tighter">{value}</p>
    </div>
  </div>
);

const LoadingPlaceholder = ({ text }) => <div className="p-32 text-center text-gray-300 font-black text-2xl animate-pulse">{text}</div>;

const DisplayRow = ({ item, t, onEdit }) => (
  <>
    <td className="px-10 py-8"><span className={`px-5 py-2 rounded-full text-[10px] font-black uppercase tracking-widest border ${item.stock < 10 ? 'bg-red-50 text-red-600 border-red-100' : 'bg-green-50 text-green-600 border-green-100'}`}>{item.stock} Units</span></td>
    <td className="px-10 py-8 font-black text-indigo-600 text-2xl">${item.price.toFixed(2)}</td>
    <td className="px-10 py-8 uppercase text-[10px] font-black tracking-widest text-gray-400">{item.prescription_required ? t.rx : t.otc}</td>
    <td className="px-10 py-8 text-right opacity-0 group-hover:opacity-100 transition-opacity">
      <button onClick={onEdit} className="p-4 bg-indigo-50 text-indigo-600 rounded-2xl hover:bg-indigo-600 hover:text-white transition-all"><Edit2 size={22}/></button>
    </td>
  </>
);

const EditRow = ({ form, setForm, onSave, onCancel, t }) => (
  <>
    <td className="px-10 py-8"><input type="number" className="w-24 border-2 border-indigo-100 rounded-xl p-2 font-bold" value={form.stock} onChange={e=>setForm({...form, stock: e.target.value})}/></td>
    <td className="px-10 py-8"><input type="number" className="w-24 border-2 border-indigo-100 rounded-xl p-2 font-bold" value={form.price} onChange={e=>setForm({...form, price: e.target.value})}/></td>
    <td className="px-10 py-8">
      <select className="border-2 border-indigo-100 rounded-xl p-2 font-bold" value={form.prescription_required} onChange={e=>setForm({...form, prescription_required: e.target.value === 'true'})}>
        <option value="true">{t.rx}</option><option value="false">{t.otc}</option>
      </select>
    </td>
    <td className="px-10 py-8 text-right flex justify-end gap-2 mt-4 mr-4">
      <button onClick={onSave} className="bg-green-500 text-white p-3 rounded-xl shadow-lg"><Save size={18}/></button>
      <button onClick={onCancel} className="bg-gray-200 text-gray-400 p-3 rounded-xl"><X size={18}/></button>
    </td>
  </>
);

const AnalyticsCard = ({ title, icon, data, type }) => (
  <div className="bg-white p-12 rounded-[3.5rem] border border-gray-200 shadow-2xl flex flex-col">
    <h3 className="text-3xl font-black text-gray-800 mb-10 tracking-tighter flex items-center gap-4">{icon} {title}</h3>
    <ResponsiveContainer width="100%" height="100%">
      {type === 'line' ? (
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
          <XAxis dataKey="date" hide /><YAxis axisLine={false} tickLine={false} tick={{fill: '#94A3B8', fontSize: 14, fontWeight: 700}} /><Tooltip />
          <Line type="monotone" dataKey="revenue" stroke="#4F46E5" strokeWidth={8} dot={{r: 8, fill: '#4F46E5', strokeWidth: 4, stroke: '#fff'}} />
        </LineChart>
      ) : (
        <BarChart data={data} layout="vertical">
          <XAxis type="number" hide /><YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{fill: '#475569', fontSize: 14, fontWeight: 800}} width={140} /><Bar dataKey="quantity" fill="#F97316" radius={[0, 20, 20, 0]} barSize={50} />
        </BarChart>
      )}
    </ResponsiveContainer>
  </div>
);

export default AdminDashboard;