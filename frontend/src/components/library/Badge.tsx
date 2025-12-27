/**
 * Badge Component
 *
 * A small label component for displaying statuses, tags, or categories.
 */

import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Badge.css';

export type BadgeVariant = 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info' | 'neutral';
export type BadgeSize = 'small' | 'medium' | 'large';

export interface BadgeProps extends BaseComponentProps {
	label: string;          /** The text content of the badge */
	variant?: BadgeVariant; /** Visual style variant */
	size?: BadgeSize;       /** Size of the badge */
	icon?: string;          /** Optional icon to display before the label */
}

export function Badge({
	label,
	variant = 'default',
	size = 'medium',
	icon,
	className,
	style,
	'data-testid': dataTestId
}: BadgeProps) {
	const badgeClassName = cn(
		'lib-badge',
		`lib-badge-${variant}`,
		`lib-badge-${size}`,
		className
	);

	return (
		<span
			className={badgeClassName}
			style={style}
			data-testid={dataTestId}
		>
			{icon && <span className="lib-badge-icon">{icon}</span>}
			<span className="lib-badge-label">{label}</span>
		</span>
	);
}
