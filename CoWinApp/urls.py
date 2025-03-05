from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from . import views

app_name = "CoWinApp"

urlpatterns = [

                  # ------------- AUTHENTICATIONS SECTION ---------------
                  path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
                  path('api-token-auth/', obtain_auth_token, name='api_token_auth'),

                  path("auth/signup/", views.postauthuser, name="authuser"),
                  path("auth/login/", views.loginUser, name="authuserlogin"),
                  path('auth/userprofile/', views.user_profile_api, name='user_profile_api'),
                  path("auth-social/", views.register_or_login, name="register_or_login"),
                  path("auth/update/password/", views.update_password, name="update_password"),
                  path("auth/update/profile-image/", views.update_profile, name="update_profile"),
                  path('auth/delete/profile-image/', views.delete_profile_image, name='delete_profile_image'),
                  path("auth/delete/user/", views.delete_user, name="delete_user"),
                  path("auth/check-user-status/", views.check_user_status, name="check_user_status"),

                  # ------------- FORGET PASSWORD SECTION ---------------

                  path("forget-password/", views.ForgetPasswordView,
                       name="forget-password"),
                  path('verify-opt/', views.VerifyOTP, name="verify-otp"),
                  path("reset-password/", views.ResetPasswordView, name="reset-password"),

                  # ---------------- SET GOALS SECTION ------------------

                  path("subdomain1/set-goals/", views.set_goals, name="set_goals"),
                  path("subdomain1/edit-goals/", views.edit_goals, name="edit_goals"),
                  path("subdomain1/get-all-goals/", views.get_all_goals, name="get_all_goals"),
                  path("subdomain1/inactive-goals/", views.get_archived_goals, name="inactive_goals"),
                  path("subdomain1/active-goals/", views.get_unarchived_goals, name="active_goals"),
                  path("subdomain1/goals-status-change/", views.update_goal_status,
                       name="goals_status_inactive"),
                  path("subdomain1/delete-goals/", views.delete_goal, name="delete_goal"),

                  # ---------------- RESUME SECTION ------------------

                  path("subdomain1/upload-resume/", views.UploadResume, name="upload_resume"),
                  path("subdomain1/update/resume/", views.UpdateResume, name="update_resume"),
                  path("subdomain1/get-all-resume/", views.GetAllResume, name="get_all_resume"),
                  path('subdomain1/download-resume/', views.download_resume, name='download_resume'),
                  path("subdomain1/delete-resume/", views.DeleteResume, name="delete_resume"),

                  # ---------------- COVER LETTER SECTION ------------------

                  path("subdomain1/upload-coverletter/", views.UploadCoverLetter, name="upload_cover_letter"),
                  path("subdomain1/update/coverletter/", views.UpdateCoverLetter,
                       name="update_cover_letter"),
                  path('subdomain1/download-cover-letter/', views.download_cover_letter,
                       name='download_cover_letter'),
                  path("subdomain1/get-all-coverletter/", views.GetAllCoverLetter, name="get_all_cover_letter"),
                  path("subdomain1/delete-coverletter/", views.DeleteCoverLetter, name="delete_cover_letter"),

                  # ----------------- Flash Card SECTION ------------------
                  path("subdomain1/flashcard/", views.FlashCardQA, name="flashcard"),

                  # ----------------- Lookup SECTION ------------------
                  path('subdomain1/get-userset-goals-lookup/', views.GetUserSetGoalsLookup,
                       name="GetUserSetGoalsLookup"),
                  path('subdomain1/resume-lookup/', views.GetUserResumeLookup,
                       name="GetUserResumeLookup"),
                  path('subdomain1/cover-letter-lookup/', views.GetUserCoverLetterLookup,
                       name="GetUserCoverLetterLookup"),
                  path('subdomain1/position-lookup/', views.GetUserPositionLookup,
                       name="GetUserPositionLookup"),
                  path('subdomain1/language-lookup/', views.GetUserLanguageLookup,
                       name="GetUserCoverLetterLookup"),

                  # ----------------- Free Mock Interview SECTION ------------------
                  path('subdomain1/free-mock-creation/', views.FreeMockCreation, name="FreeMockCreation"),
                  path('subdomain1/free-mock-creation-complete/', views.FreeMockCompletion,
                       name="FreeMockCompletion"),
                  path('subdomain1/free-mock-get/', views.FreeMockGetDetails, name="FreeMockGet"),

                  # ----------------- ProLauncher SECTION ------------------
                  path("subdomain1/pro-luancher-create/", views.ProPilotLauncherCreation, name="proluancher_creattion"),
                  path("subdomain1/Pro-luancher-data/", views.ProPilotLauncherViewGet, name="proluancher_get_data"),

                  # ----------------- AI Interview SECTION ------------------
                  path('subdomain1/ai-Interview-creation/', views.AiInterviewCreation, name="AiInterviewCreation"),
                  path('subdomain1/ai-set-status/', views.Ai_Set_Status,
                       name="SetStatusCompletion"),
                  path('subdomain1/ai-get-details/', views.AiInterviewGetDetails, name="FreeMockGet"),

                  # ----------------- ProLauncher SECTION ------------------
                  path("subdomain1/ai-pro-luancher-create/", views.AiProPilotLauncherCreation,
                       name="AiProPilotLauncherCreation"),
                  path("subdomain1/ai-pro-luancher-data/", views.AiProPilotLauncherGet, name="AiProPilotLauncherGet"),

                  # ----------------- Ai Coding Maths SECTION ------------------
                  path('subdomain1/ai-coding-maths-creation/', views.AiCodingMathsCreation, name="AiCodingMaths"),
                  path('subdomain1/ai-coding-maths-set-status/', views.AiCodingMaths_Set_Status,
                       name="SetStatusCompletion"),
                  path('subdomain1/ai-coding-maths-get-details/', views.AiCodingMathsGetDetails, name="AiCodingMaths"),

                  # ----------------- ProLauncher SECTION ------------------
                  path("subdomain1/aicodingmaths-pro-luancher-create/", views.AiCodingMathsProPilotCreation,
                       name="AiCodingMathsProPilotCreation"),
                  path('subdomain1/ai-coding-maths-pro-luancher-data/', views.AiCodingMathsProPilotGet,
                       name="AiCodingMaths"),

                  # ----------------- Resume Templates SECTION ------------------
                  path('subdomain1/resume-template/', views.ResumeTemplates, name="Resume-Template-All"),
                  path('subdomain1/resume-template-get/', views.SingleResumeTemplates, name="Resume-Template-Single"),
                  path('subdomain1/resume-template-add/', views.ResumeTemplateAdd, name="Resume-Template-add"),

                  # ----------------- CoverLetter Templates SECTION ------------------
                  path('subdomain1/cover-letter-template/', views.CoverLetterTemplates,
                       name="Cover-Letter-Template-All"),
                  path('subdomain1/cover-letter-template-single/', views.SingleCoverletterTemplates,
                       name="Cover-Letter-Template-Single"),
                  path('subdomain1/cover-letter-template-add/', views.CoverLetterTemplateAdd,
                       name="Cover-Letter-Template-Add"),

                  # ----------------- OCR  SECTION ------------------
                  path('subdomain1/perform-ocr/', views.Perform_OCR_Api, name='perform_ocr_image_to_text'),
                  path('subdomain1/delete-user-details/', views.DeleteUserDetails, name="Delete"),

                  # ----------------- Settings SECTION ------------------
                  path('subdomain1/set-temp/', views.TemperatureView, name="TemeratureView"),
                  path('subdomain1/temp/', views.TemeratureChoiceView, name="TemperatureChoices"),

                  path('subdomain1/user-detail/', views.UserData, name="UserDetails"),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
