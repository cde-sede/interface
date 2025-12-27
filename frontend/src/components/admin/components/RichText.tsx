/**
 * RichText Component
 *
 * Renders formatted text with support for:
 * - # H1, ## H2, ### H3, etc. (headers)
 * - **bold**
 * - *italic* or _italic_
 * - `code`
 * - [link text](url)
 * - Newlines (\n)
 */

import React from 'react';
import '../dsl/RichTextRenderer.css';

interface TextNode {
	type: 'text' | 'bold' | 'italic' | 'code' | 'link' | 'linebreak' | 'header';
	content?: string;
	url?: string;
	level?: number; // For headers: 1-6
}

/**
 * Parse markdown-style text into nodes
 * Supports: # headers, **bold**, *italic*, `code`, [text](url), \n
 */
function parseMarkdown(text: string): TextNode[] {
	const nodes: TextNode[] = [];
	const lines = text.split('\n');

	for (let lineIdx = 0; lineIdx < lines.length; lineIdx++) {
		const line = lines[lineIdx];

		// Check for header at start of line: # Header
		const headerMatch = line.match(/^(#{1,6})\s+(.+)$/);
		if (headerMatch) {
			const level = headerMatch[1].length;
			const content = headerMatch[2];
			nodes.push({ type: 'header', content, level });
			if (lineIdx < lines.length - 1) {
				nodes.push({ type: 'linebreak' });
			}
			continue;
		}

		// Parse inline markdown in the line
		let i = 0;
		while (i < line.length) {
			// Check for bold: **text**
			if (line.slice(i, i + 2) === '**') {
				const endIndex = line.indexOf('**', i + 2);
				if (endIndex !== -1) {
					const content = line.slice(i + 2, endIndex);
					nodes.push({ type: 'bold', content });
					i = endIndex + 2;
					continue;
				}
			}

			// Check for italic: *text* or _text_
			if (line[i] === '*' || line[i] === '_') {
				const char = line[i];
				const endIndex = line.indexOf(char, i + 1);
				if (endIndex !== -1 && line[i + 1] !== char) {
					const content = line.slice(i + 1, endIndex);
					nodes.push({ type: 'italic', content });
					i = endIndex + 1;
					continue;
				}
			}

			// Check for code: `text`
			if (line[i] === '`') {
				const endIndex = line.indexOf('`', i + 1);
				if (endIndex !== -1) {
					const content = line.slice(i + 1, endIndex);
					nodes.push({ type: 'code', content });
					i = endIndex + 1;
					continue;
				}
			}

			// Check for link: [text](url)
			if (line[i] === '[') {
				const textEndIndex = line.indexOf(']', i + 1);
				if (textEndIndex !== -1 && line[textEndIndex + 1] === '(') {
					const urlEndIndex = line.indexOf(')', textEndIndex + 2);
					if (urlEndIndex !== -1) {
						const content = line.slice(i + 1, textEndIndex);
						const url = line.slice(textEndIndex + 2, urlEndIndex);
						nodes.push({ type: 'link', content, url });
						i = urlEndIndex + 1;
						continue;
					}
				}
			}

			// Regular text - find next special character
			let endIndex = i + 1;
			while (
				endIndex < line.length &&
				line[endIndex] !== '*' &&
				line[endIndex] !== '_' &&
				line[endIndex] !== '`' &&
				line[endIndex] !== '['
			) {
				endIndex++;
			}

			const content = line.slice(i, endIndex);
			nodes.push({ type: 'text', content });
			i = endIndex;
		}

		// Add line break after each line except the last
		if (lineIdx < lines.length - 1) {
			nodes.push({ type: 'linebreak' });
		}
	}

	return nodes;
}

export interface RichTextProps {
	content: string;
	variant?: 'body' | 'small' | 'caption' | 'subtitle' | 'large';
	align?: 'left' | 'center' | 'right' | 'justify';
	className?: string;
	style?: React.CSSProperties;
}

export default function RichText({
	content,
	variant = 'body',
	align = 'left',
	className,
	style
}: RichTextProps) {
	if (!content) {
		return null;
	}

	const nodes = parseMarkdown(content);

	return (
		<div
			className={`dsl-rich-text dsl-rich-text-${variant} dsl-rich-text-${align} ${className || ''}`}
			style={style}
		>
			{nodes.map((node, index) => {
				switch (node.type) {
					case 'header': {
						const level = node.level || 1;
						return React.createElement(`h${level}`, { key: index }, node.content);
					}
					case 'bold':
						return <strong key={index}>{node.content}</strong>;
					case 'italic':
						return <em key={index}>{node.content}</em>;
					case 'code':
						return <code key={index}>{node.content}</code>;
					case 'link':
						return (
							<a key={index} href={node.url} target="_blank" rel="noopener noreferrer">
								{node.content}
							</a>
						);
					case 'linebreak':
						return <br key={index} />;
					case 'text':
					default:
						return <span key={index}>{node.content}</span>;
				}
			})}
		</div>
	);
}
