<script setup lang="ts">
import { ref, watch } from 'vue'

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
}

interface Emits {
  (e: 'rois-selected', rois: number[]): void
  (e: 'run-analysis'): void
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

// Available ROIs
const availableROIs = ref([
  { id: 1, name: 'ROI 1', color: roiColors[0] },
  { id: 2, name: 'ROI 2', color: roiColors[1] },
  { id: 3, name: 'ROI 3', color: roiColors[2] },
  { id: 4, name: 'ROI 4', color: roiColors[3] },
  { id: 5, name: 'ROI 5', color: roiColors[4] }
])

const handleROIToggle = (roiId: number) => {
  const currentSelection = [...props.selectedROIs]
  const index = currentSelection.indexOf(roiId)

  if (index > -1) {
    currentSelection.splice(index, 1)
  } else {
    currentSelection.push(roiId)
  }

  emit('rois-selected', currentSelection)
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
          <img :src="videoFrame" alt="Video frame" class="frame-image" />
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
        <div
          v-for="roi in availableROIs"
          :key="roi.id"
          :class="[
            'roi-item',
            { 'selected': selectedROIs.includes(roi.id) }
          ]"
          @click="handleROIToggle(roi.id)"
        >
          <input
            type="checkbox"
            :checked="selectedROIs.includes(roi.id)"
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
</style>
