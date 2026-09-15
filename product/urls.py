from django.urls import path

from .views import CommentDetailView, CommentListCreateView, PostDetailView, PostListCreateView

urlpatterns = [
    path('api/v1/posts/', PostListCreateView.as_view(), name='post-list'),
    path('api/v1/posts/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('api/v1/posts/<int:post_id>/comments/', CommentListCreateView.as_view(), name='comment-list'),
    path('api/v1/posts/<int:post_id>/comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
]
