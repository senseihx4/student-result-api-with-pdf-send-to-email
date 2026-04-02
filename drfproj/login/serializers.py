from rest_framework import serializers
from .models import User, reports, Subject, SubjectScore


class UserSerializer(serializers.ModelSerializer):
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)
    password = serializers.CharField(write_only=True, required=True)
    username = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username',
            'user_type', 'user_type_display',
            'password', 'profile_picture', 'is_verified',
        ]
        read_only_fields = ['id', 'is_verified']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        return user


class otpserializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class SubjectScoreSerializer(serializers.Serializer):
    subject_id = serializers.IntegerField()
    score = serializers.IntegerField(min_value=0)


class checkresultserializer(serializers.ModelSerializer):
    scores = serializers.SerializerMethodField()

    class Meta:
        model = reports
        fields = ['total_score', 'percentage', 'scores']

    def get_scores(self, obj):
        return [
            {'subject': s.subject.name, 'score': s.score}
            for s in obj.scores.select_related('subject').all()
        ]


class UploadScoreSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    username = serializers.CharField(write_only=True)
    class_name = serializers.CharField(required=False, allow_blank=True)
    scores = SubjectScoreSerializer(many=True)

    def validate_scores(self, scores):
        subject_ids = [s['subject_id'] for s in scores]
        existing = set(Subject.objects.filter(id__in=subject_ids).values_list('id', flat=True))
        missing = set(subject_ids) - existing
        if missing:
            raise serializers.ValidationError(f"Subject IDs not found: {missing}")
        return scores

    def create(self, validated_data):
        scores_data = validated_data.pop('scores')
        class_name = validated_data.pop('class_name', None)
        student = validated_data['user']

        subjects = {s.id: s for s in Subject.objects.filter(id__in=[s['subject_id'] for s in scores_data])}

        total = sum(s['score'] for s in scores_data)
        max_total = sum(subjects[s['subject_id']].max_score for s in scores_data)
        percentage = round((total / max_total) * 100, 2) if max_total > 0 else 0.0

        report = reports.objects.create(
            user=student,
            name=student.username,
            class_name=class_name,
            total_score=total,
            percentage=percentage,
        )

        SubjectScore.objects.bulk_create([
            SubjectScore(report=report, subject=subjects[s['subject_id']], score=s['score'])
            for s in scores_data
        ])

        return report
