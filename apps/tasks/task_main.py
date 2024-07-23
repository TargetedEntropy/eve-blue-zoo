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

class MainTasks:
    """The Main tasks driving class.

    We intialize, control and execute our tasks here.
    """

    def __init__(self, app:object, tasks=None):
        """Run internal class intialization functions"""
        self.tasks = ['mining_ledger']
        self.app = app
        # self.tasks = self.load_tasks()
        self.scheduler = self.configure_scheduler(self.app)

    
    def configure_scheduler(self, app):
        # Setup the scheduler to refresh coures, assignments and submissions
        scheduler = APScheduler()
        scheduler.init_app(app)
        scheduler.add_job(func=self.execute_scheduled_tasks, id='execute_scheduled_tasks', trigger="interval", seconds=10)
        scheduler.start()

        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())
        return scheduler

    def task_mining_ledger(self):
        mining_ledger = MiningLedgerTasks(self.scheduler)
        mining_ledger.main()
        print("Mining Ledger Done")
            
    def execute_scheduled_tasks(self) -> None:
        """Execute all of our tasks.

        This will run all the tasks.
        """
        print(f"Running {len(self.tasks)} tasks")
        
        for task_name in self.tasks:
            task = f"task_{task_name}"
            if hasattr(self, task) and callable(func := getattr(self, task)):
                func()

    def load_tasks(self) -> list:
        """Get list of Tasks"""

        task_list = []
        modules = os.scandir("./tasks/modules")
        for module in modules:
            if module.is_file():
                module_name, _ = os.path.splitext(module.name)
                if module_name in  ["__init__", "__pycache__"]: continue
                print(f"module_name: {module_name}")
                task_list.append(module_name)
        return task_list

