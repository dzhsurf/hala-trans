import React, { useCallback, useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '@app/store';
import ChatView, { ChatMessage } from '@components/ChatView/ChatView';


const EventStreamTranscriptionView: React.FC = () => {

    const audioMessages = useSelector((state: RootState) => state.eventStream.audioMessages);
    const [messages, setMessages] = useState<ChatMessage[]>([]);

    const updateUI = useCallback(() => {
        setMessages((prevItems) => {
            return audioMessages;
        });
    }, [audioMessages]);

    useEffect(() => {
        updateUI();
    }, [updateUI]);

    return (
        <ChatView
            items={messages}
        />
    );
};

export default EventStreamTranscriptionView;