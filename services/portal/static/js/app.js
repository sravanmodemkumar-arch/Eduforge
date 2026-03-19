/**
 * Portal – client-side JavaScript
 * Handles HTMX configuration and Alpine.js components.
 */

// ---------------------------------------------------------------------------
// HTMX: attach Django CSRF token to every request
// ---------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", function () {
    // Read the csrftoken cookie
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            var cookies = document.cookie.split(";");
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(
                        cookie.substring(name.length + 1)
                    );
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Attach CSRF token to every HTMX request
    document.body.addEventListener("htmx:configRequest", function (event) {
        var csrfToken = getCookie("csrftoken");
        if (csrfToken) {
            event.detail.headers["X-CSRFToken"] = csrfToken;
        }
    });

    // Show a subtle loading indicator on the target during requests
    document.body.addEventListener("htmx:beforeRequest", function (event) {
        var target = event.detail.target;
        if (target) {
            target.style.opacity = "0.6";
            target.style.transition = "opacity 0.15s";
        }
    });

    document.body.addEventListener("htmx:afterRequest", function (event) {
        var target = event.detail.target;
        if (target) {
            target.style.opacity = "1";
        }
    });

    // Log HTMX errors in development
    document.body.addEventListener("htmx:responseError", function (event) {
        console.error(
            "HTMX response error:",
            event.detail.xhr.status,
            event.detail.xhr.responseText.substring(0, 200)
        );
    });
});

// ---------------------------------------------------------------------------
// Alpine.js global store (optional, for cross-component state)
// ---------------------------------------------------------------------------
document.addEventListener("alpine:init", function () {
    Alpine.store("sidebar", {
        open: false,
        toggle: function () {
            this.open = !this.open;
        },
    });

    // Dropdown component
    Alpine.data("dropdown", function () {
        return {
            open: false,
            toggle: function () {
                this.open = !this.open;
            },
            close: function () {
                this.open = false;
            },
        };
    });
});
