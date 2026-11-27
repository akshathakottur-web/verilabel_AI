from celery import shared_task

from compliance.engine import run_compliance
from scans.models import Scan

from .vision_adapter import get_vision_result


@shared_task
def process_scan(scan_id):
    scan = Scan.objects.filter(id=scan_id).first()
    if scan is None:
        return

    scan.status = 'processing'
    scan.save(update_fields=['status'])

    try:
        vision_result = get_vision_result(scan.image.path)
        scan.vision_result = vision_result

        quality = vision_result.get('image_quality', {})
        if quality.get('status') == 'too_low':
            scan.status = 'low_quality'
            scan.compliance_result = {
                'image_quality_warning': quality.get('reason') or 'The photo quality is too low.',
                'rules': [],
                'score': None,
                'verdict': None,
            }
            scan.score = None
            scan.verdict = ''
        else:
            extracted_fields, compliance_result = run_compliance(vision_result)
            scan.extracted_fields = extracted_fields
            scan.compliance_result = compliance_result
            scan.score = compliance_result.get('score')
            scan.verdict = compliance_result.get('verdict') or ''
            food_name = (extracted_fields.get('food_name') or {}).get('value') or ''
            scan.product_name = str(food_name)[:200]
            scan.status = 'done'
    except Exception as error:
        scan.status = 'failed'
        scan.error_message = str(error)[:1000]

    scan.save()