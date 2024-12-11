"""Notification Tasks"""

from apps.authentication.models import (
    Characters,
    CharacterNotifications,
    SentNotifications,
    Users,
    SkillSet,
)
from apps import esi, db, discord_client
from ..common import is_feature_enabled


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
            seconds=3600,
            id="notification_main",
            name="notification_main",
            replace_existing=False,
        )

    def get_all_users(self) -> list:
        """Gets all characters"""
        with self.scheduler.app.app_context():
            character_list = CharacterNotifications.query.all()
        return character_list

    def send_discord_msg(
        self, user_id: str, character_name: str, skill_points: int
    ) -> None:
        print("sending notification")
        dm_channel = discord_client.bot_request(
            "/users/@me/channels", "POST", json={"recipient_id": user_id}
        )
        return discord_client.bot_request(
            f"/channels/{dm_channel['id']}/messages",
            "POST",
            json={
                "content": f"Hello! {character_name} is ready to harvest with {skill_points:,}!"
            },
        )

    def should_notifications_be_sent(self, character_id):
        # reset notification
        with self.scheduler.app.app_context():
            notification_count = (
                SentNotifications.query.filter(
                    SentNotifications.character_id == character_id
                )
                .filter(SentNotifications.notification_cleared == False)
                .count()
            )

        if notification_count > 0:
            return False
        else:
            return True

    def main(self):
        print("Running Notification Main")

        from datetime import datetime

        print(f"now = {datetime.now()}")

        characters = self.get_all_users()

        for character in characters:
            # Make sure there's something here
            if not character.enabled_notifications:
                continue

            # Have we already sent a notification for this character that needs to be cleared?
            if not self.should_notifications_be_sent(character.character_id):
                # reset notification
                with self.scheduler.app.app_context():
                    notification_histories = (
                        SentNotifications.query.filter(
                            SentNotifications.character_id == character.character_id
                        )
                        .filter(SentNotifications.notification_cleared == False)
                        .all()
                    )

                    skill_info = SkillSet.query.filter(
                        SkillSet.character_id == character.character_id
                    ).one()

                for notification_history in notification_histories:
                    if notification_history.total_sp == skill_info.total_sp:
                        continue
                    if notification_history.total_sp > skill_info.total_sp:
                        notification_history.notification_cleared = True

                        with self.scheduler.app.app_context():
                            db.session.merge(notification_history)
                            db.session.commit()
                continue

            # If we don't have a discord ID, no point in going on
            with self.scheduler.app.app_context():
                user = Users.query.filter(
                    Users.character_id == character.master_character_id
                ).first()
            if not user.discord_user_id:
                continue

            if character.enabled_notifications == "sp-farm-notification":
                with self.scheduler.app.app_context():
                    character_skill_info = SkillSet.query.filter(
                        SkillSet.character_id == character.character_id
                    ).one()

                    character_info = Characters.query.filter(
                        Characters.character_id == character.character_id
                    ).one()

                if character_skill_info.total_sp > 5500000:
                    print(
                        f"{character_info.character_name} is ready for harvest with sp: {character_skill_info.total_sp:,}!"
                    )

                    # send discord message
                    self.send_discord_msg(
                        user.discord_user_id,
                        character_info.character_name,
                        character_skill_info.total_sp,
                    )

                    # save total_sp to SentNotifications
                    with self.scheduler.app.app_context():
                        sent_notification = SentNotifications(
                            character_id=character.character_id,
                            master_character_id=character.master_character_id,
                            total_sp=character_skill_info.total_sp,
                        )

                        db.session.add(sent_notification)
                        db.session.commit()
