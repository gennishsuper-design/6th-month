from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Comment, Post

User = get_user_model()


class BlogAPITest(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(username='author', password='pass12345')
        self.other_user = User.objects.create_user(username='other', password='pass12345')
        self.published_post = Post.objects.create(
            author=self.author,
            title='Published post',
            body='Published body',
            is_published=True,
        )
        self.draft_post = Post.objects.create(
            author=self.author,
            title='Draft post',
            body='Draft body',
        )

    def test_guest_sees_only_published_posts_with_pagination(self):
        response = self.client.get(reverse('post-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.published_post.id)

    def test_post_list_accepts_page_size_parameter(self):
        response = self.client.get(reverse('post-list'), {'page_size': 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_authenticated_user_creates_post_with_current_user_as_author(self):
        self.client.force_authenticate(self.author)

        response = self.client.post(
            reverse('post-list'),
            {'title': 'New post', 'body': 'Body', 'is_published': True},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_post = Post.objects.get(pk=response.data['id'])
        self.assertEqual(created_post.author, self.author)

    def test_only_post_owner_can_update_or_delete(self):
        url = reverse('post-detail', args=[self.published_post.id])
        self.client.force_authenticate(self.other_user)

        update_response = self.client.put(
            url,
            {'title': 'Changed', 'body': 'Changed body', 'is_published': True},
            format='json',
        )
        delete_response = self.client.delete(url)

        self.assertEqual(update_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_guest_cannot_read_draft_detail(self):
        response = self.client.get(reverse('post-detail', args=[self.draft_post.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authenticated_user_can_create_comment_and_it_is_pending(self):
        self.client.force_authenticate(self.other_user)

        response = self.client.post(
            reverse('comment-list', args=[self.published_post.id]),
            {'body': 'A comment'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        comment = Comment.objects.get(pk=response.data['id'])
        self.assertEqual(comment.author, self.other_user)
        self.assertFalse(comment.is_approved)

    def test_guest_sees_only_approved_comments(self):
        Comment.objects.create(
            post=self.published_post,
            author=self.author,
            body='Pending',
            is_approved=False,
        )
        Comment.objects.create(
            post=self.published_post,
            author=self.author,
            body='Approved',
            is_approved=True,
        )

        response = self.client.get(reverse('comment-list', args=[self.published_post.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['body'], 'Approved')

    def test_only_comment_owner_can_update_or_delete(self):
        comment = Comment.objects.create(
            post=self.published_post,
            author=self.author,
            body='Comment',
        )
        self.client.force_authenticate(self.other_user)
        url = reverse('comment-detail', args=[self.published_post.id, comment.id])

        response = self.client.patch(url, {'body': 'Changed'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
