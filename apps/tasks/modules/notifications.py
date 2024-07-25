""" Notification Tasks """

from apps.authentication.models import Characters, Notifications, SkillSet
from apps import esi, db


class NotificationTasks:
    """Tasks related to Notifications"""

    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.schedule_tasks()

    def schedule_tasks(self) -> None:
        """Setup task execution schedule"""
        self.scheduler.add_job(
            func=self.main,
            trigger="interval",
            seconds=3600,
            id="notification_main",
            name="notification_main",
            replace_existing=True,
        )

    def get_all_users(self) -> list:
        """Gets all characters"""
        with self.scheduler.app.app_context():
            character_list = Characters.query.all()

        return character_list

    def main(self):
        print("Running Notification Main")

        from datetime import datetime
        print(f"now = {datetime.now()}")

        characters = self.get_all_users()

        for character in characters:
            print(f"Checking: {character.character_name}")

            # Get Data
            esi_params = {"character_id": character.character_id}
            notification_data = esi.get_esi(
                character, "get_characters_character_id_notifications", **esi_params
            )

            ld = notification_data.data

            with self.scheduler.app.app_context():
                notification = db.session.query(NotificationSet).filter_by(character_id=character.character_id).first()

            if notification:
                # Update the fields
                notification.total_sp = ld["total_sp"]
                notification.unallocated_sp = ld["unallocated_sp"]
                
                # Commit the changes
                with self.scheduler.app.app_context():
                    db.session.commit()
                print(f"Updated NotificationSet for character, {character.character_name}")
            else:
                notification_row = NotificationSet(
                    character_id=character.character_id,
                    total_sp=ld["total_sp"],
                    unallocated_sp=ld["unallocated_sp"]
                    )


                with self.scheduler.app.app_context():
                    db.session.merge(notification_row)
                    db.session.commit()                
