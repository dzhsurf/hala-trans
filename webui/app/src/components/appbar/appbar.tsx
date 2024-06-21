import React, { useEffect, useRef, useState, useCallback } from 'react';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import VolumeUpIcon from '@mui/icons-material/VolumeUp';
import { query_service_state, send_command } from '../../services/api';
import AudioDevicePicker from '../AudioDevicePicker/AudioDevicePicker';
import StartConfigDialogComponent from '../Dialog/StartConfigDialog';

type ServiceStateType = "" | "Running";

interface IDeviceInfo {
    name: string
    index: number
};

export default function MyAppBar() {
    const [deviceInfo, setDeviceInfo] = useState<IDeviceInfo | null>(null);
    const [serviceState, setServiceState] = useState<ServiceStateType>("");
    const fetched = useRef(false);

    const [open, setOpen] = React.useState(false);

    const onStartButtonClick = useCallback(async (): Promise<void> => {
        const ret = await send_command("start");
        // setOpen(true);
        // console.log('---------');
        // return;
        // const ret: string = "";
        if (ret === "ok") {
            setServiceState("Running");
        } else {
            console.error(ret);
        }
    }, []);

    const onStopButtonClick = useCallback(async (): Promise<void> => {
        const ret = await send_command("stop");
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

        const updateDeviceInfo = () => {
            setDeviceInfo(() => {
                return null;
                return { name: 'Device 4: Soundflower (2ch)', index: 2 } as IDeviceInfo;
            });
        };

        const fetchServiceState = async (): Promise<void> => {

            const state = await query_service_state();
            setServiceState(state);

            setTimeout(async () => {
                await fetchServiceState();
            }, 2000);
        };

        // updateDeviceInfo();
        // fetchServiceState();
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
                    <Button

                        size="medium"
                        startIcon={<VolumeUpIcon></VolumeUpIcon>}
                        color="inherit"
                    >
                        {deviceInfo && deviceInfo.name}
                        {!deviceInfo &&
                            'SELECT DEVICE'
                        }
                    </Button>
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
            <StartConfigDialogComponent
                open={open}
                onClose={() => {
                    return setOpen(false);
                }}
            />
        </React.Fragment>
    );
}