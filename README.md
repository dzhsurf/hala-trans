hala-trans
----------

hala-trans is a Real-Time Speech Translate AI Assistant.

**The project is still in its early development stages. If you are interested in the project, feel free to contact us.**


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

The architecture of the hala-trans is primarily divided into the following services:

1. **Backend Server:** Uses FastAPI to communicate with subprocesses through IPC Queue and manages subprocesses via ProcessPoolExecutor.
2. **RTS2T Controller Service:** A subprocess service responsible for coordinating data from all other subprocess services and providing it to the backend server.
3. **Audio Stream Service:** Provides voice stream data.
4. **Transcribe Service:** Utilizes Vosk for real-time speech-to-text transcriptions.
5. **Whisper Transcribe Service:** Uses the Faster Whisper model for intermittent transcription of voice data. The transcriptions from this service are considered the final results. The Whisper model has higher accuracy than Vosk but is slower, hence, there are two transcription services.
6. **Translation Service:** Uses GPT-4o to translate the transcribed text.
7. **Assistant Service:** Uses GPT-4o to analyze the transcribed text and provide assistance and suggestions.

Communication between subprocesses is achieved using ZeroMQ's PUB/SUB pattern. Each subprocess service can be deployed independently, and load balancing of subprocess services can be implemented by combining XSUB/XPUB, PUSH/PULL pattern.


![Architecture](./docs/architecture.png)


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

make run

```

Run WebUI
---------

```shell

cd webui/app

npm install 
npm run start 
```



# Reference

https://asdf-vm.com/

https://docs.anaconda.com/miniconda/miniconda-other-installer-links/

https://python-poetry.org/docs/

https://zeromq.org/

https://github.com/alphacep/vosk-api

https://github.com/SYSTRAN/faster-whisper

https://platform.openai.com/docs/api-reference/introduction

