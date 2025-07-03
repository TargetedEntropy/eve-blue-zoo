from sqlalchemy.orm.exc import NoResultFound
from apps.authentication.models import Features
from apps.authentication.models import Characters
from apps import db


def is_feature_enabled(app: object, character_id: int, feature_name: str) -> bool:
    """Check if a feature is enabled for a given character.

    Args:
        character_id (int): The ID of the character.
        feature_name (str): The name of the feature to check.

    Returns:
        bool: True if the feature is enabled, False otherwise.
    """
    with app.app_context():  # Adjust for your app's context handling
        feature_record = Features.query.filter_by(character_id=character_id).first()
        if not feature_record or not feature_record.features:
            return False

        # Check if the feature is enabled in the JSON blob
        return feature_record.features.get(feature_name, False)


def update_feature(
    app: object, character_id: int, feature_name: str, is_enabled: bool
) -> None:
    """Enable or disable a feature for a character.

    Args:
        character_id (int): The ID of the character.
        feature_name (str): The name of the feature to update.
        is_enabled (bool): Whether the feature should be enabled.
    """
    with app.app_context():
        feature_record = Features.query.filter_by(character_id=character_id).first()
        if not feature_record:
            # Create a new feature record if it doesn't exist
            feature_record = Features(
                character_id=character_id, features={feature_name: is_enabled}
            )
            db.session.add(feature_record)
        else:
            # Update the feature in the JSON blob
            feature_record.features[feature_name] = is_enabled
        db.session.commit()


def invalidate_sso(app: object, character_id: int) -> None:
    """Set the sso_is_valid field to False for a specific character.

    Args:
        app (object): The Flask app instance.
        character_id (int): The ID of the character.
    """
    with app.app_context():
        # Find the character by character_id
        character = Characters.query.filter_by(character_id=character_id).first()
        if not character:
            print(f"Character with ID {character_id} not found.")
            return

        # Set the sso_is_valid field to False
        character.sso_is_valid = False
        db.session.commit()
        print(f"sso_is_valid set to False for character {character_id}.")
