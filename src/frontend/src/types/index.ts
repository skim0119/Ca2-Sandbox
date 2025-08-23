export interface ROI {
  id: number
  name: string
  color: string
  coords: [number, number, number, number]
  selected: boolean
  intensityTrace?: number[]
  timePoints?: number[]
}

export interface VideoInfo {
  width: number
  height: number
  fps: number
  total_frames: number
  debug_mode?: boolean
  original_path?: string
}

export interface FirstFrameData {
  first_frame: string
  video_info: VideoInfo
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

export interface AnalysisData {
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

export interface ChartDataset {
  label: string
  data: number[]
  borderColor: string
  backgroundColor: string
  tension: number
}

export interface MainPlotData {
  timePoints: number[]
  datasets: ChartDataset[]
}

export interface BleachingData {
  adjustBleaching: boolean
  smoothing: number
  fitType: 'exponential' | 'inverse'
  analysisData?: AnalysisData
  analysisId?: string | null
  mainPlotData?: MainPlotData
}
