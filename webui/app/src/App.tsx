import { Box, GlobalStyles } from '@mui/material';
import MyAppBar from './components/appbar/appbar';

import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import '@fontsource/roboto/300.css';
import '@fontsource/roboto/400.css';
import '@fontsource/roboto/500.css';
import '@fontsource/roboto/700.css';

import theme from './theme/theme';
import Home from './containers/home';

const globalStyles = {

};

function App() {

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <GlobalStyles styles={globalStyles} />
      {/* Your component tree */}
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <MyAppBar />
        <Home />
      </Box>
    </ThemeProvider>
  );
}

export default App;
