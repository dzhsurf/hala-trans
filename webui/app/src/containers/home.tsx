import React, { useCallback, useEffect, useRef } from 'react';
import { Grid, Box } from '@mui/material';
import EventStreamTranscriptionView from '../fetures/eventStream/components/EventStreamTranscriptionView';
import EventStreamAssistantView from '../fetures/eventStream/components/EventStreamAssistantView';
import { useDispatch } from 'react-redux';
import { startEventStream } from '../fetures/eventStream/eventStreamActions';
import { store } from '../app/store';

const Home: React.FC = () => {
    const dispatch = useDispatch();
    const fetched = useRef(false);

    const handleFetch = useCallback(async () => {
        const startAsyncThunk = startEventStream();
        const extra = {};
        const p = await startAsyncThunk(dispatch, store.getState, extra);
        // setTimeout(() => {
        //     (p.payload as AbortController).abort("hi");
        // }, 10000);
    }, [dispatch]);

    useEffect(() => {
        if (fetched.current) {
            return;
        }
        fetched.current = true;
        handleFetch();
    }, []);

    return (
        <Box sx={{ display: 'flex', flexGrow: 1 }}>
            <Grid container spacing={0} sx={{ flex: 1 }}>
                <Grid item xs={6} sx={{ backgroundColor: '#e3e3e3' }}>
                    <EventStreamTranscriptionView />
                </Grid>
                <Grid item xs={6} sx={{ backgroundColor: '#efefef', p: 1, }}>
                    <EventStreamAssistantView />
                </Grid>
            </Grid>
        </Box>
    );
};

export default Home;