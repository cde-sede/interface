/**
 * RichText Renderer
 *
 * DSL wrapper for the RichText component that handles:
 * - Value resolution from context
 * - Nested RichTextComponent unwrapping
 * - ComponentWrapper integration for events
 */

import type { RichTextComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';
import RichText from '../components/RichText';

interface RichTextRendererProps {
	component: RichTextComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function RichTextRenderer({
	component,
	pageData,
	modalData,
	actionEngine
}: RichTextRendererProps) {
	const { content, variant = 'body', align = 'left' } = component;

	const context = { pageData, data: modalData };
	let resolvedContent = resolveValue(content, context);

	// Handle nested RichTextComponents - recursively extract content until we get a string
	while (resolvedContent && typeof resolvedContent === 'object' && resolvedContent.type === 'rich-text') {
		resolvedContent = resolveValue(resolvedContent.content, context);
	}

	// Convert to string
	const contentString = typeof resolvedContent === 'string'
		? resolvedContent
		: (resolvedContent != null ? String(resolvedContent) : '');

	if (!contentString) {
		return null;
	}

	const richTextElement = (
		<RichText
			content={contentString}
			variant={variant}
			align={align}
			style={component.customStyle as React.CSSProperties}
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
		return richTextElement;
	}

	// Create a component object without customStyle to avoid duplication
	const wrapperComponent = {
		...component,
		customStyle: undefined
	};

	return (
		<ComponentWrapper
			component={wrapperComponent}
			pageData={pageData}
			modalData={modalData}
			actionEngine={actionEngine}
		>
			{richTextElement}
		</ComponentWrapper>
	);
}
