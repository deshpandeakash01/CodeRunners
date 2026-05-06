import React, { useState, useEffect, useRef } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line
} from 'recharts';
import { 
  Truck, Package, Clock, ShieldAlert, CheckCircle, Play, Pause, FastForward, RotateCcw,
  Map as MapIcon, BarChart3, Activity
} from 'lucide-react';

const API_URL = 'http://localhost:5000/api/simulation';

const App = () => {
  const [data, setData] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [loading, setLoading] = useState(true);
  const timerRef = useRef(null);

  useEffect(() => {
    fetch(API_URL)
      .then(res => res.json())
      .then(json => {
        setData(json);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch simulation data", err);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (isPlaying && data) {
      timerRef.current = setInterval(() => {
        setCurrentIndex(prev => {
          if (prev < data.history.length - 1) return prev + 1;
          setIsPlaying(false);
          return prev;
        });
      }, 1000 / playbackSpeed);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [isPlaying, data, playbackSpeed]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-white font-sans">
        <div className="flex flex-col items-center gap-4">
          <Activity className="w-12 h-12 text-indigo-500 animate-pulse" />
          <h1 className="text-2xl font-bold tracking-tight">Initializing Simulation...</h1>
          <p className="text-slate-400">Loading map data and precomputing paths</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-white">
        <div className="bg-red-500/10 border border-red-500/50 p-6 rounded-xl max-w-md text-center">
          <ShieldAlert className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h1 className="text-xl font-bold mb-2">Connection Error</h1>
          <p className="text-slate-400">Could not connect to the Python backend at {API_URL}. Please ensure src/server.py is running.</p>
        </div>
      </div>
    );
  }

  const currentSnapshot = data.history[currentIndex];
  const metrics = currentSnapshot.metrics;
  
  // Transform data for charts
  const workloadData = currentSnapshot.agents.map(a => ({
    name: a.id,
    assignments: a.assignments
  }));

  const slaData = [
    { name: 'High', compliance: metrics.sla_metrics.high?.compliance_rate || 0 },
    { name: 'Normal', compliance: metrics.sla_metrics.normal?.compliance_rate || 0 },
    { name: 'Low', compliance: metrics.sla_metrics.low?.compliance_rate || 0 },
  ];

  const scale = 50; // Scale for SVG map
  const offset = 20;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans p-6">
      {/* Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-8">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Truck className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
              Smart Delivery Dispatch
            </h1>
          </div>
          <p className="text-slate-400 font-medium">Real-time simulation dashboard</p>
        </div>

        <div className="flex items-center gap-4 bg-slate-900/50 p-2 rounded-2xl border border-slate-800">
          <button 
            onClick={() => { setCurrentIndex(0); setIsPlaying(false); }}
            className="p-2 hover:bg-slate-800 rounded-xl transition-colors"
            aria-label="Restart Simulation"
          >
            <RotateCcw className="w-5 h-5" />
          </button>
          <button 
            onClick={() => setIsPlaying(!isPlaying)}
            className="w-12 h-12 bg-indigo-600 hover:bg-indigo-500 rounded-xl flex items-center justify-center transition-all active:scale-95 shadow-lg shadow-indigo-500/20"
            aria-label={isPlaying ? "Pause Simulation" : "Play Simulation"}
          >
            {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6 fill-white" />}
          </button>
          <div className="flex flex-col px-2">
            <span className="text-[10px] uppercase font-bold text-slate-500 mb-1">Speed</span>
            <div className="flex gap-2">
              {[1, 2, 4, 8].map(s => (
                <button 
                  key={s}
                  onClick={() => setPlaybackSpeed(s)}
                  className={`text-xs px-2 py-1 rounded-md transition-colors ${playbackSpeed === s ? 'bg-indigo-600 text-white' : 'hover:bg-slate-800 text-slate-400'}`}
                >
                  {s}x
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-slate-900/50 px-6 py-3 rounded-2xl border border-slate-800 flex flex-col items-end">
          <span className="text-xs uppercase font-bold text-slate-500 mb-1">Current Timestamp</span>
          <span className="text-lg font-mono font-bold text-indigo-400">{currentSnapshot.timestamp}</span>
        </div>
      </header>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Metrics Summary */}
        <div className="lg:col-span-3 space-y-6">
          <MetricCard 
            icon={<Clock className="text-blue-400" />} 
            label="Avg Delivery Time" 
            value={`${metrics.delivery_metrics.overall?.average_time || 0}m`}
            subValue="Minutes across all orders"
          />
          <MetricCard 
            icon={<ShieldAlert className="text-orange-400" />} 
            label="SLA Compliance" 
            value={`${metrics.sla_metrics.overall?.compliance_rate || 0}%`}
            subValue={`${metrics.sla_metrics.overall?.violations || 0} violations recorded`}
            color={metrics.sla_metrics.overall?.compliance_rate < 50 ? 'text-red-500' : 'text-green-500'}
          />
          <MetricCard 
            icon={<Activity className="text-indigo-400" />} 
            label="Fairness Index" 
            value={metrics.fairness_metrics.std_deviation || 0}
            subValue="Std dev of assignments"
          />
          <MetricCard 
            icon={<Package className="text-emerald-400" />} 
            label="Pending Queue" 
            value={currentSnapshot.pending_count}
            subValue="Orders waiting for dispatch"
          />
        </div>

        {/* Center: Live Map */}
        <div className="lg:col-span-6 bg-slate-900 rounded-3xl border border-slate-800 overflow-hidden relative group">
          <div className="absolute top-4 left-4 z-10 flex items-center gap-2 bg-slate-950/80 backdrop-blur-md px-3 py-1.5 rounded-full border border-slate-800">
            <MapIcon className="w-4 h-4 text-indigo-400" />
            <span className="text-xs font-bold uppercase tracking-wider">Live Environment Map</span>
          </div>
          
          <div className="w-full h-[600px] flex items-center justify-center p-8">
            <svg viewBox={`0 0 ${11 * scale} ${11 * scale}`} className="w-full h-full transform transition-transform duration-500">
              {/* Grid Lines */}
              {Array.from({length: 11}).map((_, i) => (
                <React.Fragment key={i}>
                  <line x1={i * scale} y1={0} x2={i * scale} y2={10 * scale} stroke="#1e293b" strokeWidth="1" />
                  <line x1={0} y1={i * scale} x2={10 * scale} y2={i * scale} stroke="#1e293b" strokeWidth="1" />
                </React.Fragment>
              ))}

              {/* Edges */}
              {data.edges.map((edge, i) => (
                <line 
                  key={i}
                  x1={edge.from[0] * scale} 
                  y1={edge.from[1] * scale}
                  x2={edge.to[0] * scale}
                  y2={edge.to[1] * scale}
                  stroke="#334155"
                  strokeWidth="2"
                  strokeDasharray="4 4"
                />
              ))}

              {/* Nodes */}
              {data.nodes.map((node, i) => (
                <circle 
                  key={i}
                  cx={node.x * scale} 
                  cy={node.y * scale}
                  r="4"
                  fill="#475569"
                />
              ))}

              {/* Orders In Transit */}
              {currentSnapshot.in_transit.map((order, i) => (
                <g key={order.order_id} role="img" aria-label={`Order ${order.order_id} in transit`}>
                  <circle 
                    cx={order.target_x * scale} 
                    cy={order.target_y * scale}
                    r="8"
                    fill="none"
                    stroke="#fbbf24"
                    strokeWidth="2"
                    className="animate-ping"
                  />
                  <Package 
                    x={order.target_x * scale - 10} 
                    y={order.target_y * scale - 10}
                    width="20"
                    height="20"
                    className="text-amber-400 opacity-80"
                  />
                </g>
              ))}

              {/* Agents */}
              {currentSnapshot.agents.map((agent, i) => (
                <g 
                  key={agent.id} 
                  className="transition-all duration-300 ease-in-out"
                  transform={`translate(${agent.x * scale}, ${agent.y * scale})`}
                  role="img"
                  aria-label={`Agent ${agent.id}`}
                >
                  <circle r="12" fill={agent.active_orders.length > 0 ? "#4f46e5" : "#1e293b"} stroke="#818cf8" strokeWidth="2" />
                  <Truck x="-8" y="-8" width="16" height="16" className="text-white" />
                  <text y="-20" textAnchor="middle" fill="#94a3b8" fontSize="10" fontWeight="bold">
                    {agent.id}
                  </text>
                </g>
              ))}
            </svg>
          </div>

          <div className="absolute bottom-4 right-4 flex gap-4 text-[10px] font-bold uppercase tracking-widest text-slate-500">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-indigo-500"></div> Agent
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-amber-500"></div> Order
            </div>
          </div>
        </div>

        {/* Right Column: Charts */}
        <div className="lg:col-span-3 space-y-6">
          <div className="bg-slate-900 p-6 rounded-3xl border border-slate-800">
            <div className="flex items-center gap-2 mb-6">
              <BarChart3 className="w-4 h-4 text-indigo-400" />
              <h2 className="text-sm font-bold uppercase tracking-wider">Agent Workload</h2>
            </div>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={workloadData}>
                  <XAxis dataKey="name" hide />
                  <YAxis hide />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '12px' }}
                  />
                  <Bar dataKey="assignments" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-slate-900 p-6 rounded-3xl border border-slate-800">
            <div className="flex items-center gap-2 mb-6">
              <CheckCircle className="w-4 h-4 text-indigo-400" />
              <h2 className="text-sm font-bold uppercase tracking-wider">SLA Compliance</h2>
            </div>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={slaData} layout="vertical">
                  <XAxis type="number" domain={[0, 100]} hide />
                  <YAxis dataKey="name" type="category" width={60} tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '12px' }}
                  />
                  <Bar dataKey="compliance" fill="#10b981" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const MetricCard = ({ icon, label, value, subValue, color = "text-white" }) => (
  <div className="bg-slate-900 p-5 rounded-3xl border border-slate-800 group hover:border-slate-700 transition-colors">
    <div className="flex items-center gap-3 mb-3">
      <div className="p-2 bg-slate-950 rounded-xl border border-slate-800 group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <span className="text-xs font-bold uppercase tracking-widest text-slate-500">{label}</span>
    </div>
    <div className={`text-3xl font-bold mb-1 ${color}`}>{value}</div>
    <div className="text-xs text-slate-400 font-medium">{subValue}</div>
  </div>
);

export default App;
