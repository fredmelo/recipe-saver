from django.urls import path
from recipes import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('recipes/', views.recipe_list, name='recipe_list'),
    path('recipes/new/', views.recipe_create, name='recipe_create'),
    path('recipes/<int:pk>/', views.recipe_detail, name='recipe_detail'),
    path('recipes/<int:pk>/edit/', views.recipe_edit, name='recipe_edit'),
    path('recipes/<int:pk>/delete/', views.recipe_delete, name='recipe_delete'),
    path('api/scrape/', views.scrape_url, name='scrape_url'),
    path('api/tags/', views.tag_create, name='tag_create'),
]
