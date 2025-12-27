/**
 * Alert Component
 *
 * Displays important messages with different severity levels.
 */

import { useState } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Alert.css';

export type AlertVariant = 'info' | 'success' | 'warning' | 'error';

export interface AlertProps extends BaseComponentProps {
	message: string;        /** The message content to display */
	variant: AlertVariant;  /** Visual style variant indicating severity */
	dismissible?: boolean;  /** Whether the alert can be dismissed */
	onDismiss?: () => void; /** Callback when alert is dismissed */
}

export function Alert({
	message,
	variant,
	dismissible = false,
	onDismiss,
	className,
	style,
	'data-testid': dataTestId
}: AlertProps) {
	const [isVisible, setIsVisible] = useState(true);

	const handleDismiss = () => {
		setIsVisible(false);
		onDismiss?.();
	};

	if (!isVisible) return null;

	const alertClassName = cn(
		'lib-alert',
		`lib-alert-${variant}`,
		className
	);

	return (
		<div
			className={alertClassName}
			style={style}
			data-testid={dataTestId}
			role="alert"
		>
			<span className="lib-alert-message">{message}</span>
			{dismissible && (
				<button
					className="lib-alert-dismiss"
					onClick={handleDismiss}
					aria-label="Dismiss alert"
					type="button"
				>
					×
				</button>
			)}
		</div>
	);
}
