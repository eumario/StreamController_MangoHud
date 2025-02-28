from asyncio import Future, AbstractEventLoop

import psutil
import os
import asyncio
from watchfiles import awatch, Change
from loguru import logger as log

class FsWatcher:
    watching = {}
    ignore = []
    watch_folder = "/"

    def __init__(self, watch_folder, add_callback, remove_callback):
        self.watch_folder = watch_folder
        self.fut : Future = None
        self.loop : AbstractEventLoop = None
        self.add_callback = add_callback
        self.remove_callback = remove_callback

    def get_process(self, log_file):
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for file in proc.open_files():
                    if file.path == log_file:
                        return proc.as_dict(['pid','name'])
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return None

    def add_watcher(self, log_file, proc, is_modified = False):
        if log_file in self.ignore and proc is not None:
            self.ignore.remove(log_file)

        if proc is None:
            log.error(f"Unable to get Process for {log_file}")
            self.ignore.append(log_file)
            return

        log.info(f"Log file {log_file} modified by {proc['name']}({proc['pid']}), adding to watcher." if is_modified else
                 f"New Log {log_file} for Process {proc['name']}({proc['pid']}), adding to watcher.")
        proc["existing"] = is_modified
        self.watching[log_file] = proc
        self.add_callback(log_file, proc)

    def has_watcher(self, log_file):
        return log_file in self.watching

    def has_ignore(self, log_file):
        return log_file in self.ignore

    def has_process(self, pid):
        return pid in (self.watching[proc]['pid'] for proc in self.watching)

    def remove_watcher(self, log_file):
        if log_file in self.ignore:
            self.ignore.remove(log_file)

        if log_file in self.watching:
            proc = self.watching[log_file]
            log.info(f"File {log_file} for {proc['name']}({proc['pid']}) removed, stopping watcher.")
            self.remove_callback(log_file, self.watching[log_file])
            del self.watching[log_file]

    async def start_watch(self):
        self.loop = asyncio.get_running_loop()
        self.fut = self.loop.create_future()

        async for changes in awatch(self.watch_folder, rust_timeout=500, yield_on_timeout=True):
            if len(changes) == 0:
                remove = []
                for file in self.watching:
                    if not psutil.pid_exists(self.watching[file]['pid']):
                        remove.append(file)

                for file in remove:
                    log.info(f"Process {self.watching[file]['name']}({self.watching[file]['pid']}) stopped, removing log file.")
                    os.remove(file)
                    self.remove_callback(file, self.watching[file])
                    del self.watching[file]
            else:
                for change_type, file_path in changes:
                    if change_type == Change.added:
                        if file_path.endswith("_summary.csv"):
                            log.info("File is a Summary, not a Stat Log, continuing.")
                            continue
                        proc = self.get_process(file_path)
                        self.add_watcher(file_path, proc)
                    elif change_type == Change.modified:
                        if self.has_watcher(file_path):
                            continue

                        proc = self.get_process(file_path)
                        if proc is None:
                            if self.has_ignore(file_path):
                                continue
                            log.error(f"Unable to get Process for {file_path}")
                            self.ignore.append(file_path)
                            continue

                        self.add_watcher(file_path, proc, True)
                    elif change_type == Change.deleted:
                        self.remove_watcher(file_path)

            if self.fut.cancelled():
                log.info("FileSystem Watcher shutdown complete.")
                break



    def stop_watch(self):
        log.info("Stopping FileSystem Watcher...")
        self.fut.cancel()
