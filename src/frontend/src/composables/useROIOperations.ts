import { ref } from 'vue'
import type { ROI, AutoROIConfig, BleachingSettings, Coords } from '../types'
import { useBackendApi } from './useBackendApi'

export function useROIOperations() {
  const availableROIs = ref<ROI[]>([])
  const selectedROIs = ref<number[]>([])
  const nextRoiId = ref(1)
  const isAutoROIRunning = ref(false)

  // ROI colors for different regions
  const roiColors = [
    '#FF6B6B', // Red
    '#4ECDC4', // Teal
    '#45B7D1', // Blue
    '#96CEB4', // Green
    '#FFEAA7', // Yellow
    '#DDA0DD', // Plum
    '#98D8C8', // Mint
    '#F7DC6F'  // Gold
  ]

  const createROI = async (
    coords: Coords,
    videoPath: string,
    bleachingSettings?: BleachingSettings
  ): Promise<void> => {
    const roiId = nextRoiId.value++
    const roiColor = roiColors[(roiId - 1) % roiColors.length]

    try {
      const { getROITraces } = useBackendApi()
      const result = await getROITraces(coords, bleachingSettings?.smoothing ?? 0.0)

      const newROI: ROI = {
        id: roiId,
        name: `ROI ${roiId}`,
        color: roiColor,
        coords: coords,
        selected: true,
        intensityTrace: result.intensity_trace,
        timePoints: result.time_points
      }

      availableROIs.value.push(newROI)
      if (newROI.selected && !selectedROIs.value.includes(newROI.id)) {
        selectedROIs.value.push(newROI.id)
      }
    } catch (error) {
      console.error('❌ Failed to create ROI:', error)
    }
  }

  const selectROI = async (roiId: number): Promise<boolean> => {
    const roi = availableROIs.value.find(r => r.id === roiId)
    if (!roi) return false

    // Update ROI in list locally (no backend call needed)
    const roiIndex = availableROIs.value.findIndex(r => r.id === roiId)
    if (roiIndex !== -1) {
      availableROIs.value[roiIndex].selected = true
      console.log('✅ ROI selected:', roiId)
      return true
    }
    return false
  }

  const unselectROI = async (roiId: number): Promise<boolean> => {
    const roi = availableROIs.value.find(r => r.id === roiId)
    if (!roi) return false

    // Update ROI in list locally (no backend call needed)
    const roiIndex = availableROIs.value.findIndex(r => r.id === roiId)
    if (roiIndex !== -1) {
      availableROIs.value[roiIndex].selected = false
      console.log('✅ ROI unselected:', roiId)
      return true
    }
    return false
  }

  const runAutoROI = async (config: AutoROIConfig): Promise<Coords[]> => {
    isAutoROIRunning.value = true
    console.log('🤖 Running auto ROI detection with config:', config)

    try {
      const { runAutoROI: apiRunAutoROI } = useBackendApi()
      const result = await apiRunAutoROI(config)

      console.log(`🎯 Auto ROI detected ${result} regions`)
      return result

    } catch (error) {
      console.error('❌ Auto ROI failed:', error)
      return []
    } finally {
      isAutoROIRunning.value = false
    }
  }

  const clearROIs = () => {
    availableROIs.value = []
    nextRoiId.value = 1
  }

  return {
    availableROIs,
    selectedROIs,
    isAutoROIRunning,
    createROI,
    selectROI,
    unselectROI,
    runAutoROI,
    clearROIs
  }
}
