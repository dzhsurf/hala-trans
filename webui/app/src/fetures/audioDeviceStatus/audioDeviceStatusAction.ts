import { AppDispatch } from "../../app/store";
import { audioDeviceStatusSlice } from "./audioDeviceStatusSlice";

const changeDevice = (dispatch: AppDispatch, deviceName: string) => {
    dispatch(audioDeviceStatusSlice.actions.deviceName(deviceName));
};

export default changeDevice;