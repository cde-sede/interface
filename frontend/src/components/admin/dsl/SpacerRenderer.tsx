/**
 * Spacer Renderer
 *
 * DSL adapter for Spacer library component.
 */

import { Spacer } from '../../library/Spacer';
import type { SpacerComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';

interface SpacerRendererProps {
	component: SpacerComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function SpacerRenderer({ component, pageData, modalData, actionEngine }: SpacerRendererProps) {
	const { size = 'md', orientation = 'vertical' } = component;

	if (!actionEngine) {
		return (
			<Spacer
				size={size}
				orientation={orientation}
			/>
		);
	}

	return (
		<ComponentWrapper
			component={component}
			pageData={pageData}
			modalData={modalData}
			actionEngine={actionEngine}
		>
			<Spacer
				size={size}
				orientation={orientation}
			/>
		</ComponentWrapper>
	);
}
