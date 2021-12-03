from devlprd import DaemonController

class DevlprServer:
    def __init__(self, board_id: str) -> None:
        self.started: bool = False
        self.controller: DaemonController = DaemonController(board_id)

    def start_if_needed(self):
        if self.started:
            return
        self.controller.start()
        self.started = True
    
    def stop(self):
        if self.started:
            self.controller.stop()
            self.started = False