import { Router, ArrowUpCircle, ArrowDownCircle, Wifi } from 'lucide-react'

const PRIORITY_STYLES = { 
  NORMAL: 'bg-green-500/20 text-green-400 border-green-500/50', 
  WARNING: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50 animate-pulse', 
  EMERGENCY: 'bg-red-500/20 text-red-400 border-red-500/50 animate-pulse' 
}

export default function GatewayPanel({ gateways, sensors }) {
  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <Router className="w-5 h-5 text-purple-400"/>Gateways
      </h2>
      <div className="space-y-3">
        {Object.entries(gateways || {}).map(([id, gw]) => {
          const gwSensors = (gw.sensors || []).map(sid => sensors?.[sid]).filter(Boolean)
          const activeCount = gwSensors.filter(s => s.status !== 'NORMAL').length
          
          return (
            <div key={id} className={`bg-slate-700/50 rounded-lg p-3 border-l-2 ${
              gw.priority === 'EMERGENCY' ? 'border-red-500' :
              gw.priority === 'WARNING' ? 'border-yellow-500' : 'border-green-500'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span className="font-medium text-white">{gw.name}</span>
                  <span className="text-xs text-slate-500 ml-2">({gw.ip})</span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded border ${PRIORITY_STYLES[gw.priority]}`}>
                  {gw.priority}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-2 text-xs mb-2">
                <div className="flex items-center gap-1 text-slate-400">
                  <ArrowUpCircle className={`w-3.5 h-3.5 ${gw.active_uplink === gw.primary_switch ? 'text-green-400' : 'text-slate-500'}`}/>
                  <span>Primary: <strong className="text-slate-300">{gw.primary_switch?.toUpperCase()}</strong></span>
                </div>
                <div className="flex items-center gap-1 text-slate-400">
                  <ArrowDownCircle className={`w-3.5 h-3.5 ${gw.active_uplink === gw.backup_switch ? 'text-blue-400' : 'text-slate-500'}`}/>
                  <span>Backup: <strong className="text-slate-300">{gw.backup_switch?.toUpperCase()}</strong></span>
                </div>
              </div>
              
              <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-600">
                <div className="flex items-center gap-1 text-slate-400">
                  <Wifi className="w-3.5 h-3.5"/>
                  Active: <strong className="text-green-400">{gw.active_uplink?.toUpperCase()}</strong>
                </div>
                <div className="text-slate-500">
                  Sensors: {gwSensors.length} {activeCount > 0 && <span className="text-yellow-400">({activeCount} alert)</span>}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
