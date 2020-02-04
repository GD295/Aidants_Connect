from django.urls import path
from magicauth import views as magicauth_views
from magicauth.urls import urlpatterns as magicauth_urls
from aidants_connect_web.views import (
    service,
    usagers,
    FC_as_FS,
    id_provider,
    new_mandat,
)

urlpatterns = [
    # service
    path("", service.home_page, name="home_page"),
    path("accounts/login/", magicauth_views.LoginView.as_view(), name="login"),
    path("dashboard/", service.dashboard, name="dashboard"),
    # usagers
    path("usagers/", usagers.usagers_index, name="usagers"),
    path("usagers/<int:usager_id>/", usagers.usagers_details, name="usagers_details"),
    path(
        "usagers/<int:usager_id>/mandats/<int:mandat_id>/delete_confirm",
        usagers.usagers_mandats_delete_confirm,
        name="usagers_mandats_delete_confirm"
    ),
    # new mandat
    path("new_mandat/", new_mandat.new_mandat, name="new_mandat"),
    path("new_mandat_recap/", new_mandat.new_mandat_recap, name="new_mandat_recap"),
    path("logout-callback/", new_mandat.new_mandat_recap, name="new_mandat_recap"),
    path(
        "new_mandat_preview/", new_mandat.new_mandat_preview, name="new_mandat_preview"
    ),
    # id_provider
    path("authorize/", id_provider.authorize, name="authorize"),
    path("token/", id_provider.token, name="token"),
    path("userinfo/", id_provider.user_info, name="user_info"),
    path("logout/", service.logout_page, name="logout"),
    path("select_demarche/", id_provider.fi_select_demarche, name="fi_select_demarche"),
    # FC_as_FS
    path("fc_authorize/", FC_as_FS.fc_authorize, name="fc_authorize"),
    path("callback/", FC_as_FS.fc_callback, name="fc_callback"),
    # misc
    path("ressources/", service.resources, name="resources"),
    path("stats/", service.statistiques, name="statistiques"),
    path("activity_check/", service.activity_check, name="activity_check"),
]

urlpatterns.extend(magicauth_urls)
