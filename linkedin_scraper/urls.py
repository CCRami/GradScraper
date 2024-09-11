"""
URL configuration for linkedin_scraper project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from scraperapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('start-scraping/', views.start_scraping, name='start_scraping'),
    path('get_progress_data/', views.get_progress_data, name='get_progress_data'),
    path('results/', views.results, name='results'),
    path('resultsbycompany/', views.resultsbycompany, name='resultsbycompany'),
    path('get_company_members/', views.get_company_members, name='get_company_members'),
    path('delete_company/', views.delete_company, name='delete_company'),
    path('index/', views.index, name='index'),
    path('settings/', views.settings, name='settings'),
    path('history/', views.history, name='history'),
    path('update_end_time/', views.update_end_time, name='update_end_time'),
    path('delete_session/', views.delete_session, name='delete_session'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
