/**
 * Skeleton Renderer
 *
 * DSL adapter for Skeleton library component.
 */

import { Skeleton } from '../../library/Skeleton';
import type { SkeletonComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { resolveValue } from './valueResolver';
import { ComponentWrapper } from './ComponentWrapper';

interface SkeletonRendererProps {
	component: SkeletonComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function SkeletonRenderer({ component, pageData, modalData, actionEngine }: SkeletonRendererProps) {
	const {
		variant = 'text',
		width,
		height,
		count = 1,
		animation = 'pulse',
		customStyle,
		className: rawClassName
	} = component;

	const context = { pageData, data: modalData };
	const resolvedWidth = width ? resolveValue(width, context) : undefined;
	const resolvedHeight = height ? resolveValue(height, context) : undefined;
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const skeletonElement = (
		<Skeleton
			variant={variant}
			width={resolvedWidth}
			height={resolvedHeight}
			count={count}
			animation={animation}
			style={customStyle as React.CSSProperties}
			className={className}
		/>
	);

	// Only use ComponentWrapper if we have wrapper-level properties (events, id, aria attributes)
	// customStyle and className are applied directly to the component above
	const needsWrapper = Boolean(
		actionEngine && (
			component.events?.click ||
			component.events?.hover ||
			component.id ||
			component.ariaLabel ||
			component.ariaDescribedBy
		)
	);

	if (!needsWrapper) {
		return skeletonElement;
	}

	// Create a component object without customStyle/className to avoid duplication
	const wrapperComponent = {
		...component,
		customStyle: undefined,
		className: undefined
	};

	return (
		<ComponentWrapper
			component={wrapperComponent}
			pageData={pageData}
			modalData={modalData}
			actionEngine={actionEngine}
		>
			{skeletonElement}
		</ComponentWrapper>
	);
}
