import { useCallback, useEffect, useState } from 'react'

/**
 * Theme is 'system' | 'light' | 'dark'. 'system' leaves data-theme off the root
 * so the prefers-color-scheme media query decides; the other two pin it.
 */
const KEY = 'gs-theme'

export function useTheme() {
  const [theme, setTheme] = useState(() => localStorage.getItem(KEY) || 'system')
  const [systemDark, setSystemDark] = useState(
    () => window.matchMedia('(prefers-color-scheme: dark)').matches,
  )

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const on = (e) => setSystemDark(e.matches)
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [])

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'system') root.removeAttribute('data-theme')
    else root.setAttribute('data-theme', theme)
    localStorage.setItem(KEY, theme)
  }, [theme])

  const isDark = theme === 'dark' || (theme === 'system' && systemDark)

  // Click cycles to the opposite of what you're currently seeing, and only
  // returns to 'system' if that happens to match.
  const toggle = useCallback(() => {
    setTheme(isDark ? 'light' : 'dark')
  }, [isDark])

  return { theme, isDark, setTheme, toggle }
}
