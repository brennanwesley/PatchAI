/**
 * Utility functions for formatting GPT text messages
 */

/**
 * Format message content with support for:
 * - Line breaks (\n → <br>)
 * - Bullet points (•, - → <ul><li>)
 * - Links: [label](url) → clickable anchor
 * - Bold text: **text** → <strong>
 * - Italic text: _text_ or *text* → <em>
 * - Code blocks: `code` → <code>
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

  // Split by lines to handle bullet points and paragraphs
  const lines = formatted.split('\n');
  const processedLines = [];
  let inList = false;
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
      if (inList) {
        processedLines.push('</ul>');
        inList = false;
      }
      closeParagraph();
      processedLines.push('');
      continue;
    }
    
    // Check if line is a bullet point
    if (line.match(/^[•\-*]\s+/)) {
      closeParagraph();
      const bulletContent = line.replace(/^[•\-*]\s+/, '');
      
      if (!inList) {
        processedLines.push('<ul class="list-disc list-inside ml-4 space-y-1 mb-3">');
        inList = true;
      }
      
      processedLines.push(`<li class="text-gray-700 dark:text-gray-300">${bulletContent}</li>`);
    } else {
      // Close list if we were in one
      if (inList) {
        processedLines.push('</ul>');
        inList = false;
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

  // Close any remaining lists or paragraphs
  if (inList) {
    processedLines.push('</ul>');
  }
  closeParagraph();

  // Join lines with newlines, but remove empty lines
  return processedLines.filter(line => line !== '').join('\n');
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
