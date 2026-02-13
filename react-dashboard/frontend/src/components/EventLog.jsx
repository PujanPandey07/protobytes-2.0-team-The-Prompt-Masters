import { ScrollText, Info, AlertTriangle, AlertCircle } from 'lucide-react'

const PRIORITY_ICONS = { INFO: Info, WARNING: AlertTriangle, CRITICAL: AlertCircle }
const PRIORITY_COLORS = { INFO: 'text-blue-400', WARNING: 'text-yellow-400', CRITICAL: 'text-red-400' }

export default function EventLog({ events }) {
  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><ScrollText className="w-5 h-5 text-slate-400"/>Event Log</h2>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {events.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-4">No events yet</p>
        ) : (
          events.slice(0, 50).map((event, i) => {
            const Icon = PRIORITY_ICONS[event.priority] || Info
            return (
              <div key={i} className="flex items-start gap-2 text-xs bg-slate-700/30 rounded p-2">
                <Icon className={`w-4 h-4 flex-shrink-0 mt-0.5 ${PRIORITY_COLORS[event.priority]}`}/>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className={`font-medium ${PRIORITY_COLORS[event.priority]}`}>{event.type}</span>
                    <span className="text-slate-500">{event.timestamp}</span>
                  </div>
                  <p className="text-slate-400 truncate">{event.message}</p>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
