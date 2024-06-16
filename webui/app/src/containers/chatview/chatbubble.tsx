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
                    maxWidth: '90%',
                    display: 'inline-block',
                }}
            >
                <Box
                    display="flex"
                    justifyContent="space-between"
                >
                    <Typography variant="body1"
                        paddingRight={subtext ? 2 : 0}
                        flex={1}
                        textAlign="left"
                    >
                        {text}
                    </Typography>
                    {subtext &&
                        <>
                            <Divider orientation='vertical' flexItem />
                            <Typography variant="body1"
                                paddingLeft={2}
                                flex={1} textAlign="left"
                            >
                                {subtext}
                            </Typography>
                        </>
                    }
                </Box>
            </Paper>
        </Box>
    );
};

export default ChatBubble;