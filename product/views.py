from rest_framework import generics, permissions
from rest_framework.authentication import TokenAuthentication

from .models import Comment, Post, Product
from .serializers import CommentSerializer, PostSerializer, ProductSerializer


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.author_id == request.user.id


class IsModerator(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user.is_authenticated and not request.user.is_staff
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and (
            request.user.is_staff or obj.owner_id == request.user.id
        )


class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Post.objects.select_related('author').prefetch_related('comments__author')
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_published=True)
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    queryset = Post.objects.select_related('author').prefetch_related('comments__author')

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_published=True)
        return queryset


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        queryset = Comment.objects.select_related('author', 'post').filter(post_id=self.kwargs['post_id'])
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_approved=True, post__is_published=True)
        return queryset.order_by('created_at')

    def perform_create(self, serializer):
        post = generics.get_object_or_404(Post, pk=self.kwargs['post_id'])
        serializer.save(post=post, author=self.request.user)

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Comment.objects.select_related('author', 'post').filter(post_id=self.kwargs['post_id'])


class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsModerator]
    queryset = Product.objects.select_related('owner').all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsModerator]
    queryset = Product.objects.select_related('owner').all()
