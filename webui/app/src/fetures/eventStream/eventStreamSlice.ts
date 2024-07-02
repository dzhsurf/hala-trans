import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { startEventStream } from './eventStreamActions';
import { ChatMessage } from '../../components/ChatView/ChatView';

export interface EventStreamState {
    audioMessages: ChatMessage[]
    cacheAudioMessages: ChatMessage[]
    audioLastUpdatedTime: number
    assistantMessages: string[]
    cacheAssistantMessages: string[]
    assistantLastUpdatedTime: number
    loading: boolean
    error: string | null
};

const initialState: EventStreamState = {
    audioMessages: [],
    cacheAudioMessages: [],
    audioLastUpdatedTime: 0,
    assistantMessages: [],
    cacheAssistantMessages: [],
    assistantLastUpdatedTime: 0,
    loading: false,
    error: null,
};

const MAX_BUFFER_SIZE = 50;
const UI_UPDATE_INTERVAL = 200; // milliseconds

const updateAudioMessages = (state: EventStreamState) => {
    // remove duplicate 
    const uniqueMessageList = (itemList: ChatMessage[]) => {
        const seenIds: Set<string> = new Set();
        const uniqueItemList = itemList
            .reverse()
            .filter((item) => {
                if (seenIds.has(item.msgid)) {
                    return false;
                } else {
                    seenIds.add(item.msgid);
                    return true;
                }
            })
            .reverse();
        return uniqueItemList;
    };
    const bulkData = uniqueMessageList([...state.cacheAudioMessages]);

    bulkData.forEach(newItem => {
        const itemIndex = state.audioMessages.findIndex(msgItem => msgItem.msgid === newItem.msgid);
        if (itemIndex !== -1) {
            // If message already exist.
            if (newItem.status === "partial") {
                state.audioMessages[itemIndex] = {
                    ...state.audioMessages[itemIndex],
                    status: newItem.status,
                    text: newItem.text,
                    translation: state.audioMessages[itemIndex].translation,
                };
            } else if (newItem.status === "fulltext") {
                state.audioMessages[itemIndex] = {
                    ...state.audioMessages[itemIndex],
                    status: newItem.status,
                    text: newItem.text,
                    translation: state.audioMessages[itemIndex].translation,
                };
            } else if (newItem.status === "translating") {
                state.audioMessages[itemIndex] = {
                    ...state.audioMessages[itemIndex],
                    translation: newItem.translation,
                };
            } else if (newItem.status === "translate") {
                state.audioMessages[itemIndex] = {
                    ...state.audioMessages[itemIndex],
                    status: newItem.status,
                    text: newItem.text,
                    translation: newItem.translation,
                };
            } else {
                console.log("unknow status " + newItem.status);
            }
        } else {
            // If message not exist, add new item.
            state.audioMessages.unshift(newItem);
        }
    });

    if (state.audioMessages.length > MAX_BUFFER_SIZE) {
        state.audioMessages = state.audioMessages.slice(0, MAX_BUFFER_SIZE);
    }

    state.cacheAudioMessages = [];
};

const updateAssistantMessages = (state: EventStreamState) => {

    if (state.cacheAssistantMessages.length >= MAX_BUFFER_SIZE) {
        state.cacheAssistantMessages.pop();
    }

    const data = [...state.cacheAssistantMessages, ...state.assistantMessages];
    state.assistantMessages = data.slice(0, MAX_BUFFER_SIZE);
    state.cacheAssistantMessages = [];
};

export const eventStreamSlice = createSlice({
    name: 'eventStream',
    initialState,
    reducers: {
        notifyRefreshCache: (state, action: PayloadAction<void>) => {
            const curr = new Date().getTime();

            const needUpdateAudioMessage = (curr - state.audioLastUpdatedTime >= 2 * UI_UPDATE_INTERVAL);
            if (needUpdateAudioMessage) {
                updateAudioMessages(state);
                state.audioLastUpdatedTime = curr;
            }

            const needUpdateAssistantMessage = (curr - state.assistantLastUpdatedTime >= 2 * UI_UPDATE_INTERVAL);
            if (needUpdateAssistantMessage) {
                updateAssistantMessages(state);
                state.assistantLastUpdatedTime = curr;
            }
        },
        receiveAudioMessage: (state, action: PayloadAction<ChatMessage>) => {

            // cache receive new messages
            state.cacheAudioMessages.unshift(action.payload);

            const curr = new Date().getTime();
            const needUpdate = (curr - state.audioLastUpdatedTime >= UI_UPDATE_INTERVAL);
            if (needUpdate) {
                updateAudioMessages(state);
                state.audioLastUpdatedTime = curr;
            }
        },
        receiveAssistantMessage: (state, action: PayloadAction<string>) => {
            state.cacheAssistantMessages.unshift(action.payload);

            const curr = new Date().getTime();
            const needUpdate = (curr - state.assistantLastUpdatedTime >= UI_UPDATE_INTERVAL);
            if (needUpdate) {
                updateAssistantMessages(state);
                state.assistantLastUpdatedTime = curr;
            }
        },
        stopEventStream: (state) => {
            state.loading = false;
        }
    },
    extraReducers: (builder) => {
        builder.addCase(startEventStream.pending, (state, action) => {
            console.log('Fetching pending: ' + state);
            state.loading = true;
            state.error = null;
        });
        builder.addCase(startEventStream.fulfilled, (state, action: PayloadAction<any>) => {
            console.log('Fetching fulfilled: ' + state + " action: " + action);
            state.loading = false;
            state.error = null;
        });
        builder.addCase(startEventStream.rejected, (state, action) => {
            console.log('Fetching rejected: ' + state + " action: " + action);
            state.loading = false;
            // state.error = action.error.error || 'Failed to start event stream';
            state.error = 'Failed to start event stream';
        });
    }
});

export const { receiveAudioMessage, receiveAssistantMessage, stopEventStream } = eventStreamSlice.actions;

export default eventStreamSlice.reducer;