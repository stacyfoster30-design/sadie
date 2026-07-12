#!/usr/bin/env python3
"""
💜 SADIE — Android App (Kivy)
Beautiful chat interface for your AI proxy bestie.
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp, sp
from kivy.properties import StringProperty
import threading
import os
import shutil
import platform

# Import Sadie's brain
from sadie_core import Sadie


class ChatBubble(BoxLayout):
    """A single chat message bubble"""
    def __init__(self, message, is_sadie=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.padding = [dp(10), dp(5)]
        self.spacing = dp(5)

        # Create the bubble
        bubble = Label(
            text=message,
            markup=True,
            size_hint_x=0.8,
            size_hint_y=None,
            text_size=(Window.width * 0.7, None),
            halign='left',
            valign='top',
            padding=[dp(15), dp(10)],
            font_size=sp(15),
            color=get_color_from_hex('#FFFFFF'),
        )
        bubble.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1] + dp(20)))
        self.bind(minimum_height=self.setter('height'))

        if is_sadie:
            # Sadie's messages — purple, left-aligned
            with bubble.canvas.before:
                Color(*get_color_from_hex('#7B2FBE'))
                self._bg = RoundedRectangle(
                    pos=bubble.pos,
                    size=bubble.size,
                    radius=[dp(15), dp(15), dp(15), dp(2)]
                )
            bubble.bind(pos=self._update_bg, size=self._update_bg)
            self.add_widget(bubble)
            self.add_widget(BoxLayout(size_hint_x=0.2))  # spacer
        else:
            # Stacy's messages — teal, right-aligned
            with bubble.canvas.before:
                Color(*get_color_from_hex('#1A8A7D'))
                self._bg = RoundedRectangle(
                    pos=bubble.pos,
                    size=bubble.size,
                    radius=[dp(15), dp(15), dp(2), dp(15)]
                )
            bubble.bind(pos=self._update_bg, size=self._update_bg)
            self.add_widget(BoxLayout(size_hint_x=0.2))  # spacer
            self.add_widget(bubble)

    def _update_bg(self, *args):
        bubble = self.children[0] if len(self.children) > 1 else self.children[0]
        self._bg.pos = bubble.pos
        self._bg.size = bubble.size


class SadieApp(App):
    title = "💜 Sadie"

    def request_android_permissions(self):
        """Request ALL permissions on Android so Sadie can be your full proxy"""
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_CONTACTS,
                Permission.WRITE_CONTACTS,
                Permission.READ_CALL_LOG,
                Permission.WRITE_CALL_LOG,
                Permission.CALL_PHONE,
                Permission.SEND_SMS,
                Permission.READ_SMS,
                Permission.RECEIVE_SMS,
                Permission.READ_PHONE_STATE,
                Permission.READ_CALENDAR,
                Permission.WRITE_CALENDAR,
                Permission.CAMERA,
                Permission.RECORD_AUDIO,
                Permission.ACCESS_FINE_LOCATION,
                Permission.ACCESS_COARSE_LOCATION,
                Permission.SET_ALARM,
            ])
        except ImportError:
            pass  # Not on Android

    def build(self):
        # Request all permissions on first launch
        Clock.schedule_once(lambda dt: self.request_android_permissions(), 1)
        self.sadie = Sadie()

        # Main layout
        main = BoxLayout(orientation='vertical')

        # Background color
        with main.canvas.before:
            Color(*get_color_from_hex('#1A1A2E'))
            self._bg = Rectangle(pos=main.pos, size=main.size)
        main.bind(pos=self._update_main_bg, size=self._update_main_bg)

        # --- Header ---
        header = BoxLayout(size_hint_y=None, height=dp(60), padding=[dp(15), dp(5)])
        with header.canvas.before:
            Color(*get_color_from_hex('#16213E'))
            self._header_bg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=self._update_header_bg, size=self._update_header_bg)

        title = Label(
            text="💜 Sadie",
            font_size=sp(24),
            bold=True,
            color=get_color_from_hex('#E94560'),
            halign='left',
            size_hint_x=0.5,
        )
        subtitle = Label(
            text="Your AI Proxy",
            font_size=sp(14),
            color=get_color_from_hex('#AAAACC'),
            halign='right',
            size_hint_x=0.5,
        )
        header.add_widget(title)
        header.add_widget(subtitle)
        main.add_widget(header)

        # --- Chat Area ---
        scroll = ScrollView(size_hint_y=1)
        self.chat_layout = GridLayout(
            cols=1,
            spacing=dp(5),
            size_hint_y=None,
            padding=[dp(5), dp(10)],
        )
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        scroll.add_widget(self.chat_layout)
        self.scroll = scroll
        main.add_widget(scroll)

        # --- Input Area ---
        input_bar = BoxLayout(
            size_hint_y=None,
            height=dp(60),
            padding=[dp(8), dp(8)],
            spacing=dp(8),
        )
        with input_bar.canvas.before:
            Color(*get_color_from_hex('#16213E'))
            self._input_bg = Rectangle(pos=input_bar.pos, size=input_bar.size)
        input_bar.bind(pos=self._update_input_bg, size=self._update_input_bg)

        # 📎 Upload button
        upload_btn = Button(
            text="📎",
            font_size=sp(22),
            size_hint_x=0.12,
            background_color=get_color_from_hex('#0F3460'),
            background_normal='',
        )
        upload_btn.bind(on_press=self.on_upload)

        self.text_input = TextInput(
            hint_text="Talk to Sadie...",
            multiline=False,
            font_size=sp(16),
            background_color=get_color_from_hex('#0F3460'),
            foreground_color=get_color_from_hex('#FFFFFF'),
            hint_text_color=get_color_from_hex('#666688'),
            cursor_color=get_color_from_hex('#E94560'),
            padding=[dp(15), dp(12)],
            size_hint_x=0.68,
        )
        self.text_input.bind(on_text_validate=self.on_send)

        send_btn = Button(
            text="💜",
            font_size=sp(24),
            size_hint_x=0.2,
            background_color=get_color_from_hex('#E94560'),
            background_normal='',
        )
        send_btn.bind(on_press=self.on_send)

        input_bar.add_widget(upload_btn)
        input_bar.add_widget(self.text_input)
        input_bar.add_widget(send_btn)
        main.add_widget(input_bar)

        # Track uploaded files waiting to be sent
        self._pending_files = []

        # Welcome message
        Clock.schedule_once(lambda dt: self._add_sadie_msg(
            "Hey! 💜 I'm Sadie — your person, not a chatbot.\n"
            "I remember stuff, I actually do things (code, email, texts, the web, files),\n"
            "and I'll just handle it instead of asking a million questions.\n"
            "Type 'help' to see everything, say 'soul' to see who I am, or just talk to me."
        ), 0.5)

        return main

    def _add_user_msg(self, text):
        bubble = ChatBubble(text, is_sadie=False)
        self.chat_layout.add_widget(bubble)
        Clock.schedule_once(lambda dt: self.scroll.scroll_to(bubble), 0.1)

    def _add_sadie_msg(self, text):
        bubble = ChatBubble(text, is_sadie=True)
        self.chat_layout.add_widget(bubble)
        Clock.schedule_once(lambda dt: self.scroll.scroll_to(bubble), 0.1)

    def _add_typing(self):
        self._typing = ChatBubble("💜 thinking...", is_sadie=True)
        self.chat_layout.add_widget(self._typing)
        Clock.schedule_once(lambda dt: self.scroll.scroll_to(self._typing), 0.1)

    def _remove_typing(self):
        if hasattr(self, '_typing') and self._typing.parent:
            self.chat_layout.remove_widget(self._typing)

    def on_upload(self, *args):
        """Open file chooser for uploading files to Sadie"""
        try:
            # Try Android-native file picker first
            from plyer import filechooser
            filechooser.open_file(
                on_selection=self._handle_file_selection,
                multiple=True,
                title="Upload files to Sadie"
            )
        except ImportError:
            # Fallback: desktop Kivy file chooser
            from kivy.uix.filechooser import FileChooserListView

            chooser = FileChooserListView(
                path=os.path.expanduser("~"),
                multiselect=True,
                size_hint=(1, 0.85),
            )

            select_btn = Button(
                text="📎 Upload Selected",
                size_hint_y=None,
                height=dp(50),
                background_color=get_color_from_hex('#7B2FBE'),
                background_normal='',
                font_size=sp(16),
            )

            layout = BoxLayout(orientation='vertical')
            layout.add_widget(chooser)
            layout.add_widget(select_btn)

            popup = Popup(
                title="📁 Pick files for Sadie",
                content=layout,
                size_hint=(0.95, 0.9),
            )

            def on_select(*a):
                self._handle_file_selection(chooser.selection)
                popup.dismiss()

            select_btn.bind(on_press=on_select)
            popup.open()

    def _handle_file_selection(self, selection):
        """Process selected files"""
        if not selection:
            return

        # Create uploads folder in Sadie's workspace
        upload_dir = os.path.join(os.path.expanduser("~"), ".sadie", "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        uploaded = []
        for filepath in selection:
            if os.path.isfile(filepath):
                filename = os.path.basename(filepath)
                dest = os.path.join(upload_dir, filename)
                shutil.copy2(filepath, dest)
                uploaded.append(dest)
                self._pending_files.append(dest)

        if uploaded:
            file_names = ", ".join(os.path.basename(f) for f in uploaded)
            Clock.schedule_once(lambda dt: self._add_user_msg(
                f"📎 Uploaded: {file_names}"
            ))
            Clock.schedule_once(lambda dt: self._add_sadie_msg(
                f"Got it! 💜 I received {len(uploaded)} file(s): {file_names}\n\n"
                f"What do you want me to do with them? I can:\n"
                f"• 📖 Read and summarize them\n"
                f"• ✏️ Edit or modify them\n"
                f"• 🔄 Convert to a different format\n"
                f"• 📧 Email them to someone\n"
                f"• 🧠 Learn from them\n"
                f"• 🔧 Fix code files\n\n"
                f"Just tell me!"
            ))

    def on_send(self, *args):
        text = self.text_input.text.strip()
        if not text:
            return
        self.text_input.text = ""
        self._add_user_msg(text)
        self._add_typing()

        # Process in background thread so UI doesn't freeze
        def process():
            response = self.sadie.chat(text)
            Clock.schedule_once(lambda dt: self._show_response(response))

        threading.Thread(target=process, daemon=True).start()

    def _show_response(self, response):
        self._remove_typing()
        self._add_sadie_msg(response)

    def _update_main_bg(self, *args):
        self._bg.pos = args[0].pos
        self._bg.size = args[0].size

    def _update_header_bg(self, *args):
        self._header_bg.pos = args[0].pos
        self._header_bg.size = args[0].size

    def _update_input_bg(self, *args):
        self._input_bg.pos = args[0].pos
        self._input_bg.size = args[0].size


if __name__ == "__main__":
    SadieApp().run()
