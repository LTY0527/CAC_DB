import { useOutletContext } from 'react-router-dom'

export default function usePlatformPageData() {
  return useOutletContext() || {}
}
