/**
 * Form Renderer
 *
 * Renders form component from DSL with validation
 */

import { startTransition } from 'react';
import type { FormComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue, resolveComponentData } from './valueResolver';
import { Form, type FormField } from '../../library';

interface FormRendererProps {
	component: FormComponent;
	pageData?: any;
	actionEngine?: ActionEngine;
	modalData?: any;
}

export default function FormRenderer({ component, pageData, actionEngine, modalData }: FormRendererProps) {
	const { submitAction, cancelAction, layout = 'vertical', readonly = false } = component;

	// Resolve fields (might be a ValueRef)
	const dslFields = resolveComponentData(component.fields, pageData, modalData) || [];

	// Map DSL fields to library FormField, resolving ValueRefs
	const context = { pageData, data: modalData };
	const fields: FormField[] = dslFields.map((field: any) => ({
		name: field.name,
		label: field.label,
		type: field.type,
		required: field.required,
		defaultValue: field.defaultValue !== undefined
			? resolveValue(field.defaultValue, context)
			: undefined,
		placeholder: field.placeholder
			? resolveValue(field.placeholder, context)
			: undefined,
		helpText: field.helpText
			? resolveValue(field.helpText, context)
			: undefined,
		validation: field.validation,
		options: field.options
			? resolveValue(field.options, context)
			: undefined,
		readonly: field.readonly,
		min: field.min,
		max: field.max,
		step: field.step
	}));

	// Handle submit
	const handleSubmit = async (formData: Record<string, any>) => {
		if (!actionEngine) return Promise.resolve();

		return new Promise<void>((resolve) => {
			startTransition(() => {
				const submitContext = { form: formData, pageData, data: modalData };
				actionEngine.execute(submitAction, submitContext).finally(() => {
					resolve();
				});
			});
		});
	};

	// Handle cancel
	const handleCancel = cancelAction && actionEngine ? () => {
		startTransition(() => {
			const cancelContext = { pageData, data: modalData };
			actionEngine.execute(cancelAction, cancelContext);
		});
	} : undefined;

	const { customStyle, className: rawClassName } = component;
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const formElement = (
		<Form
			fields={fields}
			onSubmit={handleSubmit}
			onCancel={handleCancel}
			layout={layout}
			readonly={readonly}
			submitLabel="Submit"
			cancelLabel="Cancel"
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
		return formElement;
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
			{formElement}
		</ComponentWrapper>
	);
}
