from src.backend.PluginManager.ActionBase import ActionBase

class ToggleHud(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)

        self.backend = self.plugin_base.backend

    def on_ready(self):
        self.set_top_label("Toggle")
        self.set_center_label("MangoHud")

    def on_key_down(self):
        self.backend.toggle_hud()