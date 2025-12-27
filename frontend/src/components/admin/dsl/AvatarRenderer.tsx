/**
 * Avatar Renderer
 *
 * DSL adapter for Avatar library component.
 */

import { Avatar } from '../../library/Avatar';
import type { AvatarComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface AvatarRendererProps {
	component: AvatarComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function AvatarRenderer({ component, pageData, modalData, actionEngine }: AvatarRendererProps) {
	const {
		src: rawSrc,
		name: rawName,
		size = 'md',
		variant = 'circle',
		status,
		customStyle,
		className: rawClassName
	} = component;

	const context = { pageData, data: modalData };
	const src = rawSrc ? resolveValue(rawSrc, context) : undefined;
	const name = resolveValue(rawName, context);
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const avatarElement = (
		<Avatar
			name={name}
			src={src}
			size={size}
			variant={variant}
			status={status}
			style={customStyle as React.CSSProperties}
			className={className}
		/>
	);

	// Only use ComponentWrapper if we have wrapper-level properties
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
		return avatarElement;
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
			{avatarElement}
		</ComponentWrapper>
	);
}
