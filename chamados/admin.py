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
    list_display = (
        'loja',
        'lider',
        'regional',
        'motivo',
        'aberto_por',
        'aberto_em',
        'status',
        'fechado_por',
        'fechado_em',
        'duracao_formatada',
    )
    list_filter = (
        'status',
        'regional',
        'loja',
        ('aberto_em', admin.DateFieldListFilter),  # CORRETO
    )
    search_fields = ('loja', 'lider', 'regional', 'motivo', 'observacao')
    readonly_fields = ('aberto_por', 'aberto_em', 'fechado_por', 'fechado_em', 'duracao')
    date_hierarchy = 'aberto_em'

    def duracao_formatada(self, obj):
        if obj.duracao:
            total_seconds = int(obj.duracao.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}min" if hours else f"{minutes}min"
        return "—"
    duracao_formatada.short_description = "Duração"

    def has_change_permission(self, request, obj=None):
        # Só admin/gestor pode editar
        return request.user.is_staff or getattr(request.user, 'papel', '').lower() == 'gestor'

    def has_delete_permission(self, request, obj=None):
        return request.user.is_staff


@admin.register(InventarioExcel)
class InventarioExcelAdmin(admin.ModelAdmin):
    list_display = ('loja', 'regional', 'lider', 'data', 'criado_em')
    search_fields = ('loja', 'regional', 'lider')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'texto', 'criado_em', 'enviado_por_admin')
    list_filter = ('enviado_por_admin',)
    search_fields = ('usuario__username', 'texto')
