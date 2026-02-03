function getCookie(name) {
    let cookieValue = null;
    document.cookie.split(";").forEach(c => {
        c = c.trim();
        if (c.startsWith(name + "=")) {
            cookieValue = decodeURIComponent(c.substring(name.length + 1));
        }
    });
    return cookieValue;
}

document.addEventListener("DOMContentLoaded", () => {
    const csrftoken = getCookie("csrftoken");

    /* ===== Удаление списка ===== */
    document.querySelectorAll(".delete-list").forEach(btn => {
        btn.addEventListener("click", async function () {
            if (!confirm("Удалить список?")) return;

            const listId = this.dataset.listId;
            const col = this.closest(".col-md-6");

            try {
                const res = await fetch(`/lists/${listId}/delete/`, {
                    method: "POST",
                    headers: { "X-CSRFToken": csrftoken },
                });

                if (res.ok) {
                    col.style.transition = "0.3s";
                    col.style.opacity = "0";
                    col.style.transform = "scale(0.95)";
                    setTimeout(() => col.remove(), 300);
                } else {
                    alert("Ошибка при удалении");
                }
            } catch {
                alert("Ошибка сети");
            }
        });
    });

    /* ===== Публикация ===== */
    document.querySelectorAll(".publish-switch").forEach(sw => {
        sw.addEventListener("change", function () {
            const listId = this.dataset.listId;

            fetch(`/lists/${listId}/toggle-publish/`, {
                method: "POST",
                headers: { "X-CSRFToken": csrftoken },
            })
            .then(res => res.json())
            .then(data => {
                this.checked = data.is_public;
            })
            .catch(() => {
                this.checked = !this.checked;
            });
        });
    });

    /* ===== Лайки ===== */
    document.querySelectorAll(".like-btn").forEach(btn => {
        btn.addEventListener("click", function () {

            const url = this.dataset.url;
            const icon = this.querySelector("i");
            const countEl = this.parentElement.querySelector(".likes-count");

            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.liked) {
                    icon.classList.remove("bi-heart");
                    icon.classList.add("bi-heart-fill", "text-danger");
                } else {
                    icon.classList.remove("bi-heart-fill", "text-danger");
                    icon.classList.add("bi-heart");
                }

                countEl.textContent = data.likes_count;
            });
        });
    });


    /* ===== Анимация стрелки ===== */
    /* ===== СТРЕЛКА: → / ↓ ===== */
    document.querySelectorAll(".collapse").forEach(collapseEl => {
        collapseEl.addEventListener("show.bs.collapse", function () {
            const icon = document.querySelector(`[data-bs-target="#${this.id}"] i`);
            if (icon) {
                icon.classList.remove("bi-chevron-right");
                icon.classList.add("bi-chevron-down");
            }

            // POST на сервер
            const listId = this.id.replace('list-', '');
            fetch(`/lists/${listId}/toggle-menu/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({is_open_menu: true})
            });
        });

        collapseEl.addEventListener("hide.bs.collapse", function () {
            const icon = document.querySelector(`[data-bs-target="#${this.id}"] i`);
            if (icon) {
                icon.classList.remove("bi-chevron-down");
                icon.classList.add("bi-chevron-right");
            }

            // POST на сервер
            const listId = this.id.replace('list-', '');
            fetch(`/lists/${listId}/toggle-menu/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({is_open_menu: false})
            });
        });

    });

});
