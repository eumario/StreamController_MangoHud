# Import StreamController modules

from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.EventHolder import EventHolder
from src.backend.PluginManager.ActionHolder import ActionHolder

import os

# Import Actions
from .actions.ItemDisplay import ItemDisplay
from .actions.LaunchMango import LaunchMango

class PluginWebsocket(PluginBase):
    def __init__(self):
        super().__init__()

        # Launch backend
        backend_path = os.path.join(self.PATH, "backend", "backend.py")
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