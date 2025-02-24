import os
import subprocess
import asyncio
import multiprocessing
import shutil

from loguru import logger as log

from fs_watcher import FsWatcher
from log_reader import LogReader

from streamcontroller_plugin_tools import BackendBase

MANGOHUD_CONFIG = "preset={},log_interval=100,autostart_log=1,output_folder=/tmp/sc_mangohud"


class MangoHudBackend(BackendBase):

    def __init__(self):
        super().__init__()
        if not os.path.isdir("/tmp/sc_mangohud"):
            os.mkdir("/tmp/sc_mangohud")
        self.fs_watcher = FsWatcher("/tmp/sc_mangohud", self.handle_add, self.handle_remove)
        self.log_watchers = {}

        log.info("Starting up MangoHud FileSystem watcher.")

        asyncio.run(self.fs_watcher.start_watch())

    def handle_add(self, log_file : str, proc : dict):
        watcher = LogReader(log_file, self.handle_data, proc["existing"])
        self.log_watchers[log_file] = watcher
        log.info(f"Starting MangoHud Log watcher for {log_file}")
        asyncio.create_task(watcher.start_watcher())

    def handle_remove(self, log_file : str, proc : dict):
        if log_file in self.log_watchers:
            watcher = self.log_watchers[log_file]
            log.info(f"Stopping MangoHud Log watcher for {log_file}")
            watcher.stop_watcher()
            del self.log_watchers[log_file]

    def handle_data(self, entry : dict):
        self.frontend.update_sync_event_holder.trigger_event(entry)

    def get_env(self, preset) -> dict:
        return dict(os.environ, **{
            "MANGOHUD_CONFIG": MANGOHUD_CONFIG.format(preset)
        })

    def launch_mangohud(self, command, preset):
        kwargs = {
            "env": self.get_env(preset),
            "shell": True,
            "start_new_session": True,
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "cwd": os.path.expanduser("~")
        }
        flatpak_env = self.get_env(preset)

        if "heroic" in command:
            proc = multiprocessing.Process(target=subprocess.Popen, args=[command], kwargs=kwargs)
        else:
            proc = multiprocessing.Process(target=subprocess.Popen, args=[f"mangohud {command}"], kwargs=kwargs)
        proc.start()

    def find_executable(self, executables : list[str]) -> str:
        for executable in executables:
            res = shutil.which(executable)
            if res is not None:
                return executable
        return ""

    def on_disconnect(self, conn):
        log.info("Shutting down MangoHud FileSystem Watcher")
        for log_file in self.log_watchers:
            self.log_watchers[log_file].stop_watcher()
        self.fs_watcher.stop_watch()
        super().on_disconnect(conn)

backend = MangoHudBackend()