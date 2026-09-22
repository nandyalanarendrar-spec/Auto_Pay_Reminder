import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import LoginScreen from './src/screens/LoginScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import SubscriptionsScreen from './src/screens/SubscriptionsScreen';
import AddSubscriptionScreen from './src/screens/AddSubscriptionScreen';
import EMITrackerScreen from './src/screens/EMITrackerScreen';
import ChatbotScreen from './src/screens/ChatbotScreen';

export default function App() {
  const [userToken, setUserToken] = useState(null);
  const [userEmail, setUserEmail] = useState('');
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkToken();
  }, []);

  const checkToken = async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      const email = await AsyncStorage.getItem('userEmail');
      if (token) {
        setUserToken(token);
        if (email) setUserEmail(email);
      }
    } catch (e) {
      console.log('Error reading token', e);
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSuccess = (token, email) => {
    setUserToken(token);
    setUserEmail(email || 'User');
    setActiveTab('dashboard');
  };

  const handleLogout = async () => {
    try {
      await AsyncStorage.removeItem('userToken');
      await AsyncStorage.removeItem('userEmail');
    } catch (e) {}
    setUserToken(null);
    setUserEmail('');
  };

  if (loading) {
    return (
      <View style={styles.loadingScreen}>
        <Text style={styles.loadingTitle}>🛡️ Autopay Guard</Text>
        <Text style={styles.loadingSub}>Loading your financial vault...</Text>
      </View>
    );
  }

  if (!userToken) {
    return <LoginScreen onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#080F1F" />

      {/* Top Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>🛡️ Autopay Guard</Text>
          <Text style={styles.headerSub}>{userEmail || 'Active Session'}</Text>
        </View>
        <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
          <Text style={styles.logoutBtnText}>Logout</Text>
        </TouchableOpacity>
      </View>

      {/* Main Content Area */}
      <View style={styles.content}>
        {activeTab === 'dashboard' && <DashboardScreen />}
        {activeTab === 'subscriptions' && <SubscriptionsScreen />}
        {activeTab === 'add' && (
          <AddSubscriptionScreen onAdded={() => setActiveTab('subscriptions')} />
        )}
        {activeTab === 'emis' && <EMITrackerScreen />}
        {activeTab === 'chatbot' && <ChatbotScreen />}
      </View>

      {/* Bottom Navigation Bar */}
      <View style={styles.bottomNav}>
        <TouchableOpacity
          style={[styles.navItem, activeTab === 'dashboard' && styles.activeNavItem]}
          onPress={() => setActiveTab('dashboard')}
        >
          <Text style={styles.navIcon}>📊</Text>
          <Text style={[styles.navLabel, activeTab === 'dashboard' && styles.activeNavLabel]}>
            Dashboard
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.navItem, activeTab === 'subscriptions' && styles.activeNavItem]}
          onPress={() => setActiveTab('subscriptions')}
        >
          <Text style={styles.navIcon}>💳</Text>
          <Text style={[styles.navLabel, activeTab === 'subscriptions' && styles.activeNavLabel]}>
            Subs
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.navItem, activeTab === 'add' && styles.activeNavItem]}
          onPress={() => setActiveTab('add')}
        >
          <View style={styles.addNavCircle}>
            <Text style={styles.addNavIcon}>＋</Text>
          </View>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.navItem, activeTab === 'emis' && styles.activeNavItem]}
          onPress={() => setActiveTab('emis')}
        >
          <Text style={styles.navIcon}>📉</Text>
          <Text style={[styles.navLabel, activeTab === 'emis' && styles.activeNavLabel]}>
            EMIs
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.navItem, activeTab === 'chatbot' && styles.activeNavItem]}
          onPress={() => setActiveTab('chatbot')}
        >
          <Text style={styles.navIcon}>🤖</Text>
          <Text style={[styles.navLabel, activeTab === 'chatbot' && styles.activeNavLabel]}>
            AI Help
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#080F1F',
  },
  loadingScreen: {
    flex: 1,
    backgroundColor: '#080F1F',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingTitle: {
    color: '#06B6D4',
    fontSize: 24,
    fontWeight: 'bold',
  },
  loadingSub: {
    color: '#94A3B8',
    fontSize: 14,
    marginTop: 8,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#0F172A',
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
  },
  headerTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold',
  },
  headerSub: {
    color: '#06B6D4',
    fontSize: 11,
    marginTop: 2,
  },
  logoutBtn: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    borderColor: '#EF4444',
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  logoutBtnText: {
    color: '#EF4444',
    fontSize: 12,
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  bottomNav: {
    flexDirection: 'row',
    backgroundColor: '#0F172A',
    borderTopWidth: 1,
    borderTopColor: '#1E293B',
    paddingVertical: 8,
    paddingHorizontal: 4,
    alignItems: 'center',
    justifyContent: 'space-around',
  },
  navItem: {
    alignItems: 'center',
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 8,
  },
  activeNavItem: {
    backgroundColor: 'rgba(124, 58, 237, 0.2)',
  },
  navIcon: {
    fontSize: 18,
  },
  navLabel: {
    color: '#64748B',
    fontSize: 10,
    marginTop: 2,
    fontWeight: '500',
  },
  activeNavLabel: {
    color: '#38BDF8',
    fontWeight: 'bold',
  },
  addNavCircle: {
    backgroundColor: '#7C3AED',
    width: 38,
    height: 38,
    borderRadius: 19,
    justifyContent: 'center',
    alignItems: 'center',
  },
  addNavIcon: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: 'bold',
    marginTop: -2,
  },
});
