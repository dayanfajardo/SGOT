from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from django.views.generic import TemplateView

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        LoginView.as_view(
            template_name="accounts/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),
    path(
        "",
        login_required(TemplateView.as_view(template_name="accounts/home.html")),
        name="home",
    ),
]
