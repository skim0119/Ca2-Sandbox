<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import FileSelector from './components/FileSelector.vue'
import VideoDisplay from './components/VideoDisplay.vue'
import BleachingCorrection from './components/BleachingCorrection.vue'

// Application state
const selectedFiles = ref<string[]>([])
const selectedROIs = ref<number[]>([1]) // ROI 1 is selected by default
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
  smoothing: 0.5,
  fitType: 'exponential' as 'exponential' | 'inverse'
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
}

const handleBleachingUpdate = (data: Partial<typeof bleachingData>) => {
  Object.assign(bleachingData, data)
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

const handleRunAnalysis = () => {
  console.log('🚀 Analysis requested for video:', selectedFiles.value[0])
  // TODO: Implement analysis logic here
  // This could call the backend analysis API
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
            @rois-selected="handleROISelection"
            @run-analysis="handleRunAnalysis"
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
