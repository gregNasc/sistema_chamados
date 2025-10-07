function toggleObservacao(select) {
    const textarea = document.getElementById('observacao');
    textarea.style.display = select.value === 'Sim' ? 'block' : 'none';
}

<script>
const dfExcel = {{ dados_excel|safe }}; // passar df Excel como JSON do view
const selectRegional = document.getElementById("id_regional");
const selectLoja = document.getElementById("id_loja");
const selectLider = document.getElementById("id_lider");

function preencherLojasELideres() {
    const regionalSelecionada = selectRegional.value;

    // Limpa opções
    selectLoja.innerHTML = '<option value="">Selecione uma Loja</option>';
    selectLider.innerHTML = '<option value="">Selecione um Líder</option>';

    dfExcel.forEach(row => {
        if (row.REGIONAL === regionalSelecionada) {
            if (!Array.from(selectLoja.options).some(o => o.value === row.LOJA)) {
                selectLoja.add(new Option(row.LOJA, row.LOJA));
            }
            if (!Array.from(selectLider.options).some(o => o.value === row.LIDER)) {
                selectLider.add(new Option(row.LIDER, row.LIDER));
            }
        }
    });
}

selectRegional.addEventListener('change', preencherLojasELideres);
</script>

