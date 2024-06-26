"""This is the main driving class of the overall tasks.

Here we will have a root function which is called on a schedule, that will then call subtasks which
will qualify if they run or not based on their own schedule. Meaning, some updates will happen more
frequently than others.
"""

from api import EsiTasks


class MainTasks:
    """The Main tasks driving class.

    We intialize, control and execute our tasks here.
    """

    def __init__(self):
        """Run internal class intialization functions"""
        self.load_tasks()

    def run_tasks(self, tasks:list) -> None:
        """Execute all of our tasks.

        This will run all the tasks.
        """
        for task_name in tasks:
            task = f"task_{task_name}"
            if hasattr(self, task) and callable(func := getattr(self, task)):
                func()

    def load_tasks(self):
        """Run any potential initilization tasks"""
        pass

    def purge_tasks(self):
        """Purge all tasks in the queue"""
        pass
