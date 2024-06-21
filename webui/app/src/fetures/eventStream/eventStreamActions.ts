import { createAsyncThunk } from '@reduxjs/toolkit';
import { eventStreamSlice } from './eventStreamSlice';
import { AppDispatch, RootState } from '../../app/store';
import connectDataStreamingServer, { OnErrorCallback, OnReceiveDataCallback } from '../../services/api';
import { ChatMessage } from '../../components/ChatView/ChatView';

interface StreamEventItemAssistant {
    text: string
};

interface StreamingEventItem {
    item?: ChatMessage
    assistant?: StreamEventItemAssistant
};

export const startEventStream = createAsyncThunk<
    AbortController,     // return type
    void,     // parame
    { state: RootState; dispatch: AppDispatch; }>(
        'eventStream/start',
        async (_, { dispatch, getState, signal }) => {
            const controller = new AbortController();

            setTimeout(async () => {
                try {

                    const onErrorCallback: OnErrorCallback = (error): boolean => {
                        console.error(error);
                        return false;
                    };

                    const onReceiveDataCallback: OnReceiveDataCallback<StreamingEventItem> =
                        (data: StreamingEventItem): boolean => {
                            // assistant result
                            if (data.assistant && data.assistant.text.length > 0) {
                                dispatch(eventStreamSlice.actions.receiveAssistantMessage(data.assistant.text));
                                return false;
                            }

                            // transcribe result
                            if (data && data.item && data.item!.text.length > 0) {
                                dispatch(eventStreamSlice.actions.receiveAudioMessage(data.item!));
                                return false;
                            }

                            if (data) {
                                dispatch(eventStreamSlice.actions.notifyRefreshCache());
                            }

                            return false;
                        };

                    // const stream = await initiateDataStream(controller);
                    await connectDataStreamingServer<StreamingEventItem>(
                        "http://localhost:8000/api/streaming",
                        controller,
                        onReceiveDataCallback,
                        onErrorCallback);

                    console.log(signal.aborted);
                } catch (error) {
                    if (!signal.aborted) {
                        // dispatch(dataStreamError(error));
                    }
                } finally {
                    controller.abort();
                }
            }, 10);

            return controller;
        }
    );

