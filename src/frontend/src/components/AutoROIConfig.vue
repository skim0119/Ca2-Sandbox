<script setup lang="ts">
interface Props {
  config: {
    thresholdPercentage: number
    minDistancePercentage: number
    nClusters: number
  }
  isRunning: boolean
}

interface Emits {
  (e: 'config-updated', config: {
    thresholdPercentage: number
    minDistancePercentage: number
    nClusters: number
  }): void
  (e: 'run-auto-roi'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const updateConfig = (key: keyof typeof props.config, value: number) => {
  const newConfig = { ...props.config, [key]: value }
  emit('config-updated', newConfig)
}

const handleRunAutoROI = () => {
  emit('run-auto-roi')
}
</script>

<template>
  <div class="auto-roi-config">
    <h4>Auto ROI Settings</h4>

    <div class="config-item">
      <label for="threshold-slider" title="Percentile threshold for fluctuation map. Higher values (99%+) are more selective and detect fewer, stronger ROIs. Lower values (90-95%) detect more ROIs but may include noise.">
        Threshold (%)
      </label>
      <input
        type="range"
        id="threshold-slider"
        min="90"
        max="99.9"
        step="0.1"
        :value="config.thresholdPercentage"
        @input="(e) => updateConfig('thresholdPercentage', parseFloat((e.target as HTMLInputElement).value))"
        class="config-slider"
      />
      <span class="config-value">{{ config.thresholdPercentage.toFixed(1) }}%</span>
    </div>

    <div class="config-item">
      <label for="distance-slider" title="Minimum distance between ROI centers as percentage of image width. Higher values prevent overlapping ROIs. Lower values allow closer ROIs.">
        Min Distance (%)
      </label>
      <input
        type="range"
        id="distance-slider"
        min="0.001"
        max="0.05"
        step="0.001"
        :value="config.minDistancePercentage"
        @input="(e) => updateConfig('minDistancePercentage', parseFloat((e.target as HTMLInputElement).value))"
        class="config-slider"
      />
      <span class="config-value">{{ (config.minDistancePercentage * 100).toFixed(1) }}%</span>
    </div>

    <div class="config-item">
      <label for="clusters-slider" title="Number of clusters for grouping similar ROI intensity traces. Higher values create more distinct groups. Lower values group more ROIs together.">
        Clusters
      </label>
      <input
        type="range"
        id="clusters-slider"
        min="1"
        max="20"
        step="1"
        :value="config.nClusters"
        @input="(e) => updateConfig('nClusters', parseInt((e.target as HTMLInputElement).value))"
        class="config-slider"
      />
      <span class="config-value">{{ config.nClusters }}</span>
    </div>

    <button
      @click="handleRunAutoROI"
      class="auto-roi-btn"
      :disabled="isRunning"
      title="Automatically detect regions of interest based on fluctuation analysis. Higher threshold = more selective detection."
    >
      {{ isRunning ? 'Detecting...' : 'Auto ROI' }}
    </button>
  </div>
</template>

<style scoped>
.auto-roi-config {
  flex: 1;
  padding: 1rem;
  background-color: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.auto-roi-config h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1rem;
}

.config-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.75rem;
  font-size: 0.85rem;
}

.config-item label {
  flex: 0 0 120px;
  color: #333;
  font-weight: 500;
  text-align: left;
}

.config-slider {
  flex: 0 0 25%;
  width: 25%;
  height: 4px;
  border-radius: 2px;
  background: #ddd;
  outline: none;
  -webkit-appearance: none;
  margin: 0;
}

.config-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #3498db;
  cursor: pointer;
}

.config-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #3498db;
  cursor: pointer;
  border: none;
}

.config-value {
  flex: 0 0 50px;
  text-align: right;
  font-weight: bold;
  color: #3498db;
}

.auto-roi-btn {
  width: 100%;
  padding: 0.5rem 1rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s;
  margin-top: 1rem;
}

.auto-roi-btn:hover:not(:disabled) {
  background-color: #2980b9;
  transform: translateY(-1px);
}

.auto-roi-btn:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
  transform: none;
}

/* Tooltip styling */
.config-item label[title],
.auto-roi-btn[title] {
  cursor: help;
  position: relative;
}

.config-item label[title]:hover::after,
.auto-roi-btn[title]:hover::after {
  content: attr(title);
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.9);
  color: white;
  padding: 0.75rem;
  border-radius: 6px;
  font-size: 0.8rem;
  z-index: 1000;
  pointer-events: none;
  max-width: 400px;
  min-width: 300px;
  white-space: normal;
  text-align: left;
  line-height: 1.4;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.config-item label[title]:hover::before,
.auto-roi-btn[title]:hover::before {
  content: '';
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: rgba(0, 0, 0, 0.9);
  z-index: 1000;
  pointer-events: none;
}
</style>
