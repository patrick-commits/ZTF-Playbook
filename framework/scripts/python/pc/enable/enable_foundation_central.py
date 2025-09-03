import time
from typing import Dict
from framework.scripts.python.helpers.v1.genesis import Genesis
from framework.scripts.python.helpers.state_monitor.fc_enabled_monitor import FcEnabledMonitor
from framework.scripts.python.script import Script
from framework.helpers.log_utils import get_logger

logger = get_logger(__name__)


class EnableFC(Script):
    """
    Class that enables Foundation Central
    """
    def __init__(self, data: Dict, **kwargs):
        self.status = False
        self.data = data
        self.pc_session = self.data["pc_session"]
        super(EnableFC, self).__init__(**kwargs)
        self.logger = self.logger or logger

    def execute(self, **kwargs):
        try:
            if self.data.get("enable_fc") is False:
                self.logger.info("Skipping enabling Foundation Central as per user request")
                return
            genesis = Genesis(self.pc_session)
            status, _ = genesis.is_fc_enabled()

            if status:
                self.logger.warning(f"SKIP: Foundation Central service is already enabled {self.data['pc_ip']!r}")
                return

            self.logger.info(f"Enabling Foundation Central service {self.data['pc_ip']!r}")
            self.status, _ = genesis.enable_fc()

            # Monitor the task
            if self.status:
                _, status = FcEnabledMonitor(self.pc_session).monitor()

                if not status:
                    self.exceptions.append(
                        "Timed out. Enabling Foundation Central service in PC didn't happen in the prescribed "
                        "timeframe")
                else:
                    self.logger.info(f"Enabled Foundation Central service in the PC {self.data['pc_ip']!r}")
                    time.sleep(30)  # wait for a while to let the service stabilize
        except Exception as e:
            self.exceptions.append(e)

    def verify(self, **kwargs):
        # Initial status
        self.results["Enable_FC"] = "CAN'T VERIFY"

        genesis = Genesis(self.pc_session)
        status, _ = genesis.is_fc_enabled()

        if status:
            self.results["Enable_FC"] = "PASS"
        else:
            self.results["Enable_FC"] = "FAIL"
