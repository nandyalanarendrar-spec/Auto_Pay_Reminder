import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { apiFetch } from '../api/config';

export default function EMITrackerScreen() {
  const [emis, setEmis] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchEmis = async () => {
    try {
      const res = await apiFetch('/emis/');
      setEmis(res.emis || []);
    } catch (err) {
      console.error('Fetch EMIs error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmis();
  }, []);

  const handlePayInstallment = async (emiId, lenderName) => {
    try {
      await apiFetch(`/emis/${emiId}`, {
        method: 'PUT',
        body: JSON.stringify({ pay_installment: true }),
      });
      Alert.alert('Payment Recorded', `1 installment paid for ${lenderName}! Next due date advanced by 30 days.`);
      fetchEmis();
    } catch (e) {
      Alert.alert('Error', e.message);
    }
  };

  const renderItem = ({ item }) => {
    const paid = item.installments_paid || 0;
    const total = item.total_installments || 12;
    const pct = Math.min(Math.round((paid / total) * 100), 100);
    const installment = parseFloat(item.monthly_installment || 0);

    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View>
            <Text style={styles.lenderName}>{item.lender_name}</Text>
            <Text style={styles.loanType}>{item.loan_type || 'Loan'}</Text>
          </View>
          <Text style={styles.installment}>₹{installment.toLocaleString('en-IN')}/mo</Text>
        </View>

        {/* Completion Progress Bar */}
        <View style={styles.progressContainer}>
          <View style={styles.progressHeader}>
            <Text style={styles.progressLabel}>Loan Payoff Progress</Text>
            <Text style={styles.pctText}>{pct}% ({paid}/{total} Paid)</Text>
          </View>
          <View style={styles.progressBarTrack}>
            <View style={[styles.progressBarFill, { width: `${pct}%` }]} />
          </View>
        </View>

        <View style={styles.cardFooter}>
          <Text style={styles.dueDate}>Next Due: {item.next_due_date || 'N/A'}</Text>
          <TouchableOpacity
            style={styles.payBtn}
            onPress={() => handlePayInstallment(item.id, item.lender_name)}
          >
            <Text style={styles.payBtnText}>Pay 1 Installment</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <Text style={styles.headerTitle}>EMI & Loan Tracker</Text>
      <Text style={styles.headerSubtitle}>Monitor payoff progress & monthly loan commitments</Text>

      {loading ? (
        <View style={styles.loadingBox}>
          <ActivityIndicator color="#6366F1" size="large" />
        </View>
      ) : (
        <FlatList
          data={emis}
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          contentContainerStyle={{ paddingBottom: 30 }}
          ListEmptyComponent={
            <Text style={styles.emptyText}>No active EMI loan records found.</Text>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#080F1F',
    padding: 20,
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
  loadingBox: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  card: {
    backgroundColor: '#12192B',
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    marginBottom: 16,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  lenderName: {
    color: '#FFF',
    fontSize: 17,
    fontWeight: 'bold',
  },
  loanType: {
    color: '#94A3B8',
    fontSize: 12,
    marginTop: 2,
  },
  installment: {
    color: '#10B981',
    fontSize: 18,
    fontWeight: 'bold',
  },
  progressContainer: {
    marginBottom: 16,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  progressLabel: {
    color: '#64748B',
    fontSize: 12,
  },
  pctText: {
    color: '#6366F1',
    fontWeight: 'bold',
    fontSize: 12,
  },
  progressBarTrack: {
    height: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#6366F1',
    borderRadius: 4,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.05)',
    paddingTop: 12,
  },
  dueDate: {
    color: '#94A3B8',
    fontSize: 12,
  },
  payBtn: {
    backgroundColor: '#10B981',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 10,
  },
  payBtnText: {
    color: '#FFF',
    fontWeight: 'bold',
    fontSize: 12,
  },
  emptyText: {
    color: '#64748B',
    textAlign: 'center',
    marginTop: 40,
    fontSize: 14,
  },
});
