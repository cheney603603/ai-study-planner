import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// API 基础地址
const API_BASE = 'http://localhost:8000/api/v1'

export const useStore = defineStore('user', () => {
  // 状态
  const token = ref(uni.getStorageSync('token') || '')
  const user = ref({
    id: '',
    phone: '',
    nickname: '',
    level: '入门',
    total_score: 0
  })
  const todayTasks = ref([])
  const currentPlan = ref(null)
  const rewards = ref(null)
  
  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  
  // Actions
  function setToken(newToken) {
    token.value = newToken
    uni.setStorageSync('token', newToken)
  }
  
  function logout() {
    token.value = ''
    user.value = {}
    todayTasks.value = []
    currentPlan.value = null
    rewards.value = null
    uni.removeStorageSync('token')
  }
  
  // API 请求
  async function request(url, options = {}) {
    const fullUrl = `${API_BASE}${url}`
    const headers = {
      'Content-Type': 'application/json',
      ...(token.value ? { 'Authorization': `Bearer ${token.value}` } : {})
    }
    
    try {
      const response = await uni.request({
        url: fullUrl,
        ...options,
        header: { ...headers, ...options.header }
      })
      
      if (response[1].statusCode === 401) {
        logout()
        throw new Error('登录已过期')
      }
      
      const data = response[1].data
      
      if (data.code !== 'success') {
        throw new Error(data.message || '请求失败')
      }
      
      return data.data
    } catch (e) {
      console.error('API Error:', e)
      throw e
    }
  }
  
  // 发送验证码
  async function sendCode(phone) {
    return request('/auth/send-code', {
      method: 'POST',
      data: { phone }
    })
  }
  
  // 登录
  async function login(phone, code) {
    const data = await request('/auth/login', {
      method: 'POST',
      data: { phone, code }
    })
    
    setToken(data.access_token)
    user.value = data.user
    
    return data
  }
  
  // 加载用户数据
  async function loadUserData() {
    if (!token.value) return
    
    try {
      // 获取用户信息
      const userInfo = await request('/auth/me')
      user.value = userInfo
      
      // 获取今日任务
      const tasks = await request('/plan/tasks/today')
      todayTasks.value = tasks.tasks || []
      
      // 获取当前计划
      const plan = await request('/plan/current')
      currentPlan.value = plan.has_plan ? plan : null
      
      // 获取奖励信息
      const rewardInfo = await request('/rewards/score')
      rewards.value = rewardInfo
      
    } catch (e) {
      console.error('Load user data error:', e)
    }
  }
  
  // 获取 Token 使用量
  async function getTokenUsage() {
    return request('/subscription/token-usage')
  }
  
  // 获取今日任务
  async function fetchTodayTasks() {
    const tasks = await request('/plan/tasks/today')
    todayTasks.value = tasks.tasks || []
    return tasks
  }
  
  // 获取本周任务
  async function fetchWeekTasks() {
    return request('/plan/tasks/week')
  }
  
  // 完成任务
  async function completeTask(taskId) {
    const result = await request(`/plan/task/${taskId}/complete`, {
      method: 'POST'
    })
    
    // 刷新数据
    await loadUserData()
    
    return result
  }
  
  // 发送聊天消息
  async function sendChatMessage(content, sessionId = null) {
    return request('/chat/send', {
      method: 'POST',
      data: { content, session_id: sessionId }
    })
  }
  
  // 确认并创建计划
  async function confirmPlan(planData) {
    return request('/chat/confirm-plan', {
      method: 'POST',
      data: planData
    })
  }
  
  // 获取徽章
  async function fetchBadges() {
    return request('/rewards/badges')
  }
  
  // 获取排行榜
  async function fetchLeaderboard() {
    return request('/rewards/leaderboard')
  }
  
  // 获取用户排名
  async function fetchUserRank() {
    return request('/rewards/rank')
  }
  
  return {
    // 状态
    token,
    user,
    todayTasks,
    currentPlan,
    rewards,
    isLoggedIn,
    
    // Actions
    setToken,
    logout,
    sendCode,
    login,
    loadUserData,
    getTokenUsage,
    fetchTodayTasks,
    fetchWeekTasks,
    completeTask,
    sendChatMessage,
    confirmPlan,
    fetchBadges,
    fetchLeaderboard,
    fetchUserRank
  }
})
