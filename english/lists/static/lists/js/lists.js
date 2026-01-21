// Получение CSRF токена из cookie
function getCookie(name) {
    let cookieValue = null;
    document.cookie.split(';').forEach(c => {
        c = c.trim();
        if (c.startsWith(name + '=')) {
            cookieValue = decodeURIComponent(c.substring(name.length + 1));
        }
    });
    return cookieValue;
}

document.addEventListener("DOMContentLoaded", () => {
    const csrftoken = getCookie("csrftoken");

    // Обработчик удаления
    document.querySelectorAll(".delete-list").forEach(btn => {
        btn.addEventListener("click", async function () {
            if (!confirm("Удалить список?")) return;

            const listId = this.dataset.listId;

            try {
                const res = await fetch(`/list/${listId}/delete/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrftoken,
                    },
                });

                if (res.ok) {
                    // Плавное исчезновение карточки
                    const col = this.closest(".col-md-6");
                    col.style.transition = "opacity 0.3s ease, transform 0.3s ease";
                    col.style.opacity = "0";
                    col.style.transform = "scale(0.95)";
                    setTimeout(() => col.remove(), 300);
                } else {
                    const text = await res.text();
                    console.error("Ошибка удаления:", text);
                    alert("Ошибка при удалении");
                }
            } catch(e) {
                console.error(e);
                alert("Ошибка при удалении");
            }
        });
    });
});
