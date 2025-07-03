"""Notification Tasks"""

from apps.authentication.models import (
    Characters,
    CharacterNotifications,
    SentNotifications,
    Users,
    SkillSet,
    Contract,
    ContractItem,
    ContractTrack,
    InvType,
    ContractNotify,
)
from apps import esi, db, discord_client
from ..common import is_feature_enabled


class ContractWatch:
    """Tasks related to Watching Contracts"""

    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.schedule_tasks()
        # self.discord = DiscordOAuth2Session(app)

    def schedule_tasks(self) -> None:
        """Setup task execution schedule"""
        self.scheduler.add_job(
            func=self.main,
            trigger="interval",
            seconds=340,
            id="contract_watch_main",
            name="contract_watch_main",
            replace_existing=False,
            max_instances=1
        )

    def get_all_users(self) -> list:
        """Gets all characters"""
        with self.scheduler.app.app_context():
            character_list = CharacterNotifications.query.all()
        return character_list

    def send_discord_msg(self, user_id: str, msg: str) -> None:
        print("sending notification")
        dm_channel = discord_client.bot_request(
            "/users/@me/channels", "POST", json={"recipient_id": user_id}
        )
        return discord_client.bot_request(
            f"/channels/{dm_channel['id']}/messages",
            "POST",
            json={"content": msg},
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

    def get_unnotified_matching_contracts(self, character_id: int) -> list:
        """Get contract items that match watched contract types and haven't been notified yet"""
        with self.scheduler.app.app_context():
            # Find matching contract items and contract watch entries for the same type_id
            matching_items = (
                db.session.query(ContractItem, ContractTrack.id)
                .join(ContractTrack, ContractItem.type_id == ContractTrack.type_id)
                .all()
            )
            print(f"matching_items: {matching_items}")
            # Unpack the tuple into separate variables
            new_matches = []
            for item, watch_id in matching_items:
                # Now 'item' is a ContractItem, and 'watch_id' is ContractWatch.id
                existing_notify = ContractNotify.query.filter_by(
                    character_id=character_id, contract_id=item.contract_id
                ).first()
                if not existing_notify:
                    new_matches.append(
                        (item, item.contract_id)
                    )  # Storing the tuple with both values

        return new_matches

    def get_type_name(self, type_id: int) -> str:
        """Get the typeName for a given typeID"""
        with self.scheduler.app.app_context():
            inv_type = InvType.query.filter_by(typeID=type_id).first()
            return inv_type.typeName if inv_type else None

    def add_contract_notification(self, character_id: int, contract_id: int) -> None:
        """Add a new contract notification entry"""
        with self.scheduler.app.app_context():
            new_notification = ContractNotify(
                character_id=character_id, contract_id=contract_id
            )
            db.session.add(new_notification)
            db.session.commit()

    def main(self):
        print("Running Contracts Watch Main")

        characters = self.get_all_users()

        for character in characters:
            # Make sure there's something here
            if not character.enabled_notifications:
                continue

            # If we don't have a discord ID, no point in going on
            with self.scheduler.app.app_context():
                user = Users.query.filter(
                    Users.character_id == character.master_character_id
                ).first()
            if not user.discord_user_id:
                continue

            if "contract-task" in character.enabled_notifications:
                data = self.get_unnotified_matching_contracts(character.character_id)
                for item, watch_id in data:
                    item_name = self.get_type_name(item.type_id)
                    print(f"ItemName: {item_name}")

                    # send discord message
                    self.send_discord_msg(
                        user.discord_user_id, msg=f"Found a {item_name}"
                    )
                    self.add_contract_notification(character.character_id, watch_id)
