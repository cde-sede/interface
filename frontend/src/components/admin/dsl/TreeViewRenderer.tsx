/**
 * Tree View Renderer
 *
 * DSL adapter for TreeView library component.
 */

import { useState, startTransition } from 'react';
import { TreeView } from '../../library/TreeView';
import type { TreeViewComponent, TreeNode as DSLTreeNode } from './types';
import type { ActionEngine } from './actionEngine';
import { ComponentWrapper } from './ComponentWrapper';
import { resolveValue } from './valueResolver';

interface TreeViewRendererProps {
	component: TreeViewComponent;
	pageData?: any;
	modalData?: any;
	actionEngine?: ActionEngine;
}

export default function TreeViewRenderer({ component, pageData, modalData, actionEngine }: TreeViewRendererProps) {
	const {
		nodes,
		defaultExpanded = false,
		showLines = true,
		selectable = false,
		onSelect
	} = component;

	const [_selectedNode, setSelectedNode] = useState<string | undefined>();

	const resolvedNodes = resolveValue(nodes, { pageData, data: modalData });

	// Recursively resolve tree nodes
	const resolveTreeNodes = (nodes: DSLTreeNode[]): any[] => {
		return nodes.map((node: DSLTreeNode) => ({
			id: node.id,
			label: resolveValue(node.label, { pageData, data: modalData }),
			icon: node.icon ? resolveValue(node.icon, { pageData, data: modalData }) : undefined,
			children: node.children ? resolveTreeNodes(resolveValue(node.children, { pageData, data: modalData })) : undefined,
			expanded: node.expanded,
			data: node.data,
			onClick: node.action ? () => {
				startTransition(() => {
					actionEngine?.execute(node.action!, {
						pageData,
						data: modalData,
						treeNode: node.data || node
					});
				});
			} : undefined
		}));
	};

	const handleSelect = (nodeId: string, node: any) => {
		setSelectedNode(nodeId);

		if (onSelect && actionEngine) {
			actionEngine.execute(onSelect, {
				pageData,
				data: modalData,
				treeNode: node.data || node,
				nodeId
			});
		}
	};

	const { customStyle, className: rawClassName } = component;
	const context = { pageData, data: modalData };
	const className = rawClassName ? resolveValue(rawClassName, context) : undefined;

	const treeViewElement = (
		<TreeView
			nodes={resolveTreeNodes(resolvedNodes)}
			defaultExpanded={defaultExpanded}
			showLines={showLines}
			selectable={selectable}
			onSelect={handleSelect}
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
		return treeViewElement;
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
			{treeViewElement}
		</ComponentWrapper>
	);
}
