// import React, { useEffect, useRef, useState } from 'react';
// import logo from './logo.svg';
import './App.css';
import { Box } from '@mui/material';
import MyAppBar from './components/appbar/appbar';
// import Bubble, { BubbleProps } from './Bubble';
// import connectStreamingServer from './streaming';

import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import '@fontsource/roboto/300.css';
import '@fontsource/roboto/400.css';
import '@fontsource/roboto/500.css';
import '@fontsource/roboto/700.css';

import theme from './theme/theme';
import Home from './containers/home';

// interface StreamingEventItem {
//   item: BubbleProps;
// }

function App() {

  // const [bubbles, setBubbles] = useState<BubbleProps[]>([]);
  // const [assistantContent, setAssistantContent] = useState<string>("");
  // const fetched = useRef(false);

  // useEffect(() => {
  //   const fetchData = async (): Promise<void> => {
  //     if (fetched.current) {
  //       return;
  //     }
  //     fetched.current = true;

  //     const server = 'http://localhost:8000/api/streaming';

  //     connectStreamingServer<StreamingEventItem>(server,
  //       (data: StreamingEventItem): boolean => {
  //         if (data.item == null || data.item.text.length === 0) {
  //           // console.log('No event');
  //           return false;
  //         }

  //         if (data.item.status === 'PROCESS_TEXT_STATUS.ASSISTANT') {
  //           console.log("ASSISTANT: " + data.item.text);
  //           // setAssistantContent((prevStr: string) => {
  //           //   return data.item.texts.join("\n");
  //           // });
  //           return false;
  //         }

  //         if (data.item.status === 'PROCESS_TEXT_STATUS.OPENAI_CONVERT') {
  //           console.log("OPENAI_CONVERT: " + data.item.translation);
  //         }

  //         setBubbles((prevBubbles: BubbleProps[]) => {
  //           const itemExists = prevBubbles.some(item => (item.msgid === data.item.msgid));
  //           if (itemExists) {
  //             return prevBubbles.map(bubble => {
  //               if (bubble.msgid === data.item.msgid) {
  //                 if (data.item.status === 'PROCESS_TEXT_STATUS.OPENAI_CONVERT') {
  //                   return {
  //                     ...bubble,
  //                     status: data.item.status,
  //                     translations: data.item.translation,
  //                   };
  //                 }
  //                 return {
  //                   ...bubble,
  //                   status: data.item.status,
  //                   texts: data.item.text,
  //                 };
  //               }
  //               return bubble;
  //             });
  //           } else {
  //             return [data.item, ...prevBubbles];
  //           }
  //         });

  //         return false;
  //       });
  //   };

  //   fetchData();
  // }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {/* Your component tree */}
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <MyAppBar />
        <Home />
      </Box>
    </ThemeProvider>
    // <div className='layout'>
    //   <div className='left'>
    //     {
    //       bubbles.map((bubble, index) => (
    //         <Bubble key={bubble.msgid + "-" + index.toString()}
    //           msgid={bubble.msgid}
    //           status={bubble.status}
    //           text={bubble.text}
    //           translation={bubble.translation}
    //         />
    //       ))
    //     }
    //   </div>
    //   <div className='right'>
    //     <Markdown remarkPlugins={[remarkGfm]}>{assistantContent}</Markdown>
    //   </div>
    // </div>
    // <div className="App">
    //   <header className="App-header">
    //     <img src={logo} className="App-logo" alt="logo" />
    //     <p>
    //       Edit <code>src/App.tsx</code> and save to reload.
    //     </p>
    //     <a
    //       className="App-link"
    //       href="https://reactjs.org"
    //       target="_blank"
    //       rel="noopener noreferrer"
    //     >
    //       Learn React
    //     </a>
    //   </header>
    // </div>
  );
}

export default App;
