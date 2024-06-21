// import React, { useEffect, useRef, useState } from 'react';
// import { Box, Grid, Paper } from '@mui/material';
// import ChatBubble from './chatbubble';
// import connectServer from '../../services/api';
// import MarkdownPanel from '../markdown/markdown';

// interface ChatBubbleProp {
//     msgid: string
//     status: string
//     text: string
//     translation: string | null
// };

// interface AssistantItemProp {
//     text: string
// };

// interface StreamingEventItem {
//     item: ChatBubbleProp | null
//     assistant: AssistantItemProp | null
// };

// const ChatWindow = () => {

//     const [messages, setMessages] = useState<ChatBubbleProp[]>([]);
//     const [assistantContent, setAssistantContent] = useState<string[]>([]);
//     const fetched = useRef(false);

//     const fetched1 = useRef(false);
//     const cacheData: React.MutableRefObject<ChatBubbleProp[]> = useRef([]);
//     const intervalRef: React.MutableRefObject<any> = useRef(null);

//     useEffect(() => {
//         const fetchData = async (): Promise<void> => {
//             if (fetched.current) {
//                 return;
//             }
//             fetched.current = true;

//             const server = 'http://localhost:8000/api/streaming';

//             connectServer<StreamingEventItem>(server,
//                 (data: StreamingEventItem): boolean => {
//                     // assistant result
//                     if (data.assistant && data.assistant.text.length > 0) {
//                         setAssistantContent((prevItems: string[]) => {
//                             const text = data.assistant!.text;
//                             return [text, ...prevItems];
//                         });
//                         return false;
//                     }

//                     // transcribe result
//                     if (data && data.item && data.item!.text.length > 0) {
//                         cacheData.current.push(data.item!);
//                     }

//                     return false;
//                 });
//         };

//         fetchData();
//     }, []);

//     // interval update message
//     useEffect(() => {
//         if (fetched1.current) {
//             return;
//         }
//         fetched1.current = true;

//         intervalRef.current = setInterval(() => {
//             if (cacheData.current.length > 0) {
//                 const bulkData = [...cacheData.current];
//                 // setDisplayData(prevData => [...prevData, ...bulkData]);

//                 setMessages((prevMessages: ChatBubbleProp[]): ChatBubbleProp[] => {
//                     const updatedMessages = [...prevMessages];

//                     bulkData.forEach(newItem => {
//                         const itemIndex = updatedMessages.findIndex(msgItem => msgItem.msgid === newItem.msgid);
//                         if (itemIndex !== -1) {
//                             // If message already exist.
//                             if (newItem.status === "partial") {
//                                 updatedMessages[itemIndex] = {
//                                     ...updatedMessages[itemIndex],
//                                     status: newItem.status,
//                                     text: newItem.text,
//                                     translation: updatedMessages[itemIndex].translation,
//                                 };
//                             } else if (newItem.status === "fulltext") {
//                                 updatedMessages[itemIndex] = {
//                                     ...updatedMessages[itemIndex],
//                                     status: newItem.status,
//                                     text: newItem.text,
//                                     translation: updatedMessages[itemIndex].translation,
//                                 };
//                             } else if (newItem.status === "translating") {
//                                 updatedMessages[itemIndex] = {
//                                     ...updatedMessages[itemIndex],
//                                     translation: newItem.translation,
//                                 };
//                             } else if (newItem.status === "translate") {
//                                 updatedMessages[itemIndex] = {
//                                     ...updatedMessages[itemIndex],
//                                     status: newItem.status,
//                                     text: newItem.text,
//                                     translation: newItem.translation,
//                                 };
//                             } else {
//                                 console.log("unknow status " + newItem.status);
//                             }
//                         } else {
//                             // If message not exist, add new item.
//                             updatedMessages.unshift(newItem);
//                         }
//                     });

//                     return updatedMessages;
//                 });


//                 cacheData.current = [];
//             }
//         }, 500);
//     }, []);

//     return (
//         <>
//             <Grid item xs={6} sx={{ backgroundColor: '#e3e3e3' }}>
//                 <Box p={2}>
//                     <Box
//                         sx={{
//                             height: 'calc(100vh - 96px)',
//                             overflowY: 'auto',
//                             p: 1,
//                             display: 'flex',
//                             flexGrow: 1,
//                             flexDirection: 'column',
//                         }}
//                     >
//                         {messages.map((message) => (
//                             <ChatBubble
//                                 key={message.msgid}
//                                 text={message.text}
//                                 isOwnMessage={message.status === "me"}
//                                 subtext={message.translation}
//                             />
//                         ))}
//                     </Box>
//                 </Box>
//             </Grid>
//             <Grid item xs={6} sx={{ backgroundColor: '#efefef', p: 1, }}>
//                 <Box
//                     sx={{
//                         height: 'calc(100vh - 96px)',
//                         overflowY: 'auto',
//                         p: 0,
//                         display: 'flex',
//                         flexGrow: 1,
//                         flexDirection: 'column',
//                     }}
//                 >
//                     {assistantContent.map((item, index) => (
//                         <Box sx={{ p: 1.5, }}>
//                             <Paper key={"md-" + index.toString()}
//                                 elevation={3}
//                                 sx={{
//                                     bgcolor: '#dedede',
//                                     p: 0,
//                                     width: '100%',
//                                 }}
//                             >
//                                 <MarkdownPanel content={item} />
//                             </Paper>
//                         </Box>
//                     ))}
//                 </Box>
//             </Grid>
//         </>
//     );
// };

// const ChatView: React.FC = () => {
//     return (
//         <ChatWindow />
//     );
// };

// export default ChatView;

export default () => {};