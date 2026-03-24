// 环境配置
// 开发环境：http://localhost:8000
// 生产环境：通过 manifest.json 或构建变量注入

const ENV = {
  development: {
    API_BASE: 'http://localhost:8000/api/v1',
  },
  production: {
    API_BASE: 'https://api.ai-study-planner.com/api/v1',
  },
}

// uni-app 环境判断
const isDev = process.env.NODE_ENV === 'development'

export const API_BASE = isDev ? ENV.development.API_BASE : ENV.production.API_BASE

export default {
  API_BASE,
}
