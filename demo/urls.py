
from django.urls import path
from . import views
urlpatterns = [
    path('snatch', views.snatch_view),
    path('open', views.open_view),
    path('get_wallet_list', views.get_wall_list_view)
]
