/**
 * Utility functions for formatting GPT text messages
 */

/**
 * Format message content with support for:
 * - Line breaks (\n → <br>)
 * - Bullet points (•, - → <ul><li>)
 * - Links: [label](url) → clickable anchor
 * @param {string} content - Raw message content
 * @returns {string} - Formatted HTML content
 */
export const formatMessage = (content) => {
  if (!content) return '';

  let formatted = content;

  // Convert markdown-style links [label](url) to HTML
  formatted = formatted.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-500 hover:text-blue-700 underline">$1</a>'
  );

  // Convert URLs without markdown to clickable links
  formatted = formatted.replace(
    /(https?:\/\/[^\s]+)/g,
    '<a href="$1" target="_blank" rel="noopener noreferrer" class="text-blue-500 hover:text-blue-700 underline">$1</a>'
  );

  // Split by lines to handle bullet points
  const lines = formatted.split('\n');
  const processedLines = [];
  let inList = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // Check if line is a bullet point
    if (line.match(/^[•\-*]\s+/)) {
      const bulletContent = line.replace(/^[•\-*]\s+/, '');
      
      if (!inList) {
        processedLines.push('<ul class="list-disc list-inside ml-4 space-y-1">');
        inList = true;
      }
      
      processedLines.push(`<li class="text-gray-700 dark:text-gray-300">${bulletContent}</li>`);
    } else {
      // Close list if we were in one
      if (inList) {
        processedLines.push('</ul>');
        inList = false;
      }
      
      // Add regular line (could be empty for spacing)
      if (line === '') {
        processedLines.push('<br>');
      } else {
        processedLines.push(line);
      }
    }
  }

  // Close list if still open
  if (inList) {
    processedLines.push('</ul>');
  }

  return processedLines.join('\n');
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
