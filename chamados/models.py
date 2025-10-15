from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings


class CustomUser(AbstractUser):
    PAPEL_CHOICES = (
        ('admin', 'Administrador'),
        ('usuario', 'Usuário'),
    )
    papel = models.CharField(max_length=10, choices=PAPEL_CHOICES, default='usuario')

    def __str__(self):
        return self.username


class Chamado(models.Model):
    STATUS_CHOICES = (
        ('Aberto', 'Aberto'),
        ('Finalizado', 'Finalizado'),
    )

    usuario = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    regional = models.CharField(max_length=100)
    loja = models.CharField(max_length=100)
    lider = models.CharField(max_length=100)
    motivo = models.CharField(max_length=200)
    outro_motivo = models.CharField(max_length=200, null=True, blank=True)
    abertura = models.DateTimeField(default=timezone.now)
    fechamento = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Aberto')
    observacao = models.TextField(null=True, blank=True)
    duracao = models.DurationField(null=True, blank=True)  # melhor que CharField
    data = models.DateField(blank=True, null=True)

    def save(self, *args, **kwargs):
        """
        Calcula a duração automaticamente quando o chamado é finalizado.
        Garante que abertura e fechamento tenham o mesmo timezone.
        """
        if self.status == 'Finalizado' and self.fechamento and self.abertura:
            abertura = self.abertura
            fechamento = self.fechamento

            # Se forem timezone-aware diferentes, converte fechamento para o timezone de abertura
            if abertura.tzinfo and fechamento.tzinfo and abertura.tzinfo != fechamento.tzinfo:
                fechamento = fechamento.astimezone(abertura.tzinfo)

            self.duracao = fechamento - abertura

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Chamado {self.id} - {self.motivo} ({self.status})"


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