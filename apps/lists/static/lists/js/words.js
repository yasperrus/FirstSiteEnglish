document.addEventListener("DOMContentLoaded", () => {

    /* =====================================================
       ПЕРЕВОДЫ — СТРОГО В ПРЕДЕЛАХ ОДНОГО СЛОВА
    ===================================================== */

    document.querySelectorAll(".word-card").forEach(card => {

        const partSelect = card.querySelector(".part-select");
        const translationSelect = card.querySelector(".translation-select");
        const translationsBlocks = card.querySelectorAll(".translations-data");

        function updateTranslations(partId) {
            translationSelect.innerHTML = "";

            const block = Array.from(translationsBlocks)
                .find(b => b.dataset.partId === partId);

            if (!block) {
                const opt = document.createElement("option");
                opt.textContent = "Нет перевода";
                opt.disabled = true;
                opt.selected = true;
                translationSelect.appendChild(opt);
                return;
            }

            const spans = block.querySelectorAll("span");
            let mainFound = false;

            spans.forEach(span => {
                const opt = document.createElement("option");
                opt.textContent = span.textContent.trim();

                if (span.dataset.isMain === "1" && !mainFound) {
                    opt.selected = true;
                    mainFound = true;
                }

                translationSelect.appendChild(opt);
            });

            if (!mainFound && translationSelect.options.length > 0) {
                translationSelect.options[0].selected = true;
            }
        }

        // инициализация
        if (partSelect && partSelect.value) {
            updateTranslations(partSelect.value);
        }

        partSelect.addEventListener("change", () => {
            updateTranslations(partSelect.value);
        });
    });

    /* =====================================================
       ПОИСК + ФИЛЬТРЫ (КОМБИНИРУЕМЫЕ)
    ===================================================== */

    const searchInput = document.getElementById("word-search");
    const hideKnown = document.getElementById("filter-hide-known");
    const onlyKnown = document.getElementById("filter-only-known");
    const cards = document.querySelectorAll(".word-card");

    function applyFilters() {
        const query = searchInput.value.toLowerCase().trim();
        const hide = hideKnown.checked;
        const only = onlyKnown.checked;

        cards.forEach(card => {
            const word = card.dataset.word;
            const isKnown = card.dataset.known === "1";

            let visible = true;

            if (query && !word.includes(query)) {
                visible = false;
            }

            if (hide && isKnown) {
                visible = false;
            }

            if (only && !isKnown) {
                visible = false;
            }

            card.style.display = visible ? "" : "none";
        });
    }

    searchInput.addEventListener("input", applyFilters);
    hideKnown.addEventListener("change", applyFilters);
    onlyKnown.addEventListener("change", applyFilters);

    /* =====================================================
       СКАЧИВАНИЕ — BACKEND + TABULATE
    ===================================================== */

    const downloadBtn = document.getElementById("download-words");

    downloadBtn.addEventListener("click", () => {

        const ids = [];

        document.querySelectorAll(".word-card").forEach(card => {
            if (card.style.display === "none") return;
            const id = card.dataset.wordId;
            if (id) ids.push(id);
        });

        if (!ids.length) {
            alert("Нет слов для экспорта");
            return;
        }

        // LIST_ID должен быть объявлен в шаблоне
        const url = `/list/${LIST_ID}/download/?ids=${ids.join(",")}`;
        window.location.href = url;
    });

});
