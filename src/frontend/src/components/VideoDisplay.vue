<script setup lang="ts">
import { ref, watch } from 'vue'
import VideoCanvas from './VideoCanvas.vue'
import ROIList from './ROIList.vue'
import AutoROIConfig from './AutoROIConfig.vue'
import { useROIOperations } from '../composables/useROIOperations'
import type { ROI, AutoROIConfig as AutoROIConfigType, FirstFrameData, BleachingSettings, Coords } from '../types'

interface Props {
  selectedFiles: string[]
  selectedROIs: number[]
  firstFrameData?: FirstFrameData | null
  bleachingSettings?: BleachingSettings
}

interface Emits {
  (e: 'rois-selected', rois: number[]): void
  (e: 'run-analysis'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const currentVideo = ref<string>('')

// Use the ROI operations composable
const {
  availableROIs,
  isAutoROIRunning,
  createROI,
  selectROI,
  unselectROI,
  runAutoROI
} = useROIOperations()

// Auto ROI configuration
const autoROIConfig = ref<AutoROIConfigType>({
  thresholdPercentage: 99.0,
  minDistancePercentage: 0.01,
  nClusters: 3
})

const handleROIDrawn = async (coords: Coords) => {
  await createROI(coords, props.selectedFiles[0], props.bleachingSettings)
}

const handleROIToggle = async (roiId: number) => {
  const currentSelection = [...props.selectedROIs]
  const index = currentSelection.indexOf(roiId)

  if (index > -1) {
    currentSelection.splice(index, 1)
    // Unselect ROI
    await unselectROI(roiId)
  } else {
    currentSelection.push(roiId)
    // Select ROI
    await selectROI(roiId)
  }

  emit('rois-selected', currentSelection)
}

const handleAutoROIConfigUpdated = (config: AutoROIConfigType) => {
  autoROIConfig.value = config
}

const handleRunAutoROI = async () => {
  const newROICoordss = await runAutoROI(autoROIConfig.value)
  newROICoordss.forEach(coords => createROI(coords, props.selectedFiles[0], props.bleachingSettings))
}

const handleRunAnalysis = () => {
  console.log('Running analysis for video:', currentVideo.value)
  emit('run-analysis')
}

// Watch for selected files to update current video name
watch(() => props.selectedFiles, (files) => {
  if (files.length > 0) {
    currentVideo.value = files[0]
  } else {
    currentVideo.value = ''
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

      <VideoCanvas
        :first-frame-data="props.firstFrameData"
        :available-r-o-is="availableROIs"
        @roi-drawn="handleROIDrawn"
      />

      <div class="video-info">
        <span class="video-name">{{ currentVideo || 'No file selected' }}</span>
        <div v-if="props.firstFrameData?.videoInfo.debugMode" class="debug-indicator">
          🔧 Debug Mode - Backend Not Available
        </div>
      </div>
    </div>

    <!-- ROI Management Section -->
    <div class="roi-section">
      <div class="roi-header">
        <h3>Regions of Interest</h3>
      </div>

      <div class="roi-content">
        <!-- ROI List -->
        <ROIList
          :available-r-o-is="availableROIs"
          :selected-r-o-is="props.selectedROIs"
          @roi-toggle="handleROIToggle"
        />

        <!-- Auto ROI Configuration Panel -->
        <AutoROIConfig
          :config="autoROIConfig"
          :is-running="isAutoROIRunning"
          @config-updated="handleAutoROIConfigUpdated"
          @run-auto-roi="handleRunAutoROI"
        />
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

.roi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.roi-content {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.5rem;
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
