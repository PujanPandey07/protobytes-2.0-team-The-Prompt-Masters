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

const BatteryIcon = ({ level }) => {
  const color = level < 20 ? '#ef4444' : level < 40 ? '#f59e0b' : '#22c55e'
  const width = Math.max(0, (level / 100) * 16)
  return (
    <svg viewBox="0 0 24 14" width="24" height="14">
      <rect x="0" y="1" width="20" height="12" rx="2" fill="none" stroke="#64748b" strokeWidth="1.5"/>
      <rect x="20" y="4" width="3" height="6" rx="1" fill="#64748b"/>
      <rect x="2" y="3" width={width} height="8" rx="1" fill={color}/>
    </svg>
  )
}

// Envelope Packet Icon
const EnvelopeIcon = ({ color = '#22c55e', size = 20 }) => (
  <g>
    {/* Envelope body */}
    <rect x={-size/2} y={-size/3} width={size} height={size*0.65} rx={2} 
      fill={color} stroke="white" strokeWidth={1.5}/>
    {/* Envelope flap */}
    <path d={`M${-size/2},${-size/3} L0,${size/6} L${size/2},${-size/3}`} 
      fill="none" stroke="white" strokeWidth={1.5} strokeLinejoin="round"/>
    {/* Data lines inside */}
    <line x1={-size/3} y1={size/8} x2={size/3} y2={size/8} stroke="white" strokeWidth={1} opacity={0.7}/>
    <line x1={-size/3} y1={size/4} x2={size/4} y2={size/4} stroke="white" strokeWidth={1} opacity={0.5}/>
  </g>
)

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
  onUpdateSensor,
  onUpdateSwitchBattery
}) {
  const [selectedNode, setSelectedNode] = useState(null)
  const [selectedType, setSelectedType] = useState(null)
  const [animatedPackets, setAnimatedPackets] = useState([])
  const svgRef = useRef(null)
  const animationFrameRef = useRef(null)

  // Process incoming packets
  useEffect(() => {
    if (packets.length > 0) {
      setAnimatedPackets(prev => {
        const existingIds = new Set(prev.map(p => p.id))
        const newOnes = packets
          .filter(p => !existingIds.has(p.id))
          .map(p => ({
            ...p,
            startTime: Date.now(),
            progress: 0
          }))
        // Keep recent packets + new ones
        const recent = prev.filter(p => Date.now() - p.startTime < 4000)
        return [...recent, ...newOnes]
      })
    }
  }, [packets])

  // Animation loop - update packet progress
  useEffect(() => {
    let lastTime = 0
    
    const animate = (currentTime) => {
      if (currentTime - lastTime >= 16) { // ~60fps
        lastTime = currentTime
        
        setAnimatedPackets(prev => {
          const now = Date.now()
          return prev
            .filter(p => now - p.startTime < 4000)
            .map(p => ({
              ...p,
              progress: Math.min((now - p.startTime) / 3000, 1) // 3 second animation
            }))
        })
      }
      animationFrameRef.current = requestAnimationFrame(animate)
    }
    
    animationFrameRef.current = requestAnimationFrame(animate)
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [])

  // Close popup on outside click
  useEffect(() => {
    const handle = (e) => {
      if (svgRef.current && !svgRef.current.contains(e.target)) {
        setSelectedNode(null)
        setSelectedType(null)
      }
    }
    document.addEventListener('click', handle)
    return () => document.removeEventListener('click', handle)
  }, [])

  // Node positions
  const positions = useMemo(() => ({
    s1: { x: 280, y: 100 },
    s2: { x: 420, y: 100 },
    s3: { x: 350, y: 180 },
    s4: { x: 200, y: 280 },
    s5: { x: 350, y: 320 },
    s6: { x: 500, y: 280 },
    display: { x: 600, y: 140 },
    gw_a: { x: 120, y: 400 },
    gw_b: { x: 350, y: 440 },
    gw_c: { x: 580, y: 400 },
    water_a1: { x: 60, y: 500 },
    rain_a2: { x: 180, y: 500 },
    seismic_b1: { x: 290, y: 520 },
    tilt_b2: { x: 410, y: 520 },
    temp_c1: { x: 520, y: 500 },
    smoke_c2: { x: 640, y: 500 }
  }), [])

  // Active route paths for highlighting
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

  const handleNodeClick = (nodeId, type, e) => {
    e.stopPropagation()
    if (selectedNode === nodeId) {
      setSelectedNode(null)
      setSelectedType(null)
    } else {
      setSelectedNode(nodeId)
      setSelectedType(type)
    }
  }

  // Calculate packet position along its path
  const getPacketPosition = useCallback((pkt) => {
    if (!pkt.path || pkt.path.length < 2 || pkt.progress >= 1) return null
    
    const totalSegments = pkt.path.length - 1
    const progressPosition = pkt.progress * totalSegments
    const currentSegment = Math.min(Math.floor(progressPosition), totalSegments - 1)
    const segmentProgress = progressPosition - currentSegment
    
    const fromNodeId = pkt.path[currentSegment]
    const toNodeId = pkt.path[currentSegment + 1]
    const from = positions[fromNodeId]
    const to = positions[toNodeId]
    
    if (!from || !to) return null
    
    // Calculate position
    const x = from.x + (to.x - from.x) * segmentProgress
    const y = from.y + (to.y - from.y) * segmentProgress
    
    // Calculate angle for envelope rotation
    const angle = Math.atan2(to.y - from.y, to.x - from.x) * (180 / Math.PI)
    
    return { x, y, angle, priority: pkt.priority }
  }, [positions])

  // Sensor Slider Popup
  const SensorSlider = ({ sensorId, pos }) => {
    const sensor = sensors[sensorId]
    if (!sensor) return null
    const color = getStatusColor(sensor.status)
    
    return (
      <g onClick={e => e.stopPropagation()}>
        <rect x={pos.x - 85} y={pos.y - 115} width={170} height={90} rx={8}
          fill="#1e293b" stroke={color} strokeWidth={2}/>
        <text x={pos.x - 75} y={pos.y - 95} fill="white" fontSize="11" fontWeight="bold">
          {sensor.name}
        </text>
        <rect x={pos.x + 20} y={pos.y - 108} width={55} height={16} rx={4} fill={color}/>
        <text x={pos.x + 47} y={pos.y - 96} textAnchor="middle" fill="white" fontSize="8" fontWeight="bold">
          {sensor.status}
        </text>
        <text x={pos.x} y={pos.y - 65} textAnchor="middle" fill={color} fontSize="22" fontWeight="bold">
          {sensor.value}{sensor.unit}
        </text>
        <rect x={pos.x - 75} y={pos.y - 45} width={150} height={8} rx={4} fill="#475569"/>
        <rect x={pos.x - 75} y={pos.y - 45} width={sensor.value * 1.5} height={8} rx={4} fill={color}/>
        <circle cx={pos.x - 75 + sensor.value * 1.5} cy={pos.y - 41} r={10} fill={color} stroke="white" strokeWidth={2}/>
        <foreignObject x={pos.x - 80} y={pos.y - 52} width={160} height={24}>
          <input type="range" min="0" max="100" value={sensor.value}
            onChange={(e) => onUpdateSensor?.(sensorId, e.target.value)}
            style={{ width: '100%', height: '24px', opacity: 0, cursor: 'pointer' }}/>
        </foreignObject>
      </g>
    )
  }

  // Switch Battery Slider Popup
  const SwitchSlider = ({ switchId, pos }) => {
    const sw = switches[switchId]
    if (!sw) return null
    const battery = sw.battery || 100
    const color = battery < 20 ? '#ef4444' : battery < 40 ? '#f59e0b' : '#22c55e'
    
    return (
      <g onClick={e => e.stopPropagation()}>
        <rect x={pos.x - 75} y={pos.y - 95} width={150} height={75} rx={8}
          fill="#1e293b" stroke={color} strokeWidth={2}/>
        <text x={pos.x - 65} y={pos.y - 75} fill="white" fontSize="10" fontWeight="bold">
          {sw.name || switchId.toUpperCase()}
        </text>
        <text x={pos.x} y={pos.y - 50} textAnchor="middle" fill={color} fontSize="20" fontWeight="bold">
          {Math.round(battery)}%
        </text>
        <g transform={`translate(${pos.x + 30}, ${pos.y - 68})`}>
          <BatteryIcon level={battery}/>
        </g>
        <rect x={pos.x - 65} y={pos.y - 35} width={130} height={6} rx={3} fill="#475569"/>
        <rect x={pos.x - 65} y={pos.y - 35} width={battery * 1.3} height={6} rx={3} fill={color}/>
        <circle cx={pos.x - 65 + battery * 1.3} cy={pos.y - 32} r={8} fill={color} stroke="white" strokeWidth={2}/>
        <foreignObject x={pos.x - 70} y={pos.y - 42} width={140} height={20}>
          <input type="range" min="0" max="100" value={battery}
            onChange={(e) => onUpdateSwitchBattery?.(switchId, e.target.value)}
            style={{ width: '100%', height: '20px', opacity: 0, cursor: 'pointer' }}/>
        </foreignObject>
      </g>
    )
  }

  // Get packets currently in flight
  const activePackets = animatedPackets.filter(p => p.progress < 1)

  return (
    <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-bold text-white">Network Topology</h2>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"/>
              <span className="text-green-400">{packetStats.forwarded} sent</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-red-500"/>
              <span className="text-red-400">{packetStats.dropped} dropped</span>
            </span>
            <span className="flex items-center gap-1 text-cyan-400 font-medium">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <rect x="2" y="6" width="20" height="14" rx="2" fill="currentColor"/>
                <path d="M2,6 L12,14 L22,6" fill="none" stroke="#0e7490" strokeWidth="2"/>
              </svg>
              {activePackets.length} in-flight
            </span>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-semibold"
            style={{ backgroundColor: `${intent.primary}20`, color: intent.primary, border: `1px solid ${intent.primary}` }}>
            {intent.label} MODE
          </span>
        </div>
      </div>

      {/* SVG Canvas */}
      <svg ref={svgRef} viewBox="0 0 720 560" className="w-full h-auto bg-slate-900/50 rounded-lg"
        onClick={() => { setSelectedNode(null); setSelectedType(null); }}>
        
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
          <filter id="packetGlow">
            <feGaussianBlur stdDeviation="5" result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
          <filter id="shadow">
            <feDropShadow dx="2" dy="2" stdDeviation="3" floodOpacity="0.5"/>
          </filter>
        </defs>

        {/* Switch Links */}
        {switchLinks.map(link => {
          const from = positions[link.source]
          const to = positions[link.target]
          if (!from || !to) return null
          const isActive = isActiveRoute(link.source, link.target)
          const isFailed = link.status === 'failed'
          
          return (
            <g key={link.id}>
              {/* Glow effect for active routes */}
              {isActive && !isFailed && (
                <line x1={from.x} y1={from.y} x2={to.x} y2={to.y}
                  stroke="#22c55e" strokeWidth={8} opacity={0.2} filter="url(#glow)"/>
              )}
              <line
                x1={from.x} y1={from.y} x2={to.x} y2={to.y}
                stroke={isFailed ? '#ef4444' : isActive ? '#22c55e' : '#475569'}
                strokeWidth={isActive ? 3 : 2}
                strokeDasharray={isFailed ? '8,4' : undefined}
                className={isFailed ? 'animate-pulse' : ''}/>
            </g>
          )
        })}

        {/* Display connections */}
        {['s1', 's2', 's3'].map(swId => {
          const sw = positions[swId]
          const disp = positions.display
          const isActive = isActiveRoute(swId, 'display')
          return (
            <line key={`disp-${swId}`}
              x1={sw.x} y1={sw.y} x2={disp.x} y2={disp.y}
              stroke={isActive ? '#06b6d4' : '#06b6d4'}
              strokeWidth={isActive ? 2.5 : 1.5}
              strokeDasharray={isActive ? undefined : '4,4'}
              opacity={isActive ? 0.9 : 0.4}/>
          )
        })}

        {/* Gateway Links */}
        {gatewayLinks.map(link => {
          const from = positions[link.source]
          const to = positions[link.target]
          if (!from || !to) return null
          const isActive = isActiveRoute(link.source, link.target)
          
          return (
            <line key={link.id}
              x1={from.x} y1={from.y} x2={to.x} y2={to.y}
              stroke={isActive ? '#a855f7' : '#6b21a8'}
              strokeWidth={isActive ? 2.5 : 1.5}
              strokeDasharray={link.type === 'backup' && !isActive ? '4,4' : undefined}
              opacity={isActive ? 0.9 : 0.5}/>
          )
        })}

        {/* Sensor Links */}
        {Object.values(sensors).map(sensor => {
          const from = positions[sensor.id]
          const to = positions[sensor.gateway]
          if (!from || !to) return null
          return (
            <line key={`sl-${sensor.id}`}
              x1={from.x} y1={from.y - 18} x2={to.x} y2={to.y + 16}
              stroke={getStatusColor(sensor.status)} strokeWidth={1.5}
              strokeDasharray="3,3" opacity={0.5}/>
          )
        })}

        {/* ===== PACKET ANIMATION - ENVELOPE ICONS ===== */}
        {activePackets.map((pkt, idx) => {
          const pos = getPacketPosition(pkt)
          if (!pos) return null
          
          const color = pos.priority === 'EMERGENCY' ? '#ef4444' : 
                       pos.priority === 'WARNING' ? '#f59e0b' : '#22c55e'
          const size = pos.priority === 'EMERGENCY' ? 28 : pos.priority === 'WARNING' ? 24 : 20
          
          return (
            <g key={pkt.id || idx} transform={`translate(${pos.x}, ${pos.y})`} filter="url(#shadow)">
              {/* Trail effect */}
              <circle r={size * 0.6} fill={color} opacity={0.2}>
                <animate attributeName="r" values={`${size * 0.4};${size};${size * 0.4}`} dur="0.6s" repeatCount="indefinite"/>
                <animate attributeName="opacity" values="0.3;0.1;0.3" dur="0.6s" repeatCount="indefinite"/>
              </circle>
              
              {/* Envelope packet */}
              <g transform={`rotate(${pos.angle || 0})`}>
                {/* Envelope body */}
                <rect x={-size/2} y={-size/3} width={size} height={size*0.6} rx={2} 
                  fill={color} stroke="white" strokeWidth={1.5}/>
                {/* Envelope flap (V shape) */}
                <path d={`M${-size/2},${-size/3} L0,${size/8} L${size/2},${-size/3}`} 
                  fill="none" stroke="white" strokeWidth={1.5} strokeLinejoin="round"/>
                {/* Data indicator lines */}
                <line x1={-size/4} y1={size/10} x2={size/4} y2={size/10} stroke="white" strokeWidth={1} opacity={0.7}/>
              </g>
              
              {/* Priority indicator dot */}
              <circle cx={size/2 + 2} cy={-size/3 - 2} r={4} fill="white" stroke={color} strokeWidth={1.5}/>
            </g>
          )
        })}

        {/* Switches */}
        {Object.entries(switches).map(([id, sw]) => {
          const pos = positions[id]
          if (!pos) return null
          const isActive = sw.status === 'active'
          const isCore = sw.type === 'core'
          const battery = sw.battery || 100
          const batteryColor = battery < 20 ? '#ef4444' : battery < 40 ? '#f59e0b' : '#3b82f6'
          
          return (
            <g key={id} style={{ cursor: 'pointer' }} onClick={e => handleNodeClick(id, 'switch', e)}>
              <rect x={pos.x - 30} y={pos.y - 20} width={60} height={40} rx={6}
                fill={isActive ? '#0f172a' : '#450a0a'}
                stroke={isActive ? batteryColor : '#ef4444'}
                strokeWidth={selectedNode === id ? 3 : 2}/>
              <text x={pos.x} y={pos.y - 2} textAnchor="middle" fill="white" fontSize="11" fontWeight="bold">
                {id.toUpperCase()}
              </text>
              <text x={pos.x} y={pos.y + 12} textAnchor="middle" fill="#94a3b8" fontSize="8">
                {isCore ? 'Core' : 'Zone'}
              </text>
              <g transform={`translate(${pos.x - 12}, ${pos.y + 18})`}>
                <BatteryIcon level={battery}/>
              </g>
              {!isActive && <circle cx={pos.x + 22} cy={pos.y - 14} r={5} fill="#ef4444" className="animate-pulse"/>}
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
              <rect x={pos.x - 38} y={pos.y - 16} width={76} height={32} rx={5}
                fill="#1e293b" stroke={color} strokeWidth={2}/>
              <text x={pos.x} y={pos.y - 1} textAnchor="middle" fill="white" fontSize="10" fontWeight="bold">
                {id.replace('gw_', 'GW-').toUpperCase()}
              </text>
              <text x={pos.x} y={pos.y + 10} textAnchor="middle" fill="#94a3b8" fontSize="8">
                {gw.ip}
              </text>
            </g>
          )
        })}

        {/* Display - Control Center */}
        <g>
          <rect x={positions.display.x - 50} y={positions.display.y - 38} width={100} height={76} rx={6}
            fill="#1e3a5f" stroke="#06b6d4" strokeWidth={2}/>
          <text x={positions.display.x} y={positions.display.y - 22} textAnchor="middle" fill="#06b6d4" fontSize="9" fontWeight="bold">
            CONTROL CENTER
          </text>
          {(display?.current_data || []).slice(0, 3).map((data, i) => (
            <g key={i}>
              <rect x={positions.display.x - 45} y={positions.display.y - 10 + i * 18} width={90} height={15} rx={2}
                fill={`${getStatusColor(data.priority)}15`}/>
              <text x={positions.display.x - 42} y={positions.display.y + 1 + i * 18} fill="white" fontSize="7">
                {data.sensor_name?.slice(0, 8) || 'N/A'}
              </text>
              <text x={positions.display.x + 42} y={positions.display.y + 1 + i * 18} textAnchor="end"
                fill={getStatusColor(data.priority)} fontSize="8" fontWeight="bold">
                {data.value}{data.unit}
              </text>
            </g>
          ))}
        </g>

        {/* Sensors */}
        {Object.entries(sensors).map(([id, sensor]) => {
          const pos = positions[id]
          if (!pos) return null
          const color = getStatusColor(sensor.status)
          const isSelected = selectedNode === id && selectedType === 'sensor'
          
          return (
            <g key={id} style={{ cursor: 'pointer' }} onClick={e => handleNodeClick(id, 'sensor', e)}>
              {isSelected && (
                <circle cx={pos.x} cy={pos.y} r={28} fill="none" stroke={color} strokeWidth={2} strokeDasharray="4,2"/>
              )}
              <circle cx={pos.x} cy={pos.y} r={22}
                fill="#1e293b" stroke={color} strokeWidth={isSelected ? 3 : 2}
                className={sensor.status === 'EMERGENCY' ? 'animate-pulse' : ''}/>
              <g transform={`translate(${pos.x - 9}, ${pos.y - 9})`} style={{ color }}>
                <SensorIcon type={sensor.type}/>
              </g>
              <text x={pos.x} y={pos.y + 38} textAnchor="middle" fill="white" fontSize="8">
                {sensor.name}
              </text>
              <text x={pos.x} y={pos.y + 50} textAnchor="middle" fill={color} fontSize="9" fontWeight="bold">
                {sensor.value}{sensor.unit}
              </text>
            </g>
          )
        })}

        {/* Slider Popups */}
        {selectedNode && selectedType === 'sensor' && positions[selectedNode] && (
          <SensorSlider sensorId={selectedNode} pos={positions[selectedNode]}/>
        )}
        {selectedNode && selectedType === 'switch' && positions[selectedNode] && (
          <SwitchSlider switchId={selectedNode} pos={positions[selectedNode]}/>
        )}

        {/* Legend */}
        <g transform="translate(10, 530)">
          <rect x="0" y="0" width="250" height="22" rx={4} fill="#1e293b" opacity="0.9"/>
          <text x="10" y="14" fill="#94a3b8" fontSize="9">
            Click nodes to adjust • Envelopes = packets in transit
          </text>
        </g>
      </svg>
    </div>
  )
}
