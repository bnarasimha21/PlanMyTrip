import React, { useEffect, useRef, useState } from 'react';
import { View, Text, TextInput, StyleSheet, TouchableOpacity, KeyboardAvoidingView, Platform, ActivityIndicator, NativeModules } from 'react-native';
import MapboxGL from '@rnmapbox/maps';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';

// Place your Mapbox public token here - swap with process.env/.env logic for prod
const MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoiYm5hcmFzaW1oYTIxIiwiYSI6ImNtOGQ1M2VzbDFhOXoyaXM1N3h4NW9reTMifQ.A1qPIVIJyq-wHWJkiYBadg';
MapboxGL.setAccessToken(MAPBOX_ACCESS_TOKEN);

export default function TripPlannerScreen() {
  const insets = useSafeAreaInsets();
  const [tripRequest, setTripRequest] = useState('Plan a 2-day art trip to Paris');
  const mapRef = useRef(null);
  const [userCoordinate, setUserCoordinate] = useState<number[] | null>(null);
  const cameraRef = useRef<any>(null);
  const hasCenteredRef = useRef(false);
  const [isLoading, setIsLoading] = useState(false);
  const [places, setPlaces] = useState<Array<{ name: string; latitude?: number; longitude?: number; category?: string }>>([]);
  const [mapStyleLoaded, setMapStyleLoaded] = useState(false);

  const resolveApiBase = (): string => {
    if (Platform.OS === 'ios') {
      const scriptURL = (NativeModules as any)?.SourceCode?.scriptURL as string | undefined;
      const host = scriptURL ? scriptURL.split('://')[1]?.split(':')[0] : undefined;
      if (host && host !== 'localhost' && host !== '127.0.0.1') {
        return `http://${host}:8000`;
      }
      return 'http://127.0.0.1:8000';
    }
    // Android emulator special host
    return 'http://10.0.2.2:8000';
  };

  const API_BASE = resolveApiBase();

  const handleShowPlan = async () => {
    try {
      setIsLoading(true);
      // 1) Extract trip details from free-form text
      const extractResp = await fetch(`${API_BASE}/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: tripRequest }),
      });
      if (!extractResp.ok) {
        const text = await extractResp.text();
        throw new Error(`Extract failed: HTTP ${extractResp.status} ${extractResp.statusText} – ${text}`);
      }
      const extracted = await extractResp.json();

      const destination = extracted.destination || extracted.city;
      const destination_type = extracted.destination_type || 'city';
      const interests = extracted.interests || 'art, food';
      const days = typeof extracted.days === 'number' && extracted.days > 0 ? extracted.days : 1;

      // 2) Generate itinerary with extracted fields
      const itinResp = await fetch(`${API_BASE}/itinerary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trip_request: tripRequest,
          destination,
          destination_type,
          city: destination,
          interests,
          days,
          user_id: 'bnarasimha21@gmail.com',
          subscription_plan: 'premium',
        }),
      });
      if (!itinResp.ok) {
        const text = await itinResp.text();
        throw new Error(`Itinerary failed: HTTP ${itinResp.status} ${itinResp.statusText} – ${text}`);
      }
      let data = await itinResp.json();
      if (data && data.places && Array.isArray(data.places)) {
        setPlaces(data.places || []);
        console.log('[TripPlannerScreen] places received:', (data.places || []).length);
        // Fit camera to show all places (and user if available)
        const coords = (data.places || [])
          .filter((p: any) => typeof p.longitude === 'number' && typeof p.latitude === 'number')
          .map((p: any) => [p.longitude, p.latitude] as number[]);
        if (userCoordinate) coords.push(userCoordinate);
        if (cameraRef.current && coords.length >= 1) {
          let minLng = coords[0][0], maxLng = coords[0][0], minLat = coords[0][1], maxLat = coords[0][1];
          coords.forEach(([lng, lat]) => {
            if (lng < minLng) minLng = lng;
            if (lng > maxLng) maxLng = lng;
            if (lat < minLat) minLat = lat;
            if (lat > maxLat) maxLat = lat;
          });
          if (minLng === maxLng && minLat === maxLat) {
            cameraRef.current.setCamera({ centerCoordinate: [minLng, minLat], zoomLevel: 13, animationDuration: 300 });
          } else {
            cameraRef.current.setCamera({
              bounds: { ne: [maxLng, maxLat], sw: [minLng, minLat], padding: 60 },
              animationDuration: 400,
            });
          }
        }
        if ((data.places as any[]).length === 0) {
          // Fallback: let backend handle extraction internally from free text
          const directResp = await fetch(`${API_BASE}/itinerary`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              trip_request: tripRequest,
              user_id: 'bnarasimha21@gmail.com',
              subscription_plan: 'premium',
            }),
          });
          if (directResp.ok) {
            data = await directResp.json();
            setPlaces(data.places || []);
            console.log('[TripPlannerScreen] places after fallback:', (data.places || []).length);
          }
        }
        // no popup
      } else if (data && data.error && data.message) {
        // no popup
      } else {
        // no popup
      }
    } catch (e: any) {
      // no popup
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const granted = await MapboxGL.locationManager.requestWhenInUsePermissions();
        if (!granted) return;
        await MapboxGL.locationManager.start();
        const loc = await MapboxGL.locationManager.getLastKnownLocation();
        if (mounted && loc && loc.coords) {
          const { latitude, longitude } = loc.coords as any;
          if (typeof latitude === 'number' && typeof longitude === 'number') {
            const coord = [longitude, latitude] as number[];
            setUserCoordinate(coord);
            if (cameraRef.current && !hasCenteredRef.current) {
              hasCenteredRef.current = true;
              cameraRef.current.setCamera({
                centerCoordinate: coord,
                zoomLevel: 13,
                animationDuration: 0,
              });
            }
          }
        }
      } catch {}
    })();
    return () => {
      mounted = false;
      try { MapboxGL.locationManager.stop(); } catch {}
    };
  }, []);

  return (
    <SafeAreaView style={styles.wrapper}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.kav}
      >
        <View style={styles.container}>
          <Text style={styles.title}>Enter Your Trip Request</Text>

          <TextInput
            style={styles.input}
            value={tripRequest}
            onChangeText={setTripRequest}
            placeholder="Describe your dream trip..."
            placeholderTextColor="#9ca3af"
            multiline
          />

          <View style={styles.mapContainer}>
            <MapboxGL.MapView
              ref={mapRef}
              style={styles.map}
              styleURL={MapboxGL.StyleURL.Street}
              onDidFinishLoadingStyle={() => setMapStyleLoaded(true)}
            >
              {userCoordinate ? (
                <MapboxGL.PointAnnotation id="user-point" coordinate={userCoordinate} />
              ) : null}
              {mapStyleLoaded ? (
              <MapboxGL.ShapeSource
                id="places-source"
                key={`places-${places.length}`}
                shape={{
                  type: 'FeatureCollection',
                  features: places
                    .filter(p => typeof p.longitude === 'number' && typeof p.latitude === 'number')
                    .map((p, idx) => ({
                      type: 'Feature',
                      id: `place-${idx}`,
                      properties: { name: p.name || '', category: p.category || '' },
                      geometry: { type: 'Point', coordinates: [p.longitude as number, p.latitude as number] },
                    })),
                }}
              >
                <MapboxGL.CircleLayer
                  id="places-layer"
                  style={{ circleColor: '#ef4444', circleOpacity: 0.95, circleRadius: 7, circleStrokeWidth: 2, circleStrokeColor: '#ffffff' }}
                />
              </MapboxGL.ShapeSource>
              ) : null}
              <MapboxGL.Camera
                ref={cameraRef}
                defaultSettings={{ centerCoordinate: [78.9629, 20.5937], zoomLevel: 2.6 }}
              />
            </MapboxGL.MapView>
          </View>

          <TouchableOpacity
            style={[styles.button, { marginBottom: insets.bottom + 12 }]}
            activeOpacity={0.85}
            onPress={handleShowPlan}
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Show Plan</Text>
            )}
          </TouchableOpacity>
        </View>
        {/* Minimal inline debug to verify data flow visually */}
        <Text style={{ fontSize: 12, color: '#374151', marginTop: 6 }}>Places: {places.length}</Text>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    flex: 1,
    backgroundColor: '#e0f2fe',
  },
  kav: {
    flex: 1,
  },
  container: {
    flex: 1,
    alignItems: 'center',
    paddingTop: 26,
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#2563eb',
    marginBottom: 13,
  },
  input: {
    width: '100%',
    minHeight: 48,
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#cbd5e1',
    color: '#222',
    fontSize: 16,
    paddingHorizontal: 14,
    paddingVertical: 12,
    marginBottom: 18,
    shadowColor: '#9ca3af', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.10, shadowRadius: 2,
  },
  mapContainer: {
    width: '100%',
    height: 300,
    borderRadius: 18,
    overflow: 'hidden',
    backgroundColor: '#dbeafe',
    marginBottom: 20,
    shadowColor: '#1e40af', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.06, shadowRadius: 4,
  },
  map: {
    flex: 1,
    width: '100%',
    height: '100%',
  },
  button: {
    backgroundColor: '#2563eb',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 16,
    width: '85%',
    minWidth: 180,
    maxWidth: 360,
    alignItems: 'center',
    marginTop: 2,
    alignSelf: 'center',
    elevation: 2,
  },
  buttonText: {
    color: '#fff', fontWeight: 'bold', fontSize: 18,
  },
  placeMarker: {
    backgroundColor: 'rgba(37, 99, 235, 0.9)',
    borderRadius: 10,
    width: 20,
    height: 20,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#fff',
  },
  placeMarkerDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#fff',
  },
});
