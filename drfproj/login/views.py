import io
from rest_framework import filters

from django.http import FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from .models import User, reports, pdfreport, Subject, SubjectScore
from django.core.files.base import ContentFile
from django.contrib.auth import login
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
import random
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from .serializers import UserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from .serializers import checkresultserializer, otpserializer, UploadScoreSerializer
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from rest_framework import generics



class userviewset(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAdminUser()]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data['next'] = '/verify-otp/'
        return response

    def perform_create(self, serializer):
        email = self.request.data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError({'email': 'A user with this email already exists.'})

        user = serializer.save()
        user.verification_token = str(random.randint(100000, 999999))
        user.is_verified = False
        user.save()
        self.request.session['verify_email'] = user.email

        send_mail(
            subject='Your login OTP',
            message=f'Your OTP is: {user.verification_token}\n\nThis code is valid for one use only.',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )


class loginviewset(viewsets.ViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = User.objects.filter(email=email).first()

        if user and user.check_password(password):
            if user.is_verified:
                login(request, user)
                refresh = RefreshToken.for_user(user)
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'Account not verified. Please check your email for the OTP.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'detail': 'Invalid email or password.'}, status=status.HTTP_401_UNAUTHORIZED)


class VerifyOtpViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = otpserializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if user.is_verified:
            return Response({'detail': 'Account already verified.'}, status=status.HTTP_400_BAD_REQUEST)

        if otp == user.verification_token:
            user.is_verified = True
            user.verification_token = None
            user.save()
            return Response({'detail': 'Account verified successfully. You can now log in.'}, status=status.HTTP_200_OK)

        return Response({'detail': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)


class checkresultviewset(viewsets.ViewSet):

    def _verify_admin(self, email, password):
        admin = User.objects.filter(email=email).first()
        if not admin or not admin.check_password(password):
            return None, Response({'detail': 'Invalid email or password.'}, status=status.HTTP_401_UNAUTHORIZED)
        if admin.user_type != 1:
            return None, Response({'detail': 'Only SuperAdmin can perform this action.'}, status=status.HTTP_403_FORBIDDEN)
        return admin, None

    def list(self, request):
        email = request.query_params.get('email')
        if not email:
            return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'detail': 'No user found with this email.'}, status=status.HTTP_404_NOT_FOUND)

        report = reports.objects.filter(user=user).last()
        if not report:
            return Response({'detail': 'No results found for this user.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = checkresultserializer(report)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        admin_email = request.data.get('email')
        admin_password = request.data.get('password')
        username = request.data.get('username')

        if not admin_email or not admin_password or not username:
            return Response({'detail': 'Email, password, and username are required.'}, status=status.HTTP_400_BAD_REQUEST)

        _, err = self._verify_admin(admin_email, admin_password)
        if err:
            return err

        student = User.objects.filter(username=username).first()
        if not student:
            return Response({'detail': 'No user found with that username.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UploadScoreSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(user=student)
        return Response({'detail': 'Scores uploaded successfully.'}, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        admin_email = request.data.get('email')
        admin_password = request.data.get('password')
        username = request.data.get('username')

        if not admin_email or not admin_password or not username:
            return Response({'detail': 'Email, password, and username are required.'}, status=status.HTTP_400_BAD_REQUEST)

        _, err = self._verify_admin(admin_email, admin_password)
        if err:
            return err

        student = User.objects.filter(username=username).first()
        if not student:
            return Response({'detail': 'No user found with that username.'}, status=status.HTTP_404_NOT_FOUND)

        report = reports.objects.filter(user=student).last()
        if not report:
            return Response({'detail': 'No results found for this student.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UploadScoreSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        
        report.scores.all().delete()
        scores_data = serializer.validated_data['scores']
        subjects = {s.id: s for s in Subject.objects.filter(id__in=[s['subject_id'] for s in scores_data])}
        total = sum(s['score'] for s in scores_data)
        max_total = sum(subjects[s['subject_id']].max_score for s in scores_data)
        report.total_score = total
        report.percentage = round((total / max_total) * 100, 2) if max_total > 0 else 0.0
        report.save()

        SubjectScore.objects.bulk_create([
            SubjectScore(report=report, subject=subjects[s['subject_id']], score=s['score'])
            for s in scores_data
        ])

        return Response({'detail': 'Scores updated successfully.'}, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        admin_email = request.data.get('email')
        admin_password = request.data.get('password')
        username = request.data.get('username')

        if not admin_email or not admin_password or not username:
            return Response({'detail': 'Email, password, and username are required.'}, status=status.HTTP_400_BAD_REQUEST)

        _, err = self._verify_admin(admin_email, admin_password)
        if err:
            return err

        student = User.objects.filter(username=username).first()
        if not student:
            return Response({'detail': 'No user found with that username.'}, status=status.HTTP_404_NOT_FOUND)

        report = reports.objects.filter(user=student).last()
        if not report:
            return Response({'detail': 'No results found for this student.'}, status=status.HTTP_404_NOT_FOUND)

        report.delete()
        return Response({'detail': 'Report deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


class GeneratePDF(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        student_report = reports.objects.filter(user=request.user).last()
        if not student_report:
            return Response({'error': 'No report found for this user.'}, status=status.HTTP_404_NOT_FOUND)

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)

        p.setFont("Helvetica-Bold", 18)
        p.drawString(200, 770, "Student Result Report")

        # Draw profile picture if it exists
        profile_pic = student_report.user.profile_picture
        if profile_pic:
            try:
                from reportlab.lib.utils import ImageReader
                img = ImageReader(profile_pic.path)
                p.drawImage(img, 450, 700, width=80, height=80, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass

        p.setFont("Helvetica", 12)
        p.drawString(50, 730, f"Name         : {student_report.user.username}")
        p.drawString(50, 710, f"Class        : {student_report.class_name}")
        p.drawString(50, 680, "--------------------------------------------")

        y = 660
        for subject_score in student_report.scores.select_related('subject').all():
            p.drawString(50, y, f"{subject_score.subject.name:<15}: {subject_score.score}")
            y -= 20

        p.drawString(50, y - 10, "--------------------------------------------")
        p.drawString(50, y - 30, f"Total Score  : {student_report.total_score}")
        p.drawString(50, y - 50, f"Percentage   : {student_report.percentage}%")

        p.showPage()
        p.save()

        pdf_content = buffer.getvalue()

        pdf_record = pdfreport(user=request.user)
        pdf_record.report_file.save('report.pdf', ContentFile(pdf_content), save=True)

        email = EmailMessage(
            subject='Your PDF Report',
            body='Please find attached your PDF report.',
            from_email=settings.EMAIL_HOST_USER,
            to=[request.user.email],
        )
        email.attach('report.pdf', pdf_content, 'application/pdf')
        email.send(fail_silently=False)

        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='report.pdf', content_type='application/pdf')







class UserList(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = {
        'username': ['icontains', 'exact'],
        
    }
    search_fields = ['username', 'email', 'reports__scores__subject__name']
    









