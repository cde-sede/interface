/**
 * Panel Renderer
 *
 * Renders a collapsible panel from DSL definition using Panel library component
 */

import type { PanelDefinition } from './types';
import { ActionEngine } from './actionEngine';
import { resolveValue } from './valueResolver';
import { renderComponent } from '../DSLRenderer';
import { Panel } from '../../library/Panel';

interface PanelRendererProps {
	panel: PanelDefinition;
	panelData?: any;
	pageData?: any;
	actionEngine: ActionEngine;
	isOpen: boolean;
	onClose: () => void;
	onOpen: () => void;
	isMinimized: boolean;
	onMinimize: (minimized: boolean) => void;
}

export default function PanelRenderer({
	panel,
	panelData,
	pageData,
	actionEngine,
	isOpen,
	onClose,
	onOpen,
	isMinimized,
	onMinimize
}: PanelRendererProps) {

	const {
		title: rawTitle,
		width = '400px',
		content,
		position = 'bottom-right'
	} = panel;

	// Resolve title if it's a ValueRef
	const title = resolveValue(rawTitle, { pageData, data: panelData });
	const resolvedWidth = resolveValue(width, { pageData, data: panelData });

	return (
		<Panel
			title={title}
			position={position}
			width={resolvedWidth}
			isOpen={isOpen}
			onOpen={onOpen}
			onClose={onClose}
			isMinimized={isMinimized}
			onMinimize={onMinimize}
		>
			{content?.map((component, index) => (
				<div key={index}>
					{renderComponent(component, pageData, panelData, actionEngine)}
				</div>
			))}
		</Panel>
	);
}
