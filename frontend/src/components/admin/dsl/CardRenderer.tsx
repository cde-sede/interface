/**
 * Card Renderer
 *
 * Renders a card component for grouping content
 */

import type { CardComponent, ComponentDefinition } from './types';
import { resolveValue } from './valueResolver';
import { ActionEngine } from './actionEngine';
import StatsCardsRenderer from './StatsCardsRenderer';
import InfoGridRenderer from './InfoGridRenderer';
import CodeBlockRenderer from './CodeBlockRenderer';
import TableRenderer from './TableRenderer';
import ButtonRenderer from './ButtonRenderer';
import FormRenderer from './FormRenderer';
import BadgeRenderer from './BadgeRenderer';
import ProgressBarRenderer from './ProgressBarRenderer';
import DividerRenderer from './DividerRenderer';

interface CardRendererProps {
	modalData?: any;
	component: CardComponent;
	pageData?: any;
	actionEngine: ActionEngine;
}

export default function CardRenderer({ component, pageData, modalData, actionEngine }: CardRendererProps) {
	const {
		title,
		subtitle,
		content,
		actions,
		variant = 'default',
		padding = 'medium'
	} = component;

	// Resolve title and subtitle if they're ValueRefs
	const resolvedTitle = title ? resolveValue(title, { pageData, data: modalData }) : undefined;
	const resolvedSubtitle = subtitle ? resolveValue(subtitle, { pageData, data: modalData }) : undefined;

	const className = `dsl-card dsl-card-${variant} dsl-card-padding-${padding}`;

	const renderComponent = (comp: ComponentDefinition, index: number) => {
		switch (comp.type) {
			case 'stats-cards':
				return <StatsCardsRenderer key={index} component={comp} />;
			case 'info-grid':
				return <InfoGridRenderer key={index} component={comp} pageData={pageData} modalData={modalData} />;
			case 'code-block':
				return <CodeBlockRenderer key={index} component={comp} pageData={pageData} modalData={modalData} />;
			case 'table':
				return <TableRenderer key={index} component={comp} pageData={pageData} modalData={modalData} actionEngine={actionEngine} />;
			case 'button':
				return <ButtonRenderer key={index} component={comp} pageData={pageData} modalData={modalData} actionEngine={actionEngine} />;
			case 'form':
				return <FormRenderer key={index} component={comp} pageData={pageData} modalData={modalData} actionEngine={actionEngine} />;
			case 'badge':
				return <BadgeRenderer key={index} component={comp} pageData={pageData} modalData={modalData} />;
			case 'progress-bar':
				return <ProgressBarRenderer key={index} component={comp} pageData={pageData} modalData={modalData} />;
			case 'divider':
				return <DividerRenderer key={index} component={comp} />;
			case 'alert':
				return (
					<div key={index} className={`alert alert-${comp.variant}`}>
						{comp.message}
					</div>
				);
			default:
				return <div key={index}>Unknown component type</div>;
		}
	};

	return (
		<div className={className}>
			{(resolvedTitle || resolvedSubtitle) && (
				<div className="dsl-card-header">
					{resolvedTitle && <h3 className="dsl-card-title">{resolvedTitle}</h3>}
					{resolvedSubtitle && <p className="dsl-card-subtitle">{resolvedSubtitle}</p>}
				</div>
			)}

			<div className="dsl-card-content">
				{content.map((comp, index) => renderComponent(comp, index))}
			</div>

			{actions && actions.length > 0 && (
				<div className="dsl-card-actions">
					{actions.map((action, index) => (
						<ButtonRenderer
							key={index}
							component={action}
							pageData={pageData}
							modalData={modalData}
							actionEngine={actionEngine}
						/>
					))}
				</div>
			)}
		</div>
	);
}
