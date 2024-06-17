import React, { useEffect, useRef, useState } from 'react';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import { send_command } from '../../services/api';

type ServiceStateType = "" | "Running";

export default function MyAppBar() {

    const [serviceState, setServiceState] = useState<ServiceStateType>("");
    const onStartButtonClick = async (): Promise<void> => {
        console.log('---- start');
        const ret = await send_command("start");
        if (ret === "ok") {
            setServiceState("Running");
        } else {
            console.error(ret);
        }
    };
    const onStopButtonClick = async (): Promise<void> => {
        console.log('---- stop');
        const ret = await send_command("stop");
        if (ret === "ok") {
            setServiceState("");
        } else {
            console.error(ret);
        }
    };

    useEffect(() => {
        // console.log(serviceState);
        // setServiceState("Running");
        // console.log(serviceState);
    }, []);

    return (
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
            </Toolbar>
        </AppBar>
    );
}