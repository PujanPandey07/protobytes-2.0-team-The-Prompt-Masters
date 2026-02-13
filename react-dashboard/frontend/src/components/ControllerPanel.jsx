import { Zap, Battery, Router , ToggleLeft, ToggleRight } from 'lucide-react'

export default function ControllerPanel({ 
  currentIntent = 'balanced',
  autoIntent = true,
  onSetIntent,
  routes = {}, 
  gateways = {},
  packetStats = { forwarded: 0, dropped: 0, total: 0 }
}) {
  const intentInfo = {
    'high_priority': {
      label: 'EMERGENCY',
      description: 'Minimizing latency for critical data',
      color: 'bg-red-500',
      textColor: 'text-red-400',
      borderColor: 'border-red-500',
      weights: { latency: 0.9, battery: 0.1 }
    },
    'low_latency': {
      label: 'ALERT',
      description: 'Balanced routing with priority',
      color: 'bg-yellow-500',
      textColor: 'text-yellow-400',
      borderColor: 'border-yellow-500',
      weights: { latency: 0.6, battery: 0.4 }
    },
    'balanced': {
      label: 'NORMAL',
      description: 'Battery-optimized routing',
      color: 'bg-green-500',
      textColor: 'text-green-400',
      borderColor: 'border-green-500',
      weights: { latency: 0.4, battery: 0.6 }
    }
  }

  const info = intentInfo[currentIntent] || intentInfo.balanced

  const handleIntentClick = (intent) => {
    if (onSetIntent) {
      onSetIntent(intent, false)  // Set manual mode
    }
  }

  const toggleAutoIntent = () => {
    if (onSetIntent) {
      onSetIntent(currentIntent, !autoIntent)
    }
  }

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
      <h3 className="text-white font-bold text-sm mb-3 flex items-center gap-2">
        <Router className="w-4 h-4 text-cyan-400"/>
        SDN Controller
      </h3>
      
      {/* Intent Mode Selector */}
      <div className="mb-4 p-3 bg-slate-700/50 rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <span className="text-slate-400 text-xs font-medium">Intent Mode</span>
          <button 
            onClick={toggleAutoIntent}
            className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs transition-colors ${
              autoIntent 
                ? 'bg-cyan-600 text-white' 
                : 'bg-slate-600 text-slate-300 hover:bg-slate-500'
            }`}
          >
            {autoIntent ? <ToggleRight className="w-3 h-3"/> : <ToggleLeft className="w-3 h-3"/>}
            {autoIntent ? 'AUTO' : 'MANUAL'}
          </button>
        </div>
        
        {/* Intent Buttons */}
        <div className="grid grid-cols-3 gap-1.5 mb-3">
          {Object.entries(intentInfo).map(([key, {label, color, borderColor}]) => (
            <button
              key={key}
              onClick={() => handleIntentClick(key)}
              disabled={autoIntent}
              className={`px-2 py-1.5 rounded text-[10px] font-bold transition-all ${
                currentIntent === key 
                  ? `${color} text-white shadow-lg scale-105` 
                  : autoIntent 
                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                    : `bg-slate-700 text-slate-300 hover:bg-slate-600 border ${borderColor} border-opacity-50`
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        
        {/* Current Intent Display */}
        <div className={`p-2 rounded border-l-2 ${info.borderColor} bg-slate-800/50`}>
          <div className="flex items-center justify-between mb-1">
            <span className={`${info.textColor} text-xs font-bold`}>{info.label}</span>
            <span className="text-slate-500 text-[9px]">{autoIntent ? 'Auto-detected' : 'Manual'}</span>
          </div>
          <p className="text-slate-400 text-[10px]">{info.description}</p>
          
          {/* Weight Display */}
          <div className="flex gap-3 mt-2 text-[9px]">
            <span className="flex items-center gap-1">
              <Zap className="w-3 h-3 text-cyan-400"/>
              <span className="text-cyan-400">Latency: {info.weights.latency}</span>
            </span>
            <span className="flex items-center gap-1">
              <Battery className="w-3 h-3 text-amber-400"/>
              <span className="text-amber-400">Battery: {info.weights.battery}</span>
            </span>
          </div>
        </div>
      </div>

      {/* Packet Statistics */}
      <div className="mb-4 p-3 bg-slate-700/50 rounded-lg">
        <div className="text-slate-400 text-xs mb-2">Packet Statistics</div>
        <div className="grid grid-cols-3 gap-2">
          <div className="text-center">
            <div className="text-green-400 font-bold text-lg">{packetStats.forwarded}</div>
            <div className="text-slate-500 text-[10px]">Forwarded</div>
          </div>
          <div className="text-center">
            <div className="text-red-400 font-bold text-lg">{packetStats.dropped}</div>
            <div className="text-slate-500 text-[10px]">Dropped</div>
          </div>
          <div className="text-center">
            <div className="text-cyan-400 font-bold text-lg">
              {packetStats.total > 0 
                ? Math.round((packetStats.forwarded / packetStats.total) * 100) 
                : 100}%
            </div>
            <div className="text-slate-500 text-[10px]">Success</div>
          </div>
        </div>
      </div>

      {/* Active Routes */}
      <div>
        <h4 className="text-slate-400 text-xs mb-2">Active Routes</h4>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {Object.entries(routes).length === 0 ? (
            <div className="text-slate-500 text-xs italic">No active routes</div>
          ) : (
            Object.entries(routes).map(([gwId, route]) => {
              if (!route) return null
              const gw = gateways[gwId]
              
              const priorityColors = {
                'EMERGENCY': 'border-red-500 bg-red-900/20',
                'WARNING': 'border-yellow-500 bg-yellow-900/20',
                'NORMAL': 'border-green-500 bg-green-900/20'
              }
              
              return (
                <div 
                  key={gwId} 
                  className={`p-2 rounded border-l-2 ${priorityColors[route.priority] || priorityColors.NORMAL}`}
                >
                  <div className="flex justify-between items-center">
                    <span className="text-white text-xs font-semibold">
                      {gw?.name || gwId}
                    </span>
                    <span className={`text-[10px] px-1 rounded ${
                      route.priority === 'EMERGENCY' ? 'bg-red-600' :
                      route.priority === 'WARNING' ? 'bg-yellow-600' : 'bg-green-600'
                    } text-white`}>
                      {route.priority}
                    </span>
                  </div>
                  <div className="text-cyan-400 text-[10px] mt-1 font-mono">
                    {route.path?.join(' → ')}
                  </div>
                  <div className="flex gap-3 mt-1 text-[9px] text-slate-400">
                    <span>Cost: {route.cost}</span>
                    <span>Intent: {route.intent}</span>
                  </div>
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}
