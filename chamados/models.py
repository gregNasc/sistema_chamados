from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings


class CustomUser(AbstractUser):
    PAPEL_CHOICES = (
        ('admin', 'Administrador'),
        ('gestor', 'Gestor'),
        ('usuario', 'Usuário'),
    )
    papel = models.CharField(max_length=10, choices=PAPEL_CHOICES, default='usuario')
    telefone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_papel_display()})"

class Chamado(models.Model):
    STATUS_CHOICES = (
        ('Aberto', 'Aberto'),
        ('Finalizado', 'Finalizado'),
    )

    # === AUDITORIA ===
    aberto_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chamados_abertos'
    )
    aberto_em = models.DateTimeField(default=timezone.now)

    fechado_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chamados_fechados'
    )
    fechado_em = models.DateTimeField(null=True, blank=True)

    # === DADOS DO CHAMADO ===
    regional = models.CharField(max_length=100)
    loja = models.CharField(max_length=100)
    lider = models.CharField(max_length=100)
    motivo = models.CharField(max_length=200)
    outro_motivo = models.CharField(max_length=200, null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Aberto')
    observacao = models.TextField(null=True, blank=True)

    # === DURAÇÃO ===
    duracao = models.DurationField(null=True, blank=True)  # Calculada ou manual
    tempo_manual = models.DurationField(null=True, blank=True)  # Sobrescreve cálculo

    # === LEGADO (opcional) ===
    data = models.DateField(null=True, blank=True, help_text="Data de referência (legado)")
    usuario = models.CharField(max_length=100, blank=True, null=True, editable=False)

    class Meta:
        verbose_name = 'Chamado'
        verbose_name_plural = 'Chamados'
        ordering = ['-aberto_em']

    def __str__(self):
        return f"#{self.pk} - {self.loja} ({self.status})"

    def save(self, *args, **kwargs):
        # === AO CRIAR: preenche aberto_por se não estiver definido ===
        if not self.pk and not self.aberto_por:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            # Tenta pegar do usuário atual (se disponível)
            if hasattr(self, '_current_user') and self._current_user:
                self.aberto_por = self._current_user
            # Caso contrário, deixa null (pode ser preenchido na view)

        # === AO FINALIZAR: calcula duração ===
        if self.status == 'Finalizado' and self.fechado_em and self.aberto_em:
            # Garante mesmo timezone
            abertura = self.aberto_em
            fechamento = self.fechado_em
            if abertura.tzinfo and fechamento.tzinfo and abertura.tzinfo != fechamento.tzinfo:
                fechamento = fechamento.astimezone(abertura.tzinfo)

            # Prioridade: tempo_manual → cálculo automático
            if self.tempo_manual:
                self.duracao = self.tempo_manual
            elif not self.duracao:
                self.duracao = fechamento - abertura

        super().save(*args, **kwargs)

class InventarioExcel(models.Model):
    loja = models.CharField(max_length=100)
    regional = models.CharField(max_length=100)
    lider = models.CharField(max_length=100)
    data = models.DateField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chamados_inventarioexcel'  # usa a tabela existente no PostgreSQL

class ChatMessage(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    texto = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)
    enviado_por_admin = models.BooleanField(default=False)

    def __str__(self):
        tipo = "Admin" if self.enviado_por_admin else "Usuário"
        return f"[{tipo}] {self.usuario}: {self.texto[:30]}"