[app]

# (str) Title of your application
title = Shelly 3EM

# (str) Package name
package.name = shelly3em

# (str) Package domain (needed for android/aidl)
package.domain = org.example

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (list) List of inclusions using pattern matching
source.include_patterns = assets/*,images/*.png

# (list) List of exclusions using pattern matching
source.exclude_patterns = **/.git/**, **/__pycache__/**

# (str) Application versioning (method 1)
version = 0.1.0

# (str) Application requirements
requirements = python3,kivy,requests

# (str) Supported orientation (one of landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Android permissions
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible
android.api = 31

# (int) Minimum API your APK will support
android.minapi = 21

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (list) Android additional libraries to copy into APK
#android.add_libs_armeabi = libs/android/*.so

# (bool) Indicate whether to package the app in a .apk or .aab
p4a.branch = stable


[buildozer]
# (int) Log level (0 = quiet, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1

# (bool) Use python -m pip instead of pip when installing requirements
# use_pip = False
