# 01 — 清理无用动效组件与依赖

**What to build:** 删除未使用的动效组件和无用 npm 依赖，减少 bundle 体积 5MB+，提升加载性能。

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

## 范围

以下组件和 store **未被任何页面引用**，属于死代码：

- `components/ThreeScene.vue` — Three.js 粒子动画，5MB+ bundle
- `components/MotionControlPanel.vue` — 动效控制面板悬浮按钮
- `components/EChartsBar3D.vue` — 3D 柱图组件（echarts-gl 依赖）
- `stores/motion.ts` — 动效 store（仅被上述组件使用）

## 依赖清理

```json
// 可从 dependencies 移除:
"three": "^0.185.1",
"echarts-gl": "^2.1.0",
"@types/three": "^0.185.1"

// 检查 gsap 是否在其他地方使用，如未使用一并移除
```

## 接受标准

- [ ] `ThreeScene.vue`、`MotionControlPanel.vue`、`EChartsBar3D.vue`、`motion.ts` 已删除
- [ ] `package.json` 中 `three`、`echarts-gl`、`@types/three` 已移除（`gsap` 视使用情况决定）
- [ ] `frontend-web/src` 中无任何对已删除组件/模块的引用
- [ ] `npm run build` 构建成功，bundle 体积减少
- [ ] 所有页面功能正常，无运行时错误
