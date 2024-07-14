import React, { useEffect, useRef, useState, useCallback } from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import TerminalIcon from '@mui/icons-material/Terminal';
import { backend_send_command, queryServiceState } from '@services/api';
import StartConfigDialogComponent from '@components/Dialog/StartConfigDialog';
import AudioDeviceStatusButton from '@features/audioDeviceStatus/AudioDeviceStatusButton';
 
type ServiceStateType = "" | "Running";

export default function MyAppBar() {
    const [serviceState, setServiceState] = useState<ServiceStateType>("");
    const fetched = useRef(false);

    const [open, setOpen] = React.useState(false);

    const onStartButtonClick = useCallback(async (): Promise<void> => {
        setOpen(true);
    }, []);

    const onStopButtonClick = useCallback(async (): Promise<void> => {
        const ret = await backend_send_command("stop");
        if (ret === "ok") {
            setServiceState("");
        } else {
            console.error(ret);
        }
    }, []);

    useEffect(() => {
        if (fetched.current) {
            return;
        }
        fetched.current = true;

        const fetchServiceState = async (): Promise<void> => {
            const state = await queryServiceState();
            setServiceState(state.runningState);
            const waitTime = 5000 + ((state.error) ? 10000 : 0);
            setTimeout(async () => {
                await fetchServiceState();
            }, waitTime);
        };

        fetchServiceState();
    }, []);

    return (
        <React.Fragment>

            <AppBar position="static">
                <Toolbar>
                    <IconButton
                        size="large"
                        edge="start"
                        color="inherit"
                        aria-label="menu"
                        sx={{ mr: 2 }}
                    >
                        <MenuIcon />
                    </IconButton>
                    <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                        Realtime Translate Assistant
                    </Typography>
                    <AudioDeviceStatusButton />
                    <Button
                        disabled={serviceState === "" ? false : true}
                        size="medium"
                        startIcon={<PlayArrowIcon></PlayArrowIcon>}
                        color="inherit"
                        onClick={onStartButtonClick}
                    >
                        Start
                    </Button>
                    <Button
                        disabled={serviceState === "Running" ? false : true}
                        size="medium"
                        startIcon={<StopIcon></StopIcon>}
                        color="inherit"
                        onClick={onStopButtonClick}
                    >
                        Stop
                    </Button>
                    <Button
                        disabled={false}
                        size="medium"
                        startIcon={<TerminalIcon></TerminalIcon>}
                        color="inherit"
                        onClick={undefined}
                    >
                        Console
                    </Button>
                </Toolbar>
            </AppBar>
            <StartConfigDialogComponent
                open={open}
                onClose={() => {
                    return setOpen(false);
                }}
                onDone={() => {
                    setOpen(false);
                }}
            />
        </React.Fragment>
    );
}