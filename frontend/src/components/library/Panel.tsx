/**
 * Panel Component
 *
 * Collapsible side panel for additional content.
 */

import { useState, type ReactNode } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Panel.css';

export type PanelPosition = 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';

export interface PanelProps extends BaseComponentProps {
	title: string;                 /** Panel title */
	children: ReactNode;           /** Panel content */
	position?: PanelPosition;      /** Panel position */
	width?: string;                /** Panel width */
	defaultOpen?: boolean;         /** Default open state */
	isOpen?: boolean;              /** Controlled open state */
	onOpen?: () => void;           /** Open handler */
	onClose?: () => void;          /** Close handler */
	defaultMinimized?: boolean;    /** Default minimized state */
	isMinimized?: boolean;         /** Controlled minimized state */
	onMinimize?: (isMinimized: boolean) => void; /** Minimize handler */
}

export function Panel({
	title,
	children,
	position = 'bottom-right',
	width = '400px',
	defaultOpen: _defaultOpen = false,
	isOpen: _controlledIsOpen,
	onOpen,
	onClose,
	defaultMinimized = false,
	isMinimized: controlledIsMinimized,
	onMinimize,
	className,
	style,
	'data-testid': dataTestId
}: PanelProps) {
	const [internalIsMinimized, setInternalIsMinimized] = useState(defaultMinimized);
	const [isMinimizing, setIsMinimizing] = useState(false);
	const isMinimized = controlledIsMinimized !== undefined ? controlledIsMinimized : internalIsMinimized;

	const handleClose = () => {
		onClose?.();
	};

	const handleMinimize = () => {
		if (!isMinimized) {
			// Start minimizing animation
			setIsMinimizing(true);
			// Wait for animation to complete before actually minimizing
			setTimeout(() => {
				if (controlledIsMinimized === undefined) {
					setInternalIsMinimized(true);
				}
				onMinimize?.(true);
				setIsMinimizing(false);
			}, 200); // Match animation duration
		} else {
			// Expanding - no need to delay
			if (controlledIsMinimized === undefined) {
				setInternalIsMinimized(false);
			}
			onMinimize?.(false);
		}
	};

	const handleRestore = () => {
		if (controlledIsMinimized === undefined) {
			setInternalIsMinimized(false);
		}
		onMinimize?.(false);
		onOpen?.();
	};

	const panelClassName = cn(
		'lib-panel',
		`lib-panel-${position}`,
		isMinimizing && 'minimizing',
		className
	);

	// Render minimized widget (only if actually minimized and not currently minimizing)
	if (isMinimized && !isMinimizing) {
		return (
			<div
				className={cn('lib-panel-minimized', `lib-panel-minimized-${position}`)}
				onClick={handleRestore}
				data-testid={dataTestId ? `${dataTestId}-minimized` : undefined}
			>
				<span className="lib-panel-minimized-title">{title}</span>
			</div>
		);
	}
				//<button
				//	className="lib-panel-minimized-restore"
				//	onClick={(e) => {
				//		e.stopPropagation();
				//		handleRestore();
				//	}}
				//	aria-label="Restore"
				//	type="button"
				//>
				//	□
				//</button>

	// Render full panel (also render during minimizing animation)
	return (
		<div
			className={panelClassName}
			style={{ width, ...style }}
			data-testid={dataTestId}
		>
			<div className="lib-panel-header">
				<h3 className="lib-panel-title">{title}</h3>
				<div className="lib-panel-controls">
					<button
						className="lib-panel-minimize"
						onClick={(e) => {
							e.stopPropagation();
							handleMinimize();
						}}
						aria-label="Minimize"
						type="button"
						disabled={isMinimizing}
					>
						-
					</button>
					<button
						className="lib-panel-close"
						onClick={(e) => {
							e.stopPropagation();
							handleClose();
						}}
						aria-label="Close"
						type="button"
						disabled={isMinimizing}
					>
						×
					</button>
				</div>
			</div>
			<div className="lib-panel-body">
				{children}
			</div>
		</div>
	);
}
