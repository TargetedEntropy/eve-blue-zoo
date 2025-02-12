"""This is the main driving class of the overall tasks.

Here we will have a root function which is called on a schedule, that will then call subtasks which
will qualify if they run or not based on their own schedule. Meaning, some updates will happen more
frequently than others.
"""
from flask_apscheduler import APScheduler
import atexit

from apps.tasks.modules import MiningLedgerTasks, BlueprintTasks, SkillTasks, NotificationTasks, MarketHistoryTasks, ContractTasks, ContractItemTasks, ContractWatch

class MainTasks:
    """The Main tasks driving class.

    We initialize, control, and execute our tasks here.
    """

    def __init__(self, app: object, tasks=None):
        """Run internal class initialization functions"""
        self.tasks = tasks or ["contracts", "contract_items", "contract_watch"] #, "skills", "blueprints", "mining_ledger", "notifications", "market_history"]
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
        
        task_classes = {
            "mining_ledger": MiningLedgerTasks,
            "blueprints": BlueprintTasks,
            "skills": SkillTasks,
            "notifications": NotificationTasks,
            "market_history": MarketHistoryTasks,
            "contracts": ContractTasks,
            "contract_items": ContractItemTasks,
            "contract_watch": ContractWatch,
        }

        for task_name in self.tasks:
            task_class = task_classes.get(task_name)
            if task_class:
                task_class(self.scheduler)
                print(f"{task_name.replace('_', ' ').title()} Tasks Loaded")
            else:
                print(f"Task '{task_name}' not found or is not callable.")
