# threshold-social

Generated 7 source files based on strategic design.


### README.md
```markdown
# Threshold Social - Mobile App

This is the foundational MVP for Threshold Social, built with React Native (Expo), TypeScript, and NativeWind (Tailwind CSS).

## Prerequisites
- Node.js
- Expo Go app on your phone or a simulator

## Setup & Installation

1. **Initialize the Expo project:**
```

### src/types.ts
```typescript
export type EventStatus = 'PENDING' | 'CONFIRMED' | 'CANCELLED';

export interface SocialEvent {
  id: string;
  title: string;
  description: string;
  location: string;
  date: Date;
  hostId: string;
  hostName: string;
  threshold: number;
  currentRsvps: number;
  status: EventStatus;
  userHasRsvped: boolean;
}

export type RootStackParamList = {
  Home: undefined;
  CreateEvent: undefined;
  EventDetails: { eventId: string };
};
```

### src/store.tsx
```typescript
import React, { createContext, useContext, useState } from 'react';
import { SocialEvent } from './types';

// Mock Data
const MOCK_EVENTS: SocialEvent[] = [
  {
    id: '1',
    title: 'Friday Night Tacos 🌮',
    description: 'Thinking of hitting up that new spot downtown. Only going if we get a squad.',
    location: 'El Camino, Downtown',
    date: new Date(new Date().setDate(new Date().getDate() + 1)), // Tomorrow
    hostId: 'user1',
    hostName: 'Sarah',
    threshold: 4,
    currentRsvps: 2,
    status: 'PENDING',
    userHasRsvped: false,
  },
  {
    id: '2',
    title: 'Sunday Hike ⛰️',
    description: 'Weather looks great. Lets hit the trails.',
    location: 'Mount Tam',
    date: new Date(new Date().setDate(new Date().getDate() + 3)),
    hostId: 'user2',
    hostName: 'Mike',
    threshold: 3,
    currentRsvps: 3,
    status: 'CONFIRMED',
    userHasRsvped: true,
  },
];

interface AppContextType {
  events: SocialEvent[];
  addEvent: (event: Omit<SocialEvent, 'id' | 'currentRsvps' | 'status' | 'userHasRsvped'>) => void;
  rsvpToEvent: (eventId: string) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [events, setEvents] = useState<SocialEvent[]>(MOCK_EVENTS);

  const addEvent = (newEventData: Omit<SocialEvent, 'id' | 'currentRsvps' | 'status' | 'userHasRsvped'>) => {
    const newEvent: SocialEvent = {
      ...newEventData,
      id: Math.random().toString(36).substr(2, 9),
      currentRsvps: 1, // Host counts as 1
      status: newEventData.threshold <= 1 ? 'CONFIRMED' : 'PENDING',
      userHasRsvped: true,
    };
    setEvents((prev) => [newEvent, ...prev]);
  };

  const rsvpToEvent = (eventId: string) => {
    setEvents((prevEvents) =>
      prevEvents.map((ev) => {
        if (ev.id !== eventId) return ev;
        
        // Toggle RSVP logic
        const isJoining = !ev.userHasRsvped;
        const newCount = isJoining ? ev.currentRsvps + 1 : ev.currentRsvps - 1;
        
        // Threshold Logic
        let newStatus = ev.status;
        if (newCount >= ev.threshold) {
            newStatus = 'CONFIRMED';
        } else {
            newStatus = 'PENDING';
        }

        return {
          ...ev,
          userHasRsvped: isJoining,
          currentRsvps: newCount,
          status: newStatus,
        };
      })
    );
  };

  return (
    <AppContext.Provider value={{ events, addEvent, rsvpToEvent }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppStore = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error('useAppStore must be used within AppProvider');
  return context;
};
```

### src/screens/HomeScreen.tsx
```typescript
import React from 'react';
import { View, Text, FlatList, TouchableOpacity, SafeAreaView, StatusBar } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { format } from 'date-fns';
import { Plus, Users, CheckCircle, Clock } from 'lucide-react-native';

import { useAppStore } from '../store';
import { RootStackParamList, SocialEvent } from '../types';

type HomeScreenNavProp = NativeStackNavigationProp<RootStackParamList, 'Home'>;

const EventCard = ({ event, onPress }: { event: SocialEvent; onPress: () => void }) => {
  const isConfirmed = event.status === 'CONFIRMED';
  const progressPercent = Math.min((event.currentRsvps / event.threshold) * 100, 100);

  return (
    <TouchableOpacity
      onPress={onPress}
      className={`mb-4 rounded-2xl border bg-white p-5 shadow-sm ${
        isConfirmed ? 'border-success/30' : 'border-gray-200'
      }`}
    >
      <View className="mb-2 flex-row items-center justify-between">
        <View className={`rounded-full px-3 py-1 ${isConfirmed ? 'bg-success/10' : 'bg-pending/10'}`}>
          <Text className={`text-xs font-bold ${isConfirmed ? 'text-success' : 'text-yellow-700'}`}>
            {isConfirmed ? 'EVENT ON! 🎉' : `NEEDS ${event.threshold - event.currentRsvps} MORE`}
          </Text>
        </View>
        <Text className="text-xs text-gray-400">{format(event.date, 'MMM d, h:mm a')}</Text>
      </View>

      <Text className="mb-1 text-xl font-bold text-gray-900">{event.title}</Text>
      <Text className="mb-3 text-sm text-gray-500" numberOfLines={2}>
        {event.description}
      </Text>

      {/* Threshold Progress Bar */}
      <View className="mb-3 h-2 w-full overflow-hidden rounded-full bg-gray-100">
        <View 
          className={`h-full rounded-full ${isConfirmed ? 'bg-success' : 'bg-primary'}`} 
          style={{ width: `${progressPercent}%` }} 
        />
      </View>

      <View className="flex-row items-center justify-between">
        <View className="flex-row items-center">
          <Users size={16} color="#6b7280" />
          <Text className="ml-1 text-sm text-gray-600">
            {event.currentRsvps} / <Text className="font-bold">{event.threshold}</Text> interested
          </Text>
        </View>
        <View className="flex-row items-center">
          <Text className="mr-2 text-sm text-gray-400">Host: {event.hostName}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );
};

export default function HomeScreen() {
  const navigation = useNavigation<HomeScreenNavProp>();
  const { events } = useAppStore();

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <StatusBar barStyle="dark-content" />
      
      {/* Header */}
      <View className="flex-row items-center justify-between px-5 py-4">
        <View>
            <Text className="text-2xl font-bold text-gray-900">Threshold</Text>
            <Text className="text-sm text-gray-500">Make plans that actually happen.</Text>
        </View>
        {/* Profile Placeholder */}
        <View className="h-10 w-10 items-center justify-center rounded-full bg-gray-200">
            <Text className="font-bold text-gray-600">ME</Text>
        </View>
      </View>

      {/* Feed */}
      <FlatList
        data={events}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <EventCard 
            event={item} 
            onPress={() => navigation.navigate('EventDetails', { eventId: item.id })} 
          />
        )}
        contentContainerStyle={{ padding: 20 }}
        ListEmptyComponent={
            <Text className="mt-10 text-center text-gray-500">No events yet. Start one!</Text>
        }
      />

      {/* FAB */}
      <TouchableOpacity
        className="absolute bottom-10 right-6 h-14 w-14 items-center justify-center rounded-full bg-primary shadow-lg"
        onPress={() => navigation.navigate('CreateEvent')}
      >
        <Plus color="white" size={28} />
      </TouchableOpacity>
    </SafeAreaView>
  );
}
```

### src/screens/EventDetailsScreen.tsx
```typescript
import React, { useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { useRoute, useNavigation, RouteProp } from '@react-navigation/native';
import { format } from 'date-fns';
import { MapPin, Clock, Users, ShieldCheck, Lock } from 'lucide-react-native';

import { useAppStore } from '../store';
import { RootStackParamList } from '../types';

type DetailsRouteProp = RouteProp<RootStackParamList, 'EventDetails'>;

export default function EventDetailsScreen() {
  const route = useRoute<DetailsRouteProp>();
  const navigation = useNavigation();
  const { events, rsvpToEvent } = useAppStore();
  
  const event = events.find((e) => e.id === route.params.eventId);

  useEffect(() => {
    if (!event) {
        navigation.goBack();
    }
  }, [event, navigation]);

  if (!event) return null;

  const isConfirmed = event.status === 'CONFIRMED';
  const remaining = Math.max(0, event.threshold - event.currentRsvps);

  const handleRSVP = () => {
    // If we are currently joining and this action will trigger the threshold
    if (!event.userHasRsvped && event.currentRsvps + 1 === event.threshold) {
        Alert.alert(
            "🚀 Threshold Reached!",
            "You just made this event official! Everyone will be notified.",
            [{ text: "Let's Go!" }]
        );
    }
    rsvpToEvent(event.id);
  };

  return (
    <View className="flex-1 bg-white">
      <ScrollView className="flex-1">
        {/* Header Image Placeholder */}
        <View className={`h-48 w-full items-center justify-center ${isConfirmed ? 'bg-success' : 'bg-gray-800'}`}>
            {isConfirmed ? (
                <View className="items-center">
                     <ShieldCheck size={64} color="white" />
                     <Text className="mt-2 text-2xl font-bold text-white">IT'S HAPPENING</Text>
                </View>
            ) : (
                <View className="items-center opacity-80">
                     <Lock size={64} color="white" />
                     <Text className="mt-2 text-lg font-bold text-white">PENDING THRESHOLD</Text>
                </View>
            )}
        </View>

        <View className="px-6 py-6">
            <Text className="text-3xl font-bold text-gray-900">{event.title}</Text>
            
            {/* Status Banner */}
            <View className={`mt-4 flex-row items-center rounded-lg p-3 ${isConfirmed ? 'bg-green-100' : 'bg-yellow-100'}`}>
                <Text className={`flex-1 font-medium ${isConfirmed ? 'text-green-800' : 'text-yellow-800'}`}>
                    {isConfirmed 
                        ? `Event Confirmed! The threshold of ${event.threshold} was met.` 
                        : `Waitlist mode. Need ${remaining} more people to commit.`}
                </Text>
            </View>

            {/* Meta Data */}
            <View className="mt-6 space-y-4">
                <View className="flex-row items-center">
                    <Clock size={20} color="#6b7280" />
                    <Text className="ml-3 text-lg text-gray-700">{format(event.date, 'EEEE, MMM d @ h:mm a')}</Text>
                </View>
                <View className="flex-row items-center">
                    <MapPin size={20} color="#6b7280" />
                    <Text className="ml-3 text-lg text-gray-700">{event.location}</Text>
                </View>
                <View className="flex-row items-center">
                    <Users size={20} color="#6b7280" />
                    <Text className="ml-3 text-lg text-gray-700">
                        Hosted by <Text className="font-bold">{event.hostName}</Text>
                    </Text>
                </View>
            </View>

            {/* Description */}
            <View className="mt-8 border-t border-gray-100 pt-6">
                <Text className="text-lg font-bold text-gray-900">The Plan</Text>
                <Text className="mt-2 text-base leading-6 text-gray-600">{event.description}</Text>
            </View>
        </View>
      </ScrollView>

      {/* Sticky Bottom Action */}
      <View className="border-t border-gray-200 bg-white p-5 pb-8 shadow-lg">
        <View className="mb-3 flex-row justify-between">
            <Text className="text-gray-500">Interest Level</Text>
            <Text className="font-bold text-gray-900">{event.currentRsvps} / {event.threshold}</Text>
        </View>
        {/* Progress Bar */}
        <View className="mb-5 h-2 w-full overflow-hidden rounded-full bg-gray-200">
             <View 
                className={`h-full rounded-full ${isConfirmed ? 'bg-success' : 'bg-primary'}`} 
                style={{ width: `${Math.min((event.currentRsvps / event.threshold) * 100, 100)}%` }} 
             />
        </View>

        <TouchableOpacity
            onPress={handleRSVP}
            className={`h-14 items-center justify-center rounded-xl ${
                event.userHasRsvped 
                ? 'bg-gray-200' 
                : 'bg-primary'
            }`}
        >
            <Text className={`text-lg font-bold ${event.userHasRsvped ? 'text-gray-600' : 'text-white'}`}>
                {event.userHasRsvped ? 'Count me out' : 'I\'m Interested'}
            </Text>
        </TouchableOpacity>
        <Text className="mt-2 text-center text-xs text-gray-400">
            {event.userHasRsvped 
                ? "You're on the list. We'll notify you if it happens." 
                : "Expressing interest is not visible until confirmed."}
        </Text>
      </View>
    </View>
  );
}
```

### src/screens/CreateEventScreen.tsx
```typescript
import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Users, Calendar, MapPin, AlignLeft } from 'lucide-react-native';

import { useAppStore } from '../store';

export default function CreateEventScreen() {
  const navigation = useNavigation();
  const { addEvent } = useAppStore();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [threshold, setThreshold] = useState('3');
  const [dateString, setDateString] = useState(''); // Simplified for demo

  const handleCreate = () => {
    if (!title || !threshold) {
        Alert.alert("Missing Details", "Please provide at least a Title and a Threshold.");
        return;
    }

    addEvent({
        title,
        description: description || 'No description provided.',
        location: location || 'TBD',
        date: new Date(), // Defaults to now for demo simplicity
        hostId: 'me',
        hostName: 'Me',
        threshold: parseInt(threshold),
    });

    navigation.goBack();
  };

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'} 
      className="flex-1 bg-white"
    >
      <ScrollView className="flex-1 px-6 pt-6">
        <Text className="mb-6 text-2xl font-bold text-gray-900">Design Your Night</Text>

        {/* Title Input */}
        <View className="mb-6">
            <Text className="mb-2 text-sm font-bold text-gray-500">WHAT ARE WE DOING?</Text>
            <TextInput
                className="rounded-xl bg-gray-50 p-4 text-lg text-gray-900 border border-gray-100"
                placeholder="e.g. Sushi & Karaoke"
                value={title}
                onChangeText={setTitle}
            />
        </View>

        {/* Threshold Input - The Core Feature */}
        <View className="mb-6 rounded-xl border-2 border-primary/20 bg-primary/5 p-5">
            <View className="flex-row items-center justify-between">
                <View className="flex-1">
                    <Text className="text-lg font-bold text-primary">The Threshold</Text>
                    <Text className="text-xs text-gray-500">How many people need to say YES for this to happen?</Text>
                </View>
                <View className="flex-row items-center rounded-lg bg-white px-4 py-2 shadow-sm">
                    <Users size={20} color="#6366f1" />
                    <TextInput
                        className="ml-2 w-10 text-center text-xl font-bold text-gray-900"
                        keyboardType="numeric"
                        value={threshold}
                        onChangeText={setThreshold}
                    />
                </View>
            </View>
        </View>

        {/* Details */}
        <View className="space-y-4">
            <View className="flex-row items-center rounded-xl bg-gray-50 p-3">
                <MapPin size={20} color="#9ca3af" />
                <TextInput
                    className="flex-1 ml-3 text-gray-900"
                    placeholder="Location (Optional)"
                    value={location}
                    onChangeText={setLocation}
                />
            </View>
            
            <View className="flex-row items-center rounded-xl bg-gray-50 p-3">
                <Calendar size={20} color="#9ca3af" />
                <TextInput
                    className="flex-1 ml-3 text-gray-900"
                    placeholder="When? (e.g. Tomorrow 8pm)"
                    value={dateString}
                    onChangeText={setDateString}
                />
            </View>

            <View className="flex-row items-start rounded-xl bg-gray-50 p-3">
                <AlignLeft size={20} color="#9ca3af" className="mt-1" />
                <TextInput
                    className="flex-1 ml-3 text-gray-900 min-h-[100px]"
                    placeholder="Add details, links, or vibes..."
                    multiline
                    textAlignVertical="top"
                    value={description}
                    onChangeText={setDescription}
                />
            </View>
        </View>

      </ScrollView>

      <View className="p-6 border-t border-gray-100">
        <TouchableOpacity 
            onPress={handleCreate}
            className="h-14 items-center justify-center rounded-xl bg-gray-900 shadow-lg"
        >
            <Text className="text-lg font-bold text-white">Throw it out there</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}
```

### App.tsx
```typescript
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { AppProvider } from './src/store';
import { RootStackParamList } from './src/types';

import HomeScreen from './src/screens/HomeScreen';
import CreateEventScreen from './src/screens/CreateEventScreen';
import EventDetailsScreen from './src/screens/EventDetailsScreen';

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function App() {
  return (
    <SafeAreaProvider>
      <AppProvider>
        <NavigationContainer>
          <Stack.Navigator 
            initialRouteName="Home"
            screenOptions={{
              headerShown: false,
              contentStyle: { backgroundColor: '#fff' }
            }}
          >
            <Stack.Screen name="Home" component={HomeScreen} />
            <Stack.Screen 
              name="CreateEvent" 
              component={CreateEventScreen} 
              options={{ presentation: 'modal' }} // iOS modal animation
            />
            <Stack.Screen 
              name="EventDetails" 
              component={EventDetailsScreen}
              options={{ headerShown: true, title: '', headerTransparent: true }} 
            />
          </Stack.Navigator>
        </NavigationContainer>
      </AppProvider>
    </SafeAreaProvider>
  );
}
```
