/**
 * Panel Component
 *
 * Collapsible side panel for additional content.
 * Gmail-style horizontal stacking with proper width-based positioning.
 */

import { useState, useEffect, useRef, useId, type ReactNode } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Panel.css';

export type PanelPosition = 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';

const PANEL_GAP = 10;

// Registry tracks panel order and their actual widths
interface PanelData {
	width: number;
}

const panelRegistry = new Map<PanelPosition, Map<string, PanelData>>();
const panelOrder = new Map<PanelPosition, string[]>();

function getOrCreateRegistry(position: PanelPosition): Map<string, PanelData> {
	if (!panelRegistry.has(position)) {
		panelRegistry.set(position, new Map());
		panelOrder.set(position, []);
	}
	return panelRegistry.get(position)!;
}

function registerPanel(position: PanelPosition, id: string, width: number): void {
	const registry = getOrCreateRegistry(position);
	const order = panelOrder.get(position)!;

	// Add to order if not already there
	if (!order.includes(id)) {
		order.push(id);
	}

	// Update width
	registry.set(id, { width });

	// Notify all panels to recalculate
	window.dispatchEvent(new CustomEvent('panel-layout-change', { detail: { position } }));
}

function unregisterPanel(position: PanelPosition, id: string): void {
	const registry = panelRegistry.get(position);
	const order = panelOrder.get(position);

	if (registry) {
		registry.delete(id);
	}
	if (order) {
		const idx = order.indexOf(id);
		if (idx >= 0) order.splice(idx, 1);
	}

	// Notify remaining panels
	window.dispatchEvent(new CustomEvent('panel-layout-change', { detail: { position } }));
}

/**
 * Calculate horizontal offset for a panel.
 * Offset = sum of widths of all panels to the RIGHT (higher index) + gaps
 */
function calculateOffset(position: PanelPosition, id: string): number {
	const registry = panelRegistry.get(position);
	const order = panelOrder.get(position);

	if (!registry || !order) return 0;

	const myIndex = order.indexOf(id);
	if (myIndex === -1) return 0;

	let offset = 0;

	// Sum widths of all panels to the RIGHT (higher index = closer to edge)
	for (let i = myIndex + 1; i < order.length; i++) {
		const panelId = order[i];
		const data = registry.get(panelId);
		if (data) {
			offset += data.width + PANEL_GAP;
		}
	}

	return offset;
}

function isLastPanel(position: PanelPosition, id: string): boolean {
	const order = panelOrder.get(position);
	if (!order || order.length === 0) return true;
	return order[order.length - 1] === id;
}

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
	const panelId = useId();
	const panelRef = useRef<HTMLDivElement>(null);
	const [internalIsMinimized, setInternalIsMinimized] = useState(defaultMinimized);
	const [isMinimizing, setIsMinimizing] = useState(false);
	const [horizontalOffset, setHorizontalOffset] = useState(0);

	const isMinimized = controlledIsMinimized !== undefined ? controlledIsMinimized : internalIsMinimized;

	// Register panel and set up width tracking
	useEffect(() => {
		// Auto-minimize if not the last panel (only rightmost is expanded by default)
		if (controlledIsMinimized === undefined && !defaultMinimized) {
			// Small delay to let registry populate
			setTimeout(() => {
				if (!isLastPanel(position, panelId)) {
					setInternalIsMinimized(true);
				}
			}, 0);
		}

		return () => {
			unregisterPanel(position, panelId);
		};
	}, [position, panelId]);

	// Track panel width with ResizeObserver
	useEffect(() => {
		const element = panelRef.current;
		if (!element) return;

		const updateWidth = () => {
			const rect = element.getBoundingClientRect();
			registerPanel(position, panelId, rect.width);
		};

		// Initial registration
		updateWidth();

		// Watch for size changes
		const observer = new ResizeObserver(updateWidth);
		observer.observe(element);

		return () => {
			observer.disconnect();
		};
	}, [position, panelId, isMinimized]);

	// Listen for layout changes and recalculate offset
	useEffect(() => {
		const handleLayoutChange = (e: Event) => {
			const customEvent = e as CustomEvent<{ position: PanelPosition }>;
			if (customEvent.detail.position === position) {
				const offset = calculateOffset(position, panelId);
				setHorizontalOffset(offset);
			}
		};

		window.addEventListener('panel-layout-change', handleLayoutChange);

		// Initial calculation
		const offset = calculateOffset(position, panelId);
		setHorizontalOffset(offset);

		return () => {
			window.removeEventListener('panel-layout-change', handleLayoutChange);
		};
	}, [position, panelId]);

	// Listen for maximize requests (when another panel expands, minimize this one)
	useEffect(() => {
		const handleMaximizeRequest = (e: Event) => {
			const customEvent = e as CustomEvent<{ position: PanelPosition; panelId: string }>;
			if (customEvent.detail.position === position &&
			    customEvent.detail.panelId !== panelId &&
			    !isMinimized &&
			    controlledIsMinimized === undefined) {
				setInternalIsMinimized(true);
				onMinimize?.(true);
			}
		};

		window.addEventListener('panel-maximize-request', handleMaximizeRequest);
		return () => window.removeEventListener('panel-maximize-request', handleMaximizeRequest);
	}, [position, panelId, isMinimized, controlledIsMinimized, onMinimize]);

	const handleClose = () => {
		onClose?.();
	};

	const handleMinimize = () => {
		if (!isMinimized) {
			// Minimizing - animate then minimize
			setIsMinimizing(true);
			setTimeout(() => {
				if (controlledIsMinimized === undefined) {
					setInternalIsMinimized(true);
				}
				onMinimize?.(true);
				setIsMinimizing(false);
			}, 200);
		} else {
			// Expanding - tell others to minimize first
			window.dispatchEvent(new CustomEvent('panel-maximize-request', {
				detail: { position, panelId }
			}));

			if (controlledIsMinimized === undefined) {
				setInternalIsMinimized(false);
			}
			onMinimize?.(false);
			onOpen?.();
		}
	};

	const handleRestore = () => {
		// Tell all other panels to minimize
		window.dispatchEvent(new CustomEvent('panel-maximize-request', {
			detail: { position, panelId }
		}));

		if (controlledIsMinimized === undefined) {
			setInternalIsMinimized(false);
		}
		onMinimize?.(false);
		onOpen?.();
	};

	// Build style object with positioning
	const buildPositionStyle = (baseStyle?: React.CSSProperties): React.CSSProperties => {
		const posStyle: React.CSSProperties = { ...baseStyle };

		// Vertical position
		if (position.includes('top')) {
			posStyle.top = '1rem';
		} else {
			posStyle.bottom = '1rem';
		}

		// Horizontal position with offset
		if (position.includes('right')) {
			posStyle.right = horizontalOffset > 0
				? `calc(1rem + ${horizontalOffset}px)`
				: '1rem';
		} else {
			posStyle.left = horizontalOffset > 0
				? `calc(1rem + ${horizontalOffset}px)`
				: '1rem';
		}

		return posStyle;
	};

	const panelClassName = cn(
		'lib-panel',
		`lib-panel-${position}`,
		isMinimizing && 'minimizing',
		className
	);

	// Render minimized widget
	if (isMinimized && !isMinimizing) {
		const minimizedStyle = buildPositionStyle(style);

		return (
			<div
				ref={panelRef}
				className="lib-panel-minimized"
				style={minimizedStyle}
				onClick={handleRestore}
				data-testid={dataTestId ? `${dataTestId}-minimized` : undefined}
			>
				<span className="lib-panel-minimized-title">{title}</span>
			</div>
		);
	}

	// Render full panel
	const panelStyle = buildPositionStyle({
		width,
		...style
	});

	return (
		<div
			ref={panelRef}
			className={panelClassName}
			style={panelStyle}
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
