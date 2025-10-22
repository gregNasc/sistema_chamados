document.addEventListener('DOMContentLoaded', function () {
    console.log("✅ DOMContentLoaded disparou");

    // 🔹 Elementos principais
    const selectRegional = document.getElementById("id_regional");
    const selectLoja = document.getElementById("id_loja");
    const selectLider = document.getElementById("id_lider");
    const selectMotivo = document.getElementById("id_motivo");
    const divOutroMotivo = document.getElementById("div-outro-motivo");
    const textareaObservacao = document.getElementById("observacao");

    // 🔹 Recupera motivos dinâmicos do contexto (enviados pela view)
    const motivosDinamicos = window.motivosDinamicos || [];
    console.log("Motivos dinâmicos recebidos:", motivosDinamicos);

    // 🔹 Lista de motivos fixos (base)
    const motivosFixos = [
        "FALHA NA IMPRESSÃO",
        "IMPRESSORA QUEIMADA",
        "ROUTER NÃO FUNCIONA",
        "NOTEBOOK NÃO LIGA",
        "COLETOR NA CONECTA NA REDE",
        "OUTRO"
    ];

    // 🔹 Popula o select de Motivos (mesmo após redirect)
    if (selectMotivo) {
        // Evita duplicatas (mantém ordem: fixos primeiro)
        const todosMotivos = [...motivosFixos];
        motivosDinamicos.forEach(m => {
            if (m && !todosMotivos.includes(m)) todosMotivos.push(m);
        });

        // Limpa o select
        selectMotivo.innerHTML = '<option value="">Selecione um Motivo</option>';

        // Reinsere opções
        todosMotivos.forEach(motivo => {
            const opt = document.createElement('option');
            opt.value = motivo;
            opt.textContent = motivo;
            selectMotivo.appendChild(opt);
        });

        // Restaura o valor anterior (se houver)
        const valorSelecionado = selectMotivo.dataset.selected;
        if (valorSelecionado) {
            selectMotivo.value = valorSelecionado;
        }
    }

    // 🔹 Exibe campo "Outro Motivo" quando selecionado
    if (selectMotivo && divOutroMotivo) {
        const toggleOutroMotivo = () => {
            divOutroMotivo.style.display = selectMotivo.value === "OUTRO" ? "block" : "none";
        };
        toggleOutroMotivo();
        selectMotivo.addEventListener("change", toggleOutroMotivo);
    }

    // 🔹 Exibe/oculta observação
    if (textareaObservacao) {
        window.toggleObservacao = (select) => {
            textareaObservacao.style.display = select.value === "Sim" ? "block" : "none";
        };
    }

    // 🔹 Atualiza lojas e líderes via AJAX
    if (selectRegional && selectLoja && selectLider) {
        const atualizarLojasELideres = () => {
            const regional = selectRegional.value;
            const data = document.getElementById("data")?.value || "";

            // Lojas
            fetch(`/ajax/lojas/?data=${data}&regional=${encodeURIComponent(regional)}`)
                .then(res => res.json())
                .then(resp => {
                    selectLoja.innerHTML = '<option value="">Selecione uma Loja</option>';
                    resp.lojas.forEach(loja => {
                        const opt = document.createElement("option");
                        opt.value = loja;
                        opt.textContent = loja;
                        selectLoja.appendChild(opt);
                    });
                    selectLoja.dispatchEvent(new Event("change"));
                });

            // Limpa líderes
            selectLider.innerHTML = '<option value="">Selecione um Líder</option>';
        };

        selectRegional.addEventListener("change", atualizarLojasELideres);

        if (selectRegional.value) atualizarLojasELideres();
    }
});


