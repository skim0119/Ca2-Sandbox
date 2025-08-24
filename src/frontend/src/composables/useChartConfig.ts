import { computed } from 'vue'

export function useChartConfig(title?: string) {
  const chartOptions = computed(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const
      },
      ...(title && {
        title: {
          display: true,
          text: title
        }
      })
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Time (seconds)'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Intensity'
        }
      }
    }
  }))

  return { chartOptions }
}
