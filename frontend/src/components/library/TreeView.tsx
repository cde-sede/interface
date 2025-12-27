/**
 * TreeView Component
 *
 * Hierarchical tree view for displaying nested data.
 */

import { useState } from 'react';
import { cn } from './utils';
import type { BaseComponentProps } from './types';
import './TreeView.css';

export interface TreeNode {
	id: string;            /** Unique node ID */
	label: string;         /** Node label */
	icon?: string;         /** Optional icon */
	children?: TreeNode[]; /** Child nodes */
	expanded?: boolean;    /** Initially expanded */
	onClick?: () => void;  /** Click handler */
	data?: any;            /** Additional data */
}

export interface TreeViewProps extends BaseComponentProps {
	nodes: TreeNode[];                                   /** Tree nodes */
	defaultExpanded?: boolean;                           /** Default expanded state */
	showLines?: boolean;                                 /** Show connecting lines */
	selectable?: boolean;                                /** Enable selection */
	onSelect?: (nodeId: string, node: TreeNode) => void; /** Selection handler */
}

interface TreeNodeRendererProps {
	node: TreeNode;
	level: number;
	defaultExpanded?: boolean;
	showLines?: boolean;
	selectable?: boolean;
	selectedNode?: string;
	onSelect?: (nodeId: string, node: TreeNode) => void;
}

function TreeNodeRenderer({
	node,
	level,
	defaultExpanded,
	showLines,
	selectable,
	selectedNode,
	onSelect
}: TreeNodeRendererProps) {
	const [isExpanded, setIsExpanded] = useState(node.expanded ?? defaultExpanded ?? false);

	const hasChildren = node.children && node.children.length > 0;
	const isSelected = selectable && selectedNode === node.id;

	const handleToggle = () => {
		setIsExpanded(!isExpanded);
	};

	const handleClick = () => {
		if (selectable && onSelect)
			onSelect(node.id, node);
		node.onClick?.();
	};

	const contentClassName = cn(
		'lib-tree-node-content',
		isSelected && 'lib-tree-node-selected'
	);

	const nodeClassName = cn(
		'lib-tree-node',
		selectable && 'lib-tree-node-selectable'
	);

	return (
		<div className={nodeClassName}>
			<div className={contentClassName} onClick={handleClick}>
				{Array.from({ length: level }).map((_, i) => (
					<span key={i} className="lib-tree-node-spacer" />
				))}
				{hasChildren ? (
					<button
						className={cn('lib-tree-node-toggle', isExpanded && 'lib-tree-node-expanded')}
						onClick={(e) => {
							e.stopPropagation();
							handleToggle();
						}}
						type="button"
					>
						▶
					</button>
				) : (
					<span className="lib-tree-node-spacer" />
				)}
				<div className="lib-tree-node-label">
					{node.icon && <span className="lib-tree-node-icon">{node.icon}</span>}
					<span>{node.label}</span>
				</div>
			</div>
			{hasChildren && isExpanded && (
				<div className="lib-tree-node-children">
					{node.children!.map((child) => (
						<TreeNodeRenderer
							key={child.id}
							node={child}
							level={level + 1}
							defaultExpanded={defaultExpanded}
							showLines={showLines}
							selectable={selectable}
							selectedNode={selectedNode}
							onSelect={onSelect}
						/>
					))}
				</div>
			)}
		</div>
	);
}

export function TreeView({
	nodes,
	defaultExpanded = false,
	showLines = false,
	selectable = false,
	onSelect,
	className,
	style,
	'data-testid': dataTestId
}: TreeViewProps) {
	const [selectedNode, setSelectedNode] = useState<string>();

	const handleSelect = (nodeId: string, node: TreeNode) => {
		setSelectedNode(nodeId);
		onSelect?.(nodeId, node);
	};

	return (
		<div
			className={cn('lib-tree-view', className)}
			style={style}
			data-testid={dataTestId}
		>
			{nodes.map((node) => (
				<TreeNodeRenderer
					key={node.id}
					node={node}
					level={0}
					defaultExpanded={defaultExpanded}
					showLines={showLines}
					selectable={selectable}
					selectedNode={selectedNode}
					onSelect={handleSelect}
				/>
			))}
		</div>
	);
}
