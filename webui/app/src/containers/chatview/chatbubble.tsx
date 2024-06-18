import React from 'react';
import { Box, Typography, Paper, Divider } from '@mui/material';

interface IChatBubble {
    text: string
    isOwnMessage: boolean
    subtext: string | null
};

const ChatBubble: React.FC<IChatBubble> = ({ text, isOwnMessage, subtext }) => {
    return (
        <Box
            sx={{
                display: 'flex',
                justifyContent: isOwnMessage ? 'flex-end' : 'flex-start',
                mb: 1.5,
            }}
        >

            <Paper
                elevation={3}
                sx={{
                    bgcolor: isOwnMessage ? 'lightgreen' : 'lightgray',
                    p: 1.5,
                    width: '99%',
                    display: 'inline-block',
                }}
            >
                <Box
                    display="flex"
                    justifyContent="space-between"
                >
                    <Typography variant="body1"
                        paddingRight={2}
                        flex={1}
                        textAlign="left"
                    >
                        {text.split('\n').map((line, index) => (
                            <div key={"original"+index.toString()}>{line}</div>
                        ))}
                    </Typography>
                    <Divider orientation='vertical' flexItem />
                    <Typography variant="body1"
                        paddingLeft={2}
                        flex={1} textAlign="left"
                    >
                        {subtext && subtext.split('\n').map((line, index) => (
                            <div key={"translate"+index.toString()}>{line}</div>
                        ))}
                    </Typography>
                </Box>
            </Paper>
        </Box>
    );
};

export default ChatBubble;