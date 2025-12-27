/**
 * Card Component
 *
 * Container component for grouping related content with optional header and footer.
 */

import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Card.css';

export type CardVariant = 'default' | 'outlined' | 'elevated';
export type CardPadding = 'none' | 'small' | 'medium' | 'large';

export interface CardProps extends BaseComponentProps {
	title?: string;             /** Optional card title */
	subtitle?: string;          /** Optional subtitle below title */
	variant?: CardVariant;      /** Visual variant */
	padding?: CardPadding;      /** Content padding size */
	children?: React.ReactNode; /** Card content */
	actions?: React.ReactNode;  /** Optional actions footer content */
}

export function Card({
	title,
	subtitle,
	variant = 'default',
	padding = 'medium',
	children,
	actions,
	className,
	style,
	'data-testid': dataTestId
}: CardProps) {
	const cardClassName = cn(
		'lib-card',
		`lib-card-${variant}`,
		`lib-card-padding-${padding}`,
		className
	);

	return (
		<div
			className={cardClassName}
			style={style}
			data-testid={dataTestId}
		>
			{(title || subtitle) && (
				<div className="lib-card-header">
					{title && <h3 className="lib-card-title">{title}</h3>}
					{subtitle && <p className="lib-card-subtitle">{subtitle}</p>}
				</div>
			)}

			<div className="lib-card-content">
				{children}
			</div>

			{actions && (
				<div className="lib-card-actions">
					{actions}
				</div>
			)}
		</div>
	);
}
