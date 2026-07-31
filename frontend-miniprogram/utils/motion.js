/**
 * 运动管理器 - MotionManager
 * 为微信小程序提供统一动画管理能力，模拟桌面端的 motion store 模式
 */

const ANIMATION_TYPES = {
  fadeIn: 'fade-in',
  slideUp: 'slide-up',
  slideLeft: 'slide-left',
  scaleIn: 'scale-in',
  bounce: 'bounce',
  none: 'none',
}

const IMMERSION_LEVELS = {
  minimal: 0,
  moderate: 1,
  full: 2,
}

// 轻量级设备判断：低端机（内存 < 4GB 或低端芯片）减少动画
function isLowEndDevice() {
  try {
    const systemInfo = wx.getSystemInfoSync()
    // 内存信息在部分设备上不可用，fallback 到 model
    const memLevel = systemInfo.memoryLevel || 'full'
    // 低端设备特征
    const lowEndModels = [
      'iPhone SE', 'iPhone8', 'iPhone9', 'iPhone10',
      'iPhone11,2', 'iPhone11,4', 'iPhone11,6', 'iPhone11,8',
      'iPad mini', 'iPad Air',
    ]
    const isLowEndModel = lowEndModels.some((m) => systemInfo.model.includes(m))
    return memLevel === 'low' || memLevel === 'medium' || isLowEndModel
  } catch (e) {
    return false
  }
}

class MotionManager {
  constructor() {
    this.immersionLevel = IMMERSION_LEVELS.full
    this.animating = false
    this._pageAnimations = new Map()
    this._reducedMotion = isLowEndDevice()

    // 尝试从用户偏好读取
    try {
      const saved = wx.getStorageSync('motion_preference')
      if (saved !== '') {
        this.immersionLevel = parseInt(saved, 10) || IMMERSION_LEVELS.full
      }
    } catch (e) {
      // ignore
    }

    // 系统级别减少动效检查
    try {
      const sysInfo = wx.getSystemInfoSync()
      if (sysInfo.platform === 'devtools') {
        // 模拟器中强制全量动画便于调试
        this._reducedMotion = false
      }
    } catch (e) {
      // ignore
    }
  }

  /**
   * 获取当前动效配置
   * @returns {Object} motion config
   */
  getConfig() {
    return {
      enabled: !this._reducedMotion,
      immersionLevel: this.immersionLevel,
      duration: this.immersionLevel >= 2 ? 400 : this.immersionLevel >= 1 ? 250 : 0,
      delay: this.immersionLevel >= 2 ? 60 : 30,
    }
  }

  /**
   * 设置动效强度级别
   * @param {number} level - 0=minimal, 1=moderate, 2=full
   */
  setLevel(level) {
    this.immersionLevel = Math.max(0, Math.min(2, level))
    try {
      wx.setStorageSync('motion_preference', String(this.immersionLevel))
    } catch (e) {
      // ignore storage error
    }
  }

  /**
   * 创建基础入场动画数据
   * @param {string} type - fade-in / slide-up / scale-in / bounce
   * @param {number} duration - 动画时长 ms
   * @param {Object} extra - 额外参数（如 translateX/Y、scale 等）
   * @returns {Object} animation data
   */
  createAnimation(type, duration, extra) {
    if (this._reducedMotion) return null

    const dur = duration || (this.immersionLevel >= 2 ? 400 : 250)
    let anim = null

    switch (type) {
      case ANIMATION_TYPES.fadeIn:
        anim = wx.createAnimation({
          duration: dur,
          timingFunction: 'ease-out',
          ...extra,
        })
        anim.opacity(0).step()
        anim.opacity(1).step({ duration: dur, timingFunction: 'ease-out' })
        break

      case ANIMATION_TYPES.slideUp:
        anim = wx.createAnimation({
          duration: dur,
          timingFunction: 'ease-out',
          ...extra,
        })
        anim.translateY(40).opacity(0).step()
        anim.translateY(0).opacity(1).step({ duration: dur, timingFunction: 'cubic-bezier(0.34, 1.56, 0.64, 1)' })
        break

      case ANIMATION_TYPES.slideLeft:
        anim = wx.createAnimation({
          duration: dur,
          timingFunction: 'ease-out',
          ...extra,
        })
        anim.translateX(-60).opacity(0).step()
        anim.translateX(0).opacity(1).step({ duration: dur, timingFunction: 'ease-out' })
        break

      case ANIMATION_TYPES.scaleIn:
        anim = wx.createAnimation({
          duration: dur,
          timingFunction: 'ease-out',
          ...extra,
        })
        anim.scale(0.7).opacity(0).step()
        anim.scale(1).opacity(1).step({ duration: dur, timingFunction: 'cubic-bezier(0.34, 1.56, 0.64, 1)' })
        break

      case ANIMATION_TYPES.bounce:
        anim = wx.createAnimation({
          duration: dur,
          timingFunction: 'ease-out',
          ...extra,
        })
        anim.translateY(60).opacity(0).step()
        anim.translateY(-15).step({ duration: dur * 0.3, timingFunction: 'ease-out' })
        anim.translateY(5).step({ duration: dur * 0.2, timingFunction: 'ease-out' })
        anim.translateY(0).opacity(1).step({ duration: dur * 0.5, timingFunction: 'ease-out' })
        break

      default:
        anim = null
        break
    }

    return anim
  }

  /**
   * 对指定 view 执行动画
   * @param {string} viewId - page 中 setData 绑定的 animation 变量名（不是 wx:for index）
   * @param {Object} animationData - wx.createAnimation().export() 结果
   * @param {number} delay - 延迟 ms
   */
  animateView(viewId, animationData, delay) {
    if (!animationData || this._reducedMotion) return Promise.resolve()

    return new Promise((resolve) => {
      const timer = setTimeout(() => {
        // 通过 getApp() 获取页面对象是 WeChat 小程序的常见做法
        const pages = getCurrentPages()
        const currentPage = pages[pages.length - 1]
        if (currentPage && typeof currentPage.setData === 'function') {
          const update = {}
          update[viewId] = animationData
          currentPage.setData(update, resolve)
        } else {
          resolve()
        }
      }, delay || 0)

      // 防止超时
      if (delay > 0) {
        setTimeout(() => resolve(), delay + 100)
      }
    })
  }

  /**
   * 批量交错入场动画（staggered entrance）
   * @param {Array<{viewId: string, type: string, delay?: number}>} items
   */
  staggerEntrance(items) {
    if (this._reducedMotion) return Promise.resolve()

    const { delay } = this.getConfig()
    const promises = items.map((item, index) => {
      const anim = this.createAnimation(item.type || ANIMATION_TYPES.slideUp, undefined, { delay: index * delay })
      return this.animateView(item.viewId, anim, index * delay)
    })

    return Promise.all(promises)
  }

  /**
   * 注册页面级别的动画实例
   * @param {string} pagePath - 页面路径
   * @param {Object} manager - 页面实例
   */
  registerPage(pagePath, pageInstance) {
    this._pageAnimations.set(pagePath, pageInstance)
  }

  /**
   * 注销页面动画实例
   * @param {string} pagePath
   */
  unregisterPage(pagePath) {
    this._pageAnimations.delete(pagePath)
  }
}

// 单例导出
let _instance = null
function getMotionManager() {
  if (!_instance) {
    _instance = new MotionManager()
  }
  return _instance
}

module.exports = { MotionManager, getMotionManager, ANIMATION_TYPES, isLowEndDevice }
