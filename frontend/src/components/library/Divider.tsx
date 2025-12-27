/**
 * Divider Component
 *
 * Visual separator with optional label.
 */

import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Divider.css';

export type DividerOrientation = 'horizontal' | 'vertical';
export type DividerVariant = 'solid' | 'dashed' | 'dotted';

export interface DividerProps extends BaseComponentProps {
	label?: string;                   /** Optional label text */
	orientation?: DividerOrientation; /** Orientation of the divider */
	variant?: DividerVariant;         /** Line style variant */
}

export function Divider({
	label,
	orientation = 'horizontal',
	variant = 'solid',
	className,
	style,
	'data-testid': dataTestId
}: DividerProps) {
	const dividerClassName = cn(
		'lib-divider',
		`lib-divider-${orientation}`,
		`lib-divider-${variant}`,
		className
	);

	if (label) {
		return (
			<div
				className={dividerClassName}
				style={style}
				data-testid={dataTestId}
			>
				<span className="lib-divider-label">{label}</span>
			</div>
		);
	}

	return (
		<div
			className={dividerClassName}
			style={style}
			data-testid={dataTestId}
		/>
	);
}
