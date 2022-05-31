"""sasdi_web URL Configuration

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
from . import views, api

urlpatterns = [
    path('', views.index, name='index'),
    path('results', views.results, name='results'),
    path('put-videos', api.putVideos, name='putVideos'),
    path('get-first-frame', api.get_first_frame, name='get_first_frame'),
    path('get-first-serie-frame', api.get_first_serie_frame,
         name='get_firsts_serie_frame'),
    path('unselect', api.unselect, name='unselect'),
    path('save-rois', api.save_rois, name='save-rois'),
    path('start-analysis', api.start_analysis, name='start-analysis'),
    path('process-analysis', api.process_analysis,
         name='process-analysis'),
    path('get-chart-data', api.get_chart_data,
         name='get-chart-data'),
    path('refresh', api.refresh,
         name='refresh'),
]
