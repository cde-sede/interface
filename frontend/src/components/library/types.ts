/**
 * Shared Types for Component Library
 */

/**
 * Common variant types used across components
 */
export type Variant = 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info' | 'neutral';

/**
 * Common size types
 */
export type Size = 'sm' | 'md' | 'lg';

/**
 * Base props that most components accept
 */
export interface BaseComponentProps {
  className?: string;          /** Custom CSS class name */
  style?: React.CSSProperties; /** Custom inline styles */
  'data-testid'?: string;      /** Test ID for testing */
}

/**
 * Props for components that can be disabled
 */
export interface DisableableProps {
  disabled?: boolean;
}

/**
 * Props for components with loading states
 */
export interface LoadableProps {
  loading?: boolean;
}

/**
 * Props for components with icons
 */
export interface IconProps {
  icon?: string;
  iconPosition?: 'left' | 'right';
}
