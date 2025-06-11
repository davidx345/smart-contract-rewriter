import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  const d = new Date(date)
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export function formatGasAmount(gas: number): string {
  if (gas >= 1000000) {
    return `${(gas / 1000000).toFixed(2)}M`
  } else if (gas >= 1000) {
    return `${(gas / 1000).toFixed(1)}K`
  }
  return gas.toString()
}

export function calculateGasSavings(original: number, optimized: number): {
  absolute: number
  percentage: number
} {
  const absolute = original - optimized
  const percentage = ((absolute / original) * 100)
  return { absolute, percentage }
}

export function truncateAddress(address: string, chars = 6): string {
  if (address.length <= chars * 2) return address
  return `${address.slice(0, chars)}...${address.slice(-chars)}`
}

export function copyToClipboard(text: string): Promise<void> {
  return navigator.clipboard.writeText(text)
}

export function downloadFile(content: string, filename: string, type = 'text/plain') {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
