<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import type { TracingPlotData, ROI } from '../types'
import { useResizable } from '../composables/useResizable'
import { useChartConfig } from '../composables/useChartConfig'
import { useBackendApi } from '../composables/useBackendApi'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

interface Props {
  tracingPlotData: TracingPlotData | null
  selectedFiles: string[]
  selectedROIs: number[]
  availableROIs: ROI[]
  bleachingData: {
    adjustBleaching: boolean
    smoothing: number
    analysisData?: {
      timePoints: number[]
    }
  }
}

interface Emits {
  (e: 'tracing-plot-updated', data: TracingPlotData): void
  (e: 'bleaching-updated', data: { adjustBleaching?: boolean; smoothing?: number }): void
}

const emit = defineEmits<Emits>()
const props = defineProps<Props>()

// Use the resizable composable for main plot
const { height: mainPlotHeight, isResizing: isMainResizing, handleMouseDown: handleMainMouseDown } = useResizable(400, 200, 800)

// Main plot data - computed from props
const mainChartData = computed(() => {
  if (!props.tracingPlotData) {
    return {
      labels: [] as number[],
      datasets: [] as Array<{
        label: string
        data: number[]
        borderColor: string
        backgroundColor: string
        tension: number
      }>
    }
  }

  return {
    labels: props.tracingPlotData.timePoints || [],
    datasets: props.tracingPlotData.datasets || []
  }
})

// Use the chart config composable for main chart
const { chartOptions: mainChartOptions } = useChartConfig()

const updateROITraces = async () => {
  if (!props.selectedFiles[0] || props.selectedROIs.length === 0) {
    console.log('📊 No video or ROIs selected for ROI traces')
    return
  }

  try {
    console.log('📊 Available ROIs:', props.availableROIs)
    console.log('📊 Fetching ROI traces for:', props.selectedROIs)

    // Filter available ROIs to get the selected ones with full data
    const selectedROIObjects = props.availableROIs.filter(roi =>
      props.selectedROIs.includes(roi.id)
    )
    console.log('📊 Selected ROIs:', selectedROIObjects)

    const { getROITraces } = useBackendApi()
    const result = await getROITraces(
      selectedROIObjects.map(roi => ({
        id: roi.id,
        coords: roi.coords
      })),
      props.bleachingData.smoothing
    )

    // Replace intensity trace in ROIs
    selectedROIObjects.forEach((roi) => {
      roi.intensityTrace = result.find(r => r.roiId === roi.id)?.intensityTrace
    })

    // Update the main plot data
    if (result && result.length > 0) {
      const tracingPlotData = {
        timePoints: props.bleachingData.analysisData?.timePoints || [],
        datasets: result.map((trace: { roiId: number; intensityTrace: number[] }, index: number) => ({
          label: `ROI ${trace.roiId}`,
          data: trace.intensityTrace,
          borderColor: `hsl(${index * 60}, 70%, 50%)`,
          backgroundColor: `hsla(${index * 60}, 70%, 50%, 0.1)`,
          tension: 0.1
        }))
      }

      emit('tracing-plot-updated', tracingPlotData)
    }

  } catch (error) {
    console.error('Failed to fetch ROI traces:', error)
  }
}

const handleAdjustBleachingChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('bleaching-updated', { adjustBleaching: target.checked })
}

const handleSmoothingChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('bleaching-updated', { smoothing: parseFloat(target.value) })
}

const handleSaveToCSV = () => {
  // In a real implementation, this would export the data
  console.log('Saving to CSV...')
  alert('Data saved to CSV (simulated)')
}


</script>

<template>
  <div class="intensity-tracing-plot">
    <div class="main-plot-header">
      <h3>Intensity Tracing Plot</h3>
    </div>
    <div class="plot-container" :style="{ height: mainPlotHeight + 'px' }">
      <div v-if="mainChartData.datasets.length === 0" class="empty-state">
        <div class="empty-message">No plot data available</div>
        <div class="empty-hint">Click 'Get ROI Traces' to see intensity traces</div>
      </div>
      <Line
        v-else
        :data="mainChartData"
        :options="mainChartOptions"
        class="main-chart"
      />
      <div
        class="resize-handle"
        @mousedown="handleMainMouseDown"
        :class="{ 'resizing': isMainResizing }"
      >
        <div class="resize-indicator">⋮⋮</div>
      </div>
    </div>

    <!-- Adjust Bleaching and Controls -->
    <div class="adjustment-section">
      <div class="adjustment-controls">
        <div class="adjustment-option">
          <input
            type="checkbox"
            id="adjust-bleaching"
            :checked="props.bleachingData.adjustBleaching"
            @change="handleAdjustBleachingChange"
          />
          <label for="adjust-bleaching">adjust bleaching</label>
        </div>

        <div class="smoothing-control">
          <label for="smoothing-slider">smoothing</label>
          <input
            type="range"
            id="smoothing-slider"
            min="0"
            max="1"
            step="0.1"
            :value="props.bleachingData.smoothing"
            @input="handleSmoothingChange"
            class="smoothing-slider"
          />
          <span class="smoothing-value">{{ props.bleachingData.smoothing }}</span>
        </div>

        <button @click="handleSaveToCSV" class="save-btn">
          save to CSV
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.intensity-tracing-plot {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.main-plot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.main-plot-header h3 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
  font-size: 1.1rem;
}

.get-traces-btn {
  padding: 0.5rem 1rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s;
}

.get-traces-btn:hover:not(:disabled) {
  background-color: #2980b9;
  transform: translateY(-1px);
}

.get-traces-btn:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
  transform: none;
}

.adjustment-section {
  flex: 0 0 auto;
  margin-top: 1rem;
}

.adjustment-controls {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.adjustment-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.adjustment-option input[type="checkbox"] {
  margin: 0;
}

.adjustment-option label {
  cursor: pointer;
  color: #333;
}

.smoothing-control {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.smoothing-control label {
  min-width: 60px;
  color: #333;
}

.smoothing-slider {
  flex: 1;
  height: 4px;
  border-radius: 2px;
  background: #ddd;
  outline: none;
  -webkit-appearance: none;
}

.smoothing-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #3498db;
  cursor: pointer;
}

.smoothing-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #3498db;
  cursor: pointer;
  border: none;
}

.smoothing-value {
  min-width: 30px;
  text-align: right;
  font-weight: bold;
  color: #3498db;
}

.save-btn {
  padding: 0.5rem 1rem;
  background-color: #27ae60;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: background-color 0.2s;
}

.save-btn:hover {
  background-color: #229954;
}

.plot-container {
  height: 400px;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.5rem;
  background-color: white;
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

.main-chart {
  height: 100% !important;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
  text-align: center;
}

.empty-message {
  font-size: 1.1rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #999;
}

.empty-hint {
  font-size: 0.9rem;
  color: #bbb;
}
</style>
