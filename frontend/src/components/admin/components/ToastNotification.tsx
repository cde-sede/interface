export interface Toast {
	id: number;
	message: string;
	type: 'success' | 'error' | 'info' | 'warning';
}

interface ToastNotificationProps {
	toasts: Toast[];
	onClose: (id: number) => void;
}

export default function ToastNotification({ toasts, onClose }: ToastNotificationProps) {
	return (
		<div className="toast-container">
			{toasts.map(toast => (
				<div key={toast.id} className={`toast toast-${toast.type}`}>
					<span className="toast-message">{toast.message}</span>
					<button className="toast-close" onClick={() => onClose(toast.id)}>
						×
					</button>
				</div>
			))}
		</div>
	);
}
