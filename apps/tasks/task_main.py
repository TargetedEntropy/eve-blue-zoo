"""This is the main driving class of the overall tasks.

Here we will have a root function which is called on a schedule, that will then call subtasks which
will qualify if they run or not based on their own schedule. Meaning, some updates will happen more
frequently than others.
"""
import os
from importlib import import_module

from apps.authentication.models import Characters

class MainTasks:
    """The Main tasks driving class.

    We intialize, control and execute our tasks here.
    """

    def __init__(self, tasks=None):
        """Run internal class intialization functions"""
        #self.tasks = ['mining_ledger']
        self.tasks = self.load_tasks()
        self.character_list = Characters.query.all()
        
    def task_mining_ledger(self):
        print("Mining Ledger Done")

    def run_tasks(self) -> None:
        """Execute all of our tasks.

        This will run all the tasks.
        """
        print("running tasks")
        
        for task_name in self.tasks:
            task = f"task_{task_name}"
            if hasattr(self, task) and callable(func := getattr(self, task)):
                func()

    def load_tasks(self) -> list:
        """Get list of Tasks"""

        task_list = []
        modules = os.scandir("./apps/tasks/modules")
        for module in modules:
            if not module.is_file():
                module_name, _ = os.path.splitext(module.name)
                if module_name == "__init__": continue
                print(module_name)
                task_list.append(module_name)
        return task_list

