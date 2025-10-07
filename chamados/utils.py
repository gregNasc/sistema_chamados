import pandas as pd
from django.core.files.storage import default_storage
from .models import InventarioExcel

def carregar_chamados_excel(data_filtro=None, sobrescrever=False):
    """
    Carrega dados do Excel (Loja, Regional, Líder, Data) e opcionalmente atualiza o banco.
    - data_filtro: datetime.date ou string 'YYYY-MM-DD' para filtrar apenas este dia.
    - sobrescrever: se True, sobrescreve os registros existentes no banco.
    """

    try:
        path = default_storage.path('uploads/chamados.xlsx')
        df = pd.read_excel(path, header=2)

        # Padroniza nomes das colunas
        df.columns = [str(c).strip().upper() for c in df.columns]

        # Renomeia coluna '#' para LOJA
        if '#' in df.columns:
            df.rename(columns={'#': 'LOJA'}, inplace=True)

        # Cria coluna DATA se não existir e houver coluna "4" (Data no Excel)
        if 'DATA' not in df.columns and '4' in df.columns:
            df['DATA'] = pd.to_datetime(df['4'], errors='coerce')

        # Seleciona apenas colunas essenciais
        cols = ['LOJA', 'REGIONAL', 'LÍDER']
        if 'DATA' in df.columns:
            cols.append('DATA')
        df = df[cols]

        # Remove linhas inválidas
        df = df.dropna(subset=['LOJA', 'REGIONAL', 'LÍDER'])
        df = df[(df['LOJA'] != '') & (df['REGIONAL'] != '') & (df['LÍDER'] != '')]

        # Converte DATA para tipo date, removendo NaT
        if 'DATA' in df.columns:
            df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
            df = df[~df['DATA'].isna()]
            df['DATA'] = df['DATA'].dt.date

        # Filtra por data, se fornecida
        if data_filtro and 'DATA' in df.columns:
            if isinstance(data_filtro, str):
                data_filtro = pd.to_datetime(data_filtro).date()
            df = df[df['DATA'] == data_filtro]

        # Limpa espaços em branco
        for col in ['LOJA', 'REGIONAL', 'LÍDER']:
            df[col] = df[col].astype(str).str.strip()

        # --- Atualiza o banco, se solicitado ---
        if sobrescrever and not df.empty:
            # Deleta registros existentes do mesmo período, se DATA existir
            if 'DATA' in df.columns:
                datas = df['DATA'].dropna().unique()
                InventarioExcel.objects.filter(data__in=datas).delete()
            else:
                InventarioExcel.objects.all().delete()

            # Cria novos registros
            objetos = [
                InventarioExcel(
                    loja=row['LOJA'],
                    regional=row['REGIONAL'],
                    lider=row['LÍDER'],
                    data=row['DATA'] if 'DATA' in row else None
                )
                for _, row in df.iterrows()
            ]
            InventarioExcel.objects.bulk_create(objetos)

        return df.reset_index(drop=True)

    except Exception as e:
        print("Erro ao carregar Excel:", e)
        return pd.DataFrame(columns=['LOJA', 'REGIONAL', 'LÍDER', 'DATA'])
