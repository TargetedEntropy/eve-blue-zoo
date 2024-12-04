"""This is the main driving class of the overall tasks.

Here we will have a root function which is called on a schedule, that will then call subtasks which
will qualify if they run or not based on their own schedule. Meaning, some updates will happen more
frequently than others.
"""

import os
from importlib import import_module
from flask_apscheduler import APScheduler
import atexit

from apps.tasks.modules.mining_ledger import MiningLedgerTasks
from apps.tasks.modules.blueprints import BlueprintTasks
from apps.tasks.modules.skills import SkillTasks
from apps.tasks.modules.notifications import NotificationTasks
from apps.tasks.modules.market_history import MarketHistoryTasks

class MainTasks:
    """The Main tasks driving class.

    We intialize, control and execute our tasks here.
    """

    def __init__(self, app: object, tasks=None):
        """Run internal class intialization functions"""
        self.tasks = ["mining_ledger", "blueprints", "skills", "notifications"]
        self.app = app

        self.scheduler = self.configure_scheduler(self.app)
        self.load_scheduled_tasks()

    def configure_scheduler(self, app):
        # Setup the scheduler to refresh coures, assignments and submissions
        scheduler = APScheduler()
        scheduler.init_app(app)
        scheduler.start()

        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())
        return scheduler

    def task_mining_ledger(self):
        mining_ledger = MiningLedgerTasks(self.scheduler)
        print("Mining Ledger Tasks Loaded")

    def task_blueprints(self):
        blueprints = BlueprintTasks(self.scheduler)
        print("Blueprint Tasks Loaded")

    def task_skills(self):
        skills = SkillTasks(self.scheduler)
        print("Skill Tasks Loaded")

    def task_notifications(self):
        notifications = NotificationTasks(self.scheduler)
        print("Notifications Loaded")
        
    def task_market_history(self):
        market_history = MarketHistoryTasks(self.scheduler)
        print("Market History Loaded")        

    def load_scheduled_tasks(self) -> None:
        """Load all of our tasks.

        This will run initialize the tasks.
        """
        print(f"Running {len(self.tasks)} tasks")

        for task_name in self.tasks:
            task = f"task_{task_name}"
            if hasattr(self, task) and callable(func := getattr(self, task)):
                func()
