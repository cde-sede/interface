import { useEffect, useRef, startTransition } from 'react';

export interface ConfirmDialogProps {
	message: string;
	onConfirm: () => void;
	onCancel: () => void;
}

export default function ConfirmDialog({ message, onConfirm, onCancel }: ConfirmDialogProps) {
	const dialogRef = useRef<HTMLDivElement>(null);

	useEffect(() => {
		const handleKeyDown = (e: KeyboardEvent) => {
			// Check if this dialog is the topmost modal
			const allModals = document.querySelectorAll('.modal-overlay');
			const thisModal = dialogRef.current?.parentElement;
			const topmostModal = allModals[allModals.length - 1];

			// Only handle keys if this is the topmost modal
			if (thisModal === topmostModal) {
				if (e.key === 'Enter') {
					e.preventDefault();
					e.stopImmediatePropagation();
					startTransition(() => {
						onConfirm();
					});
				} else if (e.key === 'Escape') {
					e.preventDefault();
					e.stopImmediatePropagation();
					startTransition(() => {
						onCancel();
					});
				}
			}
		};

		document.addEventListener('keydown', handleKeyDown);
		return () => document.removeEventListener('keydown', handleKeyDown);
	}, [onConfirm, onCancel]);

	return (
		<div className="modal-overlay">
			<div ref={dialogRef} className="modal-content confirm-dialog">
				<div className="modal-header">
					<h3>Confirm Action</h3>
				</div>
				<div className="modal-body">
					<p>{message}</p>
				</div>
				<div className="form-actions">
					<button className="action-button secondary" onClick={() => startTransition(() => onCancel())}>
						Cancel
					</button>
					<button className="action-button" onClick={() => startTransition(() => onConfirm())} autoFocus>
						Confirm
					</button>
				</div>
			</div>
		</div>
	);
}
