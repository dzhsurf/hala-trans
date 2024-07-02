import { configureStore } from "@reduxjs/toolkit";
import eventStreamReducer from "../fetures/eventStream/eventStreamSlice";
import audioDeviceStatusReducer from "../fetures/audioDeviceStatus/audioDeviceStatusSlice";

export const store = configureStore({
    reducer: {
        eventStream: eventStreamReducer,
        audioDeviceStatus: audioDeviceStatusReducer,
    },
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({
            serializableCheck: {
                // Ignore these action types
                ignoredActions: ['eventStream/start/fulfilled',],
                // Ignore these field paths in all actions
                // ignoredActionPaths: ['meta.arg', 'payload.timestamp'],
                // Ignore these paths in the state
                ignoredPaths: ['eventStream.abort'],
            },
        }),
});


export type RootState = ReturnType<typeof store.getState>;

export type AppDispatch = typeof store.dispatch;