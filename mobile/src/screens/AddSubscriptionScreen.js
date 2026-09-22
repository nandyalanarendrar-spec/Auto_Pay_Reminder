import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Switch,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { apiFetch } from '../api/config';

export default function AddSubscriptionScreen({ navigation }) {
  const [name, setName] = useState('');
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('Entertainment');
  const [billingCycle, setBillingCycle] = useState('monthly');
  const [nextDate, setNextDate] = useState('2026-10-01');
  const [autoRenew, setAutoRenew] = useState(true);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!name || !amount) {
      Alert.alert('Required Fields', 'Please enter subscription name and amount.');
      return;
    }

    setLoading(true);
    try {
      await apiFetch('/subscriptions/', {
        method: 'POST',
        body: JSON.stringify({
          name,
          merchant_name: name,
          amount: parseFloat(amount),
          category,
          billing_cycle: billingCycle,
          next_billing_date: nextDate,
          autopay_enabled: autoRenew,
        }),
      });

      Alert.alert('Success', `Subscription "${name}" added successfully!`, [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (err) {
      Alert.alert('Error', err.message || 'Failed to add subscription.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Add New Subscription</Text>
      <Text style={styles.subtitle}>Track upcoming debits & auto-renewals in ₹ (INR)</Text>

      <View style={styles.card}>
        <Text style={styles.label}>Subscription Name</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g. Netflix, Spotify, Swiggy One"
          placeholderTextColor="#64748B"
          value={name}
          onChangeText={setName}
        />

        <Text style={styles.label}>Monthly Amount (₹ INR)</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g. 649.00"
          placeholderTextColor="#64748B"
          keyboardType="numeric"
          value={amount}
          onChangeText={setAmount}
        />

        <Text style={styles.label}>Category</Text>
        <View style={styles.row}>
          {['Entertainment', 'Software', 'Utilities', 'Food'].map((cat) => (
            <TouchableOpacity
              key={cat}
              style={[styles.badgeBtn, category === cat && styles.badgeBtnActive]}
              onPress={() => setCategory(cat)}
            >
              <Text style={[styles.badgeText, category === cat && styles.badgeTextActive]}>
                {cat}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.label}>Billing Cycle</Text>
        <View style={styles.row}>
          {['monthly', 'yearly'].map((cycle) => (
            <TouchableOpacity
              key={cycle}
              style={[styles.badgeBtn, billingCycle === cycle && styles.badgeBtnActive]}
              onPress={() => setBillingCycle(cycle)}
            >
              <Text style={[styles.badgeText, billingCycle === cycle && styles.badgeTextActive]}>
                {cycle.toUpperCase()}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.label}>Next Renewal Date (YYYY-MM-DD)</Text>
        <TextInput
          style={styles.input}
          placeholder="2026-10-01"
          placeholderTextColor="#64748B"
          value={nextDate}
          onChangeText={setNextDate}
        />

        <View style={styles.switchRow}>
          <Text style={styles.switchLabel}>Autopay Enabled</Text>
          <Switch
            value={autoRenew}
            onValueChange={setAutoRenew}
            trackColor={{ false: '#334155', true: '#6366F1' }}
            thumbColor="#FFF"
          />
        </View>

        <TouchableOpacity style={styles.saveBtn} onPress={handleSubmit} disabled={loading}>
          {loading ? <ActivityIndicator color="#FFF" /> : <Text style={styles.saveBtnText}>Save Subscription</Text>}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#080F1F',
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFF',
    marginTop: 10,
  },
  subtitle: {
    fontSize: 13,
    color: '#94A3B8',
    marginBottom: 20,
  },
  card: {
    backgroundColor: '#12192B',
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  label: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    marginBottom: 8,
    marginTop: 12,
  },
  input: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 14,
    paddingHorizontal: 16,
    paddingVertical: 12,
    color: '#FFF',
    fontSize: 15,
  },
  row: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginVertical: 4,
  },
  badgeBtn: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  badgeBtnActive: {
    backgroundColor: '#6366F1',
    borderColor: '#6366F1',
  },
  badgeText: {
    color: '#94A3B8',
    fontSize: 12,
  },
  badgeTextActive: {
    color: '#FFF',
    fontWeight: 'bold',
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 10,
  },
  switchLabel: {
    color: '#FFF',
    fontSize: 15,
    fontWeight: '600',
  },
  saveBtn: {
    backgroundColor: '#6366F1',
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 20,
  },
  saveBtnText: {
    color: '#FFF',
    fontWeight: 'bold',
    fontSize: 16,
  },
});
