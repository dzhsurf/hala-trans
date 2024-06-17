import React, { useEffect, useRef, useState } from 'react';
import { Box } from '@mui/material';
import ChatBubble from './chatbubble';
import connectServer from '../../services/api';

interface ChatBubbleProp {
    msgid: string
    status: string
    text: string
    translation: string | null
};

interface StreamingEventItem {
    item: ChatBubbleProp | null
};

const ChatWindow = () => {

    const [messages, setMessages] = useState<ChatBubbleProp[]>([]);
    // const [assistantContent, setAssistantContent] = useState<string>("");
    const fetched = useRef(false);
    const cacheData: React.MutableRefObject<ChatBubbleProp[]> = useRef([]);
    const intervalRef: React.MutableRefObject<any> = useRef(null);

    useEffect(() => {
        const fetchData = async (): Promise<void> => {
            if (fetched.current) {
                return;
            }
            fetched.current = true;

            const server = 'http://localhost:8000/api/streaming';

            connectServer<StreamingEventItem>(server,
                (data: StreamingEventItem): boolean => {
                    if (data.item == null || data.item.text.length === 0) {
                        // console.log('No event');
                        return false;
                    }

                    cacheData.current.push(data.item);
                    return false;
                });
        };

        fetchData();
    }, []);

    useEffect(() => {
        intervalRef.current = setInterval(() => {
            if (cacheData.current.length > 0) {
                const bulkData = [...cacheData.current];
                // setDisplayData(prevData => [...prevData, ...bulkData]);

                setMessages((prevMessages: ChatBubbleProp[]): ChatBubbleProp[] => {
                    const updatedMessages = [...prevMessages];

                    bulkData.forEach(newItem => {
                        const itemIndex = updatedMessages.findIndex(msgItem => msgItem.msgid === newItem.msgid);
                        if (itemIndex !== -1) {
                            // If message already exist.
                            if (newItem.status === "partial") {
                                updatedMessages[itemIndex] = {
                                    ...updatedMessages[itemIndex],
                                    status: newItem.status,
                                    text: newItem.text,
                                    translation: updatedMessages[itemIndex].translation,
                                };
                            } else if (newItem.status === "fulltext") {
                                updatedMessages[itemIndex] = {
                                    ...updatedMessages[itemIndex],
                                    status: newItem.status,
                                    text: newItem.text,
                                    translation: updatedMessages[itemIndex].translation,
                                };
                            } else if (newItem.status === "translating") {
                                updatedMessages[itemIndex] = {
                                    ...updatedMessages[itemIndex],
                                    translation: newItem.translation,
                                };
                            } else if (newItem.status === "translate") {
                                updatedMessages[itemIndex] = {
                                    ...updatedMessages[itemIndex],
                                    status: newItem.status,
                                    text: newItem.text,
                                    translation: newItem.translation,
                                };
                            } else {
                                console.log("unknow status " + newItem.status);
                            }
                        } else {
                            // If message not exist, add new item.
                            updatedMessages.unshift(newItem);
                        }
                    });

                    return updatedMessages;
                });


                cacheData.current = [];
            }
        }, 500);
    }, []);

    return (
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
            {messages.map((message) => (
                <ChatBubble
                    key={message.msgid}
                    text={message.text}
                    isOwnMessage={message.status === "me"}
                    subtext={message.translation}
                />
            ))}
        </Box>
    );
};

const ChatView: React.FC = () => {
    return (
        <Box p={2}>
            {/* <h3>Audio input:</h3> */}
            <ChatWindow />
        </Box>
    );
};

export default ChatView;