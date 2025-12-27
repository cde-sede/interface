/**
 * Callout Component
 *
 * Highlighted message box for important information.
 */

import { useState } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Callout.css';

export type CalloutVariant = 'info' | 'success' | 'warning' | 'error' | 'neutral';

export interface CalloutProps extends BaseComponentProps {
	message: string;          /** Message content */
	title?: string;           /** Optional title */
	variant?: CalloutVariant; /** Visual variant */
	icon?: string;            /** Optional icon */
	dismissible?: boolean;    /** Whether the callout can be dismissed */
	onDismiss?: () => void;   /** Callback when dismissed */
}

export function Callout({
	message,
	title,
	variant = 'info',
	icon,
	dismissible = false,
	onDismiss,
	className,
	style,
	'data-testid': dataTestId
}: CalloutProps) {
	const [dismissed, setDismissed] = useState(false);

	const handleDismiss = () => {
		setDismissed(true);
		onDismiss?.();
	};

	if (dismissed) return null;

	const calloutClassName = cn(
		'lib-callout',
		`lib-callout-${variant}`,
		className
	);

	return (
		<div
			className={calloutClassName}
			style={style}
			data-testid={dataTestId}
		>
			{icon && <span className="lib-callout-icon">{icon}</span>}
			<div className="lib-callout-content">
				{title && <h4 className="lib-callout-title">{title}</h4>}
				<p className="lib-callout-message">{message}</p>
			</div>
			{dismissible && (
				<button
					className="lib-callout-dismiss"
					onClick={handleDismiss}
					type="button"
					aria-label="Dismiss callout"
				>
					×
				</button>
			)}
		</div>
	);
}
