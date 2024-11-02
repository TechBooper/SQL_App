# permissions.py

from models import User, Permission


def has_permission(user_id, entity, action, resource_owner_id=None):
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
