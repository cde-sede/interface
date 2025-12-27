/**
 * Image Renderer
 *
 * DSL adapter for Image library component.
 */

import { Image } from '../../library/Image';
import type { ImageComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { resolveValue } from './valueResolver';
import { ComponentWrapper } from './ComponentWrapper';

interface ImageRendererProps {
	component: ImageComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function ImageRenderer({ component, pageData, modalData, actionEngine }: ImageRendererProps) {
	const {
		src: rawSrc,
		alt: rawAlt,
		width: rawWidth,
		height: rawHeight,
		fit = 'cover',
		rounded = false,
		bordered = false,
		customStyle,
		className: rawClassName
	} = component;

	const context = { pageData, data: modalData };
	const src = resolveValue(rawSrc, context);
	const alt = rawAlt ? resolveValue(rawAlt, context) : '';
	const width = rawWidth ? resolveValue(rawWidth, context) : undefined;
	const height = rawHeight ? resolveValue(rawHeight, context) : undefined;
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const imageElement = (
		<Image
			src={src}
			alt={alt}
			width={width}
			height={height}
			fit={fit}
			rounded={rounded}
			bordered={bordered}
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
		return imageElement;
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
			{imageElement}
		</ComponentWrapper>
	);
}
