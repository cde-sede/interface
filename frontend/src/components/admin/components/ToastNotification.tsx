import { startTransition } from 'react';
import type { RichTextComponent } from '../dsl/types';
import RichTextRenderer from '../dsl/RichTextRenderer';

export interface Toast {
	id: number;
	message: string | RichTextComponent;
	type: 'success' | 'error' | 'info' | 'warning';
}

interface ToastNotificationProps {
	toasts: Toast[];
	onClose: (id: number) => void;
}

export default function ToastNotification({ toasts, onClose }: ToastNotificationProps) {
	return (
		<div className="toast-container">
			{toasts.map(toast => {
				const isRichText = typeof toast.message === 'object' && toast.message.type === 'rich-text';

				return (
					<div key={toast.id} className={`toast toast-${toast.type}`}>
						<span className="toast-message">
							{isRichText ? (
								<RichTextRenderer
									component={toast.message as RichTextComponent}
									pageData={undefined}
									modalData={undefined}
									actionEngine={undefined}
								/>
							) : (
								toast.message as string
							)}
						</span>
						<button className="toast-close" onClick={() => startTransition(() => onClose(toast.id))}>
							×
						</button>
					</div>
				);
			})}
		</div>
	);
}
