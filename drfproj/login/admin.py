from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm
from .models import User, reports, Subject, SubjectScore


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            self.fields['username'].empty_value = ''


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    list_display = ('email', 'username', 'user_type', 'is_staff', 'is_active', 'is_verified')
    list_filter = ('user_type', 'is_staff', 'is_active', 'is_verified')
    search_fields = ('email', 'username')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'profile_picture')}),
        ('Membership', {'fields': ('user_type',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'is_verified', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )




class reportsadmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'class_name', 'total_score', 'percentage')
    search_fields = ('user__email', 'name', 'class_name')

admin.site.register(reports, reportsadmin)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_score')
    search_fields = ('name',)


@admin.register(SubjectScore)
class SubjectScoreAdmin(admin.ModelAdmin):
    list_display = ('report', 'subject', 'score')
    search_fields = ('report__user__email', 'subject__name')