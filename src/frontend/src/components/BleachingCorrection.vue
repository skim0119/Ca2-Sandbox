<script setup lang="ts">
import { ref, watch } from 'vue'
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
import type { BleachingData } from '../types'
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
}

interface Emits {
  (e: 'bleaching-updated', data: Partial<BleachingData>): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Use the chart config composable
const { chartOptions: bleachingChartOptions } = useChartConfig('Photobleaching trend')

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
  if (!data) {
    console.log('Bleaching Correction:: No analysis data available')
    return
  }
  console.log('Bleaching Correction:: Updating bleaching chart with analysis data')

  // Update chart with real data
  bleachingChartData.value = {
    labels: data.timePoints,
    datasets: [
      {
        label: 'Raw Data',
        data: data.meanIntensity,
        borderColor: '#e74c3c',
        backgroundColor: 'rgba(231, 76, 60, 0.1)',
        tension: 0.1
      }
    ]
  }

  // Add fitted curves if available
  if (data.fitParams && data.fitParams.exponential) {
    const expParams = data.fitParams.exponential
    const expData = data.timePoints.map((t: number) => expParams[0] * Math.exp(-t / expParams[1]))
    const r2Exp = data.r2Scores.exponential?.toFixed(3) || 'N/A'
    bleachingChartData.value.datasets.push({
      label: `Exponential Fit (R² = ${r2Exp})`,
      data: expData,
      borderColor: '#f39c12',
      backgroundColor: 'rgba(243, 156, 18, 0.1)',
      tension: 0.1
    })
  }

  if (data.fitParams && data.fitParams.inverse) {
    const invParams = data.fitParams.inverse
    const invData = data.timePoints.map((t: number) => invParams[0] / (1 + t / invParams[1]))
    const r2Inv = data.r2Scores.inverse?.toFixed(3) || 'N/A'
    bleachingChartData.value.datasets.push({
      label: `Inverse Fit (R² = ${r2Inv})`,
      data: invData,
      borderColor: '#27ae60',
      backgroundColor: 'rgba(39, 174, 96, 0.1)',
      tension: 0.1
    })
  }
}, { immediate: true })

// Use the resizable composable for bleaching plot
const { height: bleachingPlotHeight, isResizing: isBleachingResizing, handleMouseDown: handleBleachingMouseDown } = useResizable(400, 200, 800)

const handleFitTypeChange = async (type: 'exponential' | 'inverse') => {
  emit('bleaching-updated', { fitType: type })

  // Send preference to backend if we have an analysis ID
  if (props.bleachingData.analysisId) {
    try {
      const { updateFitPreference } = useBackendApi()
      await updateFitPreference(props.bleachingData.analysisId, type)
    } catch (error) {
      console.error('Failed to update fit preference:', error)
    }
  }
}




</script>

<template>
  <div class="bleaching-correction">
    <!-- Bleaching Plot and Fit Options -->
    <div class="bleaching-plot-section">
      <h3>Bleaching Analysis</h3>

      <!-- Bleaching Plot -->
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

    <!-- Fit Options -->
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

  </div>
</template>

<style scoped>
.bleaching-correction {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
}

.bleaching-correction h3 {
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
