hala-trans
----------

hala-trans is a Real-Time Speech Translate AI Assistant.

**This project is still in its early development stages. If you are interested in this project, feel free to contact us.**




# Progress Statement

Updated 2/Jul/2024

Backend
- [TODO] Add session management.
- [TODO] Add configurable parameters for each subprocess service instead of the current hardcoded approach.
- [TODO] Optimize user interface interactions.

- [PLANNING] Enhance assistant prompt management.
- [PLANNING] Improve the capabilities of the LLM Agent.
- [PLANNING] Cross-Platform Client (Windows, macOS, Linux, iOS, Android) Release Packaging.

Frontend
- [TODO] Add frontend service config setting.
- [TODO] Add backend service config setting.
- [TODO] Add conversation ui. 



Product Screenshot
----------

![start](./docs/demo-start.png)

![transcription](./docs/demo-transcription.jpg)




Architecture
------------

The architecture of halatrans is primarily composed of the following components:

1. **Backend Service**: 
   1. **Backend Web Server**: A RestAPI Server implemented with FastAPI. It provides the interface for interaction with the Frontend UI.
   2. **RTS2T Service**: A subprocess service used to integrate and manage information from other subprocess services, communicating with the Backend Web Server via IPC.
   3. **Transcribe Service**: A subprocess service, utilizes Vosk for real-time speech-to-text transcriptions.
   4. **Whisper Transcribe Service**: A subprocess service, uses the Faster Whisper model for intermittent transcription of voice data. The transcriptions from this service are considered the final results. The Whisper model has higher accuracy than Vosk but is slower, hence, there are two transcription services.
   5. **Translation Service**: Uses GPT-4o to translate the transcribed text.
   6. **Assistant Service**: Uses GPT-4o to analyze the transcribed text and provide assistance and suggestions.
   7. **Storage Service**: Stores the original and translated data in a database.
2. **Frontend Service**:
   1. **Frontend Server/Bridge**: A RestAPI Server or API Bridge for interacting with the Frontend UI.
   2. **Audio Device Service**: A subprocess service that uses PyAudio (or others) to provide functionalities such as querying audio devices.
   3. **Audio Stream Service**: A subprocess service that provides voice stream data.
3. **Frontend UI**: A Web UI App implemented with ReactJS/Redux/Material UI.
4. **Desktop/Mobile App Packages**: [TBD] Packages the Frontend UI and Frontend Service into standalone desktop/mobile applications.



Communication between subprocesses is achieved using ZeroMQ's PUB/SUB pattern. Each subprocess service can be deployed independently, and load balancing of subprocess services can be implemented by combining XSUB/XPUB, PUSH/PULL pattern.

![Architecture](./docs/architecture.png)



Below is the design of BaseService:

![BaseService](./docs/base_service_design.png)





Requirements
------------

```plain
Python 3.11
poetry 1.8.0
```

Core components

```
Languages: Python, TypeScript
Web Server: FastAPI
Frontend: ReactJS
IPC / Message Communication: ZeroMQ
Realtime transcription: vosk
Speech transcription: faster-whisper
Translation & Assistant: OpenAI GPT-4o
Database: [TBD]
```



Install & Run Background Service
--------------------------------

```shell
# if you're using conda, use conda create -n myproj python=3.11 to obtain python 3.11 environment

poetry install

# before run backend service, set OPENAI_API_KEY env
make runBackend

make runFrontend
```



Run WebUI
---------

```shell
cd webui/app

npm install 
npm run start 
```



Reference
---------

https://asdf-vm.com/

https://docs.anaconda.com/miniconda/miniconda-other-installer-links/

https://python-poetry.org/docs/

https://zeromq.org/

https://github.com/alphacep/vosk-api

https://github.com/SYSTRAN/faster-whisper

https://platform.openai.com/docs/api-reference/introduction



Contribution
------------

Contributions are always welcome!



License
-------

halatrans's code are released under the MIT License. See [LICENSE](https://github.com/dzhsurf/hala-trans/blob/main/LICENSE) for further details.