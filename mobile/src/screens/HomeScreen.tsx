import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Platform } from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';

export default function HomeScreen({ navigation }) {
  const insets = useSafeAreaInsets();
  return (
    <SafeAreaView style={styles.wrapper}>
      <View style={styles.background} />
      <View style={styles.centeredContent}>
        <Text style={styles.logo}>✈️ TripXplorer</Text>
        <Text style={styles.headline}>Plan Your Perfect Trip</Text>
        <Text style={styles.subtitle}>
          AI-powered travel planning with interactive maps and personalized itineraries.{"\n"}
          Discover amazing places and create unforgettable memories.
        </Text>
        <View style={[styles.buttonWrap, { marginTop: 32, marginBottom: insets.bottom + 20 }]}> 
          <TouchableOpacity
            style={styles.button}
            onPress={() => navigation.navigate('TripPlanner')}
            activeOpacity={0.85}
          >
            <View style={styles.buttonSolid}>
              <Text style={styles.buttonText}>Get Started</Text>
            </View>
          </TouchableOpacity>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  background: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#38bdf8', // Light blue bg
  },
  centeredContent: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
    paddingTop: Platform.OS === 'ios' ? 64 : 32,
  },
  logo: {
    fontSize: 38, fontWeight: 'bold', marginBottom: 10, color: '#1e40af', letterSpacing: 1,
  },
  headline: {
    fontSize: 28, fontWeight: 'bold', textAlign: 'center', color: '#334155', marginBottom: 10, marginTop: 12,
  },
  subtitle: {
    fontSize: 16, textAlign: 'center', color: '#64748b', marginBottom: 0, lineHeight: 24,
    marginHorizontal: 0,
  },
  buttonWrap: {
    width: '100%',
    alignItems: 'center',
  },
  button: {
    borderRadius: 16,
    overflow: 'hidden',
    width: '85%',
    minWidth: 180,
    maxWidth: 360,
    alignSelf: 'center',
    shadowColor: "#60a5fa",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.20,
    shadowRadius: 10,
    elevation: 4,
  },
  buttonSolid: {
    minHeight: 56,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#2563eb', // Solid blue (same as before)
    paddingHorizontal: 24,
    paddingVertical: 8,
  },
  buttonText: {
    color: '#fff', fontWeight: 'bold', fontSize: 18, lineHeight: 22, letterSpacing: 0.5,
  }
});
