<script setup lang="ts">
import { ref } from 'vue'
import { useBackendApi } from '../composables/useBackendApi'

interface Props {
  selectedFiles: string[]
}

interface Emits {
  (e: 'files-selected', files: string[]): void
  (e: 'first-frame-received', data: {
    first_frame: string;
    video_info: {
      width: number;
      height: number;
      fps: number;
      total_frames: number;
      debug_mode?: boolean;
      original_path?: string;
    }
  } | null): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const folderPath = ref<string>('')
const fileList = ref<string[]>([])
const selectedVideoPath = ref<string>('')
const uploadedFiles = ref<File[]>([])

// Video file extensions to highlight
// const videoExtensions = ['.avi', '.mp4', '.mov', '.mkv', '.wmv', '.flv', '.webm']
const videoExtensions = ['.avi', '.mp4', '.mov']  // Video extension depends on cv2 capability

const isVideoFile = (filename: string): boolean => {
  const extension = filename.toLowerCase().substring(filename.lastIndexOf('.'))
  return videoExtensions.includes(extension)
}

const handleFileSelect = () => {
  // Create a hidden file input element
  const input = document.createElement('input')
  input.type = 'file'
  input.multiple = true
  input.accept = '.avi,.mp4,.mov' // Only accept video files
  input.style.display = 'none'

  input.onchange = (event) => {
    const target = event.target as HTMLInputElement
    if (target.files && target.files.length > 0) {
      const files = Array.from(target.files)

      // Filter to only include video files
      const videoFiles = files.filter(file => isVideoFile(file.name))
      
      // Add new files to existing lists (avoid duplicates)
      videoFiles.forEach(file => {
        if (!fileList.value.includes(file.name)) {
          fileList.value.push(file.name)
          uploadedFiles.value.push(file)
        }
      })

      console.log('Files selected:', videoFiles.map(f => ({ name: f.name, size: f.size, type: f.type })))
    }
  }

  // Add the input to DOM temporarily and trigger the file dialog
  document.body.appendChild(input)
  input.click()
}

const handleFileToggle = async (filename: string) => {
  console.log('File toggle called for:', filename)
  console.log('Available uploaded files:', uploadedFiles.value.map(f => f.name))
  
  const currentSelection = [...props.selectedFiles]
  const index = currentSelection.indexOf(filename)

  if (index > -1) {
    currentSelection.splice(index, 1)
  } else {
    currentSelection.push(filename)
  }

  emit('files-selected', currentSelection)

  // If this is a single video selection, automatically upload and process
  if (currentSelection.length === 1 && isVideoFile(filename)) {
    selectedVideoPath.value = currentSelection[0]
    console.log('Single video selected, attempting upload:', filename)
    
    try {
      // Find the actual File object for this filename
      const file = uploadedFiles.value.find(f => f.name === filename)
      if (file) {
        console.log('Found file object:', file.name, file.size, file.type)
        const result = await uploadAndProcessVideo(file)
        // Emit the first frame data to parent component
        emit('first-frame-received', result)
      } else {
        console.error('File object not found for filename:', filename)
      }
    } catch (error) {
      console.error('Failed to upload and process video:', error)
    }
  } else {
    selectedVideoPath.value = ''
  }
}

const handleRemoveFile = (filename: string, event: Event) => {
  event.stopPropagation() // Prevent triggering the file toggle
  
  console.log('Removing file:', filename)
  
  // Remove from file list
  const fileIndex = fileList.value.indexOf(filename)
  if (fileIndex > -1) {
    fileList.value.splice(fileIndex, 1)
  }
  
  // Remove from uploaded files
  const uploadedIndex = uploadedFiles.value.findIndex(f => f.name === filename)
  if (uploadedIndex > -1) {
    uploadedFiles.value.splice(uploadedIndex, 1)
  }
  
  // Remove from selected files if it was selected
  const currentSelection = [...props.selectedFiles]
  const selectedIndex = currentSelection.indexOf(filename)
  if (selectedIndex > -1) {
    currentSelection.splice(selectedIndex, 1)
    emit('files-selected', currentSelection)
    
    // If no files are selected anymore, clear the video
    if (currentSelection.length === 0) {
      selectedVideoPath.value = ''
      emit('first-frame-received', null)
    }
  }
}

const handleClearAll = () => {
  console.log('Clearing all files')
  
  // Clear all arrays
  fileList.value = []
  uploadedFiles.value = []
  
  // Clear selections
  emit('files-selected', [])
  selectedVideoPath.value = ''
  emit('first-frame-received', null)
}

const uploadAndProcessVideo = async (file: File) => {
  console.log('Uploading and processing video file:', file.name)

  try {
    const { uploadVideo } = useBackendApi()
    const result = await uploadVideo(file)
    return result
  } catch (error) {
    console.error('❌ Error uploading video to backend:', error)

    // Create dummy data for debugging
    const dummyData = createDummyFrameData(file.name)
    console.log('🔄 Using dummy data for debugging:', dummyData)

    return dummyData
  }
}

const createDummyFrameData = (videoPath: string) => {
  // Create a dummy SVG image with debugging information
  const dummySvg = `
    <svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="#2c3e50"/>
      <text x="50%" y="30%" text-anchor="middle" fill="white" font-family="Arial" font-size="16" font-weight="bold">
        🔧 DEV MODE - DUMMY FRAME
      </text>
      <text x="50%" y="45%" text-anchor="middle" fill="#3498db" font-family="Arial" font-size="12">
        Backend not available
      </text>
      <text x="50%" y="60%" text-anchor="middle" fill="#e74c3c" font-family="Arial" font-size="10">
        Video Path: ${videoPath}
      </text>
      <text x="50%" y="75%" text-anchor="middle" fill="#f39c12" font-family="Arial" font-size="10">
        API Call: POST /api/initiate-analysis
      </text>
      <text x="50%" y="85%" text-anchor="middle" fill="#95a5a6" font-family="Arial" font-size="8">
        Check console for debugging info
      </text>
    </svg>
  `

  const base64Svg = btoa(dummySvg)
  const dummyImage = `data:image/svg+xml;base64,${base64Svg}`

  return {
    first_frame: dummyImage,
    video_info: {
      width: 400,
      height: 300,
      fps: 30.0,
      total_frames: 1000,
      debug_mode: true,
      original_path: videoPath
    }
  }
}
</script>

<template>
  <div class="file-selector">
    <h3>File Selection</h3>

    <!-- File Selection -->
    <div class="file-selection-section">
      <button @click="handleFileSelect" class="select-files-btn">
        Select video files
      </button>
      <div class="folder-help">
        Select one or more video files to upload and process.
      </div>
      <div v-if="fileList.length > 0" class="file-count">
        Selected files: {{ fileList.length }} video file(s)
      </div>
    </div>

    <!-- File List -->
    <div class="file-list-section">
      <div class="file-list-header">
        <h4>Video files</h4>
        <button
          v-if="fileList.length > 0"
          @click="handleClearAll"
          class="clear-all-btn"
          title="Remove all files"
        >
          Clear All
        </button>
      </div>

      <div class="file-list">
        <div
          v-for="filename in fileList"
          :key="filename"
          :class="[
            'file-item',
            { 'video-file': isVideoFile(filename) },
            { 'selected': selectedFiles.includes(filename) }
          ]"
          @click="handleFileToggle(filename)"
        >
          <input
            type="checkbox"
            :checked="selectedFiles.includes(filename)"
            @change="handleFileToggle(filename)"
            class="file-checkbox"
          />
          <span class="file-name">{{ filename }}</span>
          <button
            @click="handleRemoveFile(filename, $event)"
            class="remove-file-btn"
            title="Remove file"
          >
            ×
          </button>
        </div>
      </div>

      <div class="file-legend">
        <span class="legend-item">
          <span class="legend-color video"></span>
          Video files (avi, mp4, mov)
        </span>
      </div>


    </div>
  </div>
</template>

<style scoped>
.file-selector {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.file-selector h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1.2rem;
}

.file-selection-section {
  margin-bottom: 1rem;
}

.select-files-btn {
  width: 100%;
  padding: 0.75rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.2s;
}

.select-files-btn:hover {
  background-color: #2980b9;
}

.folder-help {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: #666;
  font-style: italic;
  text-align: center;
}

.file-count {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: #28a745;
  font-weight: 500;
  text-align: center;
  background-color: #d4edda;
  padding: 0.5rem;
  border-radius: 3px;
  border: 1px solid #c3e6cb;
}

.folder-path {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: #666;
  word-break: break-all;
  background-color: #f8f9fa;
  padding: 0.5rem;
  border-radius: 3px;
  border: 1px solid #e9ecef;
}

.file-list-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.file-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.file-list-header h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 1rem;
}

.file-actions {
  display: flex;
  gap: 0.25rem;
}

.action-btn {
  padding: 0.25rem 0.5rem;
  background-color: #ecf0f1;
  border: 1px solid #bdc3c7;
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.7rem;
  transition: background-color 0.2s;
}

.action-btn:hover {
  background-color: #d5dbdb;
}

.clear-all-btn {
  padding: 0.25rem 0.5rem;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.7rem;
  transition: background-color 0.2s;
}

.clear-all-btn:hover {
  background-color: #c0392b;
}

.file-list {
  flex: 1;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow-y: auto;
  background-color: #fafafa;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background-color 0.2s;
}

.file-item:last-child {
  border-bottom: none;
}

.file-item:hover {
  background-color: #f0f0f0;
}

.file-item.selected {
  background-color: #e3f2fd;
}

.file-item.video-file {
  background-color: #fff3e0;
}

.file-item.video-file.selected {
  background-color: #ffe0b2;
}

.file-checkbox {
  margin-right: 0.5rem;
}

.file-name {
  font-size: 0.85rem;
  color: #333;
  flex: 1;
  word-break: break-all;
}

.remove-file-btn {
  background: none;
  border: none;
  color: #e74c3c;
  font-size: 1.2rem;
  font-weight: bold;
  cursor: pointer;
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  transition: all 0.2s;
  margin-left: 0.5rem;
  line-height: 1;
}

.remove-file-btn:hover {
  background-color: #e74c3c;
  color: white;
}

.file-legend {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #666;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-color.video {
  background-color: #fff3e0;
  border: 1px solid #ffb74d;
}

.selected-video-info {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.selected-video-info h5 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
  font-size: 0.9rem;
}

.selected-video-info p {
  margin: 0 0 1rem 0;
  font-size: 0.8rem;
  color: #666;
  word-break: break-all;
  background-color: #fff;
  padding: 0.5rem;
  border-radius: 3px;
  border: 1px solid #ddd;
}

.process-btn {
  padding: 0.5rem 1rem;
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: background-color 0.2s;
}

.process-btn:hover {
  background-color: #218838;
}

.process-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}
</style>
