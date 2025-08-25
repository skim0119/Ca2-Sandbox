<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import type { FirstFrameData, Coords, ROI } from '../types'

interface Props {
  firstFrameData?: FirstFrameData | null
  availableROIs: ROI[]
}

interface Emits {
  (e: 'roi-drawn', coords: Coords): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const videoFrame = ref<string>('')

// ROI drawing functionality
const isDrawing = ref(false)
const drawingStart = ref<{ x: number; y: number } | null>(null)
const currentDrawing = ref<{ x0: number; y0: number; x1: number; y1: number } | null>(null)

// Watch for first frame data from backend
watch(() => props.firstFrameData, (data) => {
  console.log('Canvas:: First frame data received:', data)
  if (data?.firstFrame) {
    // Validate base64 data
    const isValidBase64 = data.firstFrame.startsWith('data:image/') &&
                         data.firstFrame.includes('base64,')

    if (isValidBase64) {
      videoFrame.value = data.firstFrame
      console.log('Canvas:: Valid base64 image data set')
    } else {
      console.error('Canvas:: Invalid base64 data format:', data.firstFrame.substring(0, 50))
    }
  }
  else {
    videoFrame.value = ''
    console.error('Canvas:: Error: something went wrong, first frame is not received.')
  }
}, { immediate: true })

const handleMouseDown = (event: MouseEvent) => {
  if (!props.firstFrameData) return

  // Prevent default drag behavior
  event.preventDefault()
  event.stopPropagation()

  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  isDrawing.value = true
  drawingStart.value = { x, y }
  currentDrawing.value = { x0: x, y0: y, x1: x, y1: y }
}

const handleMouseMove = (event: MouseEvent) => {
  if (!isDrawing.value || !drawingStart.value || !currentDrawing.value) return

  // Prevent default drag behavior
  event.preventDefault()
  event.stopPropagation()

  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  currentDrawing.value.x1 = x
  currentDrawing.value.y1 = y
}

const handleMouseUp = async (event: MouseEvent) => {
  if (!isDrawing.value || !drawingStart.value || !currentDrawing.value) return

  // Prevent default drag behavior
  event.preventDefault()
  event.stopPropagation()

  isDrawing.value = false

  // Create ROI from drawing
  const { x0, y0, x1, y1 } = currentDrawing.value
  const coords: Coords = {
    x0: Math.min(x0, x1),
    y0: Math.min(y0, y1),
    x1: Math.max(x0, x1),
    y1: Math.max(y0, y1)
  }

  // Only create ROI if it has reasonable size
  const width = coords.x1 - coords.x0
  const height = coords.y1 - coords.y0
  if (width < 10 || height < 10) {
    drawingStart.value = null
    currentDrawing.value = null
    return
  }

  emit('roi-drawn', coords)

  drawingStart.value = null
  currentDrawing.value = null
}

// Global mouse up handler to catch mouse up events outside the canvas
const handleGlobalMouseUp = () => {
  if (isDrawing.value) {
    isDrawing.value = false
    drawingStart.value = null
    currentDrawing.value = null
  }
}

// Add and remove global event listeners
onMounted(() => {
  document.addEventListener('mouseup', handleGlobalMouseUp)
})

onUnmounted(() => {
  document.removeEventListener('mouseup', handleGlobalMouseUp)
})
</script>

<template>
  <div class="video-container" style="height: 400px;">
    <div v-if="videoFrame" class="video-frame">
      <div
        class="drawing-canvas"
        @mousedown="handleMouseDown"
        @mousemove="handleMouseMove"
        @mouseup="handleMouseUp"
      >
        <img :src="videoFrame" alt="Video frame" class="frame-image" />

        <!-- Draw current ROI box -->
        <div
          v-if="currentDrawing"
          class="drawing-box"
          :style="{
            left: Math.min(currentDrawing.x0, currentDrawing.x1) + 'px',
            top: Math.min(currentDrawing.y0, currentDrawing.y1) + 'px',
            width: Math.abs(currentDrawing.x1 - currentDrawing.x0) + 'px',
            height: Math.abs(currentDrawing.y1 - currentDrawing.y0) + 'px'
          }"
        ></div>

        <!-- Draw existing ROI boxes -->
        <div
          v-for="roi in availableROIs"
          :key="roi.id"
          class="roi-box"
          :style="{
            left: roi.coords.x0 + 'px',
            top: roi.coords.y0 + 'px',
            width: (roi.coords.x1 - roi.coords.x0) + 'px',
            height: (roi.coords.y1 - roi.coords.y0) + 'px',
            borderColor: roi.color
          }"
        >
          <span class="roi-label">{{ roi.name }}</span>
        </div>
      </div>
    </div>
    <div v-else class="video-placeholder">
      <div class="placeholder-text">No video selected</div>
    </div>
  </div>
</template>

<style scoped>
.video-container {
  flex: 1;
  border: 2px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
  background-color: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.video-frame {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.frame-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  user-select: none;
  -webkit-user-drag: none;
  -khtml-user-drag: none;
  -moz-user-drag: none;
  -o-user-drag: none;
  user-drag: none;
  pointer-events: none;
}

.drawing-canvas {
  position: relative;
  display: inline-block;
  cursor: crosshair;
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

.drawing-box {
  position: absolute;
  border: 2px dashed #3498db;
  background-color: rgba(52, 152, 219, 0.1);
  pointer-events: none;
}

.roi-box {
  position: absolute;
  border: 2px solid;
  background-color: rgba(255, 255, 255, 0.1);
  pointer-events: none;
  transition: all 0.2s ease;
}

.roi-label {
  position: absolute;
  top: -20px;
  left: 0;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 2px 6px;
  font-size: 10px;
  border-radius: 3px;
  white-space: nowrap;
}

.video-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
}

.placeholder-text {
  font-size: 1.1rem;
  color: #999;
}
</style>
