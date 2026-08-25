import React from 'react'

/** Monochrome 20px line icons — stroke follows currentColor. */
const S = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.7,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
}

const paths = {
  paper: <><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></>,
  code: <><path d="M9 18l-5-6 5-6M15 6l5 6-5 6" /></>,
  rocket: <><path d="M5 14c-1.5 1.5-2 5-2 5s3.5-.5 5-2a2.1 2.1 0 0 0-3-3z" /><path d="M13.5 6.5c3-3 6.5-3.5 7.5-3.5s.5 4.5-2.5 7.5L14 15l-5-5z" /><circle cx="15.5" cy="8.5" r="1.2" /></>,
  decode: <><rect x="3" y="10" width="18" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3M12 15v2" /></>,
  search: <><circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" /></>,
  target: <><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="3.4" /><path d="M12 2v2M12 20v2M2 12h2M20 12h2" /></>,
  scope: <><circle cx="11" cy="11" r="6" /><path d="M15.5 15.5L21 21M8.5 11h5M11 8.5v5" /></>,
  pen: <><path d="M12 20h9" /><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4z" /></>,
  wand: <><path d="M15 4V2M15 10V8M12.5 6h-2M19.5 6h-2M4 20l10-10M13.5 4.5l1-1M17.5 8.5l1-1" /></>,
  caption: <><rect x="3" y="4" width="18" height="14" rx="2.5" /><path d="M7 21l3-3M7.5 9.5h4M7.5 13h9M14.5 9.5h2" /></>,
  calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M8 3v4M16 3v4M3 10h18" /></>,
  sun: <><circle cx="12" cy="12" r="4.2" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></>,
  moon: <><path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a6.6 6.6 0 0 0 10.5 10.5z" /></>,
  chevron: <><path d="M6 9l6 6 6-6" /></>,
  lock: <><rect x="4" y="10" width="16" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></>,
  play: <><path d="M6 4l14 8-14 8z" /></>,
  stack: <><path d="M12 3l9 5-9 5-9-5 9-5z" /><path d="M3 13l9 5 9-5M3 17l9 5 9-5" /></>,
}

export default function Icon({ name, size = 18, className = '' }) {
  const d = paths[name]
  if (!d) return null
  return (
    <svg
      className={`icon ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      aria-hidden="true"
      {...S}
    >
      {d}
    </svg>
  )
}
