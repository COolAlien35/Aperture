from enum import Enum
from typing import Set

class Role(str, Enum):
    ADMIN = "Admin"
    TEAM_LEAD = "Team Lead"
    DEVELOPER = "Developer"

# Define the models each role is permitted to call.
# Admin has access to everything, Team Lead gets expensive reasoning models, 
# Developer gets standard/fast models.
ROLE_MODEL_PERMISSIONS = {
    Role.ADMIN: {"*"},  # Wildcard for all models
    Role.TEAM_LEAD: {
        "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo",
        "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"
    },
    Role.DEVELOPER: {
        "gpt-3.5-turbo", "claude-3-haiku-20240307", "claude-3-sonnet-20240229"
    }
}

def can_access_model(role_str: str, requested_model: str) -> bool:
    """
    Checks if the given role is allowed to invoke the requested model.
    """
    try:
        role = Role(role_str)
    except ValueError:
        # If the role is unknown, default to safest restrictions (or deny completely)
        return False

    allowed_models: Set[str] = ROLE_MODEL_PERMISSIONS.get(role, set())
    
    if "*" in allowed_models:
        return True
        
    return requested_model in allowed_models
