from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch
import tempfile
from PIL import Image
import io
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Post, Comment, CustomPageNumberPagination
from .serializers import PostSerializer, CommentSerializer, UserRegistrationSerializer


class BaseTestCase(APITestCase):
    """Base test case with common setup for authentication."""
    
    def setUp(self):
        self.client = APIClient()
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User1'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User2'
        )
        
        # Create test posts
        self.post1 = Post.objects.create(
            title='Test Post 1',
            body='This is the body of test post 1.',
            author=self.user1
        )
        self.post2 = Post.objects.create(
            title='Test Post 2',
            body='This is the body of test post 2.',
            author=self.user2
        )
        
        # Create test comments
        self.comment1 = Comment.objects.create(
            post=self.post1,
            author=self.user2,
            body='Great post!'
        )
        
    def get_jwt_token(self, user):
        """Helper method to get JWT token for a user."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def authenticate_user(self, user):
        """Helper method to authenticate a user."""
        token = self.get_jwt_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return token
    
    def create_test_image(self):
        """Helper method to create a test image file."""
        # Create a simple test image
        image = Image.new('RGB', (100, 100), color='red')
        image_file = io.BytesIO()
        image.save(image_file, 'JPEG')
        image_file.seek(0)
        return SimpleUploadedFile(
            'test_image.jpg',
            image_file.getvalue(),
            content_type='image/jpeg'
        )


class PostViewSetTestCase(BaseTestCase):
    """Test cases for PostViewSet endpoints."""
    
    def test_list_posts_unauthenticated(self):
        """Test that unauthenticated users can list posts."""
        url = reverse('posts-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)
        
    def test_list_posts_authenticated(self):
        """Test that authenticated users can list posts."""
        self.authenticate_user(self.user1)
        url = reverse('posts-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
    def test_retrieve_post(self):
        """Test retrieving a single post."""
        url = reverse('posts-detail', kwargs={'pk': self.post1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.post1.id)
        self.assertEqual(response.data['title'], self.post1.title)
        self.assertEqual(response.data['author'], self.user1.username)
        
    def test_create_post_authenticated(self):
        """Test creating a post as authenticated user."""
        self.authenticate_user(self.user1)
        url = reverse('posts-list')
        data = {
            'title': 'New Test Post',
            'body': 'This is a new test post body.'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Test Post')
        self.assertEqual(response.data['author'], self.user1.username)
        
        # Verify post was created in database
        self.assertTrue(Post.objects.filter(title='New Test Post').exists())
        
    def test_create_post_unauthenticated(self):
        """Test that unauthenticated users cannot create posts."""
        url = reverse('posts-list')
        data = {
            'title': 'Unauthorized Post',
            'body': 'This should fail.'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_create_post_with_image(self):
        """Test creating a post with cover photo (simplified without Cloudinary upload)."""
        self.authenticate_user(self.user1)
        url = reverse('posts-list')
        
        # Test without actual image upload to avoid Cloudinary complexity
        data = {
            'title': 'Post with Image',
            'body': 'This post has an image.',
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Post with Image')
        
    def test_update_post_by_author(self):
        """Test updating a post by its author."""
        self.authenticate_user(self.user1)
        url = reverse('posts-detail', kwargs={'pk': self.post1.id})
        data = {
            'title': 'Updated Post Title',
            'body': 'Updated post body.'
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Post Title')
        
        # Verify in database
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.title, 'Updated Post Title')
        
    def test_update_post_by_non_author(self):
        """Test that non-authors cannot update posts."""
        self.authenticate_user(self.user2)  # user2 trying to update user1's post
        url = reverse('posts-detail', kwargs={'pk': self.post1.id})
        data = {
            'title': 'Unauthorized Update',
            'body': 'This should fail.'
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_delete_post_by_author(self):
        """Test deleting a post by its author."""
        self.authenticate_user(self.user1)
        url = reverse('posts-detail', kwargs={'pk': self.post1.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(id=self.post1.id).exists())
        
    def test_delete_post_by_non_author(self):
        """Test that non-authors cannot delete posts."""
        self.authenticate_user(self.user2)  # user2 trying to delete user1's post
        url = reverse('posts-detail', kwargs={'pk': self.post1.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_like_post(self):
        """Test liking a post."""
        self.authenticate_user(self.user2)
        url = reverse('posts-like', kwargs={'pk': self.post1.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'liked')
        self.assertEqual(response.data['likes_count'], 1)
        
        # Verify in database
        self.post1.refresh_from_db()
        self.assertTrue(self.post1.likes.filter(id=self.user2.id).exists())
        
    def test_like_post_twice(self):
        """Test that liking a post twice returns an error."""
        # First like
        self.post1.likes.add(self.user2)
        
        self.authenticate_user(self.user2)
        url = reverse('posts-like', kwargs={'pk': self.post1.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already liked', response.data['error'])
        
    def test_unlike_post(self):
        """Test unliking a post."""
        # First like the post
        self.post1.likes.add(self.user2)
        
        self.authenticate_user(self.user2)
        url = reverse('posts-unlike', kwargs={'pk': self.post1.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'unliked')
        self.assertEqual(response.data['likes_count'], 0)
        
        # Verify in database
        self.post1.refresh_from_db()
        self.assertFalse(self.post1.likes.filter(id=self.user2.id).exists())
        
    def test_unlike_post_not_liked(self):
        """Test that unliking a post that wasn't liked returns an error."""
        self.authenticate_user(self.user2)
        url = reverse('posts-unlike', kwargs={'pk': self.post1.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not liked yet', response.data['error'])
        
    def test_like_unlike_unauthenticated(self):
        """Test that unauthenticated users cannot like/unlike posts."""
        like_url = reverse('posts-like', kwargs={'pk': self.post1.id})
        unlike_url = reverse('posts-unlike', kwargs={'pk': self.post1.id})
        
        like_response = self.client.post(like_url)
        unlike_response = self.client.post(unlike_url)
        
        self.assertEqual(like_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(unlike_response.status_code, status.HTTP_401_UNAUTHORIZED)


class CommentListCreateViewTestCase(BaseTestCase):
    """Test cases for CommentListCreateView endpoints."""
    
    def test_list_comments_for_post(self):
        """Test listing comments for a specific post."""
        url = reverse('post-comments', kwargs={'post_id': self.post1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['body'], 'Great post!')
        self.assertEqual(response.data['results'][0]['author'], self.user2.username)
        
    def test_list_comments_for_nonexistent_post(self):
        """Test listing comments for a post that doesn't exist."""
        url = reverse('post-comments', kwargs={'post_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
        
    def test_create_comment_authenticated(self):
        """Test creating a comment as authenticated user."""
        self.authenticate_user(self.user1)
        url = reverse('post-comments', kwargs={'post_id': self.post2.id})
        data = {
            'body': 'This is a new comment!'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['body'], 'This is a new comment!')
        self.assertEqual(response.data['author'], self.user1.username)
        
        # Verify comment was created in database
        self.assertTrue(Comment.objects.filter(
            post=self.post2, 
            body='This is a new comment!',
            author=self.user1
        ).exists())
        
    def test_create_comment_unauthenticated(self):
        """Test that unauthenticated users cannot create comments."""
        url = reverse('post-comments', kwargs={'post_id': self.post1.id})
        data = {
            'body': 'Unauthorized comment'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_create_comment_for_nonexistent_post(self):
        """Test creating a comment for a post that doesn't exist."""
        self.authenticate_user(self.user1)
        url = reverse('post-comments', kwargs={'post_id': 99999})
        data = {
            'body': 'Comment for non-existent post'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_create_comment_empty_body(self):
        """Test creating a comment with empty body."""
        self.authenticate_user(self.user1)
        url = reverse('post-comments', kwargs={'post_id': self.post1.id})
        data = {
            'body': ''
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_create_comment_missing_body(self):
        """Test creating a comment without body field."""
        self.authenticate_user(self.user1)
        url = reverse('post-comments', kwargs={'post_id': self.post1.id})
        data = {}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('body', response.data)


class AuthenticationTestCase(BaseTestCase):
    """Test cases for authentication endpoints."""
    
    def test_user_signup_valid_data(self):
        """Test user registration with valid data."""
        url = reverse('signup')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepassword123',
            'password_confirm': 'securepassword123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'User created successfully')
        self.assertEqual(response.data['user']['username'], 'newuser')
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')
        self.assertEqual(response.data['user']['first_name'], 'New')
        self.assertEqual(response.data['user']['last_name'], 'User')
        
        # Verify user was created in database
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
    def test_user_signup_password_mismatch(self):
        """Test user registration with password mismatch."""
        url = reverse('signup')
        data = {
            'username': 'newuser2',
            'email': 'newuser2@example.com',
            'password': 'securepassword123',
            'password_confirm': 'differentpassword123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Password fields didn't match", str(response.data))
        
    def test_user_signup_missing_email(self):
        """Test user registration without required email."""
        url = reverse('signup')
        data = {
            'username': 'newuser3',
            'password': 'securepassword123',
            'password_confirm': 'securepassword123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        
    def test_user_signup_weak_password(self):
        """Test user registration with weak password."""
        url = reverse('signup')
        data = {
            'username': 'newuser4',
            'email': 'newuser4@example.com',
            'password': '123',  # Too weak
            'password_confirm': '123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        
    def test_user_signup_duplicate_username(self):
        """Test user registration with existing username."""
        url = reverse('signup')
        data = {
            'username': 'testuser1',  # Already exists
            'email': 'different@example.com',
            'password': 'securepassword123',
            'password_confirm': 'securepassword123',
            'first_name': 'Different',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        
    def test_jwt_token_obtain(self):
        """Test obtaining JWT token with valid credentials."""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser1',
            'password': 'testpassword123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
    def test_jwt_token_obtain_invalid_credentials(self):
        """Test obtaining JWT token with invalid credentials."""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser1',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_jwt_token_refresh(self):
        """Test refreshing JWT token."""
        # First get tokens
        obtain_url = reverse('token_obtain_pair')
        obtain_data = {
            'username': 'testuser1',
            'password': 'testpassword123'
        }
        obtain_response = self.client.post(obtain_url, obtain_data, format='json')
        refresh_token = obtain_response.data['refresh']
        
        # Now refresh the token
        refresh_url = reverse('token_refresh')
        refresh_data = {
            'refresh': refresh_token
        }
        refresh_response = self.client.post(refresh_url, refresh_data, format='json')
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)
        
    def test_jwt_token_refresh_invalid_token(self):
        """Test refreshing JWT token with invalid refresh token."""
        refresh_url = reverse('token_refresh')
        refresh_data = {
            'refresh': 'invalid.refresh.token'
        }
        refresh_response = self.client.post(refresh_url, refresh_data, format='json')
        
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)


class PaginationTestCase(BaseTestCase):
    """Test cases for custom pagination."""
    
    def setUp(self):
        super().setUp()
        # Create additional posts for pagination testing
        for i in range(3, 16):  # Create posts 3-15 (we already have 1 and 2)
            Post.objects.create(
                title=f'Test Post {i}',
                body=f'This is the body of test post {i}.',
                author=self.user1 if i % 2 else self.user2
            )
    
    def test_default_pagination(self):
        """Test default pagination (10 items per page)."""
        url = reverse('posts-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['count'], 15)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])
        
    def test_custom_page_size(self):
        """Test custom page size parameter."""
        url = reverse('posts-list')
        response = self.client.get(url, {'page_size': 5})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['count'], 15)
        self.assertIsNotNone(response.data['next'])
        
    def test_max_page_size_limit(self):
        """Test that page size is limited to maximum allowed."""
        url = reverse('posts-list')
        response = self.client.get(url, {'page_size': 200})  # Above max of 100
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 15)  # All posts since we have less than 100
        
    def test_page_navigation(self):
        """Test navigating between pages."""
        url = reverse('posts-list')
        
        # Page 1
        page1_response = self.client.get(url, {'page': 1, 'page_size': 5})
        self.assertEqual(len(page1_response.data['results']), 5)
        self.assertIsNone(page1_response.data['previous'])
        self.assertIsNotNone(page1_response.data['next'])
        
        # Page 2
        page2_response = self.client.get(url, {'page': 2, 'page_size': 5})
        self.assertEqual(len(page2_response.data['results']), 5)
        self.assertIsNotNone(page2_response.data['previous'])
        self.assertIsNotNone(page2_response.data['next'])
        
        # Page 3 (last page)
        page3_response = self.client.get(url, {'page': 3, 'page_size': 5})
        self.assertEqual(len(page3_response.data['results']), 5)
        self.assertIsNotNone(page3_response.data['previous'])
        self.assertIsNone(page3_response.data['next'])
        
    def test_invalid_page_number(self):
        """Test requesting an invalid page number."""
        url = reverse('posts-list')
        response = self.client.get(url, {'page': 999})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_comment_pagination(self):
        """Test pagination on comments endpoint."""
        # Create multiple comments for a post
        for i in range(15):
            Comment.objects.create(
                post=self.post1,
                author=self.user1 if i % 2 else self.user2,
                body=f'Comment number {i+1}'
            )
            
        url = reverse('post-comments', kwargs={'post_id': self.post1.id})
        response = self.client.get(url, {'page_size': 5})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['count'], 16)  # 15 new + 1 existing


class ModelTestCase(BaseTestCase):
    """Test cases for models."""
    
    def test_post_str_method(self):
        """Test Post model __str__ method."""
        self.assertEqual(str(self.post1), 'Test Post 1')
        
    def test_post_likes_count_property(self):
        """Test Post model likes_count property."""
        # Initially no likes
        self.assertEqual(self.post1.likes_count, 0)
        
        # Add some likes
        self.post1.likes.add(self.user1, self.user2)
        self.assertEqual(self.post1.likes_count, 2)
        
    def test_post_relationships(self):
        """Test Post model relationships."""
        # Test author relationship
        self.assertEqual(self.post1.author, self.user1)
        
        # Test likes many-to-many relationship
        self.post1.likes.add(self.user2)
        self.assertIn(self.user2, self.post1.likes.all())
        
        # Test comments relationship
        self.assertIn(self.comment1, self.post1.comments.all())
        
    def test_comment_str_method(self):
        """Test Comment model __str__ method."""
        expected = f'Comment by {self.user2.username} on {self.post1.title}'
        self.assertEqual(str(self.comment1), expected)
        
    def test_comment_relationships(self):
        """Test Comment model relationships."""
        # Test post relationship
        self.assertEqual(self.comment1.post, self.post1)
        
        # Test author relationship
        self.assertEqual(self.comment1.author, self.user2)
        
    def test_user_post_relationship(self):
        """Test reverse relationship from User to Posts."""
        user1_posts = self.user1.posts.all()
        self.assertIn(self.post1, user1_posts)
        self.assertEqual(user1_posts.count(), 1)
        
    def test_user_liked_posts_relationship(self):
        """Test reverse relationship from User to liked Posts."""
        self.post1.likes.add(self.user2)
        user2_liked_posts = self.user2.liked_posts.all()
        self.assertIn(self.post1, user2_liked_posts)
        
    def test_post_cascade_deletion(self):
        """Test that deleting a post deletes associated comments."""
        post_id = self.post1.id
        comment_id = self.comment1.id
        
        # Verify comment exists
        self.assertTrue(Comment.objects.filter(id=comment_id).exists())
        
        # Delete post
        self.post1.delete()
        
        # Verify comment was also deleted
        self.assertFalse(Comment.objects.filter(id=comment_id).exists())
        self.assertFalse(Post.objects.filter(id=post_id).exists())
        
    def test_custom_pagination_class(self):
        """Test CustomPageNumberPagination class directly."""
        paginator = CustomPageNumberPagination()
        
        # Test default values
        self.assertEqual(paginator.page_size, 10)
        self.assertEqual(paginator.page_size_query_param, 'page_size')
        self.assertEqual(paginator.max_page_size, 100)
        self.assertEqual(paginator.page_query_param, 'page')
