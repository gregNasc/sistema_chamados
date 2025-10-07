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
    lider = forms.ChoiceField(label="Líder", choices=[], required=True)
    motivo = forms.ChoiceField(label="Motivo do Suporte", choices=[])
    outro_motivo = forms.CharField(label="Outro Motivo", required=False)

    class Meta:
        model = Chamado
        fields = ['regional', 'loja', 'lider', 'motivo']

    def __init__(self, *args, **kwargs):
        regionais = kwargs.pop('regionais', [])
        lojas = kwargs.pop('lojas', [])
        lideres = kwargs.pop('lideres', [])
        super().__init__(*args, **kwargs)

        # Popula os ChoiceFields
        self.fields['regional'].choices = [('', 'Selecione uma Regional')] + [(r, r) for r in regionais]
        self.fields['loja'].choices = [('', 'Selecione uma Loja')] + [(l, l) for l in lojas]
        self.fields['lider'].choices = [('', 'Selecione um Líder')] + [(ld, ld) for ld in lideres]

        # Motivos fixos + banco
        motivos_fixos = [
            ('', 'Selecione um Motivo'),
            ('FALHA NA IMPRESSÃO', 'FALHA NA IMPRESSÃO'),
            ('IMPRESSORA QUEIMADA', 'IMPRESSORA QUEIMADA'),
            ('ROUTER NÃO FUNCIONA', 'ROUTER NÃO FUNCIONA'),
            ('NOTEBOOK NÃO LIGA', 'NOTEBOOK NÃO LIGA'),
            ('COLETOR NA CONECTA NA REDE', 'COLETOR NA CONECTA NA REDE'),
            ('OUTRO', 'OUTRO')
        ]
        motivos_db = [(m['motivo'], m['motivo']) for m in Chamado.objects.values('motivo').distinct() if m['motivo']]
        self.fields['motivo'].choices = list(dict.fromkeys(motivos_fixos + motivos_db))

    def clean(self):
        cleaned_data = super().clean()
        motivo = cleaned_data.get('motivo')
        outro_motivo = cleaned_data.get('outro_motivo')

        if motivo == 'OUTRO':
            if not outro_motivo or not outro_motivo.strip():
                raise forms.ValidationError("Digite um motivo personalizado.")
            cleaned_data['motivo'] = outro_motivo.upper().strip()

        return cleaned_data

# ------------------------------
# Formulário de Upload de Excel
# ------------------------------
class UploadExcelForm(forms.Form):
    arquivo = forms.FileField(label="Selecione o arquivo Excel")

    def clean_arquivo(self):
        arquivo = self.cleaned_data['arquivo']

        # Verifica extensão
        if not arquivo.name.endswith('.xlsx'):
            raise forms.ValidationError("Apenas arquivos .xlsx são permitidos.")

        # Verifica tamanho (máx. 5MB)
        max_size = 5 * 1024 * 1024
        if arquivo.size > max_size:
            raise forms.ValidationError("O arquivo é muito grande (máx. 5 MB).")

        return arquivo
