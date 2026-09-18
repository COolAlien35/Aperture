export default function ApertureLogo({ size = 28, showText = true, textSub = 'AI Gateway', className = '' }) {
  return (
    <div className={`aperture-brand-logo ${className}`} style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
      <svg
        width={size}
        height={Math.round(size * (46 / 48))}
        viewBox="0 0 48 46"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ flexShrink: 0 }}
      >
        <defs>
          <linearGradient id="aperture-brand-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#EF4444" />
            <stop offset="35%" stopColor="#F97316" />
            <stop offset="70%" stopColor="#EC4899" />
            <stop offset="100%" stopColor="#8B5CF6" />
          </linearGradient>
          <linearGradient id="aperture-glow-grad" x1="10%" y1="0%" x2="90%" y2="100%">
            <stop offset="0%" stopColor="#06B6D4" />
            <stop offset="100%" stopColor="#8B5CF6" />
          </linearGradient>
        </defs>
        <path
          fill="url(#aperture-brand-grad)"
          d="M25.946 44.938c-.664.845-2.021.375-2.021-.698V33.937a2.26 2.26 0 0 0-2.262-2.262H10.287c-.92 0-1.456-1.04-.92-1.788l7.48-10.471c1.07-1.497 0-3.578-1.842-3.578H1.237c-.92 0-1.456-1.04-.92-1.788L10.013.474c.214-.297.556-.474.92-.474h28.894c.92 0 1.456 1.04.92 1.788l-7.48 10.471c-1.07 1.498 0 3.579 1.842 3.579h11.377c.943 0 1.473 1.088.89 1.83L25.947 44.94z"
        />
        <circle cx="24" cy="22" r="5" fill="#08090C" opacity="0.9" />
        <circle cx="24" cy="22" r="3" fill="url(#aperture-glow-grad)" />
      </svg>
      {showText && (
        <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.1 }}>
          <div style={{
            fontFamily: 'var(--font-sans)',
            fontWeight: 800,
            fontSize: size >= 36 ? 20 : 15,
            letterSpacing: '0.8px',
            color: 'var(--text-primary)',
          }}>
            APERTURE
          </div>
          {textSub && (
            <div style={{
              fontSize: 10,
              fontWeight: 600,
              letterSpacing: '0.6px',
              textTransform: 'uppercase',
              color: 'var(--brand-primary)',
              opacity: 0.9,
            }}>
              {textSub}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
