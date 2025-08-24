export interface Coords {
  x0: number
  y0: number
  x1: number
  y1: number
}

export interface ROI {
  id: number
  name: string
  color: string
  coords: Coords
  selected: boolean
  intensityTrace?: number[]
}

export interface VideoInfo {
  width: number
  height: number
  fps: number
  totalFrames: number
  originalPath?: string
}

export interface FirstFrameData {
  firstFrame: string
  videoInfo: VideoInfo
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
  timePoints: number[]
  meanIntensity: number[]
  fitParams: {
    exponential?: number[]
    inverse?: number[]
  }
  r2Scores: {
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
