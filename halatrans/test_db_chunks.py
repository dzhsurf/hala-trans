import os
from typing import List

import numpy as np
from faster_whisper import WhisperModel
from sqlalchemy import Column, Integer, LargeBinary, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# engine = create_engine("sqlite:///:memory:", echo=False)
engine = create_engine("sqlite:///msgs.db", echo=False)

Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


class DBChatMessage(Base):
    __tablename__ = "chatmessages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    msgid = Column(String)
    text = Column(String)
    translation = Column(String)

    def __repr__(self):
        return f"<DBChatMessage(msgid={self.msgid}, text={self.text})"


class DBChatRawChunks(Base):
    __tablename__ = "rawchunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    msgid = Column(String)
    data = Column(LargeBinary)

    def __repr__(self):
        return f"<DBChatRawChunks(name={self.msgid})>"


INT16_MAX_ABS_VALUE = 32768.0


def process_faster_whisper_transcribe(
    faster_whipser: WhisperModel,
    frame: np.ndarray,
):
    segments, info = faster_whipser.transcribe(
        frame,
        beam_size=5,
        language="en",
        condition_on_previous_text=False,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )
    for segment in segments:
        text = segment.text.strip()
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {text}")


def main():
    os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
    model_size = "tiny.en"
    faster_whipser = WhisperModel(
        model_size,
        device="cpu",
        compute_type="float32",
        cpu_threads=0,
        num_workers=1,
    )

    Base.metadata.create_all(engine)
    chunks = session.query(DBChatRawChunks).all()
    for chunk in chunks:
        print(chunk.msgid)
        # detect chunk data is ok
        frame = np.frombuffer(chunk.data, dtype=np.int16)
        audio_array = frame.astype(np.float32) / INT16_MAX_ABS_VALUE
        # use faster whisper to transcribe audio to text
        process_faster_whisper_transcribe(
            faster_whipser=faster_whipser,
            frame=audio_array,
        )


if __name__ == "__main__":
    main()
