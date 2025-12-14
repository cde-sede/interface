export interface ConfirmDialogProps {
	message: string;
	onConfirm: () => void;
	onCancel: () => void;
}

export default function ConfirmDialog({ message, onConfirm, onCancel }: ConfirmDialogProps) {
	return (
		<div className="modal-overlay">
			<div className="modal-content confirm-dialog">
				<div className="modal-header">
					<h3>Confirm Action</h3>
				</div>
				<div className="modal-body">
					<p>{message}</p>
				</div>
				<div className="form-actions">
					<button className="action-button secondary" onClick={onCancel}>
						Cancel
					</button>
					<button className="action-button" onClick={onConfirm}>
						Confirm
					</button>
				</div>
			</div>
		</div>
	);
}
