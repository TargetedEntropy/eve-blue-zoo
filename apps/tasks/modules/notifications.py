""" Notification Tasks """

from apps.authentication.models import Characters, CharacterNotifications, Users, SkillSet
from apps import esi, db

class NotificationTasks:
    """Tasks related to Notifications"""

    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.schedule_tasks()
        # self.discord = DiscordOAuth2Session(app)

    def schedule_tasks(self) -> None:
        """Setup task execution schedule"""
        self.scheduler.add_job(
            func=self.main,
            trigger="interval",
            seconds=15,
            id="notification_main",
            name="notification_main",
            replace_existing=True,
        )

    def get_all_users(self) -> list:
        """Gets all characters"""
        with self.scheduler.app.app_context():
            character_list = CharacterNotifications.query.all()
        return character_list

    def main(self):
        print("Running Notification Main")

        from datetime import datetime
        print(f"now = {datetime.now()}")

        characters = self.get_all_users()

        for character in characters:

            # Make sure there's something here
            if not character.enabled_notifications: continue

            # If we don't have a discord ID, no point in going on
            with self.scheduler.app.app_context():
                user = Users.query.filter(
                    Users.character_id == character.master_character_id
                ).first()
            if not user.discord_user_id: continue

            if character.enabled_notifications == "sp-farm-notification":
                with self.scheduler.app.app_context():
                    total_sp = SkillSet.query.filter(
                        SkillSet.character_id == character.character_id
                    ).filter(
                        SkillSet.total_sp > 5500000
                    ).one()
                
                    character_info = Characters.query.filter(
                        Characters.character_id == character.character_id
                    ).one()
                    
                if total_sp:
                    print(f"{character_info.character_name} is ready for harvest with sp: {total_sp.total_sp}")
            # # Get Data
            # esi_params = {"character_id": character.character_id}
            # notification_data = esi.get_esi(
            #     character, "get_characters_character_id_notifications", **esi_params
            # )

            # ld = notification_data.data

            # with self.scheduler.app.app_context():
            #     notification = db.session.query(CharacterNotifications).filter_by(character_id=character.character_id).first()

            # if notification:
            #     # Update the fields
            #     notification.total_sp = ld["total_sp"]
            #     notification.unallocated_sp = ld["unallocated_sp"]
                
            #     # Commit the changes
            #     with self.scheduler.app.app_context():
            #         db.session.commit()
            #     print(f"Updated NotificationSet for character, {character.character_name}")
            # else:
            #     notification_row = CharacterNotifications(
            #         character_id=character.character_id,
            #         total_sp=ld["total_sp"],
            #         unallocated_sp=ld["unallocated_sp"]
            #         )


            #     with self.scheduler.app.app_context():
            #         db.session.merge(notification_row)
            #         db.session.commit()                
