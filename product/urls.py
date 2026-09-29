from django.urls import path

from .views import CommentDetailView, CommentListCreateView, PostDetailView, PostListCreateView
from users.views import LoginView, RegisterView

urlpatterns = [
    path('api/v1/auth/register/', RegisterView.as_view(), name='api-register'),
    path('api/v1/auth/login/', LoginView.as_view(), name='api-login'),
    path('api/v1/auth/token/', LoginView.as_view(), name='api-token'),
    path('api/v1/posts/', PostListCreateView.as_view(), name='post-list'),
    path('api/v1/posts/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('api/v1/posts/<int:post_id>/comments/', CommentListCreateView.as_view(), name='comment-list'),
    path('api/v1/posts/<int:post_id>/comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
]
