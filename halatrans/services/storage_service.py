import base64
import json
import logging
import signal
from multiprocessing.managers import ValueProxy
from typing import Any, Dict, List, Optional

import zmq
from sqlalchemy import Column, Integer, LargeBinary, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from halatrans.services.interface import BaseService, ServiceConfig
from halatrans.services.utils import create_sub_socket, poll_messages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


class StorageService(BaseService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)

    @staticmethod
    def process_worker(
        stop_flag: ValueProxy[int],
        pub_addr: Optional[str],
        addition: Dict[str, Any],
        *args,
    ):
        logger.info("Init storage ")

        Base.metadata.create_all(engine)

        ctx = zmq.Context()
        rawchunks_sub = create_sub_socket(
            ctx, addition["transcribe_pub_addr"], "prooftext"
        )
        translation_sub = create_sub_socket(
            ctx, addition["translation_pub_addr"], "translation"
        )

        def should_top() -> bool:
            nonlocal stop_flag
            if stop_flag.get() == 1:
                return True
            return False

        def handle_sigint(signal_num, frame):
            nonlocal stop_flag
            stop_flag.set(1)

        signal.signal(signal.SIGINT, handle_sigint)

        def message_handler(sock: zmq.Socket, chunks: List[bytes]):
            for chunk in chunks:
                data = json.loads(chunk)
                msgid = data["msgid"]
                status = data["status"]
                if status == "translate" and "translation" in data:
                    text = data["text"]
                    translation = data["translation"]
                    newMsg = DBChatMessage(
                        msgid=msgid,
                        text=text,
                        translation=translation,
                    )
                    session.add(newMsg)
                elif status == "fulltext" and "chunks" in data:
                    # is from rawchunks_sub
                    b64_chunks = data["chunks"]
                    rawbytes = b"".join(
                        [
                            base64.b64decode(b64ecoded_text)
                            for b64ecoded_text in b64_chunks
                        ]
                    )
                    newData = DBChatRawChunks(
                        msgid=msgid,
                        data=rawbytes,
                    )
                    session.add(newData)

            session.commit()
            # msgs = session.query(DBChatMessage).all()
            # for msg in msgs:
            #     logger.info(msg)

        poll_messages([rawchunks_sub, translation_sub], message_handler, should_top)
