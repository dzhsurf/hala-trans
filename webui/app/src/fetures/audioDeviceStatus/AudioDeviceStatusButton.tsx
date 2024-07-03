import Button from "@mui/material/Button";
import VolumeUpIcon from '@mui/icons-material/VolumeUp';
import { useSelector } from "react-redux";
import { RootState } from "../../app/store";
import { useCallback, useEffect, useState } from "react";

const AudioDeviceStatusButton: React.FC = () => {
    const currentDevice = useSelector((state: RootState) => state.audioDeviceStatus.currentDevice);
    const [deviceName, setDeviceName] = useState('DEVICE');

    const handleUpdate = useCallback(() => {
        setDeviceName(currentDevice);
    }, [currentDevice]);

    useEffect(() => {
        handleUpdate();
    }, [handleUpdate]);
    
    return (
        <Button
            size="medium"
            startIcon={<VolumeUpIcon></VolumeUpIcon>}
            color="inherit"
            >
                {deviceName}
        </Button>
    );
};

export default AudioDeviceStatusButton;