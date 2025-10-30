import React, { useRef, useState } from 'react';
import { View, Text, TextInput, StyleSheet, TouchableOpacity, KeyboardAvoidingView, Platform } from 'react-native';
import MapboxGL from '@rnmapbox/maps';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';

// Place your Mapbox public token here - swap with process.env/.env logic for prod
const MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoiYm5hcmFzaW1oYTIxIiwiYSI6ImNtOGQ1M2VzbDFhOXoyaXM1N3h4NW9reTMifQ.A1qPIVIJyq-wHWJkiYBadg';
MapboxGL.setAccessToken(MAPBOX_ACCESS_TOKEN);

export default function TripPlannerScreen() {
  const insets = useSafeAreaInsets();
  const [tripRequest, setTripRequest] = useState('Plan a 2-day art trip to Paris');
  const mapRef = useRef(null);

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
            >
              <MapboxGL.Camera
                zoomLevel={2.6}
                centerCoordinate={[78.9629, 20.5937]} // Center: India, default
              />
            </MapboxGL.MapView>
          </View>

          <TouchableOpacity
            style={[styles.button, { marginBottom: insets.bottom + 12 }]}
            activeOpacity={0.85}
            onPress={() => { /* TODO: add API call to extract plan */ }}
          >
            <Text style={styles.buttonText}>Show Plan</Text>
          </TouchableOpacity>
        </View>
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
});
