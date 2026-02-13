import { Activity, Wifi, WifiOff, RotateCcw, Play, Pause } from 'lucide-react'

const INTENT_LABELS = { 
  balanced: 'Balanced', 
  low_latency: 'Low Latency', 
  low_power: 'Low Power', 
  high_priority: 'High Priority' 
}
const INTENT_COLORS = { 
  balanced: 'bg-blue-500', 
  low_latency: 'bg-green-500', 
  low_power: 'bg-yellow-500', 
  high_priority: 'bg-red-500' 
}

export default function Header({ connected, currentIntent, onResetSimulation, autoPackets, onToggleAutoPackets }) {
  return (
    <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
      <div className="container mx-auto flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <Activity className="w-8 h-8 text-blue-400" />
          <div>
            <h1 className="text-xl font-bold text-white">SADRN Dashboard</h1>
            <p className="text-xs text-slate-400">Software-Defined Adaptive Disaster Response Network</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4 flex-wrap">
          {/* Routing Intent */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-400">Intent:</span>
            <span className={`px-3 py-1 rounded-full text-xs font-medium text-white ${INTENT_COLORS[currentIntent]}`}>
              {INTENT_LABELS[currentIntent]}
            </span>
          </div>
          
          {/* Auto Packets Toggle */}
          <button 
            onClick={onToggleAutoPackets}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
              autoPackets 
                ? 'bg-green-600 hover:bg-green-500 text-white' 
                : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
            }`}
            title={autoPackets ? 'Pause auto packets' : 'Resume auto packets'}
          >
            {autoPackets ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            <span className="text-sm">{autoPackets ? 'Auto ON' : 'Auto OFF'}</span>
          </button>
          
          {/* Connection Status */}
          <div className="flex items-center gap-2">
            {connected ? (
              <Wifi className="w-5 h-5 text-green-400" />
            ) : (
              <WifiOff className="w-5 h-5 text-red-400 animate-pulse" />
            )}
            <span className={`text-sm ${connected ? 'text-green-400' : 'text-red-400'}`}>
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          
          {/* Reset Button */}
          <button 
            onClick={onResetSimulation}
            className="flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
            title="Reset Simulation"
          >
            <RotateCcw className="w-4 h-4" />
            <span className="text-sm">Reset</span>
          </button>
        </div>
      </div>
    </header>
  )
}
