from django.urls import path
from . import views

app_name = 'rides'

urlpatterns = [
    path('', views.index, name='index'),
    path('perimeter/', views.perimeter, name='perimeter'),
    path('api/calculate/', views.calculate_ride, name='calculate_ride'),
    path('api/ride/<int:ride_id>/complete/', views.complete_ride, name='complete_ride'),
]
