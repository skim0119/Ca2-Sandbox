<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'

interface Props {
  selectedFiles: string[]
  selectedROIs: number[]
  firstFrameData?: {
    first_frame: string;
    video_info: {
      width: number;
      height: number;
      fps: number;
      total_frames: number;
      debug_mode?: boolean;
      original_path?: string;
    }
  } | null
  bleachingSettings?: {
    adjustBleaching: boolean
    fitType: 'exponential' | 'inverse'
  }
}

interface ROI {
  id: number
  name: string
  color: string
  coords: [number, number, number, number] // [x0, y0, x1, y1]
  selected: boolean
  intensityTrace?: number[]
  timePoints?: number[]
}

interface Emits {
  (e: 'rois-selected', rois: number[]): void
  (e: 'run-analysis'): void
  (e: 'roi-created', roi: ROI): void
  (e: 'roi-updated', roi: ROI): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const currentVideo = ref<string>('')
const videoFrame = ref<string>('')

// Watch for first frame data from backend
watch(() => props.firstFrameData, (data) => {
  if (data && data.first_frame) {
    videoFrame.value = data.first_frame
    console.log('📺 Received first frame from backend:', data.video_info)

    // Log additional debug info if in debug mode
    if (data.video_info.debug_mode) {
      console.log('🔧 Debug mode detected - showing dummy frame')
      console.log('📁 Original video path:', data.video_info.original_path)
    }
  }
}, { immediate: true })

// ROI colors for different regions
const roiColors = [
  '#FF6B6B', // Red
  '#4ECDC4', // Teal
  '#45B7D1', // Blue
  '#96CEB4', // Green
  '#FFEAA7', // Yellow
  '#DDA0DD', // Plum
  '#98D8C8', // Mint
  '#F7DC6F'  // Gold
]

// Available ROIs - will be populated when analysis is run or user draws
const availableROIs = ref<ROI[]>([])

// ROI drawing functionality
const isDrawing = ref(false)
const drawingStart = ref<{ x: number; y: number } | null>(null)
const currentDrawing = ref<{ x0: number; y0: number; x1: number; y1: number } | null>(null)
const nextRoiId = ref(1)

const handleROIToggle = async (roiId: number) => {
  const currentSelection = [...props.selectedROIs]
  const index = currentSelection.indexOf(roiId)

  if (index > -1) {
    currentSelection.splice(index, 1)
    // Unselect ROI
    await handleROIUnselect(roiId)
  } else {
    currentSelection.push(roiId)
    // Select ROI
    await handleROISelect(roiId)
  }

  emit('rois-selected', currentSelection)
}

const handleROISelect = async (roiId: number) => {
  const roi = availableROIs.value.find(r => r.id === roiId)
  if (!roi) return

  try {
    const response = await fetch('/api/roi-operations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        operation: 'select',
        video_path: props.selectedFiles[0],
        roi_data: {
          id: roiId,
          selected: true
        }
      })
    })

    if (response.ok) {
      console.log('✅ ROI selected:', roiId)
      // Update ROI in list
      const roiIndex = availableROIs.value.findIndex(r => r.id === roiId)
      if (roiIndex !== -1) {
        availableROIs.value[roiIndex].selected = true
        emit('roi-updated', availableROIs.value[roiIndex])
      }
    }
  } catch (error) {
    console.error('❌ Failed to select ROI:', error)
  }
}

const handleROIUnselect = async (roiId: number) => {
  const roi = availableROIs.value.find(r => r.id === roiId)
  if (!roi) return

  try {
    const response = await fetch('/api/roi-operations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        operation: 'unselect',
        video_path: props.selectedFiles[0],
        roi_data: {
          id: roiId,
          selected: false
        }
      })
    })

    if (response.ok) {
      console.log('✅ ROI unselected:', roiId)
      // Update ROI in list
      const roiIndex = availableROIs.value.findIndex(r => r.id === roiId)
      if (roiIndex !== -1) {
        availableROIs.value[roiIndex].selected = false
        emit('roi-updated', availableROIs.value[roiIndex])
      }
    }
  } catch (error) {
    console.error('❌ Failed to unselect ROI:', error)
  }
}

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
  const coords: [number, number, number, number] = [
    Math.min(x0, x1),
    Math.min(y0, y1),
    Math.max(x0, x1),
    Math.max(y0, y1)
  ]

  // Only create ROI if it has reasonable size
  const width = coords[2] - coords[0]
  const height = coords[3] - coords[1]
  if (width < 10 || height < 10) {
    drawingStart.value = null
    currentDrawing.value = null
    return
  }

  await createROI(coords)

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

const createROI = async (coords: [number, number, number, number]) => {
  const roiId = nextRoiId.value++
  const roiColor = roiColors[(roiId - 1) % roiColors.length]

  try {
    const response = await fetch('/api/roi-operations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        operation: 'create',
        video_path: props.selectedFiles[0],
        roi_data: {
          id: roiId,
          coords: coords
        },
        adjust_bleaching: props.bleachingSettings?.adjustBleaching ?? false,
        fit_type: props.bleachingSettings?.fitType ?? 'inverse'
      })
    })

    if (response.ok) {
      const result = await response.json()
      console.log('✅ ROI created:', result)

      const newROI: ROI = {
        id: roiId,
        name: `ROI ${roiId}`,
        color: roiColor,
        coords: coords,
        selected: true,
        intensityTrace: result.intensity_trace,
        timePoints: result.time_points
      }

      availableROIs.value.push(newROI)
      emit('roi-created', newROI)
    }
  } catch (error) {
    console.error('❌ Failed to create ROI:', error)
  }
}

const handleRunAnalysis = () => {
  console.log('🚀 Running analysis for video:', currentVideo.value)
  emit('run-analysis')
}



// Watch for selected files to update current video name
watch(() => props.selectedFiles, (files) => {
  if (files.length > 0) {
    currentVideo.value = files[0]
  } else {
    currentVideo.value = ''
    videoFrame.value = ''
  }
}, { immediate: true })
</script>

<template>
  <div class="video-display">
    <!-- Video Display Section -->
    <div class="video-section">
      <div class="video-header">
        <h3>Video Display</h3>
        <button
          @click="handleRunAnalysis"
          class="run-analysis-btn"
          :disabled="!props.firstFrameData"
        >
          Run Analysis
        </button>
      </div>
      <div class="video-container">
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
              :class="{ 'selected': roi.selected }"
              :style="{
                left: roi.coords[0] + 'px',
                top: roi.coords[1] + 'px',
                width: (roi.coords[2] - roi.coords[0]) + 'px',
                height: (roi.coords[3] - roi.coords[1]) + 'px',
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
      <div class="video-info">
        <span class="video-name">{{ currentVideo || 'No file selected' }}</span>
        <div v-if="props.firstFrameData?.video_info.debug_mode" class="debug-indicator">
          🔧 Debug Mode - Backend Not Available
        </div>
      </div>
    </div>

    <!-- ROI Management Section -->
    <div class="roi-section">
      <h3>Regions of Interest</h3>
      <div class="roi-list">
        <div v-if="availableROIs.length === 0" class="empty-roi-state">
          <div class="empty-message">No ROIs available</div>
          <div class="empty-hint">Run analysis to detect ROIs</div>
        </div>
        <div
          v-else
          v-for="roi in availableROIs"
          :key="roi.id"
          :class="[
            'roi-item',
            { 'selected': roi.selected }
          ]"
          @click="handleROIToggle(roi.id)"
        >
          <input
            type="checkbox"
            :checked="roi.selected"
            @change="handleROIToggle(roi.id)"
            class="roi-checkbox"
          />
          <div
            class="roi-color-indicator"
            :style="{ backgroundColor: roi.color }"
          ></div>
          <span class="roi-name">{{ roi.name }}</span>
        </div>
      </div>

      <!-- ROI Legend -->
      <div class="roi-legend">
        <span class="legend-text">Different colors</span>
        <div class="color-samples">
          <div
            v-for="roi in availableROIs.slice(0, 3)"
            :key="roi.id"
            class="color-sample"
            :style="{ backgroundColor: roi.color }"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.video-display {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.video-display h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.1rem;
}

.video-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.run-analysis-btn {
  padding: 0.5rem 1rem;
  background-color: #27ae60;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s;
}

.run-analysis-btn:hover:not(:disabled) {
  background-color: #229954;
  transform: translateY(-1px);
}

.run-analysis-btn:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
  transform: none;
}

.video-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

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

.roi-box.selected {
  border-width: 3px;
  background-color: rgba(255, 255, 255, 0.2);
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

.video-info {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.video-name {
  font-size: 0.85rem;
  color: #666;
  word-break: break-all;
}

.debug-indicator {
  margin-top: 0.5rem;
  padding: 0.25rem 0.5rem;
  background-color: #f39c12;
  color: white;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: bold;
  text-align: center;
}

.roi-section {
  flex: 0 0 auto;
}

.roi-list {
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: #fafafa;
  max-height: 200px;
  overflow-y: auto;
}

.roi-item {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background-color 0.2s;
}

.roi-item:last-child {
  border-bottom: none;
}

.roi-item:hover {
  background-color: #f0f0f0;
}

.roi-item.selected {
  background-color: #e3f2fd;
}

.roi-checkbox {
  margin-right: 0.5rem;
}

.roi-color-indicator {
  width: 16px;
  height: 16px;
  border-radius: 3px;
  margin-right: 0.5rem;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.roi-name {
  font-size: 0.9rem;
  color: #333;
  flex: 1;
}

.roi-legend {
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #666;
}

.legend-text {
  white-space: nowrap;
}

.color-samples {
  display: flex;
  gap: 0.25rem;
}

.color-sample {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.empty-roi-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  color: #666;
  text-align: center;
}

.empty-message {
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
  color: #999;
}

.empty-hint {
  font-size: 0.75rem;
  color: #bbb;
}
</style>
