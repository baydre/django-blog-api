# from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListCreateAPIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, BasePermission
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Post, Comment
from .serializers import PostSerializer, CommentSerializer, UserRegistrationSerializer


class IsAuthorOrReadOnly(BasePermission):
    """
    Custom permission to only allow authors of a post to edit it.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        
        # Write permissions are only allowed to authenticated users.
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        
        # Write permissions are only allowed to the author of the post.
        return obj.author == request.user
class PostViewSet(ModelViewSet):
    queryset = Post.objects.all().order_by('-created_at').select_related('author').prefetch_related('likes','comments')
    serializer_class = PostSerializer
    permission_classes = [IsAuthorOrReadOnly]
    parser_classes = [JSONParser, MultiPartParser, FormParser]  # Support JSON and file uploads

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """Like a post. Returns error if already liked."""
        post = self.get_object()
        user = request.user
        if user in post.likes.all():
            return Response({'error': 'Post already liked'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            post.likes.add(user)
            return Response({'status': 'liked', 'likes_count': post.likes_count}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unlike(self, request, pk=None):
        """Unlike a post. Returns error if not liked."""
        post = self.get_object()
        user = request.user
        if user not in post.likes.all():
            return Response({'error': 'Post not liked yet'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            post.likes.remove(user)
            return Response({'status': 'unliked', 'likes_count': post.likes_count}, status=status.HTTP_200_OK)

class CommentListCreateView(ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='post_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Post ID'
            )
        ]
    )
    def get_queryset(self):
        return Comment.objects.filter(post_id=self.kwargs['post_id']).select_related('author')

    def perform_create(self, serializer):
        try:
            post = Post.objects.get(pk=self.kwargs['post_id'])
            serializer.save(author=self.request.user, post=post)
        except Post.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Post not found.')

@extend_schema(
    request=UserRegistrationSerializer,
    responses={201: UserRegistrationSerializer}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def signup_view(request):
    """
    Create a new user account.
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                'message': 'User created successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
            },
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
