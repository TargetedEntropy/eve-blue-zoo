"""This is the main driving class of the overall tasks.

Here we will have a root function which is called on a schedule, that will then call subtasks which
will qualify if they run or not based on their own schedule. Meaning, some updates will happen more
frequently than others.
"""

import os
import sys
import atexit
import logging
from typing import List, Optional
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# Import database configuration
try:
    from .db import init_db, get_db
except ImportError:
    from db import init_db, get_db

# Import task modules
try:
    from .modules import (
        MiningLedgerTasks,
        BlueprintTasks,
        SkillTasks,
        NotificationTasks,
        MarketHistoryTasks,
        ContractTasks,
        ContractItemTasks,
        ContractWatch,
    )
except ImportError:
    from modules import (
        MiningLedgerTasks,
        BlueprintTasks,
        SkillTasks,
        NotificationTasks,
        MarketHistoryTasks,
        ContractTasks,
        ContractItemTasks,
        ContractWatch,
    )

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MainTasks:
    """The Main tasks driving class.
    
    We initialize, control, and execute our tasks here.
    """
    
    def __init__(self, tasks: Optional[List[str]] = None, blocking: bool = True):
        """Initialize the main tasks controller.
        
        Args:
            tasks: List of task names to run. If None, uses default tasks.
            blocking: Whether to use blocking scheduler (True) or background scheduler (False).
        """
        self.tasks = tasks or ["skills", "blueprints", "contracts"]
        self.blocking = blocking
        self.scheduler = self._configure_scheduler()
        
        # Initialize database
        self._initialize_database()
        
        # Load scheduled tasks
        self._load_scheduled_tasks()
    
    def _initialize_database(self):
        """Initialize database connection and create tables."""
        try:
            # Initialize database with DSN from environment
            db = init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _configure_scheduler(self) -> BlockingScheduler:
        """Set up the scheduler to manage tasks."""
        if self.blocking:
            scheduler = BlockingScheduler()
        else:
            scheduler = BackgroundScheduler()
        
        # Register shutdown handler
        atexit.register(self._shutdown_scheduler)
        
        return scheduler
    
    def _shutdown_scheduler(self):
        """Gracefully shutdown the scheduler."""
        if self.scheduler.running:
            logger.info("Shutting down scheduler...")
            self.scheduler.shutdown()
    
    def _load_scheduled_tasks(self) -> None:
        """Load and initialize tasks based on the provided task names."""
        logger.info(f"Loading {len(self.tasks)} tasks: {', '.join(self.tasks)}")
        
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
                try:
                    task_class(self.scheduler)
                    logger.info(f"{task_name.replace('_', ' ').title()} Tasks Loaded")
                except Exception as e:
                    logger.error(f"Failed to load {task_name} tasks: {e}")
            else:
                logger.warning(f"Task '{task_name}' not found or is not callable.")
    
    def start(self):
        """Start the task scheduler."""
        try:
            logger.info("Starting task scheduler...")
            self.scheduler.start()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            self._shutdown_scheduler()
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    def stop(self):
        """Stop the task scheduler."""
        self._shutdown_scheduler()
    
    def add_task(self, task_name: str):
        """Add a single task to the scheduler."""
        if task_name not in self.tasks:
            self.tasks.append(task_name)
            self._load_scheduled_tasks()
    
    def remove_task(self, task_name: str):
        """Remove a task from the scheduler."""
        if task_name in self.tasks:
            self.tasks.remove(task_name)
            # Note: This doesn't remove already scheduled jobs
            # You may want to implement job removal logic here
    
    def list_jobs(self):
        """List all scheduled jobs."""
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            logger.info(f"Job: {job.id}, Next run: {job.next_run_time}")
        return jobs


def main():
    """Main entry point for the application."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Task Scheduler Application')
    parser.add_argument(
        '--tasks', 
        nargs='+', 
        default=["skills", "blueprints", "contracts"],
        help='List of tasks to run'
    )
    parser.add_argument(
        '--background', 
        action='store_true',
        help='Run scheduler in background mode'
    )
    parser.add_argument(
        '--list-jobs', 
        action='store_true',
        help='List all scheduled jobs and exit'
    )
    
    args = parser.parse_args()
    
    # Create main tasks instance
    main_tasks = MainTasks(
        tasks=args.tasks,
        blocking=not args.background
    )
    
    if args.list_jobs:
        main_tasks.list_jobs()
        return
    
    try:
        main_tasks.start()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()