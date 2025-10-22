from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Chamado, InventarioExcel, ChatMessage


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'papel', 'is_staff', 'is_active')
    list_filter = ('papel', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações pessoais', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissões', {'fields': ('papel', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'papel', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)


@admin.register(Chamado)
class ChamadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'regional', 'loja', 'lider', 'motivo', 'status', 'abertura', 'fechamento')
    list_filter = ('status', 'regional', 'motivo')
    search_fields = ('usuario__username', 'lider', 'motivo', 'loja')


@admin.register(InventarioExcel)
class InventarioExcelAdmin(admin.ModelAdmin):
    list_display = ('loja', 'regional', 'lider', 'data', 'criado_em')
    search_fields = ('loja', 'regional', 'lider')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'texto', 'criado_em', 'enviado_por_admin')
    list_filter = ('enviado_por_admin',)
    search_fields = ('usuario__username', 'texto')
