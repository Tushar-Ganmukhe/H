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
  
  // Inline Editing States
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ stock: 0, price: 0, prescription_required: false });

  // Initial Data Load
  useEffect(() => {
    fetchInventory();
    fetchAnalytics();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("authUser");
    navigate("/");
  };

  // --- CORE SYNC FUNCTIONS ---

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
    setUploadStatus({ type: "loading", msg: "⚙️ Processing Excel & Syncing Agents..." });

    try {
      const res = await axios.post(`${API_BASE}/admin/upload-inventory`, formData);
      
      // Update UI with Server Summary
      setUploadStatus({ 
        type: "success", 
        msg: `✅ Sync Complete! Added: ${res.data.added}, Updated: ${res.data.updated}, Skipped Blank: ${res.data.skipped_blank}` 
      });

      // CRITICAL: Refresh both inventory and analytics immediately
      await fetchInventory();
      await fetchAnalytics();

    } catch (err) {
      setUploadStatus({ type: "error", msg: "❌ Sync Failed. Please check Excel headers and try again." });
    } finally {
      setLoading(false);
      e.target.value = null; // Clear input
    }
  };

  const handleSaveRow = async (productId) => {
    try {
      await axios.put(`${API_BASE}/admin/inventory/${productId}`, editForm);
      setEditingId(null);
      
      // Sync UI and show success
      await fetchInventory(); 
      setUploadStatus({ type: "success", msg: "✅ Product updated and synced with AI Agent." });
    } catch (err) {
      alert("Error saving changes.");
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col font-sans">
      {/* --- HEADER --- */}
      <header className="bg-white border-b border-gray-200 px-8 py-4 flex justify-between items-center shadow-sm sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="bg-indigo-600 p-2.5 rounded-2xl shadow-lg shadow-indigo-100">
            <ShieldCheck className="text-white" size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-800 tracking-tight">Admin Portal</h1>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest text-nowrap">Live Data Synchronized</span>
            </div>
          </div>
        </div>

        <nav className="hidden md:flex bg-gray-100 p-1.5 rounded-2xl gap-1 border border-gray-200">
          {["overview", "inventory", "analytics"].map((t) => (
            <button
              key={t}
              onClick={() => setActiveTab(t)}
              className={`px-6 py-2 rounded-xl text-sm font-bold capitalize transition-all ${
                activeTab === t ? "bg-white text-indigo-600 shadow-md" : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {t}
            </button>
          ))}
        </nav>

        <button onClick={handleLogout} className="flex items-center gap-2 px-5 py-2.5 bg-red-50 text-red-600 rounded-2xl font-bold hover:bg-red-100 transition-all border border-red-100 shadow-sm">
          <LogOut size={18} /> Logout
        </button>
      </header>

      {/* --- MAIN CONTENT AREA --- */}
      <main className="flex-1 p-8 max-w-7xl mx-auto w-full space-y-8">
        
        {/* Status Notification Banner */}
        {uploadStatus && (
          <div className={`p-4 rounded-2xl flex items-center justify-between animate-in fade-in zoom-in duration-300 shadow-sm border ${
            uploadStatus.type === "success" ? "bg-green-50 text-green-700 border-green-200" : 
            uploadStatus.type === "error" ? "bg-red-50 text-red-700 border-red-200" : "bg-indigo-50 text-indigo-700 border-indigo-200"
          }`}>
            <div className="flex items-center gap-3">
              {uploadStatus.type === "success" ? <CheckCircle size={20}/> : <AlertCircle size={20}/>}
              <span className="font-bold text-sm">{uploadStatus.msg}</span>
            </div>
            <button onClick={() => setUploadStatus(null)} className="hover:bg-white/50 p-1 rounded-lg transition-colors"><X size={18}/></button>
          </div>
        )}

        {/* --- TAB CONTENT: OVERVIEW --- */}
        {activeTab === "overview" && (
          <div className="space-y-8">
            <div className="bg-indigo-600 rounded-[2.5rem] p-10 text-white shadow-2xl shadow-indigo-200 relative overflow-hidden group">
               <div className="relative z-10">
                 <h2 className="text-4xl font-black mb-3">System Hub</h2>
                 <p className="text-indigo-100 text-lg opacity-90 max-w-lg">
                   Welcome, {user?.name}. Your database is currently managing <b>{inventory.length}</b> products. All manual and bulk updates are instantly visible to the AI Agents.
                 </p>
               </div>
               <ShieldCheck size={200} className="absolute -right-10 -bottom-10 text-white/10 rotate-12 group-hover:rotate-0 transition-transform duration-700" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <StatCard icon={<Package/>} label="Active Inventory" value={inventory.length} color="blue" />
              <StatCard icon={<TrendingUp/>} label="Revenue (7 Days)" value={`$${analytics.daily_trends.reduce((a, b) => a + b.revenue, 0).toFixed(2)}`} color="green" />
              <StatCard icon={<AlertCircle/>} label="Low Stock Warnings" value={inventory.filter(i => i.stock < 10).length} color="orange" />
            </div>
          </div>
        )}

        {/* --- TAB CONTENT: INVENTORY MANAGEMENT --- */}
        {activeTab === "inventory" && (
          <div className="bg-white rounded-[2rem] border border-gray-200 shadow-xl overflow-hidden animate-in fade-in slide-in-from-bottom-4">
            <div className="p-8 border-b border-gray-100 flex flex-col md:flex-row justify-between items-center gap-6 bg-gray-50/30">
              <div>
                <h3 className="text-2xl font-black text-gray-800 tracking-tight">Inventory & Pricing</h3>
                <p className="text-gray-500 text-sm font-medium italic">Updates sync with Chatbot memory automatically</p>
              </div>
              
              <div className="flex gap-4">
                <label className="cursor-pointer flex items-center gap-3 px-8 py-3.5 bg-indigo-600 text-white rounded-2xl font-black hover:bg-indigo-700 transition-all shadow-xl shadow-indigo-200 active:scale-95">
                  <Upload size={20} /> Bulk Sync (Excel)
                  <input type="file" className="hidden" accept=".xlsx" onChange={handleBulkUpload} />
                </label>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-gray-50/50 text-gray-400 text-[11px] uppercase font-black tracking-widest border-b border-gray-100">
                  <tr>
                    <th className="px-8 py-5">Product ID</th>
                    <th className="px-8 py-5">Medicine Name</th>
                    <th className="px-8 py-5">Stock Level</th>
                    <th className="px-8 py-5">Price (Rec)</th>
                    <th className="px-8 py-5">Rx Status</th>
                    <th className="px-8 py-5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {inventory.map((item) => (
                    <tr key={item.product_id} className="hover:bg-gray-50/40 transition-colors group">
                      <td className="px-8 py-6 font-mono text-xs text-gray-400">{item.product_id}</td>
                      <td className="px-8 py-6">
                        <div className="font-bold text-gray-800">{item.name}</div>
                        <div className="text-[10px] text-gray-400 font-bold uppercase">{item.package_size || 'N/A'}</div>
                      </td>
                      
                      {editingId === item.product_id ? (
                        <>
                          <td className="px-8 py-6">
                            <input type="number" className="w-24 border-2 border-indigo-100 rounded-xl p-2 outline-none focus:border-indigo-500 font-black text-indigo-600" value={editForm.stock} onChange={e=>setEditForm({...editForm, stock: e.target.value})}/>
                          </td>
                          <td className="px-8 py-6">
                            <input type="number" className="w-24 border-2 border-indigo-100 rounded-xl p-2 outline-none focus:border-indigo-500 font-black text-indigo-600" value={editForm.price} onChange={e=>setEditForm({...editForm, price: e.target.value})}/>
                          </td>
                          <td className="px-8 py-6">
                            <select value={editForm.prescription_required} onChange={e=>setEditForm({...editForm, prescription_required: e.target.value === 'true'})} className="border-2 border-indigo-100 rounded-xl p-2 font-black outline-none bg-white text-indigo-600">
                              <option value="true">Required</option>
                              <option value="false">OTC</option>
                            </select>
                          </td>
                          <td className="px-8 py-6 text-right">
                            <div className="flex justify-end gap-2">
                                <button onClick={() => handleSaveRow(item.product_id)} className="bg-green-500 text-white p-2.5 rounded-xl hover:bg-green-600 shadow-lg shadow-green-100 active:scale-90"><Save size={18}/></button>
                                <button onClick={() => setEditingId(null)} className="bg-gray-100 text-gray-400 p-2.5 rounded-xl hover:bg-gray-200"><X size={18}/></button>
                            </div>
                          </td>
                        </>
                      ) : (
                        <>
                          <td className="px-8 py-6">
                            <span className={`px-4 py-1.5 rounded-full text-[11px] font-black uppercase tracking-wider border ${item.stock < 10 ? 'bg-red-50 text-red-600 border-red-100' : 'bg-green-50 text-green-600 border-green-100'}`}>
                              {item.stock} Units
                            </span>
                          </td>
                          <td className="px-8 py-6 font-black text-indigo-600">${item.price.toFixed(2)}</td>
                          <td className="px-8 py-6">
                            {item.prescription_required ? (
                              <span className="text-orange-500 flex items-center gap-1.5 font-black text-[10px] uppercase border border-orange-100 bg-orange-50 px-3 py-1 rounded-lg tracking-tight"><AlertCircle size={12}/> Rx Required</span>
                            ) : (
                              <span className="text-gray-400 font-black text-[10px] uppercase bg-gray-50 border border-gray-100 px-3 py-1 rounded-lg">OTC</span>
                            )}
                          </td>
                          <td className="px-8 py-6 text-right opacity-0 group-hover:opacity-100 transition-all">
                            <button onClick={() => { setEditingId(item.product_id); setEditForm(item); }} className="text-indigo-600 bg-indigo-50 p-3 rounded-xl hover:bg-indigo-600 hover:text-white transition-all transform hover:scale-110">
                              <Edit2 size={18} />
                            </button>
                          </td>
                        </>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
              {inventory.length === 0 && !loading && (
                <div className="p-24 text-center">
                   <Package size={48} className="mx-auto text-gray-200 mb-4" />
                   <div className="text-gray-300 font-black text-xl">Inventory Empty</div>
                   <p className="text-gray-400 text-sm mt-1">Upload your Excel file to sync the system.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* --- TAB CONTENT: SALES ANALYTICS --- */}
        {activeTab === "analytics" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 animate-in fade-in zoom-in duration-500">
            {/* Sales Trends Chart */}
            <div className="bg-white p-8 rounded-[2.5rem] border border-gray-200 shadow-xl space-y-8 flex flex-col">
              <div>
                <h3 className="text-2xl font-black text-gray-800 flex items-center gap-3 tracking-tight">
                  <LineChartIcon className="text-indigo-600" /> Revenue Trend
                </h3>
                <p className="text-gray-400 text-xs font-bold uppercase mt-1">Last 7 Days Selling Performance</p>
              </div>
              <div className="h-[320px] w-full mt-auto">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={analytics.daily_trends}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                    <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{fill: '#94A3B8', fontSize: 10, fontWeight: 700}} dy={15} />
                    <YAxis axisLine={false} tickLine={false} tick={{fill: '#94A3B8', fontSize: 10, fontWeight: 700}} />
                    <Tooltip contentStyle={{borderRadius: '20px', border: 'none', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)', padding: '15px'}} />
                    <Line type="monotone" dataKey="revenue" stroke="#4F46E5" strokeWidth={5} dot={{r: 6, fill: '#4F46E5', strokeWidth: 3, stroke: '#fff'}} activeDot={{r: 10}} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Top Products Chart */}
            <div className="bg-white p-8 rounded-[2.5rem] border border-gray-200 shadow-xl space-y-8 flex flex-col">
              <div>
                <h3 className="text-2xl font-black text-gray-800 flex items-center gap-3 tracking-tight">
                  <BarChart3 className="text-orange-500" /> Best Sellers
                </h3>
                <p className="text-gray-400 text-xs font-bold uppercase mt-1">Top 5 Products by Quantity Sold</p>
              </div>
              <div className="h-[320px] w-full mt-auto">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.best_sellers} layout="vertical" margin={{ left: 30 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#F1F5F9" />
                    <XAxis type="number" hide />
                    <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{fill: '#475569', fontSize: 10, fontWeight: 800}} width={120} />
                    <Tooltip cursor={{fill: '#F8FAFC'}} contentStyle={{borderRadius: '20px', border: 'none', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)'}} />
                    <Bar dataKey="quantity" fill="#F97316" radius={[0, 10, 10, 0]} barSize={28} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

// Sub-Component: Stats Widget
const StatCard = ({ icon, label, value, color }) => {
  const themes = {
    blue: "bg-blue-50 text-blue-600 shadow-blue-50/50 border-blue-100",
    green: "bg-green-50 text-green-600 shadow-green-50/50 border-green-100",
    orange: "bg-orange-50 text-orange-600 shadow-orange-50/50 border-orange-100"
  };
  return (
    <div className="bg-white p-8 rounded-[2rem] border border-gray-100 shadow-xl flex items-center gap-6 group hover:translate-y-[-5px] transition-all duration-300">
      <div className={`${themes[color]} p-5 rounded-2xl shadow-xl transition-all border group-hover:scale-110`}>
        {icon}
      </div>
      <div>
        <p className="text-gray-400 text-[10px] font-black uppercase tracking-[0.2em] mb-1">{label}</p>
        <p className="text-3xl font-black text-gray-800 tracking-tighter">{value}</p>
      </div>
    </div>
  );
};

export default AdminDashboard;