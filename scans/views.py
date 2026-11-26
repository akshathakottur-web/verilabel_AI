
import os
from functools import partial

from django.db import transaction
from PIL import Image
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from pipeline.tasks import process_scan

from .models import Batch, Scan
from .permissions import can_view_scan
from .serializers import ScanSerializer

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
MAX_FILE_MB = 10
MAX_FILES_PER_BATCH = 20


def check_image(upload):
    """Returns a problem message, or None if the file is fine."""
    extension = os.path.splitext(upload.name)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        return f'{upload.name}: only JPG or PNG photos are allowed.'
    if upload.size > MAX_FILE_MB * 1024 * 1024:
        return f'{upload.name}: the file is larger than {MAX_FILE_MB} MB.'
    try:
        Image.open(upload).verify()
    except Exception:
        return f'{upload.name}: this file is not a valid image.'
    finally:
        upload.seek(0)
    return None


class ScanListCreateView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        scans = Scan.objects.filter(uploaded_by=request.user).select_related(
            'uploaded_by', 'reviewed_by'
        )
        return Response(ScanSerializer(scans, many=True).data)

    def post(self, request):
        if request.user.role == 'inspector':
            return self.upload_batch(request)
        return self.upload_single(request)

    def upload_single(self, request):
        files = request.FILES.getlist('image')
        if len(files) != 1:
            return Response(
                {'error': 'Please upload exactly one photo in the field "image".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        problem = check_image(files[0])
        if problem:
            return Response({'error': problem}, status=status.HTTP_400_BAD_REQUEST)
        scan = Scan.objects.create(uploaded_by=request.user, image=files[0])
        transaction.on_commit(partial(process_scan.delay, scan.id))
        return Response(
            {'scan_id': scan.id, 'status': scan.status},
            status=status.HTTP_201_CREATED,
        )

    def upload_batch(self, request):
        files = request.FILES.getlist('images')
        if not files:
            return Response(
                {'error': 'Please upload at least one photo in the field "images".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(files) > MAX_FILES_PER_BATCH:
            return Response(
                {'error': f'You can upload at most {MAX_FILES_PER_BATCH} photos at once.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for upload in files:
            problem = check_image(upload)
            if problem:
                return Response({'error': problem}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            batch = Batch.objects.create(created_by=request.user)
            scans = [
                Scan.objects.create(uploaded_by=request.user, batch=batch, image=upload)
                for upload in files
            ]
            for scan in scans:
                transaction.on_commit(partial(process_scan.delay, scan.id))
        return Response(
            {
                'batch_id': batch.id,
                'scans': [{'scan_id': s.id, 'status': s.status} for s in scans],
            },
            status=status.HTTP_201_CREATED,
        )


class ScanDetailView(APIView):
    def get(self, request, scan_id):
        scan = (
            Scan.objects.select_related('uploaded_by', 'reviewed_by')
            .filter(id=scan_id)
            .first()
        )
        if scan is None or not can_view_scan(request.user, scan):
            return Response({'error': 'Scan not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ScanSerializer(scan).data)