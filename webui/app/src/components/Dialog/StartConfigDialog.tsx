import React, { Fragment, SetStateAction, useCallback, useEffect, useRef, useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog, { DialogProps } from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import Switch from '@mui/material/Switch';
import { AudioDeviceItem, AudioDeviceResponse, queryAudioDeviceList, queryServiceState, backend_send_command, ServiceStateType, frontend_record_service } from '../../services/api';
import { useDispatch } from 'react-redux';
import changeDevice from '../../fetures/audioDeviceStatus/audioDeviceStatusAction';

interface StartConfigDialogProps extends DialogProps {
    // custom props
};

const defaultDeviceValue = 'AUTO';
const defaultDeviceInfoOption = new AudioDeviceItem(defaultDeviceValue);

const StartConfigDialog = ({ open, onClose }: StartConfigDialogProps) => {
    const [maxWidth, setMaxWidth] = useState<DialogProps['maxWidth']>('sm');
    // const [open, setOpen] = useState(prop.open);
    const fetched = useRef(false);
    const dispatch = useDispatch();

    const [device, setDevice] = useState(defaultDeviceValue);
    const [deviceList, setDeviceList] = useState<AudioDeviceItem[]>([defaultDeviceInfoOption]);

    const handleDeviceChange = (event: { target: { value: SetStateAction<string>; }; }) => {
        setDevice(event.target.value);
        changeDevice(dispatch, event.target.value.toString());
    };

    const onLaunch = useCallback(() => {
        const selectedIndex = deviceList.findIndex((item) => {
            return item.name === device;
        });
        if (selectedIndex < 0) {
            console.log("launch with config: " + defaultDeviceValue + " idx: undefined");
        } else {
            console.log("launch with config: " + deviceList[selectedIndex].name + " idx: " + deviceList[selectedIndex].index);
        }
        // first, start backend service
        // seconds, start front service
        // TODO: ui loading for service launching.
        backend_send_command("start").then(async (msg) => {
            console.log("backend send command finished. " + msg);
            const param = {
                'cmd': 'start',
                'deviceIndex': deviceList[selectedIndex].index,
            };
            console.log("frontend record service params: " + param);
            await frontend_record_service(param.cmd, param.deviceIndex);
        });
    }, [device, deviceList]);

    const onDismiss = useCallback(() => {
        if (onClose) {
            onClose({}, "backdropClick");
        }
    }, [onClose]);

    useEffect(() => {
        if (!open) {
            return;
        }
        queryAudioDeviceList().then((result: AudioDeviceResponse) => {
            console.log(result.itemRecords);
            setDeviceList([defaultDeviceInfoOption, ...result.itemRecords]);
        });
    }, [open]);

    return (
        <Fragment>
            <Dialog
                fullWidth={true}
                maxWidth={maxWidth}
                open={open}
                onClose={onClose}
            >
                <DialogTitle>Start RTS2T Service</DialogTitle>
                <DialogContent dividers>
                    <DialogContentText>Select the target audio device.</DialogContentText>
                    <Box
                        noValidate
                        component="form"
                        sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            m: 'auto',
                            // width: 'fit-content',
                        }}
                    >
                        <FormControl sx={{
                            mt: 2,
                            minWidth: 180,
                            width: 'auto',
                            whiteSpace: 'nowrap',
                        }}>
                            <InputLabel htmlFor="device-index">Device</InputLabel>
                            <Select
                                autoFocus
                                value={device}
                                onChange={handleDeviceChange}
                                label="Device"
                                // inputProps={{
                                //     name: 'device-index',
                                //     id: 'device-index',
                                // }}
                            >
                                {deviceList.map((device, index) => (
                                    <MenuItem key={'device-' + index.toString()} value={device.name}>{device.name}</MenuItem>
                                ))}
                            </Select>
                        </FormControl>

                        <DialogContentText sx={{ mt: 2, }}>TODO: Features setting</DialogContentText>
                        <FormControlLabel
                            sx={{ mt: 1 }}
                            control={
                                <Switch disabled={true} checked={true} onChange={undefined} />
                            }
                            label="Translate service"
                        />
                        <FormControlLabel
                            sx={{ mt: 1 }}
                            control={
                                <Switch disabled={true} checked={true} onChange={undefined} />
                            }
                            label="Assistant service"
                        />
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={onDismiss}>Dismiss</Button>
                    <Button onClick={onLaunch}>Launch</Button>
                </DialogActions>
            </Dialog>
        </Fragment>
    );
};

// StartConfigDialog.propTypes = {
//     open: PropTypes.bool.isRequired,
//     onClose: PropTypes.func.isRequired
// };

export default StartConfigDialog;