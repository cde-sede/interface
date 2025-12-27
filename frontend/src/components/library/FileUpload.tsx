/**
 * FileUpload Component
 *
 * File upload with drag-and-drop, previews, and multiple variants.
 */

import { useState, useRef } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './FileUpload.css';

export type FileUploadVariant = 'button' | 'dropzone' | 'avatar';

export interface FileUploadProps extends BaseComponentProps {
	name?: string;                                  /** Input name */
	label?: string;                                 /** Upload label */
	accept?: string;                                /** Accepted file types */
	multiple?: boolean;                             /** Allow multiple files */
	maxSize?: number;                               /** Maximum file size in bytes */
	maxFiles?: number;                              /** Maximum number of files */
	onUpload?: (files: File[]) => void;             /** Upload handler */
	onRemove?: (file: File, index: number) => void; /** Remove handler */
	variant?: FileUploadVariant;                    /** Visual variant */
	showPreview?: boolean;                          /** Show image previews */
}

export function FileUpload({
	name,
	label = 'Upload File',
	accept,
	multiple = false,
	maxSize,
	maxFiles,
	onUpload,
	onRemove,
	variant = 'button',
	showPreview = true,
	className,
	style,
	'data-testid': dataTestId
}: FileUploadProps) {
	const [files, setFiles] = useState<File[]>([]);
	const [previews, setPreviews] = useState<string[]>([]);
	const [isDragging, setIsDragging] = useState(false);
	const fileInputRef = useRef<HTMLInputElement>(null);

	const handleFiles = (fileList: FileList) => {
		const newFiles = Array.from(fileList);

		if (maxFiles && files.length + newFiles.length > maxFiles) {
			console.error(`Maximum ${maxFiles} files allowed`);
			return;
		}

		if (maxSize) {
			const oversizedFiles = newFiles.filter(f => f.size > maxSize);
			if (oversizedFiles.length > 0) {
				console.error(`Files exceed maximum size of ${maxSize} bytes`);
				return;
			}
		}

		const updatedFiles = multiple ? [...files, ...newFiles] : newFiles;
		setFiles(updatedFiles);

		// Generate previews for images
		if (showPreview) {
			const newPreviews: string[] = [];
			for (const file of newFiles) {
				if (file.type.startsWith('image/')) {
					const reader = new FileReader();
					reader.onload = (e) => {
						newPreviews.push(e.target?.result as string);
						setPreviews(multiple ? [...previews, ...newPreviews] : newPreviews);
					};
					reader.readAsDataURL(file);
				}
			}
		}

		onUpload?.(updatedFiles);
	};

	const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		if (e.target.files)
			handleFiles(e.target.files);
	};

	const handleDrop = (e: React.DragEvent) => {
		e.preventDefault();
		setIsDragging(false);
		if (e.dataTransfer.files)
			handleFiles(e.dataTransfer.files);
	};

	const handleDragOver = (e: React.DragEvent) => {
		e.preventDefault();
		setIsDragging(true);
	};

	const handleDragLeave = () => {
		setIsDragging(false);
	};

	const removeFile = (index: number) => {
		const removedFile = files[index];
		const updatedFiles = files.filter((_, i) => i !== index);
		const updatedPreviews = previews.filter((_, i) => i !== index);
		setFiles(updatedFiles);
		setPreviews(updatedPreviews);

		onRemove?.(removedFile, index);
	};

	const formatFileSize = (bytes: number): string => {
		if (bytes === 0) return '0 Bytes';
		const k = 1024;
		const sizes = ['Bytes', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
	};

	const containerClassName = cn(
		'lib-file-upload-container',
		variant === 'avatar' && 'lib-file-upload-avatar',
		className
	);

	if (variant === 'button') {
		return (
			<div className={containerClassName} style={style} data-testid={dataTestId}>
				{label && <label className="lib-file-upload-label">{label}</label>}
				<input
					ref={fileInputRef}
					type="file"
					name={name}
					accept={accept}
					multiple={multiple}
					onChange={handleFileInputChange}
					className="lib-file-upload-input"
				/>
				<button
					type="button"
					className="lib-file-upload-button"
					onClick={() => fileInputRef.current?.click()}
				>
					Choose File{multiple ? 's' : ''}
				</button>
				{files.length > 0 && (
					<div className="lib-file-upload-list">
						{files.map((file, index) => (
							<div key={index} className="lib-file-upload-item">
								{showPreview && previews[index] && (
									<img src={previews[index]} alt={file.name} className="lib-file-upload-preview" />
								)}
								<div className="lib-file-upload-info">
									<span className="lib-file-upload-name">{file.name}</span>
									<span className="lib-file-upload-size">{formatFileSize(file.size)}</span>
								</div>
								<button
									type="button"
									className="lib-file-upload-remove"
									onClick={() => removeFile(index)}
								>
									×
								</button>
							</div>
						))}
					</div>
				)}
			</div>
		);
	}

	if (variant === 'dropzone') {
		const dropzoneClassName = cn(
			'lib-file-upload-dropzone',
			isDragging && 'lib-file-upload-dragging'
		);

		return (
			<div className={containerClassName} style={style} data-testid={dataTestId}>
				{label && <label className="lib-file-upload-label">{label}</label>}
				<input
					ref={fileInputRef}
					type="file"
					name={name}
					accept={accept}
					multiple={multiple}
					onChange={handleFileInputChange}
					className="lib-file-upload-input"
				/>
				<div
					className={dropzoneClassName}
					onDrop={handleDrop}
					onDragOver={handleDragOver}
					onDragLeave={handleDragLeave}
					onClick={() => fileInputRef.current?.click()}
				>
					<div className="lib-file-upload-dropzone-content">
						<span className="lib-file-upload-icon">📁</span>
						<p className="lib-file-upload-text">Drag and drop files here or click to browse</p>
						{maxSize && <p className="lib-file-upload-hint">Max size: {formatFileSize(maxSize)}</p>}
					</div>
				</div>
				{files.length > 0 && (
					<div className="lib-file-upload-list">
						{files.map((file, index) => (
							<div key={index} className="lib-file-upload-item">
								{showPreview && previews[index] && (
									<img src={previews[index]} alt={file.name} className="lib-file-upload-preview" />
								)}
								<div className="lib-file-upload-info">
									<span className="lib-file-upload-name">{file.name}</span>
									<span className="lib-file-upload-size">{formatFileSize(file.size)}</span>
								</div>
								<button
									type="button"
									className="lib-file-upload-remove"
									onClick={() => removeFile(index)}
								>
									×
								</button>
							</div>
						))}
					</div>
				)}
			</div>
		);
	}

	return (
		<div className={containerClassName} style={style} data-testid={dataTestId}>
			{label && <label className="lib-file-upload-label">{label}</label>}
			<input
				ref={fileInputRef}
				type="file"
				name={name}
				accept={accept || 'image/*'}
				onChange={handleFileInputChange}
				className="lib-file-upload-input"
			/>
			<div className="lib-file-upload-avatar-wrapper" onClick={() => fileInputRef.current?.click()}>
				{previews[0] ? (
					<img src={previews[0]} alt="Avatar" className="lib-file-upload-avatar-preview" />
				) : (
					<div className="lib-file-upload-avatar-placeholder">📷</div>
				)}
				<div className="lib-file-upload-avatar-overlay">Change</div>
			</div>
		</div>
	);
}
