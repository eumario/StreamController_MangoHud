import asyncio
from io import TextIOWrapper
from loguru import logger as log

class LogReader:
    END_OF_HEADER = "fps,frametime,cpu_load,cpu_power,gpu_load,cpu_temp,gpu_temp,gpu_core_clock,gpu_mem_clock,gpu_vram_used,gpu_power,ram_used,swap_used,process_rss,elapsed"
    KEYS = END_OF_HEADER.split(",")
    def __init__(self, log_file, data_callback, existing = False):
        self.log_file : str = log_file
        self.data_callback = data_callback
        self.fut : asyncio.Future = None
        self.loop : asyncio.AbstractEventLoop = None
        self.header_found : bool = False
        self.existing : bool = existing

    async def follower(self, fh : TextIOWrapper):
        while True:
            line = fh.readline()
            if not line:
                await asyncio.sleep(0.1)
                continue
            yield line

    async def start_watcher(self):
        log.info(f"Starting LogReader Watcher for {self.log_file}")
        self.loop = asyncio.get_running_loop()
        self.fut = self.loop.create_future()

        with open(self.log_file, "r") as fh:
            if self.existing:
                self.header_found = True
                fh.seek(0,2)
            generator = self.follower(fh)
            while not self.fut.cancelled():
                line = await anext(generator)
                if self.END_OF_HEADER in line:
                    log.info("We found header, moving to reading for next line.")
                    self.header_found = True
                    continue
                if self.header_found:
                    data = {}
                    parts = line.split(",")
                    if len(parts) != len(self.KEYS):
                        continue

                    for i, key in enumerate(self.KEYS):
                        if "." in parts[i]:
                            data[key] = float(parts[i])
                        else:
                            data[key] = int(parts[i])
                    self.data_callback(self, data)

    def stop_watcher(self):
        log.info(f"Stopping LogWatcher for {self.log_file}")
        self.fut.cancel()