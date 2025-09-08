import React from "react";
import { marked } from "marked";
import hljs from "highlight.js";
import DOMPurify from "dompurify";
import "highlight.js/styles/github.css";

const renderer = new marked.Renderer();

renderer.code = function (codeToken, unusedLanguage) {
  const code = codeToken.text || "";
  const language = codeToken.lang || "";

  let highlightedValue;
  let langClass = "plaintext";

  try {
    if (language && hljs.getLanguage(language)) {
      const result = hljs.highlight(code, { language });
      highlightedValue = result.value;
      langClass = result.language;
    } else {
      const result = hljs.highlightAuto(code);
      highlightedValue = result.value;
      langClass = result.language || "plaintext";
    }
  } catch (e) {
    highlightedValue = code;
  }

  return `<pre><code class="hljs language-${langClass}">${highlightedValue}</code></pre>`;
};


marked.setOptions({ renderer, gfm: true, breaks: true });

export default function MarkdownRenderer({ markdownText }) {
  const rawHtml = marked(markdownText || "");
  const cleanHtml = DOMPurify.sanitize(rawHtml);
  console.log("RAW HTML: ", rawHtml);

  return (
    <div
      className="markdown-body"
      style={{ width: '100%' }}
      dangerouslySetInnerHTML={{ __html: cleanHtml }}
    />
  );
}
