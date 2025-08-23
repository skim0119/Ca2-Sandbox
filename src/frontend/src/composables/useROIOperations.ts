import { ref } from 'vue'
import type { ROI, AutoROIConfig, BleachingSettings } from '../types'
import { useBackendApi } from './useBackendApi'

export function useROIOperations() {
  const availableROIs = ref<ROI[]>([])
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
    coords: [number, number, number, number],
    videoPath: string,
    bleachingSettings?: BleachingSettings
  ): Promise<ROI | null> => {
    const roiId = nextRoiId.value++
    const roiColor = roiColors[(roiId - 1) % roiColors.length]

    try {
      const { createROI: apiCreateROI } = useBackendApi()
      const result = await apiCreateROI(coords, videoPath, bleachingSettings)

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
      return newROI
    } catch (error) {
      console.error('❌ Failed to create ROI:', error)
    }
    return null
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

  const runAutoROI = async (
    videoPath: string,
    config: AutoROIConfig
  ): Promise<ROI[]> => {
    if (!videoPath) {
      console.error('No video selected for auto ROI')
      return []
    }

    isAutoROIRunning.value = true
    console.log('🤖 Running auto ROI detection with config:', config)

    try {
      const { runAutoROI: apiRunAutoROI } = useBackendApi()
      const result = await apiRunAutoROI(videoPath, config)

      // Clear existing ROIs and add the new ones
      availableROIs.value = []

      // Add detected ROIs to the list
      const newROIs: ROI[] = result.rois.map((roi: { id: number; coords: [number, number, number, number]; avg_intensity: number[] }, index: number) => {
        const roiColor = roiColors[index % roiColors.length]
        return {
          id: roi.id,
          name: `Auto ROI ${roi.id + 1}`,
          color: roiColor,
          coords: roi.coords,
          selected: true,
          intensityTrace: roi.avg_intensity,
          timePoints: Array.from({ length: roi.avg_intensity.length }, (_, i) => i / 30) // Assuming 30 fps
        }
      })

      availableROIs.value.push(...newROIs)
      console.log(`🎯 Auto ROI detected ${result.stats.n_rois} regions`)
      return newROIs

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
    isAutoROIRunning,
    createROI,
    selectROI,
    unselectROI,
    runAutoROI,
    clearROIs
  }
}
