import { useState, useEffect, useCallback, useRef } from 'react'
import Header from './components/Header'
import TopologyVisualization from './components/TopologyVisualization'
import GatewayPanel from './components/GatewayPanel'
import ControllerPanel from './components/ControllerPanel'
import FailureControls from './components/FailureControls'
import EventLog from './components/EventLog'

const BACKEND_URL = 'http://localhost:5000'
const POLL_INTERVAL = 1500  // Poll every 1.5 seconds for updates

export default function App() {
  const [sensors, setSensors] = useState({})
  const [gateways, setGateways] = useState({})
  const [switches, setSwitches] = useState({})
  const [switchLinks, setSwitchLinks] = useState([])
  const [gatewayLinks, setGatewayLinks] = useState([])
  const [display, setDisplay] = useState(null)
  const [routes, setRoutes] = useState({})
  const [currentIntent, setCurrentIntent] = useState('balanced')
  const [events, setEvents] = useState([])
  const [packets, setPackets] = useState([])
  const [packetStats, setPacketStats] = useState({ forwarded: 0, dropped: 0, total: 0 })
  const [connected, setConnected] = useState(false)
  const [autoPackets, setAutoPackets] = useState(true)
  
  const updateTimeoutRef = useRef({})
  const pollRef = useRef(null)

  // Fetch all data from backend
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
      setEvents(eventsData || [])
      setPacketStats(statsData || { forwarded: 0, dropped: 0, total: 0 })
      setConnected(true)
    } catch (e) {
      console.error('Fetch error:', e)
      setConnected(false)
    }
  }, [])

  // Initial fetch and polling
  useEffect(() => {
    // Initial fetch
    fetchData()
    
    // Set up polling for real-time updates
    pollRef.current = setInterval(fetchData, POLL_INTERVAL)
    
    // Cleanup
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
      Object.values(updateTimeoutRef.current).forEach(clearTimeout)
    }
  }, [fetchData])

  // Clean up old packets
  useEffect(() => {
    const packetCleanup = setInterval(() => {
      setPackets(prev => prev.filter(p => Date.now() - p.timestamp < 3000))
    }, 500)
    return () => clearInterval(packetCleanup)
  }, [])

  // Debounced sensor update for responsive sliders
  const updateSensorValue = useCallback((sensorId, value) => {
    // Update local state immediately for responsiveness
    setSensors(prev => ({
      ...prev,
      [sensorId]: { ...prev[sensorId], value: parseInt(value) }
    }))

    if (updateTimeoutRef.current[sensorId]) {
      clearTimeout(updateTimeoutRef.current[sensorId])
    }

    updateTimeoutRef.current[sensorId] = setTimeout(async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/sensors/${sensorId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ value: parseInt(value) })
        })
        const data = await res.json()
        setSensors(prev => ({ ...prev, [sensorId]: data }))
        // Trigger immediate refresh
        fetchData()
      } catch (e) {
        console.error('Update sensor error:', e)
      }
    }, 100)
  }, [fetchData])

  const toggleSwitch = useCallback(async (switchId, action) => {
    try {
      const endpoint = action === 'fail' 
        ? `${BACKEND_URL}/api/switches/${switchId}/fail` 
        : `${BACKEND_URL}/api/switches/${switchId}/restore`
      await fetch(endpoint, { method: 'POST' })
      // Trigger immediate refresh
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
      // Trigger immediate refresh
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

  const resetSimulation = useCallback(async () => {
    try {
      await fetch(`${BACKEND_URL}/api/reset`, { method: 'POST' })
      setPackets([])
      // Trigger immediate refresh
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
        onResetSimulation={resetSimulation}
        autoPackets={autoPackets}
        onToggleAutoPackets={toggleAutoPackets}
      />
      <div className="container mx-auto px-4 py-6 max-w-full">
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          {/* Main topology area - wider */}
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
            />
            <FailureControls 
              switches={switches} 
              switchLinks={switchLinks} 
              onToggleSwitch={toggleSwitch} 
              onToggleLink={toggleLink}
            />
          </div>
          {/* Side panel - narrower */}
          <div className="space-y-6">
            <ControllerPanel 
              currentIntent={currentIntent} 
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
