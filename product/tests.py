from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Comment, Post

User = get_user_model()


class BlogAPITest(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(email='author@example.com', password='pass12345')
        self.other_user = User.objects.create_user(email='other@example.com', password='pass12345')
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


class UserAuthAPITest(APITestCase):
    def test_registration_allows_missing_phone_number(self):
        response = self.client.post(
            reverse('api-register'),
            {'email': 'new@example.com', 'password': 'SafePass12345!'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='new@example.com')
        self.assertEqual(user.phone_number, '')
        self.assertFalse(user.is_superuser)

    def test_registration_rejects_phone_number_without_996_prefix(self):
        response = self.client.post(
            reverse('api-register'),
            {
                'email': 'new@example.com',
                'password': 'SafePass12345!',
                'phone_number': '+12345678901',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data)

    def test_login_uses_email_and_returns_auth_token(self):
        User.objects.create_user(email='login@example.com', password='SafePass12345!')

        response = self.client.post(
            reverse('api-login'),
            {'email': 'login@example.com', 'password': 'SafePass12345!'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_superuser_requires_a_valid_phone_number(self):
        with self.assertRaisesMessage(ValueError, 'A phone number is required'):
            User.objects.create_superuser(email='root@example.com', password='SafePass12345!')

        with self.assertRaises(ValidationError):
            User.objects.create_superuser(
                email='root@example.com',
                password='SafePass12345!',
                phone_number='123456789',
            )

        root = User.objects.create_superuser(
            email='root@example.com',
            password='SafePass12345!',
            phone_number='+996555123456',
        )
        self.assertTrue(root.is_superuser)

    def test_custom_user_admin_page_uses_email_account(self):
        admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='SafePass12345!',
            phone_number='+996555123456',
        )
        self.client.force_login(admin_user)

        response = self.client.get('/admin/users/user/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
