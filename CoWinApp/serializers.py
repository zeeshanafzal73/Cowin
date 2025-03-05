from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

from .models import SetGoals, ResumeCV, CoverLetter, FlashCardInterviewQuestion, FreeMockInterview, ProPilotLauncher, \
    AiInterviewProPilot, AiProPilotLauncher, AiCodingMaths, \
    AiCodingMathsProPilotLauncher, ResumeTemplate, CoverLetterTemplate, Temperature, Models, TemperatureChoices, Users, \
    UserDetails


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
            'is_superuser',
            'first_name',
            'last_name',
            'date_joined',
            'is_active'
        ]

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()

        return user


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['profile']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['username'] = UserSerializer(instance.userId).data['username'] if instance.userId else None
        representation['email'] = UserSerializer(instance.userId).data['email'] if instance.userId else None
        return representation

class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    class Meta:
        fields = ("email",)


class ResetPasswordSerializer(serializers.Serializer):
    key = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    class Meta:
        fields = (
            "key",
            "new_password",
            "confirm_password",
        )
        write_only_fields = ("key", "new_password", "confirm_password")

    def validate(self, data):
        print(data)
        encoded_user = data.get("key")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")
        try:
            decoded_user = urlsafe_base64_decode(encoded_user).decode()
            user = User.objects.get(email=decoded_user)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        if new_password != confirm_password:
            raise serializers.ValidationError(
                "New password and confirm password must match"
            )
        user.set_password(new_password)
        user.save()
        return data


class SetGoalsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SetGoals
        fields = [
            'userId',
            'id',
            'position',
            'company_name',
            'programing_language',
            'location',
            'isActive'
        ]


class ResumeCVSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeCV
        fields = [
            'userId',
            'id',
            'CV_document',
            'upload_date',
            'isActive',
        ]
        extra_kwargs = {
            'isActive': {'required': False},
        }

    def get_cv_name(self, obj):
        cv_name = obj.CV_document.name.split('/')[-1]
        return cv_name

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['cv_name'] = self.get_cv_name(instance)
        return data


class CoverLetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverLetter
        fields = [
            'userId',
            'id',
            'Letter_document',
            'upload_date',
            'isActive',
        ]

    def get_cl_name(self, obj):
        cl_name = obj.Letter_document.name.split('/')[-1]
        return cl_name

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['cl_name'] = self.get_cl_name(instance)
        return data


class CvSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeTemplate
        fields = '__all__'


class CLSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverLetterTemplate
        fields = '__all__'


class FlashCardInterviewQuestionsSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    subcategory_name = serializers.SerializerMethodField()

    class Meta:
        model = FlashCardInterviewQuestion
        fields = [
            'id',
            'question',
            'answer',
            'category_name',
            'subcategory_name',
        ]

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_subcategory_name(self, obj):
        return obj.subcategory.name if obj.subcategory else None

class SetGoalsLookups(serializers.ModelSerializer):
    class Meta:
        model = SetGoals
        fields = ['id', 'userId', 'position', 'company_name', 'programing_language']


class FreeMockCreationSerializers(serializers.ModelSerializer):
    class Meta:
        model = FreeMockInterview
        fields = '__all__'
        read_only_fields = ['isActive']


class FreeMockGetSerializers(serializers.ModelSerializer):
    class Meta:
        model = FreeMockInterview
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('goals')
        representation['position'] = SetGoalsSerializer(instance.goals).data['position'] if instance.goals else None
        representation['company'] = SetGoalsSerializer(instance.goals).data['company_name'] if instance.goals else None
        return representation


class ResumeCvLookupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeCV
        fields = ['id', 'CV_document']

    def get_cv_name(self, obj):
        cv_name = obj.CV_document.name.split('/')[-1]
        return cv_name

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['cv_name'] = self.get_cv_name(instance)
        return data


class CoverLetterLookupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverLetter
        fields = ['id', 'Letter_document']

    def get_cl_name(self, obj):
        cl_name = obj.Letter_document.name.split('/')[-1]
        return cl_name

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['cl_name'] = self.get_cl_name(instance)
        return data


class PositionLookupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SetGoals
        fields = ['id', 'position']


class LanguageLookupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SetGoals
        fields = ['id', 'programing_language']


class ProPilotLauncherSerializers(serializers.ModelSerializer):
    class Meta:
        model = ProPilotLauncher
        fields = '__all__'


class AiInterviewCreationSerializers(serializers.ModelSerializer):
    class Meta:
        model = AiInterviewProPilot
        fields = '__all__'
        read_only_fields = ['isActive']


class AiInterviewGetSerializers(serializers.ModelSerializer):
    class Meta:
        model = AiInterviewProPilot
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('goals')
        representation['position'] = SetGoalsSerializer(instance.goals).data['position'] if instance.goals else None
        representation['company'] = SetGoalsSerializer(instance.goals).data['company_name'] if instance.goals else None
        return representation


class AiProPilotLauncherSerializers(serializers.ModelSerializer):
    class Meta:
        model = AiProPilotLauncher
        fields = '__all__'


class AiCodingMathsCreationSerializers(serializers.ModelSerializer):
    class Meta:
        model = AiCodingMaths
        fields = '__all__'
        read_only_fields = ['isActive']


class AiCodingMathsGetSerializers(serializers.ModelSerializer):
    class Meta:
        model = AiCodingMaths
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('goals')
        representation['position'] = SetGoalsSerializer(instance.goals).data['position'] if instance.goals else None
        representation['company'] = SetGoalsSerializer(instance.goals).data['company_name'] if instance.goals else None
        representation['language'] = SetGoalsSerializer(instance.goals).data[
            'programing_language'] if instance.goals else None
        return representation


class AiCodingMathsProPilotSerializers(serializers.ModelSerializer):
    class Meta:
        model = AiCodingMathsProPilotLauncher
        fields = ['userId', 'resume', 'cover_letter', 'programing_language', 'add_goal', 'additional_details']
        read_only_fields = ['created_at']


class AiCodingProPilotSerializers(serializers.ModelSerializer):
    class Meta:
        model = AiCodingMathsProPilotLauncher
        fields = '__all__'


class TemperatureSerializers(serializers.ModelSerializer):
    class Meta:
        model = Temperature
        fields = '__all__'
        read_only_fields = ['created_at']


class ModelsSerializers(serializers.ModelSerializer):
    class Meta:
        model = Models
        fields = '__all__'


class TemperatureChoicesSerializers(serializers.ModelSerializer):
    class Meta:
        model = TemperatureChoices
        fields = '__all__'


class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDetails
        fields = ['id', 'latest_resume', 'latest_goal']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user'] = UserSerializer(instance.user).data['username'] if instance.user else None
        return representation
