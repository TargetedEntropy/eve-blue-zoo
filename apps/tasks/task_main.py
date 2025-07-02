"""This is the main driving class of the overall tasks.

Here we will have a root function which is called on a schedule, that will then call subtasks which
will qualify if they run or not based on their own schedule. Meaning, some updates will happen more
frequently than others.
"""

from importlib import import_module
from flask_apscheduler import APScheduler
import atexit

from apps.tasks.modules.mining_ledger import MiningLedgerTasks
from apps.tasks.modules.blueprints import BlueprintTasks
from apps.tasks.modules.skills import SkillTasks
from apps.tasks.modules.notifications import NotificationTasks
from apps.tasks.modules.market_history import MarketHistoryTasks
from apps.tasks.modules.contracts import ContractTasks
from apps.tasks.modules.contract_items import ContractItemTasks
from apps.tasks.modules.contract_watch import ContractWatch

class MainTasks:
    """The Main tasks driving class.

    We intialize, control and execute our tasks here.
    """

    def __init__(self, app: object, tasks=None):
        """Run internal class intialization functions"""
        # self.tasks = tasks # or ["contracts", "contract_items"]
        self.tasks = tasks or ["skills", "blueprints"]
        # ["skills", "blueprints", "mining_ledger", "notifications", "market_history", "contracts"]
        self.app = app
        self.scheduler = self._configure_scheduler()
        self._load_scheduled_tasks()

    def _configure_scheduler(self) -> APScheduler:
        """Set up the scheduler to manage tasks."""
        scheduler = APScheduler()
        scheduler.init_app(self.app)
        scheduler.start()

        # Shut down the scheduler gracefully when exiting the app
        atexit.register(scheduler.shutdown)
        return scheduler

    def _load_scheduled_tasks(self) -> None:
        """Load and initialize tasks based on the provided task names."""
        print(f"Running {len(self.tasks)} tasks")

        for task_name in self.tasks:
            task_method_name = f"task_{task_name}"
            task_method = getattr(self, task_method_name, None)
            if callable(task_method):
                task_method()
            else:
                print(f"Task '{task_name}' not found or is not callable.")

    def task_mining_ledger(self):
        MiningLedgerTasks(self.scheduler)
        print("Mining Ledger Tasks Loaded")

    def task_blueprints(self):
        BlueprintTasks(self.scheduler)
        print("Blueprint Tasks Loaded")

    def task_skills(self):
        SkillTasks(self.scheduler)
        print("Skill Tasks Loaded")

    def task_notifications(self):
        NotificationTasks(self.scheduler)
        print("Notification Tasks Loaded")

    def task_market_history(self):
        MarketHistoryTasks(self.scheduler)
        print("Market History Tasks Loaded")

    def task_contracts(self):
        ContractTasks(self.scheduler)
        print("Contract Tasks Loaded")

    def task_contract_items(self):
        ContractItemTasks(self.scheduler)
        print("Contract Item Tasks Loaded")
        
    def task_contract_watch(self):
        ContractWatch(self.scheduler)
        print("Contract Watch Tasks Loaded")
