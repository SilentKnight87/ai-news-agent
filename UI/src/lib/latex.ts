/**
 * Utilities to clean up LaTeX markup in article text for UI display.
 *
 * This focuses on:
 * - Removing inline/block math delimiters: $...$, $$...$$, \(...\), \[...\]
 * - Stripping common LaTeX commands like \cite{...}, \ref{...}, \mathbf{...}
 * - Collapsing multiple spaces
 */

const INLINE_DOLLAR = /\$(?:\\.|[^$\\])+\$/g;            // $...$
const BLOCK_DOLLAR = /\$\$(?:\\.|[^$\\])+\$\$/g;         // $$...$$
const INLINE_PAREN = /\\\((?:\\.|[^\\)])+\\\)/g;         // \(...\)
const BLOCK_BRACKET = /\\\[(?:\\.|[^\\\]])+\\\]/g;       // \[...\]
const SIMPLE_CMD = /\\[a-zA-Z]+(\{[^{}]*\})?/g;          // \cmd or \cmd{...}
const CURLY_GROUPS = /\{([^{}]*)\}/g;                    // {content} -> content
const MULTI_SPACE = /\s{2,}/g;

export function stripLatex(raw?: string): string {
  if (!raw) return '';
  let s = raw;

  // Remove math blocks first
  s = s.replace(BLOCK_DOLLAR, ' ')
       .replace(INLINE_DOLLAR, ' ')
       .replace(BLOCK_BRACKET, ' ')
       .replace(INLINE_PAREN, ' ');

  // Remove simple commands
  s = s.replace(SIMPLE_CMD, (_m) => ' ');

  // Unwrap single-level curly text like {\em text} -> {text} -> text
  s = s.replace(CURLY_GROUPS, (_m, g1) => ` ${g1} `);

  // Normalize whitespace
  s = s.replace(MULTI_SPACE, ' ').trim();
  return s;
}

/**
 * Convenience that truncates after cleaning.
 */
export function cleanAndTruncate(raw?: string, max = 160): string {
  const cleaned = stripLatex(raw);
  if (cleaned.length <= max) return cleaned;
  return cleaned.slice(0, max).trimEnd() + '…';
}