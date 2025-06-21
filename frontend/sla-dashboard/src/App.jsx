import React, { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { Switch } from './components/ui/switch';
import { Alert, AlertDescription } from './components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Progress } from './components/ui/progress';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Moon, 
  Sun, 
  Wifi, 
  WifiOff, 
  Zap,
  TrendingUp,
  TrendingDown,
  MapPin,
  Settings,
  Bell,
  BarChart3,
  Network,
  Shield,
  Radio,
  RefreshCw
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import './App.css';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/telemetry';

// Network nodes data with more realistic locations
const networkNodes = [
  { id: 'S1', name: 'Server Node 1', lat: 40.7128, lng: -74.0060, type: 'server', status: 'healthy' },
  { id: 'S2', name: 'Server Node 2', lat: 34.0522, lng: -118.2437, type: 'server', status: 'warning' },
  { id: 'R1', name: 'Router NYC', lat: 40.7589, lng: -73.9851, type: 'router', status: 'healthy' },
  { id: 'R2', name: 'Router LA', lat: 34.0928, lng: -118.3287, type: 'router', status: 'healthy' },
  { id: 'R3', name: 'Router Chicago', lat: 41.8781, lng: -87.6298, type: 'router', status: 'critical' },
  { id: 'R4', name: 'Router Dallas', lat: 32.7767, lng: -96.7970, type: 'router', status: 'healthy' },
  { id: 'R5', name: 'Router Miami', lat: 25.7617, lng: -80.1918, type: 'router', status: 'warning' },
  { id: 'R6', name: 'Router Seattle', lat: 47.6062, lng: -122.3321, type: 'router', status: 'healthy' },
  { id: 'E1', name: 'Edge Node Boston', lat: 42.3601, lng: -71.0589, type: 'edge', status: 'healthy' },
  { id: 'E2', name: 'Edge Node Denver', lat: 39.7392, lng: -104.9903, type: 'edge', status: 'healthy' },
  { id: 'E3', name: 'Edge Node Phoenix', lat: 33.4484, lng: -112.0740, type: 'edge', status: 'warning' },
  { id: 'E4', name: 'Edge Node Atlanta', lat: 33.7490, lng: -84.3880, type: 'edge', status: 'healthy' }
];

// Network connections
const networkConnections = [
  { from: 'S1', to: 'R1', risk: 0.2, latency: 5.2 },
  { from: 'S2', to: 'R2', risk: 0.8, latency: 12.1 },
  { from: 'R1', to: 'R3', risk: 0.9, latency: 15.3 },
  { from: 'R2', to: 'R4', risk: 0.3, latency: 7.8 },
  { from: 'R3', to: 'R4', risk: 0.6, latency: 9.2 },
  { from: 'R4', to: 'R5', risk: 0.4, latency: 6.5 },
  { from: 'R1', to: 'R6', risk: 0.2, latency: 4.8 },
  { from: 'R1', to: 'E1', risk: 0.1, latency: 3.2 },
  { from: 'R4', to: 'E2', risk: 0.3, latency: 5.9 },
  { from: 'R2', to: 'E3', risk: 0.7, latency: 11.4 },
  { from: 'R5', to: 'E4', risk: 0.5, latency: 8.1 }
];

// Sample telemetry data
const generateTelemetryData = () => {
  const data = [];
  const now = new Date();
  for (let i = 23; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 60 * 60 * 1000);
    data.push({
      time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      slaViolations: Math.floor(Math.random() * 20) + (i < 6 ? 15 : 5),
      anomalies: Math.floor(Math.random() * 8) + (i < 4 ? 8 : 2),
      latency: Math.random() * 10 + 5 + (i < 6 ? 5 : 0),
      throughput: Math.random() * 2 + 1.5,
      packetLoss: Math.random() * 2 + (i < 6 ? 3 : 0.5)
    });
  }
  return data;
};

function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [telemetryData, setTelemetryData] = useState(generateTelemetryData());
  const [realTimeData, setRealTimeData] = useState({
    activeSLAViolations: 12,
    activeAnomalies: 3,
    networkHealth: 78,
    avgLatency: 8.4,
    totalNodes: networkNodes.length,
    healthyNodes: networkNodes.filter(n => n.status === 'healthy').length
  });
  const [selectedNode, setSelectedNode] = useState(null);
  const [alertsEnabled, setAlertsEnabled] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [wsConnection, setWsConnection] = useState(null);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [isRetraining, setIsRetraining] = useState(false);

  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    try {
      const ws = new WebSocket(WS_URL);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setWsConnected(true);
        setWsConnection(ws);
      };
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setWsConnected(false);
        setWsConnection(null);
        
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsConnected(false);
      };
      
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setTimeout(connectWebSocket, 3000);
    }
  }, []);

  // Handle WebSocket messages
  const handleWebSocketMessage = (message) => {
    switch (message.type) {
      case 'telemetry_created':
        // Fetch updated telemetry data
        fetchLatestTelemetry();
        break;
      case 'prediction_stored':
        // Update real-time data with new prediction
        setRealTimeData(prev => ({
          ...prev,
          activeSLAViolations: message.data.sla_violation ? prev.activeSLAViolations + 1 : prev.activeSLAViolations,
          avgLatency: (prev.avgLatency + (message.data.sla_risk_score * 10)) / 2
        }));
        break;
      case 'sla_alert':
        if (alertsEnabled) {
          addAlert('SLA Violation', `High risk detected: ${(message.data.risk_score * 100).toFixed(1)}%`, 'error');
        }
        break;
      case 'anomaly_alert':
        if (alertsEnabled) {
          addAlert('Anomaly Detected', `Anomaly score: ${message.data.anomaly_score.toFixed(3)}`, 'warning');
        }
        break;
      case 'model_retrain_start':
        setIsRetraining(true);
        addAlert('Model Retraining', 'Automatic model retraining started', 'info');
        break;
      case 'model_retrain_complete':
        setIsRetraining(false);
        addAlert('Model Retraining', 'Model retraining completed successfully', 'success');
        break;
      default:
        console.log('Unknown message type:', message.type);
    }
  };

  // Add alert to recent alerts
  const addAlert = (title, message, type) => {
    const alert = {
      id: Date.now(),
      title,
      message,
      type,
      timestamp: new Date()
    };
    setRecentAlerts(prev => [alert, ...prev.slice(0, 4)]); // Keep only 5 recent alerts
  };

  // Fetch latest telemetry data from API
  const fetchLatestTelemetry = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/telemetry/?limit=24`);
      if (response.ok) {
        const data = await response.json();
        // Convert API data to chart format
        const chartData = data.map(item => ({
          time: new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          slaViolations: item.sla_violation ? 1 : 0,
          anomalies: item.anomaly_flag ? 1 : 0,
          latency: item.latency,
          throughput: item.throughput,
          packetLoss: item.packet_loss
        }));
        setTelemetryData(chartData);
      }
    } catch (error) {
      console.error('Failed to fetch telemetry data:', error);
    }
  };

  // Fetch real-time analytics
  const fetchAnalytics = async () => {
    try {
      const [highRiskResponse, anomaliesResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/analytics/high-risk`),
        fetch(`${API_BASE_URL}/analytics/anomalies`)
      ]);
      
      if (highRiskResponse.ok && anomaliesResponse.ok) {
        const highRiskData = await highRiskResponse.json();
        const anomaliesData = await anomaliesResponse.json();
        
        setRealTimeData(prev => ({
          ...prev,
          activeSLAViolations: highRiskData.length,
          activeAnomalies: anomaliesData.length
        }));
      }
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    }
  };

  // Send test telemetry data
  const sendTestTelemetry = async () => {
    try {
      const testData = {
        bandwidth: 2.0,
        throughput: Math.random() * 2 + 1.5,
        congestion: Math.random() * 0.5,
        packet_loss: Math.random() * 2,
        latency: Math.random() * 10 + 5,
        jitter: Math.random() * 1,
        percentage_video_occupancy: Math.random() * 100,
        bitrate_video: Math.random() * 1000,
        number_videos: Math.floor(Math.random() * 5)
      };
      
      const response = await fetch(`${API_BASE_URL}/predict-and-store/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(testData)
      });
      
      if (response.ok) {
        console.log('Test telemetry sent successfully');
      }
    } catch (error) {
      console.error('Failed to send test telemetry:', error);
    }
  };

  // Configure alerts
  const configureAlerts = async () => {
    try {
      const alertConfig = {
        alert_type: 'sla_violation',
        threshold: 0.8,
        channels: ['telegram', 'email']
      };
      
      const response = await fetch(`${API_BASE_URL}/alerts/configure`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(alertConfig)
      });
      
      if (response.ok) {
        addAlert('Alert Configuration', 'Alert settings updated successfully', 'success');
      }
    } catch (error) {
      console.error('Failed to configure alerts:', error);
    }
  };

  // Toggle dark mode
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Initialize WebSocket connection
  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (wsConnection) {
        wsConnection.close();
      }
    };
  }, [connectWebSocket]);

  // Simulate real-time updates and fetch data
  useEffect(() => {
    const interval = setInterval(() => {
      // Update local state
      setRealTimeData(prev => ({
        ...prev,
        networkHealth: Math.min(100, Math.max(0, prev.networkHealth + (Math.random() - 0.5) * 5)),
        avgLatency: Math.max(1, prev.avgLatency + (Math.random() - 0.5) * 2)
      }));

      // Update telemetry data
      setTelemetryData(prev => {
        const newData = [...prev.slice(1)];
        const now = new Date();
        newData.push({
          time: now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          slaViolations: Math.floor(Math.random() * 20) + 5,
          anomalies: Math.floor(Math.random() * 8) + 2,
          latency: Math.random() * 10 + 5,
          throughput: Math.random() * 2 + 1.5,
          packetLoss: Math.random() * 2 + 0.5
        });
        return newData;
      });

      // Fetch real data from API
      fetchAnalytics();
      
      // Occasionally send test data
      if (Math.random() > 0.7) {
        sendTestTelemetry();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getNodeIcon = (node) => {
    const baseClasses = "w-4 h-4";
    switch (node.type) {
      case 'server': return <Shield className={baseClasses} />;
      case 'router': return <Network className={baseClasses} />;
      case 'edge': return <Wifi className={baseClasses} />;
      default: return <MapPin className={baseClasses} />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-500';
      case 'warning': return 'text-yellow-500';
      case 'critical': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getRiskColor = (risk) => {
    if (risk < 0.3) return '#22c55e'; // green
    if (risk < 0.7) return '#eab308'; // yellow
    return '#ef4444'; // red
  };

  const getConnectionPath = (connection) => {
    const fromNode = networkNodes.find(n => n.id === connection.from);
    const toNode = networkNodes.find(n => n.id === connection.to);
    if (!fromNode || !toNode) return [];
    return [[fromNode.lat, fromNode.lng], [toNode.lat, toNode.lng]];
  };

  const getAlertColor = (type) => {
    switch (type) {
      case 'error': return 'border-red-500 bg-red-50 dark:bg-red-950';
      case 'warning': return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950';
      case 'success': return 'border-green-500 bg-green-50 dark:bg-green-950';
      case 'info': return 'border-blue-500 bg-blue-50 dark:bg-blue-950';
      default: return 'border-gray-500 bg-gray-50 dark:bg-gray-950';
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Activity className="w-8 h-8 text-primary" />
                <h1 className="text-2xl font-bold">SLA Monitor</h1>
              </div>
              <Badge variant={realTimeData.networkHealth > 80 ? "default" : realTimeData.networkHealth > 60 ? "secondary" : "destructive"}>
                {realTimeData.networkHealth > 80 ? 'Healthy' : realTimeData.networkHealth > 60 ? 'Warning' : 'Critical'}
              </Badge>
              <div className="flex items-center space-x-2">
                {wsConnected ? (
                  <Radio className="w-4 h-4 text-green-500" />
                ) : (
                  <WifiOff className="w-4 h-4 text-red-500" />
                )}
                <span className="text-sm text-muted-foreground">
                  {wsConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              {isRetraining && (
                <div className="flex items-center space-x-2">
                  <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
                  <span className="text-sm text-blue-500">Retraining...</span>
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Bell className="w-4 h-4" />
                <Switch 
                  checked={alertsEnabled} 
                  onCheckedChange={setAlertsEnabled}
                />
                <span className="text-sm">Alerts</span>
              </div>
              
              <div className="flex items-center space-x-2">
                <Sun className="w-4 h-4" />
                <Switch 
                  checked={darkMode} 
                  onCheckedChange={setDarkMode}
                />
                <Moon className="w-4 h-4" />
              </div>
              
              <Button variant="outline" size="sm" onClick={configureAlerts}>
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6 space-y-6">
        {/* Recent Alerts */}
        {recentAlerts.length > 0 && (
          <div className="space-y-2">
            {recentAlerts.slice(0, 3).map((alert) => (
              <Alert key={alert.id} className={getAlertColor(alert.type)}>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  <strong>{alert.title}:</strong> {alert.message}
                  <span className="text-xs text-muted-foreground ml-2">
                    {alert.timestamp.toLocaleTimeString()}
                  </span>
                </AlertDescription>
              </Alert>
            ))}
          </div>
        )}

        {/* High SLA Violation Alert */}
        {realTimeData.activeSLAViolations > 10 && alertsEnabled && (
          <Alert className="border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              High SLA violation activity detected! {realTimeData.activeSLAViolations} active violations.
            </AlertDescription>
          </Alert>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">SLA Violations</CardTitle>
              <AlertTriangle className="h-4 w-4 text-destructive" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-destructive">{realTimeData.activeSLAViolations}</div>
              <p className="text-xs text-muted-foreground">
                <TrendingUp className="inline w-3 h-3 mr-1" />
                +2 from last hour
              </p>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Anomalies</CardTitle>
              <Zap className="h-4 w-4 text-yellow-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-500">{realTimeData.activeAnomalies}</div>
              <p className="text-xs text-muted-foreground">
                <TrendingDown className="inline w-3 h-3 mr-1" />
                -1 from last hour
              </p>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Network Health</CardTitle>
              <Activity className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-500">{realTimeData.networkHealth.toFixed(0)}%</div>
              <Progress value={realTimeData.networkHealth} className="mt-2" />
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
              <BarChart3 className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-500">{realTimeData.avgLatency.toFixed(1)}ms</div>
              <p className="text-xs text-muted-foreground">
                Target: &lt;10ms
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Main Dashboard */}
        <Tabs defaultValue="map" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="map">Network Map</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="nodes">Node Status</TabsTrigger>
          </TabsList>

          <TabsContent value="map" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Real-time Network Topology</CardTitle>
                <CardDescription>
                  Interactive map showing network nodes and connection health. 
                  Lines are color-coded by risk level: Green (Low), Yellow (Medium), Red (High).
                  {wsConnected && <span className="text-green-500 ml-2">● Live Updates Active</span>}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[600px] rounded-lg overflow-hidden border">
                  <MapContainer
                    center={[39.8283, -98.5795]} // Center of USA
                    zoom={4}
                    style={{ height: '100%', width: '100%' }}
                    className="z-0"
                  >
                    <TileLayer
                      url={darkMode 
                        ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                        : "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      }
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    />
                    
                    {/* Network Connections */}
                    {networkConnections.map((connection, index) => (
                      <Polyline
                        key={index}
                        positions={getConnectionPath(connection)}
                        color={getRiskColor(connection.risk)}
                        weight={4}
                        opacity={0.8}
                      />
                    ))}
                    
                    {/* Network Nodes */}
                    {networkNodes.map((node) => (
                      <Marker
                        key={node.id}
                        position={[node.lat, node.lng]}
                        eventHandlers={{
                          click: () => setSelectedNode(node)
                        }}
                      >
                        <Popup>
                          <div className="p-2">
                            <div className="flex items-center space-x-2 mb-2">
                              {getNodeIcon(node)}
                              <h3 className="font-semibold">{node.name}</h3>
                            </div>
                            <div className="space-y-1 text-sm">
                              <p>Type: <span className="capitalize">{node.type}</span></p>
                              <p>Status: <span className={getStatusColor(node.status)}>{node.status}</span></p>
                              <p>ID: {node.id}</p>
                            </div>
                          </div>
                        </Popup>
                      </Marker>
                    ))}
                  </MapContainer>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>SLA Violations & Anomalies</CardTitle>
                  <CardDescription>24-hour trend analysis</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={telemetryData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <Tooltip />
                      <Line 
                        type="monotone" 
                        dataKey="slaViolations" 
                        stroke="#ef4444" 
                        strokeWidth={2}
                        name="SLA Violations"
                      />
                      <Line 
                        type="monotone" 
                        dataKey="anomalies" 
                        stroke="#eab308" 
                        strokeWidth={2}
                        name="Anomalies"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Network Performance</CardTitle>
                  <CardDescription>Latency and throughput metrics</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={telemetryData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <Tooltip />
                      <Area 
                        type="monotone" 
                        dataKey="latency" 
                        stackId="1"
                        stroke="#3b82f6" 
                        fill="#3b82f6"
                        fillOpacity={0.6}
                        name="Latency (ms)"
                      />
                      <Area 
                        type="monotone" 
                        dataKey="throughput" 
                        stackId="2"
                        stroke="#10b981" 
                        fill="#10b981"
                        fillOpacity={0.6}
                        name="Throughput (Mbps)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="nodes" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Node Status Overview</CardTitle>
                <CardDescription>
                  {realTimeData.healthyNodes} of {realTimeData.totalNodes} nodes are healthy
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {networkNodes.map((node) => (
                    <Card key={node.id} className="hover:shadow-md transition-shadow cursor-pointer"
                          onClick={() => setSelectedNode(node)}>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            {getNodeIcon(node)}
                            <span className="font-medium">{node.name}</span>
                          </div>
                          <Badge variant={node.status === 'healthy' ? 'default' : 
                                        node.status === 'warning' ? 'secondary' : 'destructive'}>
                            {node.status}
                          </Badge>
                        </div>
                        <div className="text-sm text-muted-foreground space-y-1">
                          <p>Type: <span className="capitalize">{node.type}</span></p>
                          <p>Location: {node.lat.toFixed(4)}, {node.lng.toFixed(4)}</p>
                          <p>ID: {node.id}</p>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

export default App;

