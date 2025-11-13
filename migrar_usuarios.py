import os
import django
from django.utils import timezone
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_chamados.settings')
django.setup()

from chamados.models import Chamado

User = get_user_model()

def migrar():
    atualizados_aberto = 0
    atualizados_fechado = 0
    nao_encontrados = 0
    sem_usuario = 0

    chamados = Chamado.objects.filter(
        aberto_por__isnull=True
    ).exclude(usuario__exact='')

    print(f"Processando {chamados.count()} chamados com campo 'usuario' legado...\n")

    for chamado in chamados:
        nome_original = (chamado.usuario or "").strip()
        if not nome_original:
            sem_usuario += 1
            continue

        user = None
        motivo = ""

        # 1️⃣ username exato (case-insensitive)
        try:
            user = User.objects.get(username__iexact=nome_original)
            motivo = "username"
        except User.DoesNotExist:
            pass

        # 2️⃣ nome completo
        if not user and " " in nome_original:
            partes = nome_original.split()
            primeiro = partes[0]
            ultimo = " ".join(partes[1:])
            try:
                user = User.objects.get(first_name__iexact=primeiro, last_name__iexact=ultimo)
                motivo = "nome completo"
            except User.DoesNotExist:
                pass

        # 3️⃣ primeiro nome
        if not user:
            try:
                user = User.objects.get(first_name__iexact=nome_original)
                motivo = "primeiro nome"
            except User.DoesNotExist:
                pass

        # 4️⃣ email
        if not user:
            try:
                user = User.objects.get(email__iexact=nome_original)
                motivo = "email"
            except User.DoesNotExist:
                pass

        if user:
            if not chamado.aberto_por:
                chamado.aberto_por = user
                atualizados_aberto += 1

            # Se o chamado está finalizado e não tem fechado_por, aproveita o mesmo usuário
            if chamado.status == "Finalizado" and not chamado.fechado_por:
                chamado.fechado_por = user
                atualizados_fechado += 1

            chamado.save(update_fields=["aberto_por", "fechado_por"])
            print(f"✅ '{nome_original}' → {user.get_full_name() or user.username} ({motivo}) | #{chamado.id}")
        else:
            nao_encontrados += 1
            print(f"⚠️ NÃO ENCONTRADO: '{nome_original}' | #{chamado.id} | Loja: {chamado.loja}")

    print("\n" + "="*60)
    print("📊 RESUMO DA MIGRAÇÃO")
    print("="*60)
    print(f"Abertos atualizados:   {atualizados_aberto}")
    print(f"Fechados atualizados:  {atualizados_fechado}")
    print(f"Não encontrados:       {nao_encontrados}")
    print(f"Sem nome no legado:    {sem_usuario}")
    print(f"Total processados:     {chamados.count()}")

if __name__ == "__main__":
    migrar()
