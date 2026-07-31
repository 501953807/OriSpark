/**
 * pulse-ring 组件
 * 品牌签名脉冲涟漪效果，点击时触发外扩圆环动画
 *
 * Properties:
 *  - color {String} 环颜色，默认 #0ea5e9（OriSpark 品牌蓝）
 *  - size {Number} 点击响应区域缩放倍数，默认 2.4
 */
const BRANDING_BLUE = '#059669' // OriSpark 主品牌绿

Component({
  properties: {
    color: {
      type: String,
      value: BRANDING_BLUE,
    },
  },

  data: {
    ringAnimation: null,
    ringKey: 0, // 用于强制重播 animation
  },

  methods: {
    _onTap() {
      this.triggerEvent('tap', { detail: {} })
      this._playPulse()
    },

    _playPulse() {
      const { size } = this.properties
      // 用 CSS class 切换来触发重新播放 @keyframes
      // WeChat 小程序不支持动态 class 重播，改用 animation 对象 + step 动画
      const anim = wx.createAnimation({
        duration: 600,
        timingFunction: 'ease-out',
        transformOrigin: '50% 50%',
      })
      anim.scale(2.4).opacity(0).step()
      this.setData({ ringAnimation: anim.export(), ringKey: this.data.ringKey + 1 })
    },
  },
})
