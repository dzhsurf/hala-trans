// import axios from 'axios';

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