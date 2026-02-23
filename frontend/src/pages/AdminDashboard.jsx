import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { 
  ShieldCheck, LogOut, Upload, Save, Edit2, TrendingUp, Package, 
  AlertCircle, CheckCircle, Search, DollarSign, X, BarChart3, LineChart as LineChartIcon
} from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Legend } from "recharts";

const API_BASE = "http://127.0.0.1:8000";

const AdminDashboard = () => {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("authUser"));
  
  // Tab Management
  const [activeTab, setActiveTab] = useState("overview");

  // Data States
  const [inventory, setInventory] = useState([]);
  const [analytics, setAnalytics] = useState({ daily_trends: [], best_sellers: [] });
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  
  // --- INLINE EDITING STATES ---
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ stock: 0, price: 0, prescription_required: false });

  useEffect(() => {
    fetchInventory();
    fetchAnalytics();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("authUser");
    navigate("/");
  };

  const fetchInventory = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/admin/inventory`);
      setInventory(res.data);
    } catch (err) {
      console.error("Failed to fetch inventory", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await axios.get(`${API_BASE}/admin/analytics/sales-report`);
      setAnalytics(res.data);
    } catch (err) {
      console.error("Failed to fetch analytics", err);
    }
  };

  const handleBulkUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    setLoading(true);
    setUploadStatus({ type: "loading", msg: "⚙️ Synchronizing Data..." });
    try {
      const res = await axios.post(`${API_BASE}/admin/upload-inventory`, formData);
      setUploadStatus({ 
        type: "success", 
        msg: `✅ Sync Complete! Added: ${res.data.added}, Updated: ${res.data.updated}, Skipped Blank: ${res.data.skipped_blank}` 
      });
      await fetchInventory();
      await fetchAnalytics();
    } catch (err) {
      setUploadStatus({ type: "error", msg: "❌ Sync Failed." });
    } finally {
      setLoading(false);
      e.target.value = null;
    }
  };

  // --- SAVE MODIFIED DATA ---
  const handleSaveRow = async (productId) => {
    try {
      await axios.put(`${API_BASE}/admin/inventory/${productId}`, editForm);
      setEditingId(null); // Exit edit mode
      
      // Refresh to sync data
      await fetchInventory(); 
      setUploadStatus({ type: "success", msg: "✅ Product updated and synced with AI Agent." });
    } catch (err) {
      alert("Error saving changes. Check backend connection.");
    }
  };

  return (
    <div className="h-screen w-screen bg-[#F8FAFC] flex flex-col font-sans overflow-hidden">
      {/* HEADER */}
      <header className="bg-white border-b border-gray-200 px-10 py-5 flex justify-between items-center shadow-sm z-50">
        <div className="flex items-center gap-4">
          <div className="bg-indigo-600 p-2.5 rounded-2xl shadow-lg shadow-indigo-100">
            <ShieldCheck className="text-white" size={28} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-gray-800 tracking-tight leading-none mb-1">Admin Portal</h1>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Live Sync Active</span>
            </div>
          </div>
        </div>

        <nav className="flex bg-gray-100 p-1.5 rounded-2xl gap-2 border border-gray-200">
          {["overview", "inventory", "analytics"].map((t) => (
            <button key={t} onClick={() => setActiveTab(t)}
              className={`px-8 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${
                activeTab === t ? "bg-white text-indigo-600 shadow-md scale-105" : "text-gray-400 hover:text-gray-700"
              }`}>
              {t}
            </button>
          ))}
        </nav>

        <button onClick={handleLogout} className="flex items-center gap-2 px-6 py-3 bg-red-50 text-red-600 rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-red-100 transition-all border border-red-100 shadow-sm">
          <LogOut size={18} /> Logout
        </button>
      </header>

      {/* MAIN CONTENT */}
      <main className="flex-1 overflow-y-auto p-10">
        {uploadStatus && (
          <div className={`mb-8 p-5 rounded-3xl flex items-center justify-between shadow-sm border animate-in zoom-in duration-300 ${
            uploadStatus.type === "success" ? "bg-green-50 text-green-700 border-green-200" : 
            uploadStatus.type === "error" ? "bg-red-50 text-red-700 border-red-200" : "bg-indigo-50 text-indigo-700 border-indigo-200"
          }`}>
            <span className="font-bold flex items-center gap-2">
              {uploadStatus.type === "success" ? <CheckCircle size={18}/> : <AlertCircle size={18}/>}
              {uploadStatus.msg}
            </span>
            <button onClick={() => setUploadStatus(null)}><X size={20}/></button>
          </div>
        )}

        {activeTab === "overview" && (
          <div className="space-y-10">
            <div className="bg-indigo-600 rounded-[3rem] p-16 text-white shadow-2xl shadow-indigo-100 relative overflow-hidden group">
               <div className="relative z-10">
                 <h2 className="text-6xl font-black mb-4 tracking-tighter">System Health.</h2>
                 <p className="text-indigo-100 text-xl font-medium max-w-2xl opacity-90">
                   Hello {user?.name}. Your dashboard is fully integrated. All inventory modifications are synced to AI agents in real-time.
                 </p>
               </div>
               <ShieldCheck size={300} className="absolute -right-20 -bottom-20 text-white/10 rotate-12" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <StatCard icon={<Package/>} label="Active Inventory" value={inventory.length} color="blue" />
              <StatCard icon={<TrendingUp/>} label="7d Revenue" value={`$${analytics.daily_trends.reduce((a, b) => a + b.revenue, 0).toFixed(2)}`} color="green" />
              <StatCard icon={<AlertCircle/>} label="Low Stock Warnings" value={inventory.filter(i => i.stock < 10).length} color="orange" />
            </div>
          </div>
        )}

        {activeTab === "inventory" && (
          <div className="bg-white rounded-[3rem] border border-gray-200 shadow-2xl overflow-hidden min-h-[600px] animate-in slide-in-from-bottom-5">
            <div className="p-10 border-b border-gray-100 flex justify-between items-center bg-gray-50/30">
              <h3 className="text-3xl font-black text-gray-800 tracking-tighter">Inventory Console</h3>
              <label className="cursor-pointer flex items-center gap-3 px-10 py-4 bg-indigo-600 text-white rounded-[1.5rem] font-black hover:bg-indigo-700 transition-all shadow-xl shadow-indigo-100 active:scale-95 text-sm uppercase tracking-widest">
                <Upload size={20} /> Bulk Sync Excel
                <input type="file" className="hidden" accept=".xlsx" onChange={handleBulkUpload} />
              </label>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead className="bg-gray-50 text-gray-400 text-[10px] uppercase font-black tracking-[0.2em] border-b border-gray-100">
                  <tr>
                    <th className="px-10 py-6">Product ID</th>
                    <th className="px-10 py-6">Medicine Name</th>
                    <th className="px-10 py-6">Stock Level</th>
                    <th className="px-10 py-6">Price ($)</th>
                    <th className="px-10 py-6">Rx Status</th>
                    <th className="px-10 py-6 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {inventory.map((item) => (
                    <tr key={item.product_id} className="hover:bg-gray-50/50 transition-all group">
                      <td className="px-10 py-8 font-mono text-xs text-gray-400">{item.product_id}</td>
                      <td className="px-10 py-8 font-black text-gray-800 text-lg">{item.name}</td>
                      
                      {/* --- CONDITIONAL RENDERING FOR EDIT MODE --- */}
                      {editingId === item.product_id ? (
                        <>
                          <td className="px-10 py-8">
                            <input 
                              type="number" 
                              className="w-32 border-2 border-indigo-200 rounded-xl p-3 outline-none focus:border-indigo-600 font-black text-indigo-600 bg-white shadow-inner" 
                              value={editForm.stock} 
                              onChange={e => setEditForm({...editForm, stock: e.target.value})}
                            />
                          </td>
                          <td className="px-10 py-8">
                            <input 
                              type="number" 
                              className="w-32 border-2 border-indigo-200 rounded-xl p-3 outline-none focus:border-indigo-600 font-black text-indigo-600 bg-white shadow-inner" 
                              value={editForm.price} 
                              onChange={e => setEditForm({...editForm, price: e.target.value})}
                            />
                          </td>
                          <td className="px-10 py-8">
                            <select 
                              className="border-2 border-indigo-200 rounded-xl p-3 outline-none focus:border-indigo-600 font-black text-indigo-600 bg-white shadow-inner"
                              value={editForm.prescription_required} 
                              onChange={e => setEditForm({...editForm, prescription_required: e.target.value === 'true'})}
                            >
                              <option value="true">Required</option>
                              <option value="false">OTC</option>
                            </select>
                          </td>
                          <td className="px-10 py-8 text-right">
                             <div className="flex justify-end gap-3">
                                <button onClick={() => handleSaveRow(item.product_id)} className="bg-green-500 text-white p-4 rounded-2xl hover:bg-green-600 shadow-lg shadow-green-100 transition-all active:scale-90">
                                  <Save size={20}/>
                                </button>
                                <button onClick={() => setEditingId(null)} className="bg-gray-200 text-gray-500 p-4 rounded-2xl hover:bg-gray-300 transition-all">
                                  <X size={20}/>
                                </button>
                             </div>
                          </td>
                        </>
                      ) : (
                        <>
                          <td className="px-10 py-8">
                            <span className={`px-6 py-2 rounded-full text-[10px] font-black uppercase tracking-widest border ${item.stock < 10 ? 'bg-red-50 text-red-600 border-red-100' : 'bg-green-50 text-green-600 border-green-100'}`}>
                              {item.stock} Units
                            </span>
                          </td>
                          <td className="px-10 py-8 font-black text-indigo-600 text-2xl">${item.price.toFixed(2)}</td>
                          <td className="px-10 py-8 uppercase text-[10px] font-black tracking-widest text-gray-400">
                            {item.prescription_required ? "Rx Required" : "OTC"}
                          </td>
                          <td className="px-10 py-8 text-right opacity-0 group-hover:opacity-100 transition-all">
                            <button 
                              onClick={() => { setEditingId(item.product_id); setEditForm(item); }} 
                              className="p-4 bg-indigo-50 text-indigo-600 rounded-2xl hover:bg-indigo-600 hover:text-white transition-all shadow-sm hover:shadow-indigo-200"
                            >
                              <Edit2 size={22}/>
                            </button>
                          </td>
                        </>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
              {inventory.length === 0 && !loading && (
                <div className="p-32 text-center text-gray-300 font-black text-2xl">No inventory records found. Sync with Excel to start.</div>
              )}
            </div>
          </div>
        )}

        {activeTab === "analytics" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 h-[600px] animate-in zoom-in duration-500">
            <div className="bg-white p-12 rounded-[3.5rem] border border-gray-200 shadow-2xl flex flex-col">
              <h3 className="text-3xl font-black text-gray-800 mb-10 tracking-tighter flex items-center gap-4"><LineChartIcon className="text-indigo-600"/> Revenue Trend</h3>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={analytics.daily_trends}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                  <XAxis dataKey="date" hide />
                  <YAxis axisLine={false} tickLine={false} tick={{fill: '#94A3B8', fontSize: 14, fontWeight: 700}} />
                  <Tooltip contentStyle={{borderRadius: '24px', border: 'none', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)'}} />
                  <Line type="monotone" dataKey="revenue" stroke="#4F46E5" strokeWidth={8} dot={{r: 8, fill: '#4F46E5', strokeWidth: 4, stroke: '#fff'}} activeDot={{r: 12}} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="bg-white p-12 rounded-[3.5rem] border border-gray-200 shadow-2xl flex flex-col">
              <h3 className="text-3xl font-black text-gray-800 mb-10 tracking-tighter flex items-center gap-4"><BarChart3 className="text-orange-500"/> Best Sellers</h3>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={analytics.best_sellers} layout="vertical">
                  <XAxis type="number" hide />
                  <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{fill: '#475569', fontSize: 14, fontWeight: 800}} width={140} />
                  <Bar dataKey="quantity" fill="#F97316" radius={[0, 20, 20, 0]} barSize={50} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

const StatCard = ({ icon, label, value, color }) => {
  const themes = {
    blue: "bg-blue-50 text-blue-600",
    green: "bg-green-50 text-green-600",
    orange: "bg-orange-50 text-orange-600"
  };
  return (
    <div className="bg-white p-10 rounded-[3rem] border border-gray-100 shadow-xl flex items-center gap-8 group hover:scale-105 transition-transform duration-300">
      <div className={`${themes[color]} p-8 rounded-[2rem] shadow-lg transition-transform group-hover:rotate-12`}>{icon}</div>
      <div>
        <p className="text-gray-400 text-sm font-black uppercase tracking-[0.2em] mb-1">{label}</p>
        <p className="text-5xl font-black text-gray-800 tracking-tighter">{value}</p>
      </div>
    </div>
  );
};

export default AdminDashboard;