import { createSlice } from "@reduxjs/toolkit";

const initialState = {

};

export const demoSlice = createSlice({
    name: 'demo',
    initialState,
    reducers: {
    },
});

export const { } = demoSlice.actions;

export default demoSlice.reducer;