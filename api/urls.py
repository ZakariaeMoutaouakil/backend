from django.urls import path

from api.views import read, composantes, login, signup, cours, subscribe

urlpatterns = [
    path("read/", read, name='read'),
    path("composantes/", composantes, name='composantes'),
    path("login/", login, name='login'),
    path("signup/", signup, name='signup'),
    path("cours/", cours, name='cours'),
    path("subscribe/", subscribe, name='subscribe'),
]
