import pymumble_py3 as pymumble
from pymumble_py3.constants import (
    PYMUMBLE_CLBK_TEXTMESSAGERECEIVED,
    PYMUMBLE_CONN_STATE_FAILED,
    PYMUMBLE_CLBK_USERREMOVED,
    PYMUMBLE_CLBK_USERUPDATED,
    PYMUMBLE_CLBK_USERCREATED,
)
import threading
import re
import sys
import logging

logger = logging.getLogger("bot")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(formatter)

file_handler = logging.FileHandler(filename="logs.log", mode='a', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stdout_handler)

class Bot(threading.Thread):
    def __init__(self, port: int, host: str):
        self.mumble = pymumble.Mumble(
            host=host,
            user="ConnectBot",
            port=port,
            password="",
            tokens=[],
            stereo=False,
            debug=False,
            certfile=None,
            reconnect=True,
        )
        self.connect_strting = None
        self.mumble.start()  # start the mumble thread
        self.mumble.is_ready()  # wait for the connection

        if self.mumble.connected >= PYMUMBLE_CONN_STATE_FAILED:
            logger.info("Connect Bot disconnected")
            exit()

        self.users = self.get_user_count_in_channel()

        user_state_change_callback = lambda user, action: threading.Thread(
            target=self.user_state_change_callback,
            args=(user, action),
            daemon=True,
        ).start()

        user_disconnect_callback = lambda user, action: threading.Thread(
            target=self.user_disconnect_callback, args=(user, action), daemon=True
        ).start()

        user_connect_callback = lambda user: threading.Thread(
            target=self.user_connect_callback, args=(user), daemon=True
        ).start()

        self.mumble.callbacks.set_callback(
            PYMUMBLE_CLBK_USERREMOVED, user_disconnect_callback
        )
        self.mumble.callbacks.set_callback(
            PYMUMBLE_CLBK_USERUPDATED, user_state_change_callback
        )
        self.mumble.callbacks.set_callback(
            PYMUMBLE_CLBK_USERCREATED, user_connect_callback
        )
        self.mumble.callbacks.set_callback(
            PYMUMBLE_CLBK_TEXTMESSAGERECEIVED, self.message_received
        )
        self.join_channel("9v9 Xenon")

    def join_channel(self, name):
        self.mumble.channels.find_by_name(name).move_in()
        logger.info(f"Bot connected to channel {name}")

    def send_channel_msg(self, msg):
        msg = msg.encode("utf-8", "ignore").decode("utf-8")
        own_channel = self.mumble.channels[self.mumble.users.myself["channel_id"]]
        own_channel.send_text_message(msg)

    def message_received(self, text):
        raw_message = text.message.strip()
        message = re.sub(r"<.*?>", "", raw_message)
        if "connect " in message:
            self.connect_strting = message

    def get_user_count_in_channel(self):
        own_channel = self.mumble.channels.find_by_name("9v9 Xenon")
        return len(own_channel.get_users())

    def user_connect_callback(self, user, action, four, five, *args):
        logger.info(user["name"] + " connected")
        old = self.users
        self.users = self.get_user_count_in_channel()
        if old < self.users:
            if self.connect_strting != None:
                logger.info(f"Sending connect: {self.connect_strting}")
                self.send_channel_msg(self.connect_strting)
        logger.info(f"Users: {self.users - 1}")

    def user_disconnect_callback(self, user, action):
        logger.info(user['name'] + " disconnected")
        self.users = self.get_user_count_in_channel()
        logger.info(f"Users: {self.users - 1}")
        if self.users == 1:
            self.connect_strting = None

    def user_state_change_callback(self, user, action):
        self.users = self.get_user_count_in_channel()
        if self.users == 1:
            self.connect_strting = None
        logger.info(action)
        if user["channel_id"] == 18:
            if "channel_id" in action:
                logger.info(user["name"] + " connected")
                logger.info(self.connect_strting)
                if self.connect_strting != None:
                    logger.info(f"Sending connect: {self.connect_strting}")
                    self.send_channel_msg(self.connect_strting)
        else:
            logger.info(user["name"] + " disconnected")
        logger.info(f"Users: {self.users - 1}")

    def loop(self):
        while self.mumble.is_alive():
            pass


if __name__ == "__main__":
    hl_bot = Bot(host="icewind.nl", port=64738)
    #sixes_bot = Bot(host="icewind.nl", port=64738)
    hl_bot.loop()
