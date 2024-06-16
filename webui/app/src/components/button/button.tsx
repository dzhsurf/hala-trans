import { Button as MuiButton, ButtonProps as MuiButtonProps } from '@mui/material';
import React from 'react';

interface ButtonProps extends MuiButtonProps {
    // Extend MuiButtonProps with any custom props
}

const Button: React.FC<ButtonProps> = (props) => {
    return <MuiButton {...props} />;
};

export default Button;