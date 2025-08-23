import { ref } from 'vue'

export function useResizable(initialHeight: number, minHeight = 200, maxHeight = 800) {
  const height = ref(initialHeight)
  const isResizing = ref(false)
  const startY = ref(0)
  const startHeight = ref(0)

  const handleMouseDown = (event: MouseEvent) => {
    isResizing.value = true
    startY.value = event.clientY
    startHeight.value = height.value
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }

  const handleMouseMove = (event: MouseEvent) => {
    if (!isResizing.value) return
    const deltaY = event.clientY - startY.value
    const newHeight = Math.max(minHeight, Math.min(maxHeight, startHeight.value + deltaY))
    height.value = newHeight
  }

  const handleMouseUp = () => {
    isResizing.value = false
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
  }

  return {
    height,
    isResizing,
    handleMouseDown
  }
}
