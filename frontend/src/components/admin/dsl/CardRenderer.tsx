/**
 * Card Renderer
 *
 * DSL adapter for Card library component.
 * Handles rendering DSL content and actions.
 */

import { Card } from '../../library/Card';
import type { CardComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';
import { renderComponent } from '../DSLRenderer';
import ButtonRenderer from './ButtonRenderer';

interface CardRendererProps {
	modalData?: any;
	component: CardComponent;
	pageData?: any;
	actionEngine?: ActionEngine;
}

export default function CardRenderer({ component, pageData, modalData, actionEngine }: CardRendererProps) {
	const {
		title,
		subtitle,
		content,
		actions,
		variant = 'default',
		padding = 'medium',
		customStyle,
		className: rawClassName
	} = component;

	const context = { pageData, data: modalData };
	const resolvedTitle = title ? resolveValue(title, context) : undefined;
	const resolvedSubtitle = subtitle ? resolveValue(subtitle, context) : undefined;
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const cardElement = (
		<Card
			title={resolvedTitle}
			subtitle={resolvedSubtitle}
			variant={variant}
			padding={padding}
			style={customStyle as React.CSSProperties}
			className={className}
			actions={actions && actions.length > 0 ? (
				<>
					{actions.map((action, index) => (
						<ButtonRenderer
							key={index}
							component={action}
							pageData={pageData}
							modalData={modalData}
							actionEngine={actionEngine}
						/>
					))}
				</>
			) : undefined}
		>
			{content.map((comp, index) => (
				<div key={index}>
					{actionEngine && renderComponent(comp, pageData, modalData, actionEngine)}
				</div>
			))}
		</Card>
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
		return cardElement;
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
			{cardElement}
		</ComponentWrapper>
	);
}
