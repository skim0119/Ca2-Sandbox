import { ref } from 'vue'

export interface ROI {
  id: number
  name: string
  color: string
  coords: [number, number, number, number]
  selected: boolean
  intensityTrace?: number[]
  timePoints?: number[]
}

export interface AutoROIConfig {
  thresholdPercentage: number
  minDistancePercentage: number
  nClusters: number
}

export interface BleachingSettings {
  adjustBleaching: boolean
  fitType: 'exponential' | 'inverse'
  smoothing: number
}

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
      const response = await fetch('/api/roi-creation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          video_path: videoPath,
          roi_data: {
            id: roiId,
            coords: coords
          },
          adjust_bleaching: bleachingSettings?.adjustBleaching ?? false,
          fit_type: bleachingSettings?.fitType ?? 'inverse',
          smoothing: bleachingSettings?.smoothing ?? 0.0
        })
      })

      if (response.ok) {
        const result = await response.json()
        console.log('✅ ROI created:', result)

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
      }
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
      const response = await fetch('/api/auto-roi', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          video_path: videoPath,
          threshold_percentage: config.thresholdPercentage,
          min_distance_percentage: config.minDistancePercentage,
          n_clusters: config.nClusters
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      console.log('✅ Auto ROI completed:', result)

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
