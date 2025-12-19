/**
 * Badge Renderer
 *
 * Renders a badge component for labels/tags
 */

import type { BadgeComponent } from './types';
import { resolveValue } from './valueResolver';

interface BadgeRendererProps {
	modalData?: any;
	component: BadgeComponent;
	pageData?: any;
}

export default function BadgeRenderer({ component, pageData, modalData }: BadgeRendererProps) {
	const { label, variant = 'default', size = 'medium', icon } = component;

	// Resolve label if it's a ValueRef
	const resolvedLabel = resolveValue(label, { pageData, data: modalData });

	const className = `dsl-badge dsl-badge-${variant} dsl-badge-${size}`;

	return (
		<span className={className}>
			{icon && <span className="dsl-badge-icon">{icon}</span>}
			{resolvedLabel}
		</span>
	);
}
