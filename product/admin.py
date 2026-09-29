from django.contrib import admin

from .models import Comment, Post, Product


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'is_published', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'body', 'author__email')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'author', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('body', 'author__email', 'post__title')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner', 'price')
    search_fields = ('title', 'description', 'owner__email')
