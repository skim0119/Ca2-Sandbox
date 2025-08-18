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
  bleachingData: {
    adjustBleaching: boolean
    smoothing: number
    fitType: 'exponential' | 'inverse'
    analysisData?: {
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
    }
    analysisId?: string | null
    mainPlotData?: {
      timePoints: number[]
      datasets: Array<{
        label: string
        data: number[]
        borderColor: string
        backgroundColor: string
        tension: number
      }>
    } | undefined
  }
}

interface Emits {
  (e: 'bleaching-updated', data: Partial<Props['bleachingData']>): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

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

const bleachingChartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top' as const
    },
    title: {
      display: true,
      text: 'Bleach line'
    }
  },
  scales: {
    x: {
      title: {
        display: true,
        text: 'Time (seconds)'
      }
    },
    y: {
      title: {
        display: true,
        text: 'Intensity'
      }
    }
  }
})

// Resizable plot functionality
const bleachingPlotHeight = ref(400) // Default height (2x the original ~200px)
const isResizing = ref(false)
const startY = ref(0)
const startHeight = ref(0)

const handleMouseDown = (event: MouseEvent) => {
  isResizing.value = true
  startY.value = event.clientY
  startHeight.value = bleachingPlotHeight.value
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

const handleMouseMove = (event: MouseEvent) => {
  if (!isResizing.value) return

  const deltaY = event.clientY - startY.value
  const newHeight = Math.max(200, Math.min(800, startHeight.value + deltaY)) // Min 200px, max 800px
  bleachingPlotHeight.value = newHeight
}

const handleMouseUp = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
}

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

const mainChartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top' as const
    }
  },
  scales: {
    x: {
      title: {
        display: true,
        text: 'Time (seconds)'
      }
    },
    y: {
      title: {
        display: true,
        text: 'Intensity'
      }
    }
  }
})

const handleFitTypeChange = async (type: 'exponential' | 'inverse') => {
  emit('bleaching-updated', { fitType: type })

  // Send preference to backend if we have an analysis ID
  if (props.bleachingData.analysisId) {
    try {
      const response = await fetch('/api/update-fit-preference', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          analysis_id: props.bleachingData.analysisId,
          fit_type: type
        })
      })

      if (response.ok) {
        console.log('✅ Fit preference updated:', type)
      }
    } catch (error) {
      console.error('❌ Failed to update fit preference:', error)
    }
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
          @mousedown="handleMouseDown"
          :class="{ 'resizing': isResizing }"
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
      <h3>Main Plot</h3>
      <div class="plot-container">
        <div v-if="mainChartData.datasets.length === 0" class="empty-state">
          <div class="empty-message">No plot data available</div>
          <div class="empty-hint">Run analysis to see intensity traces</div>
        </div>
        <Line
          v-else
          :data="mainChartData"
          :options="mainChartOptions"
          class="main-chart"
        />
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
