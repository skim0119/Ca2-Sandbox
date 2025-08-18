<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import FileSelector from './components/FileSelector.vue'
import VideoDisplay from './components/VideoDisplay.vue'
import BleachingCorrection from './components/BleachingCorrection.vue'

// Application state
const selectedFiles = ref<string[]>([])
const selectedROIs = ref<number[]>([]) // No ROIs selected by default
const backendVersion = ref<string>('...')
const firstFrameData = ref<{
  first_frame: string;
  video_info: {
    width: number;
    height: number;
    fps: number;
    total_frames: number;
    debug_mode?: boolean;
    original_path?: string;
  }
} | null>(null)
const bleachingData = reactive({
  adjustBleaching: true,
  smoothing: 0.0,
  fitType: 'inverse' as 'exponential' | 'inverse',
  analysisData: undefined as {
    time_points: number[]
    mean_intensity: number[]
    fit_params: {
      exponential?: number[]
      inverse?: number[]
    }
    r2_scores: {
      exponential?: number
      inverse?: number
    }
  } | undefined,
  analysisId: null as string | null,
  mainPlotData: undefined as {
    timePoints: number[]
    datasets: Array<{
      label: string
      data: number[]
      borderColor: string
      backgroundColor: string
      tension: number
    }>
  } | undefined
})

const fetchBackendVersion = async () => {
  try {
    const response = await fetch('/api/version')
    if (response.ok) {
      const data = await response.json()
      backendVersion.value = data.version
    } else {
      backendVersion.value = 'dev mode'
    }
  } catch {
    console.log('Backend not available, running in dev mode')
    backendVersion.value = 'dev mode'
  }
}

onMounted(() => {
  fetchBackendVersion()
})

const handleFileSelection = (files: string[]) => {
  selectedFiles.value = files
}

const handleROISelection = (rois: number[]) => {
  selectedROIs.value = rois
  // Update main plot when ROI selection changes
  updateMainPlot()
}

const handleBleachingUpdate = (data: Partial<typeof bleachingData>) => {
  Object.assign(bleachingData, data)
  
  // Update main plot when bleaching settings change (especially smoothing)
  if (data.smoothing !== undefined || data.adjustBleaching !== undefined || data.fitType !== undefined) {
    updateMainPlot()
  }
}

const handleFirstFrameReceived = (data: {
  first_frame: string;
  video_info: {
    width: number;
    height: number;
    fps: number;
    total_frames: number;
    debug_mode?: boolean;
    original_path?: string;
  }
}) => {
  firstFrameData.value = data
}

const handleRunAnalysis = async () => {
  if (!selectedFiles.value[0]) {
    console.error('No video selected for analysis')
    return
  }

  console.log('🚀 Analysis requested for video:', selectedFiles.value[0])

  try {
    const response = await fetch('/api/run-analysis', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        video_path: selectedFiles.value[0]
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    console.log('✅ Analysis completed:', result)

    // Pass the analysis data to the bleaching correction component
    bleachingData.analysisData = result.bleaching_data
    bleachingData.analysisId = result.analysis_id

  } catch (error) {
    console.error('❌ Analysis failed:', error)
    // Create dummy analysis data for debugging
    bleachingData.analysisData = createDummyAnalysisData()
    bleachingData.analysisId = 'dummy_analysis'
  }
}

interface ROI {
  id: number
  name: string
  color: string
  coords: [number, number, number, number]
  selected: boolean
  intensityTrace?: number[]
  timePoints?: number[]
}

const handleROICreated = (roi: ROI) => {
  console.log('🎯 ROI created:', roi)
  // Update main plot with new ROI intensity trace
  updateMainPlot()
}

const handleROIUpdated = (roi: ROI) => {
  console.log('🔄 ROI updated:', roi)
  // Update main plot when ROI selection changes
  updateMainPlot()
}

const updateMainPlot = async () => {
  if (!selectedFiles.value[0] || selectedROIs.value.length === 0) {
    console.log('📊 No video or ROIs selected for main plot update')
    return
  }

  try {
    console.log('📊 Updating main plot with ROI data:', selectedROIs.value)
    
    const response = await fetch('/api/get-roi-traces', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        video_path: selectedFiles.value[0],
        roi_ids: selectedROIs.value,
        smoothing: bleachingData.smoothing,
        adjust_bleaching: bleachingData.adjustBleaching,
        fit_type: bleachingData.fitType
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    console.log('✅ ROI traces received:', result)

    // Update the main plot data in bleachingData
    if (result.traces && result.traces.length > 0) {
      bleachingData.mainPlotData = {
        timePoints: result.traces[0].time_points,
        datasets: result.traces.map((trace: { roi_id: number; intensity_trace: number[] }, index: number) => ({
          label: `ROI ${trace.roi_id}`,
          data: trace.intensity_trace,
          borderColor: `hsl(${index * 60}, 70%, 50%)`,
          backgroundColor: `hsla(${index * 60}, 70%, 50%, 0.1)`,
          tension: 0.1
        }))
      }
    }

  } catch (error) {
    console.error('❌ Failed to update main plot:', error)
  }
}

const createDummyAnalysisData = () => {
  // Create dummy bleaching data for debugging
  const timePoints = Array.from({ length: 100 }, (_, i) => i * 0.1)
  const meanIntensity = timePoints.map(t => 100 * Math.exp(-0.05 * t) + Math.random() * 5)

  return {
    time_points: timePoints,
    mean_intensity: meanIntensity,
    fit_params: {
      exponential: [100.0, 20.0],
      inverse: [100.0, 15.0]
    },
    r2_scores: {
      exponential: 0.985,
      inverse: 0.992
    },
    video_info: {
      width: 640,
      height: 480,
      fps: 30.0,
      total_frames: 100
    }
  }
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
            @roi-created="handleROICreated"
            @roi-updated="handleROIUpdated"
          />
        </div>

      <!-- Right Column: Bleaching Correction and Plotting -->
      <div class="column bleaching-correction">
        <BleachingCorrection
          :bleaching-data="bleachingData"
          @bleaching-updated="handleBleachingUpdate"
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
