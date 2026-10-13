from django.urls import path

from .views import (
    CommentDetailView,
    CommentListCreateView,
    PostDetailView,
    PostListCreateView,
    ProductDetailView,
    ProductListCreateView,
)
from users.views import (
    ConfirmRegistrationView,
    GoogleOAuthCallbackView,
    GoogleOAuthStartView,
    LoginView,
    RegisterView,
)

urlpatterns = [
    path('api/v1/auth/register/', RegisterView.as_view(), name='api-register'),
    path('api/v1/auth/confirm/', ConfirmRegistrationView.as_view(), name='api-confirm-registration'),
    path('api/v1/auth/login/', LoginView.as_view(), name='api-login'),
    path('api/v1/auth/token/', LoginView.as_view(), name='api-token'),
    path('api/v1/auth/google/', GoogleOAuthStartView.as_view(), name='google-oauth-start'),
    path('api/v1/auth/google/callback/', GoogleOAuthCallbackView.as_view(), name='google-oauth-callback'),
    path('api/v1/posts/', PostListCreateView.as_view(), name='post-list'),
    path('api/v1/posts/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('api/v1/posts/<int:post_id>/comments/', CommentListCreateView.as_view(), name='comment-list'),
    path('api/v1/posts/<int:post_id>/comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
    path('api/v1/products/', ProductListCreateView.as_view(), name='product-list'),
    path('api/v1/products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
]
