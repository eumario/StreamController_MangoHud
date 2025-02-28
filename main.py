# Import StreamController modules
import shutil

from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.EventHolder import EventHolder
from src.backend.PluginManager.ActionHolder import ActionHolder

import os
import subprocess
from loguru import logger as log

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Pango, GLib

# Import Actions
from .actions.ItemDisplay import ItemDisplay
from .actions.LaunchMango import LaunchMango
from .actions.ToggleHud import ToggleHud

class PluginMangoHud(PluginBase):
    def __init__(self):
        super().__init__()

        # Launch backend
        backend_dir = os.path.join(self.PATH, "backend")
        backend_path = os.path.join(backend_dir, "backend.py")
        if is_in_flatpak():
            self.flatpak_launch_backend(backend_path=backend_path, backend_dir=backend_dir, open_in_terminal=False, venv_path=os.path.join(self.PATH, "backend", ".venv"))
        else:
            self.launch_backend(backend_path=backend_path, open_in_terminal=False, venv_path=os.path.join(self.PATH, "backend", ".venv"))
        self.wait_for_backend(5)

        # Register Actions
        self.item_display_holder = ActionHolder(
            plugin_base=self,
            action_base=ItemDisplay,
            action_id="dev_eumario_MangoHud::ItemDisplay",
            action_name="Display MangoHud Stat"
        )
        self.add_action_holder(self.item_display_holder)

        self.launch_mango_holder = ActionHolder(
            plugin_base=self,
            action_base=LaunchMango,
            action_id="dev_eumario_MangoHud::LaunchMango",
            action_name="Launch App with MangoHud"
        )
        self.add_action_holder(self.launch_mango_holder)

        self.toggle_mangohud_holder = ActionHolder(
            plugin_base=self,
            action_base=ToggleHud,
            action_id="dev_eumario_MangoHud::ToggleHud",
            action_name="Toggle MangoHUD"
        )
        self.add_action_holder(self.toggle_mangohud_holder)

        # Register Events
        self.update_sync_event_holder = EventHolder(
            event_id = "dev_eumario_MangoHud::UpdateSync",
            plugin_base = self
        )
        self.add_event_holder(self.update_sync_event_holder)

        # Register Plugin
        self.register(
            plugin_name = "MangoHud Buttons",
            github_repo = "https://github.com/eumario/StreamController_MangoHud",
            plugin_version = "0.1.0",
            app_version = "1.5.0-beta6"
        )

    def get_settings_area(self):
        settings = self.get_settings()
        self.autohide_hud_control : Adw.SwitchRow = Adw.SwitchRow(title="Auto-Hide MangoHUD UI Overlay", Active=settings["autohide_hud"])
        self.autohide_hud_control.connect("notify::active", self.on_autohide_hud)
        return [self.autohide_hud_control]

    def on_autohide_hud(self, *args):
        settings = self.get_settings()
        settings["autohide_hud"] = self.autohide_hud_control.get_active()
        self.set_settings(settings)

    def flatpak_launch_backend(self, backend_path: str, backend_dir: str, venv_path: str = None, open_in_terminal: bool = False) -> None:
        self.start_server()
        port = self.server.port

        # Construct the command to launch the backend
        if open_in_terminal:
            command = "gnome-terminal -- bash -c '"
            if venv_path is not None:
                command += f". {venv_path}/bin/activate && "
            command += f"python3 {backend_path} --port={port}; exec $SHELL'"
        else:
            command = ""
            if venv_path is not None:
                command = f". {venv_path}/bin/activate && "
            command += f"python3 {backend_path} --port={port}"

        log.info(f"Launching backend: {command}")
        subprocess.Popen(f"flatpak-spawn --directory={backend_dir} --host bash -c '{command}'", shell=True, start_new_session=open_in_terminal)

        self.wait_for_backend()

def is_in_flatpak() -> bool:
    return os.path.isfile('/.flatpak-info')