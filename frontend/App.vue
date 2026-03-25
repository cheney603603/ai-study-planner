<template>
  <view class="app-container">
    <view v-if="!isLoggedIn" class="login-page">
      <view class="logo-section">
        <text class="app-title">AI 学习规划师</text>
        <text class="app-subtitle">让 AI 为你定制专属学习计划</text>
      </view>
      
      <view class="login-form">
        <input 
          class="input" 
          type="number" 
          v-model="phone" 
          placeholder="请输入手机号"
          maxlength="11"
        />
        <view class="code-row">
          <input 
            class="input code-input" 
            type="number" 
            v-model="code" 
            placeholder="验证码"
            maxlength="6"
          />
          <button 
            class="btn-secondary" 
            @click="sendCode"
            :disabled="countdown > 0 || sendingCode"
          >
            {{ sendingCode ? '发送中...' : countdown > 0 ? `${countdown}s` : '获取验证码' }}
          </button>
        </view>
        <button class="btn-primary" @click="login" :disabled="loggingIn">
          {{ loggingIn ? '登录中...' : '登录' }}
        </button>
      </view>
    </view>
    
    <!-- 已登录：显示主页 -->
    <view v-else class="main-page">
      <!-- 顶部用户信息 -->
      <view class="header">
        <view class="user-info">
          <text class="nickname">{{ user.nickname || '用户' }}</text>
          <view class="level-badge">
            <text>{{ user.level || '入门' }}</text>
          </view>
        </view>
        <view class="score-info">
          <text class="score-label">积分</text>
          <text class="score-value">{{ user.total_score || 0 }}</text>
        </view>
      </view>
      
      <!-- 今日任务 -->
      <view class="section">
        <view class="section-header">
          <text class="section-title">今日任务</text>
          <text class="section-more">查看全部 ></text>
        </view>
        <view class="task-list">
          <view v-if="todayTasks.length === 0" class="empty-tip">
            <text>暂无今日任务</text>
          </view>
          <view 
            v-for="task in todayTasks" 
            :key="task.id" 
            class="task-card"
            :class="{ completed: task.status === 'completed' }"
          >
            <view class="task-content">
              <text class="task-title">{{ task.title }}</text>
              <text class="task-desc">{{ task.content }}</text>
            </view>
            <view class="task-action">
              <text class="task-score">+{{ task.score }}分</text>
              <button 
                v-if="task.status !== 'completed'" 
                class="btn-small" 
                @click="completeTask(task.id)"
                :disabled="loadingTasks"
              >
                {{ loadingTasks ? '...' : '完成' }}
              </button>
              <text v-else class="done-tag">已完成</text>
            </view>
          </view>
        </view>
      </view>
      
      <!-- 学习计划 -->
      <view class="section">
        <view class="section-header">
          <text class="section-title">我的计划</text>
        </view>
        <view v-if="currentPlan" class="plan-card">
          <text class="plan-title">{{ currentPlan.title }}</text>
          <view class="plan-progress">
            <view class="progress-bar">
              <view class="progress-fill" :style="{ width: (currentPlan.completion_rate * 100) + '%' }"></view>
            </view>
            <text class="progress-text">{{ Math.round(currentPlan.completion_rate * 100) }}%</text>
          </view>
          <view class="plan-phases">
            <view v-for="phase in currentPlan.phases" :key="phase.id" class="phase-item">
              <text>{{ phase.name }}</text>
            </view>
          </view>
        </view>
        <view v-else class="empty-tip">
          <text>暂无学习计划</text>
          <button class="btn-primary" @click="startPlan">开始规划</button>
        </view>
      </view>
      
      <!-- 底部导航 -->
      <view class="tabbar">
        <view class="tab-item active">
          <text class="tab-icon">🏠</text>
          <text class="tab-text">首页</text>
        </view>
        <view class="tab-item">
          <text class="tab-icon">📚</text>
          <text class="tab-text">计划</text>
        </view>
        <view class="tab-item">
          <text class="tab-icon">🏆</text>
          <text class="tab-text">成就</text>
        </view>
        <view class="tab-item">
          <text class="tab-icon">👤</text>
          <text class="tab-text">我的</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useStore } from './store'

const store = useStore()

// 登录相关
const phone = ref('')
const code = ref('')
const countdown = ref(0)
const sendingCode = ref(false)   // 发送验证码 loading
const loggingIn = ref(false)     // 登录 loading
const loadingTasks = ref(false)  // 任务加载 loading

// 用户信息
const isLoggedIn = computed(() => store.isLoggedIn)
const user = computed(() => store.user)
const todayTasks = computed(() => store.todayTasks)
const currentPlan = computed(() => store.currentPlan)

// 手机号格式校验（中国大陆）
const validatePhone = (v) => /^1[3-9]\d{9}$/.test(v)

// 发送验证码
const sendCode = async () => {
  if (!validatePhone(phone.value)) {
    uni.showToast({ title: '请输入正确的 11 位手机号', icon: 'none' })
    return
  }
  if (sendingCode.value) return

  sendingCode.value = true
  try {
    await store.sendCode(phone.value)
    uni.showToast({ title: '验证码已发送', icon: 'success' })

    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (e) {
    uni.showToast({ title: e.message || '发送失败，请稍后重试', icon: 'none' })
  } finally {
    sendingCode.value = false
  }
}

// 登录
const login = async () => {
  if (!validatePhone(phone.value)) {
    uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
    return
  }
  if (!code.value || code.value.length !== 6) {
    uni.showToast({ title: '请输入 6 位验证码', icon: 'none' })
    return
  }
  if (loggingIn.value) return

  loggingIn.value = true
  try {
    await store.login(phone.value, code.value)
    await store.loadUserData()
  } catch (e) {
    uni.showToast({ title: e.message || '登录失败，请重试', icon: 'none' })
  } finally {
    loggingIn.value = false
  }
}

// 开始规划
const startPlan = () => {
  uni.navigateTo({ url: '/pages/chat/index' })
}

// 完成任务
const completeTask = async (taskId) => {
  if (loadingTasks.value) return
  loadingTasks.value = true
  try {
    const result = await store.completeTask(taskId)
    const msg = result?.level_up
      ? `任务完成！升级到 ${result.level_up.new} 🎉`
      : '任务完成！'
    uni.showToast({ title: msg, icon: 'success', duration: 2000 })
  } catch (e) {
    uni.showToast({ title: e.message || '操作失败', icon: 'none' })
  } finally {
    loadingTasks.value = false
  }
}

onMounted(async () => {
  const token = uni.getStorageSync('token')
  if (token) {
    store.setToken(token)
    try {
      await store.loadUserData()
    } catch (e) {
      // Token 失效，清除登录状态
      store.logout()
      uni.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
    }
  }
})
</script>

<style lang="scss">
page {
  background: #f5f5f5;
}

.app-container {
  min-height: 100vh;
}

.login-page {
  padding: 100rpx 60rpx;
  
  .logo-section {
    text-align: center;
    margin-bottom: 80rpx;
    
    .app-title {
      font-size: 48rpx;
      font-weight: bold;
      color: #333;
      display: block;
    }
    
    .app-subtitle {
      font-size: 28rpx;
      color: #999;
      margin-top: 20rpx;
      display: block;
    }
  }
  
  .login-form {
    .input {
      background: #fff;
      border-radius: 16rpx;
      padding: 30rpx;
      margin-bottom: 30rpx;
      font-size: 30rpx;
    }
    
    .code-row {
      display: flex;
      gap: 20rpx;
      
      .code-input {
        flex: 1;
      }
    }
    
    .btn-primary {
      background: #4A90E2;
      color: #fff;
      border-radius: 16rpx;
      padding: 30rpx;
      text-align: center;
      font-size: 32rpx;
      margin-top: 20rpx;
    }
    
    .btn-secondary {
      background: #fff;
      border: 1rpx solid #4A90E2;
      color: #4A90E2;
      border-radius: 16rpx;
      padding: 20rpx 30rpx;
      font-size: 26rpx;
    }
  }
}

.main-page {
  padding-bottom: 120rpx;
  
  .header {
    background: linear-gradient(135deg, #4A90E2, #67B26F);
    padding: 40rpx 30rpx;
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .user-info {
      .nickname {
        color: #fff;
        font-size: 36rpx;
        font-weight: bold;
      }
      
      .level-badge {
        background: rgba(255,255,255,0.3);
        padding: 8rpx 20rpx;
        border-radius: 20rpx;
        margin-top: 10rpx;
        
        text {
          color: #fff;
          font-size: 24rpx;
        }
      }
    }
    
    .score-info {
      text-align: right;
      
      .score-label {
        color: rgba(255,255,255,0.8);
        font-size: 24rpx;
        display: block;
      }
      
      .score-value {
        color: #fff;
        font-size: 48rpx;
        font-weight: bold;
      }
    }
  }
  
  .section {
    padding: 30rpx;
    
    .section-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 20rpx;
      
      .section-title {
        font-size: 32rpx;
        font-weight: bold;
        color: #333;
      }
      
      .section-more {
        font-size: 26rpx;
        color: #999;
      }
    }
    
    .task-list {
      .task-card {
        background: #fff;
        border-radius: 16rpx;
        padding: 30rpx;
        margin-bottom: 20rpx;
        display: flex;
        justify-content: space-between;
        align-items: center;
        
        &.completed {
          opacity: 0.6;
        }
        
        .task-content {
          flex: 1;
          
          .task-title {
            font-size: 30rpx;
            color: #333;
          }
          
          .task-desc {
            font-size: 26rpx;
            color: #999;
            margin-top: 10rpx;
            display: block;
          }
        }
        
        .task-action {
          .task-score {
            color: #FF9500;
            font-size: 26rpx;
            display: block;
            text-align: right;
          }
          
          .btn-small {
            background: #4A90E2;
            color: #fff;
            font-size: 24rpx;
            padding: 10rpx 30rpx;
            border-radius: 30rpx;
            margin-top: 10rpx;
          }
          
          .done-tag {
            color: #67B26F;
            font-size: 26rpx;
          }
        }
      }
    }
    
    .empty-tip {
      text-align: center;
      padding: 60rpx;
      color: #999;
      
      text {
        display: block;
        margin-bottom: 20rpx;
      }
    }
    
    .plan-card {
      background: #fff;
      border-radius: 16rpx;
      padding: 30rpx;
      
      .plan-title {
        font-size: 32rpx;
        font-weight: bold;
      }
      
      .plan-progress {
        display: flex;
        align-items: center;
        margin: 20rpx 0;
        
        .progress-bar {
          flex: 1;
          height: 16rpx;
          background: #f0f0f0;
          border-radius: 8rpx;
          overflow: hidden;
          
          .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4A90E2, #67B26F);
          }
        }
        
        .progress-text {
          margin-left: 20rpx;
          color: #4A90E2;
          font-size: 28rpx;
        }
      }
      
      .plan-phases {
        display: flex;
        gap: 20rpx;
        flex-wrap: wrap;
        
        .phase-item {
          background: #f5f5f5;
          padding: 10rpx 20rpx;
          border-radius: 8rpx;
          font-size: 24rpx;
          color: #666;
        }
      }
    }
  }
  
  .tabbar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #fff;
    display: flex;
    padding: 20rpx 0;
    border-top: 1rpx solid #f0f0f0;
    
    .tab-item {
      flex: 1;
      text-align: center;
      
      .tab-icon {
        font-size: 40rpx;
        display: block;
      }
      
      .tab-text {
        font-size: 24rpx;
        color: #999;
      }
      
      &.active .tab-text {
        color: #4A90E2;
      }
    }
  }
}

.btn-primary {
  background: #4A90E2 !important;
  color: #fff !important;
  border: none !important;
}
</style>
