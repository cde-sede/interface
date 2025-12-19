/**
 * Code Block Renderer
 *
 * Renders code block component from DSL with syntax highlighting and copy functionality
 */

import { useState } from 'react';
import type { CodeBlockComponent } from './types';
import { resolveValue } from './valueResolver';

interface CodeBlockRendererProps {
	modalData?: any;
	component: CodeBlockComponent;
	pageData?: any;
}

export default function CodeBlockRenderer({ component, pageData, modalData }: CodeBlockRendererProps) {
	const { content, language = 'json', copyable = true, collapsible = false } = component;
	const [copied, setCopied] = useState(false);
	const [collapsed, setCollapsed] = useState(false);

	// Resolve content if it's a ValueRef
	const resolvedContent = resolveValue(content, { pageData, data: modalData });

	// Convert content to string
	const contentString = (() => {
		if (typeof resolvedContent === 'string') {
			return resolvedContent;
		}
		if (typeof resolvedContent === 'object') {
			return JSON.stringify(resolvedContent, null, 2);
		}
		return String(resolvedContent);
	})();

	const handleCopy = async () => {
		try {
			await navigator.clipboard.writeText(contentString);
			setCopied(true);
			setTimeout(() => setCopied(false), 2000);
		} catch (err) {
			console.error('Failed to copy:', err);
		}
	};

	return (
		<div className="code-block-container">
			<div className="code-block-header">
				<span className="code-block-language">{language}</span>
				<div className="code-block-actions">
					{collapsible && (
						<button
							className="code-block-action-button"
							onClick={() => setCollapsed(!collapsed)}
							title={collapsed ? 'Expand' : 'Collapse'}
						>
							{collapsed ? '▼' : '▲'}
						</button>
					)}
					{copyable && (
						<button
							className="code-block-action-button"
							onClick={handleCopy}
							title="Copy to clipboard"
						>
							{copied ? '✓ Copied' : '📋 Copy'}
						</button>
					)}
				</div>
			</div>
			{!collapsed && (
				<pre className={`code-block code-block-${language}`}>
					<code>{contentString}</code>
				</pre>
			)}
		</div>
	);
}
