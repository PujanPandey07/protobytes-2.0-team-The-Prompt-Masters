export default function ControllerPanel({ 
  currentIntent = 'balanced', 
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
      weights: { latency: 0.2, battery: 0.1, hop: 0.1 }
    },
    'low_latency': {
      label: 'ALERT',
      description: 'Balanced routing with priority',
      color: 'bg-yellow-500',
      textColor: 'text-yellow-400',
      weights: { latency: 0.5, battery: 0.3, hop: 0.2 }
    },
    'balanced': {
      label: 'NORMAL',
      description: 'Battery-optimized routing',
      color: 'bg-green-500',
      textColor: 'text-green-400',
      weights: { latency: 0.3, battery: 0.5, hop: 0.2 }
    }
  }

  const info = intentInfo[currentIntent] || intentInfo.balanced

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
      <h3 className="text-white font-bold text-sm mb-3">SDN Controller</h3>
      
      {/* Auto Intent Display */}
      <div className="mb-4 p-3 bg-slate-700/50 rounded-lg">
        <div className="flex items-center justify-between mb-2">
          <span className="text-slate-400 text-xs">Auto-Detected Intent</span>
          <span className={`px-2 py-0.5 rounded text-xs font-bold text-white ${info.color}`}>
            {info.label}
          </span>
        </div>
        <p className="text-slate-300 text-xs">{info.description}</p>
        
        {/* Weight Display */}
        <div className="mt-2 pt-2 border-t border-slate-600">
          <div className="text-slate-500 text-[10px] mb-1">COST WEIGHTS:</div>
          <div className="flex gap-2 text-[10px]">
            <span className="text-cyan-400">Latency: {info.weights.latency}</span>
            <span className="text-amber-400">Battery: {info.weights.battery}</span>
            <span className="text-purple-400">Hop: {info.weights.hop}</span>
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
                    <span>Latency: {route.latency}ms</span>
                    <span>Hops: {route.hops}</span>
                    <span>Cost: {route.cost}</span>
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
