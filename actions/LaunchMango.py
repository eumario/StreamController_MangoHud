import shutil

from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase

import os
from loguru import logger as log

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Pango

class LaunchMango(ActionBase):
    PROGRAM_TYPE = ["Steam", "Heroic", "Custom Program/Game"]
    HUD_PRESETS = ["FPS Only", "Bar", "Extended", "Detailed"]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = self.plugin_base.backend

        self.program_type = 0
        self.preset = 3
        self.custom_command = ""
        self.custom_args = ""

    def on_ready(self):
        self.load_config_values(False)
        return super().on_ready()

    def get_config_rows(self) -> list:
        self.program_group = Adw.PreferencesGroup(title="Program Launching")
        self.program_type_selector = Adw.ComboRow(title="Program Type", subtitle="Launch a Launcher or Custom program")
        model = Gtk.StringList()
        for item in self.PROGRAM_TYPE: model.append(item)
        self.program_type_selector.set_model(model)
        self.program_type_custom = Adw.EntryRow(title="Custom Command")
        self.program_type_custom_args = Adw.EntryRow(title="Arguments to Pass")

        self.program_group.add(self.program_type_selector)
        self.program_group.add(self.program_type_custom)
        self.program_group.add(self.program_type_custom_args)

        self.mangohud_group = Adw.PreferencesGroup(title="Mango HUD Settings")
        self.mangohud_preset = Adw.ComboRow(title="HUD Preset", subtitle="Type of hud to display")
        model = Gtk.StringList()
        for item in self.HUD_PRESETS: model.append(item)
        self.mangohud_preset.set_model(model)

        self.mangohud_group.add(self.mangohud_preset)

        self.load_config_values()

        self.program_type_selector.connect("notify::selected", self.on_program_type_selected)
        self.program_type_custom.connect("notify::text", self.on_custom_program)
        self.program_type_custom_args.connect("notify::text", self.on_custom_args)
        self.mangohud_preset.connect("notify::selected", self.on_mangohud_preset_selected)

        return [self.program_group, self.mangohud_group]

    def on_program_type_selected(self, *args, **kwargs):
        settings = self.get_settings()
        settings["program_type"] = self.program_type = self.program_type_selector.get_selected()
        self.program_type_custom.set_visible(self.program_type == 2)
        self.program_type_custom_args.set_visible(self.program_type == 2)
        self.set_settings(settings)

    def on_custom_program(self, *args, **kwargs):
        settings = self.get_settings()
        settings["custom_command"] = self.custom_command = self.program_type_custom.get_text()
        self.set_settings(settings)

    def on_custom_args(self, *args, **kwargs):
        settings = self.get_settings()
        settings["custom_args"] = self.custom_args = self.program_type_custom.get_text()
        self.set_settings(settings)

    def on_mangohud_preset_selected(self, *args, **kwargs):
        settings = self.get_settings()
        settings["preset"] = self.preset = self.mangohud_preset.get_selected() + 1
        self.set_settings(settings)

    def load_config_values(self, ui : bool = True):
        settings = self.get_settings()
        self.program_type = settings.get("program_type", 0)
        self.preset = settings.get("preset", 3)
        self.custom_command = settings.get("custom_command", "")
        self.custom_args = settings.get("custom_args", "")

        if ui:
            self.program_type_selector.set_selected(self.program_type)
            self.program_type_custom.set_visible(self.program_type == 2)
            self.program_type_custom_args.set_visible(self.program_type == 2)
            self.program_type_custom.set_text(self.custom_command)
            self.program_type_custom_args.set_text(self.custom_args)
            self.mangohud_preset.set_selected(self.preset - 1)

    def on_key_down(self):
        if self.program_type == 0: # Steam
            steam_executable = ""
            for steam in ["steam-native", "steam-runtime", "steam", "com.valvesoftware.Steam"]:
                res = shutil.which(steam)
                if res is not None:
                    if "com.valvesoftware" in res:
                        steam_executable = f"flatpak run {steam}"
                    else:
                        steam_executable = steam
                    break

            if steam_executable == "":
                dlg = Adw.AlertDialog(title="Failed to find Steam", body="Unable to find the Steam Launcher installed on your system.  Please install it.")
                dlg.show()
                return
            self.backend.launch_mangohud(steam_executable, self.preset)
        elif self.program_type == 1: # Heroic
            heroic_executable = "" #shutil.which("heroic")
            for heroic in ["heroic", "com.heroicgameslauncher.hgl"]:
                res = shutil.which(heroic)
                if res is not None:
                    if "com.heroicgameslauncher" in res:
                        heroic_executable = f"flatpak run {heroic}"
                    else:
                        heroic_executable = res

            if heroic_executable == "":
                dlg = Adw.AlertDialog(title="Failed to find Heroic", body="Unable to find the Heroic Games Launcher installed on your system.  Please install it.")
                dlg.show()
                return
            self.backend.launch_mangohud(heroic_executable, self.preset)
        else: # Custom Command
            cmd = self.custom_command + " " + self.custom_args
            self.backend.launch_mangohud(cmd, self.preset)