import { Reveal } from './ui'

// Section panel with header (reference .panel / .panel-head).
export function Panel({
  title,
  tools,
  children,
  className = '',
}: {
  title?: React.ReactNode
  tools?: React.ReactNode
  children: React.ReactNode
  className?: string
}) {
  return (
    <Reveal as="section" className={`panel ${className}`} index={0}>
      {title != null && (
        <div className="panel-head">
          <h2>{title}</h2>
          <div className="spacer" />
          {tools}
        </div>
      )}
      {children}
    </Reveal>
  )
}
