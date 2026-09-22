import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { apiFetch } from '../api/config';

export default function DashboardScreen({ navigation }) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [safetyData, setSafetyData] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [spendingData, setSpendingData] = useState(null);

  const fetchDashboardData = async () => {
    try {
      const [safety, forecast, spending] = await Promise.all([
        apiFetch('/dashboard/safety-score').catch(() => ({ safety_score: 75, status_grade: 'MODERATE_RISK' })),
        apiFetch('/dashboard/forecast?days=30').catch(() => ({ total_projected_outflow_30d: 16730, upcoming_count: 5 })),
        apiFetch('/analytics/spending-summary').catch(() => ({ total_monthly_spend: 4230, category_breakdown: {} })),
      ]);

      setSafetyData(safety);
      setForecastData(forecast);
      setSpendingData(spending);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchDashboardData();
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#6366F1" />
        <Text style={styles.loadingText}>Loading Autopay Vault...</Text>
      </View>
    );
  }

  const score = safetyData?.safety_score || 75;
  const grade = safetyData?.status_grade || 'MODERATE_RISK';
  const monthlyTotal = spendingData?.total_monthly_spend || 4230;
  const outflow30d = forecastData?.total_projected_outflow_30d || 16730;

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#6366F1" />}
    >
      <Text style={styles.headerTitle}>Dashboard Overview</Text>
      <Text style={styles.headerSubtitle}>Real-time Autopay Security & Risk Analysis</Text>

      {/* Safety Score Card */}
      <View style={styles.card}>
        <View style={styles.scoreRow}>
          <View>
            <Text style={styles.cardLabel}>Financial Safety Score</Text>
            <Text style={styles.scoreText}>{score} / 100</Text>
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{grade.replace('_', ' ')}</Text>
            </View>
          </View>
          <Text style={styles.scoreEmoji}>{score >= 80 ? '🛡️' : score >= 50 ? '🟠' : '🚨'}</Text>
        </View>

        <Text style={styles.scoreSummary}>
          {safetyData?.summary || 'Moderate financial risk detected. Review trial traps & price hikes.'}
        </Text>
      </View>

      {/* Outflow Stats Cards Grid */}
      <View style={styles.grid}>
        <View style={[styles.card, styles.gridCard]}>
          <Text style={styles.statLabel}>Monthly Subscriptions</Text>
          <Text style={styles.statValue}>₹{monthlyTotal.toLocaleString('en-IN')}</Text>
          <Text style={styles.statSub}>Total active spend</Text>
        </View>

        <View style={[styles.card, styles.gridCard]}>
          <Text style={styles.statLabel}>30-Day Outflow</Text>
          <Text style={[styles.statValue, { color: '#6366F1' }]}>
            ₹{outflow30d.toLocaleString('en-IN')}
          </Text>
          <Text style={styles.statSub}>Projected debits</Text>
        </View>
      </View>

      {/* Contributing Factors Section */}
      <Text style={styles.sectionTitle}>Safety Score Breakdown</Text>
      {(safetyData?.contributing_factors || [
        { factor_name: 'Active Price Hike', impact_points: -15, description: 'Price increase detected on Adobe Creative Cloud' },
        { factor_name: 'Upcoming Large Payment', impact_points: -10, description: 'HDFC Home Loan EMI due soon' }
      ]).map((factor, idx) => (
        <View key={idx} style={styles.factorCard}>
          <View style={styles.factorHeader}>
            <Text style={styles.factorName}>{factor.factor_name}</Text>
            <Text style={styles.impactText}>{factor.impact_points} pts</Text>
          </View>
          <Text style={styles.factorDesc}>{factor.description}</Text>
        </View>
      ))}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#080F1F',
    padding: 20,
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#080F1F',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#94A3B8',
    marginTop: 12,
    fontSize: 14,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFF',
    marginTop: 10,
  },
  headerSubtitle: {
    fontSize: 13,
    color: '#94A3B8',
    marginBottom: 20,
  },
  card: {
    backgroundColor: '#12192B',
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    marginBottom: 16,
  },
  cardLabel: {
    color: '#94A3B8',
    fontSize: 12,
    textTransform: 'uppercase',
    fontWeight: '600',
  },
  scoreRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  scoreText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#10B981',
    marginVertical: 4,
  },
  scoreEmoji: {
    fontSize: 40,
  },
  badge: {
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  badgeText: {
    color: '#10B981',
    fontSize: 11,
    fontWeight: 'bold',
  },
  scoreSummary: {
    color: '#CBD5E1',
    fontSize: 13,
    marginTop: 14,
    lineHeight: 18,
  },
  grid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  gridCard: {
    width: '48%',
  },
  statLabel: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#10B981',
    marginVertical: 6,
  },
  statSub: {
    color: '#64748B',
    fontSize: 11,
  },
  sectionTitle: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 10,
    marginBottom: 12,
  },
  factorCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.06)',
    marginBottom: 10,
  },
  factorHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  factorName: {
    color: '#F8FAFC',
    fontWeight: 'bold',
    fontSize: 14,
  },
  impactText: {
    color: '#EF4444',
    fontWeight: 'bold',
    fontSize: 13,
  },
  factorDesc: {
    color: '#94A3B8',
    fontSize: 12,
    lineHeight: 16,
  },
});
