from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Users(models.Model):
    userId = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='Users')
    profile = models.ImageField(null=True, blank=True, upload_to='images/')
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)
    isPaid = models.BooleanField(default=False)

    def is_otp_expired(self):
        if self.otp_expiry:
            return timezone.now() > self.otp_expiry
        return True

    def set_otp_expiry(self, expiry_duration):
        self.otp_expiry = timezone.now() + timedelta(seconds=expiry_duration)


class SetGoals(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='User_Set_Goals')
    position = models.CharField(max_length=500, null=True, blank=True, default='null')
    company_name = models.CharField(max_length=500, null=True, blank=True, default='null')
    programing_language = models.CharField(max_length=500, null=True, blank=True, default='null')
    location = models.CharField(max_length=500, null=True, blank=True, default='null')
    isActive = models.BooleanField(null=True, blank=True, default=True)

    def __str__(self):
        return self.company_name


class ResumeCV(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='User_CV')
    CV_document = models.FileField(upload_to='CV_Documents/', null=True, blank=True)
    upload_date = models.DateField(auto_now_add=True, null=True, blank=True)
    isActive = models.BooleanField(null=True, blank=True, default=True)


class CoverLetter(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='User_CoverLetter')
    Letter_document = models.FileField(upload_to='CL_Documents/', null=True, blank=True)
    upload_date = models.DateField(auto_now_add=True, null=True, blank=True)
    isActive = models.BooleanField(null=True, blank=True, default=True)


class ResumeTemplate(models.Model):
    CV_template_Pdf = models.FileField(upload_to='CV_Template/Pdf/', null=True, blank=True)
    CV_template_Word = models.FileField(upload_to='CV_Template/Word/', null=True, blank=True)
    IsPaid = models.BooleanField(default=False)


class CoverLetterTemplate(models.Model):
    CL_template_Pdf = models.FileField(upload_to='CL_Template/Pdf/', null=True, blank=True)
    CL_template_Word = models.FileField(upload_to='CL_Template/Word', null=True, blank=True)
    IsPaid = models.BooleanField(default=False)


class AICategory(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class AISubcategory(models.Model):
    category = models.ForeignKey(AICategory, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class FlashCardInterviewQuestion(models.Model):
    question = models.CharField(max_length=500, null=True, blank=True, default='null')
    answer = models.TextField(max_length=1000, null=True, blank=True, default='null')
    date_added = models.DateField(auto_now_add=True)
    category = models.ForeignKey(AICategory, on_delete=models.CASCADE, null=True, blank=True)
    subcategory = models.ForeignKey(AISubcategory, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.question


class FreeMockInterview(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, related_name='FreeMockInterviews')
    goals = models.ForeignKey(SetGoals, on_delete=models.CASCADE)
    InterviewTime = models.DateTimeField(null=True, blank=True)
    IsActive = models.BooleanField(default=True)


class ProPilotLauncher(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Pro_Pilot_User')
    resume = models.ForeignKey(ResumeCV, on_delete=models.CASCADE)
    cover_letter = models.ForeignKey(CoverLetter, on_delete=models.CASCADE)
    position = models.ForeignKey(SetGoals, on_delete=models.CASCADE)
    additional_details = models.TextField(null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)


class AiInterviewProPilot(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, related_name='AiInterviews')
    goals = models.ForeignKey(SetGoals, on_delete=models.CASCADE)
    InterviewTime = models.DateTimeField(null=True, blank=True)
    IsActive = models.BooleanField(default=True, )


class AiProPilotLauncher(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Ai_Pro_Pilot_User')
    resume = models.ForeignKey(ResumeCV, on_delete=models.CASCADE)
    cover_letter = models.ForeignKey(CoverLetter, on_delete=models.CASCADE)
    position = models.ForeignKey(SetGoals, on_delete=models.CASCADE)
    additional_details = models.TextField(null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)


class AiCodingMaths(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Ai_Coding_Maths')
    goals = models.ForeignKey(SetGoals, on_delete=models.CASCADE)
    IsActive = models.BooleanField(default=True)


class AiCodingMathsProPilotLauncher(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, related_name='AiCodingMaths_Pro_Pilot_User')
    resume = models.ForeignKey(ResumeCV, on_delete=models.CASCADE)
    cover_letter = models.ForeignKey(CoverLetter, on_delete=models.CASCADE)
    programing_language = models.ForeignKey(SetGoals, on_delete=models.CASCADE)
    add_goal = models.TextField(null=True, blank=True)
    additional_details = models.TextField(null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)


class TemperatureChoices(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='choice_temperatures')
    minimum_temperature = models.FloatField(null=True, blank=True)
    maximum_temperature = models.FloatField(null=True, blank=True)
    default_temperature = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Temperature Choices for {self.user.username}"


class Temperature(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, related_name='temperatures')
    temperature_choice = models.FloatField(default=0.5)
    created_at = models.DateField(auto_now_add=True)


class UserDetails(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    latest_resume = models.TextField(null=True, blank=True)
    latest_goal = models.TextField()
    latest_temperature = models.DecimalField(max_digits=5, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"UserDetails for {self.user.username}"


class MaxToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.IntegerField()
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return str(self.token)


class ModelChoice(models.Model):
    choice = models.CharField(max_length=50)

    def __str__(self):
        return self.choice


class Models(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    model_name = models.ForeignKey(ModelChoice, on_delete=models.CASCADE, default='llama2-70b-4096')
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'model_name')


class Images(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/')
