import { AlertOctagon, CheckCircle, XCircle, Link, Server } from 'lucide-react'

export default function FailureControls({ switches, switchLinks, onToggleSwitch, onToggleLink }) {
  const coreSwitches = Object.entries(switches || {}).filter(([id, sw]) => sw.type === 'core')
  const zoneSwitches = Object.entries(switches || {}).filter(([id, sw]) => sw.type === 'zone')
  const coreLinks = (switchLinks || []).filter(l => l.type === 'core')
  const zoneLinks = (switchLinks || []).filter(l => l.type === 'zone')

  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <AlertOctagon className="w-5 h-5 text-red-400"/>Failure Simulation
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Switches */}
        <div>
          <h3 className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
            <Server className="w-4 h-4"/>Switches
          </h3>
          
          {/* Core Switches */}
          <div className="mb-3">
            <span className="text-xs text-blue-400 mb-1 block">Core (S1-S3)</span>
            <div className="space-y-1">
              {coreSwitches.map(([id, sw]) => (
                <div key={id} className="flex items-center justify-between bg-slate-700/50 rounded-lg p-2">
                  <div className="flex items-center gap-2">
                    {sw.status === 'active' ? (
                      <CheckCircle className="w-4 h-4 text-green-400"/>
                    ) : (
                      <XCircle className="w-4 h-4 text-red-400 animate-pulse"/>
                    )}
                    <span className="text-sm text-slate-300 font-medium">{id.toUpperCase()}</span>
                    <span className="text-xs text-slate-500">{sw.name}</span>
                  </div>
                  <button
                    onClick={() => onToggleSwitch(id, sw.status === 'active' ? 'fail' : 'restore')}
                    className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                      sw.status === 'active'
                        ? 'bg-red-600 hover:bg-red-500 text-white'
                        : 'bg-green-600 hover:bg-green-500 text-white'
                    }`}
                  >
                    {sw.status === 'active' ? 'Fail' : 'Restore'}
                  </button>
                </div>
              ))}
            </div>
          </div>
          
          {/* Zone Switches */}
          <div>
            <span className="text-xs text-indigo-400 mb-1 block">Zone (S4-S6)</span>
            <div className="space-y-1">
              {zoneSwitches.map(([id, sw]) => (
                <div key={id} className="flex items-center justify-between bg-slate-700/50 rounded-lg p-2">
                  <div className="flex items-center gap-2">
                    {sw.status === 'active' ? (
                      <CheckCircle className="w-4 h-4 text-green-400"/>
                    ) : (
                      <XCircle className="w-4 h-4 text-red-400 animate-pulse"/>
                    )}
                    <span className="text-sm text-slate-300 font-medium">{id.toUpperCase()}</span>
                    <span className="text-xs text-slate-500">{sw.name}</span>
                  </div>
                  <button
                    onClick={() => onToggleSwitch(id, sw.status === 'active' ? 'fail' : 'restore')}
                    className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                      sw.status === 'active'
                        ? 'bg-red-600 hover:bg-red-500 text-white'
                        : 'bg-green-600 hover:bg-green-500 text-white'
                    }`}
                  >
                    {sw.status === 'active' ? 'Fail' : 'Restore'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        {/* Links */}
        <div>
          <h3 className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
            <Link className="w-4 h-4"/>Links
          </h3>
          
          {/* Core Links */}
          <div className="mb-3">
            <span className="text-xs text-blue-400 mb-1 block">Core Mesh</span>
            <div className="space-y-1">
              {coreLinks.map(link => (
                <div key={link.id} className="flex items-center justify-between bg-slate-700/50 rounded-lg p-2">
                  <div className="flex items-center gap-2">
                    <Link className={`w-4 h-4 ${link.status === 'active' ? 'text-green-400' : 'text-red-400'}`}/>
                    <span className="text-sm text-slate-300">
                      {link.source.toUpperCase()} ↔ {link.target.toUpperCase()}
                    </span>
                    <span className="text-xs text-slate-500">{link.bandwidth}Mbps</span>
                  </div>
                  <button
                    onClick={() => onToggleLink(link.id, link.status === 'active' ? 'fail' : 'restore')}
                    className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                      link.status === 'active'
                        ? 'bg-red-600 hover:bg-red-500 text-white'
                        : 'bg-green-600 hover:bg-green-500 text-white'
                    }`}
                  >
                    {link.status === 'active' ? 'Fail' : 'Restore'}
                  </button>
                </div>
              ))}
            </div>
          </div>
          
          {/* Zone Links */}
          <div>
            <span className="text-xs text-indigo-400 mb-1 block">Zone to Core</span>
            <div className="space-y-1">
              {zoneLinks.map(link => (
                <div key={link.id} className="flex items-center justify-between bg-slate-700/50 rounded-lg p-2">
                  <div className="flex items-center gap-2">
                    <Link className={`w-4 h-4 ${link.status === 'active' ? 'text-green-400' : 'text-red-400'}`}/>
                    <span className="text-sm text-slate-300">
                      {link.source.toUpperCase()} → {link.target.toUpperCase()}
                    </span>
                    <span className="text-xs text-slate-500">{link.bandwidth}Mbps</span>
                  </div>
                  <button
                    onClick={() => onToggleLink(link.id, link.status === 'active' ? 'fail' : 'restore')}
                    className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                      link.status === 'active'
                        ? 'bg-red-600 hover:bg-red-500 text-white'
                        : 'bg-green-600 hover:bg-green-500 text-white'
                    }`}
                  >
                    {link.status === 'active' ? 'Fail' : 'Restore'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
