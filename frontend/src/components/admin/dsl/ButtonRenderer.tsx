/**
 * Button Renderer
 *
 * Renders button component from DSL
 */

import type { ButtonComponent } from './types';
import { ActionEngine } from './actionEngine';
import { resolveValue } from './valueResolver';

interface ButtonRendererProps {
	modalData?: any;
	component: ButtonComponent;
	pageData?: any;
	actionEngine: ActionEngine;
	context?: any;
}

export default function ButtonRenderer({
	component,
	pageData,
	modalData,
	actionEngine,
	context = {}
}: ButtonRendererProps) {
	const {
		label,
		action,
		variant = 'primary',
		icon,
		size = 'medium',
		disabled = false,
		confirmMessage
	} = component;

	const handleClick = async () => {
		const actionContext = { pageData, data: modalData, ...context };

		if (confirmMessage) {
			const message = resolveValue(confirmMessage, actionContext);
			await actionEngine.executeWithConfirmation(action, message, actionContext);
		} else {
			await actionEngine.execute(action, actionContext);
		}
	};

	return (
		<button
			className={`action-button ${variant} ${size}`}
			onClick={handleClick}
			disabled={disabled}
		>
			{icon && <span className="button-icon">{icon}</span>}
			{label}
		</button>
	);
}
