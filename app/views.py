import json

from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from .utils import trigger_consent_request, check_consent_status, create_data_session, get_data_from_FI, read_personal_data_from_S3, get_dynamodb_data, filter_data_from_cache
from .models import UserConsent
from django.core.cache import cache
from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
 
CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)
# Create your views here.

class CreateConsentView(APIView):

    permission_classes = (AllowAny, )

    def post(self, request):
        mobile_number = json.loads(request.body)["mobile_number"]
        user_consent_object = UserConsent.objects.filter(customer_id__icontains = mobile_number)
        if len(user_consent_object) == 0:
            response_status, url = trigger_consent_request(mobile_number)
            if response_status:
                return Response({
                    "message": "New user consent object created",
                    "url": url
                }, status = status.HTTP_201_CREATED)
            else:
                return Response({
                    "message": "An error occurred"
                }, status = status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                "message": "User with this consent exists"
            }, status = status.HTTP_200_OK)
    
class GetConsentStatusView(APIView):

    permission_classes = (AllowAny, )

    def get(self, request, number):
        user_consent_object = UserConsent.objects.filter(customer_id__icontains = number)
        if len(user_consent_object) == 0:
            return Response({}, status = status.HTTP_400_BAD_REQUEST)
        else:
            result = check_consent_status(user_consent_object[0].consent_id)
            return Response({
                "status": result
            }, status = status.HTTP_200_OK)

class ConfirmConsentView(APIView):

    permission_classes = (AllowAny, )

    def get(self, request):
        consent_id = request.GET.get('id')
        success = request.GET.get('success')
        obj = UserConsent.objects.filter(consent_id = consent_id)
        if len(obj) == 0:
            return Response({}, status = status.HTTP_400_BAD_REQUEST)
        else:
            model = obj[0]
            model.is_active = success == 'true'
            model.save()
            return Response({}, status = status.HTTP_200_OK)

class CreateDataFlowView(APIView):

    permission_classes = (AllowAny, )

    def get(self, request, number):
        user_obj = UserConsent.objects.filter(customer_id__icontains = number)
        if len(user_obj) == 0:
            return Response({}, status = status.HTTP_400_BAD_REQUEST)
        else:
            model = user_obj[0]
            result, result_id = create_data_session(model.consent_id)
            return Response({
                "fi_data_request_id": result_id if result_id is not None else "",
                "status": result
            }, status = status.HTTP_200_OK)

class FetchDataFromFI(APIView):

    permission_classes = (AllowAny, )

    def post(self, request, id):
        try:
            result = get_data_from_FI(id, json.loads(request.body)["mobile_number"])
            if result:
                return Response({}, status = status.HTTP_200_OK)
            else:
                return Response({}, status = status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({}, status = status.HTTP_400_BAD_REQUEST)

class FetchPersonalFIData(APIView):

    permission_classes = (AllowAny, )

    def post(self, request):
        try:
            mobile_number = json.loads(request.body)["mobile_number"]
            user_obj = UserConsent.objects.filter(customer_id__icontains = mobile_number)[0]
            flag, data = read_personal_data_from_S3(user_obj.customer_id)
            if flag:
                return Response(data, status = status.HTTP_200_OK)
            else:
                return Response({}, status = status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({}, status = status.HTTP_400_BAD_REQUEST)

class AnalysisData(APIView):

    permission_classes = (AllowAny, )
    def get(self, request):
        try:
            start_datetime = request.GET.get('start_datetime') if request.GET.get('start_datetime') else None
            end_datetime = request.GET.get('end_datetime') if request.GET.get('end_datetime') else None
            mode = request.GET.get('mode') if request.GET.get('mode') else None
            transaction_type = request.GET.get('transaction_type') if request.GET.get('transaction_type') else None
            cached_data = cache.get('transactions')
            if cached_data is None:
                data = get_dynamodb_data()
                cache.set('transactions', data, timeout = CACHE_TTL)
                cached_data = data
            flag, data = filter_data_from_cache(start_datetime, end_datetime, mode, transaction_type, cached_data)
            if flag:
                return Response(data, status = status.HTTP_200_OK)
            else:
                return Response({}, status = status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({}, status = status.HTTP_400_BAD_REQUEST)

class CacheView(APIView):

    def get(self, request):
        try:
            data = get_dynamodb_data()
            cache.set('transactions', data, timeout = CACHE_TTL)
            return Response({}, status = status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({}, status = status.HTTP_400_BAD_REQUEST)

class ClearCacheView(APIView):

    def get(self, request):
        cache.clear()
        return Response({}, status = status.HTTP_200_OK)