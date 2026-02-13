import { useState, useMemo, useCallback, useRef, useEffect } from 'react'

// SVG Icon Components
const SensorIcon = ({ type }) => {
  const icons = {
    flood: (
      <svg viewBox="0 0 24 24" width="18" height="18">
        <path d="M4 8 Q8 2, 12 8 Q16 14, 20 8" stroke="currentColor" strokeWidth="2" fill="none"/>
        <path d="M4 14 Q8 8, 12 14 Q16 20, 20 14" stroke="currentColor" strokeWidth="2" fill="none"/>
      </svg>
    ),
    earthquake: (
      <svg viewBox="0 0 24 24" width="18" height="18">
        <path d="M2 12 L6 4 L10 16 L14 8 L18 12 L22 12" stroke="currentColor" strokeWidth="2" fill="none"/>
      </svg>
    ),
    fire: (
      <svg viewBox="0 0 24 24" width="18" height="18">
        <path d="M12 2 Q16 6, 14 10 Q18 8, 16 14 Q20 12, 18 18 L6 18 Q4 12, 8 14 Q6 8, 10 10 Q8 6, 12 2" fill="currentColor"/>
      </svg>
    )
  }
  return icons[type] || icons.flood
}

// Main Component
export default function TopologyVisualization({
  switches = {},
  switchLinks = [],
  gateways = {},
  gatewayLinks = [],
  sensors = {},
  display,
  routes = {},
  packets = [],
  currentIntent = 'balanced',
  packetStats = { forwarded: 0, dropped: 0, total: 0 },
  onUpdateSensor
}) {
  const [selectedSensor, setSelectedSensor] = useState(null)
  const svgRef = useRef(null)

  // Close popup when clicking outside
  useEffect(() => {
    const handleClick = (e) => {
      if (svgRef.current && !svgRef.current.contains(e.target)) {
        setSelectedSensor(null)
      }
    }
    document.addEventListener('click', handleClick)
    return () => document.removeEventListener('click', handleClick)
  }, [])

  // Node positions - WIDE layout, display on RIGHT side away from switches
  const positions = useMemo(() => ({
    // Core switches triangle (center-left area)
    s1: { x: 250, y: 120 },
    s2: { x: 400, y: 120 },
    s3: { x: 325, y: 200 },
    // Zone switches spread below
    s4: { x: 180, y: 300 },
    s5: { x: 325, y: 340 },
    s6: { x: 470, y: 300 },
    // Display on FAR RIGHT side (not overlapping)
    display: { x: 700, y: 160 },
    // Gateways at bottom
    gw_a: { x: 100, y: 420 },
    gw_b: { x: 325, y: 460 },
    gw_c: { x: 550, y: 420 },
    // Sensors below gateways
    water_a1: { x: 50, y: 520 },
    rain_a2: { x: 150, y: 520 },
    seismic_b1: { x: 275, y: 540 },
    tilt_b2: { x: 375, y: 540 },
    temp_c1: { x: 500, y: 520 },
    smoke_c2: { x: 600, y: 520 }
  }), [])

  // Get active route paths for highlighting
  const activeRoutePaths = useMemo(() => {
    const paths = new Set()
    Object.values(routes).forEach(route => {
      if (route?.path) {
        for (let i = 0; i < route.path.length - 1; i++) {
          paths.add(`${route.path[i]}-${route.path[i + 1]}`)
          paths.add(`${route.path[i + 1]}-${route.path[i]}`)
        }
      }
    })
    return paths
  }, [routes])

  const isActiveRoute = useCallback((source, target) => {
    return activeRoutePaths.has(`${source}-${target}`)
  }, [activeRoutePaths])

  // Color helpers
  const getStatusColor = (status) => {
    if (status === 'EMERGENCY') return '#ef4444'
    if (status === 'WARNING') return '#f59e0b'
    return '#22c55e'
  }

  const intentColors = {
    'high_priority': { primary: '#ef4444', label: 'EMERGENCY' },
    'low_latency': { primary: '#f59e0b', label: 'ALERT' },
    'balanced': { primary: '#22c55e', label: 'NORMAL' }
  }
  const intent = intentColors[currentIntent] || intentColors.balanced

  // Handle sensor click
  const handleSensorClick = (sensorId, e) => {
    e.stopPropagation()
    setSelectedSensor(selectedSensor === sensorId ? null : sensorId)
  }

  // Curved path for backup links
  const getCurvedPath = (from, to, curve = 0) => {
    if (curve === 0) return `M ${from.x} ${from.y} L ${to.x} ${to.y}`
    const midX = (from.x + to.x) / 2
    const midY = (from.y + to.y) / 2
    const len = Math.sqrt((to.x - from.x) ** 2 + (to.y - from.y) ** 2)
    const nx = -(to.y - from.y) / len * curve
    const ny = (to.x - from.x) / len * curve
    return `M ${from.x} ${from.y} Q ${midX + nx} ${midY + ny} ${to.x} ${to.y}`
  }

  return (
    <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-bold text-white">Network Topology</h2>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-green-500"/>
              <span className="text-green-400">{packetStats.forwarded} sent</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-red-500"/>
              <span className="text-red-400">{packetStats.dropped} dropped</span>
            </span>
          </div>
          <span 
            className="px-3 py-1 rounded-full text-xs font-semibold"
            style={{ backgroundColor: `${intent.primary}20`, color: intent.primary, border: `1px solid ${intent.primary}` }}
          >
            {intent.label} MODE
          </span>
        </div>
      </div>

      {/* SVG Canvas */}
      <svg 
        ref={svgRef}
        viewBox="0 0 800 600" 
        className="w-full bg-slate-900/50 rounded-lg"
        style={{ minHeight: '500px' }}
        onClick={() => setSelectedSensor(null)}
      >
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>

        {/* Display to Core Links */}
        {['s1', 's2', 's3'].map(sw => {
          const from = positions.display
          const to = positions[sw]
          const swObj = switches[sw]
          const isActive = swObj?.status === 'active'
          const onRoute = isActiveRoute('display', sw)
          return (
            <line key={`disp-${sw}`}
              x1={from.x - 40} y1={from.y}
              x2={to.x + 25} y2={to.y}
              stroke={!isActive ? '#ef4444' : onRoute ? '#22c55e' : '#06b6d4'}
              strokeWidth={onRoute ? 3 : 2}
              strokeDasharray={onRoute ? undefined : '6,4'}
              opacity={0.7}
            />
          )
        })}

        {/* Switch Links */}
        {switchLinks.map(link => {
          const from = positions[link.source]
          const to = positions[link.target]
          if (!from || !to) return null
          
          const onRoute = isActiveRoute(link.source, link.target)
          const isFailed = link.status === 'failed'
          
          return (
            <g key={link.id}>
              <line
                x1={from.x} y1={from.y}
                x2={to.x} y2={to.y}
                stroke={isFailed ? '#ef4444' : onRoute ? '#22c55e' : '#475569'}
                strokeWidth={onRoute ? 4 : 2}
                strokeDasharray={isFailed ? '5,5' : undefined}
              />
              {onRoute && (
                <line
                  x1={from.x} y1={from.y}
                  x2={to.x} y2={to.y}
                  stroke="#22c55e"
                  strokeWidth={6}
                  opacity={0.3}
                  className="animate-pulse"
                />
              )}
            </g>
          )
        })}

        {/* Gateway Links */}
        {gatewayLinks.map((link, idx) => {
          const from = positions[link.source]
          const to = positions[link.target]
          if (!from || !to) return null
          
          const gw = gateways[link.source]
          const sw = switches[link.target]
          const isActive = gw?.status === 'active' && sw?.status === 'active'
          const isPrimary = gw?.active_uplink === link.target
          const curve = link.type === 'backup' ? (idx % 2 === 0 ? 30 : -30) : 0
          
          return (
            <path key={link.id}
              d={getCurvedPath(from, to, curve)}
              fill="none"
              stroke={!isActive ? '#ef4444' : isPrimary ? '#a855f7' : '#64748b'}
              strokeWidth={isPrimary ? 2.5 : 1.5}
              strokeDasharray={link.type === 'backup' ? '4,4' : undefined}
            />
          )
        })}

        {/* Sensor to Gateway Links */}
        {Object.entries(sensors).map(([id, sensor]) => {
          const from = positions[id]
          const to = positions[sensor.gateway]
          if (!from || !to) return null
          
          return (
            <line key={`sl-${id}`}
              x1={from.x} y1={from.y - 18}
              x2={to.x} y2={to.y + 18}
              stroke={getStatusColor(sensor.status)}
              strokeWidth={1.5}
              strokeDasharray="3,3"
              opacity={0.6}
            />
          )
        })}

        {/* Switches */}
        {Object.entries(switches).map(([id, sw]) => {
          const pos = positions[id]
          if (!pos) return null
          const isActive = sw.status === 'active'
          const isCore = sw.type === 'core'
          
          return (
            <g key={id}>
              <rect x={pos.x - 30} y={pos.y - 20} width={60} height={40} rx={6}
                fill={isActive ? '#0f172a' : '#450a0a'}
                stroke={isActive ? (isCore ? '#3b82f6' : '#6366f1') : '#ef4444'}
                strokeWidth={isCore ? 3 : 2}
              />
              <text x={pos.x} y={pos.y - 2} textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">
                {id.toUpperCase()}
              </text>
              <text x={pos.x} y={pos.y + 12} textAnchor="middle" fill="#94a3b8" fontSize="9">
                {isCore ? 'Core' : 'Zone'}
              </text>
              {!isActive && <circle cx={pos.x + 22} cy={pos.y - 14} r={6} fill="#ef4444" className="animate-pulse"/>}
            </g>
          )
        })}

        {/* Gateways */}
        {Object.entries(gateways).map(([id, gw]) => {
          const pos = positions[id]
          if (!pos) return null
          const color = getStatusColor(gw.priority)
          
          return (
            <g key={id}>
              <rect x={pos.x - 40} y={pos.y - 18} width={80} height={36} rx={6}
                fill="#1e293b" stroke={color} strokeWidth={2}
              />
              <text x={pos.x} y={pos.y - 2} textAnchor="middle" fill="white" fontSize="11" fontWeight="bold">
                {id.replace('gw_', 'GW-').toUpperCase()}
              </text>
              <text x={pos.x} y={pos.y + 11} textAnchor="middle" fill="#94a3b8" fontSize="9">
                {gw.ip}
              </text>
            </g>
          )
        })}

        {/* Display - Control Center */}
        <g>
          <rect x={positions.display.x - 55} y={positions.display.y - 45} width={110} height={90} rx={8}
            fill="#1e3a5f" stroke="#06b6d4" strokeWidth={2}
          />
          <text x={positions.display.x} y={positions.display.y - 25} textAnchor="middle" fill="#06b6d4" fontSize="11" fontWeight="bold">
            CONTROL CENTER
          </text>
          <text x={positions.display.x} y={positions.display.y - 10} textAnchor="middle" fill="#94a3b8" fontSize="9">
            10.0.0.100
          </text>
          {/* Live sensor readings in display */}
          {Object.values(sensors).slice(0, 4).map((sensor, i) => (
            <g key={sensor.id}>
              <rect x={positions.display.x - 48} y={positions.display.y + i * 14} width={96} height={12} rx={2}
                fill={`${getStatusColor(sensor.status)}20`}
              />
              <text x={positions.display.x - 44} y={positions.display.y + 9 + i * 14} fill="white" fontSize="8">
                {sensor.name}
              </text>
              <text x={positions.display.x + 44} y={positions.display.y + 9 + i * 14} textAnchor="end" fill={getStatusColor(sensor.status)} fontSize="8" fontWeight="bold">
                {sensor.value}{sensor.unit}
              </text>
            </g>
          ))}
        </g>

        {/* Sensors - CLICKABLE */}
        {Object.entries(sensors).map(([id, sensor]) => {
          const pos = positions[id]
          if (!pos) return null
          const color = getStatusColor(sensor.status)
          const isSelected = selectedSensor === id
          
          return (
            <g key={id} style={{ cursor: 'pointer' }} onClick={(e) => handleSensorClick(id, e)}>
              {/* Selection ring */}
              {isSelected && (
                <circle cx={pos.x} cy={pos.y} r={28} fill="none" stroke={color} strokeWidth={2} strokeDasharray="4,2"/>
              )}
              {/* Sensor circle */}
              <circle cx={pos.x} cy={pos.y} r={22}
                fill="#1e293b" stroke={color} strokeWidth={isSelected ? 3 : 2}
                className={sensor.status === 'EMERGENCY' ? 'animate-pulse' : ''}
              />
              {/* Icon */}
              <g transform={`translate(${pos.x - 9}, ${pos.y - 9})`} style={{ color }}>
                <SensorIcon type={sensor.type}/>
              </g>
              {/* Label */}
              <text x={pos.x} y={pos.y + 38} textAnchor="middle" fill="white" fontSize="9">
                {sensor.name}
              </text>
              <text x={pos.x} y={pos.y + 50} textAnchor="middle" fill={color} fontSize="10" fontWeight="bold">
                {sensor.value}{sensor.unit}
              </text>
              
              {/* SLIDER POPUP */}
              {isSelected && (
                <g onClick={(e) => e.stopPropagation()}>
                  <rect x={pos.x - 85} y={pos.y - 110} width={170} height={80} rx={8}
                    fill="#1e293b" stroke={color} strokeWidth={2}
                  />
                  {/* Title */}
                  <text x={pos.x - 75} y={pos.y - 90} fill="white" fontSize="11" fontWeight="bold">
                    {sensor.name}
                  </text>
                  {/* Status badge */}
                  <rect x={pos.x + 20} y={pos.y - 102} width={55} height={16} rx={4} fill={color}/>
                  <text x={pos.x + 47} y={pos.y - 90} textAnchor="middle" fill="white" fontSize="8" fontWeight="bold">
                    {sensor.status}
                  </text>
                  {/* Value display */}
                  <text x={pos.x} y={pos.y - 65} textAnchor="middle" fill={color} fontSize="20" fontWeight="bold">
                    {sensor.value}{sensor.unit}
                  </text>
                  {/* Slider background */}
                  <rect x={pos.x - 75} y={pos.y - 48} width={150} height={8} rx={4} fill="#475569"/>
                  {/* Slider fill */}
                  <rect x={pos.x - 75} y={pos.y - 48} width={sensor.value * 1.5} height={8} rx={4} fill={color}/>
                  {/* Slider handle */}
                  <circle cx={pos.x - 75 + sensor.value * 1.5} cy={pos.y - 44} r={10} fill={color} stroke="white" strokeWidth={2}/>
                  {/* Invisible slider input overlay */}
                  <foreignObject x={pos.x - 80} y={pos.y - 55} width={160} height={24}>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={sensor.value}
                      onChange={(e) => onUpdateSensor?.(id, e.target.value)}
                      style={{
                        width: '100%',
                        height: '24px',
                        opacity: 0,
                        cursor: 'pointer'
                      }}
                    />
                  </foreignObject>
                </g>
              )}
            </g>
          )
        })}

        {/* Route Info */}
        <g>
          <rect x={10} y={10} width={150} height={80} rx={6} fill="#0f172a" stroke="#6366f1" strokeWidth={1}/>
          <text x={20} y={28} fill="#a855f7" fontSize="10" fontWeight="bold">ACTIVE ROUTES</text>
          {Object.values(routes).slice(0, 3).map((route, i) => (
            <g key={i}>
              <text x={20} y={45 + i * 16} fill="#94a3b8" fontSize="8">
                {route?.gateway?.replace('gw_', 'GW-')}: cost {route?.cost?.toFixed(1) || '?'}
              </text>
            </g>
          ))}
        </g>

        {/* Legend */}
        <g transform="translate(620, 560)">
          <rect x="0" y="0" width="170" height="30" rx={4} fill="#1e293b"/>
          <text x="10" y="12" fill="#94a3b8" fontSize="8">Click sensors to adjust values</text>
          <text x="10" y="24" fill="#64748b" fontSize="7">Auto-refresh: 1.5s</text>
        </g>
      </svg>
    </div>
  )
}
