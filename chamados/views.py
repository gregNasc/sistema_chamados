import matplotlib
matplotlib.use("Agg")  # backend sem GUI

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.views.decorators.cache import never_cache
from .utils import carregar_chamados_excel
from .forms import LoginForm, ChamadoForm, UploadExcelForm
from .models import Chamado, CustomUser, InventarioExcel
from django.contrib.admin.views.decorators import staff_member_required
from .models import ChatMessage, CustomUser
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import os
import matplotlib.ticker as mticker
from datetime import datetime
import pandas as pd
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import ChamadoForm
# ------------------------------
# Funções auxiliares
# ------------------------------

def is_admin(user):
    return user.is_authenticated and getattr(user, "papel", "") == "admin"

def imagem_para_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

# ------------------------------
# Autenticação
# ------------------------------

def login_view(request):
    if request.user.is_authenticated:
        return redirect('chamados:dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )
        if user:
            login(request, user)
            messages.success(request, f"Bem-vindo(a), {user.username}!")
            return redirect('chamados:dashboard')
        messages.error(request, "Usuário ou senha incorretos")

    return render(request, 'chamados/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('chamados:login')

# ------------------------------
# Chamados
# ------------------------------

@login_required
@login_required
def sistema_chamados_view(request):
    # ------------------------------
    # Filtro por data
    # ------------------------------
    data_str = request.GET.get('data', '')
    data_filtro = None
    if data_str:
        try:
            data_filtro = datetime.strptime(data_str, "%Y-%m-%d").date()
        except ValueError:
            messages.warning(request, "Data inválida. Mostrando todos os registros.")

    # ------------------------------
    # Regional, Loja e Líder selecionados
    # ------------------------------
    regional_selecionada = request.GET.get('regional', '')
    loja_selecionada = request.GET.get('loja', '')
    lider_selecionado = request.GET.get('lider', '')

    # ------------------------------
    # Carrega dados do InventarioExcel
    # ------------------------------
    inventario_qs = InventarioExcel.objects.all().order_by('regional', 'loja')
    if data_filtro:
        inventario_qs = inventario_qs.filter(data=data_filtro)

    df_excel = pd.DataFrame(list(inventario_qs.values('regional', 'loja', 'lider')))
    if not df_excel.empty:
        df_excel[['regional', 'loja', 'lider']] = df_excel[['regional', 'loja', 'lider']].astype(str).apply(lambda x: x.str.strip())

    # ------------------------------
    # Listas únicas para filtros
    # ------------------------------
    regionais = sorted(df_excel['regional'].dropna().unique()) if not df_excel.empty else []

    if regional_selecionada and not df_excel.empty:
        lojas_filtradas = sorted(df_excel[df_excel['regional'] == regional_selecionada]['loja'].dropna().unique())
        if loja_selecionada:
            lideres_filtrados = sorted(df_excel[df_excel['loja'] == loja_selecionada]['lider'].dropna().unique())
        else:
            lideres_filtrados = sorted(df_excel[df_excel['regional'] == regional_selecionada]['lider'].dropna().unique())
    else:
        lojas_filtradas = sorted(df_excel['loja'].dropna().unique()) if not df_excel.empty else []
        lideres_filtrados = sorted(df_excel['lider'].dropna().unique()) if not df_excel.empty else []

    # ------------------------------
    # Busca chamados reais do banco
    # ------------------------------
    chamados_qs = Chamado.objects.all().order_by('-data')
    if data_filtro:
        chamados_qs = chamados_qs.filter(data=data_filtro)
    if regional_selecionada:
        chamados_qs = chamados_qs.filter(regional=regional_selecionada)
    if loja_selecionada:
        chamados_qs = chamados_qs.filter(loja=loja_selecionada)

    chamados_df = pd.DataFrame(list(chamados_qs.values()))

    # ------------------------------
    # Lista de motivos do banco
    # ------------------------------
    motivos_db = list(
        chamados_qs.exclude(motivo__isnull=True).exclude(motivo='').values_list('motivo', flat=True).distinct()
    )

    # ------------------------------
    # Formulário Chamado
    # ------------------------------
    motivo_atual = request.POST.get('motivo') if request.method == 'POST' else None
    form = ChamadoForm(
        request.POST or None,
        regionais=regionais,
        lojas=lojas_filtradas,
        lideres=lideres_filtrados,
        motivos_db=motivos_db,
        initial={
            'motivo': motivo_atual,  # garante que motivo não desapareça
            'lider': lider_selecionado  # mantém o líder selecionado
        }
    )

    # ------------------------------
    # Salva chamado se POST válido
    # ------------------------------
    if request.method == 'POST' and form.is_valid():
        chamado = form.save(commit=False)
        chamado.usuario = request.user
        if chamado.motivo == 'OUTRO' and form.cleaned_data.get('outro_motivo'):
            chamado.outro_motivo = form.cleaned_data['outro_motivo'].upper()
            chamado.motivo = 'OUTRO'
        else:
            chamado.outro_motivo = ''
        if form.cleaned_data.get('lider'):
            chamado.lider = form.cleaned_data['lider'].upper()
        chamado.save()
        messages.success(request, "✅ Chamado cadastrado!")

        # Preserva filtros e líder no redirect
        return redirect(
            f"{request.path}?data={data_str}&regional={regional_selecionada}&loja={loja_selecionada}&lider={form.cleaned_data.get('lider', '')}"
        )

    # ------------------------------
    # Renderiza template
    # ------------------------------
    return render(request, 'chamados/sistema_chamados.html', {
        'form': form,
        'dados_excel': df_excel.to_dict('records'),
        'data_selecionada': data_str,
        'regionais': regionais,
        'lojas': lojas_filtradas,
        'lideres': lideres_filtrados,
        'regional_selecionada': regional_selecionada,
        'loja_selecionada': loja_selecionada,
        'chamados': chamados_df.to_dict('records') if not chamados_df.empty else [],
    })

@login_required
def chamados_ativos(request):
    data_str = request.GET.get('data')
    data_filtro = None
    if data_str:
        try:
            data_filtro = datetime.strptime(data_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    # --- Carrega inventário para os filtros dinâmicos ---
    inventario_qs = InventarioExcel.objects.all()
    if data_filtro:
        inventario_qs = inventario_qs.filter(data=data_filtro)

    regionais = sorted(inventario_qs.values_list('regional', flat=True).distinct())
    lideres = sorted(inventario_qs.values_list('lider', flat=True).distinct())
    lojas = sorted(inventario_qs.values_list('loja', flat=True).distinct())

    motivos_db = Chamado.objects.values_list('motivo', flat=True).distinct()

    # --- Cadastro de novo chamado ---
    if request.method == "POST":
        form = ChamadoForm(
            request.POST,
            regionais=regionais,
            lojas=lojas,
            lideres=lideres,
            motivos_db=motivos_db
        )

        if form.is_valid():
            chamado = form.save(commit=False)
            chamado.status = 'Aberto'
            chamado.abertura = timezone.now()
            chamado.usuario = request.user
            chamado.save()

            messages.success(request, "Chamado cadastrado com sucesso!")
            return redirect('chamados:chamados_ativos')
        else:
            print("ERROS DO FORM:", form.errors)
            messages.warning(request, "Erro ao cadastrar chamado. Verifique os campos.")

    # --- Lista de chamados abertos ---
    chamados = Chamado.objects.filter(status='Aberto')
    if data_filtro:
        chamados = chamados.filter(abertura__date=data_filtro)

    chamados = chamados.order_by('-abertura')

    return render(request, 'chamados/sistema_chamados.html', {
        'chamados': chamados,
        'regionais': regionais,
        'lideres': lideres,
        'data_selecionada': data_str or '',
    })
@login_required
def finalizar_chamado_view(request, pk):
    chamado = get_object_or_404(Chamado, pk=pk)

    if request.method == 'POST' and chamado.status != 'Finalizado':
        chamado.status = 'Finalizado'
        chamado.fechamento = timezone.now()
        chamado.observacao = request.POST.get('observacao', '')
        if chamado.abertura:
            chamado.duracao = chamado.fechamento - chamado.abertura
        else:
            chamado.duracao = None
        chamado.save()
        messages.success(request, f"✅ Chamado {pk} finalizado!")

    # Recupera filtros da query string para manter na tela
    data = request.GET.get('data', '')
    regional = request.GET.get('regional', '')
    loja = request.GET.get('loja', '')

    # Redireciona para a view principal mantendo os filtros
    redirect_url = f"{reverse('chamados:sistema_chamados')}?data={data}&regional={regional}&loja={loja}"
    return redirect(redirect_url)

@login_required
def todos_chamados(request):
    chamados = Chamado.objects.all().order_by('-abertura')
    return render(request, 'todos_chamados.html', {'chamados': chamados})

# ------------------------------
# AJAX para filtros
# ------------------------------
@login_required
def regionais_por_data(request):
    """Retorna regionais disponíveis para a data (InventarioExcel)"""
    data_str = request.GET.get('data')
    inventario_qs = InventarioExcel.objects.all()

    if data_str:
        try:
            data_filtro = datetime.strptime(data_str, "%Y-%m-%d").date()
            inventario_qs = inventario_qs.filter(data=data_filtro)
        except ValueError:
            pass

    regionais = sorted(inventario_qs.values_list('regional', flat=True).distinct())
    return JsonResponse({'regionais': regionais})


def lojas_por_regional(request):
    """Retorna lojas de uma regional específica (InventarioExcel)"""
    regional = request.GET.get('regional')
    data_str = request.GET.get('data')
    inventario_qs = InventarioExcel.objects.all()

    if data_str:
        try:
            data_filtro = datetime.strptime(data_str, "%Y-%m-%d").date()
            inventario_qs = inventario_qs.filter(data=data_filtro)
        except ValueError:
            pass

    if regional:
        inventario_qs = inventario_qs.filter(regional=regional)

    lojas = sorted(inventario_qs.values_list('loja', flat=True).distinct())
    return JsonResponse({'lojas': lojas})


def lider_por_loja(request):
    """Retorna o líder da loja selecionada (InventarioExcel)"""
    data_str = request.GET.get('data')
    loja = request.GET.get('loja')
    inventario_qs = InventarioExcel.objects.all()

    if data_str:
        try:
            data_filtro = datetime.strptime(data_str, "%Y-%m-%d").date()
            inventario_qs = inventario_qs.filter(data=data_filtro)
        except ValueError:
            pass

    if loja:
        inventario_qs = inventario_qs.filter(loja=loja)

    lider_nome = inventario_qs.values_list('lider', flat=True).first() or ''
    return JsonResponse({'lider': lider_nome})


# ------------------------------
# Dashboard
# ------------------------------

def gerar_grafico_pie(df, coluna, titulo):
    if coluna in df and not df[coluna].empty:
        df_count = df[coluna].value_counts()
        top = df_count.head(5)
        outros = df_count.iloc[5:].sum()
        if outros > 0:
            top["Outros"] = outros
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.pie(
            top.values,
            labels=top.index,
            autopct=lambda p: f'{p:.1f}%' if p > 3 else '',
            startangle=90,
            colors=sns.color_palette("Set2", len(top)),
            wedgeprops={"edgecolor": "white"}
        )
        ax.set_title(titulo, fontsize=13, weight="bold")
        return imagem_para_base64(fig)
    return None

def gerar_grafico_bar(df, coluna, titulo):
    if coluna in df and not df[coluna].empty:
        df_count = df[coluna].value_counts().head(10).sort_values()
        fig, ax = plt.subplots(figsize=(7, 4))
        bars = ax.barh(df_count.index, df_count.values, color=sns.color_palette("Set2", len(df_count)))
        ax.set_xlabel("Quantidade")
        ax.set_title(titulo, fontsize=13, weight="bold")

        ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

        for bar in bars:
            width = bar.get_width()
            ax.text(width + 0, bar.get_y() + bar.get_height()/2, str(int(width)), va='center')
        plt.tight_layout()
        return imagem_para_base64(fig)
    return None

def gerar_grafico_tempo_medio(df, titulo="Tempo Médio de Suporte"):
    if 'abertura' not in df.columns or 'fechamento' not in df.columns or 'motivo' not in df.columns:
        return None

    df_finalizados = df.dropna(subset=['abertura', 'fechamento', 'motivo']).copy()
    if df_finalizados.empty:
        return None

    df_finalizados['abertura'] = pd.to_datetime(df_finalizados['abertura'])
    df_finalizados['fechamento'] = pd.to_datetime(df_finalizados['fechamento'])

    # 🔹 Calcula tempo em minutos
    df_finalizados['tempo_minutos'] = (df_finalizados['fechamento'] - df_finalizados['abertura']).dt.total_seconds() / 60

    df_medio = df_finalizados.groupby('motivo')['tempo_minutos'].mean().sort_values()
    if df_medio.empty:
        return None

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.barh(df_medio.index, df_medio.values, color=sns.color_palette("Set2", len(df_medio)))
    ax.set_xlabel("Minutos")
    ax.set_title(titulo, fontsize=13, weight="bold")

    for bar, val in zip(bars, df_medio.values):
        ax.text(val + 1, bar.get_y() + bar.get_height()/2, f"{val:.0f} min", va='center', fontweight='bold')

    plt.tight_layout()
    return imagem_para_base64(fig)
@login_required
def dashboard_view(request):
    #  Pega filtros do GET
    filtros = {col: request.GET.getlist(col) for col in ['regional', 'status', 'motivo', 'lider']}
    qs = Chamado.objects.all()

    #  Aplica filtros dinâmicos
    if filtros['regional']:
        qs = qs.filter(regional__in=filtros['regional'])
    if filtros['status']:
        qs = qs.filter(status__in=filtros['status'])
    if filtros['motivo']:
        qs = qs.filter(motivo__in=filtros['motivo'])
    if filtros['lider']:
        qs = qs.filter(lider__in=filtros['lider'])

    #  Converte queryset em DataFrame
    df = pd.DataFrame(list(qs.values()))

    #  Converte colunas datetime para string, evitando NaT
    for col in df.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

        try:
            df[col] = df[col].dt.tz_localize(None)
        except TypeError:
            notna_mask = df[col].notna()
            df.loc[notna_mask, col] = df.loc[notna_mask, col].dt.tz_convert(None)

    #  Filtros disponíveis (somente valores únicos e não nulos)
    filtros_disponiveis = {col: df[col].dropna().unique().tolist() for col in ['regional','status','motivo','lider']} if not df.empty else {}

    plots = {}
    template = 'chamados/dashboard_usuario.html'

    #  Admin tem todos os gráficos
    if not df.empty:
        df_grafico = df.copy()  # para usar nos gráficos

        df_grafico['motivo_grafico'] = df_grafico.apply(
            lambda row: row['outro_motivo'] if row['motivo'] == 'OUTRO' and row['outro_motivo'] else row['motivo'],
            axis=1
        )

        plots['status'] = gerar_grafico_pie(df_grafico, 'status', 'Status dos Chamados')
        plots['lideres'] = gerar_grafico_bar(df_grafico, 'lider', 'Principais Líderes')
        plots['motivos'] = gerar_grafico_bar(df_grafico, 'motivo_grafico', 'Principais Motivos')
        plots['regionais'] = gerar_grafico_bar(df_grafico, 'regional', 'Chamados por Regional')

        if getattr(request.user, 'papel', '') == 'admin':
            plots['tempo_medio'] = gerar_grafico_tempo_medio(df_grafico)
            template = 'chamados/dashboard_admin.html'

    return render(request, template, {
        'plots': plots,
        'filters': filtros_disponiveis,
        'filters_selected': filtros,
        'chamados': df.to_dict('records') if not df.empty else []
    })

# ------------------------------
# Upload e Export Excel
# ------------------------------

@login_required
@user_passes_test(is_admin)
def upload_excel(request):
    if request.method == "POST":
        form = UploadExcelForm(request.POST, request.FILES)
        if form.is_valid():
            arquivo = form.cleaned_data['arquivo']
            upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, "chamados.xlsx")
            with open(file_path, "wb+") as destino:
                for chunk in arquivo.chunks():
                    destino.write(chunk)

            # Lê Excel
            df = pd.read_excel(file_path, header=2)
            df.columns = [str(c).strip().upper() for c in df.columns]
            if '#' in df.columns:
                df.rename(columns={'#': 'LOJA'}, inplace=True)
            if '4' in df.columns:
                df['DATA'] = pd.to_datetime(df['4'], errors='coerce').dt.date

            required_cols = ['LOJA', 'REGIONAL', 'LÍDER']
            for col in required_cols:
                if col not in df.columns:
                    messages.error(request, f"Coluna '{col}' não encontrada no Excel")
                    return redirect("chamados:upload_excel")
            df = df[required_cols + (['DATA'] if 'DATA' in df.columns else [])].fillna('')

            # Limpa apenas os registros antigos de InventarioExcel
            InventarioExcel.objects.all().delete()

            # Salva no InventarioExcel (Excel como base, não chamados reais)
            for _, row in df.iterrows():
                data_valor = row.get('DATA')

                # Trata células vazias ou inválidas
                if pd.isna(data_valor) or str(data_valor).strip() == "":
                    data_valor = None
                else:
                    try:
                        data_valor = pd.to_datetime(data_valor).date()
                    except Exception:
                        data_valor = None  # se a data não for válida, ignora

                InventarioExcel.objects.create(
                    loja=str(row.get('LOJA', '')).strip(),
                    regional=str(row.get('REGIONAL', '')).strip(),
                    lider=str(row.get('LÍDER', '')).strip(),
                    data=data_valor,
                )

            messages.success(request, f"✅ {len(df)} registros de inventário importados com sucesso!")
            return redirect("chamados:upload_excel")
    else:
        form = UploadExcelForm()
    return render(request, "upload_excel.html", {"form": form})

@login_required
def exportar_excel_view(request):
    chamados = Chamado.objects.all().values()
    df = pd.DataFrame(chamados)

    # Converter datetimes
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            if df[col].dt.tz is not None:
                df[col] = df[col].dt.tz_localize(None)
            df[col] = df[col].dt.strftime('%d/%m/%Y %H:%M:%S')

    # Formatar duração para "Xh Ymin"
    if 'duracao' in df.columns:
        def format_duracao_excel(value):
            if pd.isnull(value):
                return ""
            total_seconds = int(value.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}min"

        df['duracao'] = df['duracao'].apply(format_duracao_excel)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=Lista de Chamados.xlsx'
    df.to_excel(response, index=False)
    return response

@login_required
@user_passes_test(is_admin)
def zerar_banco_view(request):
    if request.method == 'POST':
        # ⚠️ Apenas apaga os chamados reais, sem tocar no InventarioExcel ou usuários
        Chamado.objects.all().delete()
        messages.success(request, "✅ Todos os chamados foram zerados com sucesso!")
        return redirect('chamados:dashboard')  # Nome da sua view de dashboard atualizado
    return render(request, 'chamados/confirm_zerar.html')

@staff_member_required
def chat_admin_view(request):
    # Pega todos os usuários que já enviaram mensagens
    usuarios = CustomUser.objects.filter(chatmessage__isnull=False).distinct()
    return render(request, 'chamados/chat_admin.html', {
        'usuarios': usuarios,
    })

from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command

@staff_member_required  # garante que só admin consegue acessar
def run_migrations(request):
    try:
        call_command("migrate", interactive=False)
        return HttpResponse("✅ Migrations executadas com sucesso!")
    except Exception as e:
        return HttpResponse(f"❌ Erro ao executar migrations: {e}")