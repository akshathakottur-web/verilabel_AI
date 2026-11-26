
def can_view_scan(user, scan):
    """Owner, Admin, or an Inspector looking at a customer's scan."""
    if scan.uploaded_by_id == user.id:
        return True
    if user.role == 'admin':
        return True
    if user.role == 'inspector' and scan.uploaded_by.role == 'customer':
        return True
    return False
