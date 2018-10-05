from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.http import Http404, HttpResponseForbidden
from django.urls import include, path, re_path
from django.views.defaults import page_not_found, permission_denied, server_error
from django.views.generic import TemplateView
from machina.app import board

from concordia.admin import admin_bulk_import_view
from exporter import views as exporter_views

from . import trans_urls, views, views_ws

for key, value in getattr(settings, "ADMIN_SITE", {}).items():
    setattr(admin.site, key, value)


tx_urlpatterns = (
    [
        path("", views.CampaignListView.as_view(), name="campaigns"),
        path("<slug:slug>/", views.CampaignDetailView.as_view(), name="campaign"),
        re_path(
            r"^pageinuse/$", views.ConcordiaPageInUse.as_view(), name="page-in-use"
        ),
        re_path(
            r"^alternateasset/$",
            views.ConcordiaAlternateAssetView.as_view(),
            name="alternate-asset",
        ),
        re_path(
            r"exportCSV/([^/]+)/$",
            exporter_views.ExportCampaignToCSV.as_view(),
            name="export-csv",
        ),
        re_path(
            r"exportBagIt/([^/]+)/$",
            exporter_views.ExportCampaignToBagit.as_view(),
            name="export-bagit",
        ),
        path(
            "<slug:campaign_slug>/report/",
            views.ReportCampaignView.as_view(),
            name="campaign-report",
        ),
        path(
            "<slug:campaign_slug>/<slug:project_slug>/<slug:item_id>/<slug:slug>/",
            views.ConcordiaAssetView.as_view(),
            name="asset-detail",
        ),
        path(
            "<slug:campaign_slug>/<slug:slug>/",
            views.ConcordiaProjectView.as_view(),
            name="project-detail",
        ),
        path(
            "<slug:campaign_slug>/<slug:project_slug>/<slug:item_id>/",
            views.ConcordiaItemView.as_view(),
            name="item",
        ),
    ],
    "transcriptions",
)

ws_urlpatterns = (
    # FIXME: these should be a regular DRF ViewSets rather than a bunch of inconsistent one-off views
    [
        # Web Services
        re_path(
            r"^user_profile/(?P<user_id>(.*?))/$", views_ws.UserProfileGet.as_view()
        ),
        re_path(r"^user/(?P<user_name>(.*?))/$", views_ws.UserGet.as_view()),
        re_path(r"^page_in_use/(?P<page_url>(.*?))/$", views_ws.PageInUseGet.as_view()),
        re_path(
            r"^page_in_use_update/(?P<page_url>(.*?))/$",
            views_ws.PageInUsePut.as_view(),
        ),
        re_path(r"^page_in_use/$", views_ws.PageInUseCreate.as_view()),
        # FIXME: replace this with a standard DRF ViewSet
        re_path(r"^campaign/(?P<slug>(.*?))/$", views_ws.CampaignGet().as_view()),
        re_path(
            r"^campaign_by_id/(?P<id>(.*?))/$", views_ws.CampaignGetById().as_view()
        ),
        re_path(r"^item_by_id/(?P<item_id>(.*?))/$", views_ws.ItemGetById().as_view()),
        re_path(r"^asset/(?P<campaign>(.*?))/$", views_ws.AssetsList().as_view()),
        re_path(
            r"^asset_by_slug/(?P<campaign>(.*?))/(?P<slug>(.*?))/$",
            views_ws.AssetBySlug().as_view(),
        ),
        re_path(
            r"^asset_update/(?P<campaign>(.*?))/(?P<slug>(.*?))/$",
            views_ws.AssetUpdate().as_view(),
        ),
        re_path(
            r"^campaign_asset_random/(?P<campaign>(.*?))/(?P<slug>(.*?))/$",
            views_ws.AssetRandomInCampaign().as_view(),
        ),
        re_path(
            r"^transcription/(?P<asset>(.*?))/$",
            views_ws.TranscriptionLastGet().as_view(),
        ),
        re_path(
            r"^transcription_by_user/(?P<user>(.*?))/$",
            views_ws.TranscriptionByUser().as_view(),
        ),
        re_path(
            r"^transcription_by_asset/(?P<asset_slug>(.*?))/$",
            views_ws.TranscriptionByAsset().as_view(),
        ),
        path(
            "assets/<int:asset_pk>/transcriptions/submit/",
            views_ws.TranscriptionCreate().as_view(),
            name="submit-transcription",
        ),
        path(
            "assets/<int:asset_pk>/tags/",
            views_ws.UserAssetTagsGet().as_view(),
            name="get-tags",
        ),
        path(
            "assets/<int:asset_pk>/tags/submit/",
            views_ws.TagCreate.as_view(),
            name="submit-tags",
        ),
    ],
    "ws",
)

urlpatterns = [
    re_path(r"^$", views.HomeView.as_view(), name="homepage"),
    path(r"healthz", views.healthz, name="health-check"),
    path("about/", views.static_page, name="about"),
    re_path(r"^contact/$", views.ContactUsView.as_view(), name="contact"),
    re_path(r"^campaigns/", include(tx_urlpatterns, namespace="transcriptions")),
    re_path(r"^api/v1/", include(trans_urls)),
    re_path(
        r"^account/register/$",
        views.ConcordiaRegistrationView.as_view(),
        name="registration_register",
    ),
    re_path(
        r"^account/profile/$", views.AccountProfileView.as_view(), name="user-profile"
    ),
    url(r"^accounts/", include("django_registration.backends.activation.urls")),
    url(r"^accounts/", include("django.contrib.auth.urls")),
    re_path(
        r"^experiments/(.+)/$", views.ExperimentsView.as_view(), name="experiments"
    ),
    re_path(r"^wireframes/", include("concordia.experiments.wireframes.urls")),
    re_path(
        r"^privacy-policy/$",
        TemplateView.as_view(template_name="policy.html"),
        name="privacy-policy",
    ),
    re_path(
        r"^cookie-policy/$",
        TemplateView.as_view(template_name="policy.html"),
        name="cookie-policy",
    ),
    re_path(
        r"^legal/$", TemplateView.as_view(template_name="legal.html"), name="legal"
    ),
    # TODO: when we upgrade to Django 2.1 we can use the admin site override
    # mechanism (the old one is broken in 2.0): see https://code.djangoproject.com/ticket/27887
    path("admin/bulk-import", admin_bulk_import_view, name="admin-bulk-import"),
    path("admin/", admin.site.urls),
    # Apps
    path("forum/", include(board.urls)),
    path("captcha/", include("captcha.urls")),
    path("ws/", include(ws_urlpatterns, namespace="ws")),
    re_path(r"^password_reset/$", auth_views.password_reset, name="password_reset"),
    re_path(
        r"^password_reset/done/$",
        auth_views.password_reset_done,
        name="password_reset_done",
    ),
    re_path(
        r"^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$",
        auth_views.password_reset_confirm,
        name="password_reset_confirm",
    ),
    re_path(
        r"^reset/done/$",
        auth_views.password_reset_complete,
        name="password_reset_complete",
    ),
    # Internal support assists:
    path("maintenance-mode/", include("maintenance_mode.urls")),
    path("error/500/", server_error),
    path("error/404/", page_not_found, {"exception": Http404()}),
    path("error/403/", permission_denied, {"exception": HttpResponseForbidden()}),
    url("", include("django_prometheus_metrics.urls")),
    url(r"^robots\.txt", include("robots.urls")),
]

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
