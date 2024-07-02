import { PayloadAction, createSlice } from "@reduxjs/toolkit";

export interface AudioDeviceStatusState {
    currentDevice: string
};

const initialState: AudioDeviceStatusState = {
    currentDevice: 'DEVICE',
};

export const audioDeviceStatusSlice = createSlice({
    name: 'audioDeviceStatus',
    initialState,
    reducers: {
        deviceName: (state, action: PayloadAction<string>) => {
            state.currentDevice = action.payload;
        },
    },
});

// export const { deviceName } = audioDeviceStatusSlice.actions;
export default audioDeviceStatusSlice.reducer;