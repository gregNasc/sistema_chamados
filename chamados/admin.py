from django.contrib import admin
from .models import Chamado, CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'papel', 'is_staff', 'is_superuser')

@admin.register(Chamado)
class ChamadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'regional', 'loja', 'lider', 'motivo', 'status', 'abertura', 'fechamento')
    list_filter = ('status', 'regional', 'motivo')
    search_fields = ('usuario__username', 'lider', 'motivo', 'loja')
