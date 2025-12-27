/**
 * Button Component
 *
 * Interactive button with variants, sizes, and icon support.
 */

import { cn } from './utils';
import type { BaseComponentProps, DisableableProps, IconProps } from './types';
import './Button.css';

export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'success';
export type ButtonSize = 'small' | 'medium' | 'large';

export interface ButtonProps extends BaseComponentProps, DisableableProps, IconProps {
	label: string;           /** Button label text */
	variant?: ButtonVariant; /** Visual variant */
	size?: ButtonSize;       /** Size variant */
	onClick?: () => void;    /** Click handler */
}

export function Button({
	label,
	variant = 'primary',
	size = 'medium',
	icon,
	iconPosition = 'left',
	disabled = false,
	onClick,
	className,
	style,
	'data-testid': dataTestId
}: ButtonProps) {
	const buttonClassName = cn(
		'lib-button',
		`lib-button-${variant}`,
		`lib-button-${size}`,
		className
	);

	return (
		<button
			className={buttonClassName}
			onClick={onClick}
			disabled={disabled}
			style={style}
			data-testid={dataTestId}
			type="button"
		>
			{icon && iconPosition === 'left' && <span className="lib-button-icon">{icon}</span>}
			<span className="lib-button-label">{label}</span>
			{icon && iconPosition === 'right' && <span className="lib-button-icon">{icon}</span>}
		</button>
	);
}
