import React from 'react';
import { Grid, Box } from '@mui/material';
import ChatView from './chatview/chatview';
import MarkdownPanel from './markdown/markdown';

const Home: React.FC = () => {
    return (
        <Box sx={{ display: 'flex', flexGrow: 1 }}>
            <Grid container spacing={0} sx={{ flex: 1 }}>
                <Grid item xs={6} sx={{ backgroundColor: 'lightblue' }}>
                    <ChatView />
                </Grid>
                <Grid item xs={6} sx={{ backgroundColor: 'lightgreen' }}>
                    <MarkdownPanel content='Hi' />
                </Grid>
            </Grid>
        </Box>
    );
};

export default Home;