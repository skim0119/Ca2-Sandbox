<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import FileSelector from './components/FileSelector.vue'
import VideoDisplay from './components/VideoDisplay.vue'
import BleachingCorrection from './components/BleachingCorrection.vue'
import { useROIOperations } from './composables/useROIOperations'
import { useBackendApi } from './composables/useBackendApi'
import type { BleachingData, FirstFrameData } from './types'

// Application state
const selectedFiles = ref<string[]>([])

// ROI operations composable to access available ROIs
const { availableROIs, selectedROIs } = useROIOperations()
const backendVersion = ref<string>('...')
const firstFrameData = ref<FirstFrameData | null>(null)
const bleachingData = reactive<BleachingData>({
  adjustBleaching:true,
  smoothing: 0.0,
  fitType: 'inverse',
  analysisData: undefined,
  analysisId: null,
  mainPlotData: undefined
})

const fetchBackendVersion = async () => {
  const { getBackendVersion } = useBackendApi()
  backendVersion.value = await getBackendVersion()
}

onMounted(() => {
  fetchBackendVersion()
})

const handleFileSelection = (files: string[]) => {
  selectedFiles.value = files
}

const handleROISelection = (rois: number[]) => {
  selectedROIs.value = rois
}

const handleBleachingUpdate = (data: Partial<typeof bleachingData>) => {
  Object.assign(bleachingData, data)
}

const handleFirstFrameReceived = (data: FirstFrameData | null) => {
  console.log('First frame received:', data)
  firstFrameData.value = data
}

const handleRunAnalysis = async () => {
  if (!selectedFiles.value[0]) {
    console.error('No video selected for analysis')
    return
  }

  console.log('Analysis requested for video:', selectedFiles.value[0])

  try {
    const { runAnalysis } = useBackendApi()
    const result = await runAnalysis(selectedFiles.value[0])

    // Pass the analysis data to the bleaching correction component
    bleachingData.analysisData = result.bleaching_data
    bleachingData.analysisId = result.analysis_id

  } catch (error) {
    console.error('Analysis failed:', error)
  }
}

const handleMainPlotUpdate = (mainPlotData: BleachingData['mainPlotData']) => {
  console.log('📊 Main plot updated from button:', mainPlotData)
  bleachingData.mainPlotData = mainPlotData
}


</script>

<template>
  <div class="app">
    <header class="app-header">
      <h1 style="text-align: left; margin: 0;">MiV - CA2 Sandbox V 0.0.41 (backend: {{ backendVersion }})</h1>
    </header>


    <main class="app-main">
      <!-- Left Column: File Selection -->
      <div class="column file-selection">
        <FileSelector
          :selected-files="selectedFiles"
          @files-selected="handleFileSelection"
          @first-frame-received="handleFirstFrameReceived"
        />
      </div>

              <!-- Middle Column: Video Display and ROI Management -->
        <div class="column video-display">
          <VideoDisplay
            :selected-files="selectedFiles"
            :selectedROIs="selectedROIs"
            :first-frame-data="firstFrameData"
            :bleaching-settings="{
              adjustBleaching: bleachingData.adjustBleaching,
              fitType: bleachingData.fitType,
              smoothing: bleachingData.smoothing
            }"
            @rois-selected="handleROISelection"
            @run-analysis="handleRunAnalysis"
          />
        </div>

      <!-- Right Column: Bleaching Correction and Plotting -->
      <div class="column bleaching-correction">
        <BleachingCorrection
          :bleaching-data="bleachingData"
          :selected-files="selectedFiles"
          :selected-r-o-is="selectedROIs"
          :available-r-o-is="availableROIs"
          @bleaching-updated="handleBleachingUpdate"
          @main-plot-updated="handleMainPlotUpdate"
        />
      </div>
    </main>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
}

.app-header {
  background-color: #2c3e50;
  color: white;
  padding: 1rem 2rem;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.app-main {
  flex: 1;
  display: flex;
  gap: 1rem;
  padding: 1rem;
  height: calc(100vh - 80px);
}

.column {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 1rem;
  overflow: hidden;
}

.file-selection {
  flex: 0 0 250px;
}

.video-display {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.bleaching-correction {
  flex: 0 0 350px;
}

@media (max-width: 1200px) {
  .app-main {
    flex-direction: column;
    height: auto;
  }

  .file-selection,
  .bleaching-correction {
    flex: none;
  }
}
</style>
