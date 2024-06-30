"""This is the main driving class of the overall tasks.

Here we will have a root function which is called on a schedule, that will then call subtasks which
will qualify if they run or not based on their own schedule. Meaning, some updates will happen more
frequently than others.
"""
import os
from .modules.mining_ledger import MiningLedgerTasks

class MainTasks:
    """The Main tasks driving class.

    We intialize, control and execute our tasks here.
    """

    def __init__(self, tasks=None):
        """Run internal class intialization functions"""
        self.tasks = ['mining_ledger']
        print(self.tasks)
        
    def task_mining_ledger(self):
        MiningLedger = MiningLedgerTasks()
        print("Mining Ledger Done")

    def run_tasks(self) -> None:
        """Execute all of our tasks.

        This will run all the tasks.
        """
        for task_name in self.tasks:
            task = f"task_{task_name}"
            if hasattr(self, task) and callable(func := getattr(self, task)):
                func()

    # def load_tasks(self) -> list:
    #     """Get list of Tasks"""

    #     task_list = []
    #     modules = os.scandir("./apps/tasks/modules")
    #     for module in modules:
    #         if module.is_file():
    #             print(module.name)
    #             task_list.append(module.name)
    #     return task_list

