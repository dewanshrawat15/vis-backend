"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from app.views import CreateConsentView, GetConsentStatusView, ConfirmConsentView, CreateDataFlowView, FetchDataFromFI, FetchPersonalFIData, AnalysisData, CacheView, ClearCacheView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('consent/', CreateConsentView.as_view()),
    path('consent/<str:number>/status/', GetConsentStatusView.as_view()),
    path('consent/confirm/', ConfirmConsentView.as_view()),
    path('fetch/<str:number>/create/', CreateDataFlowView.as_view()),
    path('fetch/<str:id>/data/', FetchDataFromFI.as_view()),
    path('finance/personal/', FetchPersonalFIData.as_view()),
    path('finance/analyze', AnalysisData.as_view()),
    path('cache/', CacheView.as_view()),
    path('cache/clear/', ClearCacheView.as_view())
]
