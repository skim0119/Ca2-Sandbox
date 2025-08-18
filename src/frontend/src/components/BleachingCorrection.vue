<script setup lang="ts">
import { ref } from 'vue'
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
  }
}

interface Emits {
  (e: 'bleaching-updated', data: Partial<Props['bleachingData']>): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Bleaching plot data
const bleachingChartData = ref({
  labels: Array.from({ length: 50 }, (_, i) => i),
  datasets: [
    {
      label: 'Bleach line',
      data: Array.from({ length: 50 }, (_, i) => {
        // Simulate exponential decay
        return 100 * Math.exp(-0.05 * i) + Math.random() * 5
      }),
      borderColor: '#e74c3c',
      backgroundColor: 'rgba(231, 76, 60, 0.1)',
      tension: 0.1
    }
  ]
})

const bleachingChartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
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
        text: 'time'
      }
    },
    y: {
      title: {
        display: true,
        text: 'intensity'
      }
    }
  }
})

// Main plot data
const mainChartData = ref({
  labels: Array.from({ length: 100 }, (_, i) => i),
  datasets: [
    {
      label: 'ROI 1',
      data: Array.from({ length: 100 }, (_, i) => {
        // Simulate corrected data
        return 50 + 20 * Math.sin(i * 0.1) + Math.random() * 3
      }),
      borderColor: '#FF6B6B',
      backgroundColor: 'rgba(255, 107, 107, 0.1)',
      tension: 0.1
    }
  ]
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
        text: 'Time'
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

const handleFitTypeChange = (type: 'exponential' | 'inverse') => {
  emit('bleaching-updated', { fitType: type })
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

      <div class="plot-container">
        <Line
          :data="bleachingChartData"
          :options="bleachingChartOptions"
          class="bleaching-chart"
        />
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
          <label for="inverse-fit">inverse fit</label>
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
        <Line
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
  height: 200px;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.5rem;
  background-color: white;
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
</style>
