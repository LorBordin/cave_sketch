# Chaquopy / embedded CPython runtime — keep reflectively-used classes.
-keep class com.chaquo.python.** { *; }
-dontwarn com.chaquo.python.**

# App entry points referenced via Compose/AndroidX reflection are kept by AGP's
# default rules; nothing else app-specific needs keeping.
