/**
 * motion-frame 组件
 * 通用动画容器，支持多种入场动画类型
 *
 * Properties:
 *  - animationType {String} 动画类型: fade-in | slide-up | scale-in | bounce，默认 slide-up
 *  - delay {Number} 延迟毫秒数，默认 0
 *  - duration {Number} 动画时长 ms，默认 400
 *  - customStyle {String} 内联样式字符串
 */
const { getMotionManager, ANIMATION_TYPES } = require('../../utils/motion')

Component({
  options: {
    multipleSlots: true,
  },

  properties: {
    animationType: {
      type: String,
      value: ANIMATION_TYPES.slideUp,
    },
    delay: {
      type: Number,
      value: 0,
    },
    duration: {
      type: Number,
      value: 400,
    },
    customStyle: {
      type: String,
      value: '',
    },
  },

  data: {
    animationData: null,
  },

  lifetimes: {
    attached() {
      this._mounted = true
      this._runAnimation()
    },
    detached() {
      this._mounted = false
    },
  },

  methods: {
    _runAnimation() {
      const motionMgr = getMotionManager()
      const config = motionMgr.getConfig()

      if (!config.enabled) {
        this.setData({ animationData: null })
        return
      }

      const anim = motionMgr.createAnimation(this.properties.animationType, this.properties.duration)
      if (!anim) {
        this.setData({ animationData: null })
        return
      }

      const animationData = anim.export()
      this.setData({ animationData }, () => {
        // 使用 setTimeout 确保setData后动画数据已生效
        setTimeout(() => {
          if (this._mounted && this.data.animationData) {
            this.triggerEvent('animationend', { animationType: this.properties.animationType })
          }
        }, this.properties.delay + this.properties.duration + 50)
      })
    },

    /**
     * 公开方法：重新触发动画（用于数据更新后重播）
     */
    replay() {
      this._runAnimation()
    },
  },
})
