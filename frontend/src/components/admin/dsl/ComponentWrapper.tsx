/**
 * Component Wrapper
 *
 * Wraps any DSL component and adds support for:
 * - Event handlers (onClick, onHover)
 * - Custom styling
 * - Visibility control
 * - Accessibility props
 */

import { useState, startTransition, type ReactNode, type CSSProperties } from 'react';
import type { BaseComponentProps } from './types';
import type { ActionEngine } from './actionEngine';
import { resolveValue } from './valueResolver';

interface ComponentWrapperProps {
	component: BaseComponentProps;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
	children: ReactNode;
}

export function ComponentWrapper({
	component,
	pageData,
	modalData,
	actionEngine,
	children
}: ComponentWrapperProps) {
	const {
		events,
		confirmMessage,
		customStyle,
		className: rawClassName,
		visible: rawVisible = true,
		ariaLabel: rawAriaLabel,
		ariaDescribedBy: rawAriaDescribedBy,
		id
	} = component;

	const context = { pageData, data: modalData };

	// Resolve dynamic values
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;
	const visible = resolveValue(rawVisible, context);
	const ariaLabel = rawAriaLabel ? resolveValue(rawAriaLabel, context) : undefined;
	const ariaDescribedBy = rawAriaDescribedBy ? resolveValue(rawAriaDescribedBy, context) : undefined;

	// State for hover
	const [isHovered, setIsHovered] = useState(false);

	// Don't render if not visible
	if (!visible) {
		return null;
	}

	// Build event handlers (only if actionEngine is available)
	const handleClick = events?.click && actionEngine ? () => {
		const actionContext = { pageData, data: modalData };

		startTransition(() => {
			if (confirmMessage) {
				const message = resolveValue(confirmMessage, actionContext);
				actionEngine.executeWithConfirmation(events.click!, message, actionContext);
			} else {
				actionEngine.execute(events.click!, actionContext);
			}
		});
	} : undefined;

	const handleMouseEnter = events?.hover && actionEngine ? () => {
		setIsHovered(true);
		const actionContext = { pageData, data: modalData, event: 'mouseenter' };

		startTransition(() => {
			actionEngine.execute(events.hover!, actionContext);
		});
	} : undefined;

	const handleMouseLeave = events?.hover && actionEngine && isHovered ? () => {
		setIsHovered(false);
		// Hover action clears on leave
	} : undefined;

	// Build style object
	const computedStyle: CSSProperties = {
		...(customStyle as CSSProperties),
		...(handleClick && { cursor: 'pointer' })
	};

	// Build wrapper props
	const wrapperProps: any = {
		id,
		className,
		style: Object.keys(computedStyle).length > 0 ? computedStyle : undefined,
		onClick: handleClick,
		onMouseEnter: handleMouseEnter,
		onMouseLeave: handleMouseLeave,
		'aria-label': ariaLabel,
		'aria-describedby': ariaDescribedBy
	};

	// If no wrapper props, render children directly
	const hasWrapperProps = Boolean(
		id || className || handleClick || handleMouseEnter ||
		handleMouseLeave || ariaLabel || ariaDescribedBy ||
		(customStyle && Object.keys(customStyle).length > 0)
	);

	if (!hasWrapperProps) {
		return <>{children}</>;
	}

	// Wrap in div with all props
	return <div {...wrapperProps}>{children}</div>;
}
