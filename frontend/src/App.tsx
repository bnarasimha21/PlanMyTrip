import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
// @ts-ignore annyang has imperfect types
import annyang from 'annyang';

const API_BASE = (import.meta as any).env.VITE_API_BASE || 'http://localhost:8000';
const MAPBOX_TOKEN = (import.meta as any).env.VITE_MAPBOX_TOKEN || '';

mapboxgl.accessToken = MAPBOX_TOKEN;

interface Place {
  name: string;
  neighborhood?: string;
  category?: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  notes?: string;
}

export default function App() {
  const [tripRequest, setTripRequest] = useState('Plan a 1-day must see places in Bangalore');
  const [extracted, setExtracted] = useState<{ city: string; interests: string; days: number } | null>(null);
  const [places, setPlaces] = useState<Place[]>([]);
  const [status, setStatus] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [modifyInput, setModifyInput] = useState('');
  const [isExtractedCollapsed, setIsExtractedCollapsed] = useState(true);
  const [chatMessages, setChatMessages] = useState<Array<{type: 'user' | 'bot', message: string, timestamp: Date}>>([]);
  const chatMessagesEndRef = useRef<HTMLDivElement>(null);
  const [chatInput, setChatInput] = useState('');
  const [isChatListening, setIsChatListening] = useState(false);
  const [hasGeneratedItinerary, setHasGeneratedItinerary] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const [animationRoute, setAnimationRoute] = useState<number[][]>([]);

  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const carMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const animationIdRef = useRef<number | null>(null);

  // Init Map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;
    if (!MAPBOX_TOKEN || MAPBOX_TOKEN === 'your_mapbox_token_here') {
      setStatus('Please set a valid VITE_MAPBOX_TOKEN in frontend/.env file');
      return;
    }
    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: 'mapbox://styles/mapbox/navigation-night-v1',
      center: [77.5946, 12.9716],
      zoom: 11,
    });
    mapRef.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
  }, []);

  // Render markers
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;


    // Remove any existing markers
    (window as any).__markers?.forEach((m: mapboxgl.Marker) => m.remove());

    const markers: mapboxgl.Marker[] = [];
    if (places.length > 0) {
      // Calculate bounds to fit all markers
      const validPlaces = places.filter(p => p.latitude != null && p.longitude != null);
      if (validPlaces.length > 0) {
        const lats = validPlaces.map(p => p.latitude!);
        const lons = validPlaces.map(p => p.longitude!);
        
        const minLat = Math.min(...lats);
        const maxLat = Math.max(...lats);
        const minLon = Math.min(...lons);
        const maxLon = Math.max(...lons);
        
        // Create bounds with padding
        const bounds = new mapboxgl.LngLatBounds([minLon, minLat], [maxLon, maxLat]);
        
        // Fit map to bounds with padding
        map.fitBounds(bounds, {
          padding: { top: 50, bottom: 50, left: 50, right: 50 },
          maxZoom: 15 // Prevent zooming in too much for close markers
        });
      }
    }

    places.forEach((p) => {
      if (p.latitude == null || p.longitude == null) return;
      const cat = (p.category || '').toLowerCase();
      // More prominent icons with bright colors that contrast with dark map
      const FOOD_ICON = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="%23FF6B35" stroke="%23FFFFFF" stroke-width="2"/><path d="M8 6c.414 0 .75.336.75.75V12h.5V6.75a.75.75 0 011.5 0V12h.5V6.75a.75.75 0 011.5 0V13a2 2 0 01-2 2h-1a2 2 0 01-2-2V6.75c0-.414.336-.75.75-.75zM15 6a.75.75 0 01.75.75V12h1.25a.75.75 0 010 1.5H15.75V19a.75.75 0 01-1.5 0V6.75c0-.414.336-.75.75-.75z" fill="white"/></svg>';
      const ART_ICON = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="%23FF1493" stroke="%23FFFFFF" stroke-width="2"/><path d="M12 6c3.866 0 7 2.582 7 5.769 0 1.279-1.037 2.231-2.24 2.231h-1.042c-.666 0-1.074.706-.766 1.298.196.377.048.84-.327 1.051A4.5 4.5 0 0112 17.5C8.134 17.5 5 14.918 5 11.731 5 8.582 8.134 6 12 6zm-3.75 5.25a.75.75 0 100-1.5.75.75 0 000 1.5zm3-1.5a.75.75 0 100-1.5.75.75 0 000 1.5zm3 1.5a.75.75 0 100-1.5.75.75 0 000 1.5z" fill="white"/></svg>';
      const SIGHTSEEING_ICON = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="%237C3AED" stroke="%23FFFFFF" stroke-width="2"/><path d="M6 20h12v-2H6v2zm6-16L8 8v4h8V8l-4-4zm-1 6V8.5l1-1 1 1V10h-2z" fill="white"/><rect x="10" y="14" width="4" height="2" fill="white"/><circle cx="12" cy="6" r="1" fill="white"/></svg>';
      const DEFAULT_ICON = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="%2300CED1" stroke="%23FFFFFF" stroke-width="2"/><path d="M12 8l4 8H8l4-8z" fill="white"/></svg>';
      const img = document.createElement('img');
      img.src = cat.includes('food') ? FOOD_ICON : 
                cat.includes('art') ? ART_ICON : 
                (cat.includes('sight') || cat.includes('culture') || cat.includes('temple') || cat.includes('monument') || cat.includes('landmark') || cat.includes('tourist')) ? SIGHTSEEING_ICON : 
                DEFAULT_ICON;
      img.style.width = '48px';
      img.style.height = '48px';
      img.style.filter = 'drop-shadow(0 4px 8px rgba(0,0,0,0.6))';
      img.style.borderRadius = '50%';
      img.style.cursor = 'pointer';
      img.style.transition = 'filter 0.2s ease';
      // Use filter brightness instead of transform to avoid position issues
      img.addEventListener('mouseenter', () => {
        img.style.filter = 'drop-shadow(0 4px 8px rgba(0,0,0,0.6)) brightness(1.2)';
      });
      img.addEventListener('mouseleave', () => {
        img.style.filter = 'drop-shadow(0 4px 8px rgba(0,0,0,0.6))';
      });
      const marker = new mapboxgl.Marker({ element: img, anchor: 'bottom' })
        .setLngLat([p.longitude!, p.latitude!])
        .setPopup(new mapboxgl.Popup({ offset: 16 }).setHTML(`
          <div class="p-3">
            <h3 class="font-semibold text-gray-900 mb-1">${p.name}</h3>
            <p class="text-sm text-gray-600 mb-2">${p.neighborhood || ''}</p>
            <p class="text-xs text-gray-500">${p.notes || ''}</p>
          </div>
        `))
        .addTo(map);
      markers.push(marker);
    });

    (window as any).__markers = markers;
  }, [places]);


  // Function to interpolate points between coordinates for smoother animation
  const interpolateRoute = (coordinates: number[][]): number[][] => {
    const interpolated: number[][] = [];
    const pointsPerSegment = 20; // Number of points between each pair of coordinates
    
    for (let i = 0; i < coordinates.length - 1; i++) {
      const start = coordinates[i];
      const end = coordinates[i + 1];
      
      for (let j = 0; j <= pointsPerSegment; j++) {
        const ratio = j / pointsPerSegment;
        const lat = start[1] + (end[1] - start[1]) * ratio;
        const lng = start[0] + (end[0] - start[0]) * ratio;
        interpolated.push([lng, lat]);
      }
    }
    
    return interpolated;
  };

  // Function to get route using Mapbox Directions API
  const getRoute = async (coordinates: number[][]) => {
    if (!MAPBOX_TOKEN || coordinates.length < 2) {
      console.log('Skipping route API call:', { token: !!MAPBOX_TOKEN, coordCount: coordinates.length });
      return null;
    }
    
    const coordString = coordinates.map(coord => `${coord[0]},${coord[1]}`).join(';');
    const url = `https://api.mapbox.com/directions/v5/mapbox/driving/${coordString}?geometries=geojson&access_token=${MAPBOX_TOKEN}`;
    
    console.log('Fetching route from:', url);
    
    try {
      const response = await fetch(url);
      const data = await response.json();
      console.log('Route API response:', data);
      return data.routes[0]?.geometry?.coordinates || null;
    } catch (error) {
      console.error('Error fetching route:', error);
      return null;
    }
  };

  // Function to create and animate car
  const startRouteAnimation = async () => {
    const map = mapRef.current;
    if (!map || places.length < 2) {
      console.log('Cannot start animation: map missing or not enough places', { map: !!map, placesCount: places.length });
      return;
    }

    console.log('Starting route animation with', places.length, 'places');
    setIsAnimating(true);
    
    // Get coordinates of all places
    const coordinates = places
      .filter(p => p.latitude != null && p.longitude != null)
      .map(p => [p.longitude!, p.latitude!]);
    
    if (coordinates.length < 2) {
      console.log('Not enough valid coordinates for animation:', coordinates.length);
      setIsAnimating(false);
      return;
    }

    console.log('Using coordinates:', coordinates);

    // Get the route
    const routeCoords = await getRoute(coordinates);
    let finalRoute = routeCoords || coordinates;
    
    // If we only have the basic coordinates (not a detailed route), interpolate more points
    if (!routeCoords && coordinates.length >= 2) {
      finalRoute = interpolateRoute(coordinates);
    }
    
    setAnimationRoute(finalRoute);
    
    console.log('Route calculated:', { routeCoords: !!routeCoords, finalRouteLength: finalRoute.length });

    // Add route line to map
    if (map.getSource('route')) {
      map.removeLayer('route-line');
      map.removeSource('route');
    }

    map.addSource('route', {
      type: 'geojson',
      data: {
        type: 'Feature',
        properties: {},
        geometry: {
          type: 'LineString',
          coordinates: finalRoute
        }
      }
    });

    map.addLayer({
      id: 'route-line',
      type: 'line',
      source: 'route',
      layout: {
        'line-join': 'round',
        'line-cap': 'round'
      },
      paint: {
        'line-color': '#00FF88',
        'line-width': 4,
        'line-opacity': 0.8
      }
    });

    // Create car icon
    const carIcon = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><defs><linearGradient id="carGrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:%2300FF88;stop-opacity:1" /><stop offset="100%" style="stop-color:%2300CC6A;stop-opacity:1" /></linearGradient></defs><ellipse cx="16" cy="26" rx="14" ry="4" fill="rgba(0,0,0,0.2)"/><rect x="6" y="12" width="20" height="12" rx="2" fill="url(%23carGrad)" stroke="%23FFFFFF" stroke-width="1.5"/><rect x="8" y="8" width="16" height="6" rx="3" fill="url(%23carGrad)" stroke="%23FFFFFF" stroke-width="1.5"/><circle cx="10" cy="22" r="2.5" fill="%23333" stroke="%23FFF" stroke-width="1"/><circle cx="22" cy="22" r="2.5" fill="%23333" stroke="%23FFF" stroke-width="1"/><rect x="9" y="14" width="3" height="2" rx="1" fill="rgba(255,255,255,0.8)"/><rect x="13" y="14" width="3" height="2" rx="1" fill="rgba(255,255,255,0.8)"/><rect x="17" y="14" width="3" height="2" rx="1" fill="rgba(255,255,255,0.8)"/><polygon points="16,4 18,8 14,8" fill="%23FFD700" stroke="%23FFF" stroke-width="1"/></svg>';
    
    const carElement = document.createElement('img');
    carElement.src = carIcon;
    carElement.style.width = '40px';
    carElement.style.height = '40px';
    carElement.style.filter = 'drop-shadow(0 4px 8px rgba(0,255,136,0.4))';
    carElement.style.borderRadius = '50%';
    carElement.style.zIndex = '1000';

    // Remove existing car marker
    if (carMarkerRef.current) {
      carMarkerRef.current.remove();
    }

    // Create new car marker
    const carMarker = new mapboxgl.Marker({
      element: carElement,
      anchor: 'center'
    }).setLngLat(finalRoute[0]).addTo(map);
    
    carMarkerRef.current = carMarker;
    console.log('Car marker created at:', finalRoute[0]);

    // Animate car along route
    console.log('Starting car animation with route length:', finalRoute.length);
    animateCarAlongRoute(finalRoute, carMarker);
  };

  // Function to animate car movement
  const animateCarAlongRoute = (route: number[][], carMarker: mapboxgl.Marker) => {
    let currentIndex = 0;
    const speed = 200; // Animation speed (lower = faster)
    let animating = true;
    
    const animate = () => {
      if (!animating || currentIndex >= route.length - 1) {
        setIsAnimating(false);
        return;
      }

      const current = route[currentIndex];
      const next = route[currentIndex + 1];
      
      if (!current || !next) {
        setIsAnimating(false);
        return;
      }

      // Calculate bearing for car rotation
      const bearing = calculateBearing(current, next);
      
      // Update car position
      carMarker.setLngLat([current[0], current[1]]);
      
      // Rotate car element
      const carElement = carMarker.getElement();
      carElement.style.transform = `rotate(${bearing}deg)`;

      currentIndex++;
      
      // Store animation state in ref to allow stopping
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
      
      animationIdRef.current = requestAnimationFrame(() => {
        setTimeout(() => {
          if (animating) animate();
        }, speed);
      });
    };

    // Stop function for this animation
    const stopAnimation = () => {
      animating = false;
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
    };

    // Store stop function
    (carMarker as any).__stopAnimation = stopAnimation;

    animate();
  };

  // Helper function to calculate bearing between two points
  const calculateBearing = (start: number[], end: number[]): number => {
    const startLat = start[1] * Math.PI / 180;
    const startLon = start[0] * Math.PI / 180;
    const endLat = end[1] * Math.PI / 180;
    const endLon = end[0] * Math.PI / 180;

    const dLon = endLon - startLon;
    const y = Math.sin(dLon) * Math.cos(endLat);
    const x = Math.cos(startLat) * Math.sin(endLat) - Math.sin(startLat) * Math.cos(endLat) * Math.cos(dLon);

    const bearing = Math.atan2(y, x) * 180 / Math.PI;
    return (bearing + 360) % 360;
  };

  // Function to stop animation
  const stopRouteAnimation = () => {
    setIsAnimating(false);
    if (animationIdRef.current) {
      cancelAnimationFrame(animationIdRef.current);
    }
    if (carMarkerRef.current) {
      // Call the marker's stop function if it exists
      if ((carMarkerRef.current as any).__stopAnimation) {
        (carMarkerRef.current as any).__stopAnimation();
      }
      carMarkerRef.current.remove();
      carMarkerRef.current = null;
    }
    
    // Remove route line from map
    const map = mapRef.current;
    if (map && map.getSource('route')) {
      map.removeLayer('route-line');
      map.removeSource('route');
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRouteAnimation();
    };
  }, []);

  // Resize map when sidebar appears/disappears
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    
    // Delay resize to allow DOM to update
    const resizeTimeout = setTimeout(() => {
      map.resize();
    }, 100);
    
    return () => clearTimeout(resizeTimeout);
  }, [hasGeneratedItinerary, places.length > 0]);

  // Auto-scroll chatbot to bottom when new messages appear
  useEffect(() => {
    if (chatMessagesEndRef.current) {
      chatMessagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages]);

  // Mic integration
  const startListening = () => {
    if (!annyang) return setStatus('Speech not supported');
    setIsListening(true);
    setStatus('Listening...');
    annyang.setLanguage('en-US');
    annyang.removeCommands();
    annyang.addCallback('result', (phrases: string[]) => {
      if (phrases && phrases.length) {
        setTripRequest(phrases[0]);
        setStatus('');
        setIsListening(false);
        try { annyang.abort(); } catch {}
      }
    });
    annyang.addCallback('end', () => {
      setStatus('');
      setIsListening(false);
    });
    try { annyang.start({ autoRestart: false, continuous: false }); } catch { 
      setStatus('Mic error');
      setIsListening(false);
    }
  };

  const doExtract = async () => {
    setStatus('Extracting details...');
    try {
      const resp = await fetch(`${API_BASE}/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: tripRequest }),
      });
      const data = await resp.json();
      setExtracted(data);
      setStatus('');
    } catch (error) {
      setStatus('Error extracting details');
    }
  };

  const doItinerary = async () => {
    if (!API_BASE) {
      setStatus('Set VITE_API_BASE in frontend/.env');
      return;
    }
    setStatus('Generating itinerary...');
    try {
      const req = extracted || (await (await fetch(`${API_BASE}/extract`, { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify({ text: tripRequest }) 
      })).json());
      const resp = await fetch(`${API_BASE}/itinerary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ city: req.city, interests: req.interests, days: req.days }),
      });
      const data = await resp.json();
      setPlaces(data.places || []);
      setHasGeneratedItinerary(true);
      setStatus('');
    } catch (error) {
      setStatus('Error generating itinerary');
    }
  };

  const startChatListening = () => {
    if (!annyang) return setStatus('Speech not supported');
    setIsChatListening(true);
    setStatus('Listening...');
    annyang.setLanguage('en-US');
    annyang.removeCommands();
    annyang.addCallback('result', (phrases: string[]) => {
      if (phrases && phrases.length) {
        setChatInput(phrases[0]);
        setStatus('');
        setIsChatListening(false);
        try { annyang.abort(); } catch {}
      }
    });
    annyang.addCallback('end', () => {
      setIsChatListening(false);
      setStatus('');
    });
    try { annyang.start({ autoRestart: false, continuous: false }); } catch { setStatus('Mic error'); setIsChatListening(false); }
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim() || !extracted) return;
    
    const userMessage = { type: 'user' as const, message: chatInput, timestamp: new Date() };
    setChatMessages(prev => [...prev, userMessage]);
    
    const currentInput = chatInput;
    setChatInput('');
    setStatus('Processing...');
    
    try {
      if (!API_BASE) {
        setStatus('Set VITE_API_BASE in frontend/.env');
        return;
      }
      
      const resp = await fetch(`${API_BASE}/modify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          city: extracted.city, 
          interests: extracted.interests, 
          days: extracted.days, 
          places, 
          instruction: currentInput 
        }),
      });
      const data = await resp.json();
      
      // Handle different response types appropriately
      if (data.type === 'modification') {
        // For modifications, always update places (even if empty - user might have removed all)
        setPlaces(data.places || []);
      } else if (data.type === 'answer') {
        // For questions, preserve existing places since we're just answering
        // Don't update places for question-type responses
      } else {
        // Fallback: only update if we have valid places data
        if (data.places && Array.isArray(data.places) && data.places.length > 0) {
          setPlaces(data.places);
        }
      }
      
      const botMessage = { 
        type: 'bot' as const, 
        message: data.response || "I've processed your request.", 
        timestamp: new Date() 
      };
      setChatMessages(prev => [...prev, botMessage]);
      setStatus('');
    } catch (error) {
      const errorMessage = { 
        type: 'bot' as const, 
        message: 'Sorry, I encountered an error while processing your request. Please try again.', 
        timestamp: new Date() 
      };
      setChatMessages(prev => [...prev, errorMessage]);
      setStatus('Error processing request');
    }
  };

  const doModify = async () => {
    if (!extracted) return;
    if (!API_BASE) {
      setStatus('Set VITE_API_BASE in frontend/.env');
      return;
    }
    setStatus('Applying changes...');
    try {
      const resp = await fetch(`${API_BASE}/modify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ city: extracted.city, interests: extracted.interests, days: extracted.days, places, instruction: modifyInput }),
      });
      const data = await resp.json();
      setPlaces(data.places || places);
      setStatus('');
      setModifyInput('');
    } catch (error) {
      setStatus('Error applying changes');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 text-white">
      {/* Header */}
      <div className="bg-black/30 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text text-transparent">
            ✈️ Let Me Plan My Trip
          </h1>
          <p className="text-sm text-gray-300 mt-1">AI-powered travel planning with interactive maps</p>
        </div>
      </div>

            <div className="flex h-[calc(100vh-80px)]">
              {/* Sidebar */}
              <div className="w-[520px] bg-black/30 backdrop-blur-xl border-r border-white/10 overflow-y-auto">
          <div className="p-6 space-y-6">
            {/* Trip Request Section with Voice Input */}
            <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <span className="w-8 h-8 bg-gradient-to-r from-slate-600 to-gray-600 rounded-full flex items-center justify-center text-sm">✍️</span>
                  Trip Request
                </h3>
                <button
                  onClick={startListening}
                  disabled={isListening}
                  className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${
                    isListening
                      ? 'bg-red-600 hover:bg-red-700 animate-pulse text-white'
                      : 'bg-emerald-600 hover:bg-emerald-700 text-white hover:scale-110'
                  } disabled:opacity-50`}
                  title={isListening ? 'Listening...' : 'Start Speaking'}
                >
                  🎤
                </button>
              </div>
              
              <textarea
                value={tripRequest}
                onChange={(e) => setTripRequest(e.target.value)}
                rows={2}
                className="w-full bg-white/10 border border-white/20 rounded-xl p-4 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none"
                placeholder="Describe your dream trip... e.g., 'Plan a 3-day art and food tour in Paris'"
              />

            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button 
                onClick={doExtract}
                className={`py-3 px-4 bg-gradient-to-r from-slate-600 to-gray-600 hover:from-slate-700 hover:to-gray-700 rounded-xl font-medium transition-all duration-200 transform hover:scale-105 ${
                  extracted ? 'flex-1' : 'w-full'
                }`}
              >
                🔍 Get Details
              </button>
              {extracted && (
                <button 
                  onClick={doItinerary}
                  className="flex-1 py-3 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 rounded-xl font-medium transition-all duration-200 transform hover:scale-105"
                >
                  🗺️ Generate Itinerary
                </button>
              )}
            </div>

            {/* Extracted Details - Collapsible */}
            {extracted && (
              <div className="bg-gradient-to-r from-emerald-500/10 to-teal-500/10 rounded-2xl border border-emerald-500/20">
                <button
                  onClick={() => setIsExtractedCollapsed(!isExtractedCollapsed)}
                  className="w-full p-6 text-left hover:bg-emerald-500/5 transition-colors duration-200 rounded-2xl"
                >
                  <h3 className="text-lg font-semibold flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="w-8 h-8 bg-gradient-to-r from-emerald-600 to-teal-600 rounded-full flex items-center justify-center text-sm">✅</span>
                      Trip Details
                    </div>
                    <span className={`transform transition-transform duration-200 ${isExtractedCollapsed ? '' : 'rotate-180'}`}>
                      ⌄
                    </span>
                  </h3>
                </button>
                
                {!isExtractedCollapsed && (
                  <div className="px-6 pb-6">
                    <div className="bg-white/5 rounded-xl p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 bg-blue-500/20 rounded-full flex items-center justify-center text-xs">🏙️</span>
                          <span className="text-gray-300 font-medium">Destination:</span>
                        </div>
                        <span className="font-semibold text-emerald-300 bg-emerald-500/20 px-3 py-1 rounded-lg">{extracted.city}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 bg-purple-500/20 rounded-full flex items-center justify-center text-xs">🎯</span>
                          <span className="text-gray-300 font-medium">Interests:</span>
                        </div>
                        <span className="font-semibold text-purple-300 bg-purple-500/20 px-3 py-1 rounded-lg">{extracted.interests}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 bg-amber-500/20 rounded-full flex items-center justify-center text-xs">📅</span>
                          <span className="text-gray-300 font-medium">Duration:</span>
                        </div>
                        <span className="font-semibold text-amber-300 bg-amber-500/20 px-3 py-1 rounded-lg">
                          {extracted.days} {extracted.days === 1 ? 'Day' : 'Days'}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Itinerary Generation Status */}
            {status && (status.includes('Generating') || status.includes('Extracting')) && (
              <div className="bg-blue-500/10 rounded-2xl p-4 border border-blue-500/20">
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                  <p className="text-sm text-blue-200">{status}</p>
                </div>
              </div>
            )}

            {/* AI Itinerary Assistant Chatbot */}
            {hasGeneratedItinerary && (
              <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full flex items-center justify-center text-sm">🤖</span>
                  AI Itinerary Assistant
                </h3>

                {/* Chat Messages */}
                <div className="bg-white/10 rounded-xl p-4 h-80 overflow-y-auto mb-4 border border-white/20 scrollbar-hide">
                  {chatMessages.length === 0 ? (
                    <div className="text-center text-gray-400 py-8">
                      <div className="w-12 h-12 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full flex items-center justify-center mx-auto mb-3">
                        💬
                      </div>
                      <p className="text-sm">Ask me anything about your itinerary!</p>
                      <p className="text-xs mt-1">Try: "Add a coffee shop" or "What's the best route?"</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {chatMessages.map((msg, index) => (
                        <div key={index} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                          <div className={`max-w-[80%] p-3 rounded-lg ${
                            msg.type === 'user' 
                              ? 'bg-gradient-to-r from-emerald-500 to-teal-600 text-white ml-8 shadow-lg' 
                              : 'bg-gradient-to-r from-slate-600 to-slate-700 text-white mr-8 shadow-lg'
                          }`}>
                            <p className="text-sm">{msg.message}</p>
                            <p className="text-xs opacity-70 mt-1">
                              {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </p>
                          </div>
                        </div>
                      ))}
                      
                      {/* Show processing indicator in chat */}
                      {status && status.includes('Processing') && (
                        <div className="flex justify-start">
                          <div className="max-w-[80%] p-3 rounded-lg bg-gradient-to-r from-slate-600 to-slate-700 text-white mr-8 shadow-lg">
                            <div className="flex items-center gap-2">
                              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                              <p className="text-sm">{status}</p>
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {/* Invisible div for auto-scrolling */}
                      <div ref={chatMessagesEndRef} />
                    </div>
                  )}
                </div>

                {/* Chat Input */}
                <div className="flex gap-2">
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
                      className="w-full bg-white/10 border border-white/20 rounded-xl p-3 pr-12 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="Ask about your itinerary or request changes..."
                    />
                    <button
                      onClick={startChatListening}
                      disabled={isChatListening}
                      className={`absolute top-2 right-2 w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200 ${
                        isChatListening
                          ? 'bg-red-600 hover:bg-red-700 animate-pulse text-white'
                          : 'bg-purple-600 hover:bg-purple-700 text-white hover:scale-110'
                      } disabled:opacity-50`}
                      title={isChatListening ? 'Listening...' : 'Start Speaking'}
                    >
                      🎤
                    </button>
                  </div>
                  <button
                    onClick={sendChatMessage}
                    disabled={!chatInput.trim()}
                    className="px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-xl font-medium transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    ✨ Send
                  </button>
                </div>

                <div className="mt-3 text-xs text-gray-400 text-center">
                  💡 Try asking: "Add a restaurant", "Remove a place", "What's nearby?", or "Best order to visit?"
                </div>
              </div>
            )}
          </div>
        </div>

              {/* Map Container */}
              <div className="flex-1 relative">
                <div
                  ref={mapContainerRef}
                  className="w-full h-full rounded-none"
                  style={{ background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)' }}
                />

                {/* Route Animation Button Overlay */}
                {places.length >= 2 && (
                  <div className="absolute top-6 right-12 z-10">
                    <button 
                      onClick={isAnimating ? stopRouteAnimation : startRouteAnimation}
                      className={`py-3 px-6 rounded-xl font-medium transition-all duration-200 transform hover:scale-105 shadow-lg backdrop-blur-sm ${
                        isAnimating 
                          ? 'bg-orange-500/90 hover:bg-orange-600/90 text-white' 
                          : 'bg-blue-600/90 hover:bg-blue-700/90 text-white'
                      }`}
                      disabled={places.length < 2}
                    >
                      {isAnimating ? (
                        <>🛑 Stop Route</>
                      ) : (
                        <>🚗 Show Route Animation</>
                      )}
                    </button>
                  </div>
                )}

                {/* Map Loading Overlay */}
                {!MAPBOX_TOKEN && (
                  <div className="absolute inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center">
                    <div className="text-center">
                      <div className="w-16 h-16 bg-gradient-to-r from-emerald-600 to-teal-600 rounded-full flex items-center justify-center mx-auto mb-4">
                        🗺️
                      </div>
                      <h3 className="text-xl font-semibold mb-2">Map Loading</h3>
                      <p className="text-gray-300">Please set VITE_MAPBOX_TOKEN in frontend/.env</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Right Sidebar - Itinerary */}
              {(hasGeneratedItinerary || places.length > 0) && (
                <div className="w-[520px] bg-black/30 backdrop-blur-xl border-l border-white/10 overflow-y-auto">
                  <div className="p-6">
                    <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                      <h3 className="text-xl font-semibold mb-6 flex items-center gap-3">
                        <span className="w-10 h-10 bg-gradient-to-r from-emerald-600 to-teal-600 rounded-full flex items-center justify-center text-sm">🗺️</span>
                        Your Itinerary
                        {places.length > 0 && <span className="text-sm font-normal text-gray-400">({places.length} places)</span>}
                      </h3>
                      
                      {places.length > 0 ? (
                        <div className="space-y-4">
                          {places.map((place, index) => (
                          <div key={index} className="bg-white/10 rounded-xl p-4 border border-white/20 hover:bg-white/15 transition-colors duration-200">
                            <div className="flex items-start gap-3">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                                place.category?.toLowerCase().includes('food') ? 'bg-amber-600 text-white' :
                                place.category?.toLowerCase().includes('art') ? 'bg-rose-600 text-white' :
                                (place.category?.toLowerCase().includes('sight') || place.category?.toLowerCase().includes('culture') || 
                                 place.category?.toLowerCase().includes('temple') || place.category?.toLowerCase().includes('monument') ||
                                 place.category?.toLowerCase().includes('landmark') || place.category?.toLowerCase().includes('tourist')) ? 'bg-violet-600 text-white' : 'bg-slate-600 text-white'
                              }`}>
                                {index + 1}
                              </div>
                              <div className="flex-1 min-w-0">
                                <h4 className="font-semibold text-white mb-1">{place.name}</h4>
                                {place.neighborhood && (
                                  <p className="text-sm text-gray-300 mb-2 flex items-center gap-1">
                                    📍 {place.neighborhood}
                                  </p>
                                )}
                                {place.category && (
                                  <div className="flex items-center gap-2 mb-2">
                                    <span className={`px-2 py-1 rounded-lg text-xs font-medium ${
                                      place.category?.toLowerCase().includes('food') ? 'bg-amber-600/20 text-amber-300' :
                                      place.category?.toLowerCase().includes('art') ? 'bg-rose-600/20 text-rose-300' :
                                      (place.category?.toLowerCase().includes('sight') || place.category?.toLowerCase().includes('culture') || 
                                       place.category?.toLowerCase().includes('temple') || place.category?.toLowerCase().includes('monument') ||
                                       place.category?.toLowerCase().includes('landmark') || place.category?.toLowerCase().includes('tourist')) ? 'bg-violet-600/20 text-violet-300' : 'bg-slate-600/20 text-slate-300'
                                    }`}>
                                      {place.category?.toLowerCase().includes('food') ? '🍽️' :
                                       place.category?.toLowerCase().includes('art') ? '🎨' :
                                       (place.category?.toLowerCase().includes('sight') || place.category?.toLowerCase().includes('culture') || 
                                        place.category?.toLowerCase().includes('temple') || place.category?.toLowerCase().includes('monument') ||
                                        place.category?.toLowerCase().includes('landmark') || place.category?.toLowerCase().includes('tourist')) ? '🏛️' : '📍'} {place.category}
                                    </span>
                                  </div>
                                )}
                                {place.notes && (
                                  <p className="text-sm text-gray-400 leading-relaxed">{place.notes}</p>
                                )}
                                {place.address && (
                                  <p className="text-xs text-gray-500 mt-2">{place.address}</p>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                        </div>
                      ) : (
                        <div className="text-center py-12">
                          <div className="w-16 h-16 bg-gradient-to-r from-gray-600 to-slate-600 rounded-full flex items-center justify-center mx-auto mb-4">
                            🗺️
                          </div>
                          <h4 className="text-lg font-semibold text-gray-300 mb-2">No Itinerary Yet</h4>
                          <p className="text-sm text-gray-400">Generate an itinerary to see your places here</p>
                        </div>
                      )}
                      
                      {extracted && (
                        <div className="mt-6 pt-6 border-t border-white/10">
                          <div className="bg-gradient-to-r from-emerald-500/10 to-teal-500/10 rounded-xl p-4 border border-emerald-500/20">
                            <h4 className="font-semibold text-emerald-300 mb-3 flex items-center gap-2">
                              📋 Trip Summary
                            </h4>
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span className="text-gray-300">Destination:</span>
                                <span className="text-white font-medium">{extracted.city}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-300">Interests:</span>
                                <span className="text-white font-medium">{extracted.interests}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-300">Duration:</span>
                                <span className="text-white font-medium">{extracted.days} {extracted.days === 1 ? 'Day' : 'Days'}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
      </div>
    </div>
  );
}