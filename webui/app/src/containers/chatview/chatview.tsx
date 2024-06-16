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

                    // if (data.item.status === 'PROCESS_TEXT_STATUS.ASSISTANT') {
                    //     console.log("ASSISTANT: " + data.item.text);
                    //     // setAssistantContent((prevStr: string) => {
                    //     //   return data.item.texts.join("\n");
                    //     // });
                    //     return false;
                    // }

                    // const itemExists = prevMessages.some(item => (item.msgid === data.item!.msgid));
                    // if (itemExists) {
                    //     return prevMessages.map(msgItem => {
                    //         if (msgItem.msgid === data.item!.msgid) {
                    //             return {
                    //                 ...msgItem,
                    //                 status: data.item!.status,
                    //                 text: data.item!.text,
                    //                 translation: data.item!.translation,
                    //             };
                    //         }
                    //         return msgItem;
                    //     });
                    // } else {
                    //     return [data.item!, ...prevMessages];
                    // }
                    // return false;
                });
        };

        fetchData();
        // setMessages([
        //     { msgid: "1", text: "Hello, how are you?", status: "other", translation: null },
        //     { msgid: "2", text: "I am fine, thank you! How about you?", status: "me", translation: null },
        //     { msgid: "3", text: "I'm good too, thanks for asking!", status: "other", translation: null },
        //     { msgid: "4", text: "Great to hear that!", status: "other", translation: null },
        //     { msgid: "5", text: "Great to hear that!", status: "other", translation: null },
        //     { msgid: "6", text: "Great to hear that!", status: "other", translation: null },
        //     { msgid: "7", text: "Great to hear that!", status: "other", translation: null },
        //     { msgid: "8", text: "Great to hear that!", status: "other", translation: null },
        //     { msgid: "9", text: "Great to hear that!", status: "other", translation: null },
        //     { msgid: "10", text: "Great to hear that!", status: "other", translation: null },
        //     { msgid: "11", text: "Great to hear that!", status: "other", translation: null },
        //     { msgid: "12", text: "Great to hear that!", status: "other", translation: null },
        //     { msgid: "13", text: "Great to hear that!", status: "other", translation: null },
        //     { msgid: "14", text: "Great to hear that!", status: "other", translation: null },
        //     { msgid: "15", text: "Great to hear that!", status: "other", translation: null },
        // ])
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
                            updatedMessages[itemIndex] = {
                                ...updatedMessages[itemIndex],
                                status: newItem.status,
                                text: newItem.text,
                                translation: newItem.translation,
                            };
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