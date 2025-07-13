/**
 * Utility functions for formatting GPT text messages
 */

/**
 * Format message content with complete markdown support for:
 * - Tables: | col1 | col2 | → HTML tables
 * - Headers: # Header → <h1>, ## Header → <h2>, etc.
 * - Code blocks: ```code``` → <pre><code>
 * - Numbered lists: 1. Item → <ol><li>
 * - Bullet points: •, - → <ul><li>
 * - Links: [label](url) → clickable anchor
 * - Bold text: **text** → <strong>
 * - Italic text: _text_ or *text* → <em>
 * - Strikethrough: ~~text~~ → <del>
 * - Blockquotes: > text → <blockquote>
 * - Inline code: `code` → <code>
 * @param {string} content - Raw message content
 * @returns {string} - Formatted HTML content
 */
export const formatMessage = (content) => {
  if (!content) return '';

  let formatted = content;

  // Handle code blocks first (to prevent processing markdown inside them)
  formatted = formatted.replace(
    /```(?:\w+\n)?([\s\S]*?)```/g,
    '<pre class="bg-gray-100 dark:bg-gray-700 p-3 rounded-md overflow-x-auto my-2"><code class="text-sm font-mono">$1</code></pre>'
  );

  // Handle markdown tables
  formatted = formatTables(formatted);

  // Handle headers (# ## ### etc.)
  formatted = formatted.replace(/^(#{1,6})\s+(.+)$/gm, (match, hashes, text) => {
    const level = hashes.length;
    const sizes = {
      1: 'text-2xl font-bold mb-4 mt-6',
      2: 'text-xl font-bold mb-3 mt-5', 
      3: 'text-lg font-bold mb-2 mt-4',
      4: 'text-base font-bold mb-2 mt-3',
      5: 'text-sm font-bold mb-1 mt-2',
      6: 'text-xs font-bold mb-1 mt-2'
    };
    return `<h${level} class="${sizes[level]} text-gray-900 dark:text-gray-100">${text}</h${level}>`;
  });

  // Handle blockquotes
  formatted = formatted.replace(
    /^>\s+(.+)$/gm,
    '<blockquote class="border-l-4 border-gray-300 dark:border-gray-600 pl-4 py-2 my-2 bg-gray-50 dark:bg-gray-800 italic text-gray-700 dark:text-gray-300">$1</blockquote>'
  );

  // Handle strikethrough
  formatted = formatted.replace(
    /~~(.+?)~~/g,
    '<del class="line-through text-gray-500 dark:text-gray-400">$1</del>'
  );

  // Convert markdown-style links [label](url) to HTML
  formatted = formatted.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-500 hover:text-blue-700 underline break-all">$1</a>'
  );

  // Convert URLs without markdown to clickable links
  formatted = formatted.replace(
    /(https?:\/\/[^\s<]+)/g,
    '<a href="$1" target="_blank" rel="noopener noreferrer" class="text-blue-500 hover:text-blue-700 underline break-all">$1</a>'
  );

  // Handle bold text: **bold** or __bold__
  formatted = formatted.replace(
    /(\*\*|__)(.*?)\1/g,
    '<strong class="font-semibold">$2</strong>'
  );

  // Handle italic text: *italic* or _italic_
  formatted = formatted.replace(
    /(\*|_)(.*?)\1/g,
    '<em class="italic">$2</em>'
  );

  // Handle inline code: `code`
  formatted = formatted.replace(
    /`([^`]+)`/g,
    '<code class="bg-gray-100 dark:bg-gray-700 px-1 py-0.5 rounded text-sm font-mono">$1</code>'
  );

  // Split by lines to handle bullet points, numbered lists, and paragraphs
  const lines = formatted.split('\n');
  const processedLines = [];
  let inBulletList = false;
  let inNumberedList = false;
  let inParagraph = false;
  let currentParagraph = [];

  const closeParagraph = () => {
    if (currentParagraph.length > 0) {
      processedLines.push(`<p class="mb-3">${currentParagraph.join(' ')}</p>`);
      currentParagraph = [];
      inParagraph = false;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    if (line === '') {
      // Close any open list or paragraph on empty lines
      if (inBulletList) {
        processedLines.push('</ul>');
        inBulletList = false;
      }
      if (inNumberedList) {
        processedLines.push('</ol>');
        inNumberedList = false;
      }
      closeParagraph();
      processedLines.push('');
      continue;
    }
    
    // Check if line is a numbered list item
    if (line.match(/^\d+\.\s+/)) {
      closeParagraph();
      if (inBulletList) {
        processedLines.push('</ul>');
        inBulletList = false;
      }
      const numberedContent = line.replace(/^\d+\.\s+/, '');
      
      if (!inNumberedList) {
        processedLines.push('<ol class="list-decimal list-inside ml-4 space-y-1 mb-3">');
        inNumberedList = true;
      }
      
      processedLines.push(`<li class="text-gray-700 dark:text-gray-300">${numberedContent}</li>`);
    }
    // Check if line is a bullet point
    else if (line.match(/^[•\-*]\s+/)) {
      closeParagraph();
      if (inNumberedList) {
        processedLines.push('</ol>');
        inNumberedList = false;
      }
      const bulletContent = line.replace(/^[•\-*]\s+/, '');
      
      if (!inBulletList) {
        processedLines.push('<ul class="list-disc list-inside ml-4 space-y-1 mb-3">');
        inBulletList = true;
      }
      
      processedLines.push(`<li class="text-gray-700 dark:text-gray-300">${bulletContent}</li>`);
    } else {
      // Close lists if we were in them
      if (inBulletList) {
        processedLines.push('</ul>');
        inBulletList = false;
      }
      if (inNumberedList) {
        processedLines.push('</ol>');
        inNumberedList = false;
      }
      
      // Add to current paragraph
      currentParagraph.push(line);
      inParagraph = true;
      
      // If next line is empty or a bullet, close the paragraph
      if (i === lines.length - 1 || lines[i + 1].trim() === '' || lines[i + 1].match(/^[•\-*]\s+/)) {
        closeParagraph();
      }
    }
  }

  // Close any remaining open lists or paragraph
  if (inBulletList) {
    processedLines.push('</ul>');
  }
  if (inNumberedList) {
    processedLines.push('</ol>');
  }
  closeParagraph();

  // Join lines with newlines, but remove empty lines
  return processedLines.join('\n');
};

/**
 * Format markdown tables into HTML tables
 * @param {string} content - Content that may contain markdown tables
 * @returns {string} - Content with tables converted to HTML
 */
const formatTables = (content) => {
  // Match markdown tables (including header separator)
  const tableRegex = /(\|[^\n]+\|\n\|[\s:|-]+\|\n(?:\|[^\n]+\|\n?)*)/g;
  
  return content.replace(tableRegex, (tableMatch) => {
    const lines = tableMatch.trim().split('\n');
    if (lines.length < 2) return tableMatch;
    
    const headerLine = lines[0];
    const separatorLine = lines[1];
    const dataLines = lines.slice(2);
    
    // Parse header
    const headers = headerLine.split('|')
      .map(cell => cell.trim())
      .filter(cell => cell !== '');
    
    if (headers.length === 0) return tableMatch;
    
    // Parse alignment from separator line
    const alignments = separatorLine.split('|')
      .map(cell => cell.trim())
      .filter(cell => cell !== '')
      .map(cell => {
        if (cell.startsWith(':') && cell.endsWith(':')) return 'center';
        if (cell.endsWith(':')) return 'right';
        return 'left';
      });
    
    // Build HTML table
    let html = '<div class="overflow-x-auto my-4">';
    html += '<table class="min-w-full border-collapse border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800">';
    
    // Header
    html += '<thead class="bg-gray-50 dark:bg-gray-700">';
    html += '<tr>';
    headers.forEach((header, index) => {
      const alignment = alignments[index] || 'left';
      const alignClass = {
        left: 'text-left',
        center: 'text-center', 
        right: 'text-right'
      }[alignment];
      html += `<th class="border border-gray-300 dark:border-gray-600 px-4 py-2 font-semibold text-gray-900 dark:text-gray-100 ${alignClass}">${header}</th>`;
    });
    html += '</tr>';
    html += '</thead>';
    
    // Body
    if (dataLines.length > 0) {
      html += '<tbody>';
      dataLines.forEach(line => {
        if (line.trim()) {
          const cells = line.split('|')
            .map(cell => cell.trim())
            .filter((cell, index, arr) => {
              // Remove empty cells at start/end (from leading/trailing |)
              return !(index === 0 && cell === '') && !(index === arr.length - 1 && cell === '');
            });
          
          if (cells.length > 0) {
            html += '<tr class="hover:bg-gray-50 dark:hover:bg-gray-700">';
            cells.forEach((cell, index) => {
              const alignment = alignments[index] || 'left';
              const alignClass = {
                left: 'text-left',
                center: 'text-center',
                right: 'text-right'
              }[alignment];
              html += `<td class="border border-gray-300 dark:border-gray-600 px-4 py-2 text-gray-700 dark:text-gray-300 ${alignClass}">${cell}</td>`;
            });
            html += '</tr>';
          }
        }
      });
      html += '</tbody>';
    }
    
    html += '</table>';
    html += '</div>';
    
    return html;
  });
};

/**
 * Convert formatted HTML back to React-safe JSX
 * @param {string} htmlContent - HTML content from formatMessage
 * @returns {object} - Object with dangerouslySetInnerHTML prop
 */
export const createMarkup = (htmlContent) => {
  return { __html: htmlContent };
};

/**
 * Extract plain text from formatted content (for previews, etc.)
 * @param {string} content - Raw or formatted content
 * @returns {string} - Plain text without formatting
 */
export const extractPlainText = (content) => {
  if (!content) return '';
  
  return content
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Remove link formatting
    .replace(/^[•\-*]\s+/gm, '') // Remove bullet points
    .replace(/\n/g, ' ') // Replace newlines with spaces
    .trim();
};
