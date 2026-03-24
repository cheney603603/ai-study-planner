import { createPinia } from 'pinia'

const pinia = createPinia()

export default pinia

// 统一从这里导出所有 store，方便使用
export { useStore } from './user'
