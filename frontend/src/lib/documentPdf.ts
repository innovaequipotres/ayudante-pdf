import { jsPDF } from "jspdf";

const MAX_CHARACTERS_PER_LINE = 68;
const MAX_LINES_PER_PAGE = 42;
const PAGE_MARGIN_MM = 18;
const LINE_HEIGHT_MM = 6;

function wrapParagraph(paragraph: string): string[] {
  if (!paragraph) {
    return [""];
  }

  const lines: string[] = [];
  let currentLine = "";

  for (const word of paragraph.split(/\s+/)) {
    if (word.length > MAX_CHARACTERS_PER_LINE) {
      if (currentLine) {
        lines.push(currentLine);
        currentLine = "";
      }

      for (
        let offset = 0;
        offset < word.length;
        offset += MAX_CHARACTERS_PER_LINE
      ) {
        lines.push(word.slice(offset, offset + MAX_CHARACTERS_PER_LINE));
      }

      continue;
    }

    const nextLine = currentLine ? `${currentLine} ${word}` : word;

    if (nextLine.length > MAX_CHARACTERS_PER_LINE) {
      lines.push(currentLine);
      currentLine = word;
    } else {
      currentLine = nextLine;
    }
  }

  if (currentLine) {
    lines.push(currentLine);
  }

  return lines;
}

export function paginateDocumentText(content: string): string[] {
  const lines = content.split(/\r?\n/).flatMap(wrapParagraph);
  const pages: string[] = [];

  for (let offset = 0; offset < lines.length; offset += MAX_LINES_PER_PAGE) {
    pages.push(lines.slice(offset, offset + MAX_LINES_PER_PAGE).join("\n"));
  }

  return pages.length > 0 ? pages : [""];
}

export function downloadDocumentPdf(content: string, fileName: string): void {
  const pdf = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const pages = paginateDocumentText(content);

  pages.forEach((page, pageIndex) => {
    if (pageIndex > 0) {
      pdf.addPage("a4", "portrait");
    }

    pdf.setFont("helvetica", "normal");
    pdf.setFontSize(11);

    page.split("\n").forEach((line, lineIndex) => {
      pdf.text(
        line,
        PAGE_MARGIN_MM,
        PAGE_MARGIN_MM + lineIndex * LINE_HEIGHT_MM,
      );
    });
  });

  pdf.save(fileName);
}
