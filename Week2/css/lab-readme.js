/**
 * Lab HTML link routing:
 * - *.html / *.htm  → new browser / preview tab (stay on the web surface)
 * - everything else → vscode://file/... so Cursor/VS Code opens the native editor
 *   (.py, .ipynb, .md, .json, …)
 */
(function () {
  function normalizeWinPath(path) {
    var p = String(path || "");
    if (/^\/[A-Za-z]:\//.test(p)) p = p.slice(1);
    return p.replace(/\\/g, "/");
  }

  function pathFromUrl(url) {
    var path = decodeURIComponent(url.pathname || "");

    if (url.protocol === "file:") {
      return normalizeWinPath(path);
    }

    if (url.protocol === "vscode-file:") {
      path = path.replace(/^\/vscode-app\//i, "/");
      return normalizeWinPath(path);
    }

    if (
      /vscode-resource/i.test(url.hostname || "") ||
      /vscode-cdn\.net/i.test(url.hostname || "") ||
      /\.vscode-webview-resource\./i.test(url.hostname || "")
    ) {
      if (path.charAt(0) === "/") path = path.slice(1);
      return normalizeWinPath(path);
    }

    return null;
  }

  function week2RootFromScript() {
    var scripts = document.getElementsByTagName("script");
    for (var i = scripts.length - 1; i >= 0; i--) {
      var src = scripts[i].src || "";
      if (!src || !/lab-readme\.js(\?|$)/i.test(src)) continue;
      try {
        var sUrl = new URL(src, document.baseURI);
        var cssPath = pathFromUrl(sUrl);
        if (cssPath && /\/css\/lab-readme\.js$/i.test(cssPath)) {
          return cssPath.replace(/\/css\/lab-readme\.js$/i, "");
        }
      } catch (e) { /* continue */ }
    }
    return null;
  }

  function toEditorUri(absPath) {
    return "vscode://file/" + normalizeWinPath(absPath);
  }

  function isHtmlHref(href, resolvedUrl) {
    var path = "";
    try {
      path = (resolvedUrl && resolvedUrl.pathname) || href.split(/[?#]/)[0];
    } catch (e) {
      path = href.split(/[?#]/)[0];
    }
    return /\.html?$/i.test(path);
  }

  function resolveEditorUri(href) {
    var abs = new URL(href, document.baseURI);
    var pagePath = pathFromUrl(abs);
    if (pagePath) {
      return toEditorUri(pagePath);
    }

    if (abs.protocol === "http:" || abs.protocol === "https:") {
      var parts = abs.pathname.split("/").filter(Boolean);
      var lower = parts.map(function (p) { return p.toLowerCase(); });
      var idx = lower.lastIndexOf("week2");
      var root = week2RootFromScript();
      if (idx >= 0 && root) {
        return toEditorUri(root + "/" + parts.slice(idx + 1).join("/"));
      }
    }
    return null;
  }

  document.addEventListener(
    "click",
    function (e) {
      var a = e.target.closest("a[href]");
      if (!a) return;
      var href = a.getAttribute("href");
      if (!href || href.charAt(0) === "#") return;

      // Leave true external sites alone
      if (/^https?:\/\//i.test(href) && !/^https?:\/\/(127\.0\.0\.1|localhost)/i.test(href)) {
        if (!/vscode-resource|vscode-cdn\.net|vscode-webview/i.test(href)) return;
      }
      if (/^(mailto:|vscode:|cursor:)/i.test(href)) return;

      var resolved;
      try {
        resolved = new URL(href, document.baseURI);
      } catch (err) {
        return;
      }

      // HTML pages: new browser / preview tab
      if (isHtmlHref(href, resolved)) {
        e.preventDefault();
        e.stopPropagation();
        window.open(resolved.href, "_blank", "noopener,noreferrer");
        return;
      }

      // Code, notebooks, data, markdown, etc.: open in Cursor/VS Code editor
      var editorUri = null;
      try {
        editorUri = resolveEditorUri(href);
      } catch (err) {
        return;
      }
      if (!editorUri) return;

      e.preventDefault();
      e.stopPropagation();
      window.location.href = editorUri;
    },
    true
  );

  document.addEventListener("DOMContentLoaded", function () {
    var header = document.querySelector(".page-header");
    if (!header || header.querySelector(".hint")) return;
    var hint = document.createElement("p");
    hint.className = "hint";
    hint.innerHTML =
      "<strong>HTML</strong> links open in a new browser/preview tab. " +
      "Other files (<code>.py</code>, <code>.ipynb</code>, <code>.md</code>, data, …) open in the Cursor editor. " +
      "If editor links do nothing in the built-in preview, right-click this HTML → <strong>Open in Browser</strong>.";
    header.appendChild(hint);
  });
})();
