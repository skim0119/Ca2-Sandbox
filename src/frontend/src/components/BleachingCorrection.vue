<script setup lang="ts">
import { ref, watch, computed } from 'vue'
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
import type { ROI, BleachingData, MainPlotData } from '../types'
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
  bleachingData: BleachingData
  selectedFiles: string[]
  selectedROIs: number[]
  availableROIs: ROI[]
}

interface Emits {
  (e: 'bleaching-updated', data: Partial<BleachingData>): void
  (e: 'main-plot-updated', data: MainPlotData): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Use the chart config composable
const { chartOptions: bleachingChartOptions } = useChartConfig('Bleach line')

// Bleaching plot data
const bleachingChartData = ref({
  labels: [] as number[],
  datasets: [] as Array<{
    label: string
    data: number[]
    borderColor: string
    backgroundColor: string
    tension: number
  }>
})

// Watch for analysis data and update chart
watch(() => props.bleachingData.analysisData, (data) => {
  if (data) {
    console.log('📊 Updating bleaching chart with analysis data')

    // Update chart with real data
    bleachingChartData.value = {
      labels: data.time_points,
      datasets: [
        {
          label: 'Raw Data',
          data: data.mean_intensity,
          borderColor: '#e74c3c',
          backgroundColor: 'rgba(231, 76, 60, 0.1)',
          tension: 0.1
        }
      ]
    }

        // Add fitted curves if available
    if (data.fit_params && data.fit_params.exponential) {
      const expParams = data.fit_params.exponential
      const expData = data.time_points.map((t: number) => expParams[0] * Math.exp(-t / expParams[1]))
      const r2Exp = data.r2_scores.exponential?.toFixed(3) || 'N/A'
      bleachingChartData.value.datasets.push({
        label: `Exponential Fit (R² = ${r2Exp})`,
        data: expData,
        borderColor: '#f39c12',
        backgroundColor: 'rgba(243, 156, 18, 0.1)',
        tension: 0.1
      })
    }

    if (data.fit_params && data.fit_params.inverse) {
      const invParams = data.fit_params.inverse
      const invData = data.time_points.map((t: number) => invParams[0] / (1 + t / invParams[1]))
      const r2Inv = data.r2_scores.inverse?.toFixed(3) || 'N/A'
      bleachingChartData.value.datasets.push({
        label: `Inverse Fit (R² = ${r2Inv})`,
        data: invData,
        borderColor: '#27ae60',
        backgroundColor: 'rgba(39, 174, 96, 0.1)',
        tension: 0.1
      })
    }
  }
}, { immediate: true })

// Use the resizable composable for both plots
const { height: bleachingPlotHeight, isResizing: isBleachingResizing, handleMouseDown: handleBleachingMouseDown } = useResizable(400, 200, 800)
const { height: mainPlotHeight, isResizing: isMainResizing, handleMouseDown: handleMainMouseDown } = useResizable(400, 200, 800)

// Main plot data - computed from props
const mainChartData = computed(() => {
  if (!props.bleachingData.mainPlotData) {
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
    labels: props.bleachingData.mainPlotData.timePoints || [],
    datasets: props.bleachingData.mainPlotData.datasets || []
  }
})

// Use the chart config composable for main chart
const { chartOptions: mainChartOptions } = useChartConfig()

const handleFitTypeChange = async (type: 'exponential' | 'inverse') => {
  emit('bleaching-updated', { fitType: type })

  // Send preference to backend if we have an analysis ID
  if (props.bleachingData.analysisId) {
    try {
      const { updateFitPreference } = useBackendApi()
      await updateFitPreference(props.bleachingData.analysisId, type)
    } catch (error) {
      console.error('❌ Failed to update fit preference:', error)
    }
  }
}

const handleGetROITraces = async () => {
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

    // Update the main plot data
    if (result.traces && result.traces.length > 0) {
      const mainPlotData = {
        timePoints: result.traces[0].time_points,
        datasets: result.traces.map((trace: { roi_id: number; intensity_trace: number[] }, index: number) => ({
          label: `ROI ${trace.roi_id}`,
          data: trace.intensity_trace,
          borderColor: `hsl(${index * 60}, 70%, 50%)`,
          backgroundColor: `hsla(${index * 60}, 70%, 50%, 0.1)`,
          tension: 0.1
        }))
      }

      emit('main-plot-updated', mainPlotData)
    }

  } catch (error) {
    console.error('❌ Failed to fetch ROI traces:', error)
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
  <div class="bleaching-correction">
    <!-- Bleaching Plot and Fit Options -->
    <div class="bleaching-plot-section">
      <h3>Bleaching Analysis</h3>

      <div class="plot-container" :style="{ height: bleachingPlotHeight + 'px' }">
        <div v-if="bleachingChartData.datasets.length === 0" class="empty-state">
          <div class="empty-message">No bleaching data available</div>
          <div class="empty-hint">Run analysis to see bleaching trends</div>
        </div>
        <Line
          v-else
          :data="bleachingChartData"
          :options="bleachingChartOptions"
          class="bleaching-chart"
        />
        <div
          class="resize-handle"
          @mousedown="handleBleachingMouseDown"
          :class="{ 'resizing': isBleachingResizing }"
        >
          <div class="resize-indicator">⋮⋮</div>
        </div>
      </div>

      <div class="fit-options">
        <div class="fit-option">
          <input
            type="checkbox"
            id="exponential-fit"
            :checked="props.bleachingData.fitType === 'exponential'"
            @change="handleFitTypeChange('exponential')"
          />
          <label for="exponential-fit">exponential fit</label>
        </div>
        <div class="fit-option">
          <input
            type="checkbox"
            id="inverse-fit"
            :checked="props.bleachingData.fitType === 'inverse'"
            @change="handleFitTypeChange('inverse')"
          />
          <label for="inverse-fit">inverse fit (default)</label>
        </div>
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

    <!-- Main Plot -->
    <div class="main-plot-section">
      <div class="main-plot-header">
        <h3>Main Plot</h3>
        <button
          @click="handleGetROITraces"
          class="get-traces-btn"
          :disabled="!props.selectedFiles[0] || props.selectedROIs.length === 0"
          title="Fetch ROI intensity traces from the backend"
        >
          Get ROI Traces
        </button>
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
    </div>
  </div>
</template>

<style scoped>
.bleaching-correction {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.bleaching-correction h3 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
  font-size: 1.1rem;
}

.main-plot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
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

.bleaching-plot-section {
  flex: 0 0 auto;
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

.bleaching-chart {
  height: 100% !important;
}

.fit-options {
  margin-top: 0.5rem;
  display: flex;
  gap: 1rem;
}

.fit-option {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.85rem;
}

.fit-option input[type="checkbox"] {
  margin: 0;
}

.fit-option label {
  cursor: pointer;
  color: #333;
}

.adjustment-section {
  flex: 0 0 auto;
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

.main-plot-section {
  flex: 1;
  display: flex;
  flex-direction: column;
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
