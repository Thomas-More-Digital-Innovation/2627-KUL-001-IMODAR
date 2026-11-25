function cell(value: unknown): string {
  let text = value === null || value === undefined ? '' : String(value);
  // Spreadsheets execute text cells that start with these characters as formulas.
  if (typeof value === 'string' && /^[=+\-@\t\r]/.test(text)) text = `'${text}`;
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

/** Serialises rows as RFC 4180 CSV. */
export function toCsv(columns: string[], rows: unknown[][]): string {
  return [columns, ...rows].map((row) => row.map(cell).join(',')).join('\r\n');
}

export function downloadCsv(name: string, columns: string[], rows: unknown[][]): void {
  const url = URL.createObjectURL(new Blob([toCsv(columns, rows)], { type: 'text/csv' }));
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(url);
}
