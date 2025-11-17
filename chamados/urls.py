from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from .views import exportar_excel_form, exportar_excel_view

# Namespace do app
app_name = 'chamados'

urlpatterns = [

    # ------------------------------
    # Autenticação
    # ------------------------------
    path('login/', auth_views.LoginView.as_view(template_name='chamados/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page=reverse_lazy('chamados:login')), name='logout'),

    # ------------------------------
    # Sistema de Chamados
    # ------------------------------
    path('', views.sistema_chamados_view, name='sistema_chamados'),
    path('ativos/', views.chamados_ativos, name='chamados_ativos'),
    path('finalizar/<int:pk>/', views.finalizar_chamado_view, name='finalizar_chamado'),
    path('todos/', views.todos_chamados, name='todos_chamados'),
    path('usuarios/', views.gerenciar_usuarios, name='gerenciar_usuarios'),
    path('usuarios/cadastrar/', views.cadastrar_usuario, name='cadastrar_usuario'),
    path('usuarios/<int:user_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:user_id>/excluir/', views.excluir_usuario, name='excluir_usuario'),
    # ------------------------------
    # Endpoints AJAX
    # ------------------------------
    path('ajax/regionais/', views.regionais_por_data, name='regionais_por_data'),
    path('ajax/lojas/', views.lojas_por_regional, name='lojas_por_regional'),
    path('ajax/lider/', views.lider_por_loja, name='lider_por_loja'),

    # ------------------------------
    # Upload / Export Excel
    # ------------------------------
    path("upload_excel/", views.upload_excel, name="upload_excel"),
    path('exportar_excel/', views.exportar_excel_view, name='exportar_excel'),

    # ------------------------------
    # Dashboard
    # ------------------------------
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard_admin/filtrar/', views.filtrar_dashboard, name='filtrar_dashboard'),
    path('exportar/', exportar_excel_form, name='exportar_excel_form'),
    path('exportar/download/', exportar_excel_view, name='exportar_excel'),

    # ------------------------------
    # Zeragem do banco (apenas admin)
    # ------------------------------
    path('zerar-banco/', views.zerar_banco_view, name='zerar_banco'),

    path('run-migrations/', views.run_migrations, name='run-migrations'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG is False:
    urlpatterns += [
        path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    ]