export default function Modal({ open, title, onClose, children, footer }) {
  if (!open) return null;
  return (
    <div
      className={`modal-overlay${open ? ' open' : ''}`}
      onClick={(e) => e.target === e.currentTarget && onClose()}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title" id="modal-title">{title}</div>
          <button
            className="btn btn-ghost btn-icon"
            onClick={onClose}
            aria-label="Close modal"
          >✕</button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
}
