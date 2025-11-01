import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { useSubscription } from './SubscriptionContext';
import UserProfile from './UserProfile';
import SubscriptionStatus from './SubscriptionStatus';
import GoogleLogin from './GoogleLogin';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import ReactMarkdown from 'react-markdown';

const API_BASE = (import.meta as any).env.VITE_API_BASE || window.location.origin;
const MAPBOX_TOKEN = (import.meta as any).env.VITE_MAPBOX_TOKEN || '';

if (!MAPBOX_TOKEN) {
  console.error('❌ MAPBOX_TOKEN is not set! Please add VITE_MAPBOX_TOKEN to your .env file');
}

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

// Add custom styles for rich popups and better map readability
const POPUP_STYLES = `
<style>
.rich-popup .mapboxgl-popup-content {
  padding: 0 !important;
  border-radius: 12px !important;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04) !important;
  border: 1px solid rgba(0, 0, 0, 0.1) !important;
}

.rich-popup .mapboxgl-popup-tip {
  border-top-color: white !important;
  border-bottom-color: white !important;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Improve map text readability */
.mapboxgl-map {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

/* Make map labels larger and more readable */
.mapboxgl-map .mapboxgl-ctrl-geocoder input {
  font-size: 16px !important;
}
</style>`;

export default function TripPlanner() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const { subscriptionPlan, usage, limits, checkUsage, refreshUsage } = useSubscription();
  const [tripRequest, setTripRequest] = useState('Plan a 1-day must see places in Hanoi');
  const [extracted, setExtracted] = useState<{ city: string; interests: string; days: number; destination?: string; destination_type?: string } | null>(null);
  const [places, setPlaces] = useState<Place[]>([]);
  const [status, setStatus] = useState('');
  
  const [modifyInput, setModifyInput] = useState('');
  const [isExtractedCollapsed, setIsExtractedCollapsed] = useState(true);
  const [isTripRequestCollapsed, setIsTripRequestCollapsed] = useState(false);
  const [isItineraryCollapsed, setIsItineraryCollapsed] = useState(true); // Collapsed by default on mobile
  const [chatMessages, setChatMessages] = useState<Array<{type: 'user' | 'bot', message: string, timestamp: Date}>>([]);
  const chatMessagesEndRef = useRef<HTMLDivElement>(null);
  const chatMessagesContainerRef = useRef<HTMLDivElement | null>(null);
  const [chatInput, setChatInput] = useState('');
  
  const [isAutoSubmitting, setIsAutoSubmitting] = useState(false);
  const [hasGeneratedItinerary, setHasGeneratedItinerary] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const [animationRoute, setAnimationRoute] = useState<number[][]>([]);
  const [subscriptionError, setSubscriptionError] = useState<string | null>(null);

  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const carMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const animationIdRef = useRef<number | null>(null);
  const [isNarrationEnabled, setIsNarrationEnabled] = useState(true);
  const narratedPlacesRef = useRef<Set<string>>(new Set());
  
  const chatInputRef = useRef<HTMLInputElement | null>(null); // Reference to chat input for focusing
  const [isDayMode, setIsDayMode] = useState(false); // false = night mode (default)
  const [isTTSEnabled, setIsTTSEnabled] = useState(false); // Text-to-speech for chatbot responses
  const [isMobile, setIsMobile] = useState(false); // Mobile viewport detection

  // Detect mobile viewport
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 767);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Add CSS for better map readability and voice animations
  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      /* Improve Mapbox map text readability */
      .mapboxgl-map {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
      }

      /* Make street labels larger and more readable */
      .mapboxgl-map .mapboxgl-marker {
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3)) !important;
      }

      /* Improve navigation controls */
      .mapboxgl-ctrl-group {
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
        border-radius: 8px !important;
      }

      @keyframes processingDots {
        0%, 20% { opacity: 0; }
        50% { opacity: 1; }
        100% { opacity: 0; }
      }

      .animation-delay-200 {
        animation-delay: 200ms;
      }

      .animation-delay-400 {
        animation-delay: 400ms;
      }

      /* Processing Animation */
      .processing-dot:nth-child(1) { animation-delay: 0ms; }
      .processing-dot:nth-child(2) { animation-delay: 200ms; }
      .processing-dot:nth-child(3) { animation-delay: 400ms; }

      /* Hide scrollbar for chat messages */
      .chat-messages::-webkit-scrollbar {
        display: none;
      }
      
      .chat-messages {
        -ms-overflow-style: none;
        scrollbar-width: none;
      }
    `;
    document.head.appendChild(style);

    return () => {
      document.head.removeChild(style);
    };
  }, []);

  // Helper function to initialize the map (only called once)
  const initializeMap = useCallback((container: HTMLDivElement) => {
    if (mapRef.current) return; // Already initialized
    
    try {
      console.log('🌍 Creating Mapbox map instance...');
      // Initialize with current isDayMode state
      mapRef.current = new mapboxgl.Map({
        container: container,
        style: isDayMode ? 'mapbox://styles/mapbox/streets-v12' : 'mapbox://styles/mapbox/dark-v11',
        center: [77.5946, 12.9716],
        zoom: 11,
        attributionControl: false
      });
      
      mapRef.current.on('load', () => {
        console.log('✅ Map loaded successfully');
        // Ensure map is properly sized after load
        setTimeout(() => {
          if (mapRef.current) {
            mapRef.current.resize();
          }
        }, 100);
      });
      
      mapRef.current.on('error', (e) => {
        console.error('❌ Map error:', e);
        setStatus('Map failed to load. Trying alternative style...');
        
        // Try fallback to basic streets style
        setTimeout(() => {
          if (mapRef.current) {
            try {
              console.log('🔄 Trying fallback map style...');
              mapRef.current.setStyle('mapbox://styles/mapbox/streets-v11');
            } catch (fallbackError) {
              console.error('❌ Fallback also failed:', fallbackError);
              setStatus('Unable to load map. Please refresh the page.');
            }
          }
        }, 1000);
      });
      
      mapRef.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
      console.log('🎮 Added navigation controls');
    } catch (error) {
      console.error('❌ Error creating map:', error);
      setStatus('Error initializing map');
    }
  }, [isDayMode]);

  // Init Map - runs on mount and can recover if map is missing
  useEffect(() => {
    let mounted = true;
    let visibilityCheckInterval: ReturnType<typeof setInterval> | null = null;
    let initTimeout: ReturnType<typeof setTimeout> | null = null;

    const attemptInitialize = () => {
      if (!mounted) return;
      
      const container = mapContainerRef.current;
      if (!container) {
        console.log('⏳ Map container not ready yet');
        return false;
      }

      // If map already exists and is loaded, just resize it
      if (mapRef.current) {
        try {
          if (mapRef.current.loaded()) {
            console.log('✅ Map already exists and is loaded, resizing...');
            setTimeout(() => {
              if (mapRef.current && mounted) {
                mapRef.current.resize();
              }
            }, 100);
            return true;
          } else {
            // Map exists but not loaded - remove it so we can reinitialize
            console.log('⚠️ Map exists but not loaded, removing...');
            try {
              mapRef.current.remove();
            } catch (e) {
              console.warn('Error removing stale map:', e);
            }
            mapRef.current = null;
          }
        } catch (e) {
          console.warn('Error checking map state:', e);
          try {
            if (mapRef.current) {
              mapRef.current.remove();
            }
          } catch {}
          mapRef.current = null;
        }
      }

      console.log('🗺️ Initializing map. MAPBOX_TOKEN:', MAPBOX_TOKEN ? `${MAPBOX_TOKEN.substring(0, 10)}...` : 'NOT SET');
      if (!MAPBOX_TOKEN || MAPBOX_TOKEN === 'your_mapbox_token_here') {
        console.error('❌ Mapbox token is not set or invalid');
        setStatus('Please set a valid VITE_MAPBOX_TOKEN in frontend/.env file');
        return false;
      }
      
      // Wait for container to be visible before initializing
      if (container.offsetWidth === 0 || container.offsetHeight === 0) {
        console.log('⏳ Waiting for map container to be visible...');
        visibilityCheckInterval = setInterval(() => {
          if (!mounted) {
            if (visibilityCheckInterval) clearInterval(visibilityCheckInterval);
            return;
          }
          const cont = mapContainerRef.current;
          if (cont && cont.offsetWidth > 0 && cont.offsetHeight > 0) {
            if (visibilityCheckInterval) clearInterval(visibilityCheckInterval);
            visibilityCheckInterval = null;
            // Container is now visible, initialize map
            if (!mapRef.current && mounted) {
              initializeMap(cont);
            }
          }
        }, 100);
        return false;
      }
      
      // Container is visible, initialize map
      if (!mapRef.current) {
        initializeMap(container);
        return true;
      }
      return false;
    };

    // Try to initialize immediately
    const initialized = attemptInitialize();

    // If initialization failed or was delayed, set up a periodic check
    if (!initialized) {
      initTimeout = setTimeout(() => {
        if (!mounted) return;
        // Check again after a delay in case container wasn't ready
        if (!mapRef.current) {
          console.log('🔄 Retrying map initialization...');
          attemptInitialize();
        }
      }, 500);
    }

    // Also set up a periodic check to ensure map exists (for recovery after refresh)
    const recoveryCheck = setInterval(() => {
      if (!mounted) {
        clearInterval(recoveryCheck);
        return;
      }
      
      const container = mapContainerRef.current;
      if (!container || container.offsetWidth === 0 || container.offsetHeight === 0) {
        return; // Container not ready
      }

      // If map is missing but container is ready, initialize it
      if (!mapRef.current && MAPBOX_TOKEN && MAPBOX_TOKEN !== 'your_mapbox_token_here') {
        console.log('🔧 Map missing but container ready, recovering...');
        initializeMap(container);
      }
      // If map exists but not loaded for a while, try to fix it
      else if (mapRef.current) {
        try {
          if (!mapRef.current.loaded()) {
            // Map exists but not loaded - might need reinit
            console.log('⚠️ Map exists but not loaded, will retry...');
          }
        } catch (e) {
          // Map might be in bad state, remove and reinit
          console.log('🔧 Map in bad state, removing for reinit...');
          try {
            mapRef.current.remove();
          } catch {}
          mapRef.current = null;
        }
      }
    }, 1000); // Check every second

    // Cleanup function to remove map ONLY on unmount
    return () => {
      mounted = false;
      if (visibilityCheckInterval) clearInterval(visibilityCheckInterval);
      if (initTimeout) clearTimeout(initTimeout);
      clearInterval(recoveryCheck);
      
      // Only cleanup map on actual unmount (when component is removed from DOM)
      // Don't cleanup on dependency changes
    };
  }, []); // Empty dependency array - runs once on mount but has recovery logic

  // Update map style when isDayMode changes (separate from initialization)
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.loaded()) return; // Only update if map is loaded

    try {
      const newStyle = isDayMode 
        ? 'mapbox://styles/mapbox/streets-v12' 
        : 'mapbox://styles/mapbox/dark-v11';
      console.log(`🌓 Updating map style to ${isDayMode ? 'day' : 'night'} mode`);
      map.setStyle(newStyle);
    } catch (error) {
      console.error('❌ Error updating map style:', error);
    }
  }, [isDayMode]);

  // Render markers
  useEffect(() => {
    const map = mapRef.current;
    if (!map) {
      console.log('❌ Map not ready yet');
      return;
    }

    console.log('🗺️ Rendering markers for places:', places.length, places);
    console.log('🔍 Full places data:', JSON.stringify(places, null, 2));

    // Remove any existing markers
    const existingMarkers = (window as any).__markers || [];
    console.log('🧹 Removing', existingMarkers.length, 'existing markers');
    existingMarkers.forEach((m: mapboxgl.Marker) => {
      try {
        m.remove();
      } catch (e) {
        console.warn('Failed to remove marker:', e);
      }
    });

    const markers: mapboxgl.Marker[] = [];
    let validPlaces: Place[] = [];

    places.forEach((p, index) => {
      console.log(`📍 Processing place ${index + 1}/${places.length}:`, p.name);
      console.log(`   - Coordinates: ${p.latitude}, ${p.longitude}`);
      console.log(`   - Category: ${p.category}`);
      
      if (p.latitude == null || p.longitude == null) {
        console.log('⚠️ Skipping place without coordinates:', p.name, 'lat:', p.latitude, 'lng:', p.longitude);
        return;
      }
      console.log('✅ Will add marker for:', p.name, 'at', p.latitude, p.longitude);
      validPlaces.push(p);
      const cat = (p.category || '').toLowerCase();
      // More prominent icons with bright colors that contrast with dark map
      const FOOD_ICON = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="%23FF6B35" stroke="%23FFFFFF" stroke-width="2"/><path d="M8 6c.414 0 .75.336.75.75V12h.5V6.75a.75.75 0 011.5 0V12h.5V6.75a.75.75 0 011.5 0V13a2 2 0 01-2 2h-1a2 2 0 01-2-2V6.75c0-.414.336-.75.75-.75zM15 6a.75.75 0 01.75.75V12h1.25a.75.75 0 010 1.5H15.75V19a.75.75 0 01-1.5 0V6.75c0-.414.336-.75.75-.75z" fill="white"/></svg>';
      const ART_ICON = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="%23FF1493" stroke="%23FFFFFF" stroke-width="2"/><path d="M12 6c3.866 0 7 2.582 7 5.769 0 1.279-1.037 2.231-2.24 2.231h-1.042c-.666 0-1.074.706-.766 1.298.196.377.048.84-.327 1.051A4.5 4.5 0 0112 17.5C8.134 17.5 5 14.918 5 11.731 5 8.582 8.134 6 12 6zm-3.75 5.25a.75.75 0 100-1.5.75.75 0 000 1.5zm3-1.5a.75.75 0 100-1.5.75.75 0 000 1.5zm3 1.5a.75.75 0 100-1.5.75.75 0 000 1.5z" fill="white"/></svg>';
      const SIGHTSEEING_ICON = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="%237C3AED" stroke="%23FFFFFF" stroke-width="2"/><path d="M6 20h12v-2H6v2zm6-16L8 8v4h8V8l-4-4zm-1 6V8.5l1-1 1 1V10h-2z" fill="white"/><rect x="10" y="14" width="4" height="2" fill="white"/><circle cx="12" cy="6" r="1" fill="white"/></svg>';
      const DEFAULT_ICON = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="%2300CED1" stroke="%23FFFFFF" stroke-width="2"/><path d="M12 8l4 8H8l4-8z" fill="white"/></svg>';
      // Build a labeled marker element (icon + name)
      const img = document.createElement('img');
      img.src = cat.includes('food') ? FOOD_ICON : 
                 cat.includes('art') ? ART_ICON : 
                 (cat.includes('sight') || cat.includes('culture') || cat.includes('temple') || cat.includes('monument') || cat.includes('landmark') || cat.includes('tourist')) ? SIGHTSEEING_ICON : 
                 DEFAULT_ICON;
      const isMobileViewport = typeof window !== 'undefined' && window.innerWidth <= 767;
      const markerSizePx = isMobileViewport ? 32 : 48;
      img.style.width = `${markerSizePx}px`;
      img.style.height = `${markerSizePx}px`;
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

      const label = document.createElement('span');
      label.textContent = p.name;
      label.style.fontSize = isMobileViewport ? '10px' : '12px';
      label.style.lineHeight = '1';
      label.style.whiteSpace = 'nowrap';
      label.style.color = 'white';
      label.style.background = 'rgba(0,0,0,0.55)';
      label.style.padding = isMobileViewport ? '3px 6px' : '4px 8px';
      label.style.borderRadius = '8px';
      label.style.border = '1px solid rgba(255,255,255,0.15)';
      label.style.boxShadow = '0 2px 6px rgba(0,0,0,0.25)';
      label.style.userSelect = 'none';
      label.style.pointerEvents = 'none';

      const container = document.createElement('div');
      container.style.display = 'flex';
      container.style.alignItems = 'center';
      container.style.gap = '8px';
      container.style.transform = 'translateY(-6px)';
      container.appendChild(img);
      container.appendChild(label);
      // Create rich popup with enhanced content
      const createRichPopup = (place: Place) => {
        const category = (place.category || '').toLowerCase();
        let categoryIcon = '📍';
        let categoryColor = '#6B7280';
        
        if (category.includes('food') || category.includes('restaurant') || category.includes('cafe')) {
          categoryIcon = '🍽️';
          categoryColor = '#FF6B35';
        } else if (category.includes('art') || category.includes('museum') || category.includes('gallery')) {
          categoryIcon = '🎨';
          categoryColor = '#FF1493';
        } else if (category.includes('sight') || category.includes('culture') || category.includes('temple') || 
                   category.includes('monument') || category.includes('landmark') || category.includes('tourist')) {
          categoryIcon = '🏛️';
          categoryColor = '#7C3AED';
        }

        // Generate a simple, reliable placeholder image
        const gradientId = `grad${Math.random().toString(36).substring(7)}`;
        const svgContent = `<svg xmlns="http://www.w3.org/2000/svg" width="280" height="128" viewBox="0 0 280 128">
          <defs>
            <linearGradient id="${gradientId}" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:${categoryColor}" />
              <stop offset="100%" style="stop-color:${categoryColor}dd" />
            </linearGradient>
          </defs>
          <rect width="280" height="128" fill="url(#${gradientId})" />
          <circle cx="140" cy="64" r="30" fill="rgba(255,255,255,0.15)" />
          <text x="140" y="80" text-anchor="middle" fill="white" font-size="32" font-family="system-ui">${categoryIcon}</text>
        </svg>`;
        
        // Try multiple encoding methods for better compatibility
        let placeholderImage;
        try {
          placeholderImage = `data:image/svg+xml;base64,${btoa(svgContent)}`;
          console.log('Generated base64 image for:', place.name);
        } catch (e) {
          placeholderImage = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svgContent)}`;
          console.log('Generated URI encoded image for:', place.name);
        }
        
        // Log image URL for debugging
        console.log('Image URL length:', placeholderImage.length, 'for place:', place.name);
        
        // Generate a random rating for demo (you can replace with real data)
        const rating = (4.0 + Math.random() * 1.0).toFixed(1);
        const reviews = Math.floor(50 + Math.random() * 500);

        return new mapboxgl.Popup({ 
          offset: 16,
          className: 'rich-popup',
          maxWidth: '320px'
        }).setHTML(`
          ${POPUP_STYLES}
          <div class="bg-white rounded-lg overflow-hidden shadow-xl border-0" style="min-width: 280px;">
            <!-- Image Header -->
            <div class="relative h-32 overflow-hidden" style="background: linear-gradient(135deg, ${categoryColor}dd, ${categoryColor}aa);">
              <img 
                src="${placeholderImage}" 
                alt="${place.name}" 
                class="w-full h-full object-cover"
                style="display: block; max-width: 100%;"
                onload="console.log('Image loaded successfully for: ${place.name}');"
                onerror="console.log('Image failed to load for: ${place.name}'); this.style.display='none'; this.parentNode.querySelector('.fallback-icon').style.display='flex';"
              >
              <!-- Fallback icon if image fails -->
              <div class="fallback-icon absolute inset-0 flex items-center justify-center" style="display: none; background: linear-gradient(135deg, ${categoryColor}, ${categoryColor}cc);">
                <span style="font-size: 48px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">${categoryIcon}</span>
              </div>
              <div class="absolute top-2 right-2 bg-white/90 backdrop-blur-sm rounded-full px-2 py-1 text-xs font-medium" style="color: ${categoryColor};">
                ${categoryIcon} ${place.category || 'Place'}
              </div>
            </div>
            
            <!-- Content -->
            <div class="p-4">
              <div class="flex items-start justify-between mb-2">
                <h3 class="font-bold text-gray-900 text-lg leading-tight">${place.name}</h3>
                <div class="flex items-center gap-1 ml-2">
                  <span class="text-yellow-500 text-sm">⭐</span>
                  <span class="text-sm font-medium text-gray-700">${rating}</span>
                </div>
              </div>
              
              ${place.neighborhood ? `
                <p class="text-sm text-gray-600 mb-2 flex items-center gap-1">
                  <span class="text-gray-400">📍</span> ${place.neighborhood}
                </p>
              ` : ''}
              
              <div class="flex items-center gap-1 text-xs text-gray-500 mb-3">
                <span>${reviews} reviews</span>
              </div>
              
              ${place.notes ? `
                <p class="text-sm text-gray-700 mb-3 line-clamp-2">${place.notes}</p>
              ` : ''}
              
              <!-- Action Buttons -->
              <div class="w-full">
                <button onclick="getDirections('${place.latitude}', '${place.longitude}')" 
                        class="w-full flex items-center justify-center gap-1 py-2 px-3 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded-lg transition-colors duration-200">
                  <span>🧭</span> Get Directions
                </button>
              </div>
              
              ${place.address ? `
                <div class="mt-3 pt-3 border-t border-gray-100">
                  <p class="text-xs text-gray-500">${place.address}</p>
                </div>
              ` : ''}
            </div>
          </div>
        `);
      };

      try {
        console.log('🔨 Creating marker for:', p.name);
        const marker = new mapboxgl.Marker({ element: container, anchor: 'bottom' })
          .setLngLat([p.longitude!, p.latitude!])
          .setPopup(createRichPopup(p))
          .addTo(map);
        markers.push(marker);
        console.log('🎯 Marker added successfully for:', p.name, '- Total markers now:', markers.length);
      } catch (error) {
        console.error('❌ Failed to create marker for:', p.name, error);
      }
    });

    (window as any).__markers = markers;
    
    console.log('📊 Marker creation summary:');
    console.log(`   - Total places: ${places.length}`);
    console.log(`   - Valid places with coordinates: ${validPlaces.length}`);
    console.log(`   - Markers created: ${markers.length}`);
    console.log(`   - Missing markers: ${places.length - markers.length}`);

    // Fit map to bounds after all markers are created
    if (validPlaces.length > 0) {
      console.log('📍 Valid places with coordinates:', validPlaces.length, validPlaces);
      const lats = validPlaces.map(p => p.latitude!);
      const lons = validPlaces.map(p => p.longitude!);
      
      const minLat = Math.min(...lats);
      const maxLat = Math.max(...lats);
      const minLon = Math.min(...lons);
      const maxLon = Math.max(...lons);
      
      console.log('🗺️ Calculated bounds:', { minLat, maxLat, minLon, maxLon });
      
      // Create bounds and add extra padding for better visibility
      const bounds = new mapboxgl.LngLatBounds([minLon, minLat], [maxLon, maxLat]);
      
      // Calculate dynamic padding based on marker spread
      const latRange = maxLat - minLat;
      const lonRange = maxLon - minLon;
      const maxRange = Math.max(latRange, lonRange);
      
      console.log('📏 Marker spread:', { latRange, lonRange, maxRange });
      
      // Add minimal padding for very close or single places
      if (validPlaces.length === 1 || maxRange < 0.005) {
        const padding = 0.008; // About 800m padding for single places
        bounds.extend([minLon - padding, minLat - padding]);
        bounds.extend([maxLon + padding, maxLat + padding]);
        console.log('🔍 Applied minimal padding for single/close places');
      } else if (maxRange < 0.02) {
        // For moderately spread places, add small padding
        const padding = maxRange * 0.3; // 30% of current spread
        bounds.extend([minLon - padding, minLat - padding]);
        bounds.extend([maxLon + padding, maxLat + padding]);
        console.log('🔍 Applied moderate padding for medium spread');
      }
      
      console.log('🎯 Fitting map to bounds:', bounds);
      
      // Calculate dynamic padding and zoom based on marker distribution and spread
      let dynamicPadding: number;
      let maxZoom: number;
      
      if (maxRange < 0.005) {
        // Very close markers (same neighborhood) - zoom in to show street detail
        dynamicPadding = 30;
        maxZoom = 16;
      } else if (maxRange < 0.02) {
        // Close markers (same district) - zoom in to show local streets
        dynamicPadding = 35;
        maxZoom = 15;
      } else if (maxRange < 0.05) {
        // Medium spread (across city districts) - moderate zoom for area detail
        dynamicPadding = 40;
        maxZoom = 14;
      } else {
        // Wide spread (across city) - still show good detail
        dynamicPadding = 50;
        maxZoom = 13;
      }
      
      // Adjust for number of markers - single markers can zoom in more
      if (validPlaces.length === 1) {
        maxZoom = Math.min(maxZoom + 1, 17); // Allow higher zoom for single markers
        dynamicPadding = Math.max(dynamicPadding - 10, 20);
      }
      
      console.log('⚙️ Using dynamic padding:', dynamicPadding, 'maxZoom:', maxZoom, 'for range:', maxRange);
      
      // Adjust padding for mobile devices - smaller viewport needs less padding
      const isMobile = window.innerWidth <= 767;
      const mobilePadding = isMobile ? Math.max(dynamicPadding - 15, 20) : dynamicPadding;
      
      // Delay the fitBounds to ensure markers are rendered
      setTimeout(() => {
        map.fitBounds(bounds, {
          padding: isMobile ? {
            top: mobilePadding,
            bottom: mobilePadding,
            left: mobilePadding,
            right: mobilePadding
          } : mobilePadding, // Use object on mobile for better control, number on desktop
          maxZoom: isMobile ? Math.min(maxZoom, 14) : maxZoom, // Limit zoom on mobile to prevent going out of bounds
          duration: 1200 // Faster animation
        });
      }, 100);
    }
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
    
    // Reset narrated places for new animation
    narratedPlacesRef.current.clear();
    
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
    carElement.style.width = '56px';
    carElement.style.height = '56px';
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
    const speed = 350; // Animation speed (lower = faster)
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
      
      // Check if we're near any place and narrate it
      const nearestPlace = findNearestPlace([current[0], current[1]]);
      if (nearestPlace) {
        narratePlace(nearestPlace.place.name, nearestPlace.index, places.length);
      }
      
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

  // GTTS Text-to-speech for chatbot responses
  const speakText = async (text: string) => {
    if (!isTTSEnabled || !text.trim()) return;

    // Stop any currently speaking synthesis
    if (speechSynthesis.speaking) {
      speechSynthesis.cancel();
    }

    // Clean up text - remove emojis and markdown formatting
    const cleanText = text.replace(/[📍🏛️🎨🍴🛍️👁️✨🎤⏹️🗺️🎯📝💡]/g, '')
                         .replace(/\*\*(.*?)\*\*/g, '$1')
                         .replace(/\*(.*?)\*/g, '$1')
                         .replace(/[_`]/g, '')
                         .trim();

    if (!cleanText) return;

    try {
      // Try GTTS first, fallback to browser speech synthesis
      const response = await fetch('http://localhost:8000/tts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: cleanText })
      });

      if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);

        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          // Focus chat input after TTS completes
          setTimeout(() => {
            chatInputRef.current?.focus();
          }, 100);
        };

        console.log('🔊 GTTS audio playing');
        await audio.play();
        return;
      }
    } catch (gttsError) {
      console.log('GTTS unavailable, falling back to browser TTS');
    }

    // Fallback to browser speech synthesis
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(cleanText);

      // Configure voice settings
      utterance.rate = 0.9;
      utterance.pitch = 1.0;
      utterance.volume = 0.8;

      // Try to use a high-quality voice
      const voices = speechSynthesis.getVoices();
      const preferredVoice = voices.find(voice =>
        voice.name.includes('Google') ||
        voice.name.includes('Samantha') ||
        voice.name.includes('Karen') ||
        voice.name.includes('Zira') ||
        (voice.lang.startsWith('en') && voice.localService === false)
      );

      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }

      // Add event listeners for debugging and focus management
      utterance.onstart = () => console.log('🔊 Browser TTS started');
      utterance.onend = () => {
        console.log('🔇 Browser TTS ended');
        // Focus chat input after TTS completes
        setTimeout(() => {
          chatInputRef.current?.focus();
        }, 100);
      };
      utterance.onerror = (e) => {
        console.error('❌ Browser TTS error:', e);
        // Focus chat input even on error
        setTimeout(() => {
          chatInputRef.current?.focus();
        }, 100);
      };

      speechSynthesis.speak(utterance);
    }
  };

  // Text-to-speech narration function
  const narratePlace = (placeName: string, index: number, total: number) => {
    if (!isNarrationEnabled || narratedPlacesRef.current.has(placeName)) return;
    
    narratedPlacesRef.current.add(placeName);
    
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance();
      
      if (index === 0) {
        utterance.text = `Starting your trip at ${placeName}`;
      } else if (index === total - 1) {
        utterance.text = `Arriving at your final destination, ${placeName}`;
      } else {
        utterance.text = `Next stop: ${placeName}`;
      }
      
      utterance.rate = 0.9;
      utterance.pitch = 1.0;
      utterance.volume = 0.8;
      
      // Use a clear, friendly voice if available
      const voices = speechSynthesis.getVoices();
      const preferredVoice = voices.find(voice => 
        voice.name.includes('Google') || 
        voice.name.includes('Samantha') || 
        voice.name.includes('Karen') ||
        voice.lang.startsWith('en')
      );
      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }
      
      speechSynthesis.speak(utterance);
    }
  };

  // Function to find the nearest place to current position
  const findNearestPlace = (currentPos: number[]): { place: Place; index: number } | null => {
    let nearestPlace: { place: Place; index: number } | null = null;
    let minDistance = Infinity;
    
    places.forEach((place, index) => {
      if (place.latitude && place.longitude) {
        const distance = Math.sqrt(
          Math.pow(currentPos[0] - place.longitude, 2) + 
          Math.pow(currentPos[1] - place.latitude, 2)
        );
        
        if (distance < minDistance && distance < 0.001) { // Within ~100 meters
          minDistance = distance;
          nearestPlace = { place, index };
        }
      }
    });
    
    return nearestPlace;
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


  const getDirections = (latitude: string, longitude: string) => {
    const lat = parseFloat(latitude);
    const lng = parseFloat(longitude);
    
    // Open Google Maps with directions (you can also use Mapbox Directions API)
    const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
    window.open(url, '_blank');
  };

  // Day/Night mode toggle function
  const toggleDayNightMode = () => {
    const map = mapRef.current;
    if (!map) {
      console.error('Map not available for style toggle');
      return;
    }

    try {
      const newMode = !isDayMode;
      const style = newMode 
        ? 'mapbox://styles/mapbox/streets-v12' // Day mode - clean streets with good readability
        : 'mapbox://styles/mapbox/dark-v11'; // Night mode - dark theme for low light
      
      console.log(`🌓 Switching to ${newMode ? 'day' : 'night'} mode with style: ${style}`);
      map.setStyle(style);
      setIsDayMode(newMode);
    } catch (error) {
      console.error('❌ Error switching map style:', error);
      setStatus('Error switching map theme');
    }
  };

  // Make functions available globally for popup buttons
  useEffect(() => {
    (window as any).getDirections = getDirections;
    
    return () => {
      delete (window as any).getDirections;
    };
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRouteAnimation();
    };
  }, []);

  // Handle map style changes and re-add markers
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const handleStyleLoad = () => {
      console.log('Map style loaded, re-rendering markers');
      // Force markers to re-render by updating the places array reference
      setPlaces(currentPlaces => [...currentPlaces]);
    };

    map.on('styledata', handleStyleLoad);

    return () => {
      map.off('styledata', handleStyleLoad);
    };
  }, []);

  // Resize map when sidebar appears/disappears or after state changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map) {
      // Map doesn't exist - try to initialize it
      const container = mapContainerRef.current;
      if (container && container.offsetWidth > 0 && container.offsetHeight > 0 && !mapRef.current) {
        console.log('🔄 Map missing after state change, reinitializing...');
        setTimeout(() => {
          if (!mapRef.current && container && container.offsetWidth > 0) {
            initializeMap(container);
          }
        }, 200);
      }
      return;
    }
    
    // Check if map is loaded and properly rendered
    try {
      if (!map.loaded()) {
        console.log('⚠️ Map exists but not loaded after state change, waiting...');
        const checkLoaded = setInterval(() => {
          if (mapRef.current && mapRef.current.loaded()) {
            clearInterval(checkLoaded);
            setTimeout(() => {
              if (mapRef.current) {
                mapRef.current.resize();
              }
            }, 100);
          } else if (!mapRef.current) {
            clearInterval(checkLoaded);
            // Map was removed, reinitialize
            const container = mapContainerRef.current;
            if (container && container.offsetWidth > 0) {
              initializeMap(container);
            }
          }
        }, 100);
        return () => clearInterval(checkLoaded);
      }
    } catch (e) {
      console.warn('Error checking map loaded state:', e);
    }
    
    // Delay resize to allow DOM to update
    const resizeTimeout = setTimeout(() => {
      if (mapRef.current && mapRef.current.loaded()) {
        try {
          mapRef.current.resize();
        } catch (e) {
          console.warn('Error resizing map:', e);
        }
      }
    }, 100);
    
    return () => clearTimeout(resizeTimeout);
  }, [hasGeneratedItinerary, places.length > 0, initializeMap]);

  // Refresh map when window becomes visible or regains focus
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && mapRef.current) {
        console.log('👁️ Window became visible, refreshing map...');
        setTimeout(() => {
          if (mapRef.current) {
            try {
              mapRef.current.resize();
            } catch (e) {
              console.warn('Error resizing map on visibility change:', e);
            }
          }
        }, 200);
      }
    };

    const handleFocus = () => {
      if (mapRef.current) {
        console.log('🎯 Window regained focus, refreshing map...');
        setTimeout(() => {
          if (mapRef.current) {
            try {
              mapRef.current.resize();
            } catch (e) {
              console.warn('Error resizing map on focus:', e);
            }
          }
        }, 200);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleFocus);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
    };
  }, []);

  // Auto-scroll chatbot to bottom when new messages appear
  useEffect(() => {
    // Always scroll to bottom when new messages are added
    // Use requestAnimationFrame for better timing with DOM updates
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (chatMessagesContainerRef.current && chatMessagesEndRef.current) {
          const container = chatMessagesContainerRef.current;
          // Scroll to bottom smoothly
          chatMessagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
        } else if (chatMessagesEndRef.current) {
          // Fallback: if container ref not set, use original behavior
          chatMessagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
      });
    });
  }, [chatMessages]);

  // Voice input removed

  const doExtract = async () => {
    setStatus('Extracting details...');
    try {
      const resp = await fetch(`${API_BASE}/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: tripRequest }),
      });
      const data = await resp.json();
      const normalized = {
        city: data.destination || data.city,
        interests: data.interests,
        days: data.days,
        destination: data.destination || data.city,
        destination_type: data.destination_type || 'city'
      };
      setExtracted(normalized);
      setIsExtractedCollapsed(false);
      setStatus('');
    } catch (error) {
      setStatus('Error extracting details');
    }
  };

  const doItinerary = async () => {
    // Temporarily allowing itinerary generation without login
    // if (!user) {
    //   setStatus('Please login to generate itineraries');
    //   alert('Please login to generate itineraries.');
    //   return;
    // }
    if (!API_BASE) {
      setStatus('Set VITE_API_BASE in frontend/.env');
      return;
    }
    
    setSubscriptionError(null);
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
        body: JSON.stringify({ 
          destination: req.destination || req.city,
          destination_type: req.destination_type || 'city',
          city: req.city,
          interests: req.interests, 
          days: req.days,
          user_id: user?.id || 'bnarasimha@gmail.com',
          subscription_plan: "premium"
        }),
      });
      const data = await resp.json();
      
      // Check if there was a subscription error
      if (data.error && data.type === 'subscription_limit') {
        setSubscriptionError(data.message);
        setStatus('');
        return;
      }
      
      setPlaces(data.places || []);
      setHasGeneratedItinerary(true);
      // Auto-collapse Trip Request, Trip Details, and Itinerary panel after generating itinerary (especially on mobile)
      setIsTripRequestCollapsed(true);
      setIsExtractedCollapsed(true);
      setIsItineraryCollapsed(true); // Collapse itinerary panel on mobile so map is visible first
      setStatus('');
      
      // Update subscription usage immediately from response if available
      // This updates the trip count in the header panel without additional API call
      if (data.subscription_info && data.subscription_info.usage) {
        // Dispatch event to update subscription context immediately
        const maxDaysPerTrip = limits?.max_days_per_trip || (subscriptionPlan === 'premium' ? 30 : 1);
        const updatedLimits = {
          max_trips_per_month: data.subscription_info.usage.max_trips,
          max_days_per_trip: maxDaysPerTrip,
          features: data.subscription_info.features || []
        };
        
        window.dispatchEvent(new CustomEvent('usageUpdated', {
          detail: { 
            usage: data.subscription_info.usage,
            limits: updatedLimits
          }
        }));
        
        if (refreshUsage) {
          setTimeout(() => {
            refreshUsage();
          }, 300);
        }
      } else if (refreshUsage) {
        // Fallback: refresh usage if subscription_info not available
        setTimeout(() => {
          refreshUsage();
        }, 500);
      }
    } catch (error) {
      setStatus('Error generating itinerary');
    }
  };

  // Voice input removed

  const sendChatMessage = async () => {
    if (!chatInput.trim() || !extracted || isAutoSubmitting) return;
    
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
          destination: (extracted as any).destination || extracted.city,
          destination_type: (extracted as any).destination_type || 'city',
          city: extracted.city, 
          interests: extracted.interests, 
          days: extracted.days, 
          places, 
          instruction: currentInput,
          original_request: tripRequest, // Pass the original trip request
          chat_history: chatMessages.map(msg => ({ 
            type: msg.type, 
            message: msg.message,
            timestamp: msg.timestamp.toISOString()
          })) // Pass chat history
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

      // Speak the bot response
      if (isTTSEnabled) {
        speakText(botMessage.message);
      }

      // If TTS is disabled, focus the input immediately
      if (!isTTSEnabled) {
        setTimeout(() => {
          chatInputRef.current?.focus();
        }, 100);
      }

      setStatus('');
      
    } catch (error) {
      const errorMessage = { 
        type: 'bot' as const, 
        message: 'Sorry, I encountered an error while processing your request. Please try again.', 
        timestamp: new Date() 
      };
      setChatMessages(prev => [...prev, errorMessage]);

      // Speak the error message
      if (isTTSEnabled) {
        speakText(errorMessage.message);
      }

      // If TTS is disabled, focus the input immediately
      if (!isTTSEnabled) {
        setTimeout(() => {
          chatInputRef.current?.focus();
        }, 100);
      }

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

  // Note: we no longer hard-block unauthenticated users here; we show a soft banner instead

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-white via-blue-50 to-sky-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-blue-50 to-sky-100 text-slate-800">
      {/* Header */}
      <div className="bg-white/95 backdrop-blur-md border-b border-blue-200 shadow-sm relative z-50">
        <div className={`${isMobile ? 'px-4 py-3' : 'px-6 py-6'} flex items-center justify-between`}>
          <div className={`flex items-center gap-3 ${isMobile ? 'flex-1 min-w-0' : ''}`}>
            <Link to="/" className={`${isMobile ? 'flex items-center gap-2' : 'inline-block group'} ${isMobile ? 'flex-shrink-0' : ''}`}>
              <h1 className={`${isMobile ? 'text-xl' : 'text-3xl'} font-bold bg-gradient-to-r from-blue-600 via-sky-600 to-blue-500 bg-clip-text text-transparent ${!isMobile ? 'group-hover:from-blue-700 group-hover:via-sky-700 group-hover:to-blue-600 transition-all duration-200' : ''} ${isMobile ? 'whitespace-nowrap' : ''}`}>
                {isMobile ? '✈️ TripXplorer' : '✈️ TripXplorer'}
              </h1>
            </Link>
            {!isMobile && (
              <p className="text-sm text-slate-600 mt-1">AI-powered travel planning with interactive maps</p>
            )}
          </div>
          <div className={`${isMobile ? 'flex items-center gap-2 flex-shrink-0 ml-2' : 'flex items-center gap-4'} relative z-50`}>
            {isAuthenticated ? (
              <>
                <div className={isMobile ? 'order-2' : ''}>
                  <SubscriptionStatus className={isMobile ? 'py-1.5 px-2.5' : ''} />
                </div>
                <div className={isMobile ? 'order-1' : ''}>
                  <UserProfile />
                </div>
              </>
            ) : (
              <GoogleLogin className={isMobile ? 'w-36' : 'w-48'} />
            )}
          </div>
        </div>
      </div>

            <div className="flex h-[calc(100vh-100px)]">
              {/* Sidebar */}
              <div className="w-[520px] bg-white/95 backdrop-blur-xl border-r border-blue-200 overflow-hidden flex flex-col shadow-lg">
          <div className="p-6 space-y-6 flex-shrink-0">
            {/* Trip Request Section */}
            <div className="bg-gradient-to-r from-blue-50 to-sky-50 rounded-2xl border border-blue-200 shadow-lg">
              <button
                onClick={() => setIsTripRequestCollapsed(!isTripRequestCollapsed)}
                className="w-full p-6 text-left hover:bg-blue-100/50 transition-colors duration-200 rounded-2xl"
              >
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold flex items-center gap-2 text-slate-800">
                    <span className="w-8 h-8 bg-gradient-to-r from-blue-500 to-sky-600 rounded-full flex items-center justify-center text-sm text-white">✍️</span>
                    Trip Request
                  </h3>
                  <div className="flex items-center gap-2">
                    
                    <span className={`transform transition-transform duration-200 text-slate-600`}>
                      {isTripRequestCollapsed ? '▼' : '▲'}
                    </span>
                  </div>
                </div>
              </button>
              
              {!isTripRequestCollapsed && (
                <div className="px-6 pb-6">
                  <textarea
                    value={tripRequest}
                    onChange={(e) => setTripRequest(e.target.value)}
                    rows={2}
                    className="w-full bg-white border border-blue-200 rounded-xl p-4 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none mb-4 shadow-sm text-xl font-sans"
                    style={{ fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif" }}
                    placeholder="Describe your dream trip... e.g., 'Plan a 3-day art and food tour in Paris'"
                  />
                  
                  {/* Action Buttons */}
                  <div className="flex gap-3">
                    <button 
                      onClick={doExtract}
                      className={`py-3 px-4 bg-gradient-to-r from-blue-600 to-sky-600 hover:from-blue-700 hover:to-sky-700 text-white rounded-xl font-medium transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-blue-500/25 ${
                        extracted ? 'flex-1' : 'w-full'
                      }`}
                    >
                      🔍 Get Details
                    </button>
                    {extracted && (
                      <button 
                        onClick={doItinerary}
                        className="flex-1 py-3 px-4 bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-700 hover:to-blue-700 text-white rounded-xl font-medium transition-all duration-200 transform hover:scale-105 shadow-md"
                      >
                        🗺️ Generate Itinerary
                      </button>
                    )}
                  </div>
                </div>
              )}

            </div>

            {/* Extracted Details - Collapsible */}
            {extracted && (
              <div className="bg-gradient-to-r from-blue-50 to-sky-50 rounded-2xl border border-blue-200 shadow-lg">
                <button
                  onClick={() => setIsExtractedCollapsed(!isExtractedCollapsed)}
                  className="w-full p-6 text-left hover:bg-blue-100/50 transition-colors duration-200 rounded-2xl"
                >
                  <h3 className="text-lg font-semibold flex items-center justify-between text-slate-800">
                    <div className="flex items-center gap-2">
                      <span className="w-8 h-8 bg-gradient-to-r from-blue-500 to-sky-600 rounded-full flex items-center justify-center text-sm text-white">✅</span>
                      Trip Details
                    </div>
                    <span className={`transform transition-transform duration-200 text-slate-600 ${isExtractedCollapsed ? '' : 'rotate-180'}`}>
                      {isExtractedCollapsed ? '▼' : '▲'}
                    </span>
                  </h3>
                </button>
                
                {!isExtractedCollapsed && (
                  <div className="px-6 pb-6">
                    <div className="bg-white rounded-xl p-4 space-y-3 border border-blue-200 shadow-sm">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-xs">🏙️</span>
                          <span className="text-slate-600 font-medium">Destination:</span>
                        </div>
                        <span className="font-semibold text-blue-600 bg-blue-100 px-3 py-1 rounded-lg">{extracted.city}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 bg-sky-100 rounded-full flex items-center justify-center text-xs">🎯</span>
                          <span className="text-slate-600 font-medium">Interests:</span>
                        </div>
                        <span className="font-semibold text-sky-600 bg-sky-100 px-3 py-1 rounded-lg">{extracted.interests}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-xs">📅</span>
                          <span className="text-slate-600 font-medium">Duration:</span>
                        </div>
                        <span className="font-semibold text-blue-600 bg-blue-100 px-3 py-1 rounded-lg">
                          {extracted.days} {extracted.days === 1 ? 'Day' : 'Days'}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Subscription Error */}
            {subscriptionError && (
              <div className="bg-red-50 rounded-2xl p-4 border border-red-200">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-red-100 rounded-full flex items-center justify-center text-red-600 text-sm">⚠️</div>
                  <div className="flex-1">
                    <h4 className="text-sm font-semibold text-red-800 mb-1">Subscription Limit Reached</h4>
                    <p className="text-sm text-red-700 mb-3">{subscriptionError}</p>
                    <Link
                      to="/"
                      className="inline-block bg-gradient-to-r from-blue-600 to-sky-600 hover:from-blue-700 hover:to-sky-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 transform hover:scale-105"
                    >
                      Upgrade to Premium
                    </Link>
                  </div>
                </div>
              </div>
            )}

            {/* Itinerary Generation Status */}
            {status && (status.includes('Generating') || status.includes('Extracting')) && (
              <div className="bg-blue-100 rounded-2xl p-4 border border-blue-200">
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                  <p className="text-sm text-blue-700">{status}</p>
                </div>
              </div>
            )}

            {/* Your Itinerary Panel - Mobile only, shown below Trip Details, Collapsible */}
            {isMobile && (hasGeneratedItinerary || places.length > 0) && (
              <div className="bg-gradient-to-r from-blue-50 to-sky-50 rounded-2xl border border-blue-200 shadow-lg">
                <button
                  onClick={() => setIsItineraryCollapsed(!isItineraryCollapsed)}
                  className="w-full p-6 text-left hover:bg-blue-100/50 transition-colors duration-200 rounded-2xl"
                >
                  <h3 className="text-lg font-semibold flex items-center justify-between text-slate-800 mb-1">
                    <div className="flex items-center gap-2">
                      <span className="w-8 h-8 bg-gradient-to-r from-blue-500 to-sky-600 rounded-full flex items-center justify-center text-sm">🗺️</span>
                      Your Itinerary
                      {places.length > 0 && <span className="text-sm font-normal text-slate-600">({places.length} places)</span>}
                    </div>
                    <span className={`transform transition-transform duration-200 text-slate-600 ${isItineraryCollapsed ? '' : 'rotate-180'}`}>
                      {isItineraryCollapsed ? '▼' : '▲'}
                    </span>
                  </h3>
                  {isItineraryCollapsed && (
                    <p className="text-xs text-slate-500 ml-11 mt-1 italic">Expand to see your itinerary</p>
                  )}
                </button>
                
                {!isItineraryCollapsed && (
                  <div className="px-6 pb-6">
                    <div className="bg-blue-50/80 rounded-2xl p-6 border border-blue-200 shadow-lg">
                      {places.length > 0 ? (
                        <div className="space-y-4">
                          {places.map((place, index) => (
                          <div key={index} className="bg-white/80 rounded-xl p-4 border border-blue-200 hover:bg-white transition-colors duration-200 shadow-sm">
                            <div className="flex items-start gap-3">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                                place.category?.toLowerCase().includes('food') ? 'bg-amber-500 text-white' :
                                place.category?.toLowerCase().includes('art') ? 'bg-rose-500 text-white' :
                                (place.category?.toLowerCase().includes('sight') || place.category?.toLowerCase().includes('culture') || 
                                 place.category?.toLowerCase().includes('temple') || place.category?.toLowerCase().includes('monument') ||
                                 place.category?.toLowerCase().includes('landmark') || place.category?.toLowerCase().includes('tourist')) ? 'bg-violet-500 text-white' : 'bg-blue-500 text-white'
                              }`}>
                                {index + 1}
                              </div>
                              <div className="flex-1 min-w-0">
                                <h4 className="font-semibold text-slate-800 mb-1">{place.name}</h4>
                                {place.neighborhood && (
                                  <p className="text-sm text-slate-600 mb-2 flex items-center gap-1">
                                    📍 {place.neighborhood}
                                  </p>
                                )}
                                {place.category && (
                                  <div className="flex items-center gap-2 mb-2">
                                    <span className={`px-2 py-1 rounded-lg text-xs font-medium ${
                                      place.category?.toLowerCase().includes('food') ? 'bg-amber-100 text-amber-700' :
                                      place.category?.toLowerCase().includes('art') ? 'bg-rose-100 text-rose-700' :
                                      (place.category?.toLowerCase().includes('sight') || place.category?.toLowerCase().includes('culture') || 
                                       place.category?.toLowerCase().includes('temple') || place.category?.toLowerCase().includes('monument') ||
                                       place.category?.toLowerCase().includes('landmark') || place.category?.toLowerCase().includes('tourist')) ? 'bg-violet-100 text-violet-700' : 'bg-blue-100 text-blue-700'
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
                                  <p className="text-sm text-slate-600 leading-relaxed">{place.notes}</p>
                                )}
                                {place.address && (
                                  <p className="text-xs text-slate-500 mt-2">{place.address}</p>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                        </div>
                      ) : (
                        <div className="text-center py-12">
                          <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-sky-500 rounded-full flex items-center justify-center mx-auto mb-4">
                            🗺️
                          </div>
                          <h4 className="text-lg font-semibold text-slate-600 mb-2">No Itinerary Yet</h4>
                          <p className="text-sm text-slate-500">Generate an itinerary to see your places here</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

          </div>

            {/* AI Itinerary Assistant Chatbot - Desktop: in left sidebar, Mobile: below map */}
            {hasGeneratedItinerary && !isMobile && (
              <div className="flex-1 p-6 pt-0 flex flex-col overflow-hidden">
                <div className="bg-gradient-to-r from-blue-50 to-sky-50 rounded-2xl border border-blue-200 shadow-lg flex flex-col h-full">
                  <div className="p-6 pb-4 flex-shrink-0">
                    <h3 className="text-lg font-semibold flex items-center gap-2 text-slate-800">
                      <span className="w-8 h-8 bg-gradient-to-r from-blue-600 to-sky-600 rounded-full flex items-center justify-center text-sm">🤖</span>
                      AI Itinerary Assistant
                    </h3>
                  </div>

                  {/* Chat Messages - Flexible Height */}
                  <div ref={chatMessagesContainerRef} className="bg-white/80 rounded-xl mx-6 p-4 flex-1 overflow-y-auto border border-blue-200 relative chat-messages">
                    {chatMessages.length === 0 ? (
                      <div className="text-center text-slate-500 py-8">
                        <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-sky-600 rounded-full flex items-center justify-center mx-auto mb-3">
                          💬
                        </div>
                        <p className="text-base">Ask me anything about your itinerary!</p>
                        <p className="text-sm mt-1">Try: "Add a coffee shop" or "What's the best route?"</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {chatMessages.map((msg, index) => (
                          <div key={index} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-[80%] p-3 rounded-lg ${
                              msg.type === 'user' 
                                ? 'bg-gradient-to-r from-blue-500 to-sky-600 text-white ml-8 shadow-lg' 
                                : 'bg-gradient-to-r from-blue-100 to-sky-100 text-slate-800 mr-8 shadow-lg'
                            }`}>
                              {msg.type === 'bot' ? (
                                <div className="text-base prose prose-invert prose-sm max-w-none">
                                  <ReactMarkdown
                                    components={{
                                      p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                                      ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                                      ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                                      li: ({ children }) => <li className="text-sm">{children}</li>,
                                      strong: ({ children }) => <strong className="font-semibold text-slate-800">{children}</strong>,
                                      em: ({ children }) => <em className="italic">{children}</em>,
                                      code: ({ children }) => <code className="bg-blue-100 px-1 py-0.5 rounded text-xs font-mono text-blue-800">{children}</code>,
                                      pre: ({ children }) => <pre className="bg-blue-100 p-2 rounded text-xs font-mono text-blue-800 overflow-x-auto mb-2">{children}</pre>,
                                      blockquote: ({ children }) => <blockquote className="border-l-4 border-blue-400 pl-3 italic text-blue-700 mb-2">{children}</blockquote>,
                                      h1: ({ children }) => <h1 className="text-lg font-bold text-slate-800 mb-2">{children}</h1>,
                                      h2: ({ children }) => <h2 className="text-base font-bold text-slate-800 mb-2">{children}</h2>,
                                      h3: ({ children }) => <h3 className="text-sm font-bold text-slate-800 mb-1">{children}</h3>,
                                    }}
                                  >
                                    {msg.message}
                                  </ReactMarkdown>
                                </div>
                              ) : (
                                <p className="text-base">{msg.message}</p>
                              )}
                              <p className="text-sm opacity-70 mt-1">
                                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </p>
                            </div>
                          </div>
                        ))}
                        
                        {/* Show processing indicator in chat */}
                        {status && status.includes('Processing') && (
                          <div className="flex justify-start">
                            <div className="max-w-[80%] p-4 rounded-lg bg-gradient-to-r from-blue-500 via-sky-500 to-blue-600 text-white mr-8 shadow-lg">
                              <div className="flex items-center gap-3">
                                {/* Bouncing dots animation */}
                                <div className="flex gap-1">
                                  <div className="w-2 h-2 bg-white rounded-full processing-dot" style={{animation: 'processingDots 1.4s ease-in-out infinite'}}></div>
                                  <div className="w-2 h-2 bg-white rounded-full processing-dot" style={{animation: 'processingDots 1.4s ease-in-out infinite'}}></div>
                                  <div className="w-2 h-2 bg-white rounded-full processing-dot" style={{animation: 'processingDots 1.4s ease-in-out infinite'}}></div>
                                </div>

                                {/* AI brain icon with pulse */}
                                <div className="relative">
                                  <div className="w-6 h-6 bg-white/20 rounded-full animate-pulse flex items-center justify-center">
                                    <span className="text-sm">🧠</span>
                                  </div>
                                  <div className="absolute inset-0 w-6 h-6 bg-white/10 rounded-full animate-ping"></div>
                                </div>

                                <div className="flex flex-col">
                                  <p className="text-base font-medium">Analysing your request</p>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                        
                        {/* Invisible div for auto-scrolling */}
                        <div ref={chatMessagesEndRef} />
                      </div>
                    )}

                  </div>

                  {/* Chat Input - Fixed at Bottom */}
                  <div className="p-6 pt-4 flex-shrink-0">
                    

                    <div className="space-y-4">
                      {/* Full Width Input */}
                      <div className="w-full">
                        <input
                          ref={chatInputRef}
                          type="text"
                          value={chatInput}
                          onChange={(e) => setChatInput(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && sendChatMessage()}
                          className="w-full bg-white border border-blue-200 rounded-xl p-4 text-slate-800 text-lg placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 font-sans"
                          style={{ fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif" }}
                          placeholder="💡 Try: &quot;Add a restaurant&quot;, &quot;What's nearby?&quot;, or &quot;Best route?&quot;"
                        />
                      </div>

                      {/* Control Buttons Row */}
                      <div className="flex gap-3 items-center justify-between">
                        {/* TTS Toggle Switch - Left Side */}
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-slate-600">TTS</span>
                          <div className="relative">
                            <input
                              type="checkbox"
                              checked={isTTSEnabled}
                              onChange={() => setIsTTSEnabled(!isTTSEnabled)}
                              className="sr-only"
                              id="tts-toggle"
                            />
                            <label
                              htmlFor="tts-toggle"
                              className={`block w-12 h-6 rounded-full cursor-pointer transition-all duration-200 ${
                                isTTSEnabled ? 'bg-blue-500' : 'bg-slate-300'
                              }`}
                              title={isTTSEnabled ? 'Text-to-speech enabled' : 'Text-to-speech disabled'}
                            >
                              <div
                                className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform duration-200 ${
                                  isTTSEnabled ? 'translate-x-6' : 'translate-x-0'
                                }`}
                              />
                            </label>
                          </div>
                        </div>

                        {/* Buttons - Right Side */}
                        <div className="flex gap-3 items-center">
                          

                          {/* Send Button */}
                          <button
                            onClick={sendChatMessage}
                            disabled={!chatInput.trim()}
                            className="px-4 py-3 bg-gradient-to-r from-blue-600 to-sky-600 hover:from-blue-700 hover:to-sky-700 rounded-xl font-medium transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
                          >
                            ✨ Send
                          </button>
                        </div>
                      </div>

                    </div>
                  </div>

                </div>
              </div>
            )}
        </div>

              {/* Map Container */}
              <div id="map-wrapper" className="flex-1 relative">
                <div
                  ref={mapContainerRef}
                  className="w-full h-full rounded-none"
                  style={{ 
                    background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
                    minHeight: '400px' // Ensure minimum height
                  }}
                />

                {/* Day/Night Toggle - Enhanced Styling */}
                <div id="day-night-toggle" className="absolute top-6 left-6 z-10">
                  <div className="relative group">
                    {/* Toggle Switch Container */}
                    <button 
                      onClick={toggleDayNightMode}
                      className="relative flex items-center w-20 h-10 rounded-full transition-all duration-500 transform hover:scale-110 focus:outline-none"
                      title={isDayMode ? 'Switch to Night Mode' : 'Switch to Day Mode'}
                      style={{
                        background: isDayMode 
                          ? 'linear-gradient(135deg, #ff7e5f, #feb47b, #ffd700)' // Warm sunset gradient for day
                          : 'linear-gradient(135deg, #667eea, #764ba2, #2c3e50)', // Cool twilight gradient for night
                        boxShadow: isDayMode
                          ? '0 6px 25px rgba(255, 126, 95, 0.5), 0 10px 40px rgba(255, 126, 95, 0.3), inset 0 1px 0 rgba(255,255,255,0.3)'
                          : '0 6px 25px rgba(102, 126, 234, 0.5), 0 10px 40px rgba(102, 126, 234, 0.3), inset 0 1px 0 rgba(255,255,255,0.2)',
                        border: '3px solid rgba(255, 255, 255, 0.4)',
                        backdropFilter: 'blur(10px)'
                      }}
                      onMouseEnter={(e) => {
                        const label = e.currentTarget.parentElement?.querySelector('.hover-label') as HTMLElement;
                        if (label) {
                          label.style.opacity = '1';
                          label.style.transform = 'translateX(-50%) translateY(0px)';
                        }
                      }}
                      onMouseLeave={(e) => {
                        const label = e.currentTarget.parentElement?.querySelector('.hover-label') as HTMLElement;
                        if (label) {
                          label.style.opacity = '0';
                          label.style.transform = 'translateX(-50%) translateY(10px)';
                        }
                      }}
                    >
                      {/* Background Pattern */}
                      <div className="absolute inset-0 rounded-full opacity-20"
                        style={{
                          background: isDayMode
                            ? 'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.8), transparent)'
                            : 'radial-gradient(circle at 70% 70%, rgba(255,255,255,0.3), transparent)'
                        }}
                      />
                      
                      {/* Sliding Circle */}
                      <div 
                        className="absolute w-8 h-8 rounded-full transition-all duration-500 ease-in-out flex items-center justify-center"
                        style={{
                          background: 'linear-gradient(145deg, #ffffff, #f8fafc)',
                          boxShadow: '0 4px 12px rgba(0,0,0,0.25), inset 0 2px 0 rgba(255,255,255,0.9), inset 0 -2px 0 rgba(0,0,0,0.1)',
                          left: isDayMode ? '47px' : '3px',
                          top: '50%',
                          transform: `translateY(-50%) scale(${isDayMode ? '1.15' : '1'})`
                        }}
                      >
                        <span 
                          className="text-lg transition-all duration-300"
                          style={{
                            filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.15))',
                            transform: `rotate(${isDayMode ? '360deg' : '0deg'})`,
                            fontSize: '18px'
                          }}
                        >
                          {isDayMode ? '☀️' : '🌙'}
                        </span>
                      </div>
                      
                      {/* Glow Effect */}
                      <div 
                        className="absolute inset-0 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                        style={{
                          background: isDayMode
                            ? 'radial-gradient(circle, rgba(255,126,95,0.4) 0%, transparent 70%)'
                            : 'radial-gradient(circle, rgba(102,126,234,0.4) 0%, transparent 70%)',
                          filter: 'blur(6px)'
                        }}
                      />
                    </button>
                    
                    {/* Hover Label */}
                    <div 
                      className="hover-label absolute -bottom-10 left-1/2 px-3 py-1 rounded-lg text-xs font-medium transition-all duration-300 pointer-events-none"
                      style={{
                        background: 'rgba(0, 0, 0, 0.9)',
                        color: 'white',
                        backdropFilter: 'blur(10px)',
                        whiteSpace: 'nowrap',
                        opacity: 0,
                        transform: 'translateX(-50%) translateY(10px)',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                        zIndex: 1000
                      }}
                    >
                      {isDayMode ? 'Switch to Night Mode' : 'Switch to Day Mode'}
                    </div>
                  </div>
                </div>

                {/* Route Animation Button Overlay */}
                {places.length >= 2 && (
                  <div id="route-controls" className="absolute top-6 right-16 z-10 flex gap-3">
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
                        <>🚗 Trace Route</>
                      )}
                    </button>
                    
                    <button 
                      onClick={() => setIsNarrationEnabled(!isNarrationEnabled)}
                      className={`py-3 px-4 rounded-xl font-medium transition-all duration-200 transform hover:scale-105 shadow-lg backdrop-blur-sm ${
                        isNarrationEnabled 
                          ? 'bg-green-600/90 hover:bg-green-700/90 text-white' 
                          : 'bg-gray-600/90 hover:bg-gray-700/90 text-white'
                      }`}
                      title={isNarrationEnabled ? 'Disable Voice Narration' : 'Enable Voice Narration'}
                    >
                      {isNarrationEnabled ? '🔊' : '🔇'}
                    </button>
                  </div>
                )}

                {/* Map Loading Overlay */}
                {(!MAPBOX_TOKEN || status.includes('Map failed')) && (
                  <div className="absolute inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="text-center bg-white/10 backdrop-blur-md rounded-xl p-8 border border-white/20">
                      <div className="w-16 h-16 bg-gradient-to-r from-emerald-600 to-teal-600 rounded-full flex items-center justify-center mx-auto mb-4">
                        {!MAPBOX_TOKEN ? '⚠️' : '🔄'}
                      </div>
                      <h3 className="text-xl font-semibold mb-2">
                        {!MAPBOX_TOKEN ? 'Map Configuration Missing' : 'Map Loading Issues'}
                      </h3>
                      <p className="text-gray-300 mb-4">
                        {!MAPBOX_TOKEN 
                          ? 'Please set VITE_MAPBOX_TOKEN in frontend/.env' 
                          : status || 'Initializing map...'}
                      </p>
                      {MAPBOX_TOKEN && (
                        <div className="text-xs text-gray-400">
                          Token: {MAPBOX_TOKEN.substring(0, 10)}...
                          <br />
                          Try refreshing the page if map doesn't load
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* AI Itinerary Assistant Chatbot - Mobile: below map */}
              {hasGeneratedItinerary && isMobile && (
                <div className="w-full bg-white/95 backdrop-blur-xl border-t border-blue-200 p-6 flex flex-col overflow-hidden">
                  <div className="bg-gradient-to-r from-blue-50 to-sky-50 rounded-2xl border border-blue-200 shadow-lg flex flex-col h-full max-h-[50vh]">
                    <div className="p-6 pb-4 flex-shrink-0">
                      <h3 className="text-lg font-semibold flex items-center gap-2 text-slate-800">
                        <span className="w-8 h-8 bg-gradient-to-r from-blue-600 to-sky-600 rounded-full flex items-center justify-center text-sm">🤖</span>
                        AI Itinerary Assistant
                      </h3>
                    </div>

                    {/* Chat Messages - Flexible Height */}
                    <div ref={chatMessagesContainerRef} className="bg-white/80 rounded-xl mx-6 p-4 flex-1 overflow-y-auto border border-blue-200 relative chat-messages">
                      {chatMessages.length === 0 ? (
                        <div className="text-center text-slate-500 py-8">
                          <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-sky-600 rounded-full flex items-center justify-center mx-auto mb-3">
                            💬
                          </div>
                          <p className="text-base">Ask me anything about your itinerary!</p>
                          <p className="text-sm mt-1">Try: "Add a coffee shop" or "What's the best route?"</p>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          {chatMessages.map((msg, index) => (
                            <div key={index} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                              <div className={`max-w-[80%] p-3 rounded-lg ${
                                msg.type === 'user' 
                                  ? 'bg-gradient-to-r from-blue-500 to-sky-600 text-white ml-8 shadow-lg' 
                                  : 'bg-gradient-to-r from-blue-100 to-sky-100 text-slate-800 mr-8 shadow-lg'
                              }`}>
                                {msg.type === 'bot' ? (
                                  <div className="text-base prose prose-invert prose-sm max-w-none">
                                    <ReactMarkdown
                                      components={{
                                        p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                                        ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                                        ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                                        li: ({ children }) => <li className="text-sm">{children}</li>,
                                        strong: ({ children }) => <strong className="font-semibold text-slate-800">{children}</strong>,
                                        em: ({ children }) => <em className="italic">{children}</em>,
                                        code: ({ children }) => <code className="bg-blue-100 px-1 py-0.5 rounded text-xs font-mono text-blue-800">{children}</code>,
                                        pre: ({ children }) => <pre className="bg-blue-100 p-2 rounded text-xs font-mono text-blue-800 overflow-x-auto mb-2">{children}</pre>,
                                        blockquote: ({ children }) => <blockquote className="border-l-4 border-blue-400 pl-3 italic text-blue-700 mb-2">{children}</blockquote>,
                                        h1: ({ children }) => <h1 className="text-lg font-bold text-slate-800 mb-2">{children}</h1>,
                                        h2: ({ children }) => <h2 className="text-base font-bold text-slate-800 mb-2">{children}</h2>,
                                        h3: ({ children }) => <h3 className="text-sm font-bold text-slate-800 mb-1">{children}</h3>,
                                      }}
                                    >
                                      {msg.message}
                                    </ReactMarkdown>
                                  </div>
                                ) : (
                                  <p className="text-base">{msg.message}</p>
                                )}
                                <p className="text-sm opacity-70 mt-1">
                                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </p>
                              </div>
                            </div>
                          ))}
                          
                          {/* Show processing indicator in chat */}
                          {status && status.includes('Processing') && (
                            <div className="flex justify-start">
                              <div className="max-w-[80%] p-4 rounded-lg bg-gradient-to-r from-blue-500 via-sky-500 to-blue-600 text-white mr-8 shadow-lg">
                                <div className="flex items-center gap-3">
                                  {/* Bouncing dots animation */}
                                  <div className="flex gap-1">
                                    <div className="w-2 h-2 bg-white rounded-full processing-dot" style={{animation: 'processingDots 1.4s ease-in-out infinite'}}></div>
                                    <div className="w-2 h-2 bg-white rounded-full processing-dot" style={{animation: 'processingDots 1.4s ease-in-out infinite'}}></div>
                                    <div className="w-2 h-2 bg-white rounded-full processing-dot" style={{animation: 'processingDots 1.4s ease-in-out infinite'}}></div>
                                  </div>

                                  {/* AI brain icon with pulse */}
                                  <div className="relative">
                                    <div className="w-6 h-6 bg-white/20 rounded-full animate-pulse flex items-center justify-center">
                                      <span className="text-sm">🧠</span>
                                    </div>
                                    <div className="absolute inset-0 w-6 h-6 bg-white/10 rounded-full animate-ping"></div>
                                  </div>

                                  <div className="flex flex-col">
                                    <p className="text-base font-medium">Analysing your request</p>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}
                          
                          {/* Invisible div for auto-scrolling */}
                          <div ref={chatMessagesEndRef} />
                        </div>
                      )}

                    </div>

                    {/* Chat Input - Fixed at Bottom */}
                    <div className="p-6 pt-4 flex-shrink-0">
                      <div className="space-y-4">
                        {/* Full Width Input */}
                        <div className="w-full">
                          <input
                            ref={chatInputRef}
                            type="text"
                            value={chatInput}
                            onChange={(e) => setChatInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && sendChatMessage()}
                            className="w-full bg-white border border-blue-200 rounded-xl p-4 text-slate-800 text-lg placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 font-sans"
                            style={{ fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif" }}
                            placeholder="💡 Try: &quot;Add a restaurant&quot;, &quot;What's nearby?&quot;, or &quot;Best route?&quot;"
                          />
                        </div>

                        {/* Control Buttons Row */}
                        <div className="flex gap-3 items-center justify-between">
                          {/* TTS Toggle Switch - Left Side */}
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-slate-600">TTS</span>
                            <div className="relative">
                              <input
                                type="checkbox"
                                checked={isTTSEnabled}
                                onChange={() => setIsTTSEnabled(!isTTSEnabled)}
                                className="sr-only"
                                id="tts-toggle-mobile"
                              />
                              <label
                                htmlFor="tts-toggle-mobile"
                                className={`block w-12 h-6 rounded-full cursor-pointer transition-all duration-200 ${
                                  isTTSEnabled ? 'bg-blue-500' : 'bg-slate-300'
                                }`}
                                title={isTTSEnabled ? 'Text-to-speech enabled' : 'Text-to-speech disabled'}
                              >
                                <div
                                  className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform duration-200 ${
                                    isTTSEnabled ? 'translate-x-6' : 'translate-x-0'
                                  }`}
                                />
                              </label>
                            </div>
                          </div>

                          {/* Buttons - Right Side */}
                          <div className="flex gap-3 items-center">
                            {/* Send Button */}
                            <button
                              onClick={sendChatMessage}
                              disabled={!chatInput.trim()}
                              className="px-4 py-3 bg-gradient-to-r from-blue-600 to-sky-600 hover:from-blue-700 hover:to-sky-700 rounded-xl font-medium transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
                            >
                              ✨ Send
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>

                  </div>
                </div>
              )}

              {/* Right Sidebar - Itinerary - Desktop only */}
              {!isMobile && (hasGeneratedItinerary || places.length > 0) && (
                <div className="w-[520px] bg-white/95 backdrop-blur-xl border-l border-blue-200 overflow-y-auto shadow-lg">
                  <div className="p-6">
                    <div className="bg-blue-50/80 rounded-2xl p-6 border border-blue-200 shadow-lg">
                      <h3 className="text-xl font-semibold mb-6 flex items-center gap-3 text-slate-800">
                        <span className="w-10 h-10 bg-gradient-to-r from-blue-500 to-sky-600 rounded-full flex items-center justify-center text-sm">🗺️</span>
                        Your Itinerary
                        {places.length > 0 && <span className="text-sm font-normal text-slate-600">({places.length} places)</span>}
                      </h3>
                      
                      {places.length > 0 ? (
                        <div className="space-y-4">
                          {places.map((place, index) => (
                          <div key={index} className="bg-white/80 rounded-xl p-4 border border-blue-200 hover:bg-white transition-colors duration-200 shadow-sm">
                            <div className="flex items-start gap-3">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                                place.category?.toLowerCase().includes('food') ? 'bg-amber-500 text-white' :
                                place.category?.toLowerCase().includes('art') ? 'bg-rose-500 text-white' :
                                (place.category?.toLowerCase().includes('sight') || place.category?.toLowerCase().includes('culture') || 
                                 place.category?.toLowerCase().includes('temple') || place.category?.toLowerCase().includes('monument') ||
                                 place.category?.toLowerCase().includes('landmark') || place.category?.toLowerCase().includes('tourist')) ? 'bg-violet-500 text-white' : 'bg-blue-500 text-white'
                              }`}>
                                {index + 1}
                              </div>
                              <div className="flex-1 min-w-0">
                                <h4 className="font-semibold text-slate-800 mb-1">{place.name}</h4>
                                {place.neighborhood && (
                                  <p className="text-sm text-slate-600 mb-2 flex items-center gap-1">
                                    📍 {place.neighborhood}
                                  </p>
                                )}
                                {place.category && (
                                  <div className="flex items-center gap-2 mb-2">
                                    <span className={`px-2 py-1 rounded-lg text-xs font-medium ${
                                      place.category?.toLowerCase().includes('food') ? 'bg-amber-100 text-amber-700' :
                                      place.category?.toLowerCase().includes('art') ? 'bg-rose-100 text-rose-700' :
                                      (place.category?.toLowerCase().includes('sight') || place.category?.toLowerCase().includes('culture') || 
                                       place.category?.toLowerCase().includes('temple') || place.category?.toLowerCase().includes('monument') ||
                                       place.category?.toLowerCase().includes('landmark') || place.category?.toLowerCase().includes('tourist')) ? 'bg-violet-100 text-violet-700' : 'bg-blue-100 text-blue-700'
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
                                  <p className="text-sm text-slate-600 leading-relaxed">{place.notes}</p>
                                )}
                                {place.address && (
                                  <p className="text-xs text-slate-500 mt-2">{place.address}</p>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                        </div>
                      ) : (
                        <div className="text-center py-12">
                          <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-sky-500 rounded-full flex items-center justify-center mx-auto mb-4">
                            🗺️
                          </div>
                          <h4 className="text-lg font-semibold text-slate-600 mb-2">No Itinerary Yet</h4>
                          <p className="text-sm text-slate-500">Generate an itinerary to see your places here</p>
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