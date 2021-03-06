"""scheduler URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.conf import settings
from django.contrib import admin
from django.urls import path, include

from rest_framework_jwt.views import obtain_jwt_token, verify_jwt_token
from rest_framework_swagger.views import get_swagger_view

from .views import FacebookLogin, KakaoLogin, NaverLogin, GoogleLogin


schema_view = get_swagger_view(title='Schedule API')

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api-docs/', schema_view),

    path('rest-auth/facebook/', FacebookLogin.as_view(), name='facebook_login'),
    path('rest-auth/kakao/', KakaoLogin.as_view(), name='kakao_login'),
    path('rest-auth/naver/', NaverLogin.as_view(), name='naver_login'),
    path('rest-auth/google/', GoogleLogin.as_view(), name='google_login'),

    path('api-token-auth/', obtain_jwt_token),
    path('api-token-verify/', verify_jwt_token),

    path('v1/member/', include('member.urls')),
    path('v1/schedule/', include('schedule.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),

        # For django versions before 2.0:
        # url(r'^__debug__/', include(debug_toolbar.urls)),

    ] + urlpatterns
