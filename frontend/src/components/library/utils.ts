/**
 * Shared Utilities for Component Library
 */

/**
 * Combines class names, filtering out falsy values
 * Similar to clsx/classnames but lightweight
 *
 * @example
 * cn('btn', isActive && 'active', className)
 * // => 'btn active my-class'
 */
export function cn(...classes: (string | boolean | null | undefined)[]): string {
  return classes.filter(Boolean).join(' ');
}

/**
 * Generates a unique ID for component instances
 * Useful for accessibility (aria-describedby, aria-labelledby, etc.)
 */
let idCounter = 0;
export function generateId(prefix: string = 'lib'): string {
  return `${prefix}-${++idCounter}`;
}

/**
 * Format a number with thousand separators
 *
 * @example
 * formatNumber(1234567) // => '1,234,567'
 */
export function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US').format(value);
}

/**
 * Format a value as currency
 *
 * @example
 * formatCurrency(1234.56, 'USD') // => '$1,234.56'
 */
export function formatCurrency(value: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency
  }).format(value);
}

/**
 * Format a date string
 *
 * @example
 * formatDate('2025-12-25T10:00:00') // => '12/25/2025'
 */
export function formatDate(date: string | Date, options?: Intl.DateTimeFormatOptions): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat('en-US', options).format(dateObj);
}

/**
 * Truncate text with ellipsis
 *
 * @example
 * truncate('Hello World', 8) // => 'Hello...'
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

/**
 * Debounce a function call
 * Useful for search inputs, resize handlers, etc.
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null;

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null;
      func(...args);
    };

    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
