/**
 * Tooltip Component
 *
 * Hover tooltip for displaying contextual information.
 */

import { useState, useRef, useLayoutEffect, type ReactNode } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import { Portal } from './Portal';
import './Tooltip.css';

export type TooltipPlacement = 'top' | 'bottom' | 'left' | 'right';
export type TooltipVariant = 'dark' | 'light';

export interface TooltipProps extends BaseComponentProps {
	content: ReactNode;           /** Tooltip content */
	children: ReactNode;          /** Trigger element */
	placement?: TooltipPlacement; /** Tooltip placement */
	variant?: TooltipVariant;     /** Visual variant */
}

export function Tooltip({
	content,
	children,
	placement = 'top',
	variant = 'dark',
	className,
	style,
	'data-testid': dataTestId
}: TooltipProps) {
	const [isVisible, setIsVisible] = useState(false);
	const [tooltipPosition, setTooltipPosition] = useState<{ top?: number; bottom?: number; left?: number; right?: number; transform?: string }>({});
	const [actualPlacement, setActualPlacement] = useState<TooltipPlacement>(placement);
	const [isPositioned, setIsPositioned] = useState(false);
	const triggerRef = useRef<HTMLDivElement>(null);
	const tooltipRef = useRef<HTMLDivElement>(null);

	// Calculate tooltip position with boundary detection
	useLayoutEffect(() => {
		if (!isVisible) {
			setIsPositioned(false);
			return;
		}

		if (!tooltipRef.current || !triggerRef.current) return;

		// Use requestAnimationFrame to ensure tooltip is fully rendered
		const frame = requestAnimationFrame(() => {
			if (!tooltipRef.current || !triggerRef.current) return;

			const tooltip = tooltipRef.current;
			const trigger = triggerRef.current;
			const tooltipRect = tooltip.getBoundingClientRect();
			const triggerRect = trigger.getBoundingClientRect();

			// Skip if tooltip hasn't rendered with dimensions yet
			if (tooltipRect.width === 0 || tooltipRect.height === 0) {
				return;
			}

			const viewportHeight = window.innerHeight;
			const viewportWidth = window.innerWidth;
			const gap = 8; // 0.5rem gap

			const position: { top?: number; bottom?: number; left?: number; right?: number; transform?: string } = {};
			let finalPlacement = placement;

		// Calculate position based on placement with boundary checking
		const tooltipWidth = tooltipRect.width;
		const tooltipHeight = tooltipRect.height;

		// Check if preferred placement fits, otherwise flip
		if (placement === 'top') {
			const spaceAbove = triggerRect.top;
			const spaceBelow = viewportHeight - triggerRect.bottom;

			if (spaceAbove >= tooltipHeight + gap || spaceAbove > spaceBelow) {
				// Position above
				position.bottom = viewportHeight - triggerRect.top + gap;
				position.left = triggerRect.left + triggerRect.width / 2;
				position.transform = 'translateX(-50%)';
				finalPlacement = 'top';
			} else {
				// Flip to below
				position.top = triggerRect.bottom + gap;
				position.left = triggerRect.left + triggerRect.width / 2;
				position.transform = 'translateX(-50%)';
				finalPlacement = 'bottom';
			}
		} else if (placement === 'bottom') {
			const spaceBelow = viewportHeight - triggerRect.bottom;
			const spaceAbove = triggerRect.top;

			if (spaceBelow >= tooltipHeight + gap || spaceBelow > spaceAbove) {
				// Position below
				position.top = triggerRect.bottom + gap;
				position.left = triggerRect.left + triggerRect.width / 2;
				position.transform = 'translateX(-50%)';
				finalPlacement = 'bottom';
			} else {
				// Flip to above
				position.bottom = viewportHeight - triggerRect.top + gap;
				position.left = triggerRect.left + triggerRect.width / 2;
				position.transform = 'translateX(-50%)';
				finalPlacement = 'top';
			}
		} else if (placement === 'left') {
			const spaceLeft = triggerRect.left;
			const spaceRight = viewportWidth - triggerRect.right;

			if (spaceLeft >= tooltipWidth + gap || spaceLeft > spaceRight) {
				// Position left
				position.right = viewportWidth - triggerRect.left + gap;
				position.top = triggerRect.top + triggerRect.height / 2;
				position.transform = 'translateY(-50%)';
				finalPlacement = 'left';
			} else {
				// Flip to right
				position.left = triggerRect.right + gap;
				position.top = triggerRect.top + triggerRect.height / 2;
				position.transform = 'translateY(-50%)';
				finalPlacement = 'right';
			}
		} else if (placement === 'right') {
			const spaceRight = viewportWidth - triggerRect.right;
			const spaceLeft = triggerRect.left;

			if (spaceRight >= tooltipWidth + gap || spaceRight > spaceLeft) {
				// Position right
				position.left = triggerRect.right + gap;
				position.top = triggerRect.top + triggerRect.height / 2;
				position.transform = 'translateY(-50%)';
				finalPlacement = 'right';
			} else {
				// Flip to left
				position.right = viewportWidth - triggerRect.left + gap;
				position.top = triggerRect.top + triggerRect.height / 2;
				position.transform = 'translateY(-50%)';
				finalPlacement = 'left';
			}
		}

			setTooltipPosition(position);
			setActualPlacement(finalPlacement);
			setIsPositioned(true);
		});

		return () => cancelAnimationFrame(frame);
	}, [isVisible, placement]);

	const tooltipClassName = cn(
		'lib-tooltip',
		`lib-tooltip-${actualPlacement}`,
		`lib-tooltip-${variant}`,
		className
	);

	return (
		<div className="lib-tooltip-wrapper" style={style} data-testid={dataTestId}>
			<div
				ref={triggerRef}
				className="lib-tooltip-trigger"
				onMouseEnter={() => setIsVisible(true)}
				onMouseLeave={() => setIsVisible(false)}
			>
				{children}
			</div>
			{isVisible && (
				<Portal>
					<div
						ref={tooltipRef}
						className={tooltipClassName}
						style={{
							...(!isPositioned && { top: 0, left: 0 }),
							...tooltipPosition,
							opacity: isPositioned ? 1 : 0,
							transition: 'opacity 0.15s ease'
						}}
					>
						{content}
					</div>
				</Portal>
			)}
		</div>
	);
}
