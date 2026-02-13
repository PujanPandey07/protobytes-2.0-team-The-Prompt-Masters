import { useState, useEffect, useCallback, useRef } from 'react'
import Header from './components/Header'
import TopologyVisualization from './components/TopologyVisualization'
import GatewayPanel from './components/GatewayPanel'
import ControllerPanel from './components/ControllerPanel'
import FailureControls from './components/FailureControls'
import EventLog from './components/EventLog'

const BACKEND_URL = 'http://localhost:5000'
const POLL_INTERVAL = 1000  // Faster polling for responsiveness

export default function App() {
  const [sensors, setSensors] = useState({})
  const [gateways, setGateways] = useState({})
  const [switches, setSwitches] = useState({})
  const [switchLinks, setSwitchLinks] = useState([])
  const [gatewayLinks, setGatewayLinks] = useState([])
  const [display, setDisplay] = useState(null)
  const [routes, setRoutes] = useState({})
  const [currentIntent, setCurrentIntent] = useState('balanced')
  const [autoIntent, setAutoIntent] = useState(true)
  const [events, setEvents] = useState([])
  const [packets, setPackets] = useState([])
  const [packetStats, setPacketStats] = useState({ forwarded: 0, dropped: 0, total: 0 })
  const [connected, setConnected] = useState(false)
  const [autoPackets, setAutoPackets] = useState(true)
  
  const updateTimeoutRef = useRef({})
  const pollRef = useRef(null)

  const fetchData = useCallback(async () => {
    try {
      const [topologyRes, routesRes, intentRes, eventsRes, statsRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/topology`),
        fetch(`${BACKEND_URL}/api/routes`),
        fetch(`${BACKEND_URL}/api/intent`),
        fetch(`${BACKEND_URL}/api/events`),
        fetch(`${BACKEND_URL}/api/packet_stats`)
      ])
      
      const topology = await topologyRes.json()
      const routesData = await routesRes.json()
      const intentData = await intentRes.json()
      const eventsData = await eventsRes.json()
      const statsData = await statsRes.json()
      
      setSwitches(topology.switches || {})
      setSwitchLinks(topology.switch_links || [])
      setGateways(topology.gateways || {})
      setGatewayLinks(topology.gateway_links || [])
      setSensors(topology.sensors || {})
      setDisplay(topology.display || null)
      setRoutes(routesData || {})
      setCurrentIntent(intentData.intent || 'balanced')
      setAutoIntent(intentData.auto_intent !== false)
      setEvents(eventsData || [])
      setPacketStats(statsData || { forwarded: 0, dropped: 0, total: 0 })
      setConnected(true)
    } catch (e) {
      console.error('Fetch error:', e)
      setConnected(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    pollRef.current = setInterval(fetchData, POLL_INTERVAL)
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
      Object.values(updateTimeoutRef.current).forEach(clearTimeout)
    }
  }, [fetchData])

  // Packet cleanup and simulation
  useEffect(() => {
    const packetCleanup = setInterval(() => {
      setPackets(prev => prev.filter(p => Date.now() - p.jsTimestamp < 3500))
    }, 500)
    return () => clearInterval(packetCleanup)
  }, [])

  // Simulate packet flow based on routes
  useEffect(() => {
    if (!autoPackets || Object.keys(routes).length === 0) return
    
    const sendPacket = () => {
      const routeEntries = Object.entries(routes)
      if (routeEntries.length === 0) return
      
      // Pick a random route
      const [gwId, route] = routeEntries[Math.floor(Math.random() * routeEntries.length)]
      if (!route?.path) return
      
      const sensor = Object.values(sensors).find(s => s.gateway === gwId)
      if (!sensor) return
      
      const newPacket = {
        id: `pkt_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
        path: route.path,
        priority: sensor.status,
        gateway_id: gwId,
        sensor_id: sensor.id,
        jsTimestamp: Date.now(),
        progress: 0
      }
      
      setPackets(prev => [...prev.slice(-10), newPacket])  // Keep max 10 packets
    }
    
    sendPacket()  // Send immediately
    const interval = setInterval(sendPacket, 1500)
    return () => clearInterval(interval)
  }, [autoPackets, routes, sensors])

  // Immediate sensor update (no debounce for slider responsiveness)
  const updateSensorValue = useCallback((sensorId, value) => {
    const intValue = parseInt(value)
    setSensors(prev => ({
      ...prev,
      [sensorId]: { ...prev[sensorId], value: intValue }
    }))

    // Debounce only the API call, not the UI update
    if (updateTimeoutRef.current[sensorId]) {
      clearTimeout(updateTimeoutRef.current[sensorId])
    }

    updateTimeoutRef.current[sensorId] = setTimeout(async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/sensors/${sensorId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ value: intValue })
        })
        const data = await res.json()
        setSensors(prev => ({ ...prev, [sensorId]: data }))
        // Fetch routes update
        const routesRes = await fetch(`${BACKEND_URL}/api/routes`)
        const routesData = await routesRes.json()
        setRoutes(routesData)
      } catch (e) {
        console.error('Update sensor error:', e)
      }
    }, 50)  // Reduced debounce from 100ms to 50ms
  }, [])

  const updateSwitchBattery = useCallback((switchId, value) => {
    const intValue = parseInt(value)
    setSwitches(prev => ({
      ...prev,
      [switchId]: { ...prev[switchId], battery: intValue }
    }))

    const key = `sw_${switchId}`
    if (updateTimeoutRef.current[key]) {
      clearTimeout(updateTimeoutRef.current[key])
    }

    updateTimeoutRef.current[key] = setTimeout(async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/switches/${switchId}/battery`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ battery: intValue })
        })
        const data = await res.json()
        setSwitches(prev => ({ ...prev, [switchId]: { ...prev[switchId], battery: data.battery } }))
        // Fetch routes update
        const routesRes = await fetch(`${BACKEND_URL}/api/routes`)
        const routesData = await routesRes.json()
        setRoutes(routesData)
      } catch (e) {
        console.error('Update battery error:', e)
      }
    }, 50)  // Reduced debounce
  }, [])

  const toggleSwitch = useCallback(async (switchId, action) => {
    try {
      const endpoint = action === 'fail' 
        ? `${BACKEND_URL}/api/switches/${switchId}/fail` 
        : `${BACKEND_URL}/api/switches/${switchId}/restore`
      await fetch(endpoint, { method: 'POST' })
      // Immediate fetch for route update
      fetchData()
    } catch (e) {
      console.error('Toggle switch error:', e)
    }
  }, [fetchData])

  const toggleLink = useCallback(async (linkId, action) => {
    try {
      const endpoint = action === 'fail' 
        ? `${BACKEND_URL}/api/links/${linkId}/fail` 
        : `${BACKEND_URL}/api/links/${linkId}/restore`
      await fetch(endpoint, { method: 'POST' })
      // Immediate fetch for route update
      fetchData()
    } catch (e) {
      console.error('Toggle link error:', e)
    }
  }, [fetchData])

  const toggleAutoPackets = useCallback(async () => {
    try {
      await fetch(`${BACKEND_URL}/api/auto_packets`, { method: 'POST' })
      setAutoPackets(prev => !prev)
    } catch (e) {
      console.error('Toggle auto packets error:', e)
    }
  }, [])

  // Manual intent control
  const setIntent = useCallback(async (intent, auto = null) => {
    try {
      const body = { intent }
      if (auto !== null) body.auto = auto
      
      const res = await fetch(`${BACKEND_URL}/api/intent`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })
      const data = await res.json()
      setCurrentIntent(data.intent)
      setAutoIntent(data.auto_intent)
      
      // Fetch updated routes
      const routesRes = await fetch(`${BACKEND_URL}/api/routes`)
      const routesData = await routesRes.json()
      setRoutes(routesData)
    } catch (e) {
      console.error('Set intent error:', e)
    }
  }, [])

  const resetSimulation = useCallback(async () => {
    try {
      await fetch(`${BACKEND_URL}/api/reset`, { method: 'POST' })
      setPackets([])
      fetchData()
    } catch (e) {
      console.error('Reset error:', e)
    }
  }, [fetchData])

  return (
    <div className="min-h-screen bg-slate-900">
      <Header 
        connected={connected} 
        currentIntent={currentIntent}
        autoIntent={autoIntent}
        onSetIntent={setIntent}
        onResetSimulation={resetSimulation}
        autoPackets={autoPackets}
        onToggleAutoPackets={toggleAutoPackets}
      />
      <div className="container mx-auto px-4 py-6 max-w-full">
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          <div className="xl:col-span-3 space-y-6">
            <TopologyVisualization 
              switches={switches} 
              switchLinks={switchLinks} 
              gateways={gateways} 
              gatewayLinks={gatewayLinks}
              sensors={sensors}
              display={display}
              routes={routes} 
              packets={packets} 
              currentIntent={currentIntent}
              packetStats={packetStats}
              onUpdateSensor={updateSensorValue}
              onUpdateSwitchBattery={updateSwitchBattery}
            />
            <FailureControls 
              switches={switches} 
              switchLinks={switchLinks} 
              onToggleSwitch={toggleSwitch} 
              onToggleLink={toggleLink}
            />
          </div>
          <div className="space-y-6">
            <ControllerPanel 
              currentIntent={currentIntent}
              autoIntent={autoIntent}
              onSetIntent={setIntent}
              routes={routes} 
              gateways={gateways}
              packetStats={packetStats}
            />
            <GatewayPanel 
              gateways={gateways} 
              sensors={sensors}
              routes={routes}
            />
            <EventLog events={events} />
          </div>
        </div>
      </div>
    </div>
  )
}
