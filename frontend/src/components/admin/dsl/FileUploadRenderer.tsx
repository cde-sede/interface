/**
 * File Upload Renderer
 *
 * DSL adapter for FileUpload library component.
 */

import { startTransition } from 'react';
import { FileUpload } from '../../library/FileUpload';
import type { FileUploadComponent } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface FileUploadRendererProps {
	component: FileUploadComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function FileUploadRenderer({ component, pageData, modalData, actionEngine }: FileUploadRendererProps) {
	const {
		name,
		label,
		accept,
		multiple = false,
		maxSize,
		maxFiles,
		onUpload,
		onRemove,
		variant = 'button',
		showPreview = true
	} = component;

	const resolvedLabel = label ? resolveValue(label, { pageData, data: modalData }) : 'Upload File';

	const handleUpload = (files: File[]) => {
		if (onUpload && actionEngine) {
			startTransition(() => {
				actionEngine.execute(onUpload, {
					pageData,
					data: modalData,
					form: { [name]: files, files },
				});
			});
		}
	};

	const handleRemove = (file: File, index: number) => {
		if (onRemove && actionEngine) {
			startTransition(() => {
				actionEngine.execute(onRemove, {
					pageData,
					data: modalData,
					form: {
						file: {
							name: file.name,
							size: file.size,
							type: file.type
						},
						index
					}
				});
			});
		}
	};

	const { customStyle, className: rawClassName } = component;
	const context = { pageData, data: modalData };
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const fileUploadElement = (
		<FileUpload
			name={name}
			label={resolvedLabel}
			accept={accept}
			multiple={multiple}
			maxSize={maxSize}
			maxFiles={maxFiles}
			onUpload={handleUpload}
			onRemove={handleRemove}
			variant={variant}
			showPreview={showPreview}
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
		return fileUploadElement;
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
			{fileUploadElement}
		</ComponentWrapper>
	);
}
