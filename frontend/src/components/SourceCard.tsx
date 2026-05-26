interface Props {
  index:  number
  source: string
}

export default function SourceCard({ index, source }: Props) {
  const isURL = source.startsWith('http')

  const label = isURL
    ? (() => {
        try {
          return new URL(source).hostname.replace('www.', '')
        } catch {
          return source
        }
      })()
    : source.split('/').pop() || source

  return isURL ? (
    <a
      href={source}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1 text-xs px-2 py-0.5
                 rounded-full border border-brand-100 bg-brand-50
                 text-brand-800 hover:bg-brand-100 transition-colors
                 dark:border-brand-800 dark:bg-brand-900/20 dark:text-brand-200"
    >
      <span className="font-mono">[{index}]</span>
      <span className="max-w-[120px] truncate">{label}</span>
    </a>
  ) : (
    <span
      className="inline-flex items-center gap-1 text-xs px-2 py-0.5
                 rounded-full border border-gray-200 bg-gray-50
                 text-gray-600 dark:border-gray-700 dark:bg-gray-800
                 dark:text-gray-300"
      title={source}
    >
      <span className="font-mono">[{index}]</span>
      <span className="max-w-[120px] truncate">{label}</span>
    </span>
  )
}

