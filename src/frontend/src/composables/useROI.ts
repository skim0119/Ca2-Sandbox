import { ref } from 'vue'
import type { Ref } from 'vue'
import type { ROI, AutoROIConfig, BleachingSettings, Coords } from '../types'
import { useBackendApi } from './useBackendApi.ts'

export function useROIState() {
  const availableROIs = ref<ROI[]>([])
  const selectedROIs = ref<number[]>([])
  const isAutoROIRunning = ref(false)

  return {
    availableROIs,
    selectedROIs,
    isAutoROIRunning,
  }
}

export function useROIOperations(availableROIs: Ref<ROI[]>, selectedROIs: Ref<number[]>, isAutoROIRunning: Ref<boolean>) {
  const nextRoiId = ref(1)
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
      const result = await getROITraces(
        [{ id: roiId, coords: coords }],
      bleachingSettings?.smoothing ?? 0.0)

      const newROI: ROI = {
        id: roiId,
        name: `ROI ${roiId}`,
        color: roiColor,
        coords: coords,
        intensityTrace: result[0].intensityTrace,
      }

      availableROIs.value.push(newROI)
      console.log('🔄 ROI created:', availableROIs.value)
      if (!selectedROIs.value.includes(roiId)) {
        selectedROIs.value.push(roiId)
      }
    } catch (error) {
      console.error('Failed to create ROI:', error)
    }
  }

  const selectROI = async (roiId: number): Promise<boolean> => {
    const roi = availableROIs.value.find(r => r.id === roiId)
    if (!roi) return false

    const roiIndex = availableROIs.value.findIndex(r => r.id === roiId)
    if (roiIndex !== -1) {
      // Add this line to sync the arrays:
      if (!selectedROIs.value.includes(roiId)) {
        selectedROIs.value.push(roiId)
      }
      return true
    }
    return false
  }

  const unselectROI = async (roiId: number): Promise<boolean> => {
    const roi = availableROIs.value.find(r => r.id === roiId)
    if (!roi) return false

    const roiIndex = availableROIs.value.findIndex(r => r.id === roiId)
    if (roiIndex !== -1) {
      const index = selectedROIs.value.indexOf(roiId)
      if (index > -1) {
        selectedROIs.value.splice(index, 1)
      }
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
      console.error('Auto ROI failed:', error)
      return []
    } finally {
      isAutoROIRunning.value = false
    }
  }

  const clearROIs = () => {
    availableROIs.value = []
    selectedROIs.value = []
    nextRoiId.value = 1
  }

  return {
    createROI,
    selectROI,
    unselectROI,
    runAutoROI,
    clearROIs
  }
}
