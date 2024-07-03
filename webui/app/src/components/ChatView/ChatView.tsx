import React from 'react';
import { Box } from '@mui/material';
import ChatBubble from './ChatBubble';

export interface ChatMessage {
    msgid: string;
    status: string;
    text: string;
    translation?: string;
};

interface ChatViewProps {
    items: ChatMessage[];
};

const ChatWindow = ({ items }: ChatViewProps) => {

    return (
        <Box p={2}>
            <Box
                sx={{
                    height: 'calc(100vh - 96px)',
                    overflowY: 'auto',
                    p: 1,
                    display: 'flex',
                    flexGrow: 1,
                    flexDirection: 'column',
                }}
            >
                {items.map((message) => (
                    <ChatBubble
                        key={message.msgid}
                        text={message.text}
                        isOwnMessage={message.status === "me"}
                        subtext={message.translation}
                    />
                ))}
            </Box>
        </Box>
    );
};

const ChatView: React.FC<ChatViewProps> = ({ items }) => {
    return (
        <ChatWindow
            items={items}
        />
    );
};

export default ChatView;