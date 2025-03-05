import os
import random
from datetime import timedelta

from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Users, SetGoals, ResumeCV, CoverLetter, FlashCardInterviewQuestion, FreeMockInterview, \
    ProPilotLauncher, AiInterviewProPilot, AiProPilotLauncher, AiCodingMaths, AiCodingMathsProPilotLauncher, \
    ResumeTemplate, CoverLetterTemplate, Temperature, UserDetails, TemperatureChoices, Models, Images, MaxToken
from .serializers import UserSerializer, SetGoalsSerializer, ResumeCVSerializer, \
    CoverLetterSerializer, FlashCardInterviewQuestionsSerializer, ForgetPasswordSerializer, ResetPasswordSerializer, \
    SetGoalsLookups, FreeMockCreationSerializers, \
    FreeMockGetSerializers, ResumeCvLookupsSerializer, CoverLetterLookupsSerializer, PositionLookupsSerializer, \
    ProPilotLauncherSerializers, AiInterviewCreationSerializers, AiInterviewGetSerializers, \
    AiProPilotLauncherSerializers, AiCodingMathsCreationSerializers, AiCodingMathsGetSerializers, \
    AiCodingMathsProPilotSerializers, LanguageLookupsSerializer, AiCodingProPilotSerializers, CvSerializer, \
    CLSerializer, TemperatureSerializers, TemperatureChoicesSerializers, UsersSerializer, UserDetailsSerializer
from .utils import send_mail_using_smtp, perform_ocr, perform_ocr_recognition, perform_ocr_detection, decode_image

"""
-----------------------------------------------------
------------- AUTHENTICATIONS SECTION ---------------
-----------------------------------------------------
"""


@sync_to_async
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def postauthuser(request):
    try:
        fullName = request.data.get('fullname')
        first_name, last_name = fullName.split(' ', 1) if ' ' in fullName else (fullName, '')
        email = request.data.get('email')
        password = request.data.get('password')
        is_superuser = request.data.get('is_superuser')
        is_superuser = is_superuser if is_superuser is not None else False

        profile_value = request.data.get('profile')

        # Check if the user with the provided email already exists
        user = User.objects.filter(email=email).first()

        if user:
            # User already exists
            user_instance = Users.objects.get(userId=user.id)

            # Set the 'profile' value only if provided in the request
            if profile_value is not None:
                user_instance.profile = profile_value
                user_instance.save()
            return Response({'error': f'User with this email already exist.'}, status=status.HTTP_400_BAD_REQUEST)



        else:
            user_data = {
                'username': email,
                'email': email,
                'password': password,
                'first_name': first_name,
                'last_name': last_name,
                'is_superuser': is_superuser,
            }
            serializer = UserSerializer(data=user_data)

            if serializer.is_valid():
                user = serializer.create(serializer.validated_data)
                Users.objects.get_or_create(userId=user)
                user_id = user.id

                # Set the 'profile' value only if provided in the request
                if profile_value is not None:
                    user_instance = Users.objects.get(userId=user_id)
                    user_instance.profile = profile_value
                    user_instance.save()

                # Get tokens for new user
                # data = get_tokens_for_user(user, user_id, profile_value)

                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"response": f"Something went wrong: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@sync_to_async
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def loginUser(request):
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            user_id = User.objects.filter(username=username).values()

            try:
                user_instance = Users.objects.get(userId=user_id[0]['id'])
                profile_value = user_instance.profile.url if user_instance.profile else None
            except Users.DoesNotExist:
                profile_value = "unknown"

            refresh = RefreshToken.for_user(user)

            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user_id[0]).data,
                'profile': profile_value,
            }

            return Response(data, status=status.HTTP_200_OK)

        return Response({"error": "Invalid username or password"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        error_message = f"Something went wrong: {e}"
        return Response({"response": error_message}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def register_or_login(request):
    username = request.data.get('username')
    email = request.data.get('email')

    # Check if user with given email already exists
    user = User.objects.filter(email=email).first()
    if user:
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        return Response({
            'message': 'User with this email already exists.',
            'username': user.username,
            'email': user.email,
            'access_token': str(access),
            'refresh_token': str(refresh)
        })
    else:
        # User doesn't exist, create a new user
        user = User.objects.create_user(username=username, email=email)
        # Create a corresponding entry in the Users table
        Users.objects.get_or_create(userId=user)
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        return Response({
            'username': user.username,
            'email': user.email,
            'access_token': str(access),
            'refresh_token': str(refresh)
        })


@sync_to_async
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_password(request):
    try:
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            access_token = AccessToken(token)
            user_id_from_token = access_token['user_id']
            user = User.objects.get(id=user_id_from_token)
        except Exception as e:
            return Response({"error": f"You are not authorized {e}"}, status=status.HTTP_400_BAD_REQUEST)

        current_password = request.data.get('current_password', None)
        new_password = request.data.get('new_password', None)
        confirm_new_password = request.data.get('confirm_new_password', None)

        if current_password == new_password:
            return Response({"error": "New password should be different from the current password."},
                            status=status.HTTP_400_BAD_REQUEST)

        if not check_password(current_password, user.password):
            return Response({"error": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_new_password:
            return Response({"error": "New password and confirm new password does not match."},
                            status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": f"Something went wrong {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@sync_to_async
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    try:
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            access_token = AccessToken(token)
            user_id_from_token = access_token['user_id']
            user = User.objects.get(id=user_id_from_token)
        except Exception as e:
            return Response({"error": f"You are not authorized {e}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            users_instance = Users.objects.get(userId=user)
            users_fields_to_update = ['profile']
            for field in users_fields_to_update:
                if field in request.data:
                    setattr(users_instance, field, request.data[field])
            users_instance.save()
        except Users.DoesNotExist:
            pass

        return Response({"response": "Profile Picture Updated Successfully"}, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"response": f"Something went wrong {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@sync_to_async
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_profile_image(request):
    try:
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token = AccessToken(token)
        user_id_from_token = access_token['user_id']
        user = User.objects.get(id=user_id_from_token)
    except Exception as e:
        return Response({"error": f"You are not authorized {e}"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        users_instance = Users.objects.get(userId=user)
        if users_instance.profile:
            image_path = users_instance.profile.path
            default_storage.delete(image_path)
            users_instance.profile = None
            users_instance.save()

            return Response({"response": "Profile Picture Deleted Successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"response": "No profile picture to delete"}, status=status.HTTP_204_NO_CONTENT)
    except Users.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


@sync_to_async
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user(request):
    try:
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            access_token = AccessToken(token)
            user_id_from_token = access_token['user_id']
            user = User.objects.get(id=user_id_from_token)
        except Exception as e:
            return Response({"error": f"You are not authorized {e}"}, status=status.HTTP_400_BAD_REQUEST)

        user.delete()
        return Response({"message": "User deleted successfully."}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": f"Something went wrong {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_user_status(request):
    if request.method == 'GET':
        # Extract the user from the request object
        user = request.user

        # Check if the user exists and has a profile
        try:
            user_profile = Users.objects.get(userId=user)
        except Users.DoesNotExist:
            return Response({'error': 'User profile does not exist'}, status=404)

        # Check the status of the user
        if user_profile.isPaid:
            status = 'Paid'
        else:
            status = 'Not Paid'

        # Return the user status in the API response
        return Response({'status': status})
    else:
        return Response({'error': 'Method not allowed'}, status=405)


"""
-----------------------------------------------------
------------- FORGET PASSWORD SECTION ---------------
-----------------------------------------------------
"""


@api_view(['POST'])
def ForgetPasswordView(request):
    serializer = ForgetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.data["email"]

    # Get the user with the provided email
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"error": "User with this email does not exist"}, status=status.HTTP_404_NOT_FOUND)
    user_instance = Users.objects.get(userId=user.id)
    otp = random.randint(111111, 999999)
    expiry_time = timezone.now() + timedelta(hours=24)
    expiry_duration = (expiry_time - timezone.now()).total_seconds()

    # Store OTP in the user's OTP field
    user_instance.otp = otp
    user_instance.set_otp_expiry(expiry_duration)
    user_instance.save()

    # Compose email data
    email_data = {
        "from": settings.EMAIL_HOST_USER,
        "subject": "Password Reset OTP",
        "recipient": [email],
    }
    send_mail_using_smtp(otp, email_data)

    return Response({"data": f"Reset password OTP has been sent to you on {email}"}, status=status.HTTP_200_OK)


@api_view(["POST"])
def VerifyOTP(request):
    email = request.data["email"]
    otp = request.data["otp"]
    try:
        user = User.objects.filter(email=email).first()
    except User.DoesNotExist:
        return Response({"error": "User with this email does not exist"}, status=status.HTTP_404_NOT_FOUND)

    if user:
        # User already exists
        encoded_user = urlsafe_base64_encode(force_bytes(user.email))
        user_instance = Users.objects.get(userId=user.id)
        if user_instance.otp != otp:
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the OTP has expired
        if user_instance.is_otp_expired():
            return Response({"error": "OTP has expired"}, status=status.HTTP_400_BAD_REQUEST)

        # OTP is valid and not expired
        return Response({"key": encoded_user, "message": "OTP verified successfully"},
                        status=status.HTTP_200_OK)

    # Handle case where user does not exist
    return Response({"error": "User with this email does not exist"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
def ResetPasswordView(request):
    serializer = ResetPasswordSerializer(
        data=request.data, context={"request": request}
    )
    serializer.is_valid(raise_exception=True)
    return Response({"data": "Password reset successfully"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def user_profile_api(request):
    try:
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token = AccessToken(token)
        user_id_from_token = access_token['user_id']
        user = get_object_or_404(User, id=user_id_from_token)
        if request.method == 'GET':
            serializer = UsersSerializer(user.Users)
            data = serializer.data
            if user.Users.profile:
                data['profile'] = request.build_absolute_uri(user.Users.profile.url)
            else:
                data['profile'] = None
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    except AccessToken.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


"""
-----------------------------------------------------
---------------- SET GOALS SECTION ------------------
-----------------------------------------------------
"""


@sync_to_async
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_goals(request):
    try:
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            access_token = AccessToken(token)
            user_id_from_token = access_token['user_id']
            user = User.objects.get(id=user_id_from_token)
        except Exception as e:
            return Response({"error": "You are not authorized"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SetGoalsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(userId=user)
        return Response(serializer.data)
    except:
        return Response(content={"response": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@sync_to_async
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def edit_goals(request):
    try:
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            access_token = AccessToken(token)
            user_id_from_token = access_token['user_id']
            User.objects.get(id=user_id_from_token)
        except Exception as e:
            return Response({"error": "You are not authorized"}, status=status.HTTP_400_BAD_REQUEST)

        goal_id = request.data.get('goal_id')
        try:
            goals = SetGoals.objects.get(id=goal_id)
        except goals.DoesNotExist:
            return Response({"response": "Goal object not found"}, status=status.HTTP_404_NOT_FOUND)

        for field in request.data:
            setattr(goals, field, request.data[field])

        serializer = SetGoalsSerializer(goals, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"response": f"Goals not exist"}, status=status.HTTP_404_NOT_FOUND)


@sync_to_async
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_goals(request):
    try:
        user_id = request.user.id
        goals = SetGoals.objects.filter(userId=user_id)
        serializer = SetGoalsSerializer(goals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"response": "Goals not found"}, status=status.HTTP_404_NOT_FOUND)


@sync_to_async
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_archived_goals(request):
    try:
        user_id = request.user.id
        active_goals = SetGoals.objects.filter(userId=user_id, isActive=False)
        serializer = SetGoalsSerializer(active_goals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"response": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@sync_to_async
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unarchived_goals(request):
    try:
        user_id = request.user.id
        active_goals = SetGoals.objects.filter(userId=user_id, isActive=True)
        serializer = SetGoalsSerializer(active_goals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"response": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
def update_goal_status(request):
    try:
        id = request.data['id']
        isActive = request.query_params.get('isActive')
        goal = SetGoals.objects.get(pk=id)
    except SetGoals.DoesNotExist:
        return Response({"message": "Goal with id {} not found.".format(id)}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PATCH':
        serializer = SetGoalsSerializer(instance=goal, data={'isActive': isActive}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response("Invalid request method", status=status.HTTP_405_METHOD_NOT_ALLOWED)


@sync_to_async
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_goal(request):
    try:
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            access_token = AccessToken(token)
            user_id_from_token = access_token['user_id']
            user = User.objects.get(id=user_id_from_token)
        except Exception as e:
            return Response({"error": "You are not authorized"}, status=status.HTTP_400_BAD_REQUEST)

        goal_id = request.data.get("goal_id")
        goal_to_delete = SetGoals.objects.get(userId=user, id=goal_id)
        goal_to_delete.delete()
        return Response({"message": "Goal deleted successfully."}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


"""
-----------------------------------------------------
------------------ RESUME SECTION -------------------
-----------------------------------------------------
"""


@sync_to_async
@api_view(['POST'])
def UploadResume(request):
    try:
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            access_token = AccessToken(token)
            user_id_from_token = access_token['user_id']
            user = User.objects.get(id=user_id_from_token)
        except Exception as e:
            return Response({"error": f"You are not authorized {e}"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ResumeCVSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(userId=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"response": f"Something went wrong: {e}"}, status=status.HTTP_404_NOT_FOUND)


@sync_to_async
@api_view(['PATCH'])
def UpdateResume(request):
    try:
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            access_token = AccessToken(token)
            user_id_from_token = access_token['user_id']
            user = User.objects.get(id=user_id_from_token)
        except Exception as e:
            return Response({"error": f"You are not authorized {e}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            id = request.data['id']
            resume = ResumeCV.objects.get(id=id, userId=user)
        except ResumeCV.DoesNotExist:
            return Response({"error": "Resume not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ResumeCVSerializer(resume, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"response": f"Something went wrong: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def download_resume(request):
    try:
        id = request.data.get('id')
        resume = ResumeCV.objects.get(id=id)
        serializer = ResumeCVSerializer(resume)
        # Get the base URL
        data = serializer.data
        data["CV_document"] = request.build_absolute_uri(resume.CV_document.url)
        return Response(data, status=status.HTTP_200_OK)
    except ResumeCV.DoesNotExist:
        return Response({"message": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)


@sync_to_async
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def DeleteResume(request):
    try:
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            access_token = AccessToken(token)
            user_id_from_token = access_token['user_id']
            user = User.objects.get(id=user_id_from_token)
        except Exception as e:
            return Response({"error": f"You are not authorized {e}"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            resume_id = request.data.get("resume_id")
            resume_to_delete = ResumeCV.objects.get(userId=user, id=resume_id)
            resume_to_delete.delete()
            return Response({"message": "Resume deleted successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Resume not found"}, status=status.HTTP_404_NOT_FOUND)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": f"Something went wrong {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@sync_to_async
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def GetAllResume(request):
    try:
        user_id = request.user.id
        resume = ResumeCV.objects.filter(userId=user_id)
        serializer = ResumeCVSerializer(resume, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"response": f"Something went wrong {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


"""
-----------------------------------------------------
------------------ COVER LETTER SECTION -------------------
-----------------------------------------------------
"""


@sync_to_async
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def UploadCoverLetter(request):
    try:
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            access_token = AccessToken(token)
            user_id_from_token = access_token['user_id']
            user = User.objects.get(id=user_id_from_token)
        except Exception as e:
            return Response({"error": "You are not authorized"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CoverLetterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(userId=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"response": f"Something went wrong: {e}"}, status=status.HTTP_404_NOT_FOUND)


@sync_to_async
@api_view(['PATCH'])
@authentication_classes([])
@permission_classes([])
def UpdateCoverLetter(request):
    try:
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            access_token = AccessToken(token)
            user_id_from_token = access_token['user_id']
            user = User.objects.get(id=user_id_from_token)
        except Exception as e:
            return Response({"error": "You are not authorized"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            id = request.data.get('id')
            resume = CoverLetter.objects.get(id=id, userId=user)
        except CoverLetter.DoesNotExist:
            return Response({"error": "Cover Letter not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CoverLetterSerializer(resume, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"response": f"Something went wrong: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def download_cover_letter(request):
    try:
        id = request.data.get('id')
        cover_letter = CoverLetter.objects.get(id=id)
        serializer = CoverLetterSerializer(cover_letter)
        # Get the base URL
        data = serializer.data
        data["Letter_document"] = request.build_absolute_uri(cover_letter.Letter_document.url)
        return Response(data, status=status.HTTP_200_OK)
    except CoverLetter.DoesNotExist:
        return Response({"message": "Letter_document not found"}, status=status.HTTP_404_NOT_FOUND)


@sync_to_async
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def DeleteCoverLetter(request):
    try:
        try:
            token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            access_token = AccessToken(token)
            user_id_from_token = access_token['user_id']
            user = User.objects.get(id=user_id_from_token)
        except Exception as e:
            return Response({"error": f"You are not authorized: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        coverletter_id = request.data.get("coverletter_id")
        coverletter_to_delete = CoverLetter.objects.get(userId=user, id=coverletter_id)
        coverletter_to_delete.delete()
        return Response({"message": "Cover Letter deleted successfully."}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": f"Something went wrong: {e}"}, status=status.HTTP_404_NOT_FOUND)


@sync_to_async
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def GetAllCoverLetter(request):
    try:
        user_id = request.user.id
        resume = CoverLetter.objects.filter(userId=user_id)
        serializer = CoverLetterSerializer(resume, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"response": f"Something went wrong {e}"}, status=status.HTTP_404_NOT_FOUND)


"""
-----------------------------------------------------
------------------ RESUME Template SECTION -------------------
-----------------------------------------------------
"""


@api_view(['GET'])
def ResumeTemplates(request):
    if request.method == 'GET':
        try:
            resume_templates = ResumeTemplate.objects.all()
            serializer = CvSerializer(resume_templates, many=True)

            # Get the base URL
            base_url = request.build_absolute_uri('/')[:-1]

            for serialized_template in serializer.data:
                template = ResumeTemplate.objects.get(id=serialized_template['id'])
                resume_url_pdf = base_url + template.CV_template_Pdf.url
                resume_template = base_url + template.CV_template_Word.url
                serialized_template['CV_template_Pdf'] = resume_url_pdf
                serialized_template['CV_template_Word'] = resume_template

            return Response(serializer.data, status=status.HTTP_200_OK)
        except ResumeTemplate.DoesNotExist as e:
            return Response("resume not found", status=status.HTTP_404_NOT_FOUND)

    else:
        return Response("Invalid request method", status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
def SingleResumeTemplates(request):
    if request.method == 'GET':
        try:
            id = request.data.get('id')
            resume_template = ResumeTemplate.objects.get(id=id)
            CvSerializer(resume_template)

            # Get the base URL
            base_url = request.build_absolute_uri('/')[:-1]

            resume_url_pdf = base_url + resume_template.CV_template_Pdf.url
            resume_url_word = base_url + resume_template.CV_template_Word.url

            response_data = {
                'id': resume_template.id,
                'CV_template_Pdf': resume_url_pdf,
                'CV_template_Word': resume_url_word
            }

            return Response(response_data, status=status.HTTP_200_OK)
        except ResumeTemplate.DoesNotExist:
            return Response("Resume not found", status=status.HTTP_404_NOT_FOUND)
    else:
        return Response("Invalid request method", status=status.HTTP_405_METHOD_NOT_ALLOW)


@api_view(['POST'])
def ResumeTemplateAdd(request):
    if request.method == 'POST':
        serializer = CvSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response("Invalid request method", status=status.HTTP_405_METHOD_NOT_ALLOWED)


"""
-----------------------------------------------------
------------------ Cover Letter Template SECTION -------------------
-----------------------------------------------------
"""


@api_view(['GET'])
def CoverLetterTemplates(request):
    if request.method == 'GET':
        cover_letter_templates = CoverLetterTemplate.objects.all()
        serializer = CLSerializer(cover_letter_templates, many=True)
        # Get the base URL
        base_url = request.build_absolute_uri('/')[:-1]

        for serialized_template in serializer.data:
            template = CoverLetterTemplate.objects.get(id=serialized_template['id'])
            cover_letter_pdf = base_url + template.CL_template_Pdf.url
            cover_letter_word = base_url + template.CL_template_Word.url
            serialized_template['CL_template_Pdf'] = cover_letter_pdf
            serialized_template['CL_template_Word'] = cover_letter_word

        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response("Invalid request method", status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
def SingleCoverletterTemplates(request):
    if request.method == 'GET':
        try:
            id = request.data.get('id')
            cover_letter_template = CoverLetterTemplate.objects.get(id=id)
            CLSerializer(cover_letter_template)

            # Get the base URL
            base_url = request.build_absolute_uri('/')[:-1]

            cover_letter_url_pdf = base_url + cover_letter_template.CL_template_Pdf.url
            cover_letter_url_word = base_url + cover_letter_template.CL_template_Word.url

            response_data = {
                'id': cover_letter_template.id,
                'CL_template_Pdf': cover_letter_url_pdf,
                'CL_template_Word': cover_letter_url_word
            }

            return Response(response_data, status=status.HTTP_200_OK)
        except ResumeTemplate.DoesNotExist:
            return Response("Resume not found", status=status.HTTP_404_NOT_FOUND)
    else:
        return Response("Invalid request method", status=status.HTTP_405_METHOD_NOT_ALLOW)


@api_view(['POST'])
def CoverLetterTemplateAdd(request):
    if request.method == 'POST':
        serializer = CLSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response("Invalid request method", status=status.HTTP_405_METHOD_NOT_ALLOWED)


"""
-----------------------------------------------------
------------- FlashCard SECTION ---------------
-----------------------------------------------------
"""


@sync_to_async
@api_view(['GET'])
def FlashCardQA(request):
    try:
        # Get all the questions and answers with category and subcategory
        flashcard_qa = FlashCardInterviewQuestion.objects.all()
        serializer = FlashCardInterviewQuestionsSerializer(flashcard_qa, many=True)

        # Extracting unique category names from the serializer data
        category_names = set(item['category_name'] for item in serializer.data if item['category_name'])

        return Response({'data': serializer.data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"response": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


"""
-----------------------------------------------------
------------- FreeMockInterviews SECTION ---------------
-----------------------------------------------------
"""


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def GetUserSetGoalsLookup(request):
    try:
        user = request.user
        user_set_goals = SetGoals.objects.filter(userId=user)
    except SetGoals.DoesNotExist:
        return Response("SetGoals DoesNotExist", status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        serializer = SetGoalsLookups(user_set_goals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response("Invalid request method", status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def FreeMockCreation(request):
    if request.method == 'POST':
        serializer = FreeMockCreationSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response("Invalid request method", status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def FreeMockCompletion(request):
    try:
        id = request.data.get('id')
        free_mock_interview = FreeMockInterview.objects.get(id=id)
    except FreeMockInterview.DoesNotExist:
        return Response({"message": "FreeMockInterview with id {} not found.".format(id)},
                        status=status.HTTP_404_NOT_FOUND)
    if request.method == 'PATCH':
        # Update IsActive field to False
        serializer = FreeMockCreationSerializers(instance=free_mock_interview, data={'IsActive': False},
                                                 partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response("Invalid request method. This endpoint only supports PATCH.",
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def FreeMockGetDetails(request):
    if request.method == 'GET':
        user = request.user
        IsActive = request.query_params.get('isactive') or request.GET.get('isactive')
        user_set_freemock = FreeMockInterview.objects.filter(userId=user)
        if IsActive:
            user_set_freemock = FreeMockInterview.objects.filter(userId=user, IsActive=IsActive)
        serializer = FreeMockGetSerializers(user_set_freemock, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response("Invalid request method", status=status.HTTP_405_METHOD_NOT_ALLOWED)


"""
-----------------------------------------------------
------------- ProPilotLauncherView SECTION ---------------
-----------------------------------------------------
"""


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def GetUserResumeLookup(request):
    if request.method == 'GET':
        user = request.user
        user_resume = ResumeCV.objects.filter(userId=user)
        serializer = ResumeCvLookupsSerializer(user_resume, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response("Invalid request method", status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def GetUserCoverLetterLookup(request):
    if request.method == 'GET':
        user = request.user
        cover_letter = CoverLetter.objects.filter(userId=user)
        serializer = CoverLetterLookupsSerializer(cover_letter, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response("Invalid request method", status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def GetUserPositionLookup(request):
    if request.method == 'GET':
        user = request.user
        position = SetGoals.objects.filter(userId=user)
        serializer = PositionLookupsSerializer(position, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response("Invalid request method", status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def GetUserLanguageLookup(request):
    try:
        user = request.user
        language = SetGoals.objects.filter(userId=user)
    except SetGoals.DoesNotExist:
        return Response("SetGoals is not exist", status=status)
    if request.method == 'GET':
        serializer = LanguageLookupsSerializer(language, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response("Invalid request method", status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ProPilotLauncherCreation(request):
    try:
        # Extract user id from the access token
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token = AccessToken(token)
        user_id_from_token = access_token['user_id']
        user = User.objects.get(id=user_id_from_token)
    except Exception as e:
        return Response({"error": f"You are not authorized {e}"}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'POST':
        mutable_data = request.data.copy()
        mutable_data['userId'] = user.id
        serializer = ProPilotLauncherSerializers(data=mutable_data)
        if serializer.is_valid():
            # Saving the serializer
            serializer.save()
            return Response({"message": "Pro Pilot Launcher created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response("Invalid request method", status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ProPilotLauncherViewGet(request):
    if request.method == 'GET':
        user = request.user
        pro_pilot_launchers = ProPilotLauncher.objects.filter(userId=user)
        if pro_pilot_launchers:
            serializer = ProPilotLauncherSerializers(pro_pilot_launchers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response("Pro Pilot_launchers not exist", status=status.HTTP_404_NOT_FOUND)
    else:
        return Response("Invalid request method", status=status.HTTP_405_METHOD_NOT_ALLOWED)


"""
-----------------------------------------------------
------------- AI Interviews SECTION ---------------
-----------------------------------------------------
"""


@api_view(['POST'])
def AiInterviewCreation(request):
    if request.method == 'POST':
        serializer = AiInterviewCreationSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response("Invalid request method", status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['PATCH'])
def Ai_Set_Status(request):
    if request.method == 'PATCH':
        try:
            id = request.data.get('id')
            ai_interview = AiInterviewProPilot.objects.get(id=id)
        except AiInterviewProPilot.DoesNotExist:
            return Response({"message": "AI Interview with id {} not found.".format(id)},
                            status=status.HTTP_404_NOT_FOUND)

        # Update IsActive field to False
        serializer = AiInterviewCreationSerializers(instance=ai_interview, data={'IsActive': False},
                                                    partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response("Invalid request", status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def AiInterviewGetDetails(request):
    if request.method == 'GET':
        user = request.user
        IsActive = request.query_params.get('isactive') or request.GET.get('isactive')
        user_set_ai = AiInterviewProPilot.objects.filter(userId=user)
        if IsActive:
            user_set_ai = AiInterviewProPilot.objects.filter(userId=user, IsActive=IsActive)

        serializer = AiInterviewGetSerializers(user_set_ai, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------
------------- AI ProPilotLauncher SECTION ---------------
-----------------------------------------------------
"""


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def AiProPilotLauncherCreation(request):
    try:
        # Extract user id from the access token
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token = AccessToken(token)
        user_id_from_token = access_token['user_id']
        user = User.objects.get(id=user_id_from_token)
    except Exception as e:
        return Response({"error": f"You are not authorized {e}"}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'POST':
        mutable_data = request.data.copy()
        mutable_data['userId'] = user.id
    if request.method == 'POST':
        serializer = AiProPilotLauncherSerializers(data=mutable_data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "AI Pro Pilot Launcher created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def AiProPilotLauncherGet(request):
    if request.method == 'GET':
        user = request.user
        pro_pilot_launchers = AiProPilotLauncher.objects.filter(userId=user)
        serializer = AiProPilotLauncherSerializers(pro_pilot_launchers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------
------------- AiCodingMaths SECTION ---------------
-----------------------------------------------------
"""


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def AiCodingMathsCreation(request):
    if request.method == 'POST':
        serializer = AiCodingMathsCreationSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response("Invalid request", status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['PATCH'])
def AiCodingMaths_Set_Status(request):
    try:
        id = request.data.get('id')
        ai_interview = AiCodingMaths.objects.get(id=id)
    except AiCodingMaths.DoesNotExist:
        return Response({"message": "AI Interview with id {} not found.".format(id)},
                        status=status.HTTP_404_NOT_FOUND)
    if request.method == 'PATCH':
        # Update IsActive field to False
        serializer = AiCodingMathsCreationSerializers(instance=ai_interview, data={'IsActive': False},
                                                      partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response("Invalid request", status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def AiCodingMathsGetDetails(request):
    if request.method == 'GET':
        user = request.user
        IsActive = request.query_params.get('isactive') or request.GET.get('isactive')
        user_set_ai = AiCodingMaths.objects.filter(userId=user)
        if IsActive:
            user_set_ai = AiCodingMaths.objects.filter(userId=user, IsActive=IsActive)

        serializer = AiCodingMathsGetSerializers(user_set_ai, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response("Invalid request", status=status.HTTP_405_METHOD_NOT_ALLOWED)


"""
-----------------------------------------------------
------------- AiCodingMaths ProPilotLauncher SECTION ---------------
-----------------------------------------------------
"""


@api_view(['POST'])
def AiCodingMathsProPilotCreation(request):
    if request.method == 'POST':
        serializer = AiCodingMathsProPilotSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "AiCodingMaths Pro Pilot Launcher created successfully"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response("Invalid request", status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def AiCodingMathsProPilotGet(request):
    if request.method == 'GET':
        user = request.user
        pro_pilot_launchers = AiCodingMathsProPilotLauncher.objects.filter(userId=user)
        serializer = AiCodingProPilotSerializers(pro_pilot_launchers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response("Invalid request", status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def TemperatureView(request):
    if request.method == 'POST':
        user = request.user
        mutable_data = request.data.copy()
        mutable_data['userId'] = user.id
        serializer = TemperatureSerializers(data=mutable_data)
        if serializer.is_valid():
            serializer.save()
            return Response("Temperature added", status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


"""
-----------------------------------------------------
------------- OCR SECTION ---------------
-----------------------------------------------------
"""


@api_view(['GET'])
def TemeratureChoiceView(request):
    if request.method == 'GET':
        try:
            data = TemperatureChoices.objects.all()
            serializer = TemperatureChoicesSerializers(data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(f"Choices not found : {e}", status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


import base64
from PIL import Image
import io
from django.core.files.base import ContentFile


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def Perform_OCR_Api(request):
    if request.method == 'POST':
        user = request.user
        url = request.data.get('url')
        image_base64 = request.data.get('image_base64')

        if not image_base64:
            return Response({"error": "No image_base64 provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Decode the base64 string to binary data
        binary_data = base64.b64decode(image_base64)
        # Convert the binary data to BytesIO object
        binary_data = io.BytesIO(binary_data)
        binary_data.seek(0)
        try:
            # Open the image from the binary data
            image = Image.open(binary_data)
            # image.show()
            # image.save("CoWin/media/images/output_image.jpg")
        except Exception as e:
            return Response({"error": "Failed to open image from blob: {}".format(str(e))},
                            status=status.HTTP_400_BAD_REQUEST)

        if url == 'http://127.0.0.1:8000/text/':
            # Get the image file from the request
            tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

            # Perform OCR on the image
            extracted_image_text = perform_ocr(image, tesseract_path)
            extracted_image = [line.strip() for line in extracted_image_text.split('\n') if line.strip()]

            # Get the latest resume object
            resume = ResumeCV.objects.filter(userId=user, isActive=True).order_by('-id').first()
            if resume:
                resume_file_path = resume.CV_document.path
            else:
                return Response({"error": "Resume not found"}, status=status.HTTP_400_BAD_REQUEST)

            # Perform OCR recognition on the retrieved resume
            extracted_resume = perform_ocr_recognition(resume_file_path)
            extracted_resume = [line.strip() for line in extracted_resume.split('\n') if
                                line.strip() and "•" not in line]

            # Get the latest goal object
            goal = SetGoals.objects.filter(userId=user, isActive=True).order_by('-id').first()
            if goal:
                goal_position = goal.position
                goal_programing_language = goal.programing_language
            else:
                return Response({"error": "no goal exist"}, status=status.HTTP_400_BAD_REQUEST)

            # Get the latest temperature object
            temp = Temperature.objects.filter(userId=user).order_by('-id').first()
            if temp:
                temp_value = temp.temperature_choice if temp else None
            else:
                return Response({"error": "no temperature exist"}, status=status.HTTP_400_BAD_REQUEST)
            # Get the latest Model object
            latest_model = Models.objects.filter(user=user).order_by('-created_at').first()
            if latest_model:
                latest_model_value = latest_model.model_name if latest_model else None
            else:
                return Response({"error": "no model found"}, status=status.HTTP_404_NOT_FOUND)
            # Get the latest Token object
            latest_token = MaxToken.objects.filter(user=user).order_by('-created_at').first()
            if latest_token:
                latest_token = latest_token.token if latest_token else None
            else:
                return Response({"error": "no token found"}, status=status.HTTP_404_NOT_FOUND)

            UserDetails.objects.update_or_create(
                user=user,
                defaults={
                    'latest_resume': extracted_resume,
                    'latest_goal': goal_position,
                    'latest_temperature': temp_value
                }
            )

            # Perform OCR detection
            chatbot_response = perform_ocr_detection(extracted_image, goal_programing_language, goal_position,
                                                     extracted_resume, temp_value, latest_model_value, latest_token)
            chatbot = chatbot_response.split('\n')
            chatbot_response = [line.strip() for line in chatbot if line.strip()]
            # user_details = get_object_or_404(UserDetails, user=user)
            response = {
                # "user_details": user_details,
                "extrated_image_text": extracted_image,
                "chatbot_response": chatbot_response
            }

            return Response(response, status=status.HTTP_200_OK)
        else:
            # Create a new ImageField object and assign the JpegImageFile object to it
            image_field = Images.objects.create(user=user, image=None)

            # Get the file name and extension from the JpegImageFile object
            file_name, file_extension = os.path.splitext(image.filename)

            # Create a new file name with a file extension
            # new_file_name = f"{user.username}_{image.filename}"
            new_file_name = f"{user.username}_{file_extension}"

            # Create a new ContentFile object with the binary data of the image
            content_file = ContentFile(binary_data.getvalue())

            # Save the image to the ImageField object with the new file name
            image_field.image.save(new_file_name, content_file, save=False)

            # Save the Images object to the database
            image_field.save()
            latest_image = Images.objects.filter(user=user).order_by('-id').first()
            if latest_image:
                image_path = latest_image.image.path
                data = decode_image(image_path)
                chatbot = data.split('\n')
                chatbot_response = [line.strip() for line in chatbot if line.strip()]
                return Response(chatbot_response, status=status.HTTP_200_OK)
            else:
                return Response('No images found', status=status.HTTP_404_NOT_FOUND)

    else:
        return Response({"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def DeleteUserDetails(request):
    if request.method == 'DELETE':
        user = request.user
        print(f"Deleting UserDetails and Images for user {user.username}")
        try:
            UserDetails.objects.filter(user=user).delete()
            Images.objects.filter(user=user).delete()
            print("UserDetails and Images deleted successfully")
            return Response({'response': 'Delete Successfully'}, status=status.HTTP_204_NO_CONTENT)
        except UserDetails.DoesNotExist:
            print("UserDetails does not exist")
            return Response('User does not exist', status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error deleting UserDetails and Images: {e}")
            return Response({"error": "Failed to delete UserDetails and Images"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def UserData(request):
    try:
        if request.method == 'GET':
            user = request.user
            # Get the latest uploaded resume for the logged-in user
            user_details = get_object_or_404(UserDetails, user=user)

            # Serialize the UserDetails object
            serializer = UserDetailsSerializer(user_details)
            return Response(serializer.data, status=status.HTTP_200_OK)
    except UserDetails.DoesNotExist:
        return Response('User details not found', status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
