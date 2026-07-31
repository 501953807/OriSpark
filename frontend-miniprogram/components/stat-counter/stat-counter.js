/**
 * stat-counter 组件
 * 数字从 0 滚动到目标值，使用 easeOutExpo 缓动
 *
 * Properties:
 *  - target {Number} 目标数值
 *  - duration {Number} 动画时长 ms，默认 1200
 *  - prefix {String} 前缀文本（如 ¥、$），默认 ''
 *  - suffix {String} 后缀文本（如 K、M、+），默认 ''
 *  - decimals {Number} 小数位数，默认 0
 */
Component({
  properties: {
    target: {
      type: Number,
      value: 0,
    },
    duration: {
      type: Number,
      value: 1200,
    },
    prefix: {
      type: String,
      value: '',
    },
    suffix: {
      type: String,
      value: '',
    },
    decimals: {
      type: Number,
      value: 0,
    },
  },

  data: {
    displayValue: '0',
  },

  lifetimes: {
    attached() {
      this._timer = null
      this._startAnimation()
    },
    detached() {
      this._cancelTimer()
    },
  },

  observers: {
    'target': function(newVal) {
      if (newVal !== undefined && newVal !== null) {
        this._startAnimation()
      }
    },
  },

  methods: {
    /**
     * easeOutExpo 缓动函数
     */
    _easeOutExpo(t) {
      return t === 1 ? 1 : 1 - Math.pow(2, -10 * t)
    },

    _cancelTimer() {
      if (this._timer !== null) {
        clearInterval(this._timer)
        this._timer = null
      }
    },

    _startAnimation() {
      this._cancelTimer()

      const target = Math.max(0, this.properties.target)
      const duration = Math.max(100, this.properties.duration)
      const decimals = Math.min(4, Math.max(0, this.properties.decimals))

      if (target === 0) {
        this.setData({ displayValue: '0' })
        return
      }

      const startTime = Date.now()

      this._timer = setInterval(() => {
        const elapsed = Date.now() - startTime
        const progress = Math.min(elapsed / duration, 1)
        const easedProgress = this._easeOutExpo(progress)
        const currentValue = Math.round(target * easedProgress * Math.pow(10, decimals)) / Math.pow(10, decimals)

        this.setData({
          displayValue: currentValue.toFixed(decimals),
        })

        if (progress >= 1) {
          this._cancelTimer()
          // 最终值确保精确
          this.setData({ displayValue: target.toFixed(decimals) })
        }
      }, 16) // ~60fps
    },
  },
})
