from rest_framework import serializers

from .models import Comment, Post


class AuthorSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)


class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'body', 'created_at', 'updated_at', 'is_approved']
        read_only_fields = ['id', 'post', 'author', 'created_at', 'updated_at', 'is_approved']


class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'author', 'title', 'body', 'created_at', 'updated_at', 'is_published', 'comments']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'comments']
