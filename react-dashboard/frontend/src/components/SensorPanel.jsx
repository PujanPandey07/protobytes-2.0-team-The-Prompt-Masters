import { useCallback, useMemo } from 'react'
import { Droplets, Mountain, Flame, Battery, Signal, Send, Zap } from 'lucide-react'

const SENSOR_ICONS = { flood: Droplets, earthquake: Mountain, fire: Flame }
const TYPE_COLORS = { flood: 'blue', earthquake: 'amber', fire: 'orange' }
const TYPE_BG = { flood: 'bg-blue-500/10', earthquake: 'bg-amber-500/10', fire: 'bg-orange-500/10' }
const STATUS_STYLES = { 
  NORMAL: 'bg-green-500/20 text-green-400 border-green-500/50', 
  WARNING: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50 animate-pulse', 
  EMERGENCY: 'bg-red-500/20 text-red-400 border-red-500/50 animate-pulse' 
}

export default function SensorPanel({ sensors, gateways, onUpdateSensor, onGeneratePacket }) {
  const sensorsByType = useMemo(() => {
    return Object.values(sensors || {}).reduce((acc, sensor) => {
      (acc[sensor.type] = acc[sensor.type] || []).push(sensor)
      return acc
    }, {})
  }, [sensors])

  const handleSliderChange = useCallback((sensorId, e) => {
    onUpdateSensor(sensorId, e.target.value)
  }, [onUpdateSensor])

  const getSliderBackground = (sensor) => {
    const value = sensor.value
    const warn = sensor.threshold_warning
    const emerg = sensor.threshold_emergency
    
    let color = '#22c55e' // green
    if (value >= emerg) color = '#ef4444' // red
    else if (value >= warn) color = '#eab308' // yellow
    
    const percent = value
    return `linear-gradient(to right, ${color} 0%, ${color} ${percent}%, #334155 ${percent}%, #334155 100%)`
  }

  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <Signal className="w-5 h-5 text-green-400"/>Sensor Controls
      </h2>
      <div className="space-y-4">
        {Object.entries(sensorsByType).map(([type, typeSensors]) => {
          const Icon = SENSOR_ICONS[type] || Signal
          const color = TYPE_COLORS[type] || 'slate'
          const bg = TYPE_BG[type] || 'bg-slate-500/10'
          
          return (
            <div key={type} className={`rounded-lg p-3 border border-${color}-500/30 ${bg}`}>
              <div className="flex items-center gap-2 mb-3">
                <Icon className={`w-5 h-5 text-${color}-400`}/>
                <span className="text-sm font-medium text-white capitalize">{type} Sensors</span>
                <span className="text-xs text-slate-500 ml-auto">
                  Gateway: {typeSensors[0]?.gateway?.toUpperCase().replace('_', ' ')}
                </span>
              </div>
              <div className="space-y-4">
                {typeSensors.map(sensor => (
                  <div key={sensor.id} className="bg-slate-800/80 rounded-lg p-3 border border-slate-600/50">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-slate-200">{sensor.name}</span>
                        <span className="text-xs text-slate-500">({sensor.id})</span>
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded border ${STATUS_STYLES[sensor.status]}`}>
                        {sensor.status}
                      </span>
                    </div>
                    
                    {/* Value Display */}
                    <div className="flex items-center justify-between mb-2">
                      <span className={`text-2xl font-bold ${
                        sensor.status === 'EMERGENCY' ? 'text-red-400' :
                        sensor.status === 'WARNING' ? 'text-yellow-400' : 'text-green-400'
                      }`}>
                        {sensor.value}
                        <span className="text-sm font-normal text-slate-400 ml-1">{sensor.unit}</span>
                      </span>
                      <div className="flex gap-1">
                        <button
                          onClick={() => onGeneratePacket(sensor.gateway, sensor.id)}
                          className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-xs font-medium transition-all hover:scale-105 active:scale-95"
                          title="Send sensor data packet"
                        >
                          <Send className="w-3.5 h-3.5"/>Send
                        </button>
                      </div>
                    </div>
                    
                    {/* Slider */}
                    <div className="mb-2">
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={sensor.value}
                        onChange={(e) => handleSliderChange(sensor.id, e)}
                        className="w-full h-3 rounded-lg appearance-none cursor-pointer"
                        style={{ background: getSliderBackground(sensor) }}
                      />
                      <div className="flex justify-between text-[10px] mt-1">
                        <span className="text-slate-500">0</span>
                        <span className="text-yellow-500 flex items-center gap-0.5">
                          <Zap className="w-2.5 h-2.5"/>Warn: {sensor.threshold_warning}
                        </span>
                        <span className="text-red-500 flex items-center gap-0.5">
                          ⚠️ Emerg: {sensor.threshold_emergency}
                        </span>
                        <span className="text-slate-500">100</span>
                      </div>
                    </div>
                    
                    {/* Battery & Signal */}
                    <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-700">
                      <div className="flex items-center gap-3">
                        <span className="flex items-center gap-1">
                          <Battery className={`w-3.5 h-3.5 ${sensor.battery < 20 ? 'text-red-400' : 'text-green-400'}`}/>
                          {Math.round(sensor.battery)}%
                        </span>
                        <span className="flex items-center gap-1">
                          <Signal className="w-3.5 h-3.5"/>
                          {sensor.signal_strength}%
                        </span>
                      </div>
                      <span className="text-slate-500">IP: {sensor.ip}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
