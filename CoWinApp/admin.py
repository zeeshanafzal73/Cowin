from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import SetGoals, Users, ResumeCV, CoverLetter, AICategory, AISubcategory, FlashCardInterviewQuestion, \
    FreeMockInterview, ProPilotLauncher, AiInterviewProPilot, AiProPilotLauncher, AiCodingMaths, \
    AiCodingMathsProPilotLauncher, CoverLetterTemplate, ResumeTemplate, Temperature, UserDetails, Models, ModelChoice, \
    TemperatureChoices, Images, MaxToken

admin.site.site_header = 'Cowin Admin'


@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('userId', 'profile', 'otp')


@admin.register(SetGoals)
class SetGoalsAdmin(admin.ModelAdmin):
    list_display = ('id', 'userId', 'company_name', 'position', 'programing_language', 'isActive')
    search_fields = ('userId', 'company_name', 'position', 'location')
    list_filter = ('isActive',)


@admin.register(ResumeCV)
class ResumeCVAdmin(admin.ModelAdmin):
    list_display = ('id', 'userId', 'CV_document', 'upload_date', 'isActive')
    search_fields = ('CV_document', 'upload_date', 'isActive')
    list_filter = ('CV_document', 'upload_date', 'isActive')


@admin.register(CoverLetter)
class CoverLetterAdmin(admin.ModelAdmin):
    list_display = ('id', 'userId', 'Letter_document', 'upload_date', 'isActive')
    search_fields = ('Letter_document', 'upload_date', 'isActive')
    list_filter = ('Letter_document', 'upload_date', 'isActive')


@admin.register(AICategory)
class AICategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(AISubcategory)
class AISubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(FlashCardInterviewQuestion)
class FlashCardInterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer', 'date_added', 'category', 'subcategory')
    search_fields = ('question', 'answer', 'date_added', 'category', 'subcategory')
    list_filter = ('question', 'answer', 'date_added', 'category', 'subcategory')


@admin.register(FreeMockInterview)
class FreeMockInterview(admin.ModelAdmin):
    list_display = ('id', 'userId', 'goals', 'InterviewTime', 'IsActive')


@admin.register(ProPilotLauncher)
class ProPilotLauncher(admin.ModelAdmin):
    list_display = ('id', 'userId', 'resume', 'cover_letter', 'position', 'additional_details')


@admin.register(AiInterviewProPilot)
class FreeMockInterview(admin.ModelAdmin):
    list_display = ('id', 'userId', 'goals', 'InterviewTime', 'IsActive')


@admin.register(AiProPilotLauncher)
class ProPilotLauncher(admin.ModelAdmin):
    list_display = ('id', 'userId', 'resume', 'cover_letter', 'position', 'additional_details')


@admin.register(AiCodingMaths)
class AiCodingMaths(admin.ModelAdmin):
    list_display = ('id', 'userId', 'goals', 'IsActive')


@admin.register(AiCodingMathsProPilotLauncher)
class AiCodingMathsProPilot(admin.ModelAdmin):
    list_display = (
        'id', 'userId', 'resume', 'cover_letter', 'programing_language', 'add_goal', 'additional_details', 'created_at')


@admin.register(ResumeTemplate)
class ResumeTemp(admin.ModelAdmin):
    list_display = ('id', 'CV_template_Pdf', 'CV_template_Word', 'IsPaid')


@admin.register(CoverLetterTemplate)
class CoverLetterTemp(admin.ModelAdmin):
    list_display = ('id', 'CL_template_Pdf', 'CL_template_Word', 'IsPaid')


@admin.register(TemperatureChoices)
class TemperatureChoices(admin.ModelAdmin):
    list_display = ('id', 'user', 'minimum_temperature', 'maximum_temperature', 'default_temperature')


@admin.register(Temperature)
class Temperature(admin.ModelAdmin):
    list_display = ('id', 'userId', 'temperature_choice', 'created_at')


@admin.register(UserDetails)
class Temperature(admin.ModelAdmin):
    list_display = ('id', 'user', 'latest_resume', 'latest_goal', 'latest_temperature', 'updated_at')


@admin.register(Models)
class Models(admin.ModelAdmin):
    list_display = ('id', 'model_name', 'created_at')


@admin.register(ModelChoice)
class ModelChoice(ModelAdmin):
    list_display = ('id', 'choice')


@admin.register(Images)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'image')


@admin.register(MaxToken)
class MaxToken(admin.ModelAdmin):
    list_display = ('id', 'user', 'token', 'created_at')
