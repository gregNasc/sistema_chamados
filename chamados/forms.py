from django import forms
from .models import Chamado, InventarioExcel
import pandas as pd

# ------------------------------
# Formulário de Login
# ------------------------------
class LoginForm(forms.Form):
    username = forms.CharField(label="Usuário", max_length=150)
    password = forms.CharField(label="Senha", widget=forms.PasswordInput)


# ------------------------------
# Formulário de Chamado
# ------------------------------

class ChamadoForm(forms.ModelForm):
    regional = forms.ChoiceField(label="Regional", choices=[], required=True)
    loja = forms.ChoiceField(label="Loja", choices=[], required=True)
    lider = forms.CharField(label="Líder", required=True)  # mudou para CharField
    motivo = forms.ChoiceField(label="Motivo do Suporte", choices=[])
    outro_motivo = forms.CharField(label="Outro Motivo", required=False)

    class Meta:
        model = Chamado
        fields = ['regional', 'loja', 'lider', 'motivo', 'outro_motivo']

    def __init__(self, *args, **kwargs):
        regionais = kwargs.pop('regionais', [])
        lojas = kwargs.pop('lojas', [])
        lideres = kwargs.pop('lideres', [])
        motivos_db = kwargs.pop('motivos_db', [])
        initial = kwargs.get('initial', {})
        super().__init__(*args, **kwargs)

        # Popula os ChoiceFields com opções do banco
        self.fields['regional'].choices = [('', 'Selecione uma Regional')] + [(r, r) for r in regionais]
        self.fields['loja'].choices = [('', 'Selecione uma Loja')] + [(l, l) for l in lojas]
        # Líder é CharField, então não precisa de choices
        # self.fields['lider'].choices = [(ld, ld) for ld in lideres]

        # Motivos fixos + motivos do banco, sem duplicar
        motivos_fixos = [
            ('', 'Selecione um Motivo'),
            ('FALHA NA IMPRESSÃO', 'FALHA NA IMPRESSÃO'),
            ('IMPRESSORA QUEIMADA', 'IMPRESSORA QUEIMADA'),
            ('ROUTER NÃO FUNCIONA', 'ROUTER NÃO FUNCIONA'),
            ('NOTEBOOK NÃO LIGA', 'NOTEBOOK NÃO LIGA'),
            ('COLETOR NÃO CONECTA NA REDE', 'COLETOR NÃO CONECTA NA REDE'),
            ('OUTRO', 'OUTRO')
        ]
        motivos_completos = motivos_fixos + [(m, m) for m in motivos_db if m not in dict(motivos_fixos)]
        self.fields['motivo'].choices = motivos_completos

        # Mantém valor atual do motivo selecionado ao atualizar página
        if 'motivo' not in initial and self.instance and self.instance.motivo:
            self.initial['motivo'] = self.instance.motivo

# ------------------------------
# Formulário de Upload de Excel
# ------------------------------
class UploadExcelForm(forms.Form):
    file = forms.FileField(
        label="Arquivo Excel",
        widget=forms.FileInput(attrs={'accept': '.xlsx,.xls'}),
        help_text="Apenas .xlsx ou .xls"
    )
