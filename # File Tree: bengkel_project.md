# File Tree: bengkel_project

Generated on: 21/10/2025, 14:53:41
Root path: `/home/meoze/Documents/new/NGAMPUS/magang project/bengkel abangkuh/bengkel_project/bengkel_project`

```
├── 📁 settings/
│   ├── 🐍 __init__.py
│   ├── 🐍 base.py
            import os
            from pathlib import Path
            
            # Build paths inside the project like this: BASE_DIR / 'subdir'.
            BASE_DIR = Path(__file__).resolve().parent.parent.parent
            
            # Quick-start development settings - unsuitable for production
            # See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/
            
            # SECURITY WARNING: keep the secret key used in production secret!
            SECRET_KEY = os.getenv('SECRET_KEY', 'default-insecure-secret-key-for-local-dev')
            
            # SECURITY WARNING: don't run with debug turned on in production!
            DEBUG = os.getenv('DEBUG', 'False') == 'True'
            
            ALLOWED_HOSTS = []
            
            
            # Application definition
            
            INSTALLED_APPS = [
                'django.contrib.admin',
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.messages',
                'django.contrib.staticfiles',
            
                # Third-party apps
                'crispy_forms',
                'crispy_bootstrap5',
                'django_extensions',
                'debug_toolbar',
            
                # Our apps
                'apps.accounts',
                'apps.dashboard',
                'apps.transactions.apps.TransactionsConfig', 
                'apps.inventory',
                'apps.master_data',
                'apps.expenses',
                'apps.purchases.apps.PurchasesConfig', 
                'apps.reports',
            ]
            
            MIDDLEWARE = [
                'django.middleware.security.SecurityMiddleware',
                'django.contrib.sessions.middleware.SessionMiddleware',
                'django.middleware.common.CommonMiddleware',
                'django.middleware.csrf.CsrfViewMiddleware',
                'django.contrib.auth.middleware.AuthenticationMiddleware',
                'django.contrib.messages.middleware.MessageMiddleware',
                'django.middleware.clickjacking.XFrameOptionsMiddleware',
                # Django Debug Toolbar Middleware
                'debug_toolbar.middleware.DebugToolbarMiddleware',
            
            ]
            
            ROOT_URLCONF = 'bengkel_project.urls'
            
            TEMPLATES = [
                {
                    'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    # Beritahu Django untuk mencari template di folder 'templates' global
                    'DIRS': [BASE_DIR / 'templates'],
                    'APP_DIRS': True,
                    'OPTIONS': {
                        'context_processors': [
                            'django.template.context_processors.debug',
                            'django.template.context_processors.request',
                            'django.contrib.auth.context_processors.auth',
                            'django.contrib.messages.context_processors.messages',
                        ],
                    },
                },
            ]
            
            WSGI_APPLICATION = 'bengkel_project.wsgi.application'
            
            
            # Database
            # https://docs.djangoproject.com/en/4.2/ref/settings/#databases
            
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': os.getenv('DB_NAME'),
                    'USER': os.getenv('DB_USER'),
                    'PASSWORD': os.getenv('DB_PASSWORD'),
                    'HOST': os.getenv('DB_HOST'),
                    'PORT': os.getenv('DB_PORT'),
                }
            }
            
            
            # Password validation
            # https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
            
            AUTH_PASSWORD_VALIDATORS = [
                # ... (biarkan default)
            ]
            
            
            # Internationalization
            # https://docs.djangoproject.com/en/4.2/topics/i18n/
            
            LANGUAGE_CODE = 'en-us'
            TIME_ZONE = 'Asia/Jakarta' # Ganti ke zona waktu Indonesia
            USE_I18N = True
            USE_TZ = True
            
            
            # Static files (CSS, JavaScript, Images)
            # https://docs.djangoproject.com/en/4.2/howto/static-files/
            
            STATIC_URL = '/static/'
            STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # lokasi folder untuk collectstatic
            STATICFILES_DIRS = [
                os.path.join(BASE_DIR, 'static'),
            ]
            # STATIC_ROOT = BASE_DIR / 'staticfiles' # Digunakan saat production
            
            # Media files (User uploaded files)
            MEDIA_URL = '/media/'
            MEDIA_ROOT = BASE_DIR / 'media'
            
            
            # Default primary key field type
            # https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
            
            DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
            
            
            # Django Crispy Forms
            CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
            CRISPY_TEMPLATE_PACK = "bootstrap5"
            
            
            # Django Debug Toolbar
            INTERNAL_IPS = [
                "127.0.0.1",
            ]
            
            
            AUTH_USER_MODEL = 'accounts.CustomUser'
            
│   ├── 🐍 development.py
            # bengkel_project/settings/development.py
            
            # Impor semua settingan dari base.py
            from .base import *
            
            # Settingan khusus untuk mode development
            
            # Izinkan semua host saat development
            ALLOWED_HOSTS = ['*']
            
            # Di sini kita bisa menambahkan settingan lain khusus development,
            # misalnya jika kita menggunakan database yang berbeda untuk testing.
            # Untuk sekarang, ini sudah cukup.
            
            print("Development settings loaded.") # Pesan ini untuk memastikan file ini yang dipakai
│   └── 🐍 production.py
├── 🐍 __init__.py
├── 🐍 asgi.py
        """
        ASGI config for bengkel_project project.
        
        It exposes the ASGI callable as a module-level variable named ``application``.
        
        For more information on this file, see
        https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
        """
        
        import os
        
        from django.core.asgi import get_asgi_application
        
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bengkel_project.settings")
        
        application = get_asgi_application()
        
├── 🐍 settings.py
            """
            Django settings for bengkel_project project.
            
            Generated by 'django-admin startproject' using Django 5.2.7.
            
            For more information on this file, see
            https://docs.djangoproject.com/en/5.2/topics/settings/
            
            For the full list of settings and their values, see
            https://docs.djangoproject.com/en/5.2/ref/settings/
            """
            
            from pathlib import Path
            
            # Build paths inside the project like this: BASE_DIR / 'subdir'.
            BASE_DIR = Path(__file__).resolve().parent.parent
            
            
            # Quick-start development settings - unsuitable for production
            # See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
            
            # SECURITY WARNING: keep the secret key used in production secret!
            SECRET_KEY = "django-insecure-#i5d3t8th8z=&nyr85(w-hrn0z6@ah14e^xj5r+n69l7o=5%rd"
            
            # SECURITY WARNING: don't run with debug turned on in production!
            DEBUG = True
            
            ALLOWED_HOSTS = []
            
            
            # Application definition
            
            INSTALLED_APPS = [
                "django.contrib.admin",
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "django.contrib.sessions",
                "django.contrib.messages",
                "django.contrib.staticfiles",
            ]
            
            MIDDLEWARE = [
                "django.middleware.security.SecurityMiddleware",
                "django.contrib.sessions.middleware.SessionMiddleware",
                "django.middleware.common.CommonMiddleware",
                "django.middleware.csrf.CsrfViewMiddleware",
                "django.contrib.auth.middleware.AuthenticationMiddleware",
                "django.contrib.messages.middleware.MessageMiddleware",
                "django.middleware.clickjacking.XFrameOptionsMiddleware",
            ]
            
            ROOT_URLCONF = "bengkel_project.urls"
            
            TEMPLATES = [
                {
                    "BACKEND": "django.template.backends.django.DjangoTemplates",
                    "DIRS": [],
                    "APP_DIRS": True,
                    "OPTIONS": {
                        "context_processors": [
                            "django.template.context_processors.request",
                            "django.contrib.auth.context_processors.auth",
                            "django.contrib.messages.context_processors.messages",
                        ],
                    },
                },
            ]
            
            WSGI_APPLICATION = "bengkel_project.wsgi.application"
            
            
            # Database
            # https://docs.djangoproject.com/en/5.2/ref/settings/#databases
            
            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": BASE_DIR / "db.sqlite3",
                }
            }
            
            
            # Password validation
            # https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
            
            AUTH_PASSWORD_VALIDATORS = [
                {
                    "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
                },
                {
                    "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
                },
                {
                    "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
                },
                {
                    "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
                },
            ]
            
            
            # Internationalization
            # https://docs.djangoproject.com/en/5.2/topics/i18n/
            
            LANGUAGE_CODE = "en-us"
            
            TIME_ZONE = "UTC"
            
            USE_I18N = True
            
            USE_TZ = True
            
            
            # Static files (CSS, JavaScript, Images)
            # https://docs.djangoproject.com/en/5.2/howto/static-files/
            
            STATIC_URL = "static/"
            
            # Default primary key field type
            # https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
            
            DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
            
├── 🐍 urls.py
        """
        URL configuration for bengkel_project project.
        
        The `urlpatterns` list routes URLs to views. For more information please see:
            https://docs.djangoproject.com/en/5.2/topics/http/urls/
        Examples:
        Function views
            1. Add an import:  from my_app import views
            2. Add a URL to urlpatterns:  path('', views.home, name='home')
        Class-based views
            1. Add an import:  from other_app.views import Home
            2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
        Including another URLconf
            1. Import the include() function: from django.urls import include, path
            2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
        """
        
        # bengkel_project/urls.py
        # bengkel_project/urls.py
        
        from django.contrib import admin
        from django.urls import path, include
        from django.conf import settings
        from django.conf.urls.static import static
        
        
        urlpatterns = [
            path('admin/', admin.site.urls),
            
            # Jadikan halaman dashboard sebagai halaman utama
            path('', include('apps.dashboard.urls', namespace='dashboard')),
            
            # Arahkan semua URL yang berawalan 'transactions/' ke apps/transactions/urls.py
            path('transactions/', include('apps.transactions.urls', namespace='transactions')),
            path('inventory/', include('apps.inventory.urls', namespace='inventory')),
            path('purchases/', include('apps.purchases.urls', namespace='purchases')),
            path('master-data/', include('apps.master_data.urls')),
            path('reports/', include('apps.reports.urls')),
        
        ]
        
        if settings.DEBUG:
            urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
            urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
└── 🐍 wsgi.py
        """
        WSGI config for bengkel_project project.
        
        It exposes the WSGI callable as a module-level variable named ``application``.
        
        For more information on this file, see
        https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
        """
        
        import os
        
        from django.core.wsgi import get_wsgi_application
        
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bengkel_project.settings")
        
        application = get_wsgi_application()
        
```

---
*Generated by FileTree Pro Extension*