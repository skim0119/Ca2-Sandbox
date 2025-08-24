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
import type { MainPlotData } from '../types'
import { useResizable } from '../composables/useResizable'
import { useChartConfig } from '../composables/useChartConfig'

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
  mainPlotData: MainPlotData | null
}

const props = defineProps<Props>()

// Use the resizable composable for main plot
const { height: mainPlotHeight, isResizing: isMainResizing, handleMouseDown: handleMainMouseDown } = useResizable(400, 200, 800)

// Main plot data - computed from props
const mainChartData = computed(() => {
  if (!props.mainPlotData) {
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
    labels: props.mainPlotData.timePoints || [],
    datasets: props.mainPlotData.datasets || []
  }
})

// Use the chart config composable for main chart
const { chartOptions: mainChartOptions } = useChartConfig()
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
