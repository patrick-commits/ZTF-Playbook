from typing import Dict
from framework.helpers.log_utils import get_logger
from framework.scripts.python.helpers.state_monitor.marketplace_enabled_monitor import MarketPlaceEnableMonitor
from framework.scripts.python.helpers.v3.service import Service
from framework.scripts.python.script import Script

logger = get_logger(__name__)


class EnableMarketplace(Script):
    """
    Class that enables Marketplace on a Prism Central
    """
    def __init__(self, data: Dict, **kwargs):
        self.task_uuid = None
        self.data = data
        self.pc_session = self.data["pc_session"]
        super(EnableMarketplace, self).__init__(**kwargs)
        self.logger = self.logger or logger

    def execute(self, **kwargs):
        try:
            if self.data.get("enable_marketplace") is False:
                self.logger.info("Skipping enabling Marketplace as per user request")
                return
            service = Service(self.pc_session)
            status = service.is_marketplace_enabled()

            if status:
                self.logger.warning(f"SKIP: Marketplace is already enabled in {self.data['pc_ip']!r}")
                return

            self.logger.info(f"Enabling Marketplace in {self.data['pc_ip']!r}")
            try:
                service.enable_marketplace()
            except Exception as e:
                self.logger.error(f"Failed to enable Marketplace: {e}")
                self.exceptions.append(e)
                return

            # Monitor the task
            _, status = MarketPlaceEnableMonitor(self.pc_session).monitor()
            if not status:
                self.exceptions.append(
                    "Timed out. Marketplace in PC didn't happen in the prescribed timeframe")
            else:
                self.logger.info(f"Enabled Marketplace in the PC {self.data['pc_ip']!r}")
        except Exception as e:
            self.exceptions.append(e)

    def verify(self, **kwargs):
        # Initial status
        self.results["Enable_Marketplace"] = "CAN'T VERIFY"

        service = Service(self.pc_session)
        status = service.is_marketplace_enabled()

        if status:
            self.results["Enable_Marketplace"] = "PASS"
        else:
            self.results["Enable_Marketplace"] = "FAIL"
