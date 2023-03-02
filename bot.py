import pymumble_py3 as pymumble
from pymumble_py3.constants import (
    PYMUMBLE_CLBK_TEXTMESSAGERECEIVED,
    PYMUMBLE_CONN_STATE_FAILED,
    PYMUMBLE_CLBK_USERREMOVED,
    PYMUMBLE_CLBK_USERUPDATED,
)
import threading
import re


class Bot(threading.Thread):
    def __init__(self):
        self.mumble = pymumble.Mumble(
            host="icewind.nl",
            user="ConnectBot",
            port=64738,
            password="",
            tokens=[],
            stereo=False,
            debug=True,
            certfile=None,
            reconnect=True,
        )
        self.mumble.callbacks.set_callback(
            PYMUMBLE_CLBK_TEXTMESSAGERECEIVED, self.message_received
        )
        self.connect = None
        self.mumble.start()  # start the mumble thread
        self.mumble.is_ready()  # wait for the connection

        if self.mumble.connected >= PYMUMBLE_CONN_STATE_FAILED:
            exit()

        self.join_channel("9v9 Xenon")
        self._user_in_channel = self.get_user_count_in_channel()

        user_change_callback = lambda user, action: threading.Thread(
            target=self.users_changed, args=(user, action), daemon=True
        ).start()

        self.mumble.callbacks.set_callback(
            PYMUMBLE_CLBK_USERREMOVED, user_change_callback
        )
        self.mumble.callbacks.set_callback(
            PYMUMBLE_CLBK_USERUPDATED, user_change_callback
        )

    def join_channel(self, name):
        self.mumble.channels.find_by_name(name).move_in()

    def send_channel_msg(self, msg):
        msg = msg.encode("utf-8", "ignore").decode("utf-8")
        own_channel = self.mumble.channels[self.mumble.users.myself["channel_id"]]
        own_channel.send_text_message(msg)

    def message_received(self, text):
        raw_message = text.message.strip()
        message = re.sub(r"<.*?>", "", raw_message)
        if "connect" in message:
            self.connect = message

    def get_user_count_in_channel(self):
        own_channel = self.mumble.channels[self.mumble.users.myself["channel_id"]]
        return len(own_channel.get_users())

    def users_changed(self, user, action):
        user_count = self.get_user_count_in_channel()
        if user_count > self._user_in_channel and self.connect != None:
            self.send_channel_msg(self.connect)
            self._user_in_channel = user_count

    def loop(self):
        while self.mumble.is_alive():
            pass


if __name__ == "__main__":
    bot = Bot()
    bot.loop()
