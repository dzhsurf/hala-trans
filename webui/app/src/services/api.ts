// import axios from 'axios';

const serverURL = "http://localhost:8000/internal/services";

export const send_command = async (cmd: string): Promise<string> => {
    try {

        const postData = {
            "cmd": cmd,
        }

        const response = await fetch(serverURL,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(postData),
            }
        );
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const responseData = await response.json();
        console.log('Success: ', responseData);
        return "ok";
    } catch (error) {
        console.error('Error:', error);
        return String(error);
    }
}


async function connectServer<T>(serverURL: string, callback: (data: T) => boolean): Promise<void> {
    try {

        const response = await fetch(serverURL);
        const reader = response.body!.getReader();
        const decoder = new TextDecoder('utf-8');

        while (true) {
            // ReadableStreamReadResult<Uint8Array>
            const { done, value } = await reader.read();
            if (done) {
                console.log('Stream finished.');
                break;
            }

            const bodyText: string = decoder.decode(value);
            const chunks: string[] = bodyText.trim().split("\n\n");
            let stop = false;
            for (const i in chunks) {
                const chunk = chunks[i].substring(6);
                console.log(chunk);
                const data: T = JSON.parse(chunk);
                let stop = false;
                if (callback) {
                    stop = callback(data);
                }
                if (stop) {
                    break;
                }
            }
            if (stop) {
                break;
            }
        }
    } catch (error) {
        console.log(error);
        setTimeout(() => {
            connectServer<T>(serverURL, callback);
        }, 5000);
    }
};

export default connectServer;