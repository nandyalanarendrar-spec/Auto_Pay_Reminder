import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  SafeAreaView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { apiRequest } from '../api/config';

export default function ChatbotScreen() {
  const [activeTab, setActiveTab] = useState('cancellation'); // 'cancellation' or 'gemini'
  const [messages, setMessages] = useState([
    {
      id: '1',
      sender: 'bot',
      text: 'Hello! I am your Autopay Guard Assistant. Ask me how to cancel any subscription or ask Gemini AI for financial insights!',
      type: 'general',
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);

  const quickPrompts = activeTab === 'cancellation' 
    ? ['How to cancel Netflix?', 'Cancel Spotify', 'How to cancel Prime', 'Cancel Disney+ Hotstar']
    : ['Analyze my spending risk', 'Which trials expire soon?', 'How much do I spend monthly?', 'Tips to save on EMIs'];

  const handleSend = async (overrideQuery = null) => {
    const query = (overrideQuery || inputText).trim();
    if (!query) return;

    const userMsg = { id: Date.now().toString(), sender: 'user', text: query };
    setMessages((prev) => [...prev, userMsg]);
    if (!overrideQuery) setInputText('');
    setLoading(true);

    try {
      const res = await apiRequest('/chatbot/ask', 'POST', { query });
      let botText = res?.reply || 'Response received.';
      let guideData = null;

      if (res?.query_type === 'cancellation_guide' && res?.cancellation_steps?.length > 0) {
        guideData = {
          steps: res.cancellation_steps,
          official_url: res.official_url,
          merchant_name: res.matched_merchant
        };
      }

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          text: botText,
          guideData: guideData,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          text: '⚠️ Network connection failed. Please ensure the backend is running.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const renderMessageItem = ({ item }) => {
    const isUser = item.sender === 'user';
    return (
      <View style={[styles.msgWrapper, isUser ? styles.userMsgWrapper : styles.botMsgWrapper]}>
        <View style={[styles.msgBubble, isUser ? styles.userBubble : styles.botBubble]}>
          <Text style={isUser ? styles.userMsgText : styles.botMsgText}>{item.text}</Text>
          {item.guideData && (
            <View style={styles.guideContainer}>
              <Text style={styles.guideTitle}>📋 Steps to Cancel:</Text>
              {item.guideData.steps?.map((step, idx) => (
                <Text key={idx} style={styles.stepText}>
                  {idx + 1}. {step}
                </Text>
              ))}
              {item.guideData.official_url && (
                <Text style={styles.urlText}>🌐 Official Link: {item.guideData.official_url}</Text>
              )}
            </View>
          )}
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header Tabs */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'cancellation' && styles.activeTabButton]}
          onPress={() => setActiveTab('cancellation')}
        >
          <Text style={[styles.tabText, activeTab === 'cancellation' && styles.activeTabText]}>
            🛑 Cancellation Guide
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'gemini' && styles.activeTabButton]}
          onPress={() => setActiveTab('gemini')}
        >
          <Text style={[styles.tabText, activeTab === 'gemini' && styles.activeTabText]}>
            ✨ Gemini AI Assistant
          </Text>
        </TouchableOpacity>
      </View>

      {/* Quick Prompts */}
      <View style={styles.promptsContainer}>
        <FlatList
          horizontal
          showsHorizontalScrollIndicator={false}
          data={quickPrompts}
          keyExtractor={(item, index) => index.toString()}
          renderItem={({ item }) => (
            <TouchableOpacity style={styles.promptChip} onPress={() => handleSend(item)}>
              <Text style={styles.promptChipText}>{item}</Text>
            </TouchableOpacity>
          )}
        />
      </View>

      {/* Chat Messages */}
      <KeyboardAvoidingView
        style={styles.chatContainer}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <FlatList
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={renderMessageItem}
          contentContainerStyle={styles.messagesList}
        />

        {loading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color="#06B6D4" />
            <Text style={styles.loadingText}>Autopay Guard is thinking...</Text>
          </View>
        )}

        {/* Input Bar */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            placeholder={
              activeTab === 'cancellation'
                ? 'Ask: "How to cancel Netflix?"'
                : 'Ask Gemini: "Analyze my risk..."'
            }
            placeholderTextColor="#64748B"
            value={inputText}
            onChangeText={setInputText}
            onSubmitEditing={() => handleSend()}
          />
          <TouchableOpacity style={styles.sendButton} onPress={() => handleSend()} disabled={loading}>
            <Text style={styles.sendButtonText}>Send</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#080F1F',
  },
  tabContainer: {
    flexDirection: 'row',
    padding: 12,
    gap: 8,
    backgroundColor: '#0F172A',
  },
  tabButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: '#1E293B',
    alignItems: 'center',
  },
  activeTabButton: {
    backgroundColor: '#7C3AED',
  },
  tabText: {
    color: '#94A3B8',
    fontSize: 13,
    fontWeight: '600',
  },
  activeTabText: {
    color: '#FFFFFF',
  },
  promptsContainer: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: '#080F1F',
  },
  promptChip: {
    backgroundColor: 'rgba(6, 182, 212, 0.15)',
    borderColor: '#06B6D4',
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    marginRight: 8,
  },
  promptChipText: {
    color: '#38BDF8',
    fontSize: 12,
    fontWeight: '500',
  },
  chatContainer: {
    flex: 1,
  },
  messagesList: {
    padding: 16,
    gap: 12,
  },
  msgWrapper: {
    marginVertical: 4,
    maxWidth: '85%',
  },
  userMsgWrapper: {
    alignSelf: 'flex-end',
  },
  botMsgWrapper: {
    alignSelf: 'flex-start',
  },
  msgBubble: {
    padding: 14,
    borderRadius: 16,
  },
  userBubble: {
    backgroundColor: '#7C3AED',
    borderBottomRightRadius: 2,
  },
  botBubble: {
    backgroundColor: '#1E293B',
    borderColor: '#334155',
    borderWidth: 1,
    borderBottomLeftRadius: 2,
  },
  userMsgText: {
    color: '#FFFFFF',
    fontSize: 14,
  },
  botMsgText: {
    color: '#F1F5F9',
    fontSize: 14,
    lineHeight: 20,
  },
  guideContainer: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  guideTitle: {
    color: '#38BDF8',
    fontWeight: 'bold',
    marginBottom: 6,
    fontSize: 13,
  },
  stepText: {
    color: '#CBD5E1',
    fontSize: 13,
    marginVertical: 2,
  },
  urlText: {
    color: '#06B6D4',
    fontSize: 12,
    marginTop: 8,
    fontStyle: 'italic',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    gap: 8,
  },
  loadingText: {
    color: '#06B6D4',
    fontSize: 12,
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 12,
    backgroundColor: '#0F172A',
    gap: 8,
    alignItems: 'center',
  },
  input: {
    flex: 1,
    backgroundColor: '#1E293B',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    color: '#FFFFFF',
    fontSize: 14,
    borderColor: '#334155',
    borderWidth: 1,
  },
  sendButton: {
    backgroundColor: '#06B6D4',
    paddingHorizontal: 18,
    paddingVertical: 10,
    borderRadius: 20,
  },
  sendButtonText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: 14,
  },
});
