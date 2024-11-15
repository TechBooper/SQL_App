"""Permissions module for Epic Events CRM.

This module handles permission checks for user actions on various entities,
ensuring that users have the appropriate rights to perform actions like create,
read, update, or delete on clients, contracts, and events.
"""

from models import User, Permission

def has_permission(user_id, entity, action, resource_owner_id=None):
    """Check if a user has permission to perform a specific action on an entity.

    Args:
        user_id (int): The ID of the user attempting the action.
        entity (str): The entity type ('client', 'contract', 'event').
        action (str): The action to perform ('create', 'read', 'update', 'delete').
        resource_owner_id (int, optional): The ID of the resource owner, if applicable.

    Returns:
        bool: True if the user has the required permission, False otherwise.
    """
    user = User.get_by_id(user_id)
    if not user:
        return False

    # Check if the user has the permission for the action
    permissions = Permission.get_permissions_by_role(user.role_id)
    has_perm = False
    for perm in permissions:
        if perm.entity == entity and perm.action == action:
            has_perm = True
            break

    if not has_perm:
        return False

    # Ownership checks for certain actions
    if action in ["update", "delete"] and entity in ["client", "contract", "event"]:
        if user.role.name == "Management":
            # Management can update/delete any resource
            return True
        else:
            # For Sales and Support, check ownership
            if resource_owner_id is not None:
                return user_id == resource_owner_id
            else:
                # Ownership ID not provided; deny access
                return False

    # For create actions, additional ownership checks may apply
    if action == "create" and entity == "event" and user.role.name == "Sales":
        # Sales can only create events for their clients
        return resource_owner_id == user_id

    # If no ownership check is needed
    return True
