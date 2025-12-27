/**
 * Stepper Component
 *
 * Multi-step process indicator.
 */

import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './Stepper.css';

export type StepStatus = 'pending' | 'active' | 'completed' | 'error';
export type StepperOrientation = 'horizontal' | 'vertical';

export interface StepItem {
	label: string;        /** Step label */
	description?: string; /** Optional description */
	status?: StepStatus;  /** Step status */
}

export interface StepperProps extends BaseComponentProps {
	steps: StepItem[];                /** Array of steps */
	currentStep?: number;             /** Current active step index */
	orientation?: StepperOrientation; /** Layout orientation */
}

export function Stepper({
	steps,
	currentStep = 0,
	orientation = 'horizontal',
	className,
	style,
	'data-testid': dataTestId
}: StepperProps) {
	if (!steps || steps.length === 0) {
		return null;
	}

	const stepperClassName = cn(
		'lib-stepper',
		`lib-stepper-${orientation}`,
		className
	);

	const renderStep = (step: StepItem, index: number) => {
		let status = step.status;
		if (!status) {
			if (index < currentStep) {
				status = 'completed';
			} else if (index === currentStep) {
				status = 'active';
			} else {
				status = 'pending';
			}
		}

		const stepClassName = cn(
			'lib-stepper-step',
			`lib-stepper-step-${status}`
		);

		return (
			<div key={index} className={stepClassName}>
				<div className="lib-stepper-step-indicator">
					<div className="lib-stepper-step-circle">
						{status === 'completed' ? '✓' : status === 'error' ? '✕' : index + 1}
					</div>
					{index < steps.length - 1 && <div className="lib-stepper-step-line" />}
				</div>
				<div className="lib-stepper-step-content">
					<div className="lib-stepper-step-label">{step.label}</div>
					{step.description && (
						<div className="lib-stepper-step-description">{step.description}</div>
					)}
				</div>
			</div>
		);
	};

	return (
		<div
			className={stepperClassName}
			style={style}
			data-testid={dataTestId}
		>
			{steps.map((step, index) => renderStep(step, index))}
		</div>
	);
}
