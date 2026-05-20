import { createApp } from 'vue'
import App from './App.vue'

import VueECharts from 'vue-echarts'
import 'echarts'

const app = createApp(App)
app.component('v-chart', VueECharts)
app.mount('#app')
