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

const CATEGORIES = ['All', 'Entertainment', 'Software', 'Utilities', 'Food'];
const STATUSES = ['All', 'active', 'trial', 'cancelled'];

export default function SubscriptionsScreen({ navigation }) {
  const [subscriptions, setSubscriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');

  const fetchSubscriptions = async () => {
    try {
      let endpoint = '/subscriptions/?';
      if (selectedCategory !== 'All') endpoint += `category=${selectedCategory}&`;
      if (selectedStatus !== 'All') endpoint += `status=${selectedStatus}&`;

      const res = await apiFetch(endpoint);
      setSubscriptions(res.subscriptions || []);
    } catch (err) {
      console.error('Fetch subscriptions error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubscriptions();
  }, [selectedCategory, selectedStatus]);

  const handleDelete = (id, name) => {
    Alert.alert(
      'Cancel Subscription',
      `Are you sure you want to cancel ${name}?`,
      [
        { text: 'No', style: 'cancel' },
        {
          text: 'Yes, Cancel',
          style: 'destructive',
          onPress: async () => {
            try {
              await apiFetch(`/subscriptions/${id}`, { method: 'DELETE' });
              fetchSubscriptions();
            } catch (e) {
              Alert.alert('Error', e.message);
            }
          },
        },
      ]
    );
  };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <View>
          <Text style={styles.subName}>{item.name || item.merchant_name}</Text>
          <Text style={styles.subCategory}>{item.category || 'General'}</Text>
        </View>
        <Text style={styles.subAmount}>₹{floatVal(item.amount).toFixed(2)}</Text>
      </View>

      <View style={styles.cardFooter}>
        <Text style={styles.nextDate}>
          Next Debit: {item.next_billing_date || 'N/A'} ({item.billing_cycle || 'monthly'})
        </Text>
        <TouchableOpacity
          style={styles.deleteBtn}
          onPress={() => handleDelete(item.id, item.name || item.merchant_name)}
        >
          <Text style={styles.deleteText}>Cancel</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const floatVal = (val) => parseFloat(val) || 0;

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <Text style={styles.headerTitle}>Subscriptions</Text>
        <TouchableOpacity
          style={styles.addBtn}
          onPress={() => navigation.navigate('AddSubscription')}
        >
          <Text style={styles.addBtnText}>+ Add</Text>
        </TouchableOpacity>
      </View>

      {/* Category Filter Chips */}
      <ScrollViewHorizontal title="Category">
        {CATEGORIES.map((cat) => (
          <TouchableOpacity
            key={cat}
            style={[styles.chip, selectedCategory === cat && styles.chipActive]}
            onPress={() => setSelectedCategory(cat)}
          >
            <Text style={[styles.chipText, selectedCategory === cat && styles.chipTextActive]}>
              {cat}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollViewHorizontal>

      {loading ? (
        <View style={styles.loadingBox}>
          <ActivityIndicator color="#6366F1" />
        </View>
      ) : (
        <FlatList
          data={subscriptions}
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          contentContainerStyle={{ paddingBottom: 30 }}
          ListEmptyComponent={
            <Text style={styles.emptyText}>No subscriptions found.</Text>
          }
        />
      )}
    </View>
  );
}

const ScrollViewHorizontal = ({ children }) => (
  <View style={styles.filterRow}>{children}</View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#080F1F',
    padding: 20,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
    marginTop: 10,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFF',
  },
  addBtn: {
    backgroundColor: '#6366F1',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 12,
  },
  addBtnText: {
    color: '#FFF',
    fontWeight: 'bold',
    fontSize: 14,
  },
  filterRow: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  chip: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 6,
    marginRight: 8,
  },
  chipActive: {
    backgroundColor: '#6366F1',
    borderColor: '#6366F1',
  },
  chipText: {
    color: '#94A3B8',
    fontSize: 12,
  },
  chipTextActive: {
    color: '#FFF',
    fontWeight: 'bold',
  },
  loadingBox: {
    flex: 1,
    justify: 'center',
    alignItems: 'center',
  },
  card: {
    backgroundColor: '#12192B',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    marginBottom: 12,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  subName: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  subCategory: {
    color: '#94A3B8',
    fontSize: 12,
    marginTop: 2,
  },
  subAmount: {
    color: '#10B981',
    fontSize: 18,
    fontWeight: 'bold',
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.05)',
    paddingTop: 10,
  },
  nextDate: {
    color: '#64748B',
    fontSize: 12,
  },
  deleteBtn: {
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 8,
  },
  deleteText: {
    color: '#EF4444',
    fontSize: 12,
    fontWeight: 'bold',
  },
  emptyText: {
    color: '#64748B',
    textAlign: 'center',
    marginTop: 40,
    fontSize: 14,
  },
});
