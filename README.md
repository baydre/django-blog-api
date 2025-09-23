# Django Blog API

A RESTful API for a blog application built with Django and Django REST Framework.

**Technical Task for Communisolve Python Django Developer Role**

## Features

- 🚀 RESTful API built with Django REST Framework
- 🔐 JWT Authentication with djangorestframework-simplejwt
- 📝 Blog post management
- 🌐 CORS support for frontend integration
- 📊 API documentation with drf-spectacular
- 🖼️ Image handling with Cloudinary storage
- 🗄️ PostgreSQL database support
- 🧪 Testing with pytest-django
- 🚀 Production-ready with Gunicorn and WhiteNoise

## Tech Stack

- **Framework**: Django 4.2
- **API**: Django REST Framework
- **Authentication**: JWT (Simple JWT)
- **Database**: PostgreSQL (with SQLite for development)
- **File Storage**: Cloudinary
- **Documentation**: drf-spectacular (OpenAPI/Swagger)
- **Testing**: pytest-django
- **Server**: Gunicorn
- **Static Files**: WhiteNoise

## Prerequisites

- Python 3.11+
- PostgreSQL (for production)
- uv (for dependency management)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/baydre/django-blog-api.git
   cd django-blog-api
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   uv pip install -r requirements.txt
   # or
   uv add -r requirements.txt
   ```

4. **Environment Variables**
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   DATABASE_URL=postgres://user:password@localhost:5432/django_blog_api
   CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name
   CLOUDINARY_API_KEY=your-cloudinary-api-key
   CLOUDINARY_API_SECRET=your-cloudinary-api-secret
   ```

5. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration
- `POST /api/auth/refresh/` - Refresh JWT token

### Blog Posts
- `GET /api/posts/` - List all blog posts
- `POST /api/posts/` - Create a new blog post
- `GET /api/posts/{id}/` - Retrieve a specific blog post
- `PUT /api/posts/{id}/` - Update a blog post
- `DELETE /api/posts/{id}/` - Delete a blog post

### Documentation
- `GET /api/schema/` - OpenAPI schema
- `GET /api/docs/` - Swagger UI documentation
- `GET /api/redoc/` - ReDoc documentation

## Development

### Running Tests
```bash
pytest
```

### Code Quality
```bash
# Format code
black .

# Check linting
flake8 .

# Type checking
mypy .
```

### Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

## Project Structure

```
django-blog-api/
├── blog/                   # Blog app
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
├── config/                 # Django project settings
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── .env                    # Environment variables (create this)
├── .gitignore
├── main.py
├── manage.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Deployment

### Using Gunicorn
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Environment Variables for Production
```env
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=postgres://user:password@localhost:5432/django_blog_api_prod
CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-api-key
CLOUDINARY_API_SECRET=your-cloudinary-api-secret
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For questions about this technical task, please contact the Communisolve development team.
