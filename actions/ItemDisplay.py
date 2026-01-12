import time
from typing import Tuple
from datetime import timedelta

from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase

import os
from loguru import logger as log

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Pango, GLib

class ItemDisplay(ActionBase):
    STAT_ITEMS = "fps,frametime,cpu_load,cpu_power,gpu_load,cpu_temp,gpu_temp,gpu_core_clock,gpu_mem_clock,gpu_vram_used,gpu_power,ram_used,swap_used,process_rss,cpu_mhz,elapsed".split(",")
    DEFAULT_LABELS = ["FPS","FrameTime", "CPU Load", "CPU Power", "GPU Load", "CPU Temp", "GPU Temp", "GPU Clock", "VRAM Clock", "VRAM Used", "GPU Power", "RAM Used", "Swap Used", "RSS Used", "CPU GHz", "Elapsed"]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = self.plugin_base.backend

        self.plugin_base.connect_to_event(event_id="dev_eumario_MangoHud::UpdateSync",
                                          callback=self.on_data_sync)

        self.field = ""
        self.label_location = 0
        self.label_text = ""
        self.stat_location = 1
        self.first_data_sync = True
        self.timeout = 0
        self.last_updated = 0

    def on_ready(self):
        self.load_config_values(False)
        self.update_text(self.label_location, self.label_text)
        return super().on_ready()

    def on_data_sync(self, _signal : str, data : dict):
        if self.first_data_sync:
            self.first_data_sync = False
            GLib.timeout_add(1000,self.handle_timer)
        self.last_updated = time.time()
        field = self.field
        value = data[field]
        loc = self.stat_location
        label = self.get_formatted_string(field, value)

        self.update_text(loc, label)

    def handle_timer(self):
        if time.time() - self.last_updated > 5:
            self.update_text(self.stat_location, "")
            self.first_data_sync = True
            return False
        return True

    def get_formatted_string(self, field, value):
        if field in ["fps"]:
            i = int(value)
            return f"{i}"
        elif field in ["frametime"]:
            return f"{value:.1f}ms"
        elif field in ["cpu_load", "gpu_load"]:
            if type(value) == float:
                return f"{value:.2f}%"
            else:
                return f"{value}%"
        elif field in ["gpu_vram_used", "ram_used", "swap_used"]:
            return f"{value:.1f}GB"
        elif field in ["cpu_power", "gpu_power"]:
            return f"{value}W"
        elif field in ["cpu_temp", "gpu_temp"]:
            return f"{value}\u00B0C"
        elif field in ["gpu_core_clock", "gpu_mem_clock"]:
            return f"{value}MHz"
        elif field in ["cpu_mhz"]:
            ghz = value / 1000
            return f"{ghz:.2f}GHz"
        elif field in ["elapsed"]:
            seconds = value / 1_000_000_000
            return str(timedelta(seconds=int(seconds)))
        return f"{value}"

    def get_config_rows(self) -> list:
        self.group_stat = Adw.PreferencesGroup(title="Stat Settings")
        self.field_select = Adw.ComboRow(title="MangoHUD Field", subtitle="Select the field to show the stat of")

        model = Gtk.StringList()
        for item in self.STAT_ITEMS: model.append(item)
        self.field_select.set_model(model)

        self.stat_location_select = Adw.ComboRow(title="Location of Stat Text")

        model = Gtk.StringList()
        for item in ["Top","Middle","Bottom"]: model.append(item)

        self.stat_location_select.set_model(model)

        self.group_stat.add(self.field_select)
        self.group_stat.add(self.stat_location_select)

        self.group_label = Adw.PreferencesGroup(title="Label Settings")
        self.label_field = Adw.EntryRow(title="Title Label")
        self.label_location_select = Adw.ComboRow(title="Location of Label Text")

        model = Gtk.StringList()
        for item in ["Top","Middle","Bottom"]: model.append(item)

        self.label_location_select.set_model(model)

        self.group_label.add(self.label_field)
        self.group_label.add(self.label_location_select)

        self.load_config_values()

        self.field_select.connect("notify::selected", self.on_stat_changed)
        self.stat_location_select.connect("notify::selected", self.on_stat_loc_changed)
        self.label_field.connect("notify::text", self.on_label_changed)
        self.label_location_select.connect("notify::selected", self.on_label_loc_changed)

        return [self.group_stat, self.group_label]

    def on_stat_changed(self, combo_row, _pspec):
        settings = self.get_settings()
        settings["field"] = self.field = self.STAT_ITEMS[combo_row.get_selected()]
        settings["label_text"] = self.label_text = self.DEFAULT_LABELS[combo_row.get_selected()]
        self.label_field.set_text(self.label_text)
        self.set_settings(settings)

    def on_stat_loc_changed(self, combo_row, _pspec):
        self.update_text(self.stat_location, "")
        settings = self.get_settings()
        settings["stat_loc"] = self.stat_location = combo_row.get_selected()
        if self.stat_location == self.label_location:
            if self.label_location == 0: settings["label_loc"] = self.label_location = 1
            elif self.label_location == 1: settings["label_loc"] = self.label_location = 2
            elif self.label_location == 2: settings["label_loc"] = self.label_location = 0
            self.label_location_select.set_selected(self.label_location)
            self.update_text(self.label_text)
        self.set_settings(settings)

    def on_label_changed(self, *_args):
        settings = self.get_settings()
        settings["label_text"] = self.label_text = self.label_field.get_text()
        self.set_settings(settings)
        self.update_text(self.label_location, self.label_text)

    def on_label_loc_changed(self, combo_row, _pspec):
        self.update_text(self.label_location, "")
        settings = self.get_settings()
        settings["label_loc"] = self.label_location = combo_row.get_selected()
        if self.label_location == self.stat_location:
            if self.stat_location == 0: settings["stat_loc"] = self.stat_location = 1
            elif self.stat_location == 1: settings["stat_loc"] = self.stat_location = 2
            elif self.stat_location == 2: settings["stat_loc"] = self.stat_location = 0
            self.stat_location_select.set_selected(self.stat_location)
        self.update_text(self.label_location, self.label_text)
        self.set_settings(settings)

    def load_config_values(self, ui : bool = True):
        settings = self.get_settings()
        self.field = settings.get("field", "fps")
        self.stat_location = settings.get("stat_loc", 1)
        self.label_location = settings.get("label_loc", 0)
        self.label_text = settings.get("label_text", self.DEFAULT_LABELS[self.STAT_ITEMS.index(self.field)])
        if ui:
            self.field_select.set_selected(self.STAT_ITEMS.index(self.field))
            self.stat_location_select.set_selected(self.stat_location)
            self.label_location_select.set_selected(self.label_location)
            self.label_field.set_text(self.label_text)


    def update_text(self, location : int, text : str):
        if location == 0:
            self.set_top_label(text)
        elif location == 1:
            self.set_center_label(text)
        elif location == 2:
            self.set_bottom_label(text)
