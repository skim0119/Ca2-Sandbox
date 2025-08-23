import type { FirstFrameData, ROI, AutoROIConfig, BleachingSettings, AnalysisData } from '../types'

export function useBackendApi() {
  const uploadVideo = async (file: File): Promise<FirstFrameData> => {
    console.log('Uploading video file to backend:', file.name, 'Size:', file.size, 'Type:', file.type)

    // First check if backend is reachable
    try {
      const versionResponse = await fetch('/api/version')
      console.log('Backend version check:', versionResponse.status)
    } catch (error) {
      console.error('Backend not reachable:', error)
      throw new Error('Backend server is not running or not accessible')
    }

    const formData = new FormData()
    formData.append('video_file', file)

    console.log('FormData created, sending request to /api/upload-video...')

    try {
      const response = await fetch('/api/upload-video', {
        method: 'POST',
        body: formData
      })

      console.log('Response received:', response.status, response.statusText)

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Response error:', errorText)
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`)
      }

      const result = await response.json()
      console.log('✅ Video upload and processing successful:', result)
      return result
    } catch (error) {
      console.error('❌ Upload failed:', error)
      throw error
    }
  }
  const runAnalysis = async (videoPath: string): Promise<{ bleaching_data: AnalysisData; analysis_id: string }> => {
    console.log('🚀 Analysis requested for video:', videoPath)
    const response = await fetch('/api/run-analysis', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        video_path: videoPath
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    console.log('✅ Analysis completed:', result)
    return result
  }

  const createROI = async (
    coords: [number, number, number, number],
    videoPath: string,
    bleachingSettings?: BleachingSettings
  ): Promise<{ intensity_trace: number[]; time_points: number[] }> => {
    const response = await fetch('/api/roi-creation', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        video_path: videoPath,
        roi_data: {
          coords: coords
        },
        adjust_bleaching: bleachingSettings?.adjustBleaching ?? false,
        fit_type: bleachingSettings?.fitType ?? 'inverse',
        smoothing: bleachingSettings?.smoothing ?? 0.0
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    console.log('✅ ROI created:', result)
    return result
  }

  const runAutoROI = async (videoPath: string, config: AutoROIConfig): Promise<{
    rois: Array<{ id: number; coords: [number, number, number, number]; avg_intensity: number[] }>;
    stats: { n_rois: number }
  }> => {
    console.log('🤖 Running auto ROI detection with config:', config)
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
    return result
  }

  const getROITraces = async (rois: Array<{ id: number; coords: [number, number, number, number] }>, smoothing: number): Promise<{
    traces: Array<{ roi_id: number; intensity_trace: number[]; time_points: number[] }>
  }> => {
    console.log('📊 Fetching ROI traces for:', rois.map(r => r.id))
    const response = await fetch('/api/get-roi-traces', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        rois: rois,
        smoothing: smoothing
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    console.log('✅ ROI traces received:', result)
    return result
  }

  const updateFitPreference = async (analysisId: string, fitType: 'exponential' | 'inverse'): Promise<void> => {
    const response = await fetch('/api/update-fit-preference', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        analysis_id: analysisId,
        fit_type: fitType
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    console.log('✅ Fit preference updated:', fitType)
  }

  const getBackendVersion = async (): Promise<string> => {
    try {
      const response = await fetch('/api/version')
      if (response.ok) {
        const data = await response.json()
        return data.version
      } else {
        return 'dev mode'
      }
    } catch {
      console.log('Backend not available, running in dev mode')
      return 'dev mode'
    }
  }

  return {
    uploadVideo,
    runAnalysis,
    createROI,
    runAutoROI,
    getROITraces,
    updateFitPreference,
    getBackendVersion
  }
}
