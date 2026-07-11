from django.urls import path
from tracker.views.auth_views import (
    RegisterView, CustomLoginView, CustomLogoutView,
    CustomPasswordChangeView, CustomPasswordChangeDoneView,
)
app_name = 'auth'
urlpatterns = [
    path('register/',             RegisterView.as_view(),               name='register'),
    path('login/',                CustomLoginView.as_view(),            name='login'),
    path('logout/',               CustomLogoutView.as_view(),           name='logout'),
    path('password/change/',      CustomPasswordChangeView.as_view(),   name='password_change'),
    path('password/change/done/', CustomPasswordChangeDoneView.as_view(),name='password_change_done'),
]
