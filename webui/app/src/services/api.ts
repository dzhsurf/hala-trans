// import axios from 'axios';

const serverURL = "http://localhost:8000";

export const backend_send_command = async (cmd: string): Promise<string> => {
    try {

        const postData = {
            "cmd": cmd,
        }

        const response = await fetch(serverURL + "/api/service_management",
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


// ===== /api/record 

export const frontend_record_service = async (cmd: string, index?: number): Promise<void> => {
    try {

        const postData = {
            "cmd": cmd,
            "deviceIndex": index,
        }

        const response = await fetch(serverURL + "/api/record",
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
    } catch (error) {
        console.error('Error:', error);
    }
};

// ===== /api/service_management

export interface ServiceStateType {
    error?: any
    runningState: "" | "Running"
};

export const queryServiceState = async (): Promise<ServiceStateType> => {
    try {
        const response = await fetch(serverURL + "/api/service_management");
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const responseData = await response.json();
        console.log('Success: ', responseData);
        return responseData;
    } catch (error) {
        console.error('Error:', error);
        return {
            error: error,
            runningState: "",
        };
    }
};


// ===== /api/devices

export class AudioDeviceItem {
    name: string;
    index?: number;

    constructor(name: string, index?: number) {
        this.name = name;
        if (index !== undefined) {
            this.index = index;
        }
    }

    static fromRecord(record: Record<string, string>): AudioDeviceItem[] {
        const devices = Object.entries(record).map(
            ([key, value]) => new AudioDeviceItem(value, Number(key))
        );
        return devices.sort((a, b) => {
            if (a.index === undefined) {
                return 1;
            }
            if (b.index === undefined) {
                return -1;
            }
            return (a.index ?? 0) - (b.index ?? 0);
        });
    }
};

export class AudioDeviceResponse {
    itemRecords: AudioDeviceItem[]
    error?: any

    constructor(itemRecords: AudioDeviceItem[], err?: any) {
        this.itemRecords = itemRecords;
        if (err !== undefined) {
            this.error = err;
        }
    }
};

export const queryAudioDeviceList = async (): Promise<AudioDeviceResponse> => {
    try {
        const response = await fetch(serverURL + "/api/devices");
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const responseData = await response.json() as Record<string, string>;
        const ret = new AudioDeviceResponse(AudioDeviceItem.fromRecord(responseData), undefined);
        console.log('Success: ', ret);
        return ret;
    } catch (error) {
        console.error('Error:', error);
        return new AudioDeviceResponse([], error);
    }
};

// =============== /api/event-stream

export type OnErrorCallback = (error: any) => boolean | null;
export type OnReceiveDataCallback<T> = (data: T) => boolean | null;

async function connectDataStreamingServer<T>(
    abortController: AbortController,
    callback: OnReceiveDataCallback<T>,
    onError: OnErrorCallback): Promise<void> {

    console.info("start data streaming...");
    const { signal } = abortController;
    while (!signal.aborted) {
        try {

            const response = await fetch(serverURL + "/api/event_stream");
            const reader = response.body!.getReader();
            const decoder = new TextDecoder('utf-8');

            while (true) {
                if (signal.aborted) {
                    break;
                }

                // ReadableStreamReadResult<Uint8Array>
                const { done, value } = await reader.read();
                if (done) {
                    console.log('Stream finished.');
                    // abortController.abort('done');
                    // wait 10 seconds...
                    await new Promise((resolver) => { setTimeout(resolver, 10000) });
                    break;
                }

                const bodyText: string = decoder.decode(value);
                const chunks: string[] = bodyText.trim().split("\n\n");

                for (const i in chunks) {
                    if (signal.aborted) {
                        break;
                    }

                    const chunk = chunks[i].substring(6);
                    console.log(chunk);
                    const data: T = JSON.parse(chunk);
                    if (callback && callback(data)) {
                        abortController.abort("STOP");
                    }
                }
            }
        } catch (error) {
            console.log(error);
            if (onError && onError(error)) {
                abortController.abort("STOP");
                break;
            }

            // wait 5 seconds...
            await new Promise((resolver) => { setTimeout(resolver, 5000) });
        }
    }

    console.info("data streaming end.")
};

export default connectDataStreamingServer;