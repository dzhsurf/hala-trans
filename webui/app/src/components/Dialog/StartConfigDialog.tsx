import React, { Fragment, SetStateAction, useEffect, useRef, useState } from 'react';
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
import PropTypes from 'prop-types';
import { AudioDeviceItem, AudioDeviceResponse, queryAudioDeviceList, queryServiceState, ServiceStateType } from '../../services/api';

interface StartConfigDialogProps extends DialogProps {
    // custom props
};

const defaultDeviceValue = 'AUTO';
const defaultDeviceInfoOption = new AudioDeviceItem(defaultDeviceValue);

const StartConfigDialog = ({ open, onClose }: StartConfigDialogProps) => {
    const [maxWidth, setMaxWidth] = useState<DialogProps['maxWidth']>('sm');
    // const [open, setOpen] = useState(prop.open);
    const fetched = useRef(false);
    const [device, setDevice] = useState(defaultDeviceValue);
    const handleDeviceChange = (event: { target: { value: SetStateAction<string>; }; }) => {
        setDevice(event.target.value);
    };

    const [deviceList, setDeviceList] = useState<AudioDeviceItem[]>([defaultDeviceInfoOption]);

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
                <DialogContent>
                    <DialogContentText>
                        You can set service config here.
                    </DialogContentText>
                    <Box
                        noValidate
                        component="form"
                        sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            m: 'auto',
                            width: 'fit-content',
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
                                inputProps={{
                                    name: 'device-index',
                                    id: 'device-index',
                                }}
                            >
                                {deviceList.map((device, index) => (
                                    <MenuItem value={device.name}>{device.name}</MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                        {/* <FormControlLabel
                            sx={{ mt: 1 }}
                            control={
                                <Switch checked={fullWidth} onChange={handleFullWidthChange} />
                            }
                            label="Full width"
                        /> */}
                    </Box>
                </DialogContent>
                <DialogActions>
                    {/* <Button onClick={onClose}>Close</Button> */}
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