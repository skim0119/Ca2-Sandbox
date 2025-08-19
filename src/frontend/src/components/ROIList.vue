<script setup lang="ts">
import { ref } from 'vue'

interface ROI {
  id: number
  name: string
  color: string
  coords: [number, number, number, number]
  selected: boolean
  intensityTrace?: number[]
  timePoints?: number[]
}

interface Props {
  availableROIs: ROI[]
  selectedROIs: number[]
}

interface Emits {
  (e: 'roi-toggle', roiId: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Resizable ROI table functionality
const roiTableHeight = ref(200) // Default height
const isResizing = ref(false)
const startY = ref(0)
const startHeight = ref(0)

const handleResizeMouseDown = (event: MouseEvent) => {
  isResizing.value = true
  startY.value = event.clientY
  startHeight.value = roiTableHeight.value
  document.addEventListener('mousemove', handleResizeMouseMove)
  document.addEventListener('mouseup', handleResizeMouseUp)
}

const handleResizeMouseMove = (event: MouseEvent) => {
  if (!isResizing.value) return

  const deltaY = event.clientY - startY.value
  const newHeight = Math.max(100, Math.min(400, startHeight.value + deltaY)) // Min 100px, max 400px
  roiTableHeight.value = newHeight
}

const handleResizeMouseUp = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', handleResizeMouseMove)
  document.removeEventListener('mouseup', handleResizeMouseUp)
}

const handleROIToggle = (roiId: number) => {
  emit('roi-toggle', roiId)
}
</script>

<template>
  <div class="roi-list-container">
    <div class="roi-list" :style="{ height: roiTableHeight + 'px' }">
      <div v-if="availableROIs.length === 0" class="empty-roi-state">
        <div class="empty-message">No ROIs available</div>
        <div class="empty-hint">Draw ROIs on the video or run auto ROI detection</div>
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
      <div
        class="resize-handle"
        @mousedown="handleResizeMouseDown"
        :class="{ 'resizing': isResizing }"
      >
        <div class="resize-indicator">⋮⋮</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.roi-list-container {
  flex: 2;
}

.roi-list {
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: #fafafa;
  overflow-y: auto;
  position: relative;
  transition: height 0.1s ease;
}

.resize-handle {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 8px;
  background: linear-gradient(to bottom, transparent, rgba(0, 0, 0, 0.1));
  cursor: ns-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0 0 4px 4px;
  transition: background-color 0.2s ease;
}

.resize-handle:hover {
  background: linear-gradient(to bottom, transparent, rgba(0, 0, 0, 0.2));
}

.resize-handle.resizing {
  background: linear-gradient(to bottom, transparent, rgba(52, 152, 219, 0.3));
}

.resize-indicator {
  font-size: 12px;
  color: #666;
  user-select: none;
  pointer-events: none;
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
