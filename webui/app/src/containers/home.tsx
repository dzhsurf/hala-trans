import React from 'react';
import { Grid, Box } from '@mui/material';
import ChatView from './chatview/chatview';

const Home: React.FC = () => {



    return (
        <Box sx={{ display: 'flex', flexGrow: 1 }}>
            <Grid container spacing={0} sx={{ flex: 1 }}>
                <ChatView />
            </Grid>
        </Box>
    );
};

export default Home;