/**
 * Divider Renderer
 *
 * Renders a divider component for visual separation
 */

import type { DividerComponent } from './types';

interface DividerRendererProps {
	component: DividerComponent;
}

export default function DividerRenderer({ component }: DividerRendererProps) {
	const { label, orientation = 'horizontal', variant = 'solid' } = component;

	const className = `dsl-divider dsl-divider-${orientation} dsl-divider-${variant}`;

	if (label) {
		return (
			<div className={className}>
				<span className="dsl-divider-label">{label}</span>
			</div>
		);
	}

	return <div className={className} />;
}
