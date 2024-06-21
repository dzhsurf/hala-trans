import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../../../app/store';
import { Box, Grid, Paper } from '@mui/material';
// import MarkdownPanel from '../../../containers/markdown/markdown';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const EventStreamAssistantView: React.FC = () => {
    // const dispatch = useDispatch();
    const assistantMessages = useSelector((state: RootState) => state.eventStream.assistantMessages);
    const [assistantContent, setAssistantContent] = useState<string[]>([]);

    useEffect(() => {
        setAssistantContent((_) => {
            return assistantMessages;
        });
    }, [assistantMessages]);

    return (
        <Box
            sx={{
                height: 'calc(100vh - 96px)',
                overflowY: 'auto',
                p: 0,
                display: 'flex',
                flexGrow: 1,
                flexDirection: 'column',
            }}
        >
            {assistantContent.map((item, index) => (
                <Box key={"md-" + index.toString()} sx={{ p: 1.5, }}>
                    <Paper
                        elevation={3}
                        sx={{
                            bgcolor: '#dedede',
                            p: 2,
                            width: '100%',
                        }}
                    >
                        <div className='markdown'>
                            <Markdown children={item} remarkPlugins={[remarkGfm]} />
                        </div>
                    </Paper>
                </Box>
            ))}
        </Box>
    );
};

export default EventStreamAssistantView;