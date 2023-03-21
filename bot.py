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


class Bot(threading.Thread):
    def __init__(self):
        self.mumble = pymumble.Mumble(
            host="icewind.nl",
            user="ConnectBot",
            port=64738,
            password="",
            tokens=[],
            stereo=False,
            debug=False,
            certfile=None,
            reconnect=False,
        )
        self.connect = None
        self.mumble.start()  # start the mumble thread
        self.mumble.is_ready()  # wait for the connection

        if self.mumble.connected >= PYMUMBLE_CONN_STATE_FAILED:
            exit()

        self.users = self.get_user_count_in_channel()

        user_move_callback = lambda user, action: threading.Thread(
            target=self.change_callback,
            args=(user, action),
            daemon=True,
        ).start()

        user_disconnect_callback = lambda user, action: threading.Thread(
            target=self.disconnect_callback, args=(user, action), daemon=True
        ).start()

        user_connect_callback = lambda user: threading.Thread(
            target=self.connect_callback, args=(user), daemon=True
        ).start()

        self.mumble.callbacks.set_callback(
            PYMUMBLE_CLBK_USERREMOVED, user_disconnect_callback
        )
        self.mumble.callbacks.set_callback(
            PYMUMBLE_CLBK_USERUPDATED, user_move_callback
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
        own_channel = self.mumble.channels.find_by_name("9v9 Xenon")
        return len(own_channel.get_users())

    def connect_callback(self, user, action, four, five, *args):
        print("connect")
        old = self.users
        self.users = self.get_user_count_in_channel()
        if old < self.users:
            if self.connect != None:
                print("sending connect")
                self.send_channel_msg(self.connect)
        print(f"Users: {self.users}")

    def disconnect_callback(self, user, action):
        print("disconnect")
        self.users = self.get_user_count_in_channel()
        print(f"Users: {self.users}")
        if self.users == 1:
            self.connect = None

    def change_callback(self, user, action):
        self.users = self.get_user_count_in_channel()
        if self.users == 1:
            self.connect = None
        print(action)
        if user["channel_id"] == 18:
            if "channel_id" in action:
                print(user["name"] + " connected")
                print(self.connect)
                if self.connect != None:
                    print("sending connect")
                    self.send_channel_msg(self.connect)
        else:
            print(user["name"] + " disconnected")
        print(f"Users: {self.users}")

    def loop(self):
        while self.mumble.is_alive():
            pass


if __name__ == "__main__":
    bot = Bot()
    bot.loop()
