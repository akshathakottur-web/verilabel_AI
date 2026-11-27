from django.utils import timezone


def review_scan(scan, reviewer, note):
    """Marks a finished scan as Reviewed. Raises ValueError with a message the page can show."""
    note = (note or '').strip()
    if scan.status != 'done':
        raise ValueError('Only a finished scan (status "done") can be reviewed.')
    if scan.review_status == 'reviewed':
        raise ValueError('This scan has already been reviewed.')
    if not note:
        raise ValueError('Please type the confirmation text.')
    if len(note) > 1000:
        raise ValueError('The confirmation text must be at most 1000 characters.')
    scan.review_status = 'reviewed'
    scan.reviewed_by = reviewer
    scan.reviewed_at = timezone.now()
    scan.review_note = note
    scan.save(update_fields=['review_status', 'reviewed_by', 'reviewed_at', 'review_note'])
    return scan