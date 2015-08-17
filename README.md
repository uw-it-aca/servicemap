# servicemap

This README documents whatever steps are necessary to get your application up and running.

## Installing the application ##

**Create a virtualenv for your project**
    
    $ virutualenv yourenv
    $ cd yourenv
    $ source bin/activate

**Create an empty Django project**
    
    $ (yourenv) django-admin.py startproject yourproj
    $ (yourenv) cd yourproj
        
**Install ServiceMap app**  
    
    $ (yourenv) pip install -e git+https://github.com/vegitron/servicemap/#egg=servicemap
    
**Update your urls.py**
    
    urlpatterns = patterns('',
        ...
        url(r'^', include('servicemap.urls')),
    )
    
**Update your settings.py**
    
    INSTALLED_APPS = (
        ...
        'compressor',
        'servicemap',
    )

    MIDDLEWARE_CLASSES = (
        ...
        'django_mobileesp.middleware.UserAgentDetectionMiddleware',
    )

    STATICFILES_FINDERS = (
        "django.contrib.staticfiles.finders.FileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
        'compressor.finders.CompressorFinder',
    )
    
    # compressor
    COMPRESS_ROOT = "/tmp/some/path/for/files"
    COMPRESS_PRECOMPILERS = (('text/less', 'lessc {infile} {outfile}'),)
    COMPRESS_ENABLED = False # True if you want to compress your development build
    COMPRESS_OFFLINE = False # True if you want to compress your build offline
    COMPRESS_CSS_FILTERS = [
        'compressor.filters.css_default.CssAbsoluteFilter',
        'compressor.filters.cssmin.CSSMinFilter'
    ]
    COMPRESS_JS_FILTERS = [
        'compressor.filters.jsmin.JSMinFilter',
    ]
       
    # mobileesp
    from django_mobileesp.detector import mobileesp_agent as agent
    
    DETECT_USER_AGENTS = {
        'is_mobile': agent.detectMobileQuick,
        'is_tablet' : agent.detectTierTablet,
    }

**Create your database**
    $ (yourenv) python manage.py syncdb

**Run your server:**
    
    $ (yourenv) python manage.py runserver 0:8000
    
    
**It worked!** 
    
    You should see the Django server running when viewing http://localhost:8000