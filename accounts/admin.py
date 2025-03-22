from django.contrib import admin
from .models import Profile, UnverifiedUser

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'is_verified')
    list_filter = ('status', 'is_verified')
    search_fields = ('user__username', 'user__email')

class UnverifiedUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('username', 'email')

admin.site.register(Profile, ProfileAdmin)
admin.site.register(UnverifiedUser, UnverifiedUserAdmin)